# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-24 20:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0050_auto_20161118_1049'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraddress',
            name='identification_no',
            field=models.CharField(blank=True, max_length=32, verbose_name='\u8eab\u4efd\u8bc1\u53f7\u7801'),
        ),
    ]
