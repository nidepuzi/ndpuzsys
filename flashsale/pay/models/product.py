# coding=utf-8
from __future__ import unicode_literals

import re
import json
import datetime
import urlparse
import collections
from django.db import models
from django.db.models import F, Sum, Avg
from django.conf import settings
from django.db.models.signals import post_save
from django.core.cache import cache
from django.utils.functional import cached_property
from django.forms.models import model_to_dict
from common.utils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseTagModel
from core.options import get_systemoa_user, log_action, CHANGE

from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSkuContrast, ContrastContent
from shopback.items.models import ProductSku
from shopback.items.constants import SKU_CONSTANTS_SORT_MAP as SM, PROPERTY_NAMES, PROPERTY_KEYMAP
from shopback.items.tasks_stats import task_product_upshelf_notify_favorited_customer
from .. import constants
from .base import PayBaseModel, BaseModel
from ..signals import signal_record_supplier_models
from ..managers import modelproduct

import logging
logger = logging.getLogger(__name__)

WASH_INSTRUCTION ='''洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。
有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。'''.replace('\n','')


class Productdetail(PayBaseModel):
    """　DEPRECATED 该MODEL已废弃，新功能开发请不要引用 """
    OUT_PERCENT = 0  # 未设置代理返利比例
    ZERO_PERCENT = -1
    THREE_PERCENT = 3
    FIVE_PERCENT = 5
    TEN_PERCENT = 10
    TWENTY_PERCENT = 20
    THIRTY_PERCENT = 30

    WEIGHT_CHOICE = ((i, i) for i in range(1, 201)[::-1])
    DISCOUNT_CHOICE = ((i, i) for i in range(1, 101)[::-1])
    BUY_LIMIT_CHOICE = ((i, i) for i in range(1, 21))

    REBETA_CHOICES = ((OUT_PERCENT, u'未设置返利'),
                      (ZERO_PERCENT, u'该商品不返利'),
                      (THREE_PERCENT, u'返利百分之3'),
                      (FIVE_PERCENT, u'返利百分之5'),
                      (TEN_PERCENT, u'返利百分之10'),
                      (TWENTY_PERCENT, u'返利百分之20'),
                      (THIRTY_PERCENT, u'返利百分之30'),)

    product = models.OneToOneField(Product, primary_key=True,
                                   related_name='details', verbose_name=u'库存商品')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    mama_discount = models.IntegerField(default=100, choices=DISCOUNT_CHOICE, verbose_name=u'妈妈折扣')
    is_seckill = models.BooleanField(db_index=True, default=False, verbose_name=u'秒杀')

    is_recommend = models.BooleanField(db_index=True, default=False, verbose_name=u'专区推荐')
    is_sale = models.BooleanField(db_index=True, default=False, verbose_name=u'专场')
    order_weight = models.IntegerField(db_index=True, default=8, choices=WEIGHT_CHOICE, verbose_name=u'权值')
    buy_limit = models.BooleanField(db_index=True, default=False, verbose_name=u'是否限购')
    per_limit = models.IntegerField(default=5, choices=BUY_LIMIT_CHOICE, verbose_name=u'限购数量')

    material = models.CharField(max_length=64, blank=True, verbose_name=u'商品材质')
    color = models.CharField(max_length=64, blank=True, verbose_name=u'可选颜色')
    wash_instructions = models.TextField(default=WASH_INSTRUCTION, blank=True, verbose_name=u'洗涤说明')
    note = models.CharField(max_length=256, blank=True, verbose_name=u'备注')
    mama_rebeta = models.IntegerField(default=OUT_PERCENT, choices=REBETA_CHOICES, db_index=True, verbose_name=u'代理返利')

    rebeta_scheme_id = models.IntegerField(default=0, verbose_name=u'返利计划')

    class Meta:
        db_table = 'flashsale_productdetail'
        app_label = 'pay'
        verbose_name = u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.product.outer_id, self.product.name)

    def mama_rebeta_rate(self):
        if self.mama_rebeta == self.ZERO_PERCENT:
            return 0.0
        if self.mama_rebeta == self.OUT_PERCENT:
            return None
        rate = self.mama_rebeta / 100.0
        assert rate >= 0 and rate <= 1
        return rate

    def head_images(self):
        return self.head_imgs.split()

    @property
    def content_images(self):
        return self.content_imgs.split()

    def update_order_weight(self, order_weight):
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            self.save(update_fields=['order_weight'])
            return True
        return False

    def update_weight_and_recommend(self, is_topic, order_weight, is_recommend):
        p_detail_update_fields = []
        if self.is_sale != is_topic:
            self.is_sale = is_topic
            p_detail_update_fields.append('is_sale')
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            p_detail_update_fields.append('order_weight')
        if self.is_recommend != is_recommend:
            self.is_recommend = is_recommend
            p_detail_update_fields.append('is_recommend')
        if p_detail_update_fields:
            self.save(update_fields=p_detail_update_fields)
            return True


def default_modelproduct_extras_tpl():
    return {
        "saleinfos": {
            "is_product_buy_limit": True,
            "per_limit_buy_num": 20,
            "is_bonded_goods": False, #标识商品是否保税商品
            "is_coupon_deny": False,
        },
        # "payinfo": {
        #     "use_coupon_only": True,
        #     "coupon_template_ids": [
        #       770
        #     ],
        # },
        "new_properties": [],
        "sources": {
            "source_type": 0,
        },
        # "template_id": 530, 对应优惠券id
        "tables": [
            {
                "table": [
                    []
                ]
            }
        ],
    }


