from campfin.settings.base import *

DEBUG = False

#INSTALLED_APPS += [
#	'debug_toolbar'
#]

STATIC_ROOT = '/var/www/campfin_data/static'

ALLOWED_HOSTS = ['*', 'campfin.kuow.org']

DATA_DIR = os.path.join('/', 'home', 'ubuntu', 'code', 'campfin', 'data')
GEO_DATA_DIR = os.path.join(DATA_DIR, 'shapefiles')
SOS_BALLOTS_DIR = os.path.join(DATA_DIR, 'sos_ballots')
PDC_SCRAPED_DIR = os.path.join(DATA_DIR, 'pdc_scraped_data')

PDC_LOBBIO_PATH = os.path.join(PDC_DATA_DIR, 'dbo_lobbio_4_26_2016.csv')
PDC_LOBEMP_PATH = os.path.join(PDC_DATA_DIR, 'dbo_lobemp_4_26_2016.csv')
PDC_LOBL2_PATH = os.path.join(PDC_DATA_DIR, 'dbo_lobl2_4_26_2016.csv')
PDC_LOBREG_PATH = os.path.join(PDC_DATA_DIR, 'dbo_lobreg_4_26_2016.csv')
PDC_LOBFIRM_PATH = os.path.join(PDC_DATA_DIR, 'dbo_lobfirm_4_26_2016.csv')
PDC_CONTRIBUTIONS_PATH = os.path.join(PDC_DATA_DIR, 'take_two_dbo_rcpt.csv')
PDC_REPORTS_PATH = os.path.join(PDC_DATA_DIR, 'dbo_reports_4_26_2016.csv')
ST_BRIEF_CONTRACTS_PATH = os.path.join(PDC_DATA_DIR, 'sound_transit_purchase_orders.csv')
