# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django_statsd.clients import statsd
from django.db.models import Sum, F, Count, FloatField

from shopmanager import celery_app as app

from flashsale.coupon.models import CouponTransferRecord, TransferCouponDetail, UserCoupon
from flashsale.xiaolumm.models import OrderCarry
from flashsale.xiaolumm.models import XiaoluCoinLog

@app.task
def task_transfer_coupon_order_statsd():
    ctr_qs = CouponTransferRecord.objects.filter(status=1, transfer_status=3)
    coupon_qs = UserCoupon.objects.filter(coupon_type=UserCoupon.TYPE_TRANSFER)

    coupon_sale_detail = coupon_qs.aggregate(
        coupon_sale_num=Count('id'), coupon_sale_amount=Sum('value'))
    coupon_sale_num    = coupon_sale_detail.get('coupon_sale_num') or 0
    coupon_sale_amount = coupon_sale_detail.get('coupon_sale_amount') or 0

    values = coupon_qs.filter(status=UserCoupon.USED).aggregate(
        coupon_used_num=Count('id'), coupon_used_amount=Sum('value'))
    coupon_used_num    = values.get('coupon_used_num') or 0
    coupon_used_amount = values.get('coupon_used_amount') or 0

    transfer_details = ctr_qs.filter(
        transfer_type=CouponTransferRecord.OUT_TRANSFER
    ).aggregate(
        transfer_count=Count('id'),
        transfer_nums=Sum('coupon_num'),
        transfer_amounts=Sum(F('coupon_num') * F('coupon_value'), output_field=FloatField()),
    )

    refund_return_num = ctr_qs.filter(transfer_type=CouponTransferRecord.OUT_CASHOUT).aggregate(
        transfer_amounts=Sum(F('coupon_num') * F('coupon_value'), output_field=FloatField())
    ).get('transfer_amounts') or 0

    exchg_order_num = ctr_qs.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER).aggregate(
        exchg_amounts=Sum(F('coupon_num') * F('coupon_value'), output_field=FloatField())
    ).get('exchg_amounts') or 0

    coupon_chained_detail = UserCoupon.objects.filter(
        coupon_type=UserCoupon.TYPE_TRANSFER, is_chained=True).exclude(status=UserCoupon.CANCEL)\
        .aggregate(chained_num=Count('id'), chained_amount=Sum('value'))

    coin_stats = XiaoluCoinLog.objects.values('subject').annotate(Sum('amount'))

    dt_str = datetime.datetime.now().strftime('%Y.%m.%d')
    statsd.gauge('xiaolumm.boutique.coupon.sale_num.%s'%dt_str, coupon_sale_num)
    statsd.gauge('xiaolumm.boutique.coupon.sale_amount.%s'% dt_str, coupon_sale_amount)
    statsd.gauge('xiaolumm.boutique.coupon.used_num.%s'% dt_str, coupon_used_num)
    statsd.gauge('xiaolumm.boutique.coupon.used_amount.%s'% dt_str, coupon_used_amount)
    statsd.gauge('xiaolumm.boutique.coupon.refund_over_amount.%s'% dt_str, refund_return_num)
    statsd.gauge('xiaolumm.boutique.coupon.exchg_order_amount.%s'% dt_str, exchg_order_num)
    statsd.gauge('xiaolumm.boutique.coupon.chained_num.%s' % dt_str, coupon_chained_detail.get('chained_num') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.chained_amount.%s' % dt_str, coupon_chained_detail.get('chained_amount') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_count.%s' % dt_str, transfer_details.get('transfer_count') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_nums.%s' % dt_str, transfer_details.get('transfer_nums') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_amounts.%s' % dt_str, transfer_details.get('transfer_amounts') or 0)

    statsd.gauge('xiaolumm.boutique.coupon.sale_num', coupon_sale_num)
    statsd.gauge('xiaolumm.boutique.coupon.sale_amount', coupon_sale_amount)
    statsd.gauge('xiaolumm.boutique.coupon.used_num', coupon_used_num)
    statsd.gauge('xiaolumm.boutique.coupon.used_amount', coupon_used_amount)
    statsd.gauge('xiaolumm.boutique.coupon.refund_over_amount', refund_return_num)
    statsd.gauge('xiaolumm.boutique.coupon.exchg_order_amount', exchg_order_num)
    statsd.gauge('xiaolumm.boutique.coupon.chained_num', coupon_chained_detail.get('chained_num') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.chained_amount', coupon_chained_detail.get('chained_amount') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_count', transfer_details.get('transfer_count') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_nums', transfer_details.get('transfer_nums') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_amounts', transfer_details.get('transfer_amounts') or 0)

    for coin_stat in coin_stats:
        statsd.gauge('xiaolumm.boutique.coin.%s.%s'%(coin_stat['subject'], dt_str),
                     coin_stat['amount__sum'] / 100 or 0)
        statsd.gauge('xiaolumm.boutique.coin.%s'%coin_stat['subject'],
                     coin_stat['amount__sum'] / 100 or 0)


@app.task
def task_boutique_mama_statsd():
    ctr_qs = CouponTransferRecord.objects.filter(status=1)

    dt = datetime.datetime.now()
    elite_mama_count = ctr_qs.filter(
        transfer_status=CouponTransferRecord.DELIVERED
    ).values('coupon_to_mama_id').distinct().count()

    active_elite_mama_count = ctr_qs.filter(
        date_field=dt.date(),
        transfer_status=CouponTransferRecord.DELIVERED
    ).values('coupon_to_mama_id').distinct().count()

    order_mama_count = OrderCarry.objects.filter(
        date_field=dt.date(),
        status__in=(1, 2, 3),
        carry_type__in=(1, 2),
        mama_id__gt=0
    ).values_list('mama_id', flat=True).distinct().count()

    dt_str = dt.strftime('%Y.%m.%d')
    statsd.gauge('xiaolumm.boutique.mama.elite_count.%s'% dt_str, elite_mama_count)
    statsd.gauge('xiaolumm.boutique.mama.active_count.%s'% dt_str, active_elite_mama_count)
    statsd.gauge('xiaolumm.boutique.mama.ordered_count.%s'% dt_str, order_mama_count)

    statsd.gauge('xiaolumm.boutique.mama.elite_count', elite_mama_count)
    statsd.gauge('xiaolumm.boutique.mama.active_count', active_elite_mama_count)
    statsd.gauge('xiaolumm.boutique.mama.ordered_count', order_mama_count)


@app.task
def task_boutique_mama_weekly_active():
    """ 精英妈妈连续七天活跃度 """
    ctr_qs = CouponTransferRecord.objects.filter(status=1)

    dt = datetime.datetime.now()
    df = dt - datetime.timedelta(days=7)

    active_elite_mama_values_list = ctr_qs.filter(
        date_field__range=(df, dt)
    ).values_list('coupon_from_mama_id','coupon_to_mama_id')

    active_elite_mama_array = set()
    for mama_list in active_elite_mama_values_list:
        active_elite_mama_array.add(mama_list[0])
        active_elite_mama_array.add(mama_list[1])

    statsd.gauge('xiaolumm.boutique.weekly.active_mama_count', len(active_elite_mama_array))










