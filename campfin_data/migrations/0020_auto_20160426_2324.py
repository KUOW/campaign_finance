# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-26 23:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0019_auto_20160426_2323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pdccommitteeyear',
            name='year',
            field=models.IntegerField(db_index=True, default=0),
            preserve_default=False,
        ),
    ]
