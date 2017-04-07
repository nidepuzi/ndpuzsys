# -*- coding:utf8 -*-
from django.contrib import admin
from core.filters import DateFieldListFilter
from .models import DailyStat, PopularizeCost, DailyBoutiqueStat, DailySkuAmountStat, DailySkuDeliveryStat, DailySqlRecord
from django import forms

from flashsale.pay.models import ModelProduct
from core.admin import ApproxAdmin


class DailyStatForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DailyStatForm, self).__init__(*args, **kwargs)
        self.initial['total_payment'] = self.instance.get_total_payment_display()

    total_payment = forms.FloatField(label=u'日成交额', min_value=0)

    class Meta:
        model = DailyStat
        exclude = ()

    def clean_total_payment(self):
        total_payment = self.cleaned_data['total_payment']
        return int(total_payment * 100)

@admin.register(DailyStat)
class DailyStatAdmin(ApproxAdmin):
    form = DailyStatForm
    list_display = ('day_date', 'total_click_count', 'total_valid_count', 'total_visiter_num', 'total_new_visiter_num',
                    'get_total_payment_display', 'total_paycash_display', 'get_total_coin_display', 'total_budget_display',
                    'total_coupon_display', 'total_boutique_display', 'total_deposite_display',
                    'total_order_num', 'total_new_order_num', 'total_buyer_num', 'get_new_customer_num_display',
                    'get_seven_new_buyer_num', 'get_daily_rpi_display', 'get_price_per_customer_display',
                    'get_daily_roi_display')
    list_filter = (('day_date', DateFieldListFilter),)
    date_hierarchy = 'day_date'
    search_fields = ['=day_date']
    ordering = ('-day_date',)

    def total_paycash_display(self, obj):
        return '%.2f'% (obj.total_paycash / 100.0)

    total_paycash_display.allow_tags = True
    total_paycash_display.short_description = u"实付现金"

    def total_coupon_display(self, obj):
        return '%.2f' % (obj.total_coupon / 100.0)

    total_coupon_display.allow_tags = True
    total_coupon_display.short_description = u"券支付额"

    def total_budget_display(self, obj):
        return '%.2f' % (obj.total_budget / 100.0)

    total_budget_display.allow_tags = True
    total_budget_display.short_description = u"钱包余额"

    def total_boutique_display(self, obj):
        return '%.2f' % (obj.total_boutique / 100.0)

    total_boutique_display.allow_tags = True
    total_boutique_display.short_description = u"购券＆充值"

    def total_deposite_display(self, obj):
        return '%.2f' % (obj.total_deposite / 100.0)

    total_deposite_display.allow_tags = True
    total_deposite_display.short_description = u"支付押金"

@admin.register(PopularizeCost)
class PopularizeCostAdmin(admin.ModelAdmin):
    list_display = ('date',
                    'carrylog_order', 'carrylog_click', 'carrylog_thousand',
                    'carrylog_agency', 'carrylog_recruit','carrylog_order_buy',
                    'carrylog_cash_out', 'carrylog_deposit', 'carrylog_refund_return',
                    'carrylog_red_packet',
                    'total_incarry',
                    'total_outcarry')
    list_filter = (('date', DateFieldListFilter),)
    search_fields = ['=date']
    ordering = ('-date',)


@admin.register(DailyBoutiqueStat)
class DailyBoutiqueStatAdmin(admin.ModelAdmin):
    list_display = ('model_id', 'product_link',
                    'stat_date', 'model_stock_num', 'model_sale_num','model_refund_num',
                    'coupon_sale_num', 'coupon_use_num', 'coupon_refund_num',)
    list_filter = (('stat_date', DateFieldListFilter),)
    search_fields = ['=model_id']
    ordering = ('-stat_date',)

    def product_link(self, obj):
        mp = ModelProduct.objects.filter(id=obj.model_id).first()
        return '<a href="/admin/pay/modelproduct/?q=%s" style="width:100px;">%s</a>'%(mp.id, mp.name)

    product_link.allow_tags = True
    product_link.short_description = u"商品名称"


@admin.register(DailySkuAmountStat)
class DailySkuAmountStatAdmin(admin.ModelAdmin):
    list_display = ('sku_id', 'model_id', 'stat_date',
                    'total_amount', 'total_cost', 'direct_payment', 'coin_payment',
                    'coupon_amount', 'coupon_payment', 'exchg_amount')
    list_filter = (('stat_date', DateFieldListFilter),)
    search_fields = ['=sku_id','=model_id']
    ordering = ('-stat_date',)


@admin.register(DailySkuDeliveryStat)
class DailySkuDeliveryStatAdmin(admin.ModelAdmin):
    list_display = ('sku_id', 'model_id', 'stat_date',
                     'days', 'post_num','wait_num')
    list_filter = (('stat_date', DateFieldListFilter),'days')
    search_fields = ['=sku_id','=model_id']
    ordering = ('-stat_date',)

@admin.register(DailySqlRecord)
class DailySqlRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'query_data', 'status')
    list_filter = ('status', )
    search_fields = ['=id', 'query_data']
    ordering = ('-modified',)