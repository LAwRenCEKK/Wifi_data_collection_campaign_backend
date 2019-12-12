# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2019-04-03 11:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('datacollection', '0014_auto_20190312_1440'),
    ]

    operations = [
        migrations.CreateModel(
            name='feedback_question',
            fields=[
                ('ID', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Contents', models.TextField(blank=True, max_length=300, null=True, verbose_name='Question')),
            ],
        ),
        migrations.CreateModel(
            name='user_feedback',
            fields=[
                ('ID', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MacID', models.CharField(max_length=30, null=True, verbose_name='MacID')),
                ('Items', models.CharField(blank=True, max_length=125, null=True, verbose_name='Clicked_item')),
                ('Additional', models.TextField(blank=True, max_length=300, null=True, verbose_name='Comments')),
                ('Time', models.DateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='Time')),
            ],
        ),
    ]