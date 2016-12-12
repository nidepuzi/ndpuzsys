# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-12 11:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daystats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailystat',
            name='total_boutique',
            field=models.IntegerField(default=0, verbose_name='\u8d2d\u7cbe\u54c1\u5238'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_budget',
            field=models.IntegerField(default=0, verbose_name='\u94b1\u5305\u4f59\u989d'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_coupon',
            field=models.IntegerField(default=0, verbose_name='\u4f18\u60e0\u5238'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_deposite',
            field=models.IntegerField(default=0, verbose_name='\u652f\u4ed8\u62bc\u91d1'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_paycash',
            field=models.IntegerField(default=0, verbose_name='\u5b9e\u4ed8\u73b0\u91d1'),
        ),
    ]