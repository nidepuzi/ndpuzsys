# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime

from django.db import models
from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)

class EliteMamaStatus(BaseModel):
    """ 精英妈妈状态 """
    NORMAL  = 0
    STAGING = 1
    FOLLOUP = 2
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (STAGING, u'待跟进'),
        (FOLLOUP, u'跟进中'),
    )

    mama_id = models.IntegerField(unique=True, verbose_name=u'妈妈ID')

    sub_mamacount   = models.IntegerField(default=0, db_index=True, verbose_name=u'下属数量')

    purchase_amount_out = models.IntegerField(default=0, db_index=True, verbose_name=u'出券面额')
    purchase_amount_in  = models.IntegerField(default=0, db_index=True, verbose_name=u'进券面额')

    transfer_amount_out = models.IntegerField(default=0, db_index=True, verbose_name=u'转出面额')
    transfer_amount_in  = models.IntegerField(default=0, db_index=True, verbose_name=u'转入面额')

    return_amount_out   = models.IntegerField(default=0, db_index=True, verbose_name=u'退还上级面额')
    return_amount_in    = models.IntegerField(default=0, db_index=True, verbose_name=u'收回下级面额')

    sale_amount_out     = models.IntegerField(default=0, db_index=True, verbose_name=u'直接买货面额')
    sale_amount_in      = models.IntegerField(default=0, db_index=True, verbose_name=u'直接出货面额')

    refund_coupon_out = models.IntegerField(default=0, db_index=True, verbose_name=u'退货出券面额')
    refund_coupon_in  = models.IntegerField(default=0, db_index=True, verbose_name=u'退货回券面额')

    refund_amount_out = models.IntegerField(default=0, db_index=True, verbose_name=u'退券面额')
    refund_amount_in  = models.IntegerField(default=0, db_index=True, verbose_name=u'回券面额')

    exchg_amount_out    = models.IntegerField(default=0, db_index=True, verbose_name=u'兑换买货面额')
    exchg_amount_in     = models.IntegerField(default=0, db_index=True, verbose_name=u'兑换出货面额')

    gift_amount_out = models.IntegerField(default=0, db_index=True, verbose_name=u'赠出面额')
    gift_amount_in  = models.IntegerField(default=0, db_index=True, verbose_name=u'赠入面额')

    saleout_rate   = models.FloatField(default=0, db_index=True, verbose_name=u'出货率')
    transfer_rate  = models.FloatField(default=0, db_index=True, verbose_name=u'转移流通率', help_text='券转移给下属比例')
    refund_rate    = models.FloatField(default=0, db_index=True, verbose_name=u'退券率')

    joined_date = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'加入时间')
    last_active_time = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'最近活跃时间')

    status = models.IntegerField(choices=STATUS_CHOICES, db_index=True, default=NORMAL, verbose_name=u'状态')
    memo   = models.TextField(max_length=1024, verbose_name=u'备注')

    class Meta:
        db_table = 'xiaolumm_elitestatus'
        app_label = 'xiaolumm'
        verbose_name = u'精英妈妈/活跃状态'
        verbose_name_plural = u'精英妈妈/活跃状态列表'

    def save(self, *args, **kwargs):
        in_amount = self.purchase_amount_in + self.transfer_amount_in + self.gift_amount_in
        if in_amount > 0:
            self.saleout_rate  = '%.4f'%((self.sale_amount_out + self.exchg_amount_out - self.refund_coupon_in) * 1.0 / in_amount)
            self.transfer_rate = '%.4f'%(max(self.transfer_amount_out - self.return_amount_in, 0) * 1.0 / in_amount)
            self.refund_rate   = '%.4f'%((self.return_amount_out + self.refund_amount_out) * 1.0 / in_amount)
            update_fields = kwargs.get('update_fields')
            if update_fields:
                update_fields.extend(['saleout_rate', 'transfer_rate', 'refund_rate'])
        return super(EliteMamaStatus, self).save(*args, **kwargs)


    def __unicode__(self):
        return u'<%s,%s>' % (self.mama_id, self.status)


class EliteMamaAwardLog(BaseModel):

    UNSEND = 'unsend'
    SEND = 'send'
    CANCEL = 'cancel'

    STATUS_CHOICES = (
        (UNSEND, u'待发放'),
        (SEND, u'已发放'),
        (CANCEL, u'已取消'),
    )

    customer_id = models.IntegerField(default=0, db_index=True, verbose_name=u"用户编号")
    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u"妈妈编号")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, db_index=True, default=UNSEND, verbose_name=u'状态')
    referal_id = models.CharField(max_length=32, blank=True, verbose_name=u'引用id')
    remark = models.CharField(max_length=255, blank=True, verbose_name=u'备注')


    class Meta:
        db_table = 'flashsale_xlmm_elitemamaawardlog'
        app_label = 'xiaolumm'
        verbose_name = u'精英妈妈奖金记录'
        verbose_name_plural = u'精英妈妈奖金记录'
