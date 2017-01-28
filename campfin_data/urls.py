from django.conf.urls import url

from views import geo, scraped

urlpatterns = [
    url(r'^committees/(?P<committee_id>[0-9]+)/$',
        scraped.committee,
        name='committee'),
    url(r'^committees/filer_id/(?P<filer_id>.+)/$',
        scraped.filer_id,
        name='filer_id'),
    url(r'^contributions/(?P<contribution_id>[0-9]+)/$',
        scraped.contribution,
        name='contribution'),
    url(r'^expenses/(?P<expense_id>[0-9]+)/$',
        scraped.expense,
        name='expense'),
    url(r'^inkinds/(?P<inkind_id>[0-9]+)/$',
        scraped.inkind,
        name='inkind'),
    url(r'^refunds/(?P<refund_id>[0-9]+)/$',
        scraped.refund,
        name='refund'),
    url(r'^json/committee_contribs/(?P<committee_id>[0-9]+)/$',
        scraped.contributions_for_committee,
        name='contribs_committee'),
    url(r'^json/committee_contribs/filer_id/(?P<filer_id>.+)/$',
        scraped.contributions_for_committee,
        name='contribs_committee'),
    url(r'^json/committee_inkinds/(?P<committee_id>[0-9]+)/$',
        scraped.inkinds_for_committee,
        name='inkinds_committee'),
    url(r'^json/committee_inkinds/filer_id/(?P<filer_id>.+)/$',
        scraped.inkinds_for_committee,
        name='inkinds_committee'),
    url(r'^json/committee_expenses/(?P<committee_id>[0-9]+)/$',
        scraped.expenses_for_committee,
        name='expenses_committee'),
    url(r'^json/committee_expenses/filer_id/(?P<filer_id>.+)/$',
        scraped.expenses_for_committee,
        name='expenses_committee'),
    url(r'^json/committee_refunds/(?P<committee_id>[0-9]+)/$',
        scraped.refunds_for_committee,
        name='refunds_committee'),
    url(r'^json/committee_refunds/filer_id/(?P<filer_id>.+)/$',
        scraped.refunds_for_committee,
        name='refunds_committee'),
    url(
        r'^ballot/?$',
        geo.ballot,
        name='ballot'),
    url(
        r'^geocode/?$',
        geo.geocode,
        name='geocode'),
    url(
        r'^my_ballot/?$',
        geo.my_ballot,
        name='my-ballot'),
    url(
        r'^metadata/(?P<district_id>[0-9]+).json$',
        geo.district_id_router,
        name='district_id_router')
]