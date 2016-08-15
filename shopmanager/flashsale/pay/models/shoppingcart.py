# -*- coding:utf-8 -*-
import uuid
import datetime
import urlparse
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save
from django.conf import settings
from django.db import transaction

from .base import PayBaseModel, BaseModel
from shopback.items.models import Product, ProductSku


class ShoppingCart(BaseModel):
    """ 购物车 """

    NORMAL = 0
    CANCEL = 1

    STATUS_CHOICE = ((NORMAL, u'正常'),
                     (CANCEL, u'关闭'))

    id = models.AutoField(primary_key=True)
    buyer_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'买家ID')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')

    item_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'单价')
    std_sale_price = models.FloatField(default=0.0, verbose_name=u'标准售价')

    sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')

    sku_name = models.CharField(max_length=256, blank=True, verbose_name=u'规格名称')

    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    remain_time = models.DateTimeField(null=True, blank=True, verbose_name=u'保留时间')

    status = models.IntegerField(choices=STATUS_CHOICE, default=NORMAL,
                                 db_index=True, blank=True, verbose_name=u'订单状态')

    class Meta:
        db_table = 'flashsale_shoppingcart'
        index_together = [('buyer_id', 'item_id', 'sku_id')]
        app_label = 'pay'
        verbose_name = u'特卖/购物车'
        verbose_name_plural = u'特卖/购物车'

    def __unicode__(self):
        return '%s' % (self.id)

    @property
    def product(self):
        if not hasattr(self, '_product_'):
            self._product_ = Product.objects.filter(id=self.item_id).first()
        return self._product_

    @transaction.atomic
    def close_cart(self, release_locknum=True):
        """ 关闭购物车 """
        try:
            ShoppingCart.objects.get(id=self.id, status=ShoppingCart.NORMAL)
        except ShoppingCart.DoesNotExist:
            return

        self.status = self.CANCEL
        self.save()
        if release_locknum:
            sku = get_object_or_404(ProductSku, pk=self.sku_id)
            Product.objects.releaseLockQuantity(sku, self.num)

    # def std_sale_price(self):
    #     sku = ProductSku.objects.get(id=self.sku_id)
    #     return sku.std_sale_price

    def is_deposite(self):
        product = Product.objects.get(id=self.item_id)
        return product.outer_id.startswith('RMB')

    def is_good_enough(self):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return (product_sku.product.shelf_status == Product.UP_SHELF
                and product_sku.real_remainnum >= self.num)

    def calc_discount_fee(self, xlmm=None):
        product_sku = ProductSku.objects.get(id=self.sku_id)
        return product_sku.calc_discount_fee(xlmm)

    def is_repayable(self):
        """ can repay able """
        pro_sku = ProductSku.objects.filter(id=self.sku_id).first()
        if pro_sku and pro_sku.product.is_onshelf():
            return pro_sku.sale_out
        return False

    def get_item_weburl(self):
        product = self.product
        return urlparse.urljoin(settings.M_SITE_URL,
                                Product.MALL_PRODUCT_TEMPLATE_URL.format(product.model_id))


from shopback import signals


def off_the_shelf_func(sender, product_list, *args, **kwargs):
    from core.options import log_action, CHANGE, get_systemoa_user
    from .trade import SaleTrade
    sysoa_user = get_systemoa_user()
    for pro_bean in product_list:
        all_cart = ShoppingCart.objects.filter(item_id=pro_bean.id, status=ShoppingCart.NORMAL)
        for cart in all_cart:
            cart.close_cart()
            log_action(sysoa_user.id, cart, CHANGE, u'下架后更新')
        all_trade = SaleTrade.objects.filter(sale_orders__item_id=pro_bean.id, status=SaleTrade.WAIT_BUYER_PAY)
        for trade in all_trade:
            try:
                trade.close_trade()
                log_action(sysoa_user.id, trade, CHANGE, u'系统更新待付款状态到交易关闭')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)


signals.signal_product_downshelf.connect(off_the_shelf_func, sender=Product)


def shoppingcart_update_productskustats_shoppingcart_num(sender, instance, *args, **kwargs):
    from flashsale.pay.tasks_stats import task_shoppingcart_update_productskustats_shoppingcart_num
    task_shoppingcart_update_productskustats_shoppingcart_num.delay(instance.sku_id)


post_save.connect(shoppingcart_update_productskustats_shoppingcart_num, sender=ShoppingCart,
                  dispatch_uid='post_save_shoppingcart_update_productskustats_shoppingcart_num')
