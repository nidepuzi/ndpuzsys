# -*- coding:utf-8 -*-
import json
import datetime
import urlparse
from django.db import models
from django.db.models import F
from django.conf import settings
from django.db.models.signals import post_save

from tagging.fields import TagField
from common.utils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseTagModel
from core.options import get_systemoa_user, log_action, CHANGE
from .base import PayBaseModel, BaseModel

from shopback.items.models import Product, ProductSkuContrast, ContrastContent
from ..signals import signal_record_supplier_models
from shopback import paramconfig as pcfg
from shopback.items.constants import SKU_CONSTANTS_SORT_MAP as SM, PROPERTY_NAMES, PROPERTY_KEYMAP
from shopback.items.tasks_stats import task_product_upshelf_notify_favorited_customer

import logging
logger = logging.getLogger(__name__)

WASH_INSTRUCTION ='''洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。
有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。'''.replace('\n','')

class Productdetail(PayBaseModel):
    OUT_PERCENT = 0  # 未设置代理返利比例
    ZERO_PERCENT = -1
    THREE_PERCENT = 3
    FIVE_PERCENT = 5
    TEN_PERCENT = 10
    TWENTY_PERCENT = 20
    THIRTY_PERCENT = 30

    WEIGHT_CHOICE = ((i, i) for i in range(1, 101)[::-1])
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
            "per_limit_buy_num": 3,
        },
        "properties": {},
    }


