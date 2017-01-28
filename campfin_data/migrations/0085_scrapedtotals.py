# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-22 18:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0084_auto_20160817_2323'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapedTotals',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raised', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('spent', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('inkinds', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('loans', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('ie_for', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('ie_against', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('filing_committee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.ScrapedCommittee')),
            ],
        ),
    ]
