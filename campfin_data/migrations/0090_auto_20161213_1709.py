# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-12-14 01:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0089_scrapedcommittee_committee_year'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scrapedcommittee',
            old_name='committee_year',
            new_name='filing_year',
        ),
    ]
