import geocoder
import logging
import usaddress

from boto import ses
from campfin_data.models import *
from collections import OrderedDict
from csv import DictWriter
from datetime import datetime, date, timedelta
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import Distance
from django.db.models import Count, Q, Sum
from django.db.utils import *
from django.http import HttpRequest, HttpResponse
from django.template import loader
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from StringIO import StringIO

logger = logging.getLogger(__name__)

def parse_address(address):
    formatted = {
        'street_1': None,
        'street_2': None,
        'city': None,
        'state': None,
        'zipcode': None,
        'zipcode_plus': None
    }

    try:
        parsed, address_type = usaddress.tag(address)
    except usaddress.RepeatedLabelError:
        return formatted

    if address_type == 'PO Box':
        formatted['street_1'] = ' '.join([e for e in [
            parsed.get('USPSBoxType', ''),
            parsed.get('USPSBoxID', '')] if e]).strip()

        formatted['street_2'] = ' '.join([e for e in [
            parsed.get('USPSBoxGroupType', ''),
            parsed.get('USPSBoxGroupID', '')] if e]).strip()

    elif address_type == 'Street Address':
        formatted['street_1'] = ' '.join([e for e in [
            parsed.get('AddressNumberPrefix', ''),
            parsed.get('AddressNumber', ''),
            parsed.get('AddressNumberSuffix', ''),
            parsed.get('StreetNamePreDirectional', ''),
            parsed.get('StreetNamePreModifier', ''),
            parsed.get('StreetNamePreType', ''),
            parsed.get('StreetName', ''),
            parsed.get('StreetNamePostType', ''),
            parsed.get('StreetNamePostDirectional', ''),
            parsed.get('StreetNamePostModifier', '')] if e]).strip()

        formatted['street_2'] = ' '.join([e for e in [
            parsed.get('OccupancyType', ''),
            parsed.get('OccupancyIdentifier', '')] if e]).strip()

    elif address_type == 'Intersection':
        formatted['street_1'] = ' '.join([e for e in [
            parsed.get('StreetName', ''),
            parsed.get('IntersectionSeparator', ''),
            parsed.get('SecondStreetName', '')] if e]).strip()

        formatted['street_2'] = ' '.join([e for e in [
            parsed.get('OccupancyType', ''),
            parsed.get('OccupancyIdentifier', '')] if e]).strip()

    elif address_type == 'Ambiguous':
        return formatted

    formatted['city'] = parsed.get('PlaceName', '').strip()
    formatted['state'] = parsed.get('StateName', '').strip()[:2]

    formatted['zipcode'] = parsed.get('ZipCode', None)
    if formatted['zipcode'] and formatted['zipcode'].find('-') != -1:
        try:
            formatted['zipcode'], formatted['zipcode_plus'] = formatted['zipcode'].split('-')
        except ValueError:
            formatted['zipcode'] = parsed.get('ZipCode', '')[:5]
            formatted['zipcode_plus'] = None

    if formatted['zipcode'] and not formatted['zipcode'].isdigit():
        formatted['zipcode'] = None
    if formatted['zipcode_plus'] and not formatted['zipcode_plus'].isdigit():
        formatted['zipcode_plus'] = None

    if not formatted['zipcode']:
        formatted['zipcode'] = None
    if not formatted['zipcode_plus']:
        formatted['zipcode_plus'] = None

    return formatted


def load_address(original_address):
    parsed_address = parse_address(original_address)
    try:
        address, created = Address.objects.update_or_create(
            street_1=parsed_address['street_1'],
            street_2=parsed_address['street_2'],
            city=parsed_address['city'],
            state=parsed_address['state'],
            zipcode=parsed_address['zipcode'],
            zipcode_plus=parsed_address['zipcode_plus'],
            original_address=original_address)
    except IntegrityError:
        address = None
    except Exception:
        logging.info('Address triggered dataerror: %s' % original_address)
        address = None
    return address


