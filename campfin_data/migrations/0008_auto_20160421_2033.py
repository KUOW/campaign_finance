# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-21 20:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0007_auto_20160421_2032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stvendor',
            name='addresses',
            field=models.ManyToManyField(null=True, to='campfin_data.Address'),
        ),
    ]
