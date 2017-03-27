# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import collections
from itertools import chain
from django.db import connection
from django.db.models import Sum, Count, F

from shopmanager import celery_app as app

from core.utils.timeutils import day_range
from ..models import DailySkuDeliveryStat, DailySkuAmountStat
from flashsale.pay.models import SaleOrder, SaleTrade
from flashsale.coupon.models import UserCoupon, CouponTemplate
from shopback.items.models import ProductSku

@app.task
def task_call_all_sku_delivery_stats(stat_date=None):
    """ 统计所有订单规格sku发货天数 """
    if not stat_date:
        stat_date = datetime.date.today() - datetime.timedelta(days=1)

    post_values = SaleOrder.objects.filter(consign_time__range=day_range(stat_date))\
        .extra(select={'days': 'TIMESTAMPDIFF(DAY, pay_time, consign_time)'})\
        .values('sku_id', 'days').annotate(Sum('num'))

    wait_values = SaleOrder.objects.filter(
        status=SaleOrder.WAIT_SELLER_SEND_GOODS,
    ).extra(select={'days': 'TIMESTAMPDIFF(DAY, pay_time, NOW())'}) \
        .values('sku_id', 'days').annotate(Sum('num'))

    sku_ids  = chain([l['sku_id'] for l in post_values], [l['sku_id'] for l in wait_values])
    sku_maps = dict(ProductSku.objects.filter(id__in=list(sku_ids)).values_list('id', 'product__model_id'))

    for value in post_values:
        stat, state = DailySkuDeliveryStat.objects.get_or_create(
            sku_id=value['sku_id'], stat_date=stat_date, days=value['days'])
        stat.post_num = value['num__sum']
        stat.model_id = sku_maps.get(int(value['sku_id']))
        stat.save()

    for value in wait_values:
        stat, state = DailySkuDeliveryStat.objects.get_or_create(
            sku_id=value['sku_id'], stat_date=stat_date, days=value['days'])
        stat.wait_num = value['num__sum']
        stat.model_id = sku_maps.get(int(value['sku_id']))
        stat.save()


