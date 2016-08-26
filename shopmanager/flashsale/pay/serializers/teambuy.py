# -*- encoding:utf-8 -*-
from django.forms import model_to_dict
from rest_framework import serializers

from shopback.items.models import Product, ProductSku
from ..models import SaleTrade, District, UserAddress, ModelProduct, BrandProduct
from ..models.teambuy import TeamBuy, TeamBuyDetail


class TeamBuySerializer(serializers.ModelSerializer):
    detail_info = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()

    class Meta:
        model = TeamBuy
        fields = ('id', 'sku', 'product_info', 'limit_time', 'limit_days', 'status', 'detail_info')

    def get_detail_info(self, obj):
        res = []
        for detail in obj.details.all():
            item = {
                'oid': detail.oid,
                'tid': detail.tid,
                'customer_id': detail.customer.id,
                'customer_nick': detail.customer.nick,
                'customer_thumbnail': detail.customer.thumbnail,
                'join_time': detail.created,
                'info': u'发起团购' if detail.originizer else u'加入团购',
            }
            res.append(item)
        return res

    def get_product_info(self, obj):
        product = obj.sku.product
        model_product = product.get_product_model()
        res = {
            'price': model_product.teambuy_price,
            "head_imgs": [product.pic_path],
            "name": product.name,
            "item_marks": [
                "包邮"
            ]
        }
        return res
