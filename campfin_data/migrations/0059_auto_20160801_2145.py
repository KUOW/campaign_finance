# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-01 21:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0058_auto_20160801_1933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ballotelection',
            name='general_election_id',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]
