# -*- coding:utf-8 -*-
import time
import json
import datetime
from django.db import models
from django.db.models import Q, Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from bitfield import BitField
from core.fields import BigIntegerAutoField, BigIntegerForeignKey

from shopback.users.models import User
from core.options import log_action, CHANGE
from shopback.orders.models import Trade, Order, STEP_TRADE_STATUS
from shopback.trades.managers import MergeTradeManager
from shopback.items.models import Item, Product, ProductSku
from shopback.logistics.models import Logistics, LogisticsCompany
from shopback.refunds.models import Refund, REFUND_STATUS
from shopback import paramconfig as pcfg
from shopback import signals
from common.utils import (parse_datetime,
                          get_yesterday_interval_time,
                          update_model_fields)
from flashsale.pay.models import SaleTrade
from flashsale import pay
# from flashsale import pay
import logging
from shopback.warehouse import WARE_SH, WARE_CHOICES

logger = logging.getLogger('django.request')

SYS_TRADE_STATUS = (
    (pcfg.WAIT_AUDIT_STATUS, u'问题单'),
    (pcfg.WAIT_PREPARE_SEND_STATUS, u'待发货准备'),
    (pcfg.WAIT_CHECK_BARCODE_STATUS, u'待扫描验货'),
    (pcfg.WAIT_SCAN_WEIGHT_STATUS, u'待扫描称重'),
    (pcfg.FINISHED_STATUS, u'已完成'),
    (pcfg.INVALID_STATUS, u'已作废'),
    (pcfg.ON_THE_FLY_STATUS, u'飞行模式'),
    (pcfg.REGULAR_REMAIN_STATUS, u'定时提醒'),
)

SYS_ORDER_STATUS = (
    (pcfg.IN_EFFECT, u'有效'),
    (pcfg.INVALID_STATUS, u'无效'),
)

TAOBAO_TRADE_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY, u'订单创建'),
    (pcfg.WAIT_BUYER_PAY, u'待付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS, u'待发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS, u'待确认收货'),
    (pcfg.TRADE_BUYER_SIGNED, u'货到付款签收'),
    (pcfg.TRADE_FINISHED, u'交易成功'),
    (pcfg.TRADE_CLOSED, u'退款交易关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO, u'未付款关闭'),
)

TAOBAO_ORDER_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY, u'没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY, u'等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS, u'等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS, u'等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED, u'已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED, u'交易成功'),
    (pcfg.TRADE_CLOSED, u'退款成功，交易关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO, u'付款以前关闭交易'),
    (pcfg.WAIT_CONFIRM_WAIT_SEND_GOODS, u"付款信息待确认，待发货"),
    (pcfg.WAIT_CONFIRM_SEND_GOODS, u"付款信息待确认，已发货"),
    (pcfg.WAIT_CONFIRM_GOODS_CONFIRM, u"付款信息待确认，已收货"),
    (pcfg.CONFIRM_WAIT_SEND_GOODS, u"付款信息已确认，待发货"),
    (pcfg.CONFIRM_SEND_GOODS, u"付款信息已确认，已发货"),
    (pcfg.TRADE_REFUNDED, u"已退款"),
    (pcfg.TRADE_REFUNDING, u"退款中"),
)

TRADE_TYPE = (
    (pcfg.TAOBAO_TYPE, u'淘宝&商城'),
    (pcfg.FENXIAO_TYPE, u'淘宝分销'),
    (pcfg.SALE_TYPE, u'小鹿特卖'),
    (pcfg.JD_TYPE, u'京东商城'),
    (pcfg.YHD_TYPE, u'一号店'),
    (pcfg.DD_TYPE, u'当当商城'),
    (pcfg.SN_TYPE, u'苏宁易购'),
    (pcfg.WX_TYPE, u'微信小店'),
    (pcfg.AMZ_TYPE, u'亚马逊'),
    (pcfg.DIRECT_TYPE, u'内售'),
    (pcfg.REISSUE_TYPE, u'补发'),
    (pcfg.EXCHANGE_TYPE, u'退换货'),
)

COD_STATUS = (
    (pcfg.COD_NEW_CREATED, u'初始状态'),
    (pcfg.COD_ACCEPTED_BY_COMPANY, u'接单成功'),
    (pcfg.COD_REJECTED_BY_COMPANY, u'接单失败'),
    (pcfg.COD_RECIEVE_TIMEOUT, u'接单超时'),
    (pcfg.COD_TAKEN_IN_SUCCESS, u'揽收成功'),
    (pcfg.COD_TAKEN_IN_FAILED, u'揽收失败'),
    (pcfg.COD_TAKEN_TIMEOUT, u'揽收超时'),
    (pcfg.COD_SIGN_IN, u'签收成功'),
    (pcfg.COD_REJECTED_BY_OTHER_SIDE, u'签收失败'),
    (pcfg.COD_WAITING_TO_BE_SENT, u'订单等待发送给物流公司'),
    (pcfg.COD_CANCELED, u'用户取消物流订单'),
)

SHIPPING_TYPE_CHOICE = (
    (pcfg.EXPRESS_SHIPPING_TYPE, u'快递'),
    (pcfg.POST_SHIPPING_TYPE, u'平邮'),
    (pcfg.EMS_SHIPPING_TYPE, u'EMS'),
    (pcfg.EXTRACT_SHIPPING_TYPE, u'无需物流'),
)

PRIORITY_TYPE = (
    (pcfg.PRIORITY_HIG, u'高'),
    (pcfg.PRIORITY_MID, u'中'),
    (pcfg.PRIORITY_LOW, u'低'),
)

GIFT_TYPE = (
    (pcfg.REAL_ORDER_GIT_TYPE, u'实付'),
    (pcfg.CS_PERMI_GIT_TYPE, u'赠送'),
    (pcfg.OVER_PAYMENT_GIT_TYPE, u'满就送'),
    (pcfg.COMBOSE_SPLIT_GIT_TYPE, u'拆分'),
    (pcfg.RETURN_GOODS_GIT_TYPE, u'退货'),
    (pcfg.CHANGE_GOODS_GIT_TYPE, u'换货'),
    (pcfg.ITEM_GIFT_TYPE, u'买就送'),
)


