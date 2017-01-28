# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-17 23:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0029_auto_20160506_1901'),
    ]

    operations = [
        migrations.CreateModel(
            name='PDCLobbyist',
            fields=[
                ('lobnum', models.CharField(db_index=True, max_length=20, primary_key=True, serialize=False)),
                ('person', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.Person')),
            ],
        ),
        migrations.CreateModel(
            name='PDCLobbyistRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(blank=True, db_index=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('cell_phone', models.CharField(blank=True, max_length=15, null=True)),
                ('temp_phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.CharField(blank=True, max_length=150, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('deceased', models.CharField(blank=True, max_length=50, null=True)),
                ('ltr', models.CharField(blank=True, max_length=50, null=True)),
                ('warn', models.CharField(blank=True, max_length=50, null=True)),
                ('company', models.CharField(blank=True, db_index=True, max_length=150, null=True)),
                ('warning_letter', models.DateField(blank=True, null=True)),
                ('stipulate_letter', models.DateField(blank=True, null=True)),
                ('brief_enforcement', models.DateField(blank=True, null=True)),
                ('full_enforcement', models.DateField(blank=True, null=True)),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.Address')),
                ('lobbyist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.PDCLobbyist')),
                ('other_lobbyists', models.ManyToManyField(blank=True, to='campfin_data.Person')),
            ],
        ),
    ]