def geocode_address(address):
    try:
        result = geocoder.google(address.original_address)
        address.coords = GEOSGeometry(
            'POINT(%s %s)' % (result.json['lng'], result.json['lat']), srid=4326)
        address.geocode_confidence = result.json['confidence']
        address.geocode_provider = 'GOOG'
        address.save()
    except Exception, e:
        if address.original_address:
            logging.info('Error geocoding address %s with Google: %s' % (
                address.original_address, e))
        else:
            logging.info('No original address to geocode for %s' % str(address))


def fetch_nearby_entities_from_sos_corporations(
    corporations, distance=settings.DEFAULT_PROXIMITY_DISTANCE):
    """
    Iterate over list of corporations and find any possibly-nearby entities.
    Nearby is defined as "within distance", defaults to 10 meters.
    """
    addresses = []
    for corporation in corporations:
        if corporation.alternate_address:
            if not corporation.alternate_address.coords:
                geocode_address(corporation.alternate_address.coords)
            if corporation.alternate_address.coords:
                addresses.append(corporation.alternate_address)
        if corporation.registered_agent.address:
            if not corporation.registered_agent.address.coords:
                geocode_address(corporation.registered_agent.address)
            if corporation.registered_agent.address.coords:
                addresses.append(corporation.registered_agent.address)
        for person in corporation.governing_persons.all():
            if person.address:
                if not person.address.coords:
                    geocode_address(person.address)
                if person.address.coords:
                    addresses.append(person.address)
    return find_nearby_entities(addresses, distance)


def find_nearby_entities(addresses, distance=settings.DEFAULT_PROXIMITY_DISTANCE):
    """
    Find all nearby entities, of any type, for a given address.
    Nearby is defined as "within distance", defaults to 10 meters.
    """
    nearby = {
        'Person': [],
        'STVendor': [],
        'SOSCorporation': [],
        'PDCCommitteeYear': []
    }

    for address in addresses:
        nearby['Person'] += list(Person.objects.filter(
            address__coords__distance_lt=(address.coords, Distance(km=distance))).all())
        nearby['STVendor'] += list(STVendor.objects.filter(
            addresses__coords__distance_lt=(address.coords, Distance(km=distance))).all())
        nearby['SOSCorporation'] += list(SOSCorporation.objects.filter(
            alternate_address__coords__distance_lt=(address.coords, Distance(km=distance))).all())
        nearby['PDCCommitteeYear'] += list(PDCCommitteeYear.objects.filter(
            address__coords__distance_lt=(address.coords, Distance(km=distance))).all())

    return nearby

def get_st_ballot_measure_donations(person):
    """"
    Get donations to ST2/3 ballot measures for given pkey.
    """
    links = get_person_links(person, recursive=True)
    contributions = PDCContribution.objects.filter(
        donor__in=links['all_people'],
        filer_id__in=settings.ST_BALLOT_MEASURE_COMMITTEES,
        is_superseded=False).order_by('-rcpt_date')
    results = {
        'all': {'contribs': contributions},
        'pre_st2': {
            'contribs': contributions.filter(rcpt_date__lt=settings.ST_2_2007_ELECTION_DAY)
        },
        'during_st2': {
            'contribs': contributions.filter(
                rcpt_date__gte=settings.ST_2_2007_ELECTION_DAY,
                rcpt_date__lte=settings.ST_2_2008_ELECTION_DAY),
        },
        'post_st2': {
            'contribs': contributions.filter(rcpt_date__gt=settings.ST_2_2008_ELECTION_DAY)
        }
    }
    for result in results:
        results[result]['aggregate'] = results[result]['contribs'].aggregate(
            num_contribs=Count('ident'),
            total_amount=Sum('amount'))
    return results