class \
        MergeTrade(models.Model):
    TAOBAO_TYPE = pcfg.TAOBAO_TYPE
    FENXIAO_TYPE = pcfg.FENXIAO_TYPE
    SALE_TYPE = pcfg.SALE_TYPE
    JD_TYPE = pcfg.JD_TYPE
    YHD_TYPE = pcfg.YHD_TYPE
    DD_TYPE = pcfg.DD_TYPE
    SN_TYPE = pcfg.SN_TYPE
    WX_TYPE = pcfg.WX_TYPE
    AMZ_TYPE = pcfg.AMZ_TYPE
    DIRECT_TYPE = pcfg.DIRECT_TYPE
    REISSUE_TYPE = pcfg.REISSUE_TYPE
    EXCHANGE_TYPE = pcfg.EXCHANGE_TYPE

    EMPTY_STATUS = pcfg.EMPTY_STATUS
    WAIT_AUDIT_STATUS = pcfg.WAIT_AUDIT_STATUS
    WAIT_PREPARE_SEND_STATUS = pcfg.WAIT_PREPARE_SEND_STATUS
    WAIT_CHECK_BARCODE_STATUS = pcfg.WAIT_CHECK_BARCODE_STATUS
    WAIT_SCAN_WEIGHT_STATUS = pcfg.WAIT_SCAN_WEIGHT_STATUS
    FINISHED_STATUS = pcfg.FINISHED_STATUS
    INVALID_STATUS = pcfg.INVALID_STATUS
    ON_THE_FLY_STATUS = pcfg.ON_THE_FLY_STATUS
    REGULAR_REMAIN_STATUS = pcfg.REGULAR_REMAIN_STATUS

    TRADE_NO_CREATE_PAY = pcfg.TRADE_NO_CREATE_PAY
    WAIT_SELLER_SEND_GOODS = pcfg.WAIT_SELLER_SEND_GOODS
    WAIT_BUYER_CONFIRM_GOODS = pcfg.WAIT_BUYER_CONFIRM_GOODS
    TRADE_BUYER_SIGNED = pcfg.TRADE_BUYER_SIGNED
    TRADE_FINISHED = pcfg.TRADE_FINISHED
    TRADE_CLOSED = pcfg.TRADE_CLOSED
    TRADE_CLOSED_BY_TAOBAO = pcfg.TRADE_CLOSED_BY_TAOBAO

    TRADE_REFUNDED = pcfg.TRADE_REFUNDED
    TRADE_REFUNDING = pcfg.TRADE_REFUNDING

    WAIT_WEIGHT_STATUS = pcfg.WAIT_WEIGHT_STATUS
    SYS_TRADE_STATUS = SYS_TRADE_STATUS
    TAOBAO_TRADE_STATUS = TAOBAO_TRADE_STATUS
    TRADE_TYPE = TRADE_TYPE
    COD_STATUS = COD_STATUS
    SHIPPING_TYPE_CHOICE = SHIPPING_TYPE_CHOICE
    PRIORITY_TYPE = PRIORITY_TYPE

    WARE_NONE = 0
    WARE_SH = 1
    WARE_GZ = 2
    WARE_CHOICES = ((WARE_NONE, u'未选仓'),
                    (WARE_SH, u'上海仓'),
                    (WARE_GZ, u'广州仓'))

    id = BigIntegerAutoField(primary_key=True, verbose_name=u'订单ID')
    tid = models.CharField(max_length=32,
                           default=lambda: 'DD%d' % int(time.time() * 10 ** 5),
                           verbose_name=u'原单ID')
    user = models.ForeignKey(User, related_name='merge_trades', verbose_name=u'所属店铺')
    buyer_nick = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'买家昵称')

    type = models.CharField(max_length=32, choices=TRADE_TYPE, db_index=True,
                            blank=True, verbose_name=u'订单类型')
    shipping_type = models.CharField(max_length=12, blank=True,
                                     choices=SHIPPING_TYPE_CHOICE, verbose_name=u'物流方式')

    order_num = models.IntegerField(default=0, verbose_name=u'单数')
    prod_num = models.IntegerField(default=0, verbose_name=u'品类数')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'折扣')
    adjust_fee = models.FloatField(default=0.0, verbose_name=u'调整费用')
    post_fee = models.FloatField(default=0.0, verbose_name=u'物流费用')
    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')

    is_cod = models.BooleanField(default=False, verbose_name=u'货到付款')
    seller_cod_fee = models.FloatField(default=0.0, verbose_name=u'COD卖家费用')
    buyer_cod_fee = models.FloatField(default=0.0, verbose_name=u'COD买家费用')
    cod_fee = models.FloatField(default=0.0, verbose_name=u'COD费用')
    cod_status = models.CharField(max_length=32, blank=True,
                                  choices=COD_STATUS, verbose_name=u'COD状态')

    weight = models.CharField(max_length=10, blank=True, verbose_name=u'包裹重量')
    post_cost = models.FloatField(default=0.0, verbose_name=u'物流成本')

    buyer_message = models.TextField(max_length=1000, blank=True, verbose_name=u'买家留言')
    seller_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'卖家备注')
    sys_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'系统备注')
    seller_flag = models.IntegerField(null=True, verbose_name=u'淘宝旗帜')

    created = models.DateTimeField(null=True, blank=True, verbose_name=u'生成日期')
    pay_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'付款日期')
    modified = models.DateTimeField(null=True, auto_now=True, blank=True, verbose_name=u'修改日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'预售日期')
    send_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    weight_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'称重日期')
    charge_time = models.DateTimeField(null=True, blank=True, verbose_name=u'揽件日期')
    remind_time = models.DateTimeField(null=True, blank=True, verbose_name=u'提醒日期')

    is_brand_sale = models.BooleanField(default=False, verbose_name=u'品牌特卖')
    is_force_wlb = models.BooleanField(default=False, verbose_name=u'物流宝')
    trade_from = BitField(flags=(pcfg.TF_WAP,
                                 pcfg.TF_HITAO,
                                 pcfg.TF_TOP,
                                 pcfg.TF_TAOBAO,
                                 pcfg.TF_JHS), verbose_name=u'交易来源')

    is_lgtype = models.BooleanField(default=False, verbose_name=u'速递')
    lg_aging = models.DateTimeField(null=True, blank=True, verbose_name=u'速递送达时间')
    lg_aging_type = models.CharField(max_length=20, blank=True, verbose_name=u'速递类型')

    buyer_rate = models.BooleanField(default=False, verbose_name=u'买家已评')
    seller_rate = models.BooleanField(default=False, verbose_name=u'卖家已评')
    seller_can_rate = models.BooleanField(default=False, verbose_name=u'卖家可评')
    is_part_consign = models.BooleanField(default=False, verbose_name=u'分单发货')

    out_sid = models.CharField(max_length=64, db_index=True,
                               blank=True, verbose_name=u'物流编号')
    logistics_company = models.ForeignKey(LogisticsCompany, null=True,
                                          blank=True, verbose_name=u'物流公司')
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')

    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24, db_index=True,
                                       blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True,
                                      blank=True, verbose_name=u'电话')

    step_paid_fee = models.CharField(max_length=10, blank=True, verbose_name=u'分阶付款金额')
    step_trade_status = models.CharField(max_length=32, choices=STEP_TRADE_STATUS,
                                         blank=True, verbose_name=u'分阶付款状态')

    reason_code = models.CharField(max_length=100, blank=True, verbose_name=u'问题编号')  # 1,2,3 问题单原因编码集合
    status = models.CharField(max_length=32, choices=TAOBAO_TRADE_STATUS,
                              blank=True, verbose_name=u'订单状态')

    is_picking_print = models.BooleanField(default=False, verbose_name=u'发货单')
    is_express_print = models.BooleanField(default=False, verbose_name=u'物流单')
    is_send_sms = models.BooleanField(default=False, verbose_name=u'发货通知')
    has_refund = models.BooleanField(default=False, verbose_name=u'待退款')
    has_out_stock = models.BooleanField(default=False, verbose_name=u'缺货')
    has_rule_match = models.BooleanField(default=False, verbose_name=u'有匹配')
    has_memo = models.BooleanField(default=False, verbose_name=u'有留言')
    has_merge = models.BooleanField(default=False, verbose_name=u'有合单')
    has_sys_err = models.BooleanField(default=False, verbose_name=u'系统错误')
    refund_num = models.IntegerField(null=True, default=0, verbose_name=u'退款单数')  # 退款单数

    is_qrcode = models.BooleanField(default=False, verbose_name=u'热敏订单')
    qrcode_msg = models.CharField(max_length=32, blank=True, verbose_name=u'打印信息')

    can_review = models.BooleanField(default=False, verbose_name=u'复审')
    priority = models.IntegerField(default=0,
                                   choices=PRIORITY_TYPE, verbose_name=u'优先级')
    operator = models.CharField(max_length=32, blank=True, verbose_name=u'打单员')
    scanner = models.CharField(max_length=64, blank=True, verbose_name=u'扫描员')
    weighter = models.CharField(max_length=64, blank=True, verbose_name=u'称重员')
    is_locked = models.BooleanField(default=False, verbose_name=u'锁定')
    is_charged = models.BooleanField(default=False, verbose_name=u'揽件')
    sys_status = models.CharField(max_length=32, db_index=True,
                                  choices=SYS_TRADE_STATUS, blank=True,
                                  default='', verbose_name=u'系统状态')
    ware_by = models.IntegerField(default=WARE_SH, choices=WARE_CHOICES,
                                  db_index=True, verbose_name=u'所属仓库')
    reserveo = models.CharField(max_length=64, blank=True, verbose_name=u'自定义1')
    reservet = models.CharField(max_length=64, blank=True, verbose_name=u'自定义2')
    reserveh = models.CharField(max_length=64, blank=True, verbose_name=u'自定义3')

    objects = MergeTradeManager()

    class Meta:
        db_table = 'shop_trades_mergetrade'
        unique_together = ("tid", "user")
        app_label = 'trades'
        ordering = []
        verbose_name = u'订单'
        verbose_name_plural = u'订单列表'
        permissions = [
            ("can_trade_modify", u"修改订单状态权限"),
            ("can_trade_aduit", u"审核订单权限"),
            ("sync_trade_post_taobao", u"同步淘宝发货权限"),
            ("merge_order_action", u"合并订单权限"),
            ("pull_order_action", u"重新下载订单权限"),
            ("invalid_order_action", u"作废订单权限"),
            ("unlock_trade_action", u"订单解锁权限"),
            ("export_finance_action", u"订单金额导出权限"),
            ("export_logistic_action", u"物流信息导出权限"),
            ("export_buyer_action", u"买家信息导出权限"),
            ("export_orderdetail_action", u"订单明细导出权限"),
            ("export_yunda_action", u"韵达信息导出权限")
        ]

    def __unicode__(self):
        return '<%s,%s>' % (str(self.id), self.buyer_nick)

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    @property
    def total_num(self):
        """ 订单商品总数 """
        return self.inuse_orders.aggregate(total_num=Sum('num')).get('total_num') or 0

    @property
    def inuse_orders(self):
        return self.merge_orders.filter(sys_status=pcfg.IN_EFFECT)

    @property
    def normal_orders(self):
        return self.merge_orders.filter(sys_status=pcfg.IN_EFFECT)

    @property
    def print_orders(self):
        return self.merge_orders.filter(sys_status=pcfg.IN_EFFECT) \
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)

    @property
    def split_orders(self):
        return self.merge_orders.filter(refund_status__in=(pcfg.NO_REFUND, pcfg.REFUND_CLOSED)) \
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE) \
            .exclude(sys_status=pcfg.INVALID_STATUS, gift_type=pcfg.CS_PERMI_GIT_TYPE)

    @property
    def return_orders(self):
        return self.merge_orders.filter(sys_status=pcfg.IN_EFFECT,
                                        gift_type=pcfg.RETURN_GOODS_GIT_TYPE)

    @property
    def buyer_full_address(self):
        return '%s%s%s%s%s%s%s' % (self.receiver_name.strip(),
                                   self.receiver_mobile.strip(),
                                   self.receiver_phone.strip(),
                                   self.receiver_state.strip(),
                                   self.receiver_city.strip(),
                                   self.receiver_district.strip(),
                                   self.receiver_address.strip())

    @property
    def can_change_order(self):
        return self.sys_status in (pcfg.WAIT_AUDIT_STATUS,
                                   pcfg.REGULAR_REMAIN_STATUS,
                                   pcfg.WAIT_CHECK_BARCODE_STATUS,
                                   pcfg.WAIT_SCAN_WEIGHT_STATUS)

    @property
    def can_reverse_order(self):
        return self.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                   pcfg.WAIT_SCAN_WEIGHT_STATUS)

    def isPostScan(self):
        return self.status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                               pcfg.WAIT_SCAN_WEIGHT_STATUS)

    def isSplit(self):
        """ 是否分拆过后的订单 """
        return self.is_part_consign

    def get_sale_trade(self):
        if self.type == pcfg.SALE_TYPE:
            return SaleTrade.objects.get(tid=self.tid)
        return None

    def get_sale_orders(self):
        from flashsale.pay.models import SaleOrder, SaleRefund
        if self.type == pcfg.SALE_TYPE:
            sale_trade_ids = [s.id for s in SaleTrade.objects.filter(tid=self.tid)]
            if self.has_merge:
                merge_ids = [m.sub_tid for m in MergeBuyerTrade.objects.filter(main_tid=self.id)]
                sale_trade_ids.extend(merge_ids)
            return SaleOrder.objects.filter(sale_trade_id__in=sale_trade_ids, refund_status=SaleRefund.NO_REFUND)
        return None

    def get_package(self):
        if self.status == pcfg.ON_THE_FLY_STATUS:
            return None
        else:
            if self.out_sid:
                try:
                    return PackageOrder.objects.get(out_sid=self.out_sid)
                except:
                    pass
            try:
                sale_trade = self.get_sale_trade()
                if sale_trade and self.ware_by:
                    return PackageOrder.objects.filter(buyer_id=sale_trade.buyer_id,
                                                    user_address_id=sale_trade.user_address_id, ware_by=self.ware_by)\
                        .order_by('-id').first()
                elif sale_trade:
                    return PackageOrder.objects.filter(buyer_id=sale_trade.buyer_id,
                                                       user_address_id=sale_trade.user_address_id).order_by('-id').first()
                else:
                    return None
            except:
                return None

    def get_trade_assign_ware(self):
        """ 获取订单关联仓库 """

        pre_ware = MergeTrade.WARE_NONE
        for order in self.normal_orders:
            try:
                cur_ware = Product.objects.get(outer_id=order.outer_id).ware_by
                if pre_ware and pre_ware != cur_ware:
                    return MergeTrade.WARE_NONE
                pre_ware = cur_ware
            except:
                return MergeTrade.WARE_NONE
        return pre_ware

    def update_inventory(self, update_returns=False, update_changes=True):
        """
            根据订单商品更新库存信息：
            update_returns:是否更新退货单上库存(默认不更新,因为在退货商品入库是已经更新);
            update_changes:是否更新换货商品库存信息;
        """
        post_orders = self.inuse_orders
        if not update_returns:
            post_orders.exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)

        if not update_changes:
            post_orders.exclude(gift_type=pcfg.CHANGE_GOODS_GIT_TYPE)

        for order in post_orders:
            outer_sku_id = order.outer_sku_id
            outer_id = order.outer_id
            order_num = order.num
            prod = None
            prod_sku = None
            is_reverse = order.gift_type != pcfg.RETURN_GOODS_GIT_TYPE
            if outer_sku_id and outer_id:
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id, product__outer_id=outer_id)
                prod_sku.update_quantity(order_num, dec_update=is_reverse)
            elif outer_id:
                prod = Product.objects.get(outer_id=outer_id)
                prod.update_collect_num(order_num, dec_update=is_reverse)
            else:
                raise Exception('订单商品没有商家编码')
            if order.gift_type in (pcfg.REAL_ORDER_GIT_TYPE, pcfg.COMBOSE_SPLIT_GIT_TYPE):
                if prod_sku:
                    prod_sku.update_wait_post_num(order_num, dec_update=True)
                else:
                    prod.update_wait_post_num(order_num, dec_update=True)
        return True

    def append_reason_code(self, code):

        reason_set = set(self.reason_code.split(','))
        reason_set.add(str(code))
        self.reason_code = ','.join(list(reason_set))

        if code in (pcfg.POST_MODIFY_CODE,
                    pcfg.POST_SUB_TRADE_ERROR_CODE,
                    pcfg.COMPOSE_RULE_ERROR_CODE,
                    pcfg.PULL_ORDER_ERROR_CODE,
                    pcfg.PAYMENT_RULE_ERROR_CODE,
                    pcfg.MERGE_TRADE_ERROR_CODE):
            self.has_sys_err = True

        if (self.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                pcfg.WAIT_SCAN_WEIGHT_STATUS) and
                self.can_review):
            self.can_review = False
            log_action(self.user.user.id, self, CHANGE,
                       u'新问题(编号：%s)' % self.reason_code)

        update_model_fields(self, update_fields=['reason_code',
                                                 'has_sys_err',
                                                 'can_review'])

        rows = MergeTrade.objects.filter(id=self.id,
                                         out_sid='',
                                         sys_status=pcfg.WAIT_PREPARE_SEND_STATUS) \
            .update(sys_status=pcfg.WAIT_AUDIT_STATUS)
        if rows > 0:
            self.sys_status = pcfg.WAIT_AUDIT_STATUS

    def remove_reason_code(self, code):
        reason_set = set(self.reason_code.split(','))
        try:
            reason_set.remove(str(code))
        except:
            return False
        else:
            self.reason_code = ','.join(list(reason_set))

            update_model_fields(self, update_fields=['reason_code', ])
        return True

    def has_reason_code(self, code):
        reason_set = set(self.reason_code.split(','))
        return str(code) in reason_set

    def update_buyer_message(self, trade_id, msg):

        msg = msg.replace('|', '，'.decode('utf8')) \
            .replace(':', '：'.decode('utf8'))
        buyer_msg = self.buyer_message.split('|')

        msg_dict = {}
        for m in buyer_msg:
            m = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.id)] = (self.buyer_message
                                          .replace('|', '，'.decode('utf8'))
                                          .replace(':', '：'.decode('utf8')))
        msg_dict[str(trade_id)] = msg
        self.buyer_message = '|'.join(['%s:%s' % (k, v) for k, v in msg_dict.items()])

        update_model_fields(self, update_fields=['buyer_message'])
        self.append_reason_code(pcfg.NEW_MEMO_CODE)

        return self.buyer_message

    def remove_buyer_message(self, trade_id):

        buyer_msg = self.buyer_message.split('|')
        msg_dict = {}
        for m in buyer_msg:
            m = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]

        if msg_dict:
            msg_dict.pop(int(trade_id), None)
            self.buyer_message = '|'.join(['%s:%s' % (k, v) for k, v in msg_dict.items()])

            update_model_fields(self, update_fields=['buyer_message'])

        return self.buyer_message

    def update_seller_memo(self, trade_id, msg):

        msg = msg.replace('|', '，'.decode('utf8')).replace(':', '：'.decode('utf8'))
        seller_msg = self.seller_memo.split('|')
        msg_dict = {}
        for m in seller_msg:
            m = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]
            else:
                msg_dict[str(self.id)] = self.seller_memo.replace('|', '，'.decode('utf8')) \
                    .replace(':', '：'.decode('utf8'))
        msg_dict[str(trade_id)] = msg
        self.seller_memo = '|'.join(['%s:%s' % (k, v) for k, v in msg_dict.items()])

        update_model_fields(self, update_fields=['seller_memo'])

        self.append_reason_code(pcfg.NEW_MEMO_CODE)

        return self.seller_memo

    def remove_seller_memo(self, trade_id):

        seller_msg = self.seller_memo.split('|')
        msg_dict = {}
        for m in seller_msg:
            m = m.split(':')
            if len(m) == 2:
                msg_dict[m[0]] = m[1]
        if msg_dict:
            msg_dict.pop(str(trade_id), None)
            self.seller_memo = '|'.join(['%s:%s' % (k, v) for k, v in msg_dict.items()])

            update_model_fields(self, update_fields=['seller_memo'])

        return self.seller_memo

    def sync_attr_from_package(self, package):
        attrs = []
        for attr in attrs:
            val = getattr(package, attr)
            setattr(self, attr, val)
        self.save()


