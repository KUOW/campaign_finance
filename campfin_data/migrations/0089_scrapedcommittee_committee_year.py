# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-12-14 01:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0088_auto_20160920_1109'),
    ]

    operations = [
        migrations.AddField(
            model_name='scrapedcommittee',
            name='committee_year',
            field=models.IntegerField(default=2016),
            preserve_default=False,
        ),
    ]
