import locale
import logging

from campfin_data.models import *
from campfin_data.utils import *
from datetime import datetime
from django.conf import settings
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

"""
Basic detail views
"""

def committee(request, committee_id):
	try:
		committee = ScrapedCommittee.objects.get(id=committee_id)
		try:
			totals = ScrapedTotals.objects.get(filing_committee=committee)
		except:
			totals = None
		try:
			other_years = ScrapedCommittee.objects.filter(
				filer_id=committee.filer_id).exclude(id=committee_id).order_by('-filing_year')
		except:
			other_years = None
		return render(
			request,
			'campfin_data/scraped/committee.html',
			{
				'committee': committee,
				'totals': totals,
				'other_years': other_years
			}
		)
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def filer_id(request, filer_id):
	try:
		committees = ScrapedCommittee.objects.filter(filer_id=filer_id).order_by('-filing_year')
		try:
			totals = ScrapedTotals.objects.filter(filing_committee__in=committees).aggregate(
				Sum('raised'),
				Sum('spent'),
				Sum('inkinds'),
				Sum('loans'),
				Sum('ie_for'),
				Sum('ie_against'))
		except:
			totals = None
		return render(
			request,
			'campfin_data/scraped/committee.html',
			{
				'committees': committees,
				'aggregated_totals': totals,
			}
		)
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def contribution(request, contribution_id):
	try:
		contribution = ScrapedContribution.objects.get(id=contribution_id)
		return render(
			request,
			'campfin_data/scraped/contribution.html',
			{
				'contribution': contribution
			}
		)
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def inkind(request, inkind_id):
	try:
		inkind = ScrapedInkind.objects.get(id=inkind_id)
		return render(
			request,
			'campfin_data/scraped/inkind.html',
			{
				'inkind': inkind
			}
		)
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def expense(request, expense_id):
	try:
		expense = ScrapedExpense.objects.get(id=expense_id)
		return render(
			request,
			'campfin_data/scraped/expense.html',
			{
				'expense': expense
			}
		)
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def refund(request, refund_id):
	try:
		refund = ScrapedRefund.objects.get(id=refund_id)
		return render(
			request,
			'campfin_data/scraped/refund.html',
			{
				'refund': refund
			}
		)
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})


"""
JSON-returning views (i.e. data endpoints)
"""

def contributions_for_committee(request, committee_id=None, filer_id=None):
	try:
		if committee_id:
			committee = ScrapedCommittee.objects.get(id=committee_id)
			try:
				contributions = ScrapedContribution.objects.filter(filing_committee=committee)
			except:
				contributions = None
		elif filer_id:
			committees = ScrapedCommittee.objects.filter(filer_id=filer_id)
			try:
				contributions = ScrapedContribution.objects.filter(filing_committee__in=committees)
			except:
				contributions = None

		return JsonResponse({
			'data': [
				{
					'donor': c.donor,
					'amount': float(c.amount),
					'date': c.date,
					'employer': c.employer,
					'occupation': c.occupation,
					'city': c.city,
					'state': c.state,
					'zipcode': c.zipcode,
					'primary_general': c.primary_general
				} for c in contributions]
		})

	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def inkinds_for_committee(request, committee_id=None, filer_id=None):
	try:
		if committee_id:
			committee = ScrapedCommittee.objects.get(id=committee_id)
			try:
				inkinds = ScrapedInkind.objects.filter(filing_committee=committee)
			except:
				inkinds = None
		elif filer_id:
			committees = ScrapedCommittee.objects.filter(filer_id=filer_id)
			try:
				inkinds = ScrapedInkind.objects.filter(filing_committee__in=committees)
			except:
				inkinds = None

		return JsonResponse({
			'data': [
				{
					'donor': i.donor,
					'amount': float(i.amount),
					'date': i.date,
					'employer': i.employer,
					'occupation': i.occupation,
					'description': i.description,
					'city': i.city,
					'state': i.state,
					'zipcode': i.zipcode,
					'primary_general': i.primary_general
				} for i in inkinds]
		})

	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def expenses_for_committee(request, committee_id=None, filer_id=None):
	try:
		if committee_id:
			committee = ScrapedCommittee.objects.get(id=committee_id)
			try:
				expenses = ScrapedExpense.objects.filter(filing_committee=committee)
			except:
				expenses = None
		elif filer_id:
			committees = ScrapedCommittee.objects.filter(filer_id=filer_id)
			try:
				expenses = ScrapedExpense.objects.filter(filing_committee__in=committees)
			except:
				expenses = None

		return JsonResponse({
			'data': [
				{
					'vendor': e.vendor,
					'amount': float(e.amount),
					'date': e.date,
					'description': e.description,
					'city': e.city,
					'state': e.state,
					'zipcode': e.zipcode,
				} for e in expenses]
		})

	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})

def refunds_for_committee(request, committee_id=None, filer_id=None):
	try:
		if committee_id:
			committee = ScrapedCommittee.objects.get(id=committee_id)
			try:
				refunds = ScrapedRefund.objects.filter(filing_committee=committee)
			except:
				refunds = None
		elif filer_id:
			committees = ScrapedCommittee.objects.filter(filer_id=filer_id)
			try:
				refunds = ScrapedRefund.objects.filter(filing_committee__in=committees)
			except:
				refunds = None

		return JsonResponse({
			'data': [
				{
					'donor': r.donor,
					'amount': float(r.amount),
					'date': r.date,
					'description': r.description,
					'city': r.city,
					'state': r.state,
					'zipcode': r.zipcode,
				} for r in refunds]
		})
	except Exception, e:
		return render(request, 'campfin_data/error.html', {'message': e})