# 平台名称与存储编码映射
TF_CODE_MAP = {
    pcfg.TF_WAP: MergeTrade.trade_from.WAP,
    pcfg.TF_HITAO: MergeTrade.trade_from.HITAO,
    pcfg.TF_TOP: MergeTrade.trade_from.TOP,
    pcfg.TF_TAOBAO: MergeTrade.trade_from.TAOBAO,
    pcfg.TF_JHS: MergeTrade.trade_from.JHS,
}


def recalc_trade_fee(sender, trade_id, *args, **kwargs):
    trade = MergeTrade.objects.get(id=trade_id)
    fee_dict = trade.merge_orders.aggregate(total_total_fee=Sum('total_fee'),
                                            total_payment=Sum('payment'),
                                            total_discount_fee=Sum('discount_fee'),
                                            total_adjust_fee=Sum('adjust_fee'))

    trade.total_fee = fee_dict.get('total_total_fee')
    trade.payment = fee_dict.get('total_payment')
    trade.discount_fee = fee_dict.get('total_discount_fee')
    trade.adjust_fee = fee_dict.get('total_adjust_fee')

    update_model_fields(trade, update_fields=['total_fee',
                                              'payment',
                                              'discount_fee',
                                              'adjust_fee'])


signals.recalc_fee_signal.connect(recalc_trade_fee, sender=MergeTrade)


