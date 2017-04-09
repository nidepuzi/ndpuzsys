# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-30 22:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolupay', '0003_refundorder'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='refundorder',
            options={'verbose_name': '\u5c0f\u9e7f\u652f\u4ed8/\u9000\u6b3e', 'verbose_name_plural': '\u5c0f\u9e7f\u652f\u4ed8/\u9000\u6b3e\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='refundorder',
            name='funding_source',
            field=models.CharField(blank=True, choices=[('unsettled_funds', '\u4f7f\u7528\u672a\u7ed3\u7b97\u8d44\u91d1\u9000\u6b3e'), ('recharge_funds', '\u4f7f\u7528\u53ef\u7528\u4f59\u989d\u9000\u6b3e')], default='unsettled_funds', max_length=16, verbose_name='\u6e20\u9053\u6d41\u6c34\u53f7'),
        ),
        migrations.AlterField(
            model_name='chargeorder',
            name='transaction_no',
            field=models.CharField(blank=True, max_length=64, verbose_name='\u652f\u4ed8\u6e20\u9053\u6d41\u6c34\u5355\u53f7'),
        ),
        migrations.AlterField(
            model_name='refundorder',
            name='transaction_no',
            field=models.CharField(blank=True, max_length=64, verbose_name='\u6e20\u9053\u6d41\u6c34\u53f7'),
        ),
    ]