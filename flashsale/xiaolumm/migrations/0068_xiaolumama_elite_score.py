# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-20 12:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0067_auto_20161118_1049'),
    ]

    operations = [
        migrations.AddField(
            model_name='xiaolumama',
            name='elite_score',
            field=models.IntegerField(default=0, verbose_name='\u7cbe\u82f1\u6c47\u79ef\u5206'),
        ),
    ]