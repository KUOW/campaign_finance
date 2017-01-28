# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-14 02:55
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0054_geography_shapefile'),
    ]

    operations = [
        migrations.AddField(
            model_name='geography',
            name='multipoly',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='geography',
            name='poly',
            field=django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326),
        ),
    ]
