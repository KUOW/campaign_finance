import locale
import logging
import os
import requests
import time

from campfin_data.models import *
from campfin_data.utils import *
from csv import DictReader, DictWriter
from datetime import datetime
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand, CommandError

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except:
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Loads a geography (shapefile) into db'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            'shapefile',
            type=str,
            help="""
            Name of shapefile - not including extension. Assumes folder of same name in data
            directory.
            """)

        parser.add_argument(
            '--shapetype',
            type=str,
            help='Type of geometry objects to create. Default is polygon.')

        parser.add_argument(
            '--flush',
            action='store_true',
            dest='flush',
            help='Flush existing geographies matching this shapefile name')

    def handle(self, *args, **options):
        if options['flush']:
            logging.info('Deleting geographies matching shapefile %s' % options['shapefile'])
            deleted = Geography.objects.filter(shapefile=options['shapefile'])
            logging.info('Deleted geographies: %s' % deleted)

        if not options['shapetype'] or options['shapetype'].upper() not in [
            'POLYGON', 'MULTIPOLYGON']:
            options['shapetype'] = 'POLYGON'

        path = os.path.join(
            settings.GEO_DATA_DIR, options['shapefile'], '%s.shp' % options['shapefile'])
        data = DataSource(path)
        test = data[0]
        print 'Metadata:'
        print 'Geometry type: %s' % test.geom_type
        print 'SRS: %s' % test.srs
        print 'Layers: %d' % len(data)
        print 'Features: %d' % len(test.get_fields(test.fields[0]))
        print '-------\n'
        print 'Previewing features in this file'
        for field in test.fields:
            print '%s: %s' % (
                field, '; '.join([str(f) for f in test.get_fields(field)[:3]]))
        
        field_name = ''
        while not field_name:
            print 'Pick field from the following to use for names of features in this file:'
            print ', '.join(test.fields)
            entered = raw_input('Field: ')
            if entered in test.fields:
                field_name = entered
            else:
                print "Sorry, %s isn't a valid field name; please try again" % entered

        field_identifier = ''
        while not field_identifier:
            print 'Identifiers are usually district numbers (machine-readable)'
            print 'Pick field from the following to use to identify features in this file:'
            print ', '.join(test.fields)
            entered = raw_input('Field: ')
            if entered in test.fields:
                field_identifier = entered
            else:
                print "Sorry, %s isn't a valid field name; please try again" % entered

        geo_type = None
        print 'Enter a geography type to associate with this...geography.'
        print 'Leave blank if this is a one-off geography.'
        geo_type = raw_input('Type: ')

        mapping = {
            'name': field_name,
            'identifier': field_identifier,
            options['shapetype'].lower()[:-3]: options['shapetype'].upper()
            #options['shapetype'].lower(): options['shapetype'].upper()
        }
        layer = LayerMapping(Geography, path, mapping)
        layer.save(verbose=True)

        # No easy way to inject anything into layermapping, so this is a hack
        geographies = Geography.objects.filter(shapefile__exact='')
        for geo in geographies:
            geo.shapefile = options['shapefile']
            geo.geo_type = geo_type
            try:
                geo.save()
            except Exception, e:
                logging.info('Error saving geo, aborting: %s' % e)
                break

