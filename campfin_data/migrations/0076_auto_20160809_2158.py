# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-09 21:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0075_scrapedcontribution_filing_committee'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapedExpense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendor', models.CharField(db_index=True, max_length=500)),
                ('date', models.DateField(db_index=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('city', models.CharField(db_index=True, max_length=50)),
                ('state', models.CharField(db_index=True, max_length=50)),
                ('zipcode', models.CharField(db_index=True, max_length=11)),
                ('description', models.CharField(db_index=True, max_length=300)),
                ('filing_committee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.ScrapedCommittee')),
            ],
        ),
        migrations.CreateModel(
            name='ScrapedInkind',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donor', models.CharField(db_index=True, max_length=500)),
                ('date', models.DateField(db_index=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('primary_general', models.CharField(db_index=True, max_length=15)),
                ('city', models.CharField(db_index=True, max_length=50)),
                ('state', models.CharField(db_index=True, max_length=50)),
                ('zipcode', models.CharField(db_index=True, max_length=11)),
                ('employer', models.CharField(db_index=True, max_length=100)),
                ('occupation', models.CharField(db_index=True, max_length=100)),
                ('description', models.CharField(db_index=True, max_length=300)),
                ('filing_committee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.ScrapedCommittee')),
            ],
        ),
        migrations.RemoveField(
            model_name='scrapedcontribution',
            name='description',
        ),
    ]
