# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import time
import hashlib
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.signals import pre_save, post_save

from core.models import BaseTagModel, BaseModel
from core.fields import JSONCharMyField
from core.utils import update_model_fields
from pms.supplier.constants import STOCKING_MODE_CHOICES

def set_saleproduct_default_extras():
    return {
        # "is_boutique": False, #　是否精品汇商品
        # "product_type": "0",  # 商品类型
        "consoles": {
            "is_batch_mgt": False,  # 启动批次管理
            "is_expire_mgt": False,  # 启动保质期管理
            "is_vendor_mgt": False,  # 启动多供应商管理(支持同SKU多供应商供货)
            "shelf_life_days": 0,  # 保质期(天数)
        },
    }

class SaleProduct(BaseTagModel):
    MANUAL = 'manual'
    MANUALINPUT = 'manualinput'
    TAOBAO = 'taobao'
    TMALL = 'tianmao'
    ZHEBABAI = 'zhe800'
    XIAOHER = 'xiaoher'
    VIP = 'vip'
    JHS = 'jhs'
    BBW = 'bbw'

    PLATFORM_CHOICE = (
        (MANUAL, u'手工录入'),
        (MANUALINPUT, u'线下店'),
        (TAOBAO, u'淘宝'),
        (TMALL, u'天猫'),
        (ZHEBABAI, u'折800'),
        (XIAOHER, u'小荷特卖'),
        (VIP, u'唯品会'),
        (JHS, u'聚划算'),
        (BBW, u'贝贝网'),
    )

    WAIT = 'wait'
    SELECTED = 'selected'
    PURCHASE = 'purchase'
    PASSED = 'passed'
    SCHEDULE = 'scheduling'
    IGNORED = 'ignored'
    REJECTED = 'rejected'
    STATUS_CHOICES = (
        (WAIT, u'待选'),
        (SELECTED, u'入围'),
        (PURCHASE, u'取样'),
        (PASSED, u'通过'),
        (SCHEDULE, u'排期'),
        (REJECTED, u'淘汰'),
        (IGNORED, u'忽略'),
    )

    SOURCE_SELF = 0  # 自存商品
    SOURCE_TTP = 1  # 三方仓商品
    SOURCE_BONDED = 2  # 保税仓商品
    SOURCE_OUTSIDE = 3  # 关外商品（直邮）
    SOURCE_CHOICES = (
        (SOURCE_SELF, u'自储商品'),
        (SOURCE_TTP, u'第三方仓'),
        (SOURCE_BONDED, u'保税仓'),
        (SOURCE_OUTSIDE, u'关外直邮'),
    )

    outer_id = models.CharField(max_length=64, blank=True,
                                # default=lambda: 'OO%s' % int(time.time() * 10 ** 3),
                                verbose_name=u'外部ID')
    title = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'标题')
    price = models.FloatField(default=0, verbose_name=u'价格')
    pic_url = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    product_link = models.CharField(max_length=512, blank=True, verbose_name=u'商品外部链接')

    sale_supplier = models.ForeignKey('supplier.SaleSupplier', null=True, related_name='supplier_products',
                                      verbose_name=u'供货商')
    sale_category = models.ForeignKey('supplier.SaleCategory', null=True, related_name='category_products',
                                      verbose_name=u'类别')
    platform = models.CharField(max_length=16, blank=True, default=MANUAL,
                                choices=PLATFORM_CHOICE, verbose_name=u'来自平台')

    hot_value = models.IntegerField(default=0, verbose_name=u'热度值')
    stocking_mode = models.IntegerField(default=0, choices=STOCKING_MODE_CHOICES, db_index=True, verbose_name=u'存货模式')
    voting = models.BooleanField(default=False, verbose_name=u'参与投票')
    sale_price = models.FloatField(default=0, verbose_name=u'采购价')
    on_sale_price = models.FloatField(default=0, verbose_name=u'售价')
    std_sale_price = models.FloatField(default=0, verbose_name=u'吊牌价')
    product_material = models.CharField(max_length=16, blank=True, verbose_name=u'商品材质')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    is_changed = models.BooleanField(default=False, db_index=True, verbose_name=u'排期改动')

    status = models.CharField(max_length=16, blank=True,
                              choices=STATUS_CHOICES, default=WAIT, verbose_name=u'状态')

    contactor = models.ForeignKey('auth.User', null=True, related_name='sale_products', verbose_name=u'接洽人')
    librarian = models.CharField(max_length=32, blank=True, db_index=True, null=True, verbose_name=u'资料员')
    buyer = models.CharField(max_length=32, blank=True, null=True, db_index=True, verbose_name=u'采购员')

    sale_time = models.DateTimeField(null=True, blank=True, verbose_name=u'上架日期')
    reserve_time = models.DateTimeField(null=True, blank=True, verbose_name=u'预留时间')
    supplier_sku = models.CharField(max_length=64, blank=True, verbose_name=u'供应商货号')
    orderlist_show_memo = models.BooleanField(default=False, verbose_name=u'订货详情显示备注')
    source_type = models.IntegerField(default=SOURCE_SELF, db_index=True, choices=SOURCE_CHOICES, verbose_name=u'商品货源')
    # TODO@MENTION 之前的比如第三方仓货源信息需要刷新数据, 并且需要更新到modelproduct记录上
    sku_extras = JSONCharMyField(max_length=10240, default=[], verbose_name=u"sku信息")

    extras = JSONCharMyField(max_length=512, default={}, verbose_name=u"附加信息")

    class Meta:
        db_table = 'supplychain_supply_product'
        unique_together = [("outer_id", "platform")]
        index_together = [('status', 'sale_time', 'sale_category')]
        app_label = 'supplier'
        verbose_name = u'特卖/选品'
        verbose_name_plural = u'特卖/选品列表'
        permissions = [
            ("sale_product_mgr", u"特卖商品管理"),
            ("schedule_manage", u"排期管理"),
            ("delete_sale_product", u"删除选品")
        ]

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    @property
    def item_products(self):
        if not hasattr(self, '_item_products_'):
            from shopback.items.models import Product

            self._item_products_ = Product.objects.filter(sale_product=self.id, status=Product.NORMAL)
        return self._item_products_

    @property
    def product_id(self):
        from shopback.items.models import Product
        p = Product.objects.filter(sale_product=self.id).first()
        if p:
            return p.id
        spr = self.saleproductrelation_set.first()
        if spr:
            return spr.id
        return None

    def get_item_products(self):
        """获取相关所有商品"""
        from shopback.items.models import Product
        product_ids = list(self.saleproductrelation_set.values_list('product_id', flat=True))
        p = Product.objects.filter(sale_product=self.id).first()
        if p:
            product_ids = [p.id] + product_ids
        return Product.objects.filter(id__in=product_ids)

    @property
    def model_product(self):
        """ 对应特卖款式 """
        if not hasattr(self, '_pay_model_product_'):
            from flashsale.pay.models import ModelProduct
            self._pay_model_product_ = ModelProduct.objects.filter(saleproduct_id=self.id,
                                                                   status=ModelProduct.NORMAL).first()
        return self._pay_model_product_

    @property
    def is_batch_mgt_on(self):
        return self.extras.get('consoles', {}).get('is_batch_mgt') or 0

    @property
    def is_expire_mgt_on(self):
        return self.extras.get('consoles', {}).get('is_expire_mgt') or 0

    @property
    def is_vendor_mgt_on(self):
        return self.extras.get('consoles', {}).get('is_vendor_mgt') or 0

    @property
    def shelf_life_days(self):
        return self.extras.get('consoles', {}).get('shelf_life_days') or 0

    def sale_product_figures(self):
        """ 选品排期数据 """
        if not hasattr(self, '_product_figures_'):
            from statistics.models import ModelStats

            self._product_figures_ = ModelStats.objects.filter(sale_product=self.id).first()
        return self._product_figures_

    def total_sale_product_figures(self):
        """ 选品总销售额退货率计算 """
        if not hasattr(self, '_product_total_figures_'):
            from statistics.models import ModelStats

            stats = ModelStats.objects.filter(sale_product=self.id)
            agg = stats.aggregate(s_p=Sum('pay_num'), s_rg=Sum('return_good_num'), s_pm=Sum('payment'))
            p_n = agg['s_p']
            rg = agg['s_rg']
            payment = agg['s_pm']
            rat = round(float(rg) / p_n, 4) if p_n > 0 else 0
            self._product_total_figures_ = {'total_pay_num': p_n, 'total_rg_rate': rat, 'total_payment': payment}
        return self._product_total_figures_

    def set_special_fields_by_skuextras(self):
        """
        根据sku_extras字段　价格信息设置　instance 一些价格信息 agent_price std_sale_price cost
        # agent_price std_sale_price cost
        # 计算最小值
        """
        if not (isinstance(self.sku_extras, list) and self.sku_extras):
            return
        agent_prices = []
        std_sale_prices = []
        costs = []
        for sku in self.sku_extras:
            agent_prices.append(sku['agent_price'])
            std_sale_prices .append(sku['std_sale_price'])
            costs.append(sku['cost'])
        update_fields = []
        if self.price != min(agent_prices):
            self.price = min(agent_prices)
            self.on_sale_price = min(agent_prices)
            update_fields.extend(['price', 'on_sale_price'])
        if self.std_sale_price != min(std_sale_prices):
            self.std_sale_price = min(std_sale_prices)
            update_fields.append('std_sale_price')
        if self.sale_price != min(costs):
            self.sale_price = min(costs)
            update_fields.append('sale_price')
        if update_fields:
            update_fields.append('modified')
            self.save(update_fields=update_fields)
        return

    @property
    def is_inschedule(self):
        from pms.supplier.models import SaleProductManageDetail
        return SaleProductManageDetail.objects.filter(sale_product_id=self.id).exists()

    def update_sku_extras(self):
        """ 更新数据库　sku 信息　到　sku_extras 字段"""
        try:
            md = self.model_product
        except Exception as e:
            print self.id, e
            return
        sku_list = []
        if not md:
            return
        for pro in md.products:
            for psku in pro.normal_skus:
                sku_list.append({'color': pro.name,
                                 'agent_price': psku.agent_price,
                                 'remain_num': psku.remain_num,
                                 'std_sale_price': psku.std_sale_price,
                                 'cost': psku.cost,
                                 'properties_alias': psku.properties_alias,
                                 'properties_name': psku.properties_name})
        self.sku_extras = sku_list
        self.save(update_fields=['sku_extras', 'modified'])

    @property
    def sku_extras_info(self):
        """ 更新数据库　sku 信息　到　sku_extras 字段"""
        try:
            md = self.model_product
        except Exception as e:
            print self.id, e
            return
        sku_list = []
        if not md:
            return self.sku_extras
        for pro in md.products:
            for psku in pro.normal_skus:
                sku_list.append({'color': pro.name.find('/') > -1 and pro.name.split('/')[-1] or pro.name,
                                 'pic_path': pro.pic_path,
                                 'agent_price': psku.agent_price,
                                 'remain_num': psku.remain_num,
                                 'std_sale_price': psku.std_sale_price,
                                 'cost': psku.cost,
                                 'elite_score': pro.elite_score,
                                 'supplier_skucode': psku.supplier_skucode,
                                 'properties_alias': psku.properties_alias,
                                 'properties_name': psku.properties_name})
        return sku_list


    def get_product_type(self):
        if not self.extras:
            return 0
        return self.extras.get('product_type') or 0

    def get_boutique_value(self):
        return bool(self.extras and self.extras.get('is_boutique') or 0)

    def gen_outer_id(self):
        if self.product_link:
            self.outer_id = hashlib.md5(self.product_link).hexdigest()
        else:
            self.outer_id = 'OO%d' % time.time()
        outer_base_num = 0
        outer_base = self.outer_id
        while SaleProduct.objects.filter(outer_id=self.outer_id, platform=self.platform).exists():
            if '-' in self.outer_id:
                outer_base = self.outer_id.split('-')[0]
                try:
                    outer_base_num = int(self.outer_id.split('-')[1])
                except:
                    outer_base_num = 0
            self.outer_id = outer_base + '-' + str(outer_base_num + 1)

    @staticmethod
    def get_by_product(product):
        spids = list(SaleProductRelation.objects.filter(product_id=product.id).values_list('sale_product_id', flat=True))
        spids = spids + [product.sale_product]
        return SaleProduct.objects.filter(id__in=spids).exclude(status__in=[SaleProduct.REJECTED, SaleProduct.IGNORED])

    @staticmethod
    @transaction.atomic
    def create(product, title, supplier_id, supplier_sku, product_link, memo, creater, platform=MANUAL, extras=None):
        if supplier_id in list(SaleProduct.get_by_product(product).values_list("sale_supplier_id", flat=True)):
            raise Exception(u'此商品已向该供应商订货，应该进行编辑而非新增')
        sp = SaleProduct(
            title=title,
            sale_supplier_id=supplier_id,
            product_link=product_link,
            supplier_sku=supplier_sku,
            memo=memo,
            librarian=creater.username,
            platform=platform,
            price=product.std_purchase_price,
        )
        if extras is None:
            sp.extras = set_saleproduct_default_extras()
        else:
            sp.extras = extras
        sp.gen_outer_id()
        sp.save()
        sp.sale_category = product.category.get_sale_category()
        sp.save()
        SaleProductRelation.create(sale_product=sp, product=product)
        return sp

    def delete(self):
        self.status = SaleProduct.REJECTED
        self.save()

