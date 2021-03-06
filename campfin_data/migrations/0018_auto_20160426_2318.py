# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-26 23:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campfin_data', '0017_auto_20160426_2105'),
    ]

    operations = [
        migrations.CreateModel(
            name='PDCCommittee',
            fields=[
                ('filer_id', models.CharField(db_index=True, max_length=25, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='PDCCommitteeYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(db_index=True)),
                ('c1_id', models.IntegerField(blank=True, null=True)),
                ('repno', models.IntegerField(blank=True, null=True)),
                ('filer_type', models.CharField(max_length=25)),
                ('affil', models.TextField(blank=True, null=True)),
                ('affil_info', models.TextField(blank=True, null=True)),
                ('mgr_info', models.TextField(blank=True, null=True)),
                ('memo', models.TextField(blank=True, null=True)),
                ('jurisdiction', models.TextField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('candidate_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.Address')),
                ('committee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campfin_data.PDCCommittee')),
            ],
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='code',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='contribution_type',
            field=models.CharField(blank=True, db_index=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='description',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='donor_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.Address'),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='donor_employer',
            field=models.CharField(blank=True, db_index=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='donor_employer_city',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='donor_employer_state',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='donor_occupation',
            field=models.CharField(blank=True, db_index=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='memo',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='rcpt_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='pdccontribution',
            name='rpt_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='pdccontribution',
            name='filer_committee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campfin_data.PDCCommittee'),
        ),
    ]
