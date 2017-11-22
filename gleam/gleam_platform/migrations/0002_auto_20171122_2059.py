# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-22 12:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gleam_platform', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='contests',
            field=models.ManyToManyField(to='gleam_platform.Contest'),
        ),
        migrations.AlterField(
            model_name='team',
            name='members',
            field=models.ManyToManyField(to='gleam_platform.Contestant'),
        ),
    ]
