# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-18 23:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0036_auto_20160518_2237'),
    ]

    operations = [
        migrations.CreateModel(
            name='PDCLobbyistMonthlyExpenseReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amended', models.BooleanField(db_index=True, default=False)),
                ('amended_report_id', models.CharField(blank=True, max_length=25, null=True)),
                ('report_period_month_begin', models.DateField(db_index=True)),
                ('amended_date', models.DateField(blank=True, db_index=True, null=True)),
                ('postmark', models.DateField(blank=True, null=True)),
                ('compensation', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('personal_expenses', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('entertainment_expenses', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('contributions', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('advertising_expenses', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('political_ads', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('other_expenses', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('unre_expenses', models.DecimalField(blank=True, decimal_places=3, max_digits=15, null=True)),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.PDCLobbyistEmployer')),
                ('lobbyist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.PDCLobbyist')),
            ],
        ),
    ]