class ModelProduct(BaseTagModel):

    NORMAL = 'normal'
    DELETE = 'delete'
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (DELETE, u'作废')
    )

    ON_SHELF = 'on'
    OFF_SHELF = 'off'
    WILL_SHELF = 'will' # 即将上新
    SHELF_CHOICES = (
        (ON_SHELF,u'已上架'),
        (OFF_SHELF,u'未上架')
    )

    name = models.CharField(max_length=64, db_index=True, verbose_name=u'款式名称')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    # TODO@meron　类目根据选品类目更新
    salecategory = models.ForeignKey('supplier.SaleCategory', null=True, default=None,
                                     related_name='modelproduct_set', verbose_name=u'分类')

    lowest_agent_price = models.FloatField(default=0.0, db_index=True, verbose_name=u'最低售价')
    lowest_std_sale_price = models.FloatField(default=0.0, verbose_name=u'最低原价')

    is_onsale    = models.BooleanField(default=False, db_index=True, verbose_name=u'特价/秒杀')
    is_teambuy   = models.BooleanField(default=False, db_index=True, verbose_name=u'团购')
    is_recommend = models.BooleanField(default=False, db_index=True, verbose_name=u'推荐商品')
    is_topic     = models.BooleanField(default=False, db_index=True, verbose_name=u'专题商品')
    is_flatten   = models.BooleanField(default=False, db_index=True, verbose_name=u'平铺显示')
    is_watermark = models.BooleanField(default=False, db_index=True, verbose_name=u'图片水印')

    teambuy_price = models.FloatField(default=0, verbose_name=u'团购价')
    teambuy_person_num = models.IntegerField(default=3, verbose_name=u'团购人数')

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
        return self.content_imgs.split()

    @property
    def head_images(self):
        head_imgs = []
        for product in self.products:
            head_imgs.append(product.PIC_PATH)
        return head_imgs

    @property
    def is_single_spec(self):
        """ 是否单颜色 """
        if self.id <= 0:
            return True
        products = Product.objects.filter(model_id=self.id, status=Product.NORMAL)
        if products.count() > 1:
            return False
        return True

    @property
    def item_product(self):
        if not hasattr(self, '__first_product__'):
            product = self.products.first()
            if not product:
                return None
            self.__first_product__ = product
        return self.__first_product__

    @property
    def is_sale_out(self):
        """ 是否卖光 """
        if not hasattr(self, '_is_saleout_'):
            all_sale_out = True
            for product in self.products:
                all_sale_out &= product.is_sale_out()
            self._is_saleout_ = all_sale_out
        return self._is_saleout_

    def get_web_url(self):
        return urlparse.urljoin(settings.M_SITE_URL, Product.MALL_PRODUCT_TEMPLATE_URL.format(self.id))

    @property
    def model_code(self):
        product = self.item_product
        if not product:
            return ''
        return product.outer_id[0:-1]

    # @property
    # def is_recommend(self):
    #     """ 是否推荐 """
    #     product = self.item_product
    #     if not product or not product.detail:
    #         return False
    #     return product.detail.is_recommend

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

    # @property
    # def offshelf_time(self):
    #     """ 下架时间 """
    #     product = self.item_product
    #     if not product or not product.detail:
    #         return False
    #     return product.offshelf_time

    # @property
    # def shelf_status(self):
    #     """上架状态"""
    #     product = self.item_product
    #     if not product:
    #         return 0
    #     return product.shelf_status

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

    # @property
    # def lowest_agent_price(self):
    #     """ 最低售价 """
    #     lowest_price = 0
    #     for product in self.products:
    #         if lowest_price == 0:
    #             lowest_price = product.lowest_price()
    #         else:
    #             lowest_price = min(lowest_price, product.lowest_price())
    #     return lowest_price

    # @property
    # def lowest_std_sale_price(self):
    #     """ 最低吊牌价 """
    #     product = self.item_product
    #     return product and product.std_sale_price or 0

    @property
    def properties(self):
        """ 商品属性 """
        return {}

    @property
    def attributes(self):
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

        attrs = sorted(prop_value_dict.items(), key=lambda x: PROPERTY_KEYMAP.get(x[0], 100))
        PROPERTY_NAME_DICT = dict(PROPERTY_NAMES)
        attr_dict = [{'name': PROPERTY_NAME_DICT.get(key), 'value': value} for key, value in attrs
                     if value.strip() and PROPERTY_NAME_DICT.get(key)]

        return attr_dict

    @property
    def products(self):
        return Product.objects.filter(model_id=self.id, status=pcfg.NORMAL)

    def product_simplejson(self, product):
        sku_list = []
        for sku in product.normal_skus:
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
            'sku_items': sku_list
        }

    @property
    def detail_content(self):
        return {
            'name': self.name,
            'model_code': self.model_code,
            'head_imgs': self.head_images,
            'content_imgs': self.content_images,
            'is_sale_out': self.is_sale_out,
            'is_recommend':self.is_recommend,
            'is_saleopen': self.is_saleopen,
            'is_flatten': self.is_flatten,
            'is_newsales': self.is_newsales,
            'lowest_agent_price': self.lowest_agent_price,
            'lowest_std_sale_price': self.lowest_std_sale_price,
            'category': self.category,
            'sale_time': self.sale_time,
            'offshelf_time': self.offshelf_time,
            'sale_state': self.sale_state,
            'properties':self.properties,
            'watermark_op': '',
            'item_marks': [u'包邮'],
        }

    @property
    def sku_info(self):
        product_list = []
        products = self.products
        for p in products:
            product_list.append(self.product_simplejson(p))
        return product_list

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

    @property
    def comparison(self):
        p_tables = []
        uni_set = set()
        try:
            for p in self.products:
                contrast_origin = p.contrast.contrast_detail
                uni_key = ''.join(sorted(contrast_origin.keys()))
                if uni_key not in uni_set:
                    uni_set.add(uni_key)
                    p_tables.append({'table': self.format_contrast2table(contrast_origin)})
        except ProductSkuContrast.DoesNotExist:
            logger.warn('ProductSkuContrast not exists:%s' % (p.outer_id))
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

    def update_schedule_detail_info(self, order_weight):
        """更新权重和是否推广字段"""
        update_fields = []
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            update_fields.append('order_weight')
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
            return True
        return False

    def update_lowest_price(self, lowest_agent_price, lowest_std_sale_price):
        """ 更新最低价格 """
        update_fields = []
        if self.lowest_agent_price != lowest_agent_price:
            self.lowest_agent_price = lowest_agent_price
            update_fields.append('lowest_agent_price')
        if self.lowest_std_sale_price != lowest_std_sale_price:
            self.lowest_std_sale_price = lowest_std_sale_price
            update_fields.append('lowest_std_sale_price')
        if update_fields:
            self.save(update_fields=update_fields)
            return True
        return False

    def update_extras(self, extras):
        """ 更新扩展字段 """
        if self.extras != extras:
            self.extras = extras
            self.save(update_fields=['extras'])
            return True
        return False

    def set_lowest_price(self):
        """ 设置款式最低价格 """
        prices = self.products.values('agent_price', 'std_purchase_price')
        agent_prices = [i['agent_price'] for i in prices]
        std_purchase_price = [i['std_purchase_price'] for i in prices]
        lowest_agent_price = sorted(agent_prices, reverse=False)[0]  # 递增
        lowest_std_sale_price = sorted(std_purchase_price, reverse=False)[0]  # 递增
        self.update_lowest_price(lowest_agent_price, lowest_std_sale_price)

    def set_choose_colors(self):
        """ 更新可选颜色 """
        names = self.products.values('name')
        colors = [i['name'].split('/')[-1] for i in names if '/' in i['name']]
        c = ','.join(colors)
        extras = self.extras
        extras.setdefault('properties', {})
        properties = extras.get('properties')
        if c.strip():
            properties.update({'color': c.strip()})
        self.update_extras(extras)

    def set_is_flatten(self):
        """
        is_flatten: 平铺展示
        判断： 没有ProductSku或者只有一个则is_fatten = True
        设置： 款式以及款式下的产品is_flatten字段
        """
        from shopback.items.models import ProductSku
        products = self.products()
        flatten_count = ProductSku.objects.filter(product__in=products).count()
        is_flatten = flatten_count in [0, 1]
        products.update(is_flatten=is_flatten)
        if self.is_flatten != is_flatten:
            self.is_flatten = is_flatten
            self.save(update_fields=['is_flatten'])


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


def modelproduct_update_supplier_info(sender, obj, **kwargs):
    pro = obj.item_product
    if isinstance(pro, Product):
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_select_num = F('total_select_num') + 1
            update_model_fields(supplier, update_fields=['total_select_num'])


signal_record_supplier_models.connect(modelproduct_update_supplier_info,
                                      sender=ModelProduct, dispatch_uid='post_save_modelproduct_update_supplier_info')
