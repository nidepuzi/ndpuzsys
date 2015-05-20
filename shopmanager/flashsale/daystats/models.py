__author__ = 'yann'
# -*- coding:utf-8 -*-
from django.db import models
from shopapp.weixin.models import WXOrder
from flashsale.xiaolumm.models import Clicks, XiaoluMama, AgencyLevel
import datetime


class DailyStat(models.Model):
    
    total_click_count = models.IntegerField(default=0, verbose_name=u'日点击数')
    total_valid_count = models.IntegerField(default=0, verbose_name=u'日有效点击数')
    total_visiter_num = models.IntegerField(default=0, verbose_name=u'日访客数')
    
    total_payment     = models.IntegerField(default=0, verbose_name=u'日成交额')
    total_order_num   = models.IntegerField(default=0, verbose_name=u'日订单数')
    
    total_buyer_num   = models.IntegerField(default=0, verbose_name=u'日购买人数')
    total_old_buyer_num   = models.IntegerField(default=0, verbose_name=u'日老用户成交人数')
    seven_buyer_num   = models.IntegerField(default=0, verbose_name=u'七日老用户成交人数')
    
#     page_view_count   = models.IntegerField(verbose_name=u'商品浏览量数')
#     shelf_view_count   = models.IntegerField(verbose_name=u'首页浏览量数')
    
    day_date = models.DateField(verbose_name=u'统计日期')
    
    class Meta:
        db_table = 'flashsale_dailystat'
        app_label = 'xiaolumm'
        verbose_name = u'每日统计'
        verbose_name_plural = u'每日统计列表'
    
    @property
    def total_payment_cash(self):

        if not self.total_payment:
            return 0
        return self.total_payment 
    
    def get_total_payment_display(self):
        return self.total_payment_cash / 100.0

    get_total_payment_display.allow_tags = True
    get_total_payment_display.short_description = u"日成交额"
    
    @property
    def price_per_customer(self):
        if not self.total_buyer_num:
            return 0
        return round(self.total_payment / float(self.total_buyer_num),2) 

    def get_price_per_customer_display(self):
        return self.price_per_customer / 100.0

    get_price_per_customer_display.allow_tags = True
    get_price_per_customer_display.short_description = u"客单价"
    
    def get_new_customer_num_display(self):
        return self.total_buyer_num - self.total_old_buyer_num

    get_new_customer_num_display.allow_tags = True
    get_new_customer_num_display.short_description = u"新购买用户数"
    
    @property
    def daily_roi(self):
        if not self.total_visiter_num:
            return 0
        return round(self.total_buyer_num / float(self.total_visiter_num),2)

    def get_daily_roi_display(self):
        return self.daily_roi

    get_daily_roi_display.allow_tags = True
    get_daily_roi_display.short_description = u"日转化率"
    
    @property
    def daily_rpi(self):
        if not self.total_old_buyer_num:
            return 0
        return round(self.total_old_buyer_num / float(self.total_buyer_num),2)

    def get_daily_rpi_display(self):
        return self.daily_rpi

    get_daily_rpi_display.allow_tags = True
    get_daily_rpi_display.short_description = u"重复购买率"
    
    
    
    
    
