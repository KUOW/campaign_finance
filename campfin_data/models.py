from __future__ import unicode_literals

import logging

from django.contrib.gis.db import models
from django.core.urlresolvers import reverse

logger = logging.getLogger(__name__)

CURRENCY_FIELDS_MAX_DIGITS = 15
CURRENCY_FIELDS_NUM_DECIMALS = 3

class Address(models.Model):
    """
    Represents a specific address, containing both textual representation and,
    when present, geocoded coordinates.
    """
    street_1 = models.CharField(max_length=350, blank=True, null=True)
    street_2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    state = models.CharField(max_length=2, db_index=True, blank=True, null=True)
    zipcode = models.IntegerField(db_index=True, blank=True, null=True)
    zipcode_plus = models.IntegerField(blank=True, null=True)

    original_address = models.TextField(blank=True, null=True)

    # Computed fields
    census_block = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    census_county_fips = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    census_tract = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    census_year = models.CharField(max_length=25, blank=True, null=True)
    coords = models.PointField(blank=True, null=True)
    geocode_confidence = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        db_index=True)

    # Meta fields
    pending_geocode = models.BooleanField(default=False)
    geocode_provider = models.CharField(max_length=5, blank=True, null=True, db_index=True)


    def __str__(self):
        return self.original_address.encode('ascii', errors='replace')


class Person(models.Model):
    """
    Represents an individual.
    """
    full_name = models.CharField(max_length=300, db_index=True, blank=True, null=True)

    address = models.ForeignKey(Address, null=True)

    first_name = models.CharField(db_index=True, max_length=30, blank=True, null=True)
    middle_name = models.CharField(db_index=True, max_length=30, blank=True, null=True)
    last_name = models.CharField(db_index=True, max_length=60, blank=True, null=True)

    def __str__(self):
        return self.full_name.encode('ascii', errors='replace')

    def get_absolute_url(self):
        return reverse('person-detail', args=[str(self.pk)])


class Geography(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100)
    shapefile = models.CharField(max_length=100)
    poly = models.PolygonField(srid=4326, blank=True, null=True)
    multipoly = models.MultiPolygonField(srid=4326, blank=True, null=True)
    geo_type = models.CharField(max_length=100, default="oneoff")

    def __str__(self):
        return 'Geography: %s' % self.name


class PersonLink(models.Model):
    """
    Represents a link between multiple people.
    """
    SAME = 'SM'
    PARTNER = 'PT'
    LINK_TYPE_CHOICES = (
        (SAME, 'Same'),
        (PARTNER, 'Partner')
    )
    canonical = models.ForeignKey(Person, db_index=True, related_name='canonical')
    secondary = models.ForeignKey(Person, db_index=True, related_name='secondary')
    link_type = models.CharField(
        db_index=True, max_length=2, choices=LINK_TYPE_CHOICES, default=SAME)
    link_source = models.CharField(db_index=True, max_length=30)


class STVendor(models.Model):
    """
    Represents a specific Sound Transit vendor.
    """
    name = models.CharField(max_length=200)
    addresses = models.ManyToManyField(Address, blank=True)

    def __str__(self):
        return self.name.encode('ascii', errors='replace')


class STVendorContract(models.Model):
    """
    Represents a specific contract between Sound Transit and a vendor.
    """
    vendor = models.ForeignKey(STVendor)

    amount_bid = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    amount_awarded = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)

    contract_name = models.TextField(db_index=True)
    solicitation_id = models.CharField(max_length=20, db_index=True)
    award_date = models.DateTimeField(db_index=True, blank=True, null=True)

    not_lowest = models.BooleanField(default=False)
    only_bidder = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    st2_related = models.BooleanField(default=False)
    st3_related = models.BooleanField(default=False)
    all_one_dollar_bids = models.BooleanField(default=False)

    def __str__(self):
        return '%s - %s'.encode('ascii', errors='replace') % (self.vendor.name, self.contract_name)

    def get_absolute_url(self):
        return reverse('contract-detail', args=[str(self.pk)])


