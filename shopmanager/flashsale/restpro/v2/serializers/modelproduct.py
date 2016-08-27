# coding: utf-8

import datetime

from django.conf import settings
from rest_framework import serializers

from flashsale.pay.models import ModelProduct, Favorites, Customer
from flashsale.restpro.local_cache import image_watermark_cache

class SimpleModelProductSerializer(serializers.HyperlinkedModelSerializer):

    # url = serializers.HyperlinkedIdentityField(view_name='rest_v2:modelproduct-detail')
    category_id = serializers.IntegerField(source='salecategory.id', read_only=True)
    is_saleout  = serializers.BooleanField(source='is_sale_out', read_only=True)
    web_url     = serializers.CharField(source='get_web_url', read_only=True)
    watermark_op = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'category_id', 'lowest_agent_price', 'lowest_std_sale_price',
                  'onshelf_time', 'offshelf_time', 'is_saleout', 'sale_state',
                  'head_img', 'web_url', 'watermark_op')

    def get_watermark_op(self, obj):
        if not obj.is_watermark:
            return ''
        return image_watermark_cache.latest_qs or ''


class ModelProductSerializer(serializers.ModelSerializer):

    detail_content = serializers.SerializerMethodField()
    extras = serializers.SerializerMethodField()
    sku_info = serializers.SerializerMethodField()
    custom_info = serializers.SerializerMethodField()
    teambuy_info = serializers.SerializerMethodField()

    class Meta:
        model = ModelProduct
        fields = ('id', 'detail_content', 'sku_info', 'comparison', 'extras', 'custom_info', 'teambuy_info') #

    def get_detail_content(self, obj):
        content = obj.detail_content
        if obj.is_flatten:
            request = self.context.get('request')
            product_id = request.GET.get('product_id', None)
            if product_id and product_id.isdigit():
                product = obj.products.filter(id=product_id).first()
                content['name'] = product.name
                content['head_imgs'] = [product.pic_path]
        return content

    def get_extras(self, obj):
        return obj.extras.get('saleinfos',{})

    def get_sku_info(self, obj):
        if obj.is_flatten:
            request = self.context.get('request')
            product_id = request.GET.get('product_id',None)
            if  product_id and product_id.isdigit():
                product = obj.products.filter(id=product_id).first()
                return obj.product_simplejson(product)
        return obj.sku_info

    def get_custom_info(self, obj):
        request = self.context['request']
        if not request.user.is_authenticated():
            return {'is_favorite': False}
        customer = Customer.objects.filter(user=request.user).first()
        if not customer:
            return {'is_favorite': False}
        favorite = Favorites.objects.filter(customer=customer, model=obj)
        return {'is_favorite': favorite and True or False}

    def get_teambuy_info(self, obj):
        if not obj.is_teambuy:
            return {'teambuy': False}
        return {
            'teambuy':True,
            'teambuy_price': obj.teambuy_price,
            'teambuy_person_num': obj.teambuy_person_num
        }