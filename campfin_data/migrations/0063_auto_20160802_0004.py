# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-02 00:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0062_auto_20160802_0003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ballotoffice',
            name='election_code',
            field=models.CharField(blank=True, db_index=True, max_length=25, null=True),
        ),
    ]