class STVendorBrief(models.Model):
    """
    Contains Sound Transit vendor info from brief contracts data file.
    """
    entity = models.ForeignKey(Person, db_index=True, null=True, blank=True)
    vendor_number = models.CharField(max_length=15, db_index=True)


class STVendorContractBrief(models.Model):
    """
    Contains Sound Transit contract info from brief contracts data file.
    """
    vendor = models.ForeignKey(STVendorBrief, db_index=True)

    po_number = models.CharField(max_length=15, db_index=True)
    po_type = models.CharField(max_length=15, db_index=True)
    procurement_number = models.CharField(max_length=35, db_index=True, blank=True, null=True)
    po_description = models.TextField(blank=True, null=True)

    department = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    division = models.CharField(max_length=100, db_index=True, blank=True, null=True)

    contract_specialist = models.ForeignKey(
        Person, blank=True, null=True, db_index=True, related_name='contract_specialist')
    project_manager = models.ForeignKey(
        Person, blank=True, null=True, db_index=True, related_name='project_manager')

    start_date = models.DateField(db_index=True, blank=True, null=True)
    expiration_date = models.DateField(db_index=True, blank=True, null=True)
    close_date = models.DateField(db_index=True, blank=True, null=True)

    award = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    expenditures = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    award_remaining = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    unreleased = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)


class SOSGoverningPerson(models.Model):
    """
    Represents an intermediate relationship of an SOSCorporatePerson as a governing agent of an
    SOSCorporation.
    """
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    corporation = models.ForeignKey('SOSCorporation', on_delete=models.CASCADE)
    title = models.CharField(max_length=75, blank=True, null=True)

    def __str__(self):
        return '%s (%s) -> %s'.encode('ascii', errors='replace') % (
            self.person.full_name, self.title, self.corporation.name)


class SOSCorporation(models.Model):
    """
    Represents an individual corporation retrieved from the WA SoS db.
    """
    ubi = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    state_incorporation = models.CharField(max_length=2, db_index=True)
    category = models.CharField(max_length=20, db_index=True)

    date_incorporation = models.DateField(db_index=True, blank=True, null=True)
    date_expiration = models.DateField(db_index=True, blank=True, null=True)
    date_dissolution = models.DateField(db_index=True, blank=True, null=True)

    record_status = models.CharField(max_length=20, db_index=True)
    corp_type = models.CharField(max_length=20, db_index=True)

    registered_agent = models.ForeignKey(
        Person, related_name='registered_agent', null=True)

    governing_persons = models.ManyToManyField(
        Person, through=SOSGoverningPerson, related_name='governing_persons')

    alternate_address = models.ForeignKey(Address, null=True)

    def __str__(self):
        return self.name.encode('ascii', errors='replace')

    def get_absolute_url(self):
        return reverse('corporation-detail', args=[str(self.pk)])


class PDCCommittee(models.Model):
    """
    Represents a base PDC committee.
    """
    filer_id = models.CharField(max_length=25, db_index=True, primary_key=True)
    name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return '%s (%s)'.encode('ascii', errors='replace') % (self.filer_id, self.name)

    def get_absolute_url(self):
        return reverse('committee-detail', args=[str(self.filer_id)])


