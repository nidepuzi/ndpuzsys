# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apprelease', '0004_apprelease_device_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apprelease',
            name='auto_update',
            field=models.BooleanField(default=False, verbose_name='\u81ea\u52a8\u66f4\u65b0'),
        ),
    ]