def get_person_links(person, recursive=False):
    """
    Get all people related to a person. Recursive is just one level deep, for
    now, and isn't truly recursive obviously. Maybe should be.
    """
    links = PersonLink.objects.filter(Q(canonical=person) | Q(secondary=person))
    all_people = set()
    canonicals = set()
    all_people.add(person)
    for link in links:
        all_people.add(link.canonical)
        canonicals.add(link.canonical)
        all_people.add(link.secondary)
    for p in list(all_people):
        links = PersonLink.objects.filter(Q(canonical=p) | Q(secondary=p))
        for link in links:
            all_people.add(link.canonical)
            canonicals.add(link.canonical)
            all_people.add(link.secondary)
    return {'all_people': list(all_people), 'canonicals': list(canonicals)}

def ballot_geocoder(address):
    if address:
        try:
            g = geocoder.google(address, key=settings.GOOGLE_GEOCODER_KEY)
            return {'lng': g.json['lng'], 'lat': g.json['lat']}
        except:
            return {'lng': None, 'lat': None}
    return {'lng': None, 'lat': None}

def ballot_race_builder(lat, lon, fallback_district_ids=['49', '55', '52', '107246']): 
    counties = []
    vtds = []
    precincts = []
    districts = []
    bds = []

    county_shapefile_mapping = {
        'votdst': 'KI',
        'Election_Precincts': 'PI',
        'PrecinctBoundary': 'SN'
    }

    # We need this because the SoS-provided geographies don't contain correct ST tax area.
    in_sound_transit = False
    
    try:
        point = 'POINT(%s %s)' % (lon, lat)
        geos = Geography.objects.filter(
            Q(shapefile='vtd10', multipoly__contains=point) |
            Q(geo_type='countyprecinct', multipoly__contains=point) |
            Q(shapefile='RTA_16Q4', poly__contains=point))
        precinct_ids = []
        county = ''
        for geo in geos:
            if geo.geo_type == 'countyprecinct':
                precinct_ids.append(geo.identifier)
                county = county_shapefile_mapping[geo.shapefile]
            elif geo.shapefile == 'RTA_16Q4':
                in_sound_transit = True
            else:
                vtds.append(geo.identifier)

        if precinct_ids:
            logging.info('Found %d matching precinct ids; skipping crosswalk' % len(precinct_ids))
            for pct in BallotPrecinct.objects.filter(
                precinct_code__in=precinct_ids, county=county):
                precincts.append(pct)
        else:
            logging.info('Missed more specific precinct')
            crosswalks = VTDPrecinctCrosswalk.objects.filter(vtd_identifier__in=vtds)

            for cw in crosswalks:
                for pct in BallotPrecinct.objects.filter(
                        precinct_code=cw.precinct_code, county__iexact=cw.county):
                    precincts.append(pct)

        bds = BallotDistrictPrecinctMap.objects.filter(precinct__in=precincts)

        districts = BallotDistrictDistrictMap.objects.filter(
            Q(child_district__in=[bd.district for bd in bds]) |
            Q(parent_district__in=[bd.district for bd in bds]))
        
        co_geos = Geography.objects.filter(shapefile='county10', poly__contains=point)
        for geo in co_geos:
            counties.append(geo.identifier)
    except Exception, e:
        logging.info('Error fetching districts for lat %s lon %s: %s' % (lat, lon, e))

    election = BallotElection.objects.get(is_current=True)

    all_districts = set()
    for district in districts:
        all_districts.add(district.child_district)
        all_districts.add(district.parent_district)

    for district in bds:
        all_districts.add(district.district)

    if in_sound_transit:
        st_district = BallotDistrict.objects.get(
            district_id=settings.SOUND_TRANSIT_DISTRICT_ID)
        all_districts.add(st_district)

    if not all_districts:
        all_districts = set(
            BallotDistrict.objects.filter(district_id__in=fallback_district_ids))

    return {
        'precincts': precincts,
        'counties': counties,
        'districts': sort_districts_for_ballot(all_districts)
    }

