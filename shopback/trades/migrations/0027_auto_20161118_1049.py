# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0026_psi_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='packageorder',
            name='merged',
        ),
        migrations.RemoveField(
            model_name='packageorder',
            name='type',
        ),
        migrations.AddField(
            model_name='packageorder',
            name='can_send_time',
            field=models.DateTimeField(blank=True, db_column=b'merged', null=True, verbose_name='\u53ef\u53d1\u8d27\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='dirtymergetrade',
            name='trade_from',
            field=models.IntegerField(default=0, verbose_name='\u4ea4\u6613\u6765\u6e90'),
        ),
        migrations.AlterField(
            model_name='dirtymergetrade',
            name='ware_by',
            field=models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
        migrations.AlterField(
            model_name='mergetrade',
            name='trade_from',
            field=models.IntegerField(default=0, verbose_name='\u4ea4\u6613\u6765\u6e90'),
        ),
        migrations.AlterField(
            model_name='mergetrade',
            name='ware_by',
            field=models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='priority',
            field=models.IntegerField(default=0, verbose_name='\u4f5c\u5e9f\u5b57\u6bb5'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='ware_by',
            field=models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='assign_status',
            field=models.IntegerField(choices=[(0, '\u672a\u5907\u8d27'), (1, '\u5df2\u5907\u8d27'), (2, '\u5df2\u51fa\u8d27'), (4, '\u5382\u5bb6\u5907\u8d27\u4e2d'), (3, '\u5df2\u53d6\u6d88')], db_index=True, default=0, verbose_name='\u72b6\u6001'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='book_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u51c6\u5907\u8ba2\u8d27\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='status',
            field=models.CharField(blank=True, choices=[(b'paid', '\u521a\u4ed8\u5f85\u5904\u7406'), (b'prepare_book', '\u5f85\u8ba2\u8d27'), (b'booked', '\u5f85\u5907\u8d27'), (b'ready', '\u5f85\u5206\u914d'), (b'third_send', '\u5f85\u7b2c\u4e09\u65b9\u53d1\u8d27'), (b'assigned', '\u5f85\u5408\u5355'), (b'merged', '\u5f85\u6253\u5355'), (b'waitscan', '\u5f85\u626b\u63cf'), (b'waitpost', '\u5f85\u79f0\u91cd'), (b'sent', '\u5f85\u6536\u8d27'), (b'finish', '\u5b8c\u6210'), (b'cancel', '\u53d6\u6d88'), (b'holding', '\u6302\u8d77')], db_index=True, default=b'paid', max_length=32, verbose_name='\u8ba2\u5355\u72b6\u6001'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='ware_by',
            field=models.IntegerField(choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')], db_index=True, default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93'),
        ),
    ]