class ModelProduct(BaseTagModel):

    API_CACHE_KEY_TPL = 'api_modelproduct_{0}'

    NORMAL = 'normal'
    DELETE = 'delete'
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (DELETE, u'作废')
    )

    ON_SHELF = 'on'
    OFF_SHELF = 'off'
    WILL_SHELF = 'will'  # 即将上新
    SHELF_CHOICES = (
        (ON_SHELF, u'已上架'),
        (OFF_SHELF, u'未上架')
    )

    USUAL_TYPE    = 0
    VIRTUAL_TYPE  = 1
    METARIAL_TYPE = 2
    TYPE_CHOICES = (
        (USUAL_TYPE, u'商品'),
        (VIRTUAL_TYPE, u'虚拟商品'),
        (METARIAL_TYPE, u'包材辅料'),
    )

    name = models.CharField(max_length=64, db_index=True, verbose_name=u'款式名称')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)', help_text=u'商品分享展示图片(取首张)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)',  help_text=u"多色则多图，单色则单图")
    detail_first_img = models.TextField(blank=True, verbose_name=u'详情首图')
    title_imgs = JSONCharMyField(max_length=5000, verbose_name=u'主图', help_text=u"多色则多图，单色则单图")
    salecategory = models.ForeignKey('supplier.SaleCategory', null=True, default=None,
                                     related_name='modelproduct_set', verbose_name=u'分类')
    brand = models.ForeignKey('pay.ProductBrand', null=True, blank=True, default=None,
                              on_delete=models.SET_NULL, verbose_name=u'品牌')

    lowest_agent_price = models.FloatField(default=0.0, db_index=True, verbose_name=u'最低售价')
    lowest_std_sale_price = models.FloatField(default=0.0, verbose_name=u'最低原价')

    is_onsale    = models.BooleanField(default=False, db_index=True, verbose_name=u'特价/秒杀')
    is_teambuy   = models.BooleanField(default=False, db_index=True, verbose_name=u'团购')
    is_recommend = models.BooleanField(default=False, db_index=True, verbose_name=u'推荐商品')
    is_topic     = models.BooleanField(default=False, db_index=True, verbose_name=u'专题商品')
    is_flatten   = models.BooleanField(default=False, db_index=True, verbose_name=u'平铺显示')
    is_watermark = models.BooleanField(default=False, db_index=True, verbose_name=u'图片水印')
    is_boutique  = models.BooleanField(default=False, db_index=True, verbose_name=u'精品汇')
    is_outside = models.BooleanField(default=False, db_index=True, verbose_name=u'海外直邮')
    teambuy_price = models.FloatField(default=0, verbose_name=u'团购价')
    teambuy_person_num = models.IntegerField(default=3, verbose_name=u'团购人数')
    charger = models.CharField(default=None,  max_length=32, db_index=True, blank=True, null=True, verbose_name=u'负责人')
    shelf_status = models.CharField(max_length=8, choices=SHELF_CHOICES,
                                    default=OFF_SHELF, db_index=True, verbose_name=u'上架状态')
    onshelf_time  = models.DateTimeField(default=None, blank=True, db_index=True, null=True, verbose_name=u'上架时间')
    offshelf_time = models.DateTimeField(default=None, blank=True, db_index=True, null=True, verbose_name=u'下架时间')

    order_weight = models.IntegerField(db_index=True, default=50, verbose_name=u'权值')
    rebeta_scheme_id = models.IntegerField(default=0, verbose_name=u'返利计划ID')
    saleproduct  = models.ForeignKey('supplier.SaleProduct', null=True, default=None,
                                     related_name='modelproduct_set', verbose_name=u'特卖选品')

    extras  = JSONCharMyField(max_length=5000, default=default_modelproduct_extras_tpl, verbose_name=u'附加信息')
    status = models.CharField(max_length=16, db_index=True, choices=STATUS_CHOICES,
                              default=NORMAL, verbose_name=u'状态')
    product_type = models.IntegerField(choices=TYPE_CHOICES, default=0, db_index=True, verbose_name=u'商品类型')
    objects = modelproduct.ModelProductManager()

    class Meta:
        db_table = 'flashsale_modelproduct'
        app_label = 'pay'
        verbose_name = u'特卖商品/款式'
        verbose_name_plural = u'特卖商品/款式列表'
        permissions = [
            ("change_name_permission", u"修改名字"),
        ]

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.name)

    def delete(self, using=None):
        self.status = self.DELETE
        self.save()

    def head_img(self):
        return self.head_imgs and self.head_imgs.split()[0] or ''

    head_img_url = property(head_img)

    @property
    def content_images(self):
        return [img for img in self.content_imgs.split() if img.strip()]

    @property
    def head_images(self):
        # head_imgs = []
        # for product in self.productobj_list:
        #     head_imgs.append(product.PIC_PATH)
        if self.title_imgs:
            head_imgs = self.title_imgs.values()
            return head_imgs
        return list(self.products.values_list('pic_path', flat=True))

    @property
    def is_single_spec(self):
        """ 是否单颜色 """
        if self.id <= 0:
            return True
        if len(self.productobj_list) > 1:
            return False
        return True

    @property
    def item_product(self):
        if not hasattr(self, '__first_product__'):
            products = self.productobj_list
            if not products:
                return None
            self.__first_product__ = products[0]
        return self.__first_product__

    @property
    def is_sale_out(self):
        """ 是否卖光 """
        if not hasattr(self, '_is_saleout_'):
            all_sale_out = True
            for product in self.productobj_list:
                all_sale_out &= product.is_sale_out()
            self._is_saleout_ = all_sale_out
        return self._is_saleout_

    @property
    def is_virtual_product(self):
        return int(self.product_type) == ModelProduct.VIRTUAL_TYPE or self.model_code.startswith('RMB')

    @property
    def is_boutique_product(self):
        return int(self.product_type) == ModelProduct.USUAL_TYPE and self.is_boutique

    @property
    def is_boutique_coupon(self):
        return int(self.product_type) == ModelProduct.VIRTUAL_TYPE and self.is_boutique

    def get_web_url(self):
        return urlparse.urljoin(settings.M_SITE_URL, Product.MALL_PRODUCT_TEMPLATE_URL.format(self.id))

    @property
    def model_code(self):
        product = self.item_product
        if not product:
            return ''
        return product.outer_id[0:-1]

    @property
    def sale_time(self):
        """  上架时间 """
        product = self.item_product
        if not product or not product.detail:
            return None
        return product.sale_time

    @property
    def sale_state(self):
        if self.shelf_status == self.OFF_SHELF and \
                (not self.onshelf_time or self.onshelf_time > datetime.datetime.now()):
            return self.WILL_SHELF
        return self.shelf_status

    @property
    def category(self):
        """  分类 """
        product = self.item_product
        if not product or not product.category:
            return {}
        return {'id': product.category_id}

    @property
    def is_saleopen(self):
        """ 是否新售 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.sale_open()

    @property
    def is_newsales(self):
        """ 是否新售 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.new_good()

    @property
    def properties(self):
        """ 商品属性 """
        return {}

    def get_properties(self):
        """
        商品颜色尺码 支持老商品
        返回{颜色:[尺码]}
        识别规则：
            对单product
                1、SKU中含有|且分隔了两个字串 表示同时有颜色与尺码
                2、SKU中含有|且分隔了一个字串 字串在前表达颜色，在后表达尺码
                3、SKU中含有统一规格 表示没有多种规格
                4、product中含有/颜色,表示颜色
            对多product
                4、从product的properties_name中获取颜色
                5、从sku中|分隔后个字串获取尺码
        """
        UNIQ_COLOR = u'统一规格'
        UNIQ_SIZE = u'经典'
        res = {}
        if self.products.count() == 1:
            for sku in self.product.prod_skus.filter(status=ProductSku.NORMAL):
                if '|' in sku.properties_name:
                    color, size = sku.properties_name.split('|')
                else:
                    size = sku.properties_name
                    color = self.product.properties_name
                color = color or UNIQ_COLOR
                if color not in res:
                    res[color] = []
                size = size or UNIQ_SIZE
                if not size in res[color]:
                    res[color].append(size)
        else:
            for p in self.products.all():
                color = p.properties_name
                for sku in p.prod_skus.filter(status=ProductSku.NORMAL):
                    if '|' in sku.properties_name:
                        _color, size = sku.properties_name.split('|')
                    else:
                        size = sku.properties_name
                        _color = self.product.properties_name
                    if _color and color == UNIQ_COLOR:
                        color = _color
                    if color not in res:
                        res[color] = []
                    size = size or UNIQ_SIZE
                    if not size in res[color]:
                        res[color].append(size)
        if not res:
            res = {UNIQ_COLOR: UNIQ_SIZE}
        return res

    @property
    def attributes(self):
        new_properties = self.extras.get('new_properties')
        if new_properties :
            new_properties.insert(0,{'name': u'商品编码', 'value':self.model_code})
            for props in new_properties:
                props['value'] = re.sub('^\[.*\]','', props['value'])
            return new_properties

        product = self.item_product
        if not product:
            return []
        detail = product.detail
        prop_value_dict = {'model_code': self.model_code}
        model_properties = self.extras.get('properties', {})
        prop_value_dict.update(model_properties)

        if not model_properties and detail:
            for key in ('material', 'color', 'wash_instructions', 'note'):
                prop_value_dict[key] = getattr(detail, key)

        if isinstance(model_properties, dict):
            attrs = sorted(prop_value_dict.items(), key=lambda x: PROPERTY_KEYMAP.get(x[0], 100))
            PROPERTY_NAME_DICT = dict(PROPERTY_NAMES)
            attr_dict = [{'name': PROPERTY_NAME_DICT.get(key), 'value': value} for key, value in attrs
                         if value.strip() and PROPERTY_NAME_DICT.get(key)]
            return attr_dict
        if isinstance(model_properties, list):
            return model_properties
        return []

    @property
    def products(self):
        return Product.objects.filter(model_id=self.id, status=pcfg.NORMAL)

    @cached_property
    def product(self):
        return Product.objects.filter(model_id=self.id, status=pcfg.NORMAL).first()

    @property
    def productobj_list(self):
        if not hasattr(self, '_productobj_list_'):
            self._productobj_list_ = list(self.products)
        return self._productobj_list_

    @property
    def source_type(self):
        return self.extras.get('sources', {}).get('source_type') or 0

    @property
    def respective_imgs(self):
        # 等同于title_imgs, 用于处理老商品多个product的情况。
        if self.title_imgs:
            return self.title_imgs
        res = {p.properties_name: p.pic_path for p in self.products}
        return res

    def change_title_imgs_skus(self):
        ti = self.title_imgs
        colors = self.get_properties().keys()
        self.title_imgs = dict(zip(colors, [''] * len(colors)))
        for key in self.title_imgs:
            self.title_imgs[key] = ti.get(key, '')

    def set_title_imgs_values(self, respective_imgs=None):
        if respective_imgs:
            self.title_imgs = respective_imgs
        elif not self.title_imgs or (len(self.title_imgs) ==1 and self.title_imgs.values()==['']):
            self.title_imgs = {p.properties_name: p.pic_path for p in self.products}

    def set_title_imgs_key(self):
        colors = self.get_properties().keys()
        initial_imgs_dict = dict(zip(colors, [''] * len(colors)))
        if not self.title_imgs:
            self.title_imgs = initial_imgs_dict
        else:
            for color in colors:
                self.title_imgs[color] = self.title_imgs.get(color, '')

    def set_title_imgs_key_bak(self):
        # title_imgs同时支持了颜色放在Product(每颜色一种)上和颜色放在ProductSku上的情况。
        # 一般使用颜色或规格名为key，如果该名为空，则使用img为key
        if len(self.products) == 0:
            return
        elif len(self.products) > 1:
            keys = [pro.property_name for pro in self.products.all()]
            keys = list(set(keys))
            if None in keys:
                keys.remove(None)
        else:
            product_ids = [pro.id for pro in self.products]
            properties_names = list(ProductSku.objects.filter(product_id__in=product_ids).values_list('properties_name',flat=True).distinct())
            if '|' in properties_names[0]:
                colors = [name.split('|')[0] for name in properties_names]
                colors = list(set(colors))
            else:
                colors = [properties_names[0]]
            keys = [(color if color != '' else 'img') for color in colors]
        initial_imgs_dict = dict(zip(keys, [''] * len(keys)))
        if not self.title_imgs:
            self.title_imgs = initial_imgs_dict
        else:
            _title_imgs = {}
            for key in initial_imgs_dict:
                _title_imgs[key] = self.title_imgs.get(key, initial_imgs_dict[key])
            self.title_imgs = _title_imgs

    def product_simplejson(self, product):
        sku_list = []
        skuobj_list = product.normal_skus
        for sku in skuobj_list:
            sku_list.append({
                'type':'size',
                'sku_id':sku.id,
                'name':sku.name,
                'free_num':sku.free_num,
                'is_saleout': sku.free_num <= 0,
                'std_sale_price':sku.std_sale_price,
                'agent_price':sku.agent_price,
            })
        return {
            'type':'color',
            'product_id':product.id,
            'name':product.property_name,
            'product_img': product.pic_path,
            'outer_id': product.outer_id,
            'is_saleout': product.is_sale_out(),
            'std_sale_price':product.std_sale_price,
            'agent_price':product.agent_price,
            'lowest_price': product.lowest_price(),
            'sku_items': sku_list,
            'elite_score': product.elite_score
        }

    def product_sku_simplejson(self, product, skus):
        sku_list = []
        sku = None
        for sku in skus:
            sku_list.append({
                'type':'size',
                'sku_id':sku.id,
                'name':sku.size,
                'free_num':sku.free_num,
                'is_saleout': sku.free_num <= 0,
                'std_sale_price':sku.std_sale_price,
                'agent_price':sku.agent_price,
            })
        return {
            'type':'color',
            'product_id':product.id,
            'name':sku and sku.color,
            'product_img': product.pic_path,
            'outer_id': product.outer_id,
            'is_saleout': product.is_sale_out(),
            'std_sale_price':product.std_sale_price,
            'agent_price':product.agent_price,
            'lowest_price': product.lowest_price(),
            'sku_items': sku_list,
            'elite_score': product.elite_score
        }

    @property
    def detail_content(self):
        head_imgs = [i for i in self.head_imgs.split() if i.strip()]
        return {
            'name': self.name,
            'model_code': self.model_code,
            'head_img': len(head_imgs) > 0 and head_imgs[0] or '',
            'head_imgs': self.head_images,
            'content_imgs': self.content_images,
            'is_sale_out': False, #self.is_sale_out,
            'is_onsale': self.is_onsale,
            'is_boutique': self.is_boutique,
            'is_recommend':self.is_recommend,
            'is_saleopen': self.is_saleopen,
            'is_flatten': self.is_flatten,
            'is_newsales': self.is_newsales,
            'product_type': self.product_type,
            'lowest_agent_price': self.lowest_agent_price,
            'lowest_std_sale_price': self.lowest_std_sale_price,
            'category': {'id': self.salecategory_id},
            'sale_time': self.onshelf_time,
            'onshelf_time': self.onshelf_time,
            'offshelf_time': self.offshelf_time,
            'sale_state': self.sale_state,
            'properties':self.properties,
            'watermark_op': '',
            'item_marks': [u'包邮'],
            'web_url': self.get_web_url()
        }

    @property
    def sku_info(self):
        product_list = []
        if self.products.count() > 1:
            for p in self.productobj_list:
                product_list.append(self.product_simplejson(p))
            return product_list
        else:
            for color in self.get_properties():
                skus = self.product.get_skus_by_color(color)
                product_list.append(self.product_sku_simplejson(self.product, skus))
            return product_list

    def set_boutique_coupon(self):
        if self.extras.get('template_id'):
            raise Exception(u'已有优惠券不允许设置精品券')

        from flashsale.coupon.services import get_or_create_boutique_template
        usual_model_id = self.saleproduct.product_link.split('?')[0].split('/')[-1]
        if not usual_model_id.isdigit():
            raise ValueError('精品券关联商品款式链接不合法')

        usual_modleproduct = ModelProduct.objects.filter(id=usual_model_id).first()
        usual_product_ids = ','.join(map(str, usual_modleproduct.products.values_list('id', flat=True)))
        if not usual_modleproduct or not usual_modleproduct.is_boutique_product:
            raise ValueError('请输入正确的精品商品链接(商品需打上精品汇标记)')

        # 创建精品券
        coupon_template = get_or_create_boutique_template(
            self.id, self.lowest_agent_price, model_title=self.name,
            usual_modelproduct_ids=str(usual_model_id), usual_product_ids=usual_product_ids,
            model_img=self.head_img_url
        )

        # 设置精品商品只可使用指定优惠券
        usual_modleproduct.set_boutique_coupon_only(coupon_template.id, self.id)
        usual_modleproduct.save()

        # 设置精品券商品不不允许使用优惠券
        self.as_boutique_coupon_product(coupon_template.id)
        self.save()

        for product in self.products:
            product.shelf_status = Product.UP_SHELF
            product.save(update_fields=['shelf_status'])

    def delete_boutique_coupon(self):
        raise

    def format_contrast2table(self, origin_contrast):
        result_data = []
        constants_maps = ContrastContent.contrast_maps()
        constant_set  = set()
        for k1, v1 in origin_contrast.items():
            constant_set.update(v1)
        constant_keys = list(constant_set)
        result_data.append([u'尺码'])
        for k in constant_keys:
            result_data[0].append(constants_maps.get(k, k))
        tmp_result = []
        for k1, v1 in origin_contrast.items():
            temp_list = []
            for key in constant_keys:
                val = v1.get(key, '-')
                temp_list.append(val)
            tmp_result.append([k1] + temp_list)
        tmp_result.sort(key=lambda x:SM.find(x[0][0:2]) if SM.find(x[0][0:2])>-1 else SM.find(x[0][0:1]))
        return result_data + tmp_result

    def get_model_product_profit(self, virtual_model_products=None):
        """
        获取精品汇商品利润

        params:
        - mp <ModelProduct>
        - vmps <[ModelProduct]> 虚拟商品列表
        """
        profit = cache.get('get-model-product-profit-%s' % self.id)
        if profit:
            return profit

        virtual_model_products = virtual_model_products or ModelProduct.objects.get_virtual_modelproducts()

        coupon_template_id = self.extras.get('payinfo', {}).get('coupon_template_ids', [])
        coupon_template_id = coupon_template_id[0] if coupon_template_id else None

        find_mp = None
        for md in virtual_model_products:
            md_bind_tpl_id = md.extras.get('template_id')
            if md_bind_tpl_id and coupon_template_id == md_bind_tpl_id:
                find_mp = md
                break

        if not find_mp:
            return {}

        prices = [x.agent_price for x in find_mp.products]
        min_price = min(prices)
        max_price = max(prices)

        profit = {
            'min': round(self.lowest_agent_price - max_price, 2),
            'max': round(self.lowest_agent_price - min_price, 2)
        }
        cache.set('get-model-product-profit-%s' % self.id, profit, 60*60)
        return profit

    def reset_new_propeties_table_by_comparison(self):
        """
        功能：　设置　extras　的　new_properties 键　的尺码表内容　从　以前的尺码表中读取数据来填充
        """
        old_table = self.comparison['tables']
        if not old_table:
            return
        tt = old_table[0]
        table = tt['table']
        t_head = table[0]
        t_bodys = table[1::]
        values = []
        for t_body in t_bodys:
            c = 0
            dic = {}
            for x in t_body:
                dic.update({t_head[c]: x})
                c += 1
            values.append(dic)
        current_new_properties = self.extras.get('new_properties') or None
        table_head = {"name": "尺码对照参数", "value": t_head}
        table_body = {"name": "尺码表", "value": values}
        if not current_new_properties:
            new_properties = [table_head, table_body]
        else:
            for x in current_new_properties:
                if x.get('name') == '尺码对照参数':
                    x['value'] = t_head
                if x.get('name') == '尺码表':
                    x['value'] = values
            new_properties = current_new_properties
        self.extras.update({'new_properties': new_properties})
        self.save(update_fields=['extras'])
        return

    def set_tables_into_extras(self):
        """
        功能: 将　self.comparison　中 的尺码表保存到extras 中
        """
        old_tables = self.comparison['tables']
        if not old_tables:
            return
        self.extras.update({'tables': old_tables})
        self.save(update_fields=['extras'])
        return

    @property
    def comparison(self):
        uni_set = set()
        constrast_detail = ''
        property_tables  = self.extras.get('tables') or []
        p_tables = len(property_tables) > 0 and property_tables or []
        if not p_tables:
            try:
                product_ids = list(self.products.values_list('id', flat=True))
                skucontrasts = ProductSkuContrast.objects.filter(product__in=product_ids)\
                    .values_list('contrast_detail',flat=True)
                for constrast_detail in skucontrasts:
                    contrast_origin = constrast_detail
                    uni_key = ''.join(sorted(contrast_origin.keys()))
                    if uni_key not in uni_set:
                        uni_set.add(uni_key)
                        p_tables.append({'table': self.format_contrast2table(contrast_origin)})
            except ProductSkuContrast.DoesNotExist:
                logger.warn('ProductSkuContrast not exists:%s' % (constrast_detail))
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
        return {
            'attributes': self.attributes,
            'tables': p_tables,
            'metrics': {
                # 'table':[
                # [u'厚度指数', u'偏薄', u'适中',u'偏厚',u'加厚' ],
                #     [u'弹性指数', u'无弹性', u'微弹性',u'适中', u'强弹性'],
                #     [u'触感指数', u'偏硬', u'柔软', u'适中', u'超柔'],
                # ],
                # 'choices':[2,3,2]
            },
        }

    @classmethod
    def update_schedule_manager_info(cls,
                                     action_user,
                                     sale_product_ids,
                                     upshelf_time,
                                     offshelf_time,
                                     is_topic):
        """
        更新上下架时间和专题类型
        """
        mds = cls.objects.filter(saleproduct__in=sale_product_ids, status=cls.NORMAL)
        for md in mds:
            if md.shelf_status == cls.ON_SHELF:  # 如果是已经上架状态的款式则不去同步时间和专题类型
                continue
            update_fields = []
            if md.onshelf_time != upshelf_time:
                md.onshelf_time = upshelf_time
                update_fields.append('onshelf_time')
            if md.offshelf_time != offshelf_time:
                md.offshelf_time = offshelf_time
                update_fields.append('offshelf_time')
            if md.is_topic != is_topic:
                md.is_topic = is_topic
                update_fields.append('is_topic')
            if update_fields:
                md.save(update_fields=update_fields)
                log_action(action_user, md, CHANGE, u'同步上下架时间和专题类型')

    def update_schedule_detail_info(self, order_weight, is_recommend):
        """
        更新权重和是否推广字段
        """
        update_fields = []
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            update_fields.append('order_weight')
        if self.is_recommend != is_recommend:
            self.is_recommend = is_recommend
            update_fields.append('is_recommend')
        if update_fields:
            self.save(update_fields=update_fields)
            return True

    @classmethod
    def upshelf_right_now_models(cls):
        """需要立即上架的款式"""
        now = datetime.datetime.now()  # 现在时间在上架时间和下架时间之间　状态为正常 处于下架状态
        return cls.objects.filter(
            onshelf_time__lte=now, offshelf_time__gt=now,
            status=cls.NORMAL,
            shelf_status=cls.OFF_SHELF,
            onshelf_time__isnull=False,
            offshelf_time__isnull=False)

    @classmethod
    def offshelf_right_now_models(cls):
        """需要立即下架的款式"""
        now = datetime.datetime.now()  # 下架时间小于现在（在这之前就应该下架）　　状态正常　且处于　上架状态　的　产品
        return cls.objects.filter(
            offshelf_time__lte=now,
            status=cls.NORMAL,
            shelf_status=cls.ON_SHELF)

    def upshelf_model(self):
        """ 上架款式 """
        if self.shelf_status != ModelProduct.ON_SHELF:
            self.shelf_status = ModelProduct.ON_SHELF
            self.save(update_fields=['shelf_status'])
            task_product_upshelf_notify_favorited_customer.delay(self)
            return True
        return False

    def offshelf_model(self):
        """ 下架款式 """
        if self.shelf_status != ModelProduct.OFF_SHELF:
            self.shelf_status = ModelProduct.OFF_SHELF
            self.save(update_fields=['shelf_status'])
            for product in self.products:
                product.offshelf_product()
            if self.is_teambuy:
                product = self.products.first()
                if product:
                    sku = product.prod_skus.first()
                    if sku:
                        from flashsale.pay.models import TeamBuy
                        TeamBuy.end_teambuy(sku)
            return True
        return False

    def update_fields_with_kwargs(self, **kwargs):
        update_fields = []
        source_type = kwargs.pop('source_type', None)
        for k, v in kwargs.iteritems():
            if hasattr(self, k) and getattr(self, k) != v :
                setattr(self, k, v)
                update_fields.append(k)

        if source_type is not None and source_type != self.source_type:
            self.set_product_source_type(source_type)
            update_fields.append('extras')

        if update_fields:
            self.save(update_fields=update_fields)
            return True

        return False

    def set_product_source_type(self, source_type):
        from pms.supplier.models import SaleProduct
        self.extras.setdefault('sources', {'source_type': SaleProduct.SOURCE_SELF})
        self.extras['sources']['source_type'] = source_type
        if 'saleinfos' not in self.extras:
            self.extras['saleinfos'] = {}
        self.extras['saleinfos']['is_bonded_goods'] = \
            source_type in (SaleProduct.SOURCE_BONDED, SaleProduct.SOURCE_OUTSIDE)


    def reset_product_shelf_info(self):
        """
        功能：　重置 items product 的上下架信息
        """
        for pro in self.products:
            pro.reset_shelf_info()
        return

    def reset_shelf_info(self):
        """
        功能：　重置上下架时间　和上架状态
        """
        update_fields = []
        if self.shelf_status != ModelProduct.OFF_SHELF:
            self.shelf_status = ModelProduct.OFF_SHELF
            update_fields.append('shelf_status')
        if self.offshelf_time is not None:
            self.offshelf_time = None
            update_fields.append('offshelf_time')
        if self.onshelf_time is not None:
            self.onshelf_time = None
            update_fields.append('onshelf_time')
        if update_fields:
            self.save(update_fields=update_fields)
        self.reset_product_shelf_info()  # 重置产品
        return

    def update_extras(self, extras):
        """ 更新扩展字段 """
        if self.extras != extras:
            self.extras = extras
            self.save(update_fields=['extras'])
            return True
        return False

    def set_lowest_price(self):
        """ 设置款式最低价格 """
        product_ids = self.products.values_list('id', flat=True)
        skus = ProductSku.objects.filter(product_id__in=product_ids).values_list('agent_price', 'std_sale_price')
        lowest_agent_price = min([sku[0] for sku in skus])
        lowest_std_sale_price = min([sku[1] for sku in skus])
        self.update_fields_with_kwargs(**{
            'lowest_agent_price': lowest_agent_price,
            'lowest_std_sale_price': lowest_std_sale_price
        })

    def set_choose_colors(self):
        """ 更新可选颜色 """
        names = self.products.values('name')
        colors = [cc for cc in set(i['name'].split('/')[-1] for i in names if '/' in i['name'] and i)]
        c = ','.join(colors)
        if not c:
            colors = [i['name'] for i in names]
            c = ','.join(colors)
        if not c:
            return
        extras = self.extras
        extras.setdefault('properties', [])
        properties = extras.get('properties')
        model_properties_d = [{u'可选颜色': c}]
        old_properties_d = dict([(tt['name'], tt['value']) for tt in properties]) if properties else model_properties_d
        old_properties_d.update(model_properties_d[0])
        properties = [{'name': k, "value": v} for k, v in old_properties_d.iteritems()]
        extras.update({'properties': properties})
        self.extras = extras
        self.save(update_fields=['extras'])

    def set_is_flatten(self):
        """
        is_flatten: 平铺展示
        判断： 没有ProductSku或者只有一个则is_fatten = True
        设置： 款式以及款式下的产品is_flatten字段
        """
        products = self.products
        flatten_count = ProductSku.objects.filter(product__in=products).count()
        is_flatten = flatten_count in [0, 1]
        if self.is_boutique:
            is_flatten = False
        products.update(is_flatten=is_flatten)
        if self.is_flatten != is_flatten:
            self.is_flatten = is_flatten
            self.save(update_fields=['is_flatten'])

    def set_boutique_coupon_only(self, coupon_tpl_id, coupon_modelproduct_id):
        # 设置成精品汇商品返利计划
        self.rebeta_scheme_id = constants.BOUTIQUE_PRODUCT_REBETA_SCHEME_ID
        self.extras.update({
            "payinfo": {
                "use_coupon_only": True,
                "coupon_template_ids": [int(coupon_tpl_id)],
                "coupon_modelproduct_id": coupon_modelproduct_id
            }
        })

    def as_boutique_coupon_product(self, coupon_tpl_id):
        sale_infos = self.extras.get('saleinfos', {})
        sale_infos.update({
                "is_coupon_deny": True,
                "per_limit_buy_num": 1000
            })
        self.extras.update({
            "saleinfos": sale_infos,
            "template_id": int(coupon_tpl_id)
        })

    def sale_num(self):
        return None

    def rebet_amount(self):
        return None

    def next_rebet_amount(self):
        return None

    def get_rebate_scheme(self):
        from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
        return AgencyOrderRebetaScheme.get_rebeta_scheme(self.rebeta_scheme_id)

    def set_shelftime_none(self):
        """
        设置上下架时间为空(排期删除明细特殊场景使用)
        """
        if self.shelf_status == ModelProduct.ON_SHELF:  # 上架状态的产品不予处理
            return
        self.onshelf_time = None
        self.offshelf_time = None
        self.save()

    def to_apimodel(self):
        from apis.v1.products import ModelProduct as APIModel
        data = self.__dict__
        data.update({
            'product_ids': self.products.values_list('id',flat=True),
            'sku_info': self.sku_info,
            'comparison': self.comparison,
            'detail_content': self.detail_content,
            'source_type': self.source_type,
            'product_type': self.product_type,
        })
        return APIModel(**data)

    def set_sale_product(self):
        try:
            product = self.products.first()
            self.saleproduct = product.get_sale_product()
            self.save()
        except Exception, e:
            logger.error(e.message, exc_info=True)

    @property
    def is_coupon_deny(self):
        """
        功能：　判断是否阻止使用优惠券　True 表示不能使用优惠券　
        """
        saleinfos = self.extras.get('saleinfos') or None
        if saleinfos:
            is_coupon_deny = saleinfos.get('is_coupon_deny') or False
            return is_coupon_deny
        return False

    @cached_property
    def sale_product(self):
        sp = self.product.get_sale_product()
        if not sp:
            l = self.products.values_list('sale_product', flat=True).distinct()
            l = list(set(l))
            if 0 in l:
                l.remove(0)
            if l:
                from pms.supplier.models import SaleProduct
                sp = SaleProduct.objects.get(id=l[0])
            else:
                from pms.supplier.models.product import SaleProductRelation
                spr = SaleProductRelation.objects.filter(product_id__in=[p.id for p in self.products]).first()
                if spr:
                    sp = spr.sale_product
            return sp
        else:
            return sp

    @cached_property
    def sale_product_figures(self):
        from statistics.models import ModelStats
        return ModelStats.objects.filter(model_id=self.id).first()

    @cached_property
    def total_sale_product_figures(self):
        """ 选品总销售额退货率计算 """
        from statistics.models import ModelStats
        stats = ModelStats.objects.filter(sale_product=self.id)
        agg = stats.aggregate(s_p=Sum('pay_num'), s_rg=Sum('return_good_num'), s_pm=Sum('payment'))
        p_n = agg['s_p']
        rg  = agg['s_rg']
        payment = agg['s_pm']
        rat = round(float(rg) / p_n, 4) if p_n > 0 else 0
        return {'total_pay_num': p_n, 'total_rg_rate': rat, 'total_payment': payment}

    @staticmethod
    def create(product, name=name, extras=extras, is_onsale=False, is_teambuy=False, is_recommend=False,
               is_topic=False, is_flatten=False, is_boutique=False, is_outside=False):
        """
        :param product:
        :param extras:
        :param is_onsale:
        :param is_teambuy:
        :param is_recommend:
        :param is_topic:
        :param is_flatten:
        :param is_boutique:
        :return:
        """
        # 目前一个商品只能对应一个售卖款式
        if product.model_id:
            raise Exception(u'当前商品已有对应的售卖款式，无法再创建一个。')

        model_product = ModelProduct(name=name,
            product_type=product.type,
            lowest_agent_price=product.get_lowest_agent_price(),
            lowest_std_sale_price=product.get_lowest_std_sale_price(),
            is_onsale=is_onsale,
            is_teambuy=is_teambuy,
            is_recommend=is_recommend,
            is_topic=is_topic,
            is_flatten=is_flatten,
            is_boutique=is_boutique)
        try:
            model_product.salecategory = product.category.get_sale_category()
        except:
            pass
        if not extras:
            model_product.extras = default_modelproduct_extras_tpl()
        else:
            model_product.extras = extras
        model_product.save()
        product.model_id = model_product.id
        product.save()

        if model_product.is_boutique_coupon:
            model_product.set_boutique_coupon()

        model_product.set_title_imgs_key()
        model_product.set_title_imgs_values()
        model_product.set_lowest_price()

        if model_product.is_boutique_product:
            model_product.rebeta_scheme_id = constants.BOUTIQUE_PRODUCT_REBETA_SCHEME_ID

        model_product.save()
        model_product.set_sale_product()

        return model_product

    @staticmethod
    def get_by_supplier(supplier_id):
        from pms.supplier.models import SaleProduct, SaleSupplier
        from pms.supplier.models.product import SaleProductRelation
        sale_supplier = SaleSupplier.objects.get(id=supplier_id)
        spids = list(sale_supplier.supplier_products.values_list('id', flat=True))
        product_ids = list(SaleProductRelation.get_products(spids).values_list('id', flat=True))
        model_product_ids = Product.objects.filter(id__in=product_ids).values_list('model_id', flat=True)
        return ModelProduct.objects.filter(id__in=model_product_ids)

    @staticmethod
    def get_by_suppliers(supplier_ids):
        from pms.supplier.models import SaleProduct, SaleSupplier
        from pms.supplier.models.product import SaleProductRelation
        spids = list(SaleProduct.objects.filter(sale_supplier_id__in=supplier_ids).values_list('id', flat=True))
        product_ids = list(SaleProductRelation.get_products(spids).values_list('id', flat=True))
        model_product_ids = Product.objects.filter(id__in=product_ids).values_list('model_id', flat=True)
        return ModelProduct.objects.filter(id__in=model_product_ids)

