# -*- encoding:utf-8 -*-
from django.forms import model_to_dict
from rest_framework import serializers

from shopback.items.models import Product
from flashsale.pay.models import ProductSku
from ..models import SaleTrade, District, UserAddress, ModelProduct, SaleRefund
from pms.supplier.serializers import SaleSupplierSimpleSerializer, SaleCategorySerializer,\
    StatusField, JSONParseField # todo@黄炎
from statistics.serializers import ModelStatsSimpleSerializer
from pms.supplier.models import SaleProductManage


class DetailInfoField(serializers.Field):
    def to_representation(self, obj):

        detail_dict = {'head_imgs': [], 'content_imgs': [],
                       'buy_limit': obj.buy_limit,
                       'per_limit': obj.per_limit}
        if obj.head_imgs.strip():
            detail_dict['head_imgs'] = [s.strip() for s in obj.head_imgs.split('\n')
                                        if s.startswith('http://') or s.startswith('https://')]

        if obj.content_imgs.strip():
            detail_dict['content_imgs'] = [s.strip() for s in obj.content_imgs.split('\n')
                                           if s.startswith('http://') or s.startswith('https://')]

        return detail_dict

    def to_internal_value(self, data):
        return data


class CusUidField(serializers.Field):
    def to_representation(self, obj):
        return obj.cus_uid

    def to_internal_value(self, data):
        return data


class ProductSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    class Meta:
        model = Product
        fields = ('id', 'name', 'title', 'category', 'pic_path', 'collect_num', 'std_sale_price',
                  'agent_price', 'sale_out', 'status', 'created', 'memo')


class ProductSkuField(serializers.Field):
    def to_representation(self, obj):
        sku_list = []
        for sku in obj.filter(status=ProductSku.NORMAL):
            sku_dict = model_to_dict(sku)
            sku_dict['sale_out'] = sku.sale_out
            sku_list.append(sku_dict)

        return sku_list

    def to_internal_value(self, data):
        return data


class ProductDetailSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    details = DetailInfoField()
    prod_skus = ProductSkuField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'pic_path', 'collect_num', 'std_sale_price',
                  'agent_price', 'status', 'created', 'memo', 'prod_skus', 'details')


class SaleOrderField(serializers.Field):
    def to_representation(self, obj):
        order_list = []
        for order in obj.all():
            odict = model_to_dict(order)
            odict['refund'] = order.refund
            odict['refundable'] = order.refundable
            order_list.append(odict)
        return order_list

    def to_internal_value(self, data):
        return data


class SaleTradeSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    sale_orders = SaleOrderField()

    class Meta:
        model = SaleTrade
        fields = ('id', 'tid', 'buyer_id', 'buyer_nick', 'channel', 'payment', 'post_fee', 'total_fee', 'channel',
                  'payment', 'post_fee', 'total_fee', 'buyer_message', 'seller_memo', 'created', 'pay_time',
                  'modified', 'consign_time', 'trade_type', 'out_sid', 'logistics_company', 'receiver_name',
                  'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip',
                  'receiver_mobile', 'receiver_phone', 'status', 'status_name', 'sale_orders', 'order_num',
                  'order_type')


class SampleSaleTradeSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()

    class Meta:
        model = SaleTrade
        fields = ('id', 'tid', 'buyer_id', 'buyer_nick', 'channel', 'payment', 'post_fee', 'total_fee', 'channel',
                  'payment', 'post_fee', 'total_fee', 'buyer_message', 'seller_memo', 'created', 'pay_time',
                  'modified', 'consign_time', 'trade_type', 'out_sid', 'logistics_company', 'receiver_name',
                  'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address', 'receiver_zip',
                  'receiver_mobile', 'receiver_phone', 'status', 'status_name', 'order_num', 'order_title',
                  'order_pic')


class UserAddressSerializer(serializers.ModelSerializer):
    # category = SaleCategorySerializer()
    class Meta:
        model = UserAddress
        fields = ('id', 'cus_uid', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district',
                  'receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone', 'default')


# 用户积分Serializer
from ..models import IntegralLog, Integral


class UserIntegralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integral
        fields = ('id', 'integral_user', 'integral_value')


class UserIntegralLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegralLog
        fields = \
            ('id', 'integral_user', 'mobile', 'order', 'log_value', 'log_status', 'log_type', 'in_out', 'created',
             'modified')


class ModelProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'head_imgs', 'content_imgs', 'sale_time')
        # , 'std_sale_price', 'agent_price', 'shelf_status', 'status')


