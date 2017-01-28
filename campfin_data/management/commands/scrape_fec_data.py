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
from django.db import utils
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
        parser.add_argument('--load-cmtes',
            action='store_true',
            dest='load_cmtes',
            default=False,
            help='Flush and load race metadata for federal races')

        parser.add_argument('--contribs-only',
            action='store_true',
            dest='contribs_only',
            default=False,
            help='Only fetch contribs for races')

        parser.add_argument('--expenses-only',
            action='store_true',
            dest='expenses_only',
            default=False,
            help='Only fetch expenses for races')

        parser.add_argument('--totals-only',
            action='store_true',
            dest='totals_only',
            default=False,
            help='Only fetch totals for races')

    def handle(self, *args, **options):
        if options['load_cmtes']:
            self.load_cmtes()
        if not options['totals_only'] and not options['expenses_only']:
            self.load_contributions()
            self.load_committee_contributions()
        if not options['contribs_only'] and not options['totals_only']:
            self.load_expenditures()
        if not options['contribs_only'] and not options['expenses_only']:
            self.load_totals()

    def repeatedly_fetch_json(self, url, num_retries):
        #logging.info('Fetching %s' % url)
        r = requests.get(url)
        time.sleep(0.3)

        try:
            results = r.json()['results']
            if not results:
                return {'results': []}
            else:
                #logging.info('Found %d results' % len(results))
                return r.json()
        except Exception, e:
            if (num_retries > 0):
                logging.info('Hit error %s retrieving JSON for %s; retrying %d more times' % (
                    e, url, num_retries - 1))
                # exponential-ish backoff
                time.sleep(2 * (1 + abs(10 - num_retries)))
                return self.repeatedly_fetch_json(url, num_retries - 1)
            else:
                logging.info(
                    'Hit error %s retrieving JSON for %s but max retries exceeded' % (
                        e, url))
                return {'results': []}

    def load_totals(self):
        logging.info('Loading totals')
        filings_base_url = (
            'https://api.open.fec.gov/v1/committee/%s/totals/?cycle=2016&sort=-cycle&'
            'per_page=20&api_key=%s&page=1')

        for cmte in ScrapedCommittee.objects.filter(committee_group='federal'):
            ScrapedTotals.objects.filter(filing_committee=cmte).delete()

            total = ScrapedTotals.objects.create(
                filing_committee=cmte,
                raised=0.,
                spent=0.,
                ie_for=0.,
                ie_against=0.,
                inkinds=0.,
                loans=0.)
            url = filings_base_url % (cmte.filer_id, settings.FEC_API_KEY)
            results = self.repeatedly_fetch_json(url, settings.NUM_FEC_RETRIES)
            if not results['results']:
                logging.info('No results for %s' % cmte.filer_id)
                continue

            for result in results['results']:
                total.raised += result['receipts'] if result['receipts'] else 0.
                total.spent += result['disbursements'] if result['disbursements'] else 0.
                total.ie_for += 0
                total.ie_against += 0
                total.inkinds += 0
                if 'loans_received' in result and result['loans_received']:
                    total.loans += result['loans_received']
                else:
                    if 'loans' in result and result['loans']:
                        total.loans += result['loans']
            total.save()
        
            logging.info('Saved totals metadata for %s: %s received, %s spent, %s loaned' % (
                cmte.filer_id, total.raised, total.spent, total.loans))

    def load_contributions(self):
        logging.info('Loading contributions')
        filings_base_url = (
            'https://api.open.fec.gov/v1/schedules/schedule_a/?is_individual=true&'
            'two_year_transaction_period=2016&per_page=100&api_key=%s&committee_id=%s%s%s')

        refund_total = 0.
        for cmte in ScrapedCommittee.objects.filter(committee_group='federal'):
            logging.info('Currently have %d contribs to %s (%s)' % (
                ScrapedContribution.objects.filter(filing_committee=cmte).count(),
                cmte.filer_id,
                cmte.name))
            cand_refund_total = 0.
            ScrapedContribution.objects.filter(filing_committee=cmte).delete()

            pagination = {}

            if cmte.office == 'President' and cmte.filer_id not in ['C00575795', 'C00580100']:
                logging.info('Skipping committee %s (%s)' % (cmte.filer_id, cmte.name))
                continue

            while True:
                if pagination and pagination['last_indexes']:
                    suffix = '&%s' % '&'.join(
                        ['%s=%s' % (
                            k,
                            pagination['last_indexes'][k]
                         ) for k in pagination['last_indexes']])
                else:
                    suffix = ''

                if cmte.office == 'President':
                    state_filter = '&contributor_state=WA'
                else:
                    state_filter = ''

                url = filings_base_url % (
                    settings.FEC_API_KEY, cmte.filer_id, state_filter, suffix)
                results = self.repeatedly_fetch_json(url, settings.NUM_FEC_RETRIES)
                if not results['results']:
                    logging.info('Now have %d contribs to %s (%s)' % (
                        ScrapedContribution.objects.filter(filing_committee=cmte).count(),
                        cmte.filer_id,
                        cmte.name))
                    break

                pagination = results['pagination']

                for entry in results['results']:
                    contrib_date = None

                    """
                    Don't give the campaigns too much credit. If they haven't disclosed a
                    refund, don't give them prospective credit. This is mostly an issue for
                    Trump.
                    if float(entry['contribution_receipt_amount']) > 0 and (
                        (entry['memo_text'] and
                            entry['memo_text'].lower().find('refund') != -1) or
                        (entry['receipt_type_full'] and
                            entry['receipt_type_full'].lower().find('refund') != -1)):
                        logging.info('Found refund memo: %s and %s' % (
                            entry['memo_text'], entry['receipt_type_full']))
                        logging.info('%s to %s from %s' % (
                            entry['contribution_receipt_amount'],
                            cmte.name,
                            entry['contributor_name']))
                        refund_total += float(entry['contribution_receipt_amount'])
                        cand_refund_total += float(entry['contribution_receipt_amount'])
                        logging.info('Refund: %s' % entry)
                        continue
                    """

                    if entry['contribution_receipt_date']:
                        contrib_date = datetime.strptime(
                            entry['contribution_receipt_date'], '%Y-%m-%dT%H:%M:%S')

                    if not entry['contributor_name']:
                        logging.info('No donor for %s' % entry['pdf_url'])
                    else:
                        try:
                            ScrapedContribution.objects.create(
                                donor=entry['contributor_name'],
                                date=contrib_date,
                                amount=entry['contribution_receipt_amount'],
                                primary_general=entry['fec_election_type_desc'],
                                city=entry['contributor_city'],
                                state=entry['contributor_state'],
                                zipcode=entry['contributor_zip'],
                                employer=entry['contributor_employer'],
                                occupation=entry['contributor_occupation'],
                                filing_committee=cmte
                            )
                        except Exception, e:
                            logging.info('Error loading contribution %s: %s' % (entry, e))
            logging.info('Found %d in refunds to %s' % (cand_refund_total, cmte.name))
        logging.info('Found %d refunds overall' % refund_total)

    def load_committee_contributions(self):
        logging.info('Loading committee contributions')
        filings_base_url = (
            'https://api.open.fec.gov/v1/schedules/schedule_a/?contributor_type=committee&'
            'api_key=%s&committee_id=%s&two_year_transaction_period=2016%s%s')

        refund_total = 0.
        for cmte in ScrapedCommittee.objects.filter(committee_group='federal'):
            logging.info('Currently have %d contribs to %s (%s)' % (
                ScrapedContribution.objects.filter(filing_committee=cmte).count(),
                cmte.filer_id,
                cmte.name))
            cand_refund_total = 0.
            pagination = {}

            if cmte.office == 'President' and cmte.filer_id not in ['C00575795', 'C00580100']:
                logging.info('Skipping committee %s (%s)' % (cmte.filer_id, cmte.name))
                continue

            while True:
                if pagination and pagination['last_indexes']:
                    suffix = '&%s' % '&'.join(
                        ['%s=%s' % (
                            k,
                            pagination['last_indexes'][k]
                         ) for k in pagination['last_indexes']])
                else:
                    suffix = ''

                if cmte.office == 'President':
                    state_filter = '&contributor_state=WA'
                else:
                    state_filter = ''

                url = filings_base_url % (
                    settings.FEC_API_KEY, cmte.filer_id, state_filter, suffix)
                results = self.repeatedly_fetch_json(url, settings.NUM_FEC_RETRIES)
                if not results['results']:
                    logging.info('Now have %d contribs to %s (%s)' % (
                        ScrapedContribution.objects.filter(filing_committee=cmte).count(),
                        cmte.filer_id,
                        cmte.name))
                    break

                pagination = results['pagination']

                for entry in results['results']:
                    contrib_date = None

                    if entry['contribution_receipt_date']:
                        contrib_date = datetime.strptime(
                            entry['contribution_receipt_date'], '%Y-%m-%dT%H:%M:%S')

                    if not entry['contributor_name']:
                        logging.info('No donor for %s' % entry['pdf_url'])
                    else:
                        try:
                            ScrapedContribution.objects.create(
                                donor=entry['contributor_name'],
                                date=contrib_date,
                                amount=entry['contribution_receipt_amount'],
                                primary_general=entry['fec_election_type_desc'],
                                city=entry['contributor_city'],
                                state=entry['contributor_state'],
                                zipcode=entry['contributor_zip'],
                                employer=entry['contributor_employer'],
                                occupation=entry['contributor_occupation'],
                                filing_committee=cmte
                            )
                        except Exception, e:
                            logging.info('Error loading contribution %s: %s' % (entry, e))
            logging.info('Found %d in refunds to %s' % (cand_refund_total, cmte.name))
        logging.info('Found %d refunds overall' % refund_total)

    def load_expenditures(self):
        logging.info('Loading expenditures')
        filings_base_url = (
            'https://api.open.fec.gov/v1/schedules/schedule_b/?'
            'two_year_transaction_period=2016&per_page=100&api_key=%s&committee_id=%s%s%s')

        for cmte in ScrapedCommittee.objects.filter(committee_group='federal'):
            logging.info('Currently have %d expenditures and %d refunds for %s (%s)' % (
                ScrapedExpense.objects.filter(filing_committee=cmte).count(),
                ScrapedRefund.objects.filter(filing_committee=cmte).count(),
                cmte.filer_id,
                cmte.name))
            ScrapedExpense.objects.filter(filing_committee=cmte).delete()
            ScrapedRefund.objects.filter(filing_committee=cmte).delete()

            pagination = {}

            if cmte.office == 'President' and cmte.filer_id not in ['C00575795', 'C00580100']:
                logging.info('Skipping committee %s (%s)' % (cmte.filer_id, cmte.name))
                continue

            while True:
                if pagination and pagination['last_indexes']:
                    suffix = '&%s' % '&'.join(
                        ['%s=%s' % (
                            k,
                            pagination['last_indexes'][k]
                         ) for k in pagination['last_indexes']])
                else:
                    suffix = ''

                if cmte.office == 'President':
                    state_filter = '&recipient_state=WA'
                else:
                    state_filter = ''

                url = filings_base_url % (
                    settings.FEC_API_KEY, cmte.filer_id, state_filter, suffix)
                results = self.repeatedly_fetch_json(url, settings.NUM_FEC_RETRIES)
                if not results['results']:
                    logging.info('Now have %d expenditures for %s (%s)' % (
                        ScrapedExpense.objects.filter(filing_committee=cmte).count(),
                        cmte.filer_id,
                        cmte.name))
                    break

                pagination = results['pagination']

                for entry in results['results']:
                    contrib_date = None
                    if entry['disbursement_date']:
                        contrib_date = datetime.strptime(
                            entry['disbursement_date'], '%Y-%m-%dT%H:%M:%S')

                    try:
                        ScrapedExpense.objects.create(
                            vendor=entry['recipient_name'],
                            date=contrib_date,
                            amount=entry['disbursement_amount'],
                            city=entry['recipient_city'],
                            state=entry['recipient_state'],
                            zipcode=entry['recipient_zip'],
                            description='%s: %s' % (
                                entry['disbursement_purpose_category'],
                                entry['disbursement_description']),
                            filing_committee=cmte
                       )
                    except Exception, e:
                        logging.info('Error loading expenditure %s: %s' % (entry, e))

                    if entry['disbursement_purpose_category'].upper() == 'REFUNDS':
                        ScrapedRefund.objects.create(
                            filing_committee=cmte,
                            donor=entry['recipient_name'],
                            date=contrib_date,
                            amount=entry['disbursement_amount'],
                            city=entry['recipient_city'],
                            state=entry['recipient_state'],
                            zipcode=entry['recipient_zip'],
                            description=entry['disbursement_description'])

    def load_cmtes(self):
        logging.info('Flushing and loading cmtes')
        deleted = ScrapedCommittee.objects.filter(committee_group='federal').delete()
        logging.info('Flushed %s committees' % locale.format('%d', deleted[0], grouping=True))

        fec_url = (
            'http://www.fec.gov/fecviewer/CandidateCommitteeDetail.do?'
            'candidateCommitteeId=%s&tabIndex=1')

        for district in range(1, 11):
            house_url = (
                'https://api.open.fec.gov/v1/elections/?district=%s&sort=-total_receipts&page=1'
                '&office=house&per_page=20&state=WA&cycle=2016&api_key=%s')
            url = house_url % (district, settings.FEC_API_KEY)
            results = self.repeatedly_fetch_json(url, settings.NUM_FEC_RETRIES)

            for result in results['results']:
                for cmte_id in result['committee_ids']:
                    ScrapedCommittee.objects.create(
                        filer_id=cmte_id,
                        pdc_url=fec_url % cmte_id,
                        name=result['candidate_name'],
                        party=result['party_full'],
                        office='House, District %d' % district,
                        committee_group='federal')

        statewide_url = (
            'https://api.open.fec.gov/v1/elections/?sort=-total_receipts&page=1&office=%s'
            '&per_page=200%s&cycle=2016&api_key=%s')
        for office in ['senate', 'president']:
            if office == 'senate':
                state = '&state=WA'
            else:
                state = ''
            url = statewide_url % (office, state, settings.FEC_API_KEY)
            results = self.repeatedly_fetch_json(url, settings.NUM_FEC_RETRIES)

            for result in results['results']:
                for cmte_id in result['committee_ids']:
                    try:
                        ScrapedCommittee.objects.create(
                            filer_id=cmte_id,
                            pdc_url=fec_url % cmte_id,
                            name=result['candidate_name'],
                            party=result['party_full'],
                            office=office.title(),
                            committee_group='federal')
                    except utils.IntegrityError:
                        continue