def invalid_apimodelproduct_cache(sender, instance, *args, **kwargs):
    if hasattr(sender, 'API_CACHE_KEY_TPL'):
        logger.debug('invalid_apimodelproduct_cache: %s' % instance.id)
        cache.delete(ModelProduct.API_CACHE_KEY_TPL.format(instance.id))

post_save.connect(invalid_apimodelproduct_cache, sender=ModelProduct,
                  dispatch_uid='post_save_invalid_apimodelproduct_cache')

def update_product_details_info(sender, instance, created, **kwargs):
    """
    同步更新products details
    """
    systemoa = get_systemoa_user()

    def update_pro_shelf_time(upshelf_time, offshelf_time, is_topic):
        # change the item product shelf time and product detail is_sale order_weight and is_recommend in same time
        def _wrapper(p):
            state = p.update_shelf_time(upshelf_time, offshelf_time)
            if state:
                log_action(systemoa, p, CHANGE, u'系统自动同步排期时间')
            if p.detail:
                p.detail.update_weight_and_recommend(is_topic, instance.order_weight, instance.is_recommend)

        return _wrapper

    # 更新产品item Product信息
    try:
        map(update_pro_shelf_time(instance.onshelf_time,
                                  instance.offshelf_time, instance.is_topic), instance.products)
    except Exception as exc:
        logger.error(exc)

