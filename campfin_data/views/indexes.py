import locale
import logging
import os
import requests

from campfin_data.models import *
from campfin_data.utils import *
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
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


@login_required
def index(request):
    template = loader.get_template('campfin_data/index.html')

    year = request.GET.get('year', 'all')

    if (year == 'all' or not year.isdigit()
            or int(year) < settings.MIN_FILING_YEAR
            or int(year) > settings.MAX_FILING_YEAR):
        year = 'all'
        contribs = ScrapedContribution.objects.all()
        expenses = ScrapedExpense.objects.all()
        committees = ScrapedCommittee.objects.all()
    else:
        contribs = ScrapedContribution.objects.filter(
            filing_committee__filing_year=year)
        expenses = ScrapedExpense.objects.filter(
            filing_committee__filing_year=year)
        committees = ScrapedCommittee.objects.filter(filing_year=year)

    context = {
        'title': 'Home',
        'showing_year': year,
        'years': [str(y) for y in range(
            settings.MIN_FILING_YEAR, settings.MAX_FILING_YEAR + 1)],
        'timestamp': datetime.now(timezone(settings.TIME_ZONE)),
        'contribs': locale.currency(
            contribs.aggregate(Sum('amount'))['amount__sum'], grouping=True),
        'expenses': locale.currency(
            expenses.aggregate(Sum('amount'))['amount__sum'], grouping=True),
        'committees': locale.format('%d', committees.count(), grouping=True)
    }
    return HttpResponse(template.render(context, request))