#
# class MergeCtrl(models.Model):
#
#     WARE_SH  = 0
#     WARE_GZ  = 1
#     WARE_CHOICES = ((WARE_SH,u'上海仓'),
#                     (WARE_GZ,u'广州仓'))
#
#     mergetrade       = models.OneToOneField(MergeTrade,primary_key=True,
#                                           related_name='controller',verbose_name=u'所属订单')
#
#     is_picking_print = models.BooleanField(default=False,verbose_name=u'发货单')
#     is_express_print = models.BooleanField(default=False,verbose_name=u'物流单')
#     is_send_sms      = models.BooleanField(default=False,verbose_name=u'发货通知')
#     has_refund       = models.BooleanField(default=False,verbose_name=u'待退款')
#     has_out_stock    = models.BooleanField(default=False,verbose_name=u'缺货')
#     has_rule_match   = models.BooleanField(default=False,verbose_name=u'有匹配')
#     has_memo         = models.BooleanField(default=False,verbose_name=u'有留言')
#     has_merge        = models.BooleanField(default=False,verbose_name=u'有合单')
#     has_sys_err      = models.BooleanField(default=False,verbose_name=u'系统错误')
#     refund_num       = models.IntegerField(null=True,default=0,verbose_name=u'退款单数')  #退款单数
#
#     is_qrcode        = models.BooleanField(default=False,verbose_name=u'热敏订单')
#     qrcode_msg       = models.CharField(max_length=32,blank=True,verbose_name=u'打印信息')
#
#     can_review       = models.BooleanField(default=False,verbose_name=u'复审')
#     priority       =  models.IntegerField(default=0,
#                                           choices=PRIORITY_TYPE,verbose_name=u'优先级')
#     operator       =  models.CharField(max_length=32,blank=True,verbose_name=u'打单员')
#     scanner        =  models.CharField(max_length=64,blank=True,verbose_name=u'扫描员')
#     weighter       =  models.CharField(max_length=64,blank=True,verbose_name=u'称重员')
#     is_locked      =  models.BooleanField(default=False,verbose_name=u'锁定')
#     is_charged     =  models.BooleanField(default=False,verbose_name=u'揽件')
#     sys_status     =  models.CharField(max_length=32,db_index=True,
#                                        choices=SYS_TRADE_STATUS,blank=True,
#                                        default='',verbose_name=u'系统状态')
#
#     ware_by        = models.IntegerField(default=WARE_SH,choices=WARE_CHOICES,
#                                          index=True,verbose_name=u'所属仓库')
#     reason_code = models.CharField(max_length=100,blank=True,verbose_name=u'问题编号')  #1,2,3 问题单原因编码集合
#     class Meta:
#         db_table = 'shop_trades_ctrl'
#         verbose_name=u'订单操作状态'
#         verbose_name_plural = u'订单操作状态列表'
#
#     def __unicode__(self):
#         return '<%s,%s>'%(str(self.mergetrade),self.sys_status)


class MergeOrder(models.Model):
    NO_REFUND = pcfg.NO_REFUND
    REFUND_WAIT_SELLER_AGREE = pcfg.REFUND_WAIT_SELLER_AGREE
    REFUND_WAIT_RETURN_GOODS = pcfg.REFUND_WAIT_RETURN_GOODS
    REFUND_CONFIRM_GOODS = pcfg.REFUND_CONFIRM_GOODS
    REFUND_REFUSE_BUYER = pcfg.REFUND_REFUSE_BUYER
    REFUND_CLOSED = pcfg.REFUND_CLOSED
    REFUND_SUCCESS = pcfg.REFUND_SUCCESS

    REAL_ORDER_GIT_TYPE = pcfg.REAL_ORDER_GIT_TYPE
    CS_PERMI_GIT_TYPE = pcfg.CS_PERMI_GIT_TYPE
    OVER_PAYMENT_GIT_TYPE = pcfg.OVER_PAYMENT_GIT_TYPE
    COMBOSE_SPLIT_GIT_TYPE = pcfg.COMBOSE_SPLIT_GIT_TYPE
    RETURN_GOODS_GIT_TYPE = pcfg.RETURN_GOODS_GIT_TYPE
    CHANGE_GOODS_GIT_TYPE = pcfg.CHANGE_GOODS_GIT_TYPE
    ITEM_GIFT_TYPE = pcfg.ITEM_GIFT_TYPE

    SYS_ORDER_STATUS = SYS_ORDER_STATUS
    TAOBAO_ORDER_STATUS = TAOBAO_ORDER_STATUS
    GIFT_TYPE = GIFT_TYPE

    NORMAL = pcfg.IN_EFFECT
    DELETE = pcfg.INVALID_STATUS
    SYS_ORDER_STATUS = (
        (NORMAL, u'有效'),
        (DELETE, u'无效'),
    )

    id = BigIntegerAutoField(primary_key=True)
    oid = models.CharField(max_length=32,
                           default=lambda: 'DO%d' % int(time.time() * 10 ** 5),
                           verbose_name=u'原单ID')
    merge_trade = BigIntegerForeignKey(MergeTrade,
                                       related_name='merge_orders',
                                       verbose_name=u'所属订单')

    cid = models.BigIntegerField(null=True, verbose_name=u'商品分类')
    num_iid = models.CharField(max_length=64, blank=True, verbose_name=u'线上商品编号')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'单价')

    sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    num = models.IntegerField(null=True, default=0, verbose_name=u'商品数量')

    outer_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品编码')
    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格编码')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'折扣')
    adjust_fee = models.FloatField(default=0.0, verbose_name=u'调整费用')

    sku_properties_name = models.CharField(max_length=256, blank=True,
                                           verbose_name=u'购买规格')

    refund_id = models.BigIntegerField(null=True, blank=True, verbose_name=u'退款号')
    refund_status = models.CharField(max_length=40, choices=REFUND_STATUS,
                                     blank=True, verbose_name=u'退款状态')

    pic_path = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')

    seller_nick = models.CharField(max_length=32, blank=True, verbose_name=u'卖家昵称')
    buyer_nick = models.CharField(max_length=32, blank=True, verbose_name=u'买家昵称')

    created = models.DateTimeField(null=True, blank=True, verbose_name=u'创建日期')
    pay_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'付款日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')

    out_stock = models.BooleanField(default=False, verbose_name=u'缺货')
    is_merge = models.BooleanField(default=False, verbose_name=u'合并')
    is_rule_match = models.BooleanField(default=False, verbose_name=u'匹配')
    is_reverse_order = models.BooleanField(default=False, verbose_name=u'追改')
    gift_type = models.IntegerField(choices=GIFT_TYPE, default=0, verbose_name=u'类型')

    status = models.CharField(max_length=32, choices=TAOBAO_ORDER_STATUS,
                              blank=True, verbose_name=u'订单状态')
    sys_status = models.CharField(max_length=32,
                                  choices=SYS_ORDER_STATUS,
                                  blank=True,
                                  default='',
                                  verbose_name=u'系统状态')

    class Meta:
        db_table = 'shop_trades_mergeorder'
        unique_together = ("oid", "merge_trade")
        app_label = 'trades'
        verbose_name = u'订单明细'
        verbose_name_plural = u'订单明细列表'

    def __unicode__(self):
        return '<%s,%s>' % (str(self.id), self.outer_id)

    @property
    def sale_order(self):
        if not hasattr(self, '_sale_trade_'):
            try:
                from flashsale.pay.models import SaleOrder
                sale_trade = SaleTrade.objects.get(tid=self.merge_trade.tid)
                self._sale_trade_ = SaleOrder.objects.get(sale_trade_id=sale_trade.id, sku_id=self.sku_id, num=self.num)
            except:
                self._sale_trade_ = None
        return self._sale_trade_

    def isEffect(self):
        return self.sys_status == pcfg.IN_EFFECT

    def isInvalid(self):
        return self.sys_status == pcfg.INVALID_STATUS

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

    def get_ware_by(self):
        try:
            return Product.objects.get(outer_id=self.outer_id).ware_by
        except:
            return Product.WARE_NONE

    @classmethod
    def get_yesterday_orders_totalnum(cls, shop_user_id, outer_id, outer_sku_id):
        """ 获取某店铺昨日某商品销售量，与总销量 """

        st_f, st_t = get_yesterday_interval_time()
        orders = cls.objects.filter(merge_trade__pay_time__gte=st_f,
                                    merge_trade__pay_time__lte=st_t,
                                    outer_id=outer_id,
                                    outer_sku_id=outer_sku_id)
        total_num = orders.count()
        user_order_num = orders.filter(merge_trade__user__id=shop_user_id).count()

        return total_num, user_order_num

    @classmethod
    def gen_new_order(cls, trade_id, outer_id, outer_sku_id, num,
                      gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                      status=pcfg.WAIT_SELLER_SEND_GOODS,
                      is_reverse=False,
                      payment='0',
                      created=None,
                      pay_time=None):

        merge_trade = MergeTrade.objects.get(id=trade_id)
        product = Product.objects.get(outer_id=outer_id)
        # print "到了这里788888", product
        sku_properties_name = ''
        productsku = None

        if outer_sku_id:
            try:
                productsku = ProductSku.objects.get(outer_id=outer_sku_id, product__outer_id=outer_id)
                sku_properties_name = productsku.name
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                merge_trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
        # print "到了这里788888", gift_type
        merge_order = MergeOrder.objects.create(
            merge_trade=merge_trade,
            outer_id=outer_id,
            price=product.std_sale_price,
            payment=payment,
            num=num,
            title=product.name,
            outer_sku_id=outer_sku_id,
            sku_properties_name=sku_properties_name,
            refund_status=pcfg.NO_REFUND,
            seller_nick=merge_trade.user.nick,
            buyer_nick=merge_trade.buyer_nick,
            created=created or datetime.datetime.now(),
            pay_time=pay_time or datetime.datetime.now(),
            consign_time=merge_trade.consign_time,
            gift_type=gift_type,
            is_reverse_order=is_reverse,
            out_stock=(productsku.is_out_stock if productsku else product.is_out_stock),
            status=status,
            sys_status=pcfg.IN_EFFECT,
        )
        # print "成功6666555555", merge_order
        post_save.send(sender=cls, instance=merge_order)  # 通知消息更新主订单
        return merge_order

    def getImgSimpleNameAndPrice(self):
        try:
            prod = Product.objects.get(outer_id=self.outer_id)
            prodSku = None
            std_sale_price = prod.std_sale_price
            if self.outer_sku_id:
                prodSku = ProductSku.objects.get(outer_id=self.outer_sku_id,
                                                 product=prod)
                std_sale_price = prodSku.std_sale_price
            simplename = ' '.join([prod.name, (prodSku and prodSku.name or ''), 'x' + str(self.num)])
            return [prod.pic_path, simplename, std_sale_price]
        except:
            return [self.pic_path, self.title + ' x' + str(self.num), ""]

    def getSimpleName(self):

        try:
            prod = Product.objects.get(outer_id=self.outer_id)
            prodSku = None
            if self.outer_sku_id:
                prodSku = ProductSku.objects.get(outer_id=self.outer_sku_id,
                                                 product=prod)
            return ' '.join([prod.name, (prodSku and prodSku.name or ''), 'x' + str(self.num)])
        except:
            return self.title + ' x' + str(self.num)


