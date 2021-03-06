# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-18 19:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0030_pdclobbyist_pdclobbyistregistration'),
    ]

    operations = [
        migrations.CreateModel(
            name='PDCLobbyistEmployer',
            fields=[
                ('employer_id', models.CharField(db_index=True, max_length=15, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='PDCLobbyistEmployerYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(blank=True, db_index=True, null=True)),
                ('email', models.CharField(blank=True, max_length=50, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('pacs', models.CharField(blank=True, max_length=10, null=True)),
                ('letter', models.CharField(blank=True, max_length=10, null=True)),
                ('catnum', models.CharField(blank=True, max_length=10, null=True)),
                ('memo', models.TextField(blank=True, null=True)),
                ('govtagency', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.Address')),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.Person')),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.PDCLobbyistEmployer')),
            ],
        ),
    ]