def change_saleprodut_by_pre_save(sender, instance, raw, *args, **kwargs):
    try:
        product = SaleProduct.objects.get(id=instance.id)
        # 如果上架时间修改，则重置is_verify
        if (product.status == SaleProduct.SCHEDULE and
                (product.sale_time != instance.sale_time or product.status != instance.status)):
            instance.is_changed = True
            update_model_fields(instance, update_fields=['is_changed'])
    except SaleProduct.DoesNotExist:
        pass


pre_save.connect(change_saleprodut_by_pre_save, sender=SaleProduct,
                 dispatch_uid=u'pre_save_change_saleprodut_by_pre_save')


class HotProduct(models.Model):
    SELECTED = 0
    PASSED = 1
    MANUFACTURE = 2
    SALE = 3
    CLOSE = 4
    CANCEL = 5
    STATUS_CHOICES = ((SELECTED, u'入围'),
                      (PASSED, u'待生产'),
                      (MANUFACTURE, u'生产'),
                      (SALE, u'开卖'),
                      (CLOSE, u'结束'),  # 全状态结束
                      (CANCEL, u'作废'))  # 中断

    name = models.CharField(max_length=128, verbose_name=u'名称')
    proid = models.IntegerField(default=0, db_index=True, verbose_name=u'产品ID')
    pic_pth = models.CharField(max_length=512, verbose_name=u'图片链接')
    site_url = models.CharField(max_length=512, verbose_name=u'站点链接')
    price = models.FloatField(default=0.0, verbose_name=u'预售价格')
    hot_value = models.IntegerField(default=0, verbose_name=u'热度值')
    voting = models.BooleanField(default=False, verbose_name=u'参与投票')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name=u'爆款状态')
    contactor = models.BigIntegerField(null=True, db_index=True, verbose_name=u'接洽人')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_hot_product'
        app_label = 'supplier'
        verbose_name = u'特卖/爆款表'
        verbose_name_plural = u'特卖/爆款列表'

    def __unicode__(self):
        return self.name


