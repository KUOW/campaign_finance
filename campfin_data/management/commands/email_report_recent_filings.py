import locale
import logging

from boto import ses
from campfin_data.models import *
from campfin_data.utils import *
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template import loader

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except:
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Emails report of recent filing activity'

    def handle(self, *args, **options):
        cutoff_amount = settings.RECENT_FILING_AMOUNT_CUTOFF
        one_week = timedelta(days=7)
        week_ago = datetime.today() - one_week

        contribs = ScrapedContribution.objects.filter(
            date__gte=week_ago).order_by('-amount', '-date').filter(
            amount__gte=settings.RECENT_FILING_AMOUNT_CUTOFF)

        donors = contribs.values('donor').annotate(sum=Sum('amount')).order_by('-sum')
        for donor in donors:
            print '%s gave %s' % (donor['donor'], locale.currency(donor['sum'], grouping=True))
            filtered_contribs = contribs.filter(donor=donor['donor']).values(
                'filing_committee__name').annotate(sum=Sum('amount')).order_by('-sum')
            for contrib in filtered_contribs:
                print '%s to %s' % (locale.currency(contrib['sum'], grouping=True), contrib['filing_committee__name'])
            print '---'

        for address in settings.RECENT_FILING_REPORT_EMAIL_ADDRESSES:
            render_and_send_email(
                address,
                {
                    'contribs': contribs,
                    'begin_date': week_ago,
                    'amount': settings.RECENT_FILING_AMOUNT_CUTOFF
                },
                'recent_filing',
                'recent filing activity',
                payload=convert_list_of_models_to_csv_string(contribs))
