from campfin_data.models import *
from haystack import indexes

class ScrapedCommitteeIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True, use_template=True)
	filing_year = indexes.IntegerField(model_attr='filing_year')

	def get_model(self):
		return ScrapedCommittee

class ScrapedContributionIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True, use_template=True)
	filing_year = indexes.IntegerField(model_attr='filing_committee__filing_year')

	def get_model(self):
		return ScrapedContribution

class ScrapedInkindIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True, use_template=True)
	filing_year = indexes.IntegerField(model_attr='filing_committee__filing_year')

	def get_model(self):
		return ScrapedInkind

class ScrapedExpenseIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True, use_template=True)
	filing_year = indexes.IntegerField(model_attr='filing_committee__filing_year')

	def get_model(self):
		return ScrapedExpense

class ScrapedRefundIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True, use_template=True)
	filing_year = indexes.IntegerField(model_attr='filing_committee__filing_year')

	def get_model(self):
		return ScrapedRefund