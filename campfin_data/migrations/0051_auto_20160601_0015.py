# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-01 00:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0050_auto_20160531_2319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pdccommitteeyear',
            name='for_against',
            field=models.CharField(blank=True, choices=[('F', 'For'), ('A', 'Against'), ('U', 'Unknown')], db_index=True, default='U', max_length=1, null=True),
        ),
    ]