def sort_districts_for_ballot(districts):
    rankings = {
        49: -5,
        55: -3,
        52: -2,
        107246: -1,
        settings.SOUND_TRANSIT_DISTRICT_ID: -0.5,
        107247: 4
    }
    for district in districts:
        if district.district_id not in rankings:
            if district.district_name.lower().startswith('congressional district'):
                rankings[district.district_id] = -4
            elif district.district_name.lower().startswith('legislative district'):
                rankings[district.district_id] = 0
            else:
                rankings[district.district_id] = 1
    return sorted(districts, key=lambda k: rankings[k.district_id])

def extract_party_code_from_preference(pref):
    if not pref:
        return 'Non'
    codes = [
        ('democrat', 'Dem'),
        ('republican', 'Rep'),
        ('libertarian', 'Lib'),
        ('green', 'Gre'),
        ('independant', 'Ind'),
        ('non-partisan', 'Non'),
        ('constitution', 'Con'),
        ('gop', 'Rep'),
        ('dem', 'Dem'),
        ('no party', 'Non'),
        ('socialist workers party', 'Soc'),
        ('socialism', 'Soc'),
        ('none', 'Non'),
        ('g.o.p.', 'Rep'),
        ('independent', 'Ind'),
    ]
    for code in codes:
        if pref.lower().find(code[0]) != -1:
            return code[1]
    return 'Oth'

def extract_party_name_from_preference(pref):
    if not pref:
        return 'Non-partisan'
    codes = [
        ('democrat', 'Democratic'),
        ('republican', 'Republican'),
        ('libertarian', 'Libertarian'),
        ('green', 'Green'),
        ('independant', 'Independent'),
        ('non-partisan', 'Non-partisan'),
        ('constitution', 'Constitution'),
        ('gop', 'Republican'),
        ('dem', 'Democratic'),
        ('no party', 'Non-partisan'),
        ('socialist workers party', 'Socialist'),
        ('socialism', 'Socialist'),
        ('none', 'Non-partisan'),
        ('g.o.p.', 'Republican'),
        ('independent', 'Independent'),
    ]
    for code in codes:
        if pref.lower().find(code[0]) != -1:
            return code[1]
    return 'Other'

def get_candidates_by_district():
    # Generates dict of all districts, with all candidates running in that district
    districts = {}
    election = BallotElection.objects.get(is_current=True)

    for district in BallotDistrict.objects.all():
        candidates = BallotRaceSummary.objects.filter(
            election=election, district=district)
        if candidates.count() > 0:
            districts[district.district_id] = {}
            for candidate in candidates:
                if (candidate.district.district_id == 49 and
                        candidate.ballot_id not in [45726, 45724, 40725, 41135]):
                    continue
                if candidate.race_id not in districts[district.district_id]:
                    districts[district.district_id][candidate.race_id] = {
                        'race_name': candidate.race_name,
                        'race_id': candidate.race_id,
                        'candidates': {}
                    }
                if candidate.ballot_id not in (
                        districts[district.district_id][candidate.race_id]['candidates']):
                    districts[district.district_id][candidate.race_id]['candidates'][
                        candidate.ballot_id] = candidate
    return districts

