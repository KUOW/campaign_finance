# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-18 20:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0031_pdclobbyistemployer_pdclobbyistemployeryear'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pdclobbyistemployeryear',
            name='catnum',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='pdclobbyistemployeryear',
            name='letter',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='pdclobbyistemployeryear',
            name='pacs',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
