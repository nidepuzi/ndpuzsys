# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-20 12:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0020_auto_20161118_1048'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='skustock',
            managers=[
                ('_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='elite_score',
            field=models.IntegerField(default=0, verbose_name='\u7cbe\u54c1\u5546\u54c1\u79ef\u5206'),
        ),
    ]