post_save.connect(update_product_details_info, sender=ModelProduct,
                  dispatch_uid=u'post_save_update_product_details_info')


def update_product_onshelf_status(sender, instance, created, **kwargs):
    if instance.shelf_status == ModelProduct.OFF_SHELF:
        instance.offshelf_model()
    for product in instance.products:
        if product.type != instance.product_type:
            product.type = instance.product_type
            product.save()


post_save.connect(update_product_onshelf_status, sender=ModelProduct,
                  dispatch_uid=u'post_save_update_product_onshelf_status')


def modelproduct_update_supplier_info(sender, obj, **kwargs):
    pro = obj.item_product
    if isinstance(pro, Product):
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_select_num = F('total_select_num') + 1
            update_model_fields(supplier, update_fields=['total_select_num'])


signal_record_supplier_models.connect(modelproduct_update_supplier_info,
                                      sender=ModelProduct, dispatch_uid='post_save_modelproduct_update_supplier_info')


class ModelProductSkuContrast(BaseModel):
    """ 商品规格尺寸参数 """
    modelproduct = models.OneToOneField(ModelProduct, primary_key=True, related_name='contrast', verbose_name=u'款式ID')
    contrast_detail = JSONCharMyField(max_length=10240, blank=True, verbose_name=u'对照详情')

    class Meta:
        db_table = 'pay_modelproduct_contrast'
        app_label = 'pay'
        verbose_name = u'特卖商品/款式尺码对照表'
        verbose_name_plural = u'特卖商品/款式尺码对照列表'

    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.modelproduct.id)

