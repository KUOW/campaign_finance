# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-31 22:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0046_auto_20160531_1653'),
    ]

    operations = [
        migrations.CreateModel(
            name='SOSElectionCandidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('votes', models.IntegerField(blank=True, null=True)),
                ('vote_percent', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SOSElectionRace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(db_index=True)),
                ('level', models.CharField(db_index=True, max_length=15)),
                ('name', models.TextField()),
                ('jurisdiction', models.CharField(blank=True, db_index=True, max_length=30, null=True)),
                ('ballot_number', models.CharField(blank=True, db_index=True, max_length=10, null=True)),
                ('candidates', models.ManyToManyField(related_name='candidate', to='campfin_data.SOSElectionCandidate')),
                ('winner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='winner', to='campfin_data.SOSElectionCandidate')),
            ],
        ),
    ]
