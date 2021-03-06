# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origin_no', models.CharField(unique=True, max_length=32, verbose_name=b'\xe5\x8e\x9f\xe5\x90\x88\xe5\x90\x8c\xe5\x8f\xb7')),
                ('forecast_date', models.DateField(null=True, verbose_name=b'\xe9\xa2\x84\xe6\xb5\x8b\xe5\x88\xb0\xe8\xb4\xa7\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('post_date', models.DateField(null=True, verbose_name=b'\xe5\x8f\x91\xe8\xb4\xa7\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('service_date', models.DateField(null=True, verbose_name=b'\xe4\xb8\x9a\xe5\x8a\xa1\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('creator', models.CharField(max_length=64, null=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe4\xba\xba', blank=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('purchase_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe6\x95\xb0\xe9\x87\x8f')),
                ('storage_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe5\xb7\xb2\xe5\x85\xa5\xe5\xba\x93\xe6\x95\xb0')),
                ('total_fee', models.FloatField(default=0.0, verbose_name=b'\xe6\x80\xbb\xe8\xb4\xb9\xe7\x94\xa8')),
                ('prepay', models.FloatField(default=0.0, verbose_name=b'\xe9\xa2\x84\xe4\xbb\x98\xe6\xac\xbe')),
                ('payment', models.FloatField(default=0.0, verbose_name=b'\xe5\xb7\xb2\xe4\xbb\x98\xe6\xac\xbe')),
                ('receiver_name', models.CharField(max_length=32, verbose_name=b'\xe6\x94\xb6\xe8\xb4\xa7\xe4\xba\xba', blank=True)),
                ('status', models.CharField(default=b'DRAFT', max_length=32, verbose_name=b'\xe8\xae\xa2\xe5\x8d\x95\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'DRAFT', b'\xe8\x8d\x89\xe7\xa8\xbf'), (b'APPROVAL', b'\xe5\xae\xa1\xe6\xa0\xb8'), (b'FINISH', b'\xe5\xae\x8c\xe6\x88\x90'), (b'INVALID', b'\xe4\xbd\x9c\xe5\xba\x9f')])),
                ('arrival_status', models.CharField(default=b'NO_ARRIVAL', max_length=20, verbose_name=b'\xe5\x88\xb0\xe8\xb4\xa7\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'NO_ARRIVAL', b'\xe6\x9c\xaa\xe5\x88\xb0\xe8\xb4\xa7'), (b'PART_ARRIVAL', b'\xe9\x83\xa8\xe5\x88\x86\xe5\x88\xb0\xe8\xb4\xa7'), (b'FULL_ARRIVAL', b'\xe5\x85\xa8\xe9\x83\xa8\xe5\x88\xb0\xe8\xb4\xa7')])),
                ('extra_name', models.CharField(max_length=256, verbose_name=b'\xe6\xa0\x87\xe9\xa2\x98', blank=True)),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
                ('prepay_cent', models.FloatField(default=0.0, verbose_name=b'\xe9\xa2\x84\xe4\xbb\x98\xe6\xaf\x94\xe4\xbe\x8b')),
                ('attach_files', models.FileField(upload_to=b'site_media/download/purchase', blank=True)),
                ('deposite', models.ForeignKey(related_name='purchases', verbose_name=b'\xe4\xbb\x93\xe5\xba\x93', blank=True, to='archives.Deposite', null=True)),
                ('purchase_type', models.ForeignKey(related_name='purchases', verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe7\xb1\xbb\xe5\x9e\x8b', blank=True, to='archives.PurchaseType', null=True)),
                ('supplier', models.ForeignKey(related_name='purchases', verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86', blank=True, to='archives.Supplier', null=True)),
            ],
            options={
                'db_table': 'shop_purchases_purchase',
                'verbose_name': '\u91c7\u8d2d\u5355',
                'verbose_name_plural': '\u91c7\u8d2d\u5355\u5217\u8868',
                'permissions': [('can_purchase_check', '\u5ba1\u6279\u91c7\u8d2d\u5408\u540c'), ('can_purchase_confirm', '\u786e\u8ba4\u91c7\u8d2d\u5b8c\u6210')],
            },
        ),
        migrations.CreateModel(
            name='PurchaseItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('supplier_item_id', models.CharField(max_length=64, verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86\xe8\xb4\xa7\xe5\x8f\xb7', blank=True)),
                ('product_id', models.IntegerField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81ID')),
                ('sku_id', models.IntegerField(null=True, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbcID')),
                ('outer_id', models.CharField(max_length=32, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('properties_name', models.CharField(max_length=64, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe5\xb1\x9e\xe6\x80\xa7', blank=True)),
                ('purchase_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe6\x95\xb0\xe9\x87\x8f')),
                ('storage_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe5\xb7\xb2\xe5\x85\xa5\xe5\xba\x93\xe6\x95\xb0')),
                ('discount', models.FloatField(default=0, null=True, verbose_name=b'\xe6\x8a\x98\xe6\x89\xa3')),
                ('std_price', models.FloatField(default=0.0, verbose_name=b'\xe5\xae\x9e\xe9\x99\x85\xe8\xbf\x9b\xe4\xbb\xb7')),
                ('price', models.FloatField(default=0.0, verbose_name=b'\xe6\xa0\x87\xe5\x87\x86\xe8\xbf\x9b\xe4\xbb\xb7')),
                ('total_fee', models.FloatField(default=0.0, verbose_name=b'\xe6\x80\xbb\xe8\xb4\xb9\xe7\x94\xa8')),
                ('prepay', models.FloatField(default=0.0, verbose_name=b'\xe9\xa2\x84\xe4\xbb\x98\xe6\xac\xbe')),
                ('payment', models.FloatField(default=0.0, verbose_name=b'\xe5\xb7\xb2\xe4\xbb\x98\xe6\xac\xbe')),
                ('created', models.DateTimeField(auto_now=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('status', models.CharField(default=b'normal', max_length=12, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'normal', b'\xe6\x9c\x89\xe6\x95\x88'), (b'delete', b'\xe4\xbd\x9c\xe5\xba\x9f')])),
                ('arrival_status', models.CharField(default=b'NO_ARRIVAL', max_length=12, verbose_name=b'\xe5\x88\xb0\xe8\xb4\xa7\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'NO_ARRIVAL', b'\xe6\x9c\xaa\xe5\x88\xb0\xe8\xb4\xa7'), (b'PART_ARRIVAL', b'\xe9\x83\xa8\xe5\x88\x86\xe5\x88\xb0\xe8\xb4\xa7'), (b'FULL_ARRIVAL', b'\xe5\x85\xa8\xe9\x83\xa8\xe5\x88\xb0\xe8\xb4\xa7')])),
                ('extra_info', models.CharField(max_length=1000, verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
                ('purchase', models.ForeignKey(related_name='purchase_items', verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe5\x8d\x95', to='purchases.Purchase')),
            ],
            options={
                'db_table': 'shop_purchases_item',
                'verbose_name': '\u91c7\u8d2d\u9879\u76ee',
                'verbose_name_plural': '\u91c7\u8d2d\u9879\u76ee\u5217\u8868',
                'permissions': [('can_storage_confirm', '\u786e\u8ba4\u5165\u5e93\u6570\u91cf')],
            },
        ),
        migrations.CreateModel(
            name='PurchasePayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origin_nos', models.TextField(verbose_name=b'\xe5\x8e\x9f\xe5\x8d\x95\xe6\x8d\xae\xe5\x8f\xb7', blank=True)),
                ('pay_type', models.CharField(db_index=True, max_length=6, verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe7\xb1\xbb\xe5\x9e\x8b', choices=[(b'COD', b'\xe8\xb4\xa7\xe5\x88\xb0\xe4\xbb\x98\xe6\xac\xbe'), (b'POP', b'\xe9\xa2\x84\xe4\xbb\x98\xe6\xac\xbe'), (b'POD', b'\xe4\xbb\x98\xe6\xac\xbe\xe6\x8f\x90\xe8\xb4\xa7'), (b'OTHER', b'\xe5\x85\xb6\xe5\xae\x83')])),
                ('apply_time', models.DateTimeField(null=True, verbose_name=b'\xe7\x94\xb3\xe8\xaf\xb7\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('pay_time', models.DateTimeField(null=True, verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('payment', models.FloatField(default=0, verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe9\x87\x91\xe9\xa2\x9d')),
                ('created', models.DateTimeField(auto_now=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('status', models.CharField(default=b'WAIT_APPLY', max_length=12, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'WAIT_APPLY', b'\xe6\x9c\xaa\xe7\x94\xb3\xe8\xaf\xb7'), (b'WAIT_PAMMENT', b'\xe5\xbe\x85\xe4\xbb\x98\xe6\xac\xbe'), (b'HAS_PAMMENT', b'\xe5\xb7\xb2\xe4\xbb\x98\xe6\xac\xbe'), (b'INVALID', b'\xe5\xb7\xb2\xe4\xbd\x9c\xe5\xba\x9f')])),
                ('applier', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe7\x94\xb3\xe8\xaf\xb7\xe4\xba\xba', blank=True)),
                ('cashier', models.CharField(db_index=True, max_length=32, verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe4\xba\xba', blank=True)),
                ('pay_no', models.CharField(db_index=True, max_length=256, verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe6\xb5\x81\xe6\xb0\xb4\xe5\x8d\x95\xe5\x8f\xb7', blank=True)),
                ('pay_bank', models.CharField(max_length=128, verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe9\x93\xb6\xe8\xa1\x8c(\xe5\xb9\xb3\xe5\x8f\xb0)', blank=True)),
                ('extra_info', models.TextField(max_length=1000, verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
                ('supplier', models.ForeignKey(related_name='purchase_payments', verbose_name=b'\xe6\x94\xb6\xe6\xac\xbe\xe6\x96\xb9', blank=True, to='archives.Supplier', null=True)),
            ],
            options={
                'db_table': 'shop_purchases_payment',
                'verbose_name': '\u91c7\u8d2d\u4ed8\u6b3e\u5355',
                'verbose_name_plural': '\u91c7\u8d2d\u4ed8\u6b3e\u5355\u5217\u8868',
                'permissions': [('can_payment_confirm', '\u786e\u8ba4\u91c7\u8d2d\u4ed8\u6b3e')],
            },
        ),
        migrations.CreateModel(
            name='PurchasePaymentItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('purchase_id', models.IntegerField(null=True, verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe5\x8d\x95ID', blank=True)),
                ('purchase_item_id', models.IntegerField(null=True, verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe9\xa1\xb9\xe7\x9b\xaeID', blank=True)),
                ('storage_id', models.IntegerField(null=True, verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe5\x8d\x95ID', blank=True)),
                ('storage_item_id', models.IntegerField(null=True, verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe9\xa1\xb9\xe7\x9b\xaeID', blank=True)),
                ('product_id', models.IntegerField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81ID')),
                ('sku_id', models.IntegerField(null=True, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbcID')),
                ('outer_id', models.CharField(max_length=32, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe7\xbc\x96\xe7\xa0\x81')),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('properties_name', models.CharField(max_length=64, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe5\xb1\x9e\xe6\x80\xa7', blank=True)),
                ('payment', models.FloatField(default=0.0, verbose_name=b'\xe6\x94\xaf\xe4\xbb\x98\xe8\xb4\xb9\xe7\x94\xa8')),
                ('purchase_payment', models.ForeignKey(related_name='payment_items', verbose_name=b'\xe4\xbb\x98\xe6\xac\xbe\xe5\x8d\x95', to='purchases.PurchasePayment')),
            ],
            options={
                'db_table': 'shop_purchases_paymentitem',
                'verbose_name': '\u4ed8\u6b3e\u9879\u76ee',
                'verbose_name_plural': '\u4ed8\u6b3e\u9879\u76ee\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseStorage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origin_no', models.CharField(db_index=True, max_length=256, verbose_name=b'\xe5\x8e\x9f\xe5\x8d\x95\xe6\x8d\xae\xe5\x8f\xb7', blank=True)),
                ('forecast_date', models.DateField(null=True, verbose_name=b'\xe9\xa2\x84\xe8\xae\xa1\xe5\x88\xb0\xe8\xb4\xa7\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('post_date', models.DateField(db_index=True, null=True, verbose_name=b'\xe5\xae\x9e\xe9\x99\x85\xe5\x88\xb0\xe8\xb4\xa7\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('storage_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe6\x95\xb0\xe9\x87\x8f')),
                ('status', models.CharField(default=b'DRAFT', max_length=12, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'DRAFT', b'\xe8\x8d\x89\xe7\xa8\xbf'), (b'APPROVAL', b'\xe5\xae\xa1\xe6\xa0\xb8'), (b'FINISH', b'\xe5\xae\x8c\xe6\x88\x90'), (b'INVALID', b'\xe4\xbd\x9c\xe5\xba\x9f')])),
                ('total_fee', models.FloatField(default=0.0, verbose_name=b'\xe6\x80\xbb\xe9\x87\x91\xe9\xa2\x9d')),
                ('prepay', models.FloatField(default=0.0, verbose_name=b'\xe9\xa2\x84\xe4\xbb\x98\xe9\xa2\x9d')),
                ('payment', models.FloatField(default=0.0, verbose_name=b'\xe5\xae\x9e\xe4\xbb\x98\xe6\xac\xbe')),
                ('logistic_company', models.CharField(max_length=64, verbose_name=b'\xe7\x89\xa9\xe6\xb5\x81\xe5\x85\xac\xe5\x8f\xb8', blank=True)),
                ('out_sid', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe7\x89\xa9\xe6\xb5\x81\xe7\xbc\x96\xe5\x8f\xb7', blank=True)),
                ('is_addon', models.BooleanField(default=False, verbose_name=b'\xe5\x8a\xa0\xe5\x85\xa5\xe5\xba\x93\xe5\xad\x98')),
                ('extra_name', models.CharField(max_length=256, verbose_name=b'\xe6\xa0\x87\xe9\xa2\x98', blank=True)),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
                ('is_pod', models.BooleanField(default=False, verbose_name=b'\xe9\x9c\x80\xe4\xbb\x98\xe6\xac\xbe\xe6\x8f\x90\xe8\xb4\xa7')),
                ('attach_files', models.FileField(upload_to=b'site_media/download/storage', blank=True)),
                ('deposite', models.ForeignKey(related_name='purchases_storages', verbose_name=b'\xe4\xbb\x93\xe5\xba\x93', blank=True, to='archives.Deposite', null=True)),
                ('supplier', models.ForeignKey(related_name='purchase_storages', verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86', blank=True, to='archives.Supplier', null=True)),
            ],
            options={
                'db_table': 'shop_purchases_storage',
                'verbose_name': '\u5165\u5e93\u5355',
                'verbose_name_plural': '\u5165\u5e93\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseStorageItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('supplier_item_id', models.CharField(max_length=64, verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86\xe8\xb4\xa7\xe5\x8f\xb7', blank=True)),
                ('product_id', models.IntegerField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81ID')),
                ('sku_id', models.IntegerField(null=True, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbcID')),
                ('outer_id', models.CharField(max_length=32, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('properties_name', models.CharField(max_length=64, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe5\xb1\x9e\xe6\x80\xa7', blank=True)),
                ('storage_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe6\x95\xb0\xe9\x87\x8f')),
                ('created', models.DateTimeField(auto_now=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('total_fee', models.FloatField(default=0.0, verbose_name=b'\xe6\x80\xbb\xe9\x87\x91\xe9\xa2\x9d')),
                ('prepay', models.FloatField(default=0.0, verbose_name=b'\xe9\xa2\x84\xe4\xbb\x98\xe9\xa2\x9d')),
                ('payment', models.FloatField(default=0.0, verbose_name=b'\xe5\xb7\xb2\xe4\xbb\x98\xe6\xac\xbe')),
                ('status', models.CharField(default=b'normal', max_length=12, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(b'normal', b'\xe6\x9c\x89\xe6\x95\x88'), (b'delete', b'\xe4\xbd\x9c\xe5\xba\x9f')])),
                ('is_addon', models.BooleanField(default=False, verbose_name=b'\xe5\x8a\xa0\xe5\x85\xa5\xe5\xba\x93\xe5\xad\x98')),
                ('extra_info', models.CharField(max_length=1000, verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
                ('purchase_storage', models.ForeignKey(related_name='purchase_storage_items', verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe5\x8d\x95', to='purchases.PurchaseStorage')),
            ],
            options={
                'db_table': 'shop_purchases_storageitem',
                'verbose_name': '\u5165\u5e93\u9879\u76ee',
                'verbose_name_plural': '\u5165\u5e93\u9879\u76ee\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseStorageRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('purchase_id', models.IntegerField(verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe5\x8d\x95ID')),
                ('purchase_item_id', models.IntegerField(verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe9\xa1\xb9\xe7\x9b\xaeID')),
                ('storage_id', models.IntegerField(verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe5\x8d\x95ID', db_index=True)),
                ('storage_item_id', models.IntegerField(verbose_name=b'\xe5\x85\xa5\xe5\xba\x93\xe9\xa1\xb9\xe7\x9b\xaeID')),
                ('product_id', models.IntegerField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81ID')),
                ('sku_id', models.IntegerField(null=True, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbcID')),
                ('outer_id', models.CharField(max_length=32, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe7\xbc\x96\xe7\xa0\x81')),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name=b'\xe8\xa7\x84\xe6\xa0\xbc\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('is_addon', models.BooleanField(default=False, verbose_name=b'\xe7\xa1\xae\xe8\xae\xa4\xe6\x94\xb6\xe8\xb4\xa7')),
                ('storage_num', models.IntegerField(default=0, null=True, verbose_name=b'\xe5\x85\xb3\xe8\x81\x94\xe5\x85\xa5\xe5\xba\x93\xe6\x95\xb0\xe9\x87\x8f')),
                ('total_fee', models.FloatField(default=0.0, verbose_name=b'\xe5\xba\x94\xe4\xbb\x98\xe8\xb4\xb9\xe7\x94\xa8')),
                ('prepay', models.FloatField(default=0.0, verbose_name=b'\xe9\xa2\x84\xe4\xbb\x98\xe8\xb4\xb9\xe7\x94\xa8')),
                ('payment', models.FloatField(default=0.0, verbose_name=b'\xe6\x94\xaf\xe4\xbb\x98\xe8\xb4\xb9\xe7\x94\xa8')),
            ],
            options={
                'db_table': 'shop_purchases_relationship',
                'verbose_name': '\u91c7\u8d2d\u5165\u5e93\u5173\u8054',
                'verbose_name_plural': '\u91c7\u8d2d\u5165\u5e93\u5173\u8054',
            },
        ),
        migrations.AlterUniqueTogether(
            name='purchasestoragerelationship',
            unique_together=set([('purchase_id', 'purchase_item_id', 'storage_id', 'storage_item_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='purchasestorageitem',
            unique_together=set([('purchase_storage', 'product_id', 'sku_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='purchaseitem',
            unique_together=set([('purchase', 'product_id', 'sku_id')]),
        ),
    ]
