import locale
import logging
import os
import requests
import time

from base64 import b64encode, b64decode
from boto import ses
from campfin_data.models import *
from campfin_data.utils import *
from collections import OrderedDict
from csv import DictReader, DictWriter
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Sum, Count
from django.template import loader
from django.utils.text import slugify
from lxml import etree
from StringIO import StringIO

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except:
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes all PDC contributions for all races or a given filer id'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument('--year',
            type=int,
            dest='race_year',
            help='Year to fetch races for')

        parser.add_argument('--no-email',
            action='store_true',
            dest='no_email',
            default=False,
            help='Turn off sending emails')

        parser.add_argument('--cmte-type',
            type=str,
            dest='cmte_type',
            help='Only fetch results for this committee type')

    def handle(self, *args, **options):
        year = datetime.today().year
        if options['race_year'] is not None:
            year = options['race_year']

        logging.info('Fetching disclosures for %s' % year)

        types = OrderedDict()
        types['sw'] = 'statewide'
        types['leg'] = 'legislative'
        types['jud'] = 'judicial'
        types['loc'] = 'local'
        types['continuing'] = 'continuing'
        types['single_year'] = 'single_year'
        types['initiative'] = 'initiative'
        types['caucus'] = 'caucus'
        types['party_state'] = 'party_state'
        types['party_legdist'] = 'party_legdist'
        types['party_county'] = 'party_county'
        types['party_associated'] = 'party_associated'
        types['party_minor'] = 'party_minor'

        diff_results = []
        if options['cmte_type'] is not None:
            if options['cmte_type'] in types:
                types = {options['cmte_type']: types[options['cmte_type']]}
        for cmte_type in types:
            filer_data = self.load_filer_data(cmte_type, year)
            for filer in filer_data:
                contribs = self.fetch_pdc_data(
                    filer['filer_id'], types[cmte_type], year)
                in_kinds = self.fetch_pdc_data(
                    filer['filer_id'], types[cmte_type], year, 'inkind')
                expenditures = self.fetch_pdc_data(
                    filer['filer_id'], types[cmte_type], year, 'expenditures')

                self.write_pdc_data(contribs, filer['filer_id'], year, 'contributions')
                self.write_pdc_data(in_kinds, filer['filer_id'], year, 'inkinds')
                self.write_pdc_data(expenditures, filer['filer_id'], year, 'expenditures')
                time.sleep(1)
        if diff_results and not options['no_email']:
            self.email_diff_results(diff_results)

        logging.info('Done scraping and processing new disclosures for %s' % year)

        contribs = ScrapedContribution.objects.filter(filing_committee__filing_year=year)
        expenses = ScrapedExpense.objects.filter(filing_committee__filing_year=year)
        refunds = ScrapedRefund.objects.filter(filing_committee__filing_year=year)

        print '%s contribs for %s' % (
            locale.format('%d', contribs.count(), grouping=True),
            locale.currency(contribs.aggregate(Sum('amount'))['amount__sum'], grouping=True))
        print '%s expenses for %s' % (
            locale.format('%d', expenses.count(), grouping=True),
            locale.currency(expenses.aggregate(Sum('amount'))['amount__sum'], grouping=True))
        print '%s refunds for %s' % (
            locale.format('%d', refunds.count(), grouping=True),
            locale.currency(refunds.aggregate(Sum('amount'))['amount__sum'], grouping=True))

    def load_filer_data(self, cmte_type, year):
        path = os.path.join(
            settings.DATA_DIR, 'pdc_scraped_data', 'committees_%s_%d.csv' % (cmte_type, year))
        filer_data = []
        with open(path) as fh:
            reader = DictReader(fh)
            for row in reader:
                filer_data.append(row)
        return filer_data

    def fetch_pdc_data(self, filer_id, cmte_type, year, tab='contributions'):
        directory_prefix = 'Candidate'
        if cmte_type in [
            'continuing', 'single_year', 'initiative', 'caucus', 'party_state',
            'party_legdist', 'party_county', 'party_associated', 'party_minor']:
            directory_prefix = 'Committee'

        url = ('http://web.pdc.wa.gov/MvcQuerySystem/%sData/excel?param=%s==&year=%d&'
               'tab=%s&type=%s&page=&orderBy=&groupBy=&filterBy=') % (
               directory_prefix, b64encode(filer_id), year, tab, cmte_type)

        try:
            response = requests.get(url, headers=settings.PDC_SCRAPER_CONTACT_HEADERS)
        except Exception, e:
            logging.info('Error fetching %s; retrying' % url)
            try:
                time.sleep(5)
                response = requests.get(url, headers=settings.PDC_SCRAPER_CONTACT_HEADERS)
            except Exception, e:
                logging.info('Second error with %s; bailing' % url)
                return []
        response_strio = StringIO(response.text)

        contrib_text = ''
        offset = 4
        if tab == 'inkind':
            # We can skip the header row for in-kinds because we manually set it below
            offset = 5
        if tab == 'contributions':
            self.extract_and_save_totals(response_strio, filer_id, year)
        for line in response_strio.readlines()[offset:]:
            contrib_text += line

        contrib_strio = StringIO(contrib_text.encode('utf8', 'replace'))
        if tab == 'inkind':
            reader = DictReader(
                contrib_strio,
                fieldnames=['Contributor', 'Date', 'Amount', 'P/G', 'City', 'State', 'Zip',
                            'Employer', 'Occupation', 'Description'])
        else:
            reader = DictReader(contrib_strio)

        contribs = []
        for row in reader:
            # We want to work with rows with no extra spaces
            if None in row:
                for key in ['Description', ' Description']:
                    if key in row:
                        row[key] = '%s, %s' % (row[key], ', '.join(row[None]))
                        del row[None]
            try:
                contribs.append({key.strip(): row[key].strip() for key in row if key})
            except AttributeError:
                logging.info('AttributeError with row: %s' % row)
        return contribs

    def extract_and_save_totals(self, response_strio, filer_id, year):
        response_strio.seek(0)
        topline = response_strio.readlines()[:2]
        response_strio.seek(0)
        secondline = response_strio.readlines()[2:4]
        response_strio.seek(0)

        try:
            filer_committee = ScrapedCommittee.objects.get(filer_id=filer_id, filing_year=year)
        except Exception, e:
            logging.info('Error %s: bailing on storing totals to %s' % (e, filer_id))
            return
        ScrapedTotals.objects.filter(filing_committee=filer_committee).delete()

        topline_reader = DictReader(topline, skipinitialspace=True)
        secondline_reader = DictReader(secondline, skipinitialspace=True)

        total = ScrapedTotals.objects.create(filing_committee=filer_committee)
        line = next(topline_reader)

        try:
            total.raised = self.get_dollar_amount(line['Raised'])
            total.spent = self.get_dollar_amount(line['Spent'])
            if 'IEFor' in line:
                total.ie_for = self.get_dollar_amount(line['IEFor'])
            if 'IEAgainst' in line:
                total.ie_against = self.get_dollar_amount(line['IEAgainst'])

            line = next(secondline_reader)
            total.inkinds = self.get_dollar_amount(line['Inkind Contributions'])
            total.loans = self.get_dollar_amount(line['Loans'])
            
            total.save()
        except KeyError, e:
            logging.info('KeyError with %s' % e)

    def get_dollar_amount(self, text):
        text = text.replace('$', '')
        if text.find('(') != -1:
            return float(text.replace('(', '').replace(')', '')) * -1.
        return float(text)

    def write_pdc_data(
            self, itemized, filer_id, year, data_type, diff_type=''):
        if not len(itemized):
            return
        diff_suffix = ''
        if diff_type:
            diff_suffix = '_diff_%s' % diff_type
        path = os.path.join(
            settings.DATA_DIR,
            'pdc_scraped_data',
            data_type,
            '%s_%d%s.csv' % (slugify(filer_id), year, diff_suffix))

        with open(path, 'w+') as fh:
            writer = DictWriter(fh, itemized[0].keys(), skipinitialspace=True)
            writer.writeheader()
            writer.writerows(itemized)

        try:
            filer_committee = ScrapedCommittee.objects.get(filer_id=filer_id, filing_year=year)
        except Exception, e:
            logging.info('Error %s: bailing on storing %s to %s' % (e, data_type, filer_id))
            return

        placeholder_date = '1969-01-01'

        if data_type == 'contributions':
            ScrapedContribution.objects.filter(filing_committee=filer_committee).delete()
            for contrib in itemized:
                ScrapedContribution.objects.create(
                    filing_committee=filer_committee,
                    donor=contrib.get('Contributor', ''),
                    date=contrib.get('Date', placeholder_date),
                    amount=contrib.get('Amount', 0.),
                    primary_general=contrib.get('P/G', ''),
                    city=contrib.get('City', ''),
                    state=contrib.get('State', ''),
                    zipcode=contrib.get('Zip', ''),
                    employer=contrib.get('Employer', ''),
                    occupation=contrib.get('Occupation', ''))

        elif data_type == 'inkinds':
            ScrapedInkind.objects.filter(filing_committee=filer_committee).delete()
            for inkind in itemized:
                ScrapedInkind.objects.create(
                    filing_committee=filer_committee,
                    donor=inkind.get('Contributor', ''),
                    date=inkind.get('Date', placeholder_date),
                    amount=inkind.get('Amount', 0.),
                    primary_general=inkind.get('P/G', ''),
                    city=inkind.get('City', ''),
                    state=inkind.get('State', ''),
                    zipcode=inkind.get('Zip', ''),
                    employer=inkind.get('Employer', ''),
                    occupation=inkind.get('Occupation', ''),
                    description=inkind.get('Description', ''))

        else:
            ScrapedExpense.objects.filter(filing_committee=filer_committee).delete()
            ScrapedRefund.objects.filter(filing_committee=filer_committee).delete()
            for expense in itemized:
                ScrapedExpense.objects.create(
                    filing_committee=filer_committee,
                    vendor=expense.get('Vendor', ''),
                    date=expense.get('Date', placeholder_date),
                    amount=expense.get('Amount', 0.),
                    city=expense.get('City', ''),
                    state=expense.get('State', ''),
                    zipcode=expense.get('Zip', ''),
                    description=expense.get('Description', ''))

                if expense.get('Description', '').lower().find('refund') != -1:
                    ScrapedRefund.objects.create(
                        filing_committee=filer_committee,
                        donor=expense.get('Vendor', ''),
                        date=expense.get('Date', placeholder_date),
                        amount=expense.get('Amount', 0.),
                        city=expense.get('City', ''),
                        state=expense.get('State', ''),
                        zipcode=expense.get('Zip', ''),
                        description=expense.get('Description', ''))
