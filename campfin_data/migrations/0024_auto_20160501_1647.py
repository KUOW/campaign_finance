# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-01 16:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0023_auto_20160429_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='street_1',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='full_name',
            field=models.CharField(blank=True, db_index=True, max_length=300, null=True),
        ),
    ]
