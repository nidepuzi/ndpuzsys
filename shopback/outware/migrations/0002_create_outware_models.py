# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-14 10:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
import shopback.outware.models.wareauth


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('outware', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutwareActionRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('object_id', models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u5bf9\u8c61id')),
                ('action_code', models.CharField(db_index=True, max_length=8, verbose_name='\u64cd\u4f5c\u7f16\u53f7')),
                ('state_code', models.IntegerField(choices=[(0, '\u826f\u597d'), (1, '\u51fa\u9519')], db_index=True, verbose_name='\u72b6\u6001\u7f16\u7801')),
                ('message', models.CharField(max_length=256, verbose_name='\u64cd\u4f5c\u4fe1\u606f')),
                ('record_obj', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', verbose_name='\u5173\u8054\u5bf9\u8c61')),
            ],
            options={
                'db_table': 'outware_action_record',
                'verbose_name': '\u5916\u4ed3/\u64cd\u4f5c\u8bb0\u5f55',
                'verbose_name_plural': '\u5916\u4ed3/\u64cd\u4f5c\u8bb0\u5f55',
            },
        ),
        migrations.CreateModel(
            name='OutwareInboundOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('inbound_code', models.CharField(db_index=True, max_length=64, verbose_name='\u5165\u4ed3\u5355/\u9500\u9000\u5165\u4ed3\u7f16\u53f7')),
                ('store_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u5916\u90e8\u4ed3\u5e93\u7f16\u53f7')),
                ('order_type', models.CharField(choices=[('601', '\u91c7\u8d2d\u5165\u4ed3\u5355'), ('501', '\u9500\u9000\u8d27\u5355')], db_index=True, max_length=16, verbose_name='\u5355\u636e\u7c7b\u578b')),
                ('status', models.SmallIntegerField(choices=[(0, '\u6b63\u5e38'), (1, '\u53d6\u6d88')], db_index=True, default=0, verbose_name='\u8ba2\u5355\u72b6\u6001')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=10240, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_inbound',
                'verbose_name': '\u5916\u4ed3/\u63a8\u9001\u5165\u4ed3\u5355',
                'verbose_name_plural': '\u5916\u4ed3/\u63a8\u9001\u5165\u4ed3\u5355',
            },
        ),
        migrations.CreateModel(
            name='OutwareInboundSku',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('sku_code', models.CharField(db_index=True, max_length=64, verbose_name='\u5185\u90e8SKU\u7f16\u53f7')),
                ('batch_no', models.CharField(db_index=True, max_length=32, verbose_name='\u6279\u6b21\u53f7')),
                ('push_qty', models.IntegerField(default=0, verbose_name='\u5165\u4ed3\u521b\u5efa\u6570\u91cf')),
                ('pull_good_qty', models.IntegerField(default=0, verbose_name='\u5916\u4ed3\u5165\u4ed3\u826f\u54c1\u6570')),
                ('pull_bad_qty', models.IntegerField(default=0, verbose_name='\u5916\u4ed3\u5165\u4ed3\u6b21\u54c1\u6570')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=1024, verbose_name='\u9644\u52a0\u4fe1\u606f')),
                ('outware_inboind', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareInboundOrder', verbose_name='\u5173\u8054\u63a8\u9001\u5165\u4ed3\u5355')),
            ],
            options={
                'db_table': 'outware_inboundsku',
                'verbose_name': '\u5916\u4ed3/\u63a8\u9001\u5165\u4ed3SKU',
                'verbose_name_plural': '\u5916\u4ed3/\u63a8\u9001\u5165\u4ed3SKU',
            },
        ),
        migrations.CreateModel(
            name='OutwareOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('order_type', models.CharField(choices=[('401', '\u9500\u552e\u8ba2\u5355'), ('301', '\u9000\u4ed3\u5355')], db_index=True, max_length=16, verbose_name='\u5305\u88f9\u7c7b\u578b')),
                ('store_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u5916\u90e8\u4ed3\u5e93\u7f16\u53f7')),
                ('union_order_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u7ec4\u5408\u8ba2\u5355\u7f16\u53f7')),
                ('status', models.SmallIntegerField(choices=[(0, '\u6b63\u5e38'), (1, '\u53d6\u6d88')], db_index=True, default=0, verbose_name='\u8ba2\u5355\u72b6\u6001')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=1024, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_order',
                'verbose_name': '\u5916\u4ed3/\u63a8\u9001\u8ba2\u5355',
                'verbose_name_plural': '\u5916\u4ed3/\u63a8\u9001\u8ba2\u5355',
            },
        ),
        migrations.CreateModel(
            name='OutwareOrderSku',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('union_order_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u5173\u8054\u7ec4\u5408\u8ba2\u5355\u7f16\u53f7')),
                ('origin_skuorder_no', models.CharField(db_index=True, max_length=32, verbose_name='\u539f\u59cbSKU\u8ba2\u5355\u7f16\u53f7')),
                ('sku_code', models.CharField(blank=True, db_index=True, max_length=64, verbose_name='\u5185\u90e8SKU\u7f16\u53f7')),
                ('sku_qty', models.IntegerField(default=0, verbose_name='\u63a8\u9001\u8ba2\u5355SKU\u6570\u91cf')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=1024, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_ordersku',
                'verbose_name': '\u5916\u4ed3/\u63a8\u9001\u8ba2\u5355sku',
                'verbose_name_plural': '\u5916\u4ed3/\u63a8\u9001\u8ba2\u5355sku',
            },
        ),
        migrations.CreateModel(
            name='OutwarePackage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('package_type', models.CharField(choices=[('401', '\u9500\u552e\u8ba2\u5355'), ('301', '\u9000\u4ed3\u5355')], db_index=True, max_length=16, verbose_name='\u5305\u88f9\u7c7b\u578b')),
                ('package_order_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u9500\u5355/\u9000\u4ed3\u5355\u7f16\u53f7')),
                ('store_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u5916\u90e8\u4ed3\u5e93\u7f16\u53f7')),
                ('logistics_no', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u5feb\u9012\u5355\u53f7')),
                ('carrier_code', models.CharField(blank=True, db_index=True, max_length=20, verbose_name='\u5feb\u9012\u516c\u53f8\u7f16\u7801')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=512, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_package',
                'verbose_name': '\u5916\u4ed3/\u53d1\u9001\u5305\u88f9',
                'verbose_name_plural': '\u5916\u4ed3/\u53d1\u9001\u5305\u88f9',
            },
        ),
        migrations.CreateModel(
            name='OutwarePackageSku',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('origin_skuorder_no', models.CharField(db_index=True, max_length=32, verbose_name='\u539f\u59cbSKU\u8ba2\u5355\u7f16\u53f7')),
                ('sku_code', models.CharField(blank=True, db_index=True, max_length=64, verbose_name='\u5185\u90e8SKU\u7f16\u53f7')),
                ('batch_no', models.CharField(db_index=True, max_length=32, verbose_name='\u6279\u6b21\u53f7')),
                ('sku_qty', models.IntegerField(default=0, verbose_name='\u63a8\u9001\u8ba2\u5355SKU\u6570\u91cf')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=512, verbose_name='\u9644\u52a0\u4fe1\u606f')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwarePackage', verbose_name='\u5173\u8054\u5305\u88f9')),
            ],
            options={
                'db_table': 'outware_packagesku',
                'verbose_name': '\u5916\u4ed3/\u53d1\u9001\u5305\u88f9sku',
                'verbose_name_plural': '\u5916\u4ed3/\u53d1\u9001\u5305\u88f9sku',
            },
        ),
        migrations.CreateModel(
            name='OutwareSku',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('sku_code', models.CharField(db_index=True, max_length=64, verbose_name='\u5185\u90e8SKU\u7f16\u53f7')),
                ('ware_sku_code', models.CharField(db_index=True, max_length=64, verbose_name='\u5916\u90e8SKU\u7f16\u53f7')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=1024, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_sku',
                'verbose_name': '\u5916\u4ed3/\u5bf9\u63a5\u5546\u54c1SKU',
                'verbose_name_plural': '\u5916\u4ed3/\u5bf9\u63a5\u5546\u54c1SKU',
            },
        ),
        migrations.CreateModel(
            name='OutwareSkuStock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('batch_no', models.CharField(db_index=True, max_length=32, verbose_name='\u6279\u6b21\u53f7')),
                ('sku_code', models.CharField(db_index=True, max_length=64, verbose_name='\u5185\u90e8SKU\u7f16\u53f7')),
                ('store_code', models.CharField(blank=True, db_index=True, max_length=32, verbose_name='\u5916\u90e8\u4ed3\u5e93\u7f16\u53f7')),
                ('push_sku_good_qty', models.IntegerField(default=0, help_text='\u6839\u636e\u5165\u4ed3\u5b9e\u9645\u6536\u8d27\u826f\u54c1\u6570\u91cf\u7d2f\u52a0', verbose_name='\u53d1\u7ed9\u5916\u4ed3SKU\u826f\u54c1\u6570')),
                ('push_sku_bad_qty', models.IntegerField(default=0, help_text='\u6839\u636e\u5165\u4ed3\u5b9e\u9645\u6536\u8d27\u6b21\u54c1\u6570\u91cf\u7d2f\u52a0', verbose_name='\u53d1\u7ed9\u5916\u4ed3SKU\u6b21\u54c1\u6570')),
                ('pull_good_available_qty', models.IntegerField(default=0, verbose_name='\u5916\u4ed3\u53ef\u5206\u914d\u826f\u54c1\u6570')),
                ('pull_good_lock_qty', models.IntegerField(default=0, verbose_name='\u5916\u4ed3\u5df2\u9501\u5b9a\u826f\u54c1\u6570')),
                ('pull_bad_qty', models.IntegerField(default=0, verbose_name='\u5916\u4ed3\u6b21\u54c1\u6570')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=5012, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_skustock',
                'verbose_name': '\u5916\u4ed3/\u5bf9\u63a5\u5546\u54c1SKU\u5e93\u5b58',
                'verbose_name_plural': '\u5916\u4ed3/\u5bf9\u63a5\u5546\u54c1SKU\u5e93\u5b58',
            },
        ),
        migrations.CreateModel(
            name='OutwareSupplier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, db_index=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('vendor_code', models.CharField(blank=True, db_index=True, max_length=64, verbose_name='\u4f9b\u5e94\u5546\u7f16\u53f7')),
                ('vendor_name', models.CharField(blank=True, db_index=True, max_length=64, verbose_name='\u4f9b\u5e94\u5546\u540d\u79f0')),
                ('uni_key', models.CharField(max_length=128, unique=True, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=1024, verbose_name='\u9644\u52a0\u4fe1\u606f')),
            ],
            options={
                'db_table': 'outware_supplier',
                'verbose_name': '\u5916\u4ed3/\u5bf9\u63a5\u4f9b\u5e94\u5546',
                'verbose_name_plural': '\u5916\u4ed3/\u5bf9\u63a5\u4f9b\u5e94\u5546',
            },
        ),
        migrations.AlterField(
            model_name='outwareaccount',
            name='app_id',
            field=models.CharField(default=shopback.outware.models.wareauth.gen_default_appid, max_length=64, unique=True, verbose_name='\u56de\u8c03APPID'),
        ),
        migrations.AlterField(
            model_name='outwareaccount',
            name='app_secret',
            field=models.CharField(blank=True, max_length=64, verbose_name='\u56de\u8c03SECRET'),
        ),
        migrations.AddField(
            model_name='outwaresupplier',
            name='outware_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareAccount', verbose_name='\u5173\u8054\u8d26\u53f7'),
        ),
        migrations.AddField(
            model_name='outwareskustock',
            name='outware_supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareSupplier', verbose_name='\u5173\u8054\u4f9b\u5e94\u5546'),
        ),
        migrations.AddField(
            model_name='outwaresku',
            name='outware_supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareSupplier', verbose_name='\u5173\u8054\u4f9b\u5e94\u5546'),
        ),
        migrations.AddField(
            model_name='outwarepackage',
            name='outware_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareAccount', verbose_name='\u5173\u8054\u8d26\u53f7'),
        ),
        migrations.AddField(
            model_name='outwareordersku',
            name='outware_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareAccount', verbose_name='\u5173\u8054\u8d26\u53f7'),
        ),
        migrations.AddField(
            model_name='outwareorder',
            name='outware_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareAccount', verbose_name='\u5173\u8054\u8d26\u53f7'),
        ),
        migrations.AddField(
            model_name='outwareinboundorder',
            name='outware_supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='outware.OutwareSupplier', verbose_name='\u5173\u8054\u4f9b\u5e94\u5546'),
        ),
    ]