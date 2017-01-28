import locale
import logging
import os
import requests
import time

from base64 import b64encode, b64decode
from csv import DictReader, DictWriter
from datetime import datetime
from lxml import etree
from StringIO import StringIO

from django.conf import settings
from campfin_data.models import *
from campfin_data.utils import *
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except:
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes all PDC races from Candidates page for given year and type'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument('--year',
            type=int,
            dest='race_year',
            help='Year to fetch races for')

    def handle(self, *args, **options):
        year = datetime.today().year
        if options['race_year'] is not None:
            year = options['race_year']

        logging.info('Fetching committees for %s' % year)

        cmte_types = [
            'sw', 'leg', 'jud', 'loc', 'continuing', 'single_year', 'initiative', 'caucus',
            'party_state', 'party_legdist', 'party_county', 'party_associated', 'party_minor']
        for cmte_type in cmte_types:
            cmtes = self.fetch_committees(cmte_type, year)
            self.write_committees(cmtes, cmte_type, year)

        logging.info('Done fetching committees')

    def fetch_committees(self, cmte_type, year):
        keep_going = True
        counter = 1
        committees = []
        prefix = '/MvcQuerySystem/CandidateData/contributions?param='
        directory = 'Candidate'
        suffix = 'candidates'
        if cmte_type in [
            'continuing', 'single_year', 'initiative', 'caucus', 'party_state',
            'party_legdist', 'party_county', 'party_associated', 'party_minor']:
            prefix = '/MvcQuerySystem/CommitteeData/contributions?param='
            directory = 'Committee'
            suffix = 'committees'
        headers = {
            'sw': [
                'link', 'name', 'office', 'party', 'raised', 'spent', 'debt', 'ie_support',
                'ie_oppose'],
            'leg': [
                'link', 'name', 'district', 'office', 'position', 'party', 'raised', 'spent',
                'debt', 'ie_support', 'ie_oppose'],
            'loc': [
                'link', 'name', 'locality', 'office', 'position', 'party', 'raised', 'spent',
                'debt', 'ie_support', 'ie_oppose'],
            'jud': [
                'link', 'name', 'court', 'division', 'position', 'raised', 'spent', 'debt',
                'ie_support', 'ie_oppose'],
            'continuing': ['link', 'name', 'type', 'raised', 'spent', 'debt'],
            'single_year': [
                'link', 'name', 'locality', 'for/against', 'raised', 'spent', 'debt'],
            'initiative': [
                'link', 'name', 'ballot', 'for/against', 'raised', 'spent', 'debt'],
            'caucus': ['link', 'name', 'party', 'raised', 'spent', 'debt'],
            'party_state': ['link', 'name', 'party', 'raised', 'spent', 'debt'],
            'party_legdist': ['link', 'name', 'party', 'raised', 'spent', 'debt'],
            'party_county': ['link', 'name', 'party', 'raised', 'spent', 'debt'],
            'party_associated': ['link', 'name', 'party', 'raised', 'spent', 'debt'],
            'party_minor': ['link', 'name', 'party', 'raised', 'spent', 'debt']
        }
        header = headers[cmte_type]

        while keep_going:
            url = 'http://web.pdc.wa.gov/MvcQuerySystem/%s/%s_%s?page=%d&year=%d' % (
                directory, cmte_type, suffix, counter, year)

            try:
                response = requests.get(url, headers=settings.PDC_SCRAPER_CONTACT_HEADERS)
            except Exception, e:
                logging.info('Error fetching %s; retrying' % url)
                try:
                    time.sleep(5)
                    response = requests.get(url, headers=settings.PDC_SCRAPER_CONTACT_HEADERS)
                except Exception, e:
                    logging.info('Second error with %s; bailing' % url)
                    break
            

            parser = etree.HTMLParser()
            tree = etree.parse(StringIO(response.text), parser)

            found = False
            committee = {}
            table = tree.xpath('//*[@id="grid1"]/table/tbody/tr/td')
            for idx, entry in enumerate(table):
                if committee and idx % len(header) == 0:
                    found = True
                    committees.append(committee)

                    try:
                        cmte_obj, created = ScrapedCommittee.objects.get_or_create(
                            filer_id=committee['filer_id'],
                            pdc_url=committee['link'],
                            name=committee['name'],
                            party=committee.get('party', ''),
                            office=committee.get('office', ''),
                            committee_group=cmte_type,
                            filing_year=year)
                    except Exception, e:
                        logging.info('New committee, not creating another for error %s: %s' % (
                            committee, e))
                        existing = ScrapedCommittee.objects.get(
                            filer_id=committee['filer_id'])
                        logging.info('Existing committee: %s' % '; '.join([
                            existing.filer_id,
                            existing.pdc_url,
                            existing.name,
                            existing.party,
                            existing.office,
                            existing.committee_group,
                            str(existing.filing_year)]))

                    committee = {}
                if entry.text:
                    committee[header[idx % len(header)]] = entry.text.encode(
                        'utf8', 'replace')
                if entry.getchildren():
                    try:
                        url = entry.getchildren()[0].attrib['href']
                        if url.startswith(prefix):
                            encoded = url.replace(prefix, '')[:16]
                            committee['filer_id'] = b64decode(encoded)
                            committee[header[idx % len(header)]] = (
                                'http://web.pdc.wa.gov%s' % url)
                    except Exception:
                        committee[header[idx % len(header)]] = ''
                        committee['filer_id'] = 'Unknown'
                        logging.info('Error fetching url at position %d' % idx)

            if not found:
                break
            elif committee:
                try:
                    cmte_obj, created = ScrapedCommittee.objects.get_or_create(
                        filer_id=committee['filer_id'],
                        pdc_url=committee['link'],
                        name=committee['name'],
                        party=committee.get('party', ''),
                        office=committee.get('office', ''),
                        committee_group=cmte_type,
                        filing_year=year)
                    committees.append(committee)
                except Exception, e:
                    logging.info('New committee: %s, not creating another new one for error %s' % (
                        committee, e))
                    existing = ScrapedCommittee.objects.get(
                        filer_id=committee['filer_id'])
                    logging.info('Existing committee: %s' % '; '.join([
                        existing.filer_id,
                        existing.pdc_url,
                        existing.name,
                        existing.party,
                        existing.office,
                        existing.committee_group,
                        str(existing.filing_year)]))

            counter += 1
            time.sleep(1)

        return committees

    def write_committees(self, cmtes, cmte_type, year):
        path = os.path.join(
            settings.DATA_DIR, 'pdc_scraped_data', 'committees_%s_%d.csv' % (cmte_type, year))
        with open(path, 'w+') as fh:
            if not cmtes:
                logging.info('No committees of type %s for year %s' % (cmte_type, year))
                return
            writer = DictWriter(fh, cmtes[0].keys())
            writer.writeheader()
            writer.writerows(cmtes)