def task_calc_all_sku_amount_stat_by_date(stat_date=None):
    """
        统计sku销售金额
        注意: 这里统计的商品进价不考虑不同批次采购的价格波动,只根据商品sku设置的成本价计算
    """

    if not stat_date:
        stat_date = datetime.date.today() - datetime.timedelta(days=1)

    date_tuple = day_range(stat_date)
    order_qs = SaleOrder.objects.active_orders().filter(
        pay_time__range=date_tuple,
        # oid__in=('xo1701095872ca932da30', 'xo170109587354504eb5c', 'xo170109587357913f3cd', 'xo17010958739b969a09b'), # TODO@REMOVE
    )

    order_amount_query_sql = """
        SELECT so.`sku_id`,
          sum(so.`total_fee`*100),
          sum(so.`payment`*100),
          sum(so.`discount_fee`*100),
          sum(so.`payment`*st.`coin_paid`*100/ st.`payment`),
          count(so.`id`)
          FROM flashsale_order so
          LEFT JOIN flashsale_trade st on so.`sale_trade_id`= st.id
         where
           so.status != %s and
           so.`pay_time` BETWEEN %s and %s
         GROUP BY so.`sku_id`;
    """

    cursor = connection.cursor()  # 获得一个游标(cursor)对象
    # 更新操作
    cursor.execute(order_amount_query_sql, [SaleOrder.TRADE_CLOSED_BY_SYS, date_tuple[0], date_tuple[1]])
    order_stats = cursor.fetchall()

    sku_ids = [l[0] for l in order_stats]
    sku_valuelist = ProductSku.objects.filter(id__in=list(sku_ids)).values_list('id', 'cost', 'product__model_id')
    sku_model_maps = dict([(v[0], v[2]) for v in sku_valuelist])
    sku_price_maps = dict([(v[0], v[1]) for v in sku_valuelist])

    sku_tid_num_list = order_qs.values_list('sku_id', 'sale_trade__tid', 'num', 'oid')
    tid_list = []
    tid_num_maps = collections.defaultdict(dict)
    sku_tid_maps = {}
    for st in sku_tid_num_list:
        sku_id = int(st[0])
        tid = st[1]
        model_id = sku_model_maps.get(sku_id)
        tid_list.append(tid)
        tid_num_maps[tid][model_id] = (tid_num_maps[tid].get(model_id) or 0) + st[2]
        sku_tid_maps[sku_id] = tid

    tmp_pro_maps = CouponTemplate.objects.get_template_to_modelproduct_maps()
    boutique_coupon_qs = UserCoupon.objects.get_origin_payment_boutique_coupons()
    usercoupon_values = boutique_coupon_qs.filter(trade_tid__in=tid_list)\
        .values_list('template_id', 'trade_tid', 'extras')
    # TODO@TIPS 统计妈妈购买优惠券实际支付金额
    tid_origin_price_maps = {}
    tid_template_model_masp = {}
    for template_id, tid, extras in usercoupon_values:
        tid_origin_price_maps[tid] = tid_origin_price_maps.get(tid, 0) + (extras.get('origin_price') or 0)
        tid_template_model_masp[tid] = tmp_pro_maps.get(template_id)

    sku_origin_price_maps = {}
    for st in sku_tid_num_list:
        sku_id, tid, sku_num = int(st[0]), st[1], st[2]
        model_id = sku_model_maps.get(sku_id)
        sku_sum  = tid_num_maps[tid].get(model_id, 0)
        if sku_sum == 0:
            continue
        sku_origin_price_maps[sku_id] = sku_origin_price_maps.get(sku_id, 0) \
            + (sku_num * 1.0 / sku_sum) * tid_origin_price_maps.get(tid, 0)

    # TODO@TIPS 统计妈妈兑换优惠券兑出差额 = 兑出金额 - 购券金额, (兑换金额必须根据订单实际支付金额计算)
    order_exchg_maps = {}
    order_value_list = order_qs.values('oid', 'num', 'payment')
    order_payment_maps = dict([(ol['oid'], ol) for ol in order_value_list])
    exchg_coupon_qs = boutique_coupon_qs.filter(trade_tid__in=order_payment_maps.keys())
    exchg_coupon_values = exchg_coupon_qs.values_list('trade_tid', 'value', 'extras')
    order_couponnum_maps  = dict(exchg_coupon_qs.values('trade_tid').annotate(Count('id'))
                                 .values_list('trade_tid', 'id__count'))

    for oid, value, extras in exchg_coupon_values:
        order_value = order_payment_maps.get(oid)
        order_num   = order_couponnum_maps.get(oid)
        order_per_payment = order_value.get('num') > 0  and order_value.get('payment') * 100 / order_num or 0
        order_exchg_maps[oid] = order_exchg_maps.get(oid, 0) + (order_per_payment - extras.get('origin_price', 0))

    sku_exchg_maps = {}
    for st in sku_tid_num_list:
        sku_id, oid = int(st[0]), st[3]
        sku_exchg_maps[sku_id] = sku_exchg_maps.get(sku_id, 0) + order_exchg_maps.get(oid, 0)

    for value in order_stats:
        sku_id = int(value[0])
        stat, state = DailySkuAmountStat.objects.get_or_create(
            sku_id=sku_id, stat_date=stat_date
        )
        stat.total_amount   = value[1]
        stat.direct_payment = value[2]
        stat.coupon_amount  = value[3]
        stat.coin_payment   = value[4]

        stat.total_cost   = int(sku_price_maps.get(sku_id) * value[5] * 100)
        stat.model_id     = sku_model_maps.get(sku_id)
        stat.coupon_payment = sku_origin_price_maps.get(sku_id, 0)
        stat.exchg_amount   = sku_exchg_maps.get(sku_id, 0)

        stat.save()


@app.task
def task_calc_all_sku_amount_stat_by_schedule():
    """ 统计sku销售金额,由于小鹿币的兑换时间不确定,所以这里不能做任何处理 """
    # calc the last day sku_amount
    task_calc_all_sku_amount_stat_by_date(datetime.date.today() - datetime.timedelta(days=1))

    # calc the three days ago sku_amount
    task_calc_all_sku_amount_stat_by_date(datetime.date.today() - datetime.timedelta(days=3))

    # calc the fifth days ago sku_amount
    task_calc_all_sku_amount_stat_by_date(datetime.date.today() - datetime.timedelta(days=15))

    # calc the thirty days ago sku_amount
    task_calc_all_sku_amount_stat_by_date(datetime.date.today() - datetime.timedelta(days=30))



@app.task
def task_calc_today_sku_boutique_sales_delivery_stats():

    from .boutique import task_all_boutique_stats
    today = datetime.date.today()

    task_all_boutique_stats(stat_date=today)

    task_call_all_sku_delivery_stats(stat_date=today)

    task_calc_all_sku_amount_stat_by_date(stat_date=today)