class PDCCommitteeYear(models.Model):
    """
    Represents data for a specific PDC committee for a specific year.
    """
    BALLOT_FOR = 'F'
    BALLOT_AGAINST = 'A'
    BALLOT_SUPPORT_UNKNOWN = 'U'
    FOR_AGAINST_TYPE_CHOICES = (
        (BALLOT_FOR, 'For'),
        (BALLOT_AGAINST, 'Against'),
        (BALLOT_SUPPORT_UNKNOWN, 'Unknown')
    )
    committee = models.ForeignKey(PDCCommittee, db_index=True)
    year = models.IntegerField(db_index=True)

    c1_id = models.IntegerField(null=True, blank=True)
    repno = models.IntegerField(null=True, blank=True)
    filer_type = models.CharField(max_length=25)

    address = models.ForeignKey(Address, null=True, blank=True)

    affil = models.TextField(null=True, blank=True)
    affil_info = models.TextField(null=True, blank=True)
    mgr_info = models.TextField(null=True, blank=True)
    memo = models.TextField(null=True, blank=True)
    jurisdiction = models.TextField(null=True, blank=True)

    email = models.EmailField(null=True, blank=True)
    candidate_email = models.EmailField(null=True, blank=True)

    ballot_name = models.TextField(null=True, blank=True)
    ballot_number = models.CharField(max_length=20, db_index=True, null=True, blank=True)
    for_against = models.CharField(
        max_length=1,
        db_index=True,
        blank=True,
        null=True,
        choices=FOR_AGAINST_TYPE_CHOICES,
        default=BALLOT_SUPPORT_UNKNOWN)

    def __str__(self):
        return '%s - %s'.encode('ascii', errors='replace') % (self.committee.name, self.year)

    def get_absolute_url(self):
        return reverse('committee-year-detail', args=[str(self.committee.filer_id), self.year])


class PDCContribution(models.Model):
    """
    Represents an individual contribution from the PDC.
    """
    ident = models.IntegerField()
    repno = models.IntegerField(db_index=True)
    filer_id = models.CharField(max_length=30, db_index=True)
    filer_committee = models.ForeignKey(PDCCommittee, blank=True, null=True, db_index=True)

    rec_type = models.CharField(max_length=10, db_index=True)
    form_type = models.CharField(max_length=10, db_index=True)

    rpt_date = models.DateField(db_index=True, blank=True, null=True)
    prim_gen = models.CharField(max_length=3, db_index=True)
    rcpt_date = models.DateField(db_index=True, blank=True, null=True)

    donor = models.ForeignKey(Person, db_index=True)
    donor_address = models.ForeignKey(Address, blank=True, null=True, db_index=True)
    donor_employer = models.CharField(max_length=150, db_index=True, blank=True, null=True)
    donor_occupation = models.CharField(max_length=150, db_index=True, blank=True, null=True)
    donor_employer_city = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    donor_employer_state = models.CharField(max_length=5, blank=True, null=True)

    amount = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    aggregate = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)

    description = models.CharField(max_length=150, blank=True, null=True)
    memo = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    contribution_type = models.CharField(max_length=10, blank=True, null=True, db_index=True)

    is_superseded = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return '$%d from %s to %s'.encode('ascii', errors='replace') % (
            self.amount, self.donor.full_name, self.filer_committee.name)

    def get_absolute_url(self):
        return reverse('contrib-detail', args=[str(self.pk)])


class PDCLobbyist(models.Model):
    """
    Represents an individual lobbyist registered with the PDC.
    """
    lobnum = models.CharField(max_length=20, db_index=True, primary_key=True)
    person = models.ForeignKey(Person, blank=True, null=True, db_index=True)

    def __str__(self):
        return self.person.full_name.encode('ascii', errors='replace')


class PDCLobbyistRegistration(models.Model):
    """
    Represents a yearly registration of a PDC lobbyist.
    """
    lobbyist = models.ForeignKey(PDCLobbyist, db_index=True)
    year = models.IntegerField(db_index=True, blank=True, null=True)

    address = models.ForeignKey(Address, null=True, blank=True, db_index=True)

    phone = models.CharField(max_length=15, blank=True, null=True)
    cell_phone = models.CharField(max_length=15, blank=True, null=True)
    temp_phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)

    other_lobbyists = models.ManyToManyField(Person, blank=True)

    remarks = models.TextField(blank=True, null=True)
    deceased = models.CharField(max_length=50, blank=True, null=True)
    ltr = models.CharField(max_length=50, blank=True, null=True)
    warn = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=150, blank=True, null=True, db_index=True)

    warning_letter = models.DateField(blank=True, null=True)
    stipulate_letter = models.DateField(blank=True, null=True)
    brief_enforcement = models.DateField(blank=True, null=True)
    full_enforcement = models.DateField(blank=True, null=True)


