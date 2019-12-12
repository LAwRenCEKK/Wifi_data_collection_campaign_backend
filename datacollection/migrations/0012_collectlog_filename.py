# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2019-01-21 02:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacollection', '0011_remove_collectlog_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectlog',
            name='Filename',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='datacollection.file_score'),
            preserve_default=False,
        ),
    ]