def refresh_trade_status(sender, instance, *args, **kwargs):
    """ 订单明细及交易状态更新：
        １，如果订单明细创建时间和付款时间空则使用该笔交易的时间;
        ２，更新有变动交易的字段：[order_num,prod_num,has_refund,has_out_stock,has_rule_match,sys_status];
    """
    merge_trade = instance.merge_trade
    update_params = {}
    if not (instance.pay_time and instance.created):
        instance.created = instance.created or merge_trade.created
        instance.pay_time = instance.pay_time or merge_trade.pay_time

        update_model_fields(instance, update_fields=['created',
                                                     'pay_time'])

    effect_orders = merge_trade.inuse_orders
    update_params['order_num'] = effect_orders.aggregate(total_num=Sum('num'))['total_num'] or 0
    update_params['prod_num'] = effect_orders.values_list('outer_id').distinct().count()
    if merge_trade.status in (pcfg.WAIT_SELLER_SEND_GOODS,
                              pcfg.WAIT_BUYER_CONFIRM_GOODS):

        update_params['has_refund'] = MergeTrade.objects.isTradeRefunding(merge_trade)
        update_params['has_out_stock'] = effect_orders.filter(out_stock=True).count() > 0
        update_params['has_rule_match'] = effect_orders.filter(is_rule_match=True).count() > 0

        if merge_trade.has_out_stock and not update_params['has_out_stock']:
            merge_trade.remove_reason_code(pcfg.OUT_GOOD_CODE)

    if (not merge_trade.reason_code and
                merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS and
            merge_trade.logistics_company and
                merge_trade.sys_status == pcfg.WAIT_AUDIT_STATUS and
                merge_trade.type not in (pcfg.DIRECT_TYPE,
                                         pcfg.REISSUE_TYPE,
                                         pcfg.EXCHANGE_TYPE)):
        update_params['sys_status'] = pcfg.WAIT_PREPARE_SEND_STATUS

    update_fields = []
    for k, v in update_params.iteritems():
        if getattr(merge_trade, k) != v:
            setattr(merge_trade, k, v)
            update_fields.append(k)

    if update_fields:
        update_model_fields(merge_trade, update_fields=update_fields)


post_save.connect(refresh_trade_status, sender=MergeOrder)


def refund_update_order_info(sender, obj, *args, **kwargs):
    """
    退款更新订单明细状态及对应商品的待发数
    1,找到对应的商品的有效子订单;
    2,修改对应的订单状态，该笔交易的问题编号；
    3,减掉待发数；
    """
    from flashsale.pay.models_refund import SaleRefund
    if not isinstance(obj, SaleRefund):
        logger.warning('refund ins(%s) not SaleRefund' % obj)
        return

    sysoa = User.getSystemOAUser()
    try:
        trade_tid = obj.get_tid()
        trade_oid = obj.get_oid()
        normal_status_list = MergeTrade.WAIT_WEIGHT_STATUS
        normal_status_list.append(MergeTrade.ON_THE_FLY_STATUS)
        mtrade = MergeTrade.objects.get(tid=trade_tid)
        morders = MergeOrder.objects.filter(oid=trade_oid,
                                            merge_trade__user=mtrade.user,
                                            merge_trade__sys_status__in=normal_status_list,
                                            sys_status=MergeOrder.NORMAL)
        for morder in morders:
            morder.refund_status = MergeOrder.REFUND_WAIT_SELLER_AGREE
            morder.sys_status = MergeOrder.DELETE
            morder.save()
            itrade = morder.merge_trade
            itrade.append_reason_code(pcfg.NEW_REFUND_CODE)
            if itrade.sys_status == MergeTrade.ON_THE_FLY_STATUS:
                log_action(sysoa.id, itrade, CHANGE, u'飞行模式订单(oid:%s)退款自动关闭' % morder.id)
            else:
                log_action(sysoa.id, itrade, CHANGE, u'订单(oid:%s)退款自动关闭' % morder.id)
                Product.objects.reduceWaitPostNumByCode(morder.outer_id, morder.outer_sku_id, morder.num)
                Product.objects.reduceLockNumByCode(morder.outer_id, morder.outer_sku_id, morder.num)
    except Exception, exc:
        logger.error('order refund signal:%s' % exc.message)


signals.order_refund_signal.connect(refund_update_order_info, sender=MergeOrder)


class MergeBuyerTrade(models.Model):
    MAIN_MERGE_TYPE = pcfg.MAIN_MERGE_TYPE
    NO_MERGE_TYPE = pcfg.NO_MERGE_TYPE
    SUB_MERGE_TYPE = pcfg.SUB_MERGE_TYPE

    sub_tid = models.BigIntegerField(primary_key=True)
    main_tid = models.BigIntegerField(db_index=True)
    created = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        db_table = 'shop_trades_mergebuyertrade'
        app_label = 'trades'
        verbose_name = u'合单记录'
        verbose_name_plural = u'合单列表'

    def __unicode__(self):
        return '<%d,%d>' % (self.sub_tid, self.main_tid)

    @classmethod
    def getMergeType(cls, id):
        """
        0,no merge,
        1,sub merge trade,
        2,main merge trade
        """
        try:
            cls.objects.get(sub_tid=id)
        except cls.DoesNotExist:
            merges = cls.objects.filter(main_tid=id)
            if merges.count() > 0:
                return pcfg.MAIN_MERGE_TYPE
            return pcfg.NO_MERGE_TYPE
        return pcfg.SUB_MERGE_TYPE


class MergeTradeDelivery(models.Model):
    WAIT_DELIVERY = 0
    FAIL_DELIVERY = 1

    DELIVERY_CHOICES = ((WAIT_DELIVERY, u'等待上传'),
                        (FAIL_DELIVERY, u'上传失败'),)
    id = BigIntegerAutoField(primary_key=True)
    seller = models.ForeignKey(User, null=True, verbose_name=u'所属店铺')

    trade_id = models.BigIntegerField(unique=True, verbose_name=u'订单ID')
    trade_no = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'订单编号')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')
    delivery_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'发货时间')

    is_parent = models.BooleanField(default=False, verbose_name=u'父订单')
    is_sub = models.BooleanField(default=False, verbose_name=u'子订单')

    parent_tid = models.BigIntegerField(default=0, db_index=True, verbose_name=u'父订单ID')

    message = models.CharField(max_length=126, blank=True, verbose_name=u'错误消息')

    status = models.IntegerField(choices=DELIVERY_CHOICES,
                                 default=WAIT_DELIVERY, blank=True, verbose_name=u'上传状态')

    class Meta:
        db_table = 'shop_trades_delivery'
        app_label = 'trades'
        verbose_name = u'订单/发货上传'
        verbose_name_plural = u'订单/发货上传列表'

    def __unicode__(self):
        return '%s' % self.trade_id