def generate_summary_stats_for_candidate(candidate):
    stats = {
        'ballot_id': candidate.ballot_id,
        'total_raised': 0.,
        'total_spent': 0.,
        'total_loaned': 0.,
        'total_inkinds': 0.,
        'total_ie_for': 0.,
        'total_ie_against': 0.,
        'top_donor': {},
        'top_donor_ties': 0,
        'name': candidate.ballot_name,
        'race_name': candidate.race_name,
        'party_code': extract_party_code_from_preference(candidate.party_name)
    }

    pdc_map = SOSPDCMap.objects.filter(sos_ballot_id=candidate.ballot_id)
    committees = list(set([pm.pdc_filer_id for pm in pdc_map]))
    cmte_objs = ScrapedCommittee.objects.filter(filer_id__in=committees)
    donations = ScrapedContribution.objects.filter(filing_committee__in=cmte_objs)
    top_donors = account_for_refunds(
        donations.values(
            'donor', 'city', 'state', 'employer', 'occupation'
            ).annotate(
            sum=Sum('amount'), num=Count('donor')).order_by('-sum', '-num', 'donor'),
        cmte_objs)
    totals = ScrapedTotals.objects.filter(filing_committee__in=cmte_objs)
    for total in totals:
        stats['total_raised'] += float(total.raised)
        stats['total_spent'] += float(total.spent)
        stats['total_loaned'] += float(total.loans)
        stats['total_inkinds'] += float(total.inkinds)
        stats['total_ie_for'] += float(total.ie_for) if total.ie_for else 0.
        stats['total_ie_against'] += float(total.ie_against) if total.ie_against else 0.

    if len(top_donors):
        stats['top_donor'] = {
            'donor': top_donors[0]['donor'],
            'city': top_donors[0]['city'],
            'state': top_donors[0]['state'],
            'occupation': top_donors[0]['occupation'],
            'employer': top_donors[0]['employer'],
            'sum': float(top_donors[0]['sum']),
            'num': top_donors[0]['num']
        }
        for donor in top_donors[1:]:
            if donor['sum'] == top_donors[0]['sum']:
                stats['top_donor_ties'] += 1
            else:
                break
    return stats

def account_for_refunds(donors, committees, zipcode=False):
    accounted_donors = []
    refunded_donors = {}
    if not zipcode:
        for donor in ScrapedRefund.objects.filter(
                filing_committee__in=committees).values(
                'donor', 'city', 'state').annotate(sum=Sum('amount')):
            key = '-'.join([donor['donor'], donor['city'], donor['state']])
            refunded_donors[key] = donor['sum']
    else:
        for donor in ScrapedRefund.objects.filter(
                filing_committee__in=committees).values(
                'donor', 'city', 'state', 'zipcode').annotate(sum=Sum('amount')):
            key = '-'.join([donor['donor'], donor['city'], donor['state'], donor['zipcode']])
            refunded_donors[key] = donor['sum'] 
    for donor in donors:
        dd = donor.get('donor', '') if donor.get('donor', '') else ''
        dc = donor.get('city', '') if donor.get('city', '') else ''
        ds = donor.get('state', '') if donor.get('state', '') else ''
        dz = donor.get('zipcode', '') if donor.get('zipcode', '') else ''

        if not zipcode:
            key = '-'.join([dd, dc, ds])
        else:
            key = '-'.join([dd, dc, ds, dz])
        if key in refunded_donors:
            donor['sum'] = donor['sum'] - refunded_donors[key]
        accounted_donors.append(donor)
    return sorted(
        accounted_donors, key=lambda k: (-k['sum'], -k['num'], k['donor']))

def get_committees_for_ballot_id(ballot_id):
    pdc_map = SOSPDCMap.objects.filter(sos_ballot_id=ballot_id)
    committees = list(set([pm.pdc_filer_id for pm in pdc_map]))
    return ScrapedCommittee.objects.filter(filer_id__in=committees)

def get_donations_for_ballot_id(ballot_id):
    return ScrapedContribution.objects.filter(
        filing_committee__in=get_committees_for_ballot_id(ballot_id))

def get_inkinds_for_ballot_id(ballot_id):
    committees = get_committees_for_ballot_id(ballot_id)
    return ScrapedInkind.objects.filter(filing_committee__in=committees)

def get_grouped_inkinds(inkinds):
    all_inkinds = {}
    for inkind in inkinds:
        key = '-'.join([
            str(inkind.donor),
            str(inkind.city),
            str(inkind.state),
            str(inkind.employer),
            str(inkind.occupation)
        ])
        if key not in all_inkinds:
            all_inkinds[key] = {
                'donor': inkind.donor,
                'city': inkind.city,
                'state': inkind.state,
                'employer': inkind.employer,
                'occupation': inkind.occupation,
                'sum': 0.,
                'num': 0,
                'descriptions': set()
            }
        all_inkinds[key]['sum'] += float(inkind.amount)
        all_inkinds[key]['num'] += 1
        all_inkinds[key]['descriptions'].add(inkind.description)
    return all_inkinds

