# 　coding:utf-8
from __future__ import unicode_literals

import datetime
import logging
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from .base import PayBaseModel

from flashsale.xiaolupay import apis as xiaolupay
from flashsale.xiaolupay.apis.v1 import envelope, transfers
from flashsale.xiaolupay.models.weixin_red_envelope import WeixinRedEnvelope

logger = logging.getLogger(__name__)


class Envelop(PayBaseModel):
    WXPUB = 'wx_pub'
    WX_TRANSFER = 'transfer'
    ENVELOP_CHOICES = (
        (WXPUB, u'微信公众红包'),
        (WX_TRANSFER, u'微信企业转账'),
    )

    WAIT_SEND = 'wait'
    CONFIRM_SEND = 'confirm'
    CANCEL = 'cancel'
    FAIL = 'fail'

    STATUS_CHOICES = ((WAIT_SEND, u'待发送'),
                      (CONFIRM_SEND, u'已发送'),
                      (FAIL, u'发送失败'),
                      (CANCEL, u'已取消'),)

    CASHOUT = 'cashout'
    ORDER_RED_PAC = 'ordred'
    XLAPP_CASHOUT = 'xlapp'
    LEVEL_1 = 'level1'
    LEVEL_2 = 'level2'
    SUBJECT_CHOICES = (
        (CASHOUT, u'妈妈余额提现'),
        (ORDER_RED_PAC, u'订单红包'),
        (XLAPP_CASHOUT, u'个人零钱提现'),
        (LEVEL_1, u'一级推荐人'),
        (LEVEL_2, u'二级推荐人')
    )

    UNSEND = 'unsend'
    SENDING = 'sending'
    SENT = 'sent'
    SEND_FAILED = 'failed'
    RECEIVED = 'received'
    REFUND = 'refund'

    SEND_STATUS_CHOICES = (
        (UNSEND, u'待发放'),
        (SENDING, u'发放中'),
        (SENT, u'已发放待领取'),
        (SEND_FAILED, u'发放失败'),
        (RECEIVED, u'已领取'),
        (REFUND, u'已退款'),)

    VALID_SEND_STATUS = (SENDING, SENT, RECEIVED)

    envelop_id = models.CharField(max_length=28, blank=True, db_index=True, verbose_name=u'红包ID')

    amount = models.IntegerField(default=0, verbose_name=u'红包金额')

    platform = models.CharField(max_length=8, db_index=True, choices=ENVELOP_CHOICES, verbose_name=u'红包发放类型')
    livemode = models.BooleanField(default=True, verbose_name=u'是否有效')

    recipient = models.CharField(max_length=28, db_index=True, verbose_name=u'接收者OPENID')
    receiver = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'用户标识')

    subject = models.CharField(max_length=8, db_index=True, choices=SUBJECT_CHOICES, verbose_name=u'红包主题')
    body = models.CharField(max_length=128, blank=True, verbose_name=u'红包祝福语')
    description = models.CharField(max_length=255, blank=True, verbose_name=u'备注信息')

    status = models.CharField(max_length=8, db_index=True, default=WAIT_SEND,
                              choices=STATUS_CHOICES, verbose_name=u'状态')

    send_status = models.CharField(max_length=8, db_index=True, default=UNSEND,
                                   choices=SEND_STATUS_CHOICES, verbose_name=u'发送状态')

    referal_id = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'引用ID')
    send_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'发送时间')

    class Meta:
        db_table = 'flashsale_envelop'
        app_label = 'xiaolumm'
        verbose_name = u'微信/红包'
        verbose_name_plural = u'微信/红包列表'

    def __unicode__(self):
        return '%s' % (self.id)

    @property
    def amount_cash(self):
        return self.amount / 100.0

    def get_amount_display(self):
        return self.amount_cash

    get_amount_display.allow_tags = True
    get_amount_display.admin_order_field = 'amount'
    get_amount_display.short_description = u"红包金额"

    def handle_envelop_by_pingpp(self, envelopd):
        """
        envelopd为pingpp的返回结果
        用于新微信红包接口替换ping++接口时处理旧的ping++红包时使用
        """
        from flashsale.pay.models import BudgetLog
        from flashsale.xiaolumm.models import CashOut

        now = datetime.datetime.now()
        status = envelopd['status']
        self.envelop_id = envelopd['id']
        self.livemode = envelopd['livemode']
        self.send_status = status

        delta_hours = self.send_time and ((now - self.send_time).total_seconds() / (60*60)) or 0
        # 超过72小时，一直是发送中，则退回用户账户。
        # ping++接口bug，微信拦截风险账号的红包，状态一直是发放中，不会改变，红包默认24小时不领取会退回
        if status == self.SENDING and delta_hours > 72:
            self.status = Envelop.FAIL
            self.refund_envelop()
            self.save()
            return

        if status in (self.SENDING, self.SENT, self.RECEIVED):
            self.send_time = self.send_time or now
            self.status = Envelop.CONFIRM_SEND

            if self.subject == Envelop.XLAPP_CASHOUT:
                blog = BudgetLog.objects.filter(id=self.referal_id)
                blog.confirm_budget_log()
            elif self.subject == Envelop.CASHOUT:
                cashout = CashOut.objects.filter(id=self.referal_id).first()
                cashout.approve_cashout() if cashout else None

        elif status in (self.SEND_FAILED, self.REFUND):
            self.status = Envelop.FAIL
            self.refund_envelop()
            logger.info({
                'action': 'envelop',
                'status': self.status,
                'enveop_id': self.envelop_id,
                'mama_id': self.receiver
            })
        self.save()

    def handle_envelop(self, envelopd):
        """
        envelopd => flashsale.xiaolupay.models.weixin_red_envelope.WeixinRedEnvelope
        """
        from flashsale.pay.models import BudgetLog
        from flashsale.xiaolumm.models import CashOut

        now = datetime.datetime.now()
        status = envelopd.status
        self.envelop_id = envelopd.mch_billno
        self.send_status = status.lower()

        if status in (WeixinRedEnvelope.SENDING, WeixinRedEnvelope.SENT, WeixinRedEnvelope.RECEIVED):
            self.send_time = self.send_time or now
            self.status = Envelop.CONFIRM_SEND

            if self.subject == Envelop.XLAPP_CASHOUT:
                bg = BudgetLog.objects.filter(id=self.referal_id).first()
                bg.confirm_budget_log() if bg else None

            if self.subject == Envelop.CASHOUT:
                cashout = CashOut.objects.filter(id=self.referal_id).first()
                cashout.approve_cashout() if cashout else None

        elif status in (WeixinRedEnvelope.FAILED, WeixinRedEnvelope.REFUND):
            self.status = Envelop.FAIL
            self.refund_envelop()
            logger.info({
                'action': 'envelop',
                'status': self.status,
                'enveop_id': self.envelop_id,
                'mama_id': self.receiver
            })
        self.save()

    def send_envelop_by_pingpp(self):
        if self.envelop_id:
            redenvelope = xiaolupay.RedEnvelope.retrieve(self.envelop_id)
            self.handle_envelop_by_pingpp(redenvelope)
        else:
            try:
                redenvelope = xiaolupay.RedEnvelope.create(
                    order_no=str(self.id),
                    channel=self.platform,
                    amount=self.amount,
                    subject=self.get_subject_display(),
                    body=self.body,
                    currency='cny',
                    app=dict(id=settings.PINGPP_APPID),
                    extra=dict(nick_name=u'上海己美网络科技', send_name=u'你的铺子'),
                    recipient=self.recipient,
                    description=self.description
                )
            except Exception, exc:
                self.status = Envelop.FAIL
                self.save()
                self.refund_envelop()
                raise exc
            else:
                self.handle_envelop_by_pingpp(redenvelope)

    def send_envelop(self):
        from flashsale.pay.models import BudgetLog

        if self.envelop_id or self.status != Envelop.WAIT_SEND:
            raise Exception(u'不能重复发送')

        envelope_unikey = 'xlmm%s' % (self.id)
        if self.platform == Envelop.WX_TRANSFER:
            flow_amount = self.amount
            name = self.body
            desc = u'你的铺子提现'
            trade_id = envelope_unikey

            try:
                success = transfers.transfer(self.recipient, name, flow_amount, desc, trade_id)
                if success:
                    self.status = Envelop.CONFIRM_SEND
                    self.send_status = Envelop.RECEIVED
                    self.send_time = datetime.datetime.now()
                    self.envelop_id = trade_id
                    self.save()
                    bg = BudgetLog.objects.filter(id=self.referal_id).first()
                    bg.confirm_budget_log() if bg else None
                else:
                    self.status = Envelop.FAIL
                    self.send_status = Envelop.SEND_FAILED
                    self.send_time = datetime.datetime.now()
                    self.envelop_id = trade_id
                    self.save()
                    self.refund_envelop()
            except Exception, exc:
                logger.error('转账错误%s' % exc, exc_info=True)
        else:
            try:
                redenvelope = envelope.create(
                    order_no=envelope_unikey,
                    amount=self.amount,
                    subject=self.get_subject_display(),
                    body=self.body,
                    recipient=self.recipient,
                    remark=self.description
                )
                self.status = Envelop.CONFIRM_SEND
                self.save()
            except Exception, exc:
                self.status = Envelop.FAIL
                self.save()
                self.refund_envelop()
                raise exc
            else:
                self.handle_envelop(redenvelope)

    def refund_envelop(self):
        from flashsale.pay.models import BudgetLog
        from flashsale.xiaolumm.models import CashOut

        # 你的铺子钱包提现
        if self.subject == self.XLAPP_CASHOUT:
            bg = BudgetLog.objects.get(id=self.referal_id, budget_log_type=BudgetLog.BG_CASHOUT)
            bg.confirm_budget_log()
            BudgetLog.create(bg.customer_id, BudgetLog.BUDGET_IN, bg.flow_amount, BudgetLog.BG_CASHOUT_FAIL)

        # 妈妈钱包提现
        if self.subject == self.CASHOUT:
            cashout = CashOut.objects.filter(id=self.referal_id).first()
            if not cashout:
                return
            if cashout.status == CashOut.PENDING:
                cashout.cancel_cashout()
            else:
                cashout.fail_and_return()

    def cancel_envelop(self):
        # 取消红包，同时退款
        if not self.envelop_id:  # 只有待发放状态可以取消红包
            self.status = Envelop.CANCEL
            self.save(update_fields=['status'])
            self.refund_envelop()
            return True
        return False


def push_envelop_get_msg(sender, instance, created, **kwargs):
    """ 发送红包待领取状态的时候　给妈妈及时领取推送消息　"""
    from flashsale.xiaolumm.tasks import task_push_mama_cashout_msg
    sent_status = instance.send_status
    if sent_status != Envelop.SENT:
        return
    task_push_mama_cashout_msg.delay(instance)


post_save.connect(push_envelop_get_msg, sender=Envelop)
