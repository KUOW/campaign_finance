# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-28 16:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0021_auto_20160426_2341'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='geocode_confidence',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]