class ModelProductScheduleSerializer(serializers.ModelSerializer):
    # sale_supplier = SaleSupplierSimpleSerializer(read_only=True)
    # sale_category = SaleCategorySerializer(read_only=True)
    status = serializers.CharField(source='product.get_status_display', read_only=True)
    contactor = serializers.CharField(source='charger', read_only=True)
    latest_figures = ModelStatsSimpleSerializer(source='sale_product_figures', read_only=True)
    total_figures = JSONParseField(source='total_sale_product_figures', read_only=True)
    in_schedule = serializers.SerializerMethodField()
    product_id = serializers.CharField(source='product.id', read_only=True)
    pic_path = serializers.CharField(source='product.pic_path', read_only=True)
    ref_link = serializers.CharField(source='product.ref_link', read_only=True)
    outer_id = serializers.CharField(source='product.outer_id', read_only=True)
    name = serializers.CharField(read_only=True)
    #　sale_supplier = serializers.CharField(source='sale_product.sale_supplier.supplier_name', read_only=True)
    sale_supplier = SaleSupplierSimpleSerializer(source='sale_product.sale_supplier', read_only=True)
    sale_category = serializers.CharField(source='product.get_sale_category_id', read_only=True)

    std_sale_price = serializers.CharField(source='product.std_sale_price', read_only=True)
    agent_price = serializers.CharField(source='product.agent_price', read_only=True)
    cost = serializers.CharField(source='product.cost', read_only=True)
    source_type = serializers.CharField(source='sale_product.get_source_type_display', read_only=True)
    class Meta:
        model = ModelProduct
        fields = (
            'id', 'outer_id', 'name', 'agent_price', 'pic_path', 'ref_link', 'status', 'sale_supplier',
            'contactor', 'sale_category', 'std_sale_price', 'agent_price', 'cost', 'latest_figures',
            'total_figures', 'source_type', 'in_schedule', 'extras', 'product_id')

    def get_in_schedule(self, obj):
        """ 判断选品是否在指定排期里面 """
        request = self.context.get('request')
        if request:
            schedule_id = request.GET.get('schedule_id') or None
            if not schedule_id:
                return False
            schedule = SaleProductManage.objects.get(id=schedule_id)
            return obj.id in schedule.model_product_ids
        else:
            return False


class SaleRefundSerializer(serializers.ModelSerializer):
    refund_fee_message = serializers.SerializerMethodField()
    tid = serializers.CharField(source='sale_trade.tid')
    channel_display = serializers.CharField(source='sale_trade.get_channel_display')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    good_status_display = serializers.CharField(source='get_good_status_display', read_only=True)
    trade_logistics_company = serializers.CharField(source='package_skuitem.logistics_company_name')
    trade_out_sid = serializers.CharField(source='package_skuitem.out_sid')
    trade_consign_time = serializers.DateTimeField(source='package_skuitem.finish_time')
    order_pic_path = serializers.CharField(source='saleorder.pic_path')
    order_payment = serializers.FloatField(source='saleorder.payment')
    order_status = serializers.IntegerField(source='saleorder.status')
    order_pay_time = serializers.DateTimeField(source='saleorder.pay_time')
    order_status_display = serializers.CharField(source='saleorder.get_status_display')
    postage_num_money = serializers.FloatField(source='get_postage_num_display')
    coupon_num_money = serializers.FloatField(source='get_coupon_num_display')
    manual_refund = serializers.SerializerMethodField()

    class Meta:
        model = SaleRefund
        fields = (
            'id',
            'refund_no',
            'trade_id',
            'order_id',
            'buyer_id',
            'buyer_nick',
            'mobile',
            'phone',
            'refund_id',
            'charge',
            'channel',
            'refund_channel',
            'item_id',
            'title',
            'sku_id',
            'sku_name',
            'ware_by',
            'refund_num',
            'total_fee',
            'payment',
            'refund_fee',
            'amount_flow',
            'success_time',
            'company_name',
            'sid',
            'reason',
            'proof_pic',
            'desc',
            'feedback',
            'has_good_return',
            'has_good_change',
            'is_lackrefund',
            'lackorder_id',
            'good_status',
            'status',
            'postage_num',
            'coupon_num',
            'refund_fee_message',
            'tid',
            'channel_display',
            'status_display',
            'good_status_display',
            'trade_logistics_company',
            'trade_out_sid',
            'trade_consign_time',
            'order_pic_path',
            'order_payment',
            'order_status',
            'order_pay_time',
            'order_status_display',
            'postage_num_money',
            'coupon_num_money',
            'manual_refund'
        )

    def get_refund_fee_message(self, obj):
        trade = obj.sale_trade
        if obj.is_fastrefund:  # 如果是极速退款
            return "[1]退回小鹿钱包 %.2f 元 实付余额%.2f" % (
                obj.refund_fee,
                trade.payment > 0 and (obj.refund_fee / trade.payment) * (obj.payment - trade.pay_cash) or 0)
        budget_logs = obj.get_refund_budget_logs()
        if budget_logs:
            log_money = sum([budget_log.flow_amount for budget_log in budget_logs]) / 100.0
            return '退回小鹿钱包%.2f元 实付金额%.2f'%(log_money, obj.payment)
        return "[2]退回%s %.2f元" % (trade.get_channel_display(), obj.refund_fee)

    def get_manual_refund(self, obj):
        """是否是手动退款
        1. 退款单　买家已经退货　退货待审状态 仓库已经收到货(没有　退款给用户)
        """
        if obj.good_status == SaleRefund.BUYER_RETURNED_GOODS and \
                obj.status == SaleRefund.REFUND_CONFIRM_GOODS and \
                obj.refundproduct:
            return True
        return False
