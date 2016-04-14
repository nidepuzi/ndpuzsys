# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('oid', models.AutoField(serialize=False, primary_key=True)),
                ('cid', models.BigIntegerField(null=True)),
                ('num_iid', models.CharField(max_length=64, blank=True)),
                ('title', models.CharField(max_length=128)),
                ('price', models.FloatField(default=0.0)),
                ('item_meal_id', models.IntegerField(null=True)),
                ('sku_id', models.CharField(max_length=20, blank=True)),
                ('num', models.IntegerField(default=0, null=True)),
                ('outer_sku_id', models.CharField(max_length=20, blank=True)),
                ('total_fee', models.FloatField(default=0.0)),
                ('payment', models.FloatField(default=0.0)),
                ('discount_fee', models.FloatField(default=0.0)),
                ('adjust_fee', models.FloatField(default=0.0)),
                ('sku_properties_name', models.TextField(max_length=256, blank=True)),
                ('refund_id', models.BigIntegerField(null=True)),
                ('is_oversold', models.BooleanField(default=False)),
                ('is_service_order', models.BooleanField(default=False)),
                ('item_meal_name', models.CharField(max_length=88, blank=True)),
                ('pic_path', models.CharField(max_length=128, blank=True)),
                ('seller_nick', models.CharField(max_length=32, blank=True)),
                ('buyer_nick', models.CharField(max_length=32, blank=True)),
                ('refund_status', models.CharField(blank=True, max_length=40, choices=[(b'NO_REFUND', b'\xe6\xb2\xa1\xe6\x9c\x89\xe9\x80\x80\xe6\xac\xbe'), (b'WAIT_SELLER_AGREE', b'\xe7\xad\x89\xe5\xbe\x85\xe5\x8d\x96\xe5\xae\xb6\xe5\x90\x8c\xe6\x84\x8f'), (b'WAIT_BUYER_RETURN_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe9\x80\x80\xe8\xb4\xa7'), (b'WAIT_SELLER_CONFIRM_GOODS', b'\xe5\x8d\x96\xe5\xae\xb6\xe7\xa1\xae\xe8\xae\xa4\xe6\x94\xb6\xe8\xb4\xa7'), (b'SELLER_REFUSE_BUYER', b'\xe4\xb9\xb0\xe5\xae\xb6\xe6\x8b\x92\xe7\xbb\x9d\xe9\x80\x80\xe6\xac\xbe'), (b'CLOSED', b'\xe9\x80\x80\xe6\xac\xbe\xe5\xb7\xb2\xe5\x85\xb3\xe9\x97\xad'), (b'SUCCESS', b'\xe9\x80\x80\xe6\xac\xbe\xe5\xb7\xb2\xe6\x88\x90\xe5\x8a\x9f')])),
                ('outer_id', models.CharField(max_length=64, blank=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('pay_time', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('consign_time', models.DateTimeField(null=True, blank=True)),
                ('status', models.CharField(blank=True, max_length=32, choices=[(b'TRADE_NO_CREATE_PAY', b'\xe6\xb2\xa1\xe6\x9c\x89\xe5\x88\x9b\xe5\xbb\xba\xe6\x94\xaf\xe4\xbb\x98\xe5\xae\x9d\xe4\xba\xa4\xe6\x98\x93'), (b'WAIT_BUYER_PAY', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe4\xbb\x98\xe6\xac\xbe'), (b'WAIT_SELLER_SEND_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe5\x8d\x96\xe5\xae\xb6\xe5\x8f\x91\xe8\xb4\xa7'), (b'WAIT_BUYER_CONFIRM_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe7\xa1\xae\xe8\xae\xa4\xe6\x94\xb6\xe8\xb4\xa7'), (b'TRADE_BUYER_SIGNED', b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe7\xad\xbe\xe6\x94\xb6,\xe8\xb4\xa7\xe5\x88\xb0\xe4\xbb\x98\xe6\xac\xbe\xe4\xb8\x93\xe7\x94\xa8'), (b'TRADE_FINISHED', b'\xe4\xba\xa4\xe6\x98\x93\xe6\x88\x90\xe5\x8a\x9f'), (b'TRADE_CLOSED', b'\xe4\xbb\x98\xe6\xac\xbe\xe4\xbb\xa5\xe5\x90\x8e\xe7\x94\xa8\xe6\x88\xb7\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f\xef\xbc\x8c\xe4\xba\xa4\xe6\x98\x93\xe8\x87\xaa\xe5\x8a\xa8\xe5\x85\xb3\xe9\x97\xad'), (b'TRADE_CLOSED_BY_TAOBAO', b'\xe4\xbb\x98\xe6\xac\xbe\xe4\xbb\xa5\xe5\x89\x8d\xef\xbc\x8c\xe5\x8d\x96\xe5\xae\xb6\xe6\x88\x96\xe4\xb9\xb0\xe5\xae\xb6\xe4\xb8\xbb\xe5\x8a\xa8\xe5\x85\xb3\xe9\x97\xad\xe4\xba\xa4\xe6\x98\x93')])),
            ],
            options={
                'db_table': 'shop_orders_order',
                'verbose_name': '\u6dd8\u5b9d\u8ba2\u5355\u5546\u54c1',
                'verbose_name_plural': '\u6dd8\u5b9d\u8ba2\u5355\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PinPaiTuan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outer_id', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe5\xa4\x96\xe9\x83\xa8\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('outer_sku_id', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe5\xa4\x96\xe9\x83\xa8\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('prod_sku_name', models.CharField(db_index=True, max_length=128, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe8\xa7\x84\xe6\xa0\xbc\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
            ],
            options={
                'db_table': 'shop_juhuasuan_pinpaituan',
                'verbose_name': '\u54c1\u724c\u56e2\u5165\u4ed3\u5546\u54c1',
            },
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('seller_id', models.CharField(max_length=64, blank=True)),
                ('seller_nick', models.CharField(max_length=64, blank=True)),
                ('buyer_nick', models.CharField(max_length=64, blank=True)),
                ('type', models.CharField(max_length=32, blank=True)),
                ('payment', models.FloatField(default=0.0)),
                ('discount_fee', models.FloatField(default=0.0)),
                ('adjust_fee', models.FloatField(default=0.0)),
                ('post_fee', models.FloatField(default=0.0)),
                ('total_fee', models.FloatField(default=0.0)),
                ('buyer_obtain_point_fee', models.FloatField(default=0.0)),
                ('point_fee', models.FloatField(default=0.0)),
                ('real_point_fee', models.FloatField(default=0.0)),
                ('commission_fee', models.FloatField(default=0.0)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('pay_time', models.DateTimeField(null=True, blank=True)),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('modified', models.DateTimeField(null=True, blank=True)),
                ('consign_time', models.DateTimeField(null=True, blank=True)),
                ('send_time', models.DateTimeField(null=True, blank=True)),
                ('buyer_message', models.TextField(max_length=1000, blank=True)),
                ('buyer_memo', models.TextField(max_length=1000, blank=True)),
                ('seller_memo', models.TextField(max_length=1000, blank=True)),
                ('seller_flag', models.IntegerField(null=True)),
                ('is_brand_sale', models.BooleanField(default=False)),
                ('is_force_wlb', models.BooleanField(default=False)),
                ('trade_from', models.CharField(max_length=32, blank=True)),
                ('is_lgtype', models.BooleanField(default=False)),
                ('lg_aging', models.DateTimeField(null=True, blank=True)),
                ('lg_aging_type', models.CharField(max_length=20, blank=True)),
                ('buyer_rate', models.BooleanField(default=False)),
                ('seller_rate', models.BooleanField(default=False)),
                ('seller_can_rate', models.BooleanField(default=False)),
                ('is_part_consign', models.BooleanField(default=False)),
                ('seller_cod_fee', models.FloatField(default=0.0)),
                ('buyer_cod_fee', models.FloatField(default=0.0)),
                ('cod_fee', models.FloatField(default=0.0)),
                ('cod_status', models.CharField(max_length=32, blank=True)),
                ('shipping_type', models.CharField(max_length=12, blank=True)),
                ('buyer_alipay_no', models.CharField(max_length=128, blank=True)),
                ('receiver_name', models.CharField(max_length=64, blank=True)),
                ('receiver_state', models.CharField(max_length=16, blank=True)),
                ('receiver_city', models.CharField(max_length=16, blank=True)),
                ('receiver_district', models.CharField(max_length=16, blank=True)),
                ('receiver_address', models.CharField(max_length=128, blank=True)),
                ('receiver_zip', models.CharField(max_length=10, blank=True)),
                ('receiver_mobile', models.CharField(max_length=24, blank=True)),
                ('receiver_phone', models.CharField(max_length=20, blank=True)),
                ('step_paid_fee', models.FloatField(default=0.0)),
                ('step_trade_status', models.CharField(blank=True, max_length=32, choices=[(b'FRONT_NOPAID_FINAL_NOPAID', b'\xe5\xae\x9a\xe9\x87\x91\xe6\x9c\xaa\xe4\xbb\x98\xe5\xb0\xbe\xe6\xac\xbe\xe6\x9c\xaa\xe4\xbb\x98'), (b'FRONT_PAID_FINAL_NOPAID', b'\xe5\xae\x9a\xe9\x87\x91\xe5\xb7\xb2\xe4\xbb\x98\xe5\xb0\xbe\xe6\xac\xbe\xe6\x9c\xaa\xe4\xbb\x98'), (b'FRONT_PAID_FINAL_PAID', b'\xe5\xae\x9a\xe9\x87\x91\xe5\x92\x8c\xe5\xb0\xbe\xe6\xac\xbe\xe9\x83\xbd\xe4\xbb\x98')])),
                ('status', models.CharField(blank=True, max_length=32, choices=[(b'TRADE_NO_CREATE_PAY', b'\xe6\xb2\xa1\xe6\x9c\x89\xe5\x88\x9b\xe5\xbb\xba\xe6\x94\xaf\xe4\xbb\x98\xe5\xae\x9d\xe4\xba\xa4\xe6\x98\x93'), (b'WAIT_BUYER_PAY', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe4\xbb\x98\xe6\xac\xbe'), (b'WAIT_SELLER_SEND_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe5\x8d\x96\xe5\xae\xb6\xe5\x8f\x91\xe8\xb4\xa7'), (b'WAIT_BUYER_CONFIRM_GOODS', b'\xe7\xad\x89\xe5\xbe\x85\xe4\xb9\xb0\xe5\xae\xb6\xe7\xa1\xae\xe8\xae\xa4\xe6\x94\xb6\xe8\xb4\xa7'), (b'TRADE_BUYER_SIGNED', b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe7\xad\xbe\xe6\x94\xb6,\xe8\xb4\xa7\xe5\x88\xb0\xe4\xbb\x98\xe6\xac\xbe\xe4\xb8\x93\xe7\x94\xa8'), (b'TRADE_FINISHED', b'\xe4\xba\xa4\xe6\x98\x93\xe6\x88\x90\xe5\x8a\x9f'), (b'TRADE_CLOSED', b'\xe4\xbb\x98\xe6\xac\xbe\xe4\xbb\xa5\xe5\x90\x8e\xe7\x94\xa8\xe6\x88\xb7\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f\xef\xbc\x8c\xe4\xba\xa4\xe6\x98\x93\xe8\x87\xaa\xe5\x8a\xa8\xe5\x85\xb3\xe9\x97\xad'), (b'TRADE_CLOSED_BY_TAOBAO', b'\xe4\xbb\x98\xe6\xac\xbe\xe4\xbb\xa5\xe5\x89\x8d\xef\xbc\x8c\xe5\x8d\x96\xe5\xae\xb6\xe6\x88\x96\xe4\xb9\xb0\xe5\xae\xb6\xe4\xb8\xbb\xe5\x8a\xa8\xe5\x85\xb3\xe9\x97\xad\xe4\xba\xa4\xe6\x98\x93')])),
                ('user', models.ForeignKey(related_name='trades', to='users.User', null=True)),
            ],
            options={
                'db_table': 'shop_orders_trade',
                'verbose_name': '\u6dd8\u5b9d\u8ba2\u5355',
                'verbose_name_plural': '\u6dd8\u5b9d\u8ba2\u5355\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='order',
            name='trade',
            field=models.ForeignKey(related_name='trade_orders', to='orders.Trade', null=True),
        ),
    ]