REPLAY_TRADE_STATUS = (
    (pcfg.RP_INITIAL_STATUS, u'初始状态'),
    (pcfg.RP_WAIT_ACCEPT_STATUS, u'待接单'),
    (pcfg.RP_WAIT_CHECK_STATUS, u'待验单'),
    (pcfg.RP_ACCEPT_STATUS, u'已验单'),
    (pcfg.RP_CANCEL_STATUS, u'已作废'),
)


class ReplayPostTrade(models.Model):
    """ 已发货清单 """

    operator = models.CharField(max_length=32, db_index=True, verbose_name=u'发货人')

    fid = models.BigIntegerField(default=0, verbose_name=u'父批次号')  # 正常0，合并-1，合并子单 父ID

    post_data = models.TextField(blank=True, verbose_name=u'清单数据')

    order_num = models.BigIntegerField(default=0, verbose_name=u'发货单数')
    trade_ids = models.TextField(blank=True, verbose_name=u'订单编号')

    succ_num = models.BigIntegerField(default=0, verbose_name=u'成功单数')
    succ_ids = models.TextField(blank=True, verbose_name=u'成功订单ID')

    created = models.DateTimeField(null=True, db_index=True, auto_now_add=True, verbose_name=u'创建日期')
    finished = models.DateTimeField(blank=True, db_index=True, null=True, verbose_name=u'完成日期')

    receiver = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'接单人')
    rece_date = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'接单时间')
    check_date = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'验收时间')

    status = models.IntegerField(default=0, db_index=True, choices=REPLAY_TRADE_STATUS, verbose_name=u'状态')

    class Meta:
        db_table = 'shop_trades_replayposttrade'
        app_label = 'trades'
        verbose_name = u'已发货清单'
        verbose_name_plural = u'发货清单列表'

    def __unicode__(self):
        return '<%d,%s,%s,%s>' % (self.id, self.operator,
                                  self.receiver,
                                  dict(REPLAY_TRADE_STATUS).get(self.status, ''))

    def merge(self, post_trades):
        """合并多批发货清单"""

        if post_trades.count() == 0:
            return False

        all_id_set = set()
        for t in post_trades:
            all_id_set.update(t.trade_ids.split(','))

        self.order_num = len(all_id_set)
        self.trade_ids = ','.join(all_id_set)
        self.fid = -1
        self.save()
        # 生成合并后的发货清单
        from shopback.trades.tasks import get_replay_results
        get_replay_results(self)

        for t in post_trades:
            t.fid = self.id
            t.status = pcfg.RP_CANCEL_STATUS
            t.save()

        return True

    def split(self):
        """拆分已合并的发货清单"""
        if self.fid != -1 or self.status != pcfg.RP_WAIT_ACCEPT_STATUS:
            raise Exception(u'不符合拆分条件')

        replay_trades = ReplayPostTrade.objects.filter(
            fid=self.id,
            status=pcfg.RP_CANCEL_STATUS)
        for t in replay_trades:
            t.status = pcfg.RP_WAIT_ACCEPT_STATUS
            t.fid = 0
            t.save()

        self.status = pcfg.RP_CANCEL_STATUS
        self.save()
        return True


class SendLaterTrade(models.Model):
    trade_id = models.BigIntegerField(default=0, verbose_name=u'订单id')
    success = models.BooleanField(default=False, verbose_name=u'发送成功否')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_trades_sendlatertrade'
        app_label = 'trades'
        verbose_name = u'发送超过五天的订单'
        verbose_name_plural = u'发送超过五天的订单'


REPLAY_TRADE__WULIU_STATUS = (
    (pcfg.RP_BUG_STATUS, u'查询异常'),
    (pcfg.RP_NO_RECORD_STATUS, u'没有记录'),
    (pcfg.RP_IN_WAY_STATUS, u'在路上'),
    (pcfg.RP_IN_SENDSTATUS, u'派送中'),
    (pcfg.RP_ALREADY_SIGN_STATUS, u'已经签收'),
    (pcfg.RP_REFUSE_SIGN_STATUS, u'拒绝签收'),
    (pcfg.RP_CANNOT_SEND_STATUS, u'某些原因，无法派送'),
    (pcfg.RP_INVALID__STATUS, u'无效单'),
    (pcfg.RP_OVER_TIME_STATUS, u'超时单'),
    (pcfg.RP_FAILED_SIGN_STATUS, u'签收失败'),
)


class TradeWuliu(models.Model):
    """ 已发货清单 """

    tid = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'原单ID')
    out_sid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'物流编号')
    logistics_company = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'物流公司')
    status = models.IntegerField(default=0, db_index=True, choices=REPLAY_TRADE__WULIU_STATUS, verbose_name=u'物流状态')
    time = models.DateTimeField(null=True, db_index=True, auto_now_add=False, verbose_name=u'时间')
    content = models.CharField(max_length=640, blank=True, verbose_name=u'物流详情')
    created = models.DateTimeField(null=True, db_index=True, auto_now_add=True, verbose_name=u'记录日期')
    modified = models.DateTimeField(null=True, auto_now=True, blank=True, verbose_name=u'修改日期')
    errcode = models.CharField(max_length=64, blank=True, verbose_name=u'错误代码')
    remark = models.CharField(max_length=64, blank=True, verbose_name=u'备注')

    class Meta:
        db_table = 'shop_trades_wuliudetail'
        app_label = 'trades'
        verbose_name = u'物流跟踪'
        verbose_name_plural = u'物流跟踪列表'

    def __unicode__(self):
        return '<%d,%s,%s,%s>' % (self.id, self.status, self.content, dict(REPLAY_TRADE_STATUS).get(self.status, ''))


class PackageOrder(models.Model):
    WARE_SH = 1
    WARE_GZ = 2
    WARE_CHOICES = ((WARE_SH, u'上海仓'),
                    (WARE_GZ, u'广州仓'))
<<<<<<< HEAD
    # PKG_CONFIRM = 'PKG_CONFIRM'
    # PKG_NOT_CONFIRM = 'PKG_NOT_CONFIRM'
    # PACKAGE_CONFIRM_STATUS = ((PKG_NOT_CONFIRM, u'未确定'),
    #                           (PKG_CONFIRM, u'已确定'))
=======
    PKG_CONFIRM = 'PKG_CONFIRM'
    PKG_NOT_CONFIRM = 'PKG_NOT_CONFIRM'
    PACKAGE_CONFIRM_STATUS = ((PKG_NOT_CONFIRM, u'未确定'),
                              (PKG_CONFIRM, u'已确定'))
