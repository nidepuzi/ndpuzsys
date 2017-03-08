# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-08 13:56
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import outware.models.wareauth


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OutwareAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('nick', models.CharField(blank=True, max_length=16, verbose_name='APP\u6635\u79f0')),
                ('app_id', models.CharField(default=outware.models.wareauth.gen_default_appid, max_length=64, unique=True, verbose_name='APP ID')),
                ('app_secret', models.CharField(blank=True, max_length=64, verbose_name='APP SECRET')),
                ('sign_method', models.CharField(blank=True, default='md5', max_length=16, verbose_name='\u7b7e\u540d\u65b9\u6cd5')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=512, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_account',
                'verbose_name': '\u5916\u4ed3/\u5bf9\u63a5APP',
                'verbose_name_plural': '\u5916\u4ed3/\u5bf9\u63a5APP',
            },
        ),
    ]