'''
class SaleSku(models.Model):
    """ 记录库存商品规格属性类 """

    class Meta:
        db_table = 'flashsale_salesku'
        unique_together = ("outer_id", "product")
        app_label = 'items'
        verbose_name = u'待售sku'
        verbose_name_plural = u'待售sku列表'

    API_CACHE_KEY_TPL = 'api_productsku_{0}'

    NORMAL = pcfg.NORMAL
    REMAIN = pcfg.REMAIN
    DELETE = pcfg.DELETE
    STATUS_CHOICES = (
        (pcfg.NORMAL, u'使用'),
        (pcfg.REMAIN, u'待用'),
        (pcfg.DELETE, u'作废'),
    )

    outer_id = models.CharField(max_length=32, blank=False, verbose_name=u'编码')

    supplier_skucode = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'供应商SKU编码')
    barcode = models.CharField(max_length=64, blank=True, db_index=True, verbose_name='条码')
    product = models.ForeignKey(Product, null=True, related_name='prod_skus', verbose_name='商品')

    quantity = models.IntegerField(default=0, verbose_name='库存数')
    warn_num = models.IntegerField(default=0, verbose_name='警戒数')  # 警戒库位
    remain_num = models.IntegerField(default=0, verbose_name='预留数')  # 预留库存
    wait_post_num = models.IntegerField(default=0, verbose_name='待发数')  # 待发数
    sale_num = models.IntegerField(default=0, verbose_name=u'日出库数')  # 日出库
    reduce_num = models.IntegerField(default=0, verbose_name='预减数')  # 下次入库减掉这部分库存
    lock_num = models.IntegerField(default=0, verbose_name='锁定数')  # 特卖待发货，待付款数量
    sku_inferior_num = models.IntegerField(default=0, verbose_name=u"次品数")  # 保存对应sku的次品数量

    cost = models.FloatField(default=0, verbose_name='成本价')
    std_purchase_price = models.FloatField(default=0, verbose_name='标准进价')
    std_sale_price = models.FloatField(default=0, verbose_name='吊牌价')
    agent_price = models.FloatField(default=0, verbose_name='出售价')
    staff_price = models.FloatField(default=0, verbose_name='员工价')

    weight = models.CharField(max_length=10, blank=True, verbose_name='重量(g)')

    properties_name = models.TextField(max_length=200, blank=True, verbose_name='线上规格名称')
    properties_alias = models.TextField(max_length=200, blank=True, verbose_name='系统规格名称')

    is_split = models.BooleanField(default=False, verbose_name='需拆分')
    is_match = models.BooleanField(default=False, verbose_name='有匹配')

    sync_stock = models.BooleanField(default=True, verbose_name='库存同步')
    # 是否手动分配库存，当库存充足时，系统自动设为False，手动分配过后，确定后置为True
    is_assign = models.BooleanField(default=False, verbose_name='手动分配')

    post_check = models.BooleanField(default=False, verbose_name='需扫描')
    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改时间')
    status = models.CharField(max_length=10, db_index=True, choices=STATUS_CHOICES,
                              default=pcfg.NORMAL, verbose_name='规格状态')  # normal,delete

    match_reason = models.CharField(max_length=80, blank=True, verbose_name='匹配原因')
    buyer_prompt = models.CharField(max_length=60, blank=True, verbose_name='客户提示')
    memo = models.TextField(max_length=1000, blank=True, verbose_name='备注')

    def __unicode__(self):
        return '<%s,%s:%s>' % (self.id, self.outer_id, self.properties_alias or self.properties_name)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @property
    def realtime_quantity(self):
        """
        This tells how many quantity in store.
        """
        sku_stats = self.stat
        if sku_stats:
            return self.stat.realtime_quantity
        return 0

    @property
    def real_inferior_quantity(self):
        return self.stat.inferior_num

    @property
    def excess_quantity(self):
        """ 多余未售库存数 """
        sku_stats = self.stat
        if sku_stats:
            return max(0, sku_stats.realtime_quantity - sku_stats.wait_post_num)
        return 0

    @property
    def aggregate_quantity(self):
        """
        This tells how many quantity we have in total since we introduced inbound_quantity.
        """
        raise NotImplementedError

    @property
    def name(self):
        return self.properties_alias or self.properties_name

    @property
    def title(self):
        return self.product.name

    @property
    def BARCODE(self):
        return self.barcode.strip() or '%s%s' % (self.product.outer_id.strip(),
                                                 self.outer_id.strip())

    def get_supplier_outerid(self):
        return re.sub('-[0-9]$', '', self.outer_id)

    @property
    def realnum(self):
        if self.remain_num >= self.sale_num:
            return self.remain_num - self.sale_num
        return 0

    @property
    def real_remainnum(self):
        """ 实际剩余库存 """
        wait_post_num = max(self.wait_post_num, 0)
        if self.remain_num > 0 and self.remain_num >= wait_post_num:
            return self.remain_num - wait_post_num
        return 0

    @property
    def free_num(self):
        """ 可售库存数 """
        # return max(self.remain_num - max(self.lock_num, 0), 0)
        sku_stats = self.stat
        if sku_stats:
            self.lock_num = sku_stats.lock_num
        return max(self.remain_num - max(self.lock_num, 0), 0)

    @property
    def sale_out(self):
        if self.free_num > 0:
            return False
        if self.quantity > self.wait_post_num > 0:
            return False
        return True

    @property
    def ware_by(self):
        return self.product.ware_by

    @property
    def size_of_sku(self):
        try:
            display_num = ""
            if self.free_num > 3:
                display_num = "NO"
            else:
                display_num = self.free_num
            contrast = self.product.contrast.get_correspond_content
            sku_name = self.properties_alias or self.properties_name
            display_sku = contrast[sku_name]
            display_sku = display_sku.items()
            result_data = collections.OrderedDict()
            for p in display_sku:
                result_data[p[0]] = p[1]
            return {"result": result_data, "free_num": display_num}
        except:
            return {"result": {}, "free_num": display_num}

    @property
    def not_assign_num(self):
        return self.stat.not_assign_num

    def set_remain_num(self, remain_num):
        self.remain_num = remain_num
        self.save()

    def calc_discount_fee(self, xlmm=None):
        """ 优惠折扣 """
        if not xlmm or xlmm.agencylevel < 2:
            return 0

        try:
            discount = int(self.product.details.mama_discount)
            if discount > 100:
                discount = 100

            if discount < 0:
                discount = 0
            return float('%.2f' % ((100 - discount) / 100.0 * float(self.agent_price)))
        except:
            return 0

    @property
    def is_out_stock(self):
        quantity = max(self.quantity, 0)
        wait_post_num = max(self.wait_post_num, 0)
        return quantity - wait_post_num <= 0

    @property
    def json(self):
        model_dict = model_to_dict(self)
        model_dict.update({
            'districts': self.get_district_list(),
            'barcode': self.BARCODE,
            'name': self.name
        })
        return model_dict

    def update_quantity(self, num, full_update=False, dec_update=False):
        """ 更新规格库存 """
        if full_update:
            self.quantity = num
        elif dec_update:
            self.quantity = F('quantity') - num
        else:
            self.quantity = F('quantity') + num
        update_model_fields(self, update_fields=['quantity'])

        psku = self.__class__.objects.get(id=self.id)
        self.quantity = psku.quantity

        post_save.send_robust(sender=self.__class__, instance=self, created=False)

    def update_wait_post_num(self, num, full_update=False, dec_update=False):
        """ 更新规格待发数:full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.wait_post_num = num
        elif dec_update:
            self.wait_post_num = models.F('wait_post_num') - num
        else:
            self.wait_post_num = models.F('wait_post_num') + num
        update_model_fields(self, update_fields=['wait_post_num'])

        psku = self.__class__.objects.get(id=self.id)
        self.wait_post_num = psku.wait_post_num

        post_save.send_robust(sender=self.__class__, instance=self, created=False)

    def update_lock_num(self, num, full_update=False, dec_update=False):
        """ 更新规格待发数:full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.lock_num = num
        elif dec_update:
            self.lock_num = models.F('lock_num') - num
        else:
            self.lock_num = models.F('lock_num') + num
        update_model_fields(self, update_fields=['lock_num'])

        psku = self.__class__.objects.get(id=self.id)
        self.lock_num = psku.lock_num

    def update_reduce_num(self, num, full_update=False, dec_update=False):
        """ 更新商品库存: full_update:是否全量更新 dec_update:是否减库存 """
        if full_update:
            self.reduce_num = num
        elif dec_update:
            self.reduce_num = F('reduce_num') - num
        else:
            self.reduce_num = F('reduce_num') + num
        update_model_fields(self, update_fields=['reduce_num'])

        self.reduce_num = self.__class__.objects.get(id=self.id).reduce_num
        post_save.send(sender=self.__class__, instance=self, created=False)

    def update_quantity_by_storage_num(self, num):
        if num < 0:
            raise Exception(u'入库更新商品库存数不能小于0')

        if num > self.reduce_num:
            real_update_num = num - self.reduce_num
            real_reduct_num = 0
        else:
            real_update_num = 0
            real_reduct_num = self.reduce_num - num

        self.update_quantity(real_update_num)
        self.update_reduce_num(real_reduct_num, full_update=True)

    @property
    def is_stock_warn(self):
        """
        库存是否警告:
        1，如果当前库存小于0；
        2，同步库存（当前库存-预留库存-待发数）小于警告库位 且没有设置警告取消；
        """
        quantity = max(self.quantity, 0)
        remain_num = max(self.remain_num, 0)
        wait_post_num = max(self.wait_post_num, 0)
        return quantity - remain_num - wait_post_num <= 0

    @property
    def is_warning(self):
        """
        库存预警:
        1，如果当前能同步的库存小昨日销量；
        """
        quantity = max(self.quantity, 0)
        remain_num = max(self.remain_num, 0)
        wait_post_num = max(self.wait_post_num, 0)
        sync_num = quantity - remain_num - wait_post_num
        return self.warn_num > 0 and self.warn_num >= sync_num

    @property
    def district(self):
        from shopback.items.models.storage import ProductLocation
        location = ProductLocation.objects.filter(product_id=self.product.id, sku_id=self.id).first()
        if location:
            return location.district

    def get_district_list(self):
        from shopback.items.models.storage import ProductLocation
        locations = ProductLocation.objects.filter(product_id=self.product.id, sku_id=self.id)
        return [(l.district.parent_no, l.district.district_no) for l in locations]

    def get_districts_code(self):
        """ 商品库中区位,ret_type :c,返回组合后的字符串；o,返回[父编号]-[子编号],... """
        locations = self.get_district_list()
        sdict = {}
        for d in locations:
            dno = d[1]
            pno = d[0]
            if sdict.has_key(pno):
                sdict[pno].add(dno)
            else:
                sdict[pno] = set([dno])
        dc_list = sorted(sdict.items(), key=lambda d: d[0])
        ds = []
        for k, v in dc_list:
            ds.append('%s-[%s]' % (k, ','.join(v)))
        return ','.join(ds)

    def get_sum_sku_inferior_num(self):
        same_pro_skus = ProductSku.objects.filter(product_id=self.product_id)
        sum_inferior_num = same_pro_skus.aggregate(total_inferior=Sum("sku_inferior_num")).get("total_inferior") or 0
        return sum_inferior_num

    @property
    def collect_amount(self):
        return self.cost * self.quantity

    @property
    def color_size(self):
        color = self.product.name.split('/')[-1:][0]
        size = self.properties_name
        return '%s,%s' % (color, size)

    @staticmethod
    def get_by_outer_id(outer_id, outer_sku_id):
        product = Product.objects.get(outer_id=outer_id)
        # return ProductSku.objects.filter(outer_id=outer_sku_id, product_id=product.id).first()
        return ProductSku.objects.get(outer_id=outer_sku_id, product_id=product.id)

    def is_deposite(self):
        return self.product.outer_id.startswith(Product.DIPOSITE_CODE_PREFIX)

    def to_apimodel(self):
        from apis.v1.products import SKU as APIModel
        data = self.__dict__
        data.update({
            'type': 'size',
            'id': self.id,
            'name': self.name,
            'free_num': self.free_num,
            'is_saleout': self.free_num <= 0,
            'std_sale_price': self.std_sale_price,
            'agent_price': self.agent_price,
        })
        return APIModel(**data)


def invalid_apiproductsku_cache(sender, instance, *args, **kwargs):
    if hasattr(sender, 'API_CACHE_KEY_TPL'):
        logger.debug('invalid_apiproductsku_cache: %s' % instance.id)
        from shopback.items.models.stats import SkuStock
        cache.delete(ProductSku.API_CACHE_KEY_TPL.format(instance.id))
        cache.delete(SkuStock.API_CACHE_KEY_TPL.format(instance.id))


post_save.connect(invalid_apiproductsku_cache, sender=SaleSku, dispatch_uid='post_save_invalid_apiproductsku_cache')
'''

