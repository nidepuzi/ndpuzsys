# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-24 19:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0009_stockadjust_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehouse',
            name='ware_source',
            field=models.CharField(choices=[('jimei', '\u5df1\u7f8e'), ('fengchao', '\u8702\u5de2'), ('youhe', '\u4f18\u79be')], default='', max_length=16, verbose_name='\u4ed3\u5e93\u6240\u5c5e'),
        ),
    ]