class CategoryPreference(BaseModel):
    category = models.ForeignKey('supplier.SaleCategory', related_name='category_pool_preference', verbose_name=u'类别')
    preferences = JSONCharMyField(max_length=1024, default=[], verbose_name=u"参数选项")
    is_default = models.BooleanField(default=False, verbose_name=u'设为默认')

    class Meta:
        db_table = 'supplychain_category_preference_conf'
        app_label = 'supplier'
        verbose_name = u'特卖/产品类别参数配置表'
        verbose_name_plural = u'特卖/产品类别参数配置列表'

    def __unicode__(self):
        return '<%s-%s-%s>' % (self.id, self.category.__unicode__(), self.category.id)

    def get_preferences(self):
        return list(set(self.preferences + [1,2]))


class PreferencePool(BaseModel):
    name = models.CharField(max_length=64, verbose_name=u'参数名称')
    unit = models.CharField(max_length=32, blank=True, verbose_name=u'单位')
    is_sku = models.BooleanField(default=False, verbose_name=u'是否是sku属性')
    categorys = JSONCharMyField(max_length=512, default=[], verbose_name=u'包含类别', help_text=u'哪些类别(保存id列表)包含本参数')
    preference_value = JSONCharMyField(max_length=10240, default=[], verbose_name=u"参数值")

    class Meta:
        db_table = 'supplychain_preference_pool'
        app_label = 'supplier'
        verbose_name = u'特卖/产品资料参数表'
        verbose_name_plural = u'特卖/产品资料参数列表'

    def __unicode__(self):
        return '<%s-%s>' % (self.id, self.name)


class SaleProductRelation(BaseModel):
    sale_product = models.ForeignKey(SaleProduct)
    product_id = models.IntegerField(verbose_name=u'商品id')

    class Meta:
        unique_together = [("sale_product", "product_id")]
        app_label = 'supplier'
        verbose_name = u'商品选品关系'
        verbose_name_plural = u'商品选品关联列表'

    @staticmethod
    def create(sale_product, product):
        """
            建立选品与商品的关联。如果商品未设定主选品，则将此定为主选品。
        :param sale_product:
        :param product:
        :return:
        """
        SaleProductRelation(sale_product=sale_product, product_id=product.id).save()
        if not product.sale_product:
            product.sale_product = sale_product.id
            product.save()
        return

    @staticmethod
    def get_products(sale_product_ids):
        from shopback.items.models import Product
        product_ids = list(SaleProductRelation.objects.filter(sale_product_id__in=sale_product_ids).values_list('product_id', flat=True))
        return Product.objects.filter(Q(sale_product__in=sale_product_ids) or Q(id__in=product_ids))