>>>>>>> edf284db9221e9195c32a03e350545f47f00a0a5
    pid = BigIntegerAutoField(verbose_name=u'包裹主键', primary_key=True)
    id = models.CharField(max_length=100, verbose_name=u'包裹ID')
    tid = models.CharField(max_length=32, verbose_name=u'原单ID')
    ware_by = models.IntegerField(default=WARE_SH, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    type = models.CharField(max_length=32, choices=TRADE_TYPE, db_index=True, default=pcfg.SALE_TYPE,
                            blank=True, verbose_name=u'订单类型')
    TAOBAO_TRADE_STATUS = (
        (pcfg.TRADE_NO_CREATE_PAY, u'订单创建'),
        (pcfg.WAIT_BUYER_PAY, u'待付款'),
        (pcfg.WAIT_SELLER_SEND_GOODS, u'待发货'),
        (pcfg.WAIT_BUYER_CONFIRM_GOODS, u'待确认收货'),
        (pcfg.TRADE_BUYER_SIGNED, u'货到付款签收'),
        (pcfg.TRADE_FINISHED, u'交易成功'),
        (pcfg.TRADE_CLOSED, u'退款交易关闭'),
        (pcfg.TRADE_CLOSED_BY_TAOBAO, u'未付款关闭'),
    )
    status = models.CharField(max_length=32, db_index=True,
                              choices=TAOBAO_TRADE_STATUS, blank=True,
                              default=pcfg.TRADE_NO_CREATE_PAY, verbose_name=u'系统状态')
    PKG_NEW_CREATED = 'PKG_NEW_CREATED'
    WAIT_PREPARE_SEND_STATUS = 'WAIT_PREPARE_SEND_STATUS'
    WAIT_CHECK_BARCODE_STATUS = 'WAIT_CHECK_BARCODE_STATUS'
    WAIT_SCAN_WEIGHT_STATUS = 'WAIT_SCAN_WEIGHT_STATUS'
    WAIT_CUSTOMER_RECEIVE = 'WAIT_CUSTOMER_RECEIVE'
    FINISHED_STATUS = 'FINISHED_STATUS'
    DELETE = 'DELETE'
    PACKAGE_STATUS = (
        (PKG_NEW_CREATED, u'初始状态'),
        (WAIT_PREPARE_SEND_STATUS, u'待发货准备'),
        (WAIT_CHECK_BARCODE_STATUS, u'待扫描验货'),
        (WAIT_SCAN_WEIGHT_STATUS, u'待扫描称重'),
        (WAIT_CUSTOMER_RECEIVE, u'待收货'),
        (FINISHED_STATUS, u'已到货'),
        (DELETE, u'已作废')
    )
    sys_status = models.CharField(max_length=32, db_index=True,
                                  choices=PACKAGE_STATUS, blank=True,
                                  default=PKG_NEW_CREATED, verbose_name=u'系统状态')
    # 物流信息
    seller_id = models.BigIntegerField(db_index=True, verbose_name=u'卖家ID')
    buyer_message = models.TextField(max_length=1000, blank=True, default='', null=False, verbose_name=u'买家留言')
    seller_memo = models.TextField(max_length=1000, blank=True, default='', null=False, verbose_name=u'卖家备注')
    sys_memo = models.TextField(max_length=1000, blank=True, default='', null=False, verbose_name=u'系统备注')
    # 收货信息
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')
    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24, db_index=True,
                                       blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True, blank=True, verbose_name=u'电话')
    seller_id = models.BigIntegerField(db_index=True, verbose_name=u'所属店铺')
    # 物流信息
    buyer_id = models.BigIntegerField(db_index=True, verbose_name=u'买家ID')
    buyer_nick = models.CharField(max_length=64, blank=True, verbose_name=u'买家昵称')
    user_address_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'地址ID')
    post_cost = models.FloatField(default=0.0, verbose_name=u'物流成本')

    buyer_message = models.TextField(max_length=1000, blank=True, verbose_name=u'买家留言')
    seller_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'卖家备注')
    sys_memo = models.TextField(max_length=1000, blank=True, verbose_name=u'系统备注')
    seller_flag = models.IntegerField(null=True, verbose_name=u'淘宝旗帜')

    is_lgtype = models.BooleanField(default=False, verbose_name=u'速递')
    lg_aging = models.DateTimeField(null=True, blank=True, verbose_name=u'速递送达时间')
    lg_aging_type = models.CharField(max_length=20, blank=True, verbose_name=u'速递类型')
    GIFT_TYPE = (
        (pcfg.REAL_ORDER_GIT_TYPE, u'实付'),
        (pcfg.CS_PERMI_GIT_TYPE, u'赠送'),
        (pcfg.OVER_PAYMENT_GIT_TYPE, u'满就送'),
        (pcfg.COMBOSE_SPLIT_GIT_TYPE, u'拆分'),
        (pcfg.RETURN_GOODS_GIT_TYPE, u'退货'),
        (pcfg.CHANGE_GOODS_GIT_TYPE, u'换货'),
        (pcfg.ITEM_GIFT_TYPE, u'买就送'),
    )
    sys_status = models.CharField(max_length=32, db_index=True,
                                  choices=PACKAGE_STATUS, blank=True,
                                  default=PKG_NEW_CREATED, verbose_name=u'系统状态')
    # 收货信息
    receiver_name = models.CharField(max_length=25,
                                     blank=True, verbose_name=u'收货人姓名')
    receiver_state = models.CharField(max_length=16, blank=True, verbose_name=u'省')
    receiver_city = models.CharField(max_length=16, blank=True, verbose_name=u'市')
    receiver_district = models.CharField(max_length=16, blank=True, verbose_name=u'区')
    receiver_address = models.CharField(max_length=128, blank=True, verbose_name=u'详细地址')
    receiver_zip = models.CharField(max_length=10, blank=True, verbose_name=u'邮编')
    receiver_mobile = models.CharField(max_length=24, db_index=True,
                                       blank=True, verbose_name=u'手机')
    receiver_phone = models.CharField(max_length=20, db_index=True,
                                      blank=True, verbose_name=u'电话')
    # 物流信息
    buyer_id = models.BigIntegerField(db_index=True, verbose_name=u'买家ID')
    user_address_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u'地址ID')
    post_cost = models.FloatField(default=0.0, verbose_name=u'物流成本')
    is_lgtype = models.BooleanField(default=False, verbose_name=u'速递')
    lg_aging = models.DateTimeField(null=True, blank=True, verbose_name=u'速递送达时间')
    lg_aging_type = models.CharField(max_length=20, blank=True, verbose_name=u'速递类型')
    out_sid = models.CharField(max_length=64, db_index=True,
                               blank=True, verbose_name=u'物流编号')
    logistics_company = models.ForeignKey(LogisticsCompany, null=True,
                                          blank=True, verbose_name=u'物流公司')
    # 仓库信息
    weight = models.CharField(max_length=10, blank=True, verbose_name=u'包裹重量')
    is_qrcode = models.BooleanField(default=False, verbose_name=u'热敏订单')
    qrcode_msg = models.CharField(max_length=32, blank=True, verbose_name=u'打印信息')
    can_review = models.BooleanField(default=False, verbose_name=u'复审')
    priority = models.IntegerField(default=0, choices=PRIORITY_TYPE, verbose_name=u'优先级')
    operator = models.CharField(max_length=32, blank=True, verbose_name=u'打单员')
    scanner = models.CharField(max_length=64, blank=True, verbose_name=u'扫描员')
    weighter = models.CharField(max_length=64, blank=True, verbose_name=u'称重员')
    is_locked = models.BooleanField(default=False, verbose_name=u'锁定')
    is_charged = models.BooleanField(default=False, verbose_name=u'揽件')
    is_picking_print = models.BooleanField(default=False, verbose_name=u'发货单')
    is_express_print = models.BooleanField(default=False, verbose_name=u'物流单')
    is_send_sms = models.BooleanField(default=False, verbose_name=u'发货通知')
    has_refund = models.BooleanField(default=False, verbose_name=u'待退款')
    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name=u'生成日期')
    merged = models.DateTimeField(null=True, blank=True, verbose_name=u'合并日期')
    send_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    weight_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'称重日期')
    charge_time = models.DateTimeField(null=True, blank=True, verbose_name=u'揽件日期')
    remind_time = models.DateTimeField(null=True, blank=True, verbose_name=u'提醒日期')
    consign_time = models.DateTimeField(null=True, blank=True, verbose_name=u'发货日期')
    reason_code = models.CharField(max_length=100, blank=True, verbose_name=u'问题编号')  # 1,2,3 问题单原因编码集合
    redo_sign = models.BooleanField(default=False, verbose_name=u'重做标志')  # 重做标志，表示该单要进行了一次废弃的打单验货
    merge_trade_id = models.BigIntegerField(null=True, blank=True, verbose_name=u'对应的MergeTrade')
    class Meta:
        db_table = 'flashsale_package'
        app_label = 'trades'
        verbose_name = u'包裹单'
        verbose_name_plural = u'包裹列表'

    def copy_order_info(self, sale_trade):
        """从package_order或者sale_trade复制信息"""
        attrs = ['tid', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address',
                 'receiver_zip', 'receiver_mobile', 'receiver_phone', 'buyer_nick']
        for attr in attrs:
            v = getattr(sale_trade, attr)
            setattr(self, attr, v)

    def set_out_sid(self, out_sid, logistics_company_id):
        if not self.out_sid:
            self.out_sid = out_sid
            self.logistics_company_id = logistics_company_id
            self.save()

    def copy_order_info_from_merge_trade(self, merge_trade):
        attrs = ['weight', 'can_review', 'priority', 'operator', 'scanner', 'weighter', 'weight_time']
        for attr in attrs:
            val = getattr(merge_trade, attr)
            setattr(self, attr, val)

    def finish(self, mt):
        self.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
        self.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.copy_order_info_from_merge_trade(mt)
        self.save()

    def finish_scan_weight(self):
        self.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
        self.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.save()
        package_sku_items = PackageSkuItem.objects.filter(package_order_id=self.id, assign_status=PackageSkuItem.ASSIGNED)
        for sku_item in package_sku_items:
            order_num = sku_item.num
            psku = ProductSku.objects.get(id=sku_item.sku_id)
            psku.update_quantity(order_num, dec_update=True)
            psku.update_wait_post_num(order_num, dec_update=True)
            psku.update_assign_num(order_num, dec_update=True)

    @property
    def pstat_id(self):
        return str(self.buyer_id) + '-' + str(self.user_address_id) + '-' + str(self.ware_by)

    @property
    def can_merge(self):
        '''
            是否能向包裹中加入sku订单
        '''
        return self.sys_status not in [PackageOrder.WAIT_CUSTOMER_RECEIVE, PackageOrder.FINISHED_STATUS,
                                       PackageOrder.DELETE]

    @property
    def package_sku_items(self):
        return PackageSkuItem.objects.filter(package_order_id=self.id)

    @property
    def sale_orders(self):
        if not hasattr(self, '_sale_orders_'):
            from flashsale.pay.models import SaleOrder
            sale_order_ids = [p.sale_order_id for p in PackageSkuItem.objects.filter(package_order_id=self.id)]
            self._sale_orders_ = SaleOrder.objects.filter(id__in=sale_order_ids)
        return self._sale_orders_

    def reset_to_wait_prepare_send(self):
        """
            重设状态到待发货准备
        """
        if self.sys_status != PackageOrder.WAIT_PREPARE_SEND_STATUS:
            self.redo_sign = True
            self.sys_status = PackageOrder.WAIT_PREPARE_SEND_STATUS
            self.out_sid = ''
            self.logistic_company_id = None
            self.save()

    @staticmethod
    def get_or_create(id, sale_trade):
        if not PackageOrder.objects.filter(id=id).exists():
            package_order = PackageOrder()
            package_order.copy_order_info(sale_trade)
            package_order.save()
            new_create = True
        else:
            package_order = PackageOrder.objects.get(id=id)
            new_create = False
        return package_order, new_create

    def sync_merge_trade(self, merge_trade):
        """出库时同步实际数据于理论数据，如果需要就产生新包裹"""
        # TODO@hy 在本次代码上线而自动拆单未完成时生效
        from flashsale.pay.models import SaleOrder
        for sale_order in SaleOrder.objects.filter(package_order_id=self.id):
            if sale_order.status == SaleOrder.WAIT_BUYER_CONFIRM_GOODS:
                sale_order.assign_status = SaleOrder.FINISHED
                sale_order.save()
        pstat = PackageStat.objects.get(id=self.pstat_id)
        pstat.num += 1
        pstat.save()
        now_num = pstat.num + 1
        new_id = str(pstat.id) + '-' + str(now_num)
        if SaleOrder.objects.filter(package_order_id=self.id).exclude(assign_status=SaleOrder.FINISHED).exists():
            package_order = PackageOrder.objects.create(pid=new_id,
                                                        ware_by=self.ware_by,
                                                        buyer_id=self.buyer_id,
                                                        user_address_id=self.user_address_id)
            package_order.copy_order_info(self)
            package_order.save()
            for sale_order in SaleOrder.objects.filter(package_order_id=self.id).exclude(
                    assign_status=SaleOrder.FINISHED):
                sale_order.package_order_id = new_id
                sale_order.save()
        self.merge_trade_id = merge_trade.id
        self.save()


    def get_merge_trade(self, sync=True):
        from shopback.trades.models import MergeTrade
        if self.merge_trade_id:
            return MergeTrade.objects.get(id=self.merge_trade_id)
        if not sync:
            if MergeTrade.objects.filter(tid=self.tid).exists():
                return MergeTrade.objects.filter(tid=self.tid).order_by('-sys_status').first()
        return None


    @staticmethod
    def gen_new_package_id(buyer_id, address_id, ware_by_id):
        id = str(buyer_id) + '-' + str(address_id) + '-' + str(ware_by_id)
        pstat = PackageStat.objects.get_or_create(id=id)[0]
        now_num = pstat.num + 1
        return id + '-' + str(now_num)


