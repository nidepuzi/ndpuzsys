# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-15 21:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0025_update_table_shop_trades_erp_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='sys_note',
            field=models.CharField(blank=True, max_length=32, verbose_name='\u7cfb\u7edf\u5907\u6ce8'),
        ),
    ]