class PDCLobbyistEmployer(models.Model):
    """
    Represents the employer - private or public - of a PDC lobbyist.
    """
    employer_id = models.CharField(max_length=15, db_index=True, primary_key=True)
    entity = models.ForeignKey(Person, blank=True, null=True, db_index=True)

    def __str__(self):
        return self.entity.full_name.encode('ascii', errors='replace')

class PDCLobbyistEmployerYear(models.Model):
    """
    Represents a yearly filing for a PDC lobbyist employer.
    """
    employer = models.ForeignKey(PDCLobbyistEmployer, db_index=True)
    year = models.IntegerField(db_index=True, blank=True, null=True)

    contact = models.ForeignKey(Person, null=True, blank=True, db_index=True)

    address = models.ForeignKey(Address, null=True, blank=True, db_index=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    pacs = models.CharField(max_length=50, null=True, blank=True)
    letter = models.CharField(max_length=20, null=True, blank=True)
    catnum = models.CharField(max_length=20, null=True, blank=True)

    memo = models.TextField(blank=True, null=True)
    govtagency = models.CharField(max_length=20, null=True, blank=True)


class PDCLobbyingFirm(models.Model):
    """
    Expresses relationship between a lobbyist, lobbying company and lobbyist employer for a
    specific year.
    """
    lobbyist = models.ForeignKey(PDCLobbyist, db_index=True, related_name='lobbyist')
    firm = models.ForeignKey(PDCLobbyist, db_index=True, related_name='firm')
    employer = models.ForeignKey(PDCLobbyistEmployer, db_index=True)
    year = models.IntegerField(db_index=True)


class PDCLobbyistBio(models.Model):
    """
    Contains details of a lobbyist's biography for a particular year.
    """
    lobbyist = models.ForeignKey(PDCLobbyist, db_index=True)
    year = models.IntegerField(db_index=True, null=True, blank=True)

    year_first_employed = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)


class PDCLobbyistMonthlyExpenseReport(models.Model):
    """
    Contains details of PDC lobbyist's L2 monthly expense report.
    """
    lobbyist = models.ForeignKey(PDCLobbyist, db_index=True)
    employer = models.ForeignKey(PDCLobbyistEmployer, db_index=True)

    amended = models.BooleanField(default=False, db_index=True)
    amended_report_id = models.CharField(max_length=25, blank=True, null=True)

    report_period_month_begin = models.DateField(db_index=True)
    amended_date = models.DateField(db_index=True, blank=True, null=True)
    postmark = models.DateField(blank=True, null=True)

    compensation = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    personal_expenses = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    entertainment_expenses = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    contributions = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    advertising_expenses = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    political_ads = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    other_expenses = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    unre_expenses = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    total_expenses = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)


class PDCReport(models.Model):
    """
    Contains details of PDC report filings.
    """
    repno = models.IntegerField(db_index=True)
    filer_id = models.CharField(max_length=30, db_index=True)
    filer_committee = models.ForeignKey(PDCCommittee, blank=True, null=True, db_index=True)

    is_superseded = models.BooleanField(default=False, db_index=True)
    superseding_report = models.ForeignKey(
        'self', blank=True, null=True, db_index=True, related_name='superseded_report')
    superseding_report_no = models.IntegerField(db_index=True, blank=True, null=True)

    election_year = models.IntegerField(db_index=True, blank=True, null=True)
    filer_type = models.CharField(max_length=10, db_index=True, blank=True, null=True)
    date_filed = models.DateField(db_index=True, blank=True, null=True)
    form = models.CharField(max_length=5, db_index=True, blank=True, null=True)
    subform = models.CharField(max_length=5, db_index=True, blank=True, null=True)
    status = models.CharField(max_length=5, db_index=True, blank=True, null=True)

    period_from = models.DateField(db_index=True, blank=True, null=True)
    period_thru = models.DateField(db_index=True, blank=True, null=True)

    doe = models.CharField(max_length=10, db_index=True, blank=True, null=True)
    how_filed = models.CharField(max_length=10, db_index=True, blank=True, null=True)
    received = models.CharField(max_length=10, db_index=True, blank=True, null=True)
    rptcode = models.CharField(max_length=10, db_index=True, blank=True, null=True)