def get_logistics_company(sender, instance, created, **kwargs):
    from shopback.logistics import tasks
    if created:
        tasks.task_get_logistics_company.delay(instance)


def sync_merge_trade_by_package(sender, instance, created, **kwargs):
    if created:
        merge_trade = MergeTrade()
        merge_trade.sync_attr_from_package(instance)
    elif instance.merge_trade_id:
        merge_trade = MergeTrade.objects.get(id=instance.merge_trade_id)
        merge_trade.sync_attr_from_package(instance)
    merge_trade.save()
    return


post_save.connect(get_logistics_company, sender=PackageOrder)
# post_save.connect(sync_merge_trade_by_package, sender=PackageOrder)


def create_merge_order(merge_trade, sku_item):
    MergeOrder.objects
    pass


def is_merge_trade_package_order_diff(package):
    merge_trade = package.get_merge_trade()
    # package_sku_items = package.package_sku_items
    # sale_order_ids = set([i.sale_order_id for i in package_sku_items])
    sale_order_ids = set([p.sale_order_id for p in PackageSkuItem.objects.filter(package_order_id=package.id)])
    sale_order_ids2 = set([mo.sale_order.id for mo in merge_trade.normal_orders])
    return sale_order_ids == sale_order_ids2


def sync_merge_trade_by_package_after_order_express(package):
    pass
    # '''
    #     merge_trade出库
    #     利用package_order，创建新的merge_trade
    # :param package:
    # :return:
    # '''
    #
    # if not is_merge_trade_package_order_diff(package):
    #     merge_trade = package.get_merge_trade()
    # else:
    #     merge_trade =
    #
    # merge_trade = MergeTrade()
    # merge_trade.sync_attr_from_package(package)
    # merge_trade.save()
    # package.merge_trade_id = merge_trade
    # for sku_item in package.package_sku_items:
    #     merge_order = create_merge_order(merge_trade, sku_item)
    #     merge_order.save()


class PackageStat(models.Model):
    id = models.CharField(max_length=95, verbose_name=u'收货处', primary_key=True)
    num = models.IntegerField(default=0, verbose_name=u'已发数')

    class Meta:
        db_table = 'flashsale_package_stat'
        app_label = 'trades'
        verbose_name = u'包裹发送计数'
        verbose_name_plural = u'包裹发送计数列表'

from core.models import BaseModel


class PackageSkuItem(BaseModel):
    sale_order_id = models.IntegerField(unique=True, verbose_name=u'SaleOrder ID')
    num = models.IntegerField(default=0, verbose_name=u'商品数量')
    package_order_id = models.CharField(max_length=100, blank=True, db_index=True, null=True, verbose_name=u'所属包裹订单')

    REAL_ORDER_GIT_TYPE = 0  # 实付
    CS_PERMI_GIT_TYPE = 1  # 赠送
    OVER_PAYMENT_GIT_TYPE = 2  # 满就送
    COMBOSE_SPLIT_GIT_TYPE = 3  # 拆分
    RETURN_GOODS_GIT_TYPE = 4  # 退货
    CHANGE_GOODS_GIT_TYPE = 5  # 换货
    ITEM_GIFT_TYPE = 6  # 买就送
    GIFT_TYPE = (
        (REAL_ORDER_GIT_TYPE, u'实付'),
        (CS_PERMI_GIT_TYPE, u'赠送'),
        (OVER_PAYMENT_GIT_TYPE, u'满就送'),
        (COMBOSE_SPLIT_GIT_TYPE, u'拆分'),
        (RETURN_GOODS_GIT_TYPE, u'退货'),
        (CHANGE_GOODS_GIT_TYPE, u'换货'),
        (ITEM_GIFT_TYPE, u'买就送'),
    )

    gift_type = models.IntegerField(choices=GIFT_TYPE, default=REAL_ORDER_GIT_TYPE, verbose_name=u'类型')
    NOT_ASSIGNED = 0
    ASSIGNED = 1
    FINISHED = 2
    CANCELED = 3
    ASSIGN_STATUS = (
        (NOT_ASSIGNED, u'待分配'),
        (ASSIGNED, u'已分配'),
        (FINISHED, u'已出货'),
        (CANCELED, u'已取消')
    )
    ware_by = models.IntegerField(default=WARE_SH, choices=WARE_CHOICES,
                                  db_index=True, verbose_name=u'所属仓库')

    assign_status = models.IntegerField(choices=ASSIGN_STATUS, default=NOT_ASSIGNED, db_index=True, verbose_name=u'状态')
    status = models.CharField(max_length=32, choices=TAOBAO_ORDER_STATUS, blank=True, verbose_name=u'订单状态')
    sys_status = models.CharField(max_length=32,
                                  choices=SYS_ORDER_STATUS,
                                  blank=True,
                                  default=pcfg.IN_EFFECT,
                                  verbose_name=u'系统状态')
    refund_status = models.IntegerField(choices=pay.REFUND_STATUS,
                                        default=pay.NO_REFUND,
                                        blank=True, verbose_name='退款状态')

    cid = models.BigIntegerField(null=True, verbose_name=u'商品分类')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'商品标题')
    price = models.FloatField(default=0.0, verbose_name=u'单价')

    sku_id = models.CharField(max_length=20, blank=True, db_index=True, verbose_name=u'规格ID')
    outer_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')
    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格ID')

    total_fee = models.FloatField(default=0.0, verbose_name=u'总费用')
    payment = models.FloatField(default=0.0, verbose_name=u'实付款')
    discount_fee = models.FloatField(default=0.0, verbose_name=u'折扣')
    adjust_fee = models.FloatField(default=0.0, verbose_name=u'调整费用')

    sku_properties_name = models.CharField(max_length=256, blank=True,
                                           verbose_name=u'购买规格')

    class Meta:
        db_table = 'flashsale_package_sku_item'
        verbose_name = u'sku包裹单'
        verbose_name_plural = u'sku包裹单列表'

    @property
    def sale_order(self):
        if not hasattr(self, '_sale_order_'):
            from flashsale.pay.models import SaleOrder
            self._sale_order_ = SaleOrder.objects.get(id=self.sale_order_id)
        return self._sale_order_

    @property
    def sale_trade(self):
        if not hasattr(self, '_sale_trade_'):
            self._sale_trade_ = self.sale_order.sale_trade
        return self._sale_trade_

    @property
    def product_sku(self):
        if not hasattr(self, '_product_sku_'):
            self._product_sku_ = ProductSku.objects.get(id=self.sku_id)
        return self._product_sku_

    def is_finished(self):
        return self.assign_status == PackageSkuItem.FINISHED


def update_product_sku_assign_num(sender, instance, created, **kwargs):
    #if instance.assign_status == PackageSkuItem.NOT_ASSIGNED:
    from shopback.items.tasks import task_update_product_sku_assign_num
    task_update_product_sku_assign_num.delay(instance.sku_id)


post_save.connect(update_product_sku_assign_num, sender=PackageSkuItem, dispatch_uid='post_save_update_product_sku_assign_num')


def packagize_sku_item(sender, instance, created, **kwargs):
    from shopback.trades.tasks import task_packagize_sku_item
    task_packagize_sku_item.delay(instance)

post_save.connect(packagize_sku_item, sender=PackageSkuItem, dispatch_uid='post_save_packagize_sku_item')
