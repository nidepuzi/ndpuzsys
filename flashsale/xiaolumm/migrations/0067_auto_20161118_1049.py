# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0066_add_memo_and_redirect_field_advertisement'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mamasalegrade',
            options={'verbose_name': 'V2/\u5988\u5988\u5468\u9500\u552e\u4e1a\u7ee9', 'verbose_name_plural': 'V2/\u5988\u5988\u5468\u9500\u552e\u4e1a\u7ee9\u5217\u8868'},
        ),
        migrations.AlterField(
            model_name='activitymamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='activitymamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='carrytotalrecord',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='cashout',
            name='cash_out_type',
            field=models.CharField(choices=[('renew', '\u5988\u5988\u7eed\u8d39'), ('budget', '\u63d0\u81f3\u96f6\u94b1\u5e10\u6237'), ('red', '\u5fae\u4fe1\u7ea2\u5305'), ('coupon', '\u5151\u6362\u4f18\u60e0\u5238')], default='red', max_length=8, verbose_name='\u63d0\u73b0\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='grouprelationship',
            name='referal_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='mamadailyappvisit',
            name='renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=0, verbose_name='\u5988\u5988\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='mamadailytabvisit',
            name='stats_tab',
            field=models.IntegerField(choices=[(0, 'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, 'WX/\u5e97\u94fa\u6fc0\u6d3b'), (15, 'WX/APP\u4e0b\u8f7d'), (16, 'WX/\u5f00\u5e97\u4e8c\u7ef4\u7801'), (17, 'WX/\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801'), (18, 'WX/\u5ba2\u670d\u83dc\u5355'), (19, 'WX/\u4e2a\u4eba\u5e10\u6237'), (20, 'WX/\u63d0\u73b0\u9875APP\u4e0b\u8f7d'), (21, 'WX/\u8df3\u8f6c\u4e13\u9898\u94fe\u63a5'), (22, 'WX/\u8df3\u8f6c\u5fae\u4fe1\u6587\u7ae0'), (23, 'WX/\u65b0\u624b\u6559\u7a0b'), (24, 'WX/\u7ed1\u5b9a\u624b\u673a'), (25, 'WX/\u70b9\u51fb\u6536\u76ca\u63a8\u9001'), (26, 'WX/\u70b9\u51fb\u8fd4\u73b0\u8bf4\u660e'), (27, 'APP/\u7cbe\u82f1\u5988\u5988'), (28, 'WX/\u65b0\u5988\u5988\u63a8\u9001'), (29, 'WX/\u5e7f\u544a')], db_index=True, default=0, verbose_name='\u529f\u80fdTAB'),
        ),
        migrations.AlterField(
            model_name='mamadevicestats',
            name='renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=0, verbose_name='\u5988\u5988\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='mamatabvisitstats',
            name='stats_tab',
            field=models.IntegerField(choices=[(0, 'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, 'WX/\u5e97\u94fa\u6fc0\u6d3b'), (15, 'WX/APP\u4e0b\u8f7d'), (16, 'WX/\u5f00\u5e97\u4e8c\u7ef4\u7801'), (17, 'WX/\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801'), (18, 'WX/\u5ba2\u670d\u83dc\u5355'), (19, 'WX/\u4e2a\u4eba\u5e10\u6237'), (20, 'WX/\u63d0\u73b0\u9875APP\u4e0b\u8f7d'), (21, 'WX/\u8df3\u8f6c\u4e13\u9898\u94fe\u63a5'), (22, 'WX/\u8df3\u8f6c\u5fae\u4fe1\u6587\u7ae0'), (23, 'WX/\u65b0\u624b\u6559\u7a0b'), (24, 'WX/\u7ed1\u5b9a\u624b\u673a'), (25, 'WX/\u70b9\u51fb\u6536\u76ca\u63a8\u9001'), (26, 'WX/\u70b9\u51fb\u8fd4\u73b0\u8bf4\u660e'), (27, 'APP/\u7cbe\u82f1\u5988\u5988'), (28, 'WX/\u65b0\u5988\u5988\u63a8\u9001'), (29, 'WX/\u5e7f\u544a')], db_index=True, default=0, verbose_name='\u529f\u80fdTAB'),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='potentialmama',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], default=15, verbose_name='\u6700\u540e\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='referalrelationship',
            name='referal_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='teamcarrytotalrecord',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='weekmamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='weekmamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='weixinpushevent',
            name='event_type',
            field=models.IntegerField(choices=[(1, '\u7c89\u4e1d\u589e\u52a0'), (2, '\u9080\u8bf7\u5956\u52b1\u751f\u6210'), (3, '\u9080\u8bf7\u5956\u52b1\u786e\u5b9a'), (5, '\u5173\u6ce8\u516c\u4f17\u53f7'), (4, '\u8ba2\u5355\u4f63\u91d1\u751f\u6210'), (6, '\u4e0b\u5c5e\u8ba2\u5355\u4f63\u91d1\u751f\u6210'), (7, '\u70b9\u51fb\u6536\u76ca'), (8, '\u62fc\u56e2\u6210\u529f'), (81, '\u62fc\u56e2\u5931\u8d25'), (82, '\u62fc\u56e2\u4eba\u6570\u4e0d\u8db3'), (9, '\u540c\u610f\u9000\u8d27'), (10, '\u7528\u6237\u9000\u8d27\u5230\u8fbe\u4ed3\u5e93'), (11, '\u7528\u6237\u9000\u8d27\u6210\u529f'), (101, '\u7cbe\u54c1\u5238\u6d41\u901a\u8bb0\u5f55')], db_index=True, default=0, verbose_name='\u4e8b\u4ef6\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='weixinpushevent',
            name='tid',
            field=models.IntegerField(choices=[(7, '\u6a21\u7248/\u7c89\u4e1d\u589e\u52a0'), (8, '\u6a21\u7248/\u5173\u6ce8\u516c\u4f17\u53f7'), (2, '\u6a21\u7248/\u8ba2\u5355\u4f63\u91d1'), (3, '\u6a21\u7248/\u9000\u6b3e\u6d88\u606f')], default=0, verbose_name='\u6d88\u606f\u6a21\u7248ID'),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='last_renew_type',
            field=models.IntegerField(choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (90, '\u7cbe\u82f1mama'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')], db_index=True, default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b'),
        ),
    ]
