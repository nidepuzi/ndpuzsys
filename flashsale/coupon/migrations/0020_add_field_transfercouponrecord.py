# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-12 11:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0019_add_field_is_chained'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupontransferrecord',
            name='from_mama_elite_level',
            field=models.CharField(blank=True, choices=[('SP', 'SP'), ('Partner', 'Partner'), ('VP', 'VP'), ('Director', 'Director'), ('Associate', 'Associate')], max_length=16, null=True, verbose_name='From\u7b49\u7ea7'),
        ),
        migrations.AddField(
            model_name='coupontransferrecord',
            name='from_mama_price',
            field=models.FloatField(default=0.0, verbose_name='From\u5988\u5988\u4ef7\u683c'),
        ),
        migrations.AddField(
            model_name='coupontransferrecord',
            name='to_mama_price',
            field=models.FloatField(default=0.0, verbose_name='To\u5988\u5988\u4ef7\u683c'),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='coupon_value',
            field=models.FloatField(default=0.0, verbose_name='\u9762\u989d'),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='elite_level',
            field=models.CharField(blank=True, choices=[('SP', 'SP'), ('Partner', 'Partner'), ('VP', 'VP'), ('Director', 'Director'), ('Associate', 'Associate')], max_length=16, null=True, verbose_name='\u7b49\u7ea7'),
        )
    ]