class SOSElectionCandidate(models.Model):
    """
    Contains a specific election candidate for a specific race, along with votes.
    """
    name = models.TextField()
    votes = models.IntegerField(blank=True, null=True)
    vote_percent = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)


class SOSElectionRace(models.Model):
    """
    Contains summary of election results for one race.
    """
    year = models.IntegerField(db_index=True)
    level = models.CharField(max_length=15, db_index=True)
    name = models.TextField()
    jurisdiction = models.CharField(max_length=150, db_index=True, blank=True, null=True)
    ballot_number = models.CharField(max_length=10, db_index=True, blank=True, null=True)

    candidates = models.ManyToManyField(SOSElectionCandidate, related_name='candidate')
    winner = models.ForeignKey(
        SOSElectionCandidate, related_name='winner', blank=True, null=True)


class VTDPrecinctCrosswalk(models.Model):
    """
    Contains crosswalk of VTDs <-> precincts used by Sec of State.
    """
    # SoS VRDB fields
    county = models.CharField(max_length=10, db_index=True)
    precinct_code = models.CharField(max_length=50, db_index=True)
    precinct_part = models.CharField(max_length=15, db_index=True)
    # VTD field
    vtd_identifier = models.CharField(max_length=50, db_index=True)


class DistrictPrecinctCrosswalk(models.Model):
    """
    Contains crosswalk of precincts <-> electoral districts.
    """
    county = models.CharField(max_length=10, db_index=True)
    district_type = models.CharField(max_length=50, db_index=True)
    district_id = models.IntegerField(db_index=True)
    district_code = models.CharField(max_length=15, db_index=True)
    district_name = models.CharField(max_length=250, db_index=True)
    precinct_code = models.IntegerField(db_index=True)
    precinct_part = models.IntegerField(db_index=True)


class RaceCandidate(models.Model):
    """
    Contains details of individual candidates in individual races.
    """
    race_name = models.CharField(max_length=50, db_index=True)
    race_position_name = models.CharField(max_length=50, db_index=True)
    candidate_name = models.CharField(max_length=200, db_index=True)
    party_name = models.CharField(max_length=50, db_index=True)
    county_display = models.CharField(max_length=250, db_index=True)


class BallotCandidate(models.Model):
    """
    From SOS ballot info db: contains details on individual candidates.
    """
    ballot_name = models.CharField(max_length=200, db_index=True)
    candidate_id = models.IntegerField(db_index=True)
    city = models.CharField(max_length=200, db_index=True)
    display_order_general = models.IntegerField(blank=True, null=True)
    display_order_primary = models.IntegerField(blank=True, null=True)
    election_year = models.IntegerField()

    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)

    is_filing_approved = models.BooleanField(db_index=True)
    is_locked_out_general = models.BooleanField(db_index=True)
    is_locked_out_primary = models.BooleanField(db_index=True)
    is_withdrawn = models.BooleanField(db_index=True)
    is_writein = models.BooleanField(db_index=True)

    party_name = models.CharField(max_length=100, db_index=True)

    office = models.ForeignKey('BallotOffice', db_index=True, blank=True, null=True)


class BallotDistrictDistrictMap(models.Model):
    """
    From SOS ballot info db: maps child districts to parent districts.
    """
    child_district = models.ForeignKey('BallotDistrict', related_name='child', db_index=True)
    parent_district = models.ForeignKey(
        'BallotDistrict', related_name='parent', db_index=True)


class BallotDistrictPrecinctMap(models.Model):
    """
    From SOS ballot info db: maps precincts to (child?) districts.
    """
    county = models.CharField(max_length=2, db_index=True)
    district = models.ForeignKey('BallotDistrict', db_index=True)
    precinct = models.ForeignKey('BallotPrecinct', db_index=True)


