# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-21 20:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0006_address_original_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stvendor',
            name='addresses',
            field=models.ManyToManyField(blank=True, to='campfin_data.Address'),
        ),
    ]