def get_top_inkinds(inkinds):
    top_inkinds = []
    for inkind in sorted(
            inkinds.items(),
            key=lambda x: (-1 * x[1]['sum'], -1 * x[1]['num'], x[1]['donor'])):
        top_inkinds.append([
            inkind[1]['donor'],
            inkind[1]['sum'],
            inkind[1]['num'],
            '; '.join(list(inkind[1]['descriptions'])),
            inkind[1]['employer'],
            inkind[1]['occupation'],
            inkind[1]['city'],
            inkind[1]['state']
        ])
    return top_inkinds

def get_expenses_for_ballot_id(ballot_id):
    return ScrapedExpense.objects.filter(
        filing_committee__in=get_committees_for_ballot_id(ballot_id))

def get_grouped_expenses(expenses):
    all_expenses = {}
    for expense in expenses:
        key = '-'.join([
            str(expense.vendor),
            str(expense.city),
            str(expense.state)
        ])
        if key not in all_expenses:
            all_expenses[key] = {
                'vendor': expense.vendor,
                'city': expense.city,
                'state': expense.state,
                'sum': 0.,
                'num': 0,
                'descriptions': set()
            }
        all_expenses[key]['sum'] += float(expense.amount)
        all_expenses[key]['num'] += 1
        all_expenses[key]['descriptions'].add(expense.description)
    return all_expenses

def get_top_expenses(expenses):
    top_expenses = []
    for expense in sorted(expenses.items(), key=lambda x: x[1]['sum'], reverse=True):
        top_expenses.append([
            expense[1]['vendor'],
            expense[1]['sum'],
            expense[1]['num'],
            '; '.join(list(expense[1]['descriptions'])),
            expense[1]['city'],
            expense[1]['state']
        ])
    return top_expenses

def get_top_expense_descriptions(expenses):
    return expenses.values('description').annotate(
        sum=Sum('amount'), num=Count('vendor')).order_by('-sum', '-num', 'description')

def get_top_vendors_outside_wa(expenses):
    top_vendors_outside_wa = []
    for expense in expenses:
        if expense[5] and expense[5].upper() != 'WA':
            top_vendors_outside_wa.append(expense)
    return top_vendors_outside_wa

