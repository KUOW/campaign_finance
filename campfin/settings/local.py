from campfin.settings.base import *

DEBUG = True

INSTALLED_APPS += [
	'debug_toolbar'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(process)d %(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/Users/abrahamepton/logs/worker.log',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

"""
DATABASES = {    
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'campfin_db',
        'USER' : 'campfin_admin',
    }
}
"""

DATA_DIR = os.path.join('/', 'home', 'aepton', 'code', 'campfin', 'data')
GEO_DATA_DIR = os.path.join(DATA_DIR, 'shapefiles')
SOS_BALLOTS_DIR = os.path.join(DATA_DIR, 'sos_ballots')
PDC_SCRAPED_DIR = os.path.join(DATA_DIR, 'pdc_scraped_data')

PDC_COMMITTEES_PATH = os.path.join(DATA_DIR, 'dbo_c1_4_26_2016.csv')
PDC_CONTRIBUTIONS_PATH = os.path.join(DATA_DIR, 'take_two_dbo_rcpt.csv')
PDC_LOBBIO_PATH = os.path.join(DATA_DIR, 'dbo_lobbio_4_26_2016.csv')
PDC_LOBEMP_PATH = os.path.join(DATA_DIR, 'dbo_lobemp_4_26_2016.csv')
PDC_LOBL2_PATH = os.path.join(DATA_DIR, 'dbo_lobl2_4_26_2016.csv')
PDC_LOBREG_PATH = os.path.join(DATA_DIR, 'dbo_lobreg_4_26_2016.csv')
PDC_LOBFIRM_PATH = os.path.join(DATA_DIR, 'dbo_lobfirm_4_26_2016.csv')
PDC_REPORTS_PATH = os.path.join(DATA_DIR, 'dbo_reports_4_26_2016.csv')
ST_BRIEF_CONTRACTS_PATH = os.path.join(DATA_DIR, 'sound_transit_purchase_orders.csv')