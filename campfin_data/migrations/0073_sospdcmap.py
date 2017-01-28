# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-03 21:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0072_auto_20160802_1820'),
    ]

    operations = [
        migrations.CreateModel(
            name='SOSPDCMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdc_filer_id', models.CharField(db_index=True, max_length=30)),
                ('pdc_name', models.CharField(db_index=True, max_length=500)),
                ('sos_ballot_name', models.CharField(db_index=True, max_length=500)),
                ('sos_ballot_id', models.IntegerField(db_index=True)),
            ],
        ),
    ]