class BallotDistrict(models.Model):
    """
    From SOS ballot info db: describes electoral districts.
    """
    county = models.CharField(max_length=2, db_index=True)
    display_order = models.IntegerField()
    district_code = models.CharField(max_length=30, db_index=True)
    district_id = models.IntegerField(db_index=True)
    district_name = models.CharField(max_length=200, db_index=True)
    district_type = models.ForeignKey(
        'BallotDistrictType', db_index=True, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    is_state_category = models.BooleanField(db_index=True)
    is_usable_by_measure = models.BooleanField(db_index=True)


class BallotDistrictType(models.Model):
    """
    From SOS ballot info db: describes types of electoral districts.
    """
    display_order = models.IntegerField()
    district_type = models.CharField(max_length=100)
    district_type_code = models.CharField(max_length=10)
    district_type_id = models.IntegerField(db_index=True)
    type_description = models.CharField(max_length=100)

    is_federal_category = models.BooleanField(db_index=True)
    is_state_category = models.BooleanField(db_index=True)


class BallotElection(models.Model):
    """
    From SOS ballot info db: describes an election.
    """
    certification_date = models.DateField(db_index=True, blank=True, null=True)
    election_date = models.DateField(db_index=True, blank=True, null=True)
    election_name = models.CharField(max_length=50, db_index=True)

    election_id = models.IntegerField(db_index=True)
    general_election_id = models.IntegerField(db_index=True, blank=True, null=True)

    is_current = models.BooleanField(db_index=True)
    is_general = models.BooleanField(db_index=True)
    is_special = models.BooleanField(db_index=True)
    is_state_primary = models.BooleanField(db_index=True)

    def __str__(self):
        return '%s (%s)' % (self.election_name, self.election_date)


class BallotOffice(models.Model):
    """
    From SOS ballot info db: describes an office.
    """
    display_order = models.IntegerField(blank=True, null=True)
    election_code = models.CharField(max_length=25, db_index=True, blank=True, null=True)
    office_id = models.IntegerField(db_index=True)
    office_name = models.CharField(max_length=100)
    reporting_name = models.CharField(max_length=100)

    district = models.ForeignKey(BallotDistrict, db_index=True, blank=True, null=True)
    general_election = models.ForeignKey(
        BallotElection, related_name='general_election', db_index=True, blank=True, null=True)
    primary_election = models.ForeignKey(
        BallotElection, related_name='primary_election', db_index=True, blank=True, null=True)
    subject_election = models.ForeignKey(
        BallotElection, related_name='subject_election', db_index=True, blank=True, null=True)


class BallotPrecinct(models.Model):
    """
    From SOS ballot info db: describes a precinct.
    """
    county = models.CharField(max_length=2, db_index=True)
    levy_code = models.IntegerField(db_index=True)
    precinct_code = models.IntegerField(db_index=True)
    precinct_id = models.IntegerField(db_index=True)
    precinct_name = models.CharField(max_length=100, db_index=True)


class BallotRaceSummary(models.Model):
    """
    From SOS ballot info db: describes an individual race.
    """
    ballot_display_order = models.IntegerField(blank=True, null=True)
    ballot_id = models.IntegerField(db_index=True, blank=True, null=True)
    ballot_name = models.CharField(max_length=500)
    ballot_name_with_party = models.CharField(max_length=750)
    county = models.CharField(max_length=2)
    county_display = models.CharField(max_length=500)
    county_name = models.CharField(max_length=50)
    display_order = models.IntegerField(blank=True, null=True)
    party_code = models.CharField(max_length=10)
    party_name = models.CharField(max_length=50)
    race_id = models.IntegerField(db_index=True)
    race_name = models.CharField(max_length=500)

    election = models.ForeignKey(BallotElection, db_index=True, blank=True, null=True)
    district = models.ForeignKey(BallotDistrict, db_index=True, blank=True, null=True)

    def __str__(self):
        return '%s (%s)' % (self.ballot_name, self.race_name)


class SOSPDCMap(models.Model):
    """
    Connects a PDC committee to an SOS ballot db candidate.
    """
    pdc_filer_id = models.CharField(max_length=30, db_index=True)
    pdc_name = models.CharField(max_length=500, db_index=True)
    sos_ballot_name = models.CharField(max_length=500, db_index=True)
    sos_ballot_id = models.IntegerField(db_index=True)


class ScrapedCommittee(models.Model):
    """
    Contains details on a PDC committee obtained by scraping.
    """
    filer_id = models.CharField(max_length=30, db_index=True)
    pdc_url = models.URLField()
    name = models.CharField(max_length=200, db_index=True)
    party = models.CharField(max_length=50)
    office = models.CharField(max_length=250)
    committee_group = models.CharField(max_length=20, db_index=True)
    filing_year = models.IntegerField()

    def get_absolute_url(self):
        return reverse('committee', kwargs={'committee_id': str(self.id)})


class ScrapedContribution(models.Model):
    """
    Contains individual contributions obtained by scraping PDC.
    """
    donor = models.CharField(max_length=500, db_index=True)
    date = models.DateField(db_index=True, blank=True, null=True)
    amount = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    primary_general = models.CharField(max_length=15, db_index=True, blank=True, null=True)
    city = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    state = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    zipcode = models.CharField(max_length=11, db_index=True, blank=True, null=True)
    employer = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    occupation = models.CharField(max_length=100, db_index=True, blank=True, null=True)

    filing_committee = models.ForeignKey(ScrapedCommittee, db_index=True)
    dedupe_cluster = models.ForeignKey('DedupedCluster', db_index=True, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('contribution', kwargs={'contribution_id': str(self.id)})


class ScrapedInkind(models.Model):
    """
    Contains individual in-kind contributions obtained by scraping PDC.
    """
    donor = models.CharField(max_length=500, db_index=True)
    date = models.DateField(db_index=True)
    amount = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    primary_general = models.CharField(max_length=15, db_index=True)
    city = models.CharField(max_length=50, db_index=True)
    state = models.CharField(max_length=50, db_index=True)
    zipcode = models.CharField(max_length=11, db_index=True)
    employer = models.CharField(max_length=100, db_index=True)
    occupation = models.CharField(max_length=100, db_index=True)
    description = models.CharField(max_length=300, db_index=True)

    filing_committee = models.ForeignKey(ScrapedCommittee, db_index=True)

    def get_absolute_url(self):
        return reverse('inkind', kwargs={'inkind_id': str(self.id)})


class ScrapedExpense(models.Model):
    """
    Contains individual expenses obtained by scraping PDC.
    """
    vendor = models.CharField(max_length=500, db_index=True)
    date = models.DateField(db_index=True)
    amount = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    city = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    state = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    zipcode = models.CharField(max_length=11, db_index=True, blank=True, null=True)
    description = models.CharField(max_length=300, db_index=True, blank=True, null=True)

    filing_committee = models.ForeignKey(ScrapedCommittee, db_index=True)

    def get_absolute_url(self):
        return reverse('expense', kwargs={'expense_id': str(self.id)})


class ScrapedTotals(models.Model):
    """
    Contains totals for various types of activity for a committee.
    """
    raised = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    spent = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    inkinds = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    loans = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    ie_for = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    ie_against = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)

    filing_committee = models.ForeignKey(ScrapedCommittee, db_index=True)

class ScrapedRefund(models.Model):
    """
    Represents an individual refund issued by a campaign to a donor.
    """
    donor = models.CharField(max_length=500, db_index=True)
    date = models.DateField(db_index=True, blank=True, null=True)
    amount = models.DecimalField(
        max_digits=CURRENCY_FIELDS_MAX_DIGITS,
        decimal_places=CURRENCY_FIELDS_NUM_DECIMALS,
        blank=True,
        null=True)
    city = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    state = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    zipcode = models.CharField(max_length=11, db_index=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True, db_index=True)

    filing_committee = models.ForeignKey(ScrapedCommittee, db_index=True)

    def get_absolute_url(self):
        return reverse('campfin_data.views.scraped.refund', args=[str(self.id)])

class DedupedCluster(models.Model):
    """
    Represents a cluster of entities generated by dedupe.
    """
    slug = models.SlugField(max_length=500, db_index=True, blank=True, null=True)