def get_donation_stats(donations):
    committees = [d.filing_committee for d in donations]
    accounted_donors = account_for_refunds(donations.values(
        'donor', 'city', 'state', 'employer', 'occupation').annotate(
        sum=Sum('amount'), num=Count('donor')), committees)
    # Annoying we have to do this, but campaigns suck at filling out zipcode field properly,
    # so here we are.
    zipcode_accounted_donors = account_for_refunds(donations.values(
        'donor', 'city', 'state', 'employer', 'occupation', 'zipcode').annotate(
        sum=Sum('amount'), num=Count('donor')), committees, zipcode=True)

    total = 0.
    employers = {}
    occupations = {}
    zipcodes = {}

    for donor in accounted_donors:
        employer_key = donor['employer'].lower().strip() if donor['employer'] else ''
        occupation_key = donor['occupation'].lower().strip() if donor['occupation'] else ''
        
        if employer_key not in employers:
            employers[employer_key] = {
                'employer': donor['employer'].strip() if donor['employer'] else '',
                'sum': 0.,
                'num': 0
            }
        if occupation_key not in occupations:
            occupations[occupation_key] = {
                'occupation': donor['occupation'].strip() if donor['occupation'] else '',
                'sum': 0.,
                'num': 0
            }

        employers[employer_key]['sum'] += float(donor['sum'])
        employers[employer_key]['num'] += float(donor['num'])

        occupations[occupation_key]['sum'] += float(donor['sum'])
        occupations[occupation_key]['num'] += float(donor['num'])

        total += float(donor['sum'])

    for donor in zipcode_accounted_donors:
        zipcode_key = donor['zipcode']

        if zipcode_key not in zipcodes:
            zipcodes[zipcode_key] = {
                'zipcode': zipcode_key,
                'sum': 0.,
                'num': 0
            }
            zipcodes[zipcode_key]['sum'] += float(donor['sum'])
            zipcodes[zipcode_key]['num'] += float(donor['num'])

    stats = {
        'top_donors': accounted_donors,
        'top_donor_ties': 0,
        'top_donors_outside_wa': [
            donor for donor in accounted_donors
            if donor['state'] and donor['state'].lower() != 'wa'],
        'top_donor_outside_wa_ties': 0,
        'top_employers': [
            employers[employer] for employer in sorted(
                employers, key=lambda k: (
                    -employers[k]['sum'],
                    -employers[k]['num'],
                    employers[k]['employer']))],
        'top_occupations': [
            occupations[occupation] for occupation in sorted(
                occupations, key=lambda k: (
                    -occupations[k]['sum'],
                    -occupations[k]['num'],
                    occupations[k]['occupation']))],
        'top_zips': [zipcodes[zc] for zc in zipcodes],
        'total': total
    }

    for donor in stats['top_donors'][1:]:
        if donor['sum'] == stats['top_donors'][0]['sum']:
            stats['top_donor_ties'] += 1
        else:
            break
    for donor in stats['top_donors_outside_wa'][1:]:
        if donor['sum'] == stats['top_donors_outside_wa'][0]['sum']:
            stats['top_donor_outside_wa_ties'] += 1
        else:
            break
    return stats

def generate_timeseries(itemized):
    timeseries = []
    current_day = date(2015, 1, 1)
    one_day = timedelta(days=1)
    running_total = 0.
    while current_day < date.today():
        day_total = itemized.filter(date=current_day).aggregate(Sum('amount'))
        if day_total['amount__sum']:
            running_total += float(day_total['amount__sum'])
        timeseries.append({
            'date': current_day.strftime('%Y-%m-%d'),
            'amount': running_total
        })
        current_day += one_day
    return timeseries

def convert_list_of_models_to_csv_string(data):
    fh = StringIO()
    header = sorted([k for k in data[0].__dict__.keys() if not k.startswith('_')])
    writer = DictWriter(fh, header)
    writer.writeheader()
    for row in data:
        writer.writerow({k: row.__dict__[k] for k in row.__dict__ if not k.startswith('_')})
    fh.seek(0)
    return fh.read()

def render_and_send_email(email_address, data, template_folder, report_name, payload=None):
    html_template = loader.get_template('email/%s/html.html' % template_folder)
    text_template = loader.get_template('email/%s/text.html' % template_folder)
    html_content = html_template.render(
        {
            'data': data,
            'maintainer': settings.MAINTAINER_EMAIL_ADDRESS
        },
        None)
    text_content = text_template.render(
        {
            'data': data,
            'maintainer': settings.MAINTAINER_EMAIL_ADDRESS
        },
        None)
    
    connection = ses.connect_to_region(settings.AWS_REGION)
    
    message = MIMEMultipart()
    message['Subject'] = 'Campaign Finance: %s' % report_name
    message['From'] = settings.EMAIL_FROM_ADDRESS
    message['To'] = email_address
    message.preamble = 'Multipart message.\n'

    if payload:
        data_part = MIMEText(payload)
        data_part.add_header('Content-Disposition', 'attachment', filename='data.csv')
        message.attach(data_part)

    text_part = MIMEText(text_content, 'text')
    message.attach(text_part)

    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)
 
    try:
        connection.send_raw_email(message.as_string())
    except Exception, e:
        logging.info(
            'Hit error %s; sending verification email to %s in hopes that will fix' % (
                e, email_address))
        connection.verify_email_address(email_address)
