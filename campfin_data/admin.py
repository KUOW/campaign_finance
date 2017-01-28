from django.contrib import admin
from .models import *

admin.site.register(ScrapedCommittee)
admin.site.register(ScrapedContribution)
admin.site.register(ScrapedInkind)
admin.site.register(ScrapedExpense)
admin.site.register(ScrapedTotals)
admin.site.register(ScrapedRefund)