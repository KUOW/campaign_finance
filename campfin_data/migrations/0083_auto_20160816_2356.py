# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-16 23:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0082_auto_20160816_2354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapedcontribution',
            name='date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]
