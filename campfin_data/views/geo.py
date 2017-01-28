import geocoder
import leather
import locale
import logging
import os
import requests

from campfin_data.models import *
from campfin_data.utils import *
from datetime import datetime
from collections import OrderedDict
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance
from django.db import connection
from django.db.models import Q, Sum, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from pytz import timezone

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except:
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
logger = logging.getLogger(__name__)

# Silence some unnecessary log messages
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def my_districts(request):
    template = loader.get_template('campfin_data/my_districts.html')
    lat = request.GET.get('lat', 'null')
    lon = request.GET.get('lon', 'null')
    source = request.GET.get('source', 'null')
    geos = []
    districts = {}
    num_vtds = 0
    races = []
    precincts = []
    num_precincts = 0
    if lat != 'null' and lon != 'null':
        point = 'POINT(%s %s)' % (lon, lat)
        geos = Geography.objects.filter(
            Q(poly__contains=point) | Q(multipoly__contains=point))
        for geo in geos:
            if geo.shapefile == 'vtd10':
                num_vtds += 1
                precincts = VTDPrecinctCrosswalk.objects.filter(vtd_identifier=geo.identifier)
                for precinct in precincts:
                    precinct_districts = DistrictPrecinctCrosswalk.objects.filter(
                        county=precinct.county,
                        precinct_code=precinct.precinct_code,
                        precinct_part=precinct.precinct_part)
                    for pd in precinct_districts:
                        slug = '-'.join(
                            [str(pd.district_id), pd.district_code, pd.district_name])
                        if slug not in districts:
                            districts[slug] = pd

    if precincts:
        num_precincts = precincts.count()
    candidates = RaceCandidate.objects.filter(county_display='Statewide')
    races = {}
    for candidate in candidates:
        slug = ' '.join([candidate.race_position_name, candidate.race_name])
        if slug not in races:
            races[slug] = []
        races[slug].append(candidate)

    order = [
        'President', 'Governor', 'Attorney General', 'U.S. Senator', 'Lt. Governor',
        'State Treasurer', 'Secretary of State', 'Insurance Commissioner', 'State Auditor',
        'Superintendent of Public Instruction', 'Commissioner of Public Lands',
        'Justice Position 1', 'Justice Position 5', 'Justice Position 6']

    context = {
        'title': 'My districts',
        'lat': lat,
        'lon': lon,
        'source': source,
        'geos': geos,
        'num_precincts': num_precincts,
        'districts': sorted(
            [districts[pd] for pd in districts], key=lambda x: x.district_name),
        'races': sorted(
            [races[r] for r in races], key=lambda x: order.index(x[0].race_position_name))
    }
    return HttpResponse(template.render(context, request))


def district_id_router(request, district_id):
    try:
        with open(
            os.path.join(
                settings.PDC_SCRAPED_DIR,
                'district_metadata-fail',
                '%d.json' % district_id)) as FH:
            return HttpResponse(FH.read())
    except Exception:
        r = requests.get('%smetadata/%s.json' % (settings.S3_BUCKET_UNALIASED_PATH, district_id))
        with open(
            os.path.join(settings.PDC_SCRAPED_DIR, 'district_metadata', '%s.json' % district_id),
            'w+') as FH:
            FH.write(r.text)
        return HttpResponse(r.text)


def my_ballot(request):
    template = loader.get_template('campfin_data/my_ballot.html')

    pacific = timezone('US/Pacific')
    context = {
        'title': 'My districts',
        'timestamp': datetime.now(pacific)
    }
    return HttpResponse(template.render(context, request))

def geocode(request):
    address = request.GET.get('address', None)
    context = {'results': []}
    if address:
        results = ballot_geocoder(address)
        context['results'] = [address, results['lng'], results['lat']]
    return JsonResponse(context)

def ballot(request):
    """
    This is the workhorse. Takes posted parameters for either lat/lon (preferred) or address.
    If it gets an address and no lat/lon, geocodes that first. If it has address and lat/lon,
    ignore the address.
    Once it has lat/lon, fetch & format & return JSON of all available/matching races.
    If no races match, return all statewide ones - I.E. Senate, executives,
    statewide measures.
    Don't return finance data, but do return IDs that allow clients to fetch that data
    from flat files published to S3.
    """
    address = request.GET.get('address', None)
    lat = request.GET.get('lat', None)
    lon = request.GET.get('lon', None)
    json_results = {
        'counties': [],
        'precincts': [],
        'districts': [],
        'location': {
            'address': address,
            'lat': lat,
            'lon': lon
        }
    }

    if address and (not lat and not lon):
        results = ballot_geocoder(address)
        lat = results['lat']
        lon = results['lng']
        json_results['location']['lat'] = lat
        json_results['location']['lon'] = lon

    ballot = ballot_race_builder(lat, lon)

    for precinct in ballot['precincts']:
        json_results['precincts'].append({
            'name': precinct.precinct_name,
            'id': precinct.precinct_id
        })

    for district in ballot['districts']:
        if district.district_id in [75922, 80751, 80752]:
            continue
        json_results['districts'].append({
            'name': district.district_name,
            'id': district.district_id,
            'code': district.district_code,
            'county': district.county
        })

    json_results['counties'] = ballot['counties']

    return JsonResponse(json_results)
