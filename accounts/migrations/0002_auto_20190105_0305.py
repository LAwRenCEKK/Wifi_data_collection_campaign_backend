# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2019-01-05 03:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='myuser',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='myuser',
            name='last_name',
        ),
        migrations.AddField(
            model_name='myuser',
            name='username',
            field=models.CharField(default='user', max_length=30, verbose_name='user name'),
        ),
    ]