# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-02-21 18:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0021_auto_20161120_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='ref_link',
            field=models.CharField(blank=True, max_length=1024, verbose_name='\u53c2\u8003\u94fe\u63a5'),
        ),
    ]
