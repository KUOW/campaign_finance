# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-21 18:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0005_address_zipcode_plus'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='original_address',
            field=models.TextField(blank=True),
        ),
    ]
