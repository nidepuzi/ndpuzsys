# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import calendar
import datetime
import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Sum

from core.options import get_systemoa_user
from core.options import log_action, CHANGE
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.clickrebeta.models import StatisticsShoppingByDay
from flashsale.xiaolumm.models import MamaDayStats
from flashsale.xiaolumm.models import XiaoluMama, CarryLog, OrderRedPacket, CashOut, PotentialMama
from shopapp.weixin.models import WXOrder
from shopback.trades.models import MergeTrade, MergeBuyerTrade
from flashsale.xiaolumm.signals import signal_xiaolumama_register_success

logger = logging.getLogger(__name__)

__author__ = 'meixqhi'

CLICK_REBETA_DAYS = 11
ORDER_REBETA_DAYS = 10
AGENCY_SUBSIDY_DAYS = 11
AGENCY_RECRUIT_DAYS = 1
RED_PACK_START_TIME = datetime.datetime(2015, 7, 6, 0, 0)  # 订单红包开放时间


@app.task()
def task_Push_Pending_Carry_Cash(xlmm_id=None):
    """
    将待确认金额重新计算并加入妈妈现金账户
    xlmm_id:小鹿妈妈id
    """
    # 结算订单提成
    task_Push_Pending_OrderRebeta_Cash(day_ago=ORDER_REBETA_DAYS, xlmm_id=xlmm_id)
    # 结算点击补贴
    task_Push_Pending_ClickRebeta_Cash(day_ago=CLICK_REBETA_DAYS, xlmm_id=xlmm_id)
    # 结算千元提成
    task_Push_Pending_ThousRebeta_Cash(day_ago=ORDER_REBETA_DAYS, xlmm_id=xlmm_id)

    recruit_date = datetime.date.today() - datetime.timedelta(days=AGENCY_RECRUIT_DAYS)

    c_logs = CarryLog.objects.filter(log_type__in=(  # CarryLog.CLICK_REBETA,
        # CarryLog.THOUSAND_REBETA,
        CarryLog.MAMA_RECRUIT,
        CarryLog.REFUND_OFF,
    ),
        carry_date__lte=recruit_date,
        status=CarryLog.PENDING)

    if xlmm_id:
        xlmm = XiaoluMama.objects.get(id=xlmm_id)
        c_logs = c_logs.filter(xlmm=xlmm.id)

    for cl in c_logs:
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        # 是否考试通过
        if not xlmm.exam_Passed():
            continue
        # 重新计算pre_date之前订单金额，取消退款订单提成

        # 将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        xlmm.push_carrylog_to_cash(cl)


def init_Data_Red_Packet():
    # 判断 xlmm 是否有过 首单 或者 十单  如果是的将 OrderRedPacket 状态修改过来
    xlmms = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED, agencylevel=2)

    for xlmm in xlmms:
        try:
            # 找订单
            shoppings = StatisticsShopping.objects.filter(linkid=xlmm.id, shoptime__lt=RED_PACK_START_TIME)
            if shoppings.count() >= 10:
                red_packet, state = OrderRedPacket.objects.get_or_create(xlmm=xlmm.id)
                red_packet.first_red = True  # 默认发放过首单红包
                red_packet.ten_order_red = True  # 默认发放过十单红包
                red_packet.save()
                xlmm.hasale = True
            elif shoppings.count() >= 1:
                red_packet, state = OrderRedPacket.objects.get_or_create(xlmm=xlmm.id)
                red_packet.first_red = True  # 默认发放过首单红包
                red_packet.save()
                xlmm.hasale = True

            xlmm.save()
        except Exception, exc:
            print 'exc:%s,%s' % (exc.message, xlmm.id)


def shoptime_To_DateStr(shoptime):
    return shoptime.strftime("%Y-%m-%d")


def buyer_Num(xlmm, finish=False):
    if finish is False:
        shops = StatisticsShopping.objects.filter(linkid=xlmm).exclude(status=StatisticsShopping.REFUNDED)
    else:
        shops = StatisticsShopping.objects.filter(linkid=xlmm, status=StatisticsShopping.FINISHED)
    t_dict = {}
    for p in shops:
        shop_time = shoptime_To_DateStr(p.shoptime)
        if shop_time in t_dict:
            t_dict[shop_time].append(p.openid)
        else:
            t_dict[shop_time] = [p.openid]
    buyercount = 0
    for k, v in t_dict.items():
        buyercount += len(set(v))
    return buyercount


@transaction.atomic
def order_Red_Packet_Pending_Carry(xlmm, target_date):
    today = datetime.date.today()
    if today < RED_PACK_START_TIME.date():
        return  # 开始时间之前 不执行订单红包
    # 2015-07-04 上午  要求修改为pending状态
    # 2015-07-04 要求 修改不使用红包（Envelop）， 使用CarryLog
    endtime = datetime.datetime(2015, 8, 25, 0, 0, 0)

    mama = XiaoluMama.objects.get(id=xlmm)
    # 第二批代理升级后是不发首单和十单红包　　这里要判断　接管时间　8月25　之后的妈妈　不去发放红包
    if mama.agencylevel != 2 or not mama.charge_time or mama.charge_time > endtime:
        return
    red_packet, state = OrderRedPacket.objects.get_or_create(xlmm=xlmm)
    # 据要求2015-07-11 修改为 按照人数来发放红包
    buyercount = buyer_Num(xlmm, finish=False)
    if red_packet.first_red is False and mama.agencylevel == 2 and mama.charge_status == XiaoluMama.CHARGED:
        # 判断 xlmm 在 OrderRedPacket 中的首单状态  是False 则执行下面的语句
        if buyercount >= 1:
            # 写CarryLog记录，一条IN（生成红包）
            order_red_carry_log = CarryLog(xlmm=xlmm, value=880, buyer_nick=mama.weikefu,
                                           log_type=CarryLog.ORDER_RED_PAC,
                                           carry_type=CarryLog.CARRY_IN, status=CarryLog.PENDING,
                                           carry_date=today)
            order_red_carry_log.save()  # 保存
            red_packet.first_red = True  # 已经发放首单红包
            red_packet.save()  # 保存红包状态
    if red_packet.ten_order_red is False and mama.agencylevel == 2 and mama.charge_status == XiaoluMama.CHARGED:
        #  判断 xlmm 在 OrderRedPacket 中的十单状态 是False 则执行下面语句
        if buyercount >= 10:
            # 写CarryLog记录，一条IN（生成红包）
            order_red_carry_log = CarryLog(xlmm=xlmm, value=1880, buyer_nick=mama.weikefu,
                                           log_type=CarryLog.ORDER_RED_PAC,
                                           carry_type=CarryLog.CARRY_IN, status=CarryLog.PENDING,
                                           carry_date=today)
            order_red_carry_log.save()  # 保存
            red_packet.first_red = True  # 已经发放首单红包
            red_packet.ten_order_red = True  # 已经发放10单红包
            red_packet.save()  # 保存红包状态


@transaction.atomic
def order_Red_Packet(xlmm):
    mama = XiaoluMama.objects.get(id=xlmm)
    if mama.can_send_redenvelop():
        # 寻找该妈妈以前的首单/十单红包记录
        red_pac_carry_logs = CarryLog.objects.filter(xlmm=xlmm, log_type=CarryLog.ORDER_RED_PAC,
                                                     carry_type=CarryLog.CARRY_IN)
        buyercount = buyer_Num(xlmm, finish=True)
        if buyercount >= 10:
            for red_pac_carry_log in red_pac_carry_logs:
                if red_pac_carry_log.status == CarryLog.PENDING:  # 如果是PENDING则修改
                    mama.push_carrylog_to_cash(red_pac_carry_log)

        if buyercount >= 1 and buyercount < 10:
            for red_pac_carry_log in red_pac_carry_logs:
                if red_pac_carry_log.value == 880 and red_pac_carry_log.status == CarryLog.PENDING:
                    mama.push_carrylog_to_cash(red_pac_carry_log)


@app.task()
def task_Update_Xlmm_Order_By_Day(xlmm, target_date):
    """
    更新每天妈妈订单状态及提成
    xlmm_id:小鹿妈妈id，
    target_date：计算日期
    """
    from flashsale.clickrebeta.tasks import update_Xlmm_Shopping_OrderStatus

    time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
    time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    shoping_orders = StatisticsShopping.objects.filter(linkid=xlmm, shoptime__range=(time_from, time_to))
    # 更新小鹿妈妈交易订单状态
    update_Xlmm_Shopping_OrderStatus(shoping_orders)

    try:
        order_Red_Packet(xlmm)
    except Exception, exc:
        logger.error(exc.message or 'Order Red Packet Error', exc_info=True)


@app.task()
def task_Push_Pending_ClickRebeta_Cash(day_ago=CLICK_REBETA_DAYS, xlmm_id=None):
    """
    计算待确认点击提成并计入妈妈现金帐号
    xlmm_id:小鹿妈妈id，
    day_ago：计算时间 = 当前时间 - 前几天
    """
    from flashsale.clickcount.tasks import calc_Xlmm_ClickRebeta
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)
    c_logs = CarryLog.objects.filter(log_type=CarryLog.CLICK_REBETA,
                                     carry_date__lte=pre_date,
                                     status=CarryLog.PENDING,
                                     carry_type=CarryLog.CARRY_IN)

    if xlmm_id:
        c_logs = c_logs.filter(xlmm=xlmm_id)

    for cl in c_logs:
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        #         #是否考试通过
        #         if not xlmm.exam_Passed():
        #             continue

        # 重新计算pre_date之前订单金额，取消退款订单提成
        carry_date = cl.carry_date
        task_Update_Xlmm_Order_By_Day(xlmm.id, carry_date)

        time_from = datetime.datetime(carry_date.year, carry_date.month, carry_date.day)
        time_to = datetime.datetime(carry_date.year, carry_date.month, carry_date.day, 23, 59, 59)

        click_rebeta = calc_Xlmm_ClickRebeta(xlmm, time_from, time_to)

        clog = CarryLog.objects.get(id=cl.id)
        if clog.status != CarryLog.PENDING:
            continue
        # 将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        clog.value = click_rebeta
        clog.save()
        xlmm.push_carrylog_to_cash(clog)


@app.task()
def task_Push_Pending_OrderRebeta_Cash(day_ago=ORDER_REBETA_DAYS, xlmm_id=None):
    """
    计算待确认订单提成并计入妈妈现金帐号
    xlmm_id:小鹿妈妈id，
    day_ago：计算时间 = 当前时间 - 前几天
    """
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)

    c_logs = CarryLog.objects.filter(log_type=CarryLog.ORDER_REBETA,
                                     carry_date__lte=pre_date,
                                     status=CarryLog.PENDING,
                                     carry_type=CarryLog.CARRY_IN)

    if xlmm_id:
        c_logs = c_logs.filter(xlmm=xlmm_id)

    for cl in c_logs:

        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        # 是否考试通过
        if not xlmm.exam_Passed():
            continue

        # 重新计算pre_date之前订单金额，取消退款订单提成
        carry_date = cl.carry_date
        task_Update_Xlmm_Order_By_Day(xlmm.id, carry_date)

        time_from = datetime.datetime(carry_date.year, carry_date.month, carry_date.day)
        time_to = datetime.datetime(carry_date.year, carry_date.month, carry_date.day, 23, 59, 59)
        shopings = StatisticsShopping.objects.filter(linkid=xlmm.id,
                                                     status__in=(
                                                         StatisticsShopping.WAIT_SEND, StatisticsShopping.FINISHED),
                                                     shoptime__range=(time_from, time_to))

        rebeta_fee = shopings.aggregate(total_rebeta=Sum('tichengcount')).get('total_rebeta') or 0
        # 将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        clog = CarryLog.objects.get(id=cl.id)
        if clog.status != CarryLog.PENDING:
            continue

        clog.value = rebeta_fee
        clog.save()

        xlmm.push_carrylog_to_cash(cl)


@app.task()
def task_Push_Pending_AgencyRebeta_Cash(day_ago=AGENCY_SUBSIDY_DAYS, xlmm_id=None):
    """
    计算代理贡献订单提成
    xlmm_id:小鹿妈妈id，
    day_ago：计算时间 = 当前时间 - 前几天
    """
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)

    c_logs = CarryLog.objects.filter(log_type=CarryLog.AGENCY_SUBSIDY,
                                     carry_date__lte=pre_date,
                                     status=CarryLog.PENDING,
                                     carry_type=CarryLog.CARRY_IN)

    if xlmm_id:
        c_logs = c_logs.filter(xlmm=xlmm_id)

    for cl in c_logs:
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        # 是否考试通过
        if not xlmm.exam_Passed():
            continue

        # 重新计算pre_date之前订单金额，取消退款订单提成
        carry_date = cl.carry_date
        time_from = datetime.datetime(carry_date.year, carry_date.month, carry_date.day)
        time_to = datetime.datetime(carry_date.year, carry_date.month, carry_date.day, 23, 59, 59)
        shopings = StatisticsShopping.objects.filter(linkid=cl.order_num,
                                                     status__in=(
                                                         StatisticsShopping.WAIT_SEND, StatisticsShopping.FINISHED),
                                                     shoptime__range=(time_from, time_to))

        calc_fee = shopings.aggregate(total_amount=Sum('rebetamount')).get('total_amount') or 0
        agency_rebeta_rate = xlmm.get_Mama_Agency_Rebeta_Rate()
        agency_rebeta = calc_fee * agency_rebeta_rate

        clog = CarryLog.objects.get(id=cl.id)
        if clog.status != CarryLog.PENDING:
            continue
        # 将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户

        clog.value = agency_rebeta
        clog.save()

        xlmm.push_carrylog_to_cash(clog)


### 代理提成表 的task任务  每个月 8号执行 计算 订单成交额超过1000人民币的提成
def calc_Mama_Thousand_Rebeta(xlmm, start, end):
    # 千元补贴
    shoppings = StatisticsShopping.objects.filter(
        linkid=xlmm.id,
        shoptime__range=(start, end),
        status__in=(StatisticsShopping.WAIT_SEND, StatisticsShopping.FINISHED)
    )
    # 过去一个月的成交额
    sum_wxorderamount = shoppings.aggregate(total_order_amount=Sum('rebetamount')).get('total_order_amount') or 0

    return sum_wxorderamount


@app.task()
def task_ThousandRebeta(date_from, date_to):
    """
    计算千元提成
    date_from: 开始日期，
    date_to：结束日期
    """
    carry_no = date_from.strftime('%y%m%d')
    xlmms = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED)
    for xlmm in xlmms:
        commission = calc_Mama_Thousand_Rebeta(xlmm, date_from, date_to)
        c_logs = CarryLog.objects.filter(xlmm=xlmm.id, order_num=carry_no, log_type=CarryLog.THOUSAND_REBETA)
        if c_logs.count() > 0 or commission >= xlmm.get_Mama_Thousand_Target_Amount() * 100:  # 分单位
            # 写一条carry_log记录
            carry_log, state = CarryLog.objects.get_or_create(xlmm=xlmm.id, order_num=carry_no,
                                                              log_type=CarryLog.THOUSAND_REBETA)
            if not state and carry_log.status != CarryLog.PENDING:
                continue

            carry_log.buyer_nick = xlmm.mobile
            carry_log.carry_type = CarryLog.CARRY_IN
            carry_log.value = commission * xlmm.get_Mama_Thousand_Rate()  # 上个月的千元提成
            carry_log.buyer_nick = xlmm.mobile
            carry_log.status = CarryLog.PENDING
            carry_log.save()


def get_pre_month(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


@app.task
def task_Calc_Month_ThousRebeta(pre_month=1):
    """
    按月计算千元代理提成
    pre_month:计算过去第几个月
    """
    today = datetime.datetime.now()
    year, month = today.year, today.month
    for m in range(pre_month):
        year, month = get_pre_month(year, month)

    month_range = calendar.monthrange(year, month)

    date_from = datetime.datetime(year, month, 1, 0, 0, 0)
    date_to = datetime.datetime(year, month, month_range[1], 23, 59, 59)

    task_ThousandRebeta(date_from, date_to)


@app.task()
def task_Push_Pending_ThousRebeta_Cash(day_ago=ORDER_REBETA_DAYS, xlmm_id=None):
    """
    计算待确认千元提成并计入妈妈现金帐号
    xlmm_id:小鹿妈妈id，
    day_ago：计算时间 = 当前时间 - 前几天
    """
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)

    c_logs = CarryLog.objects.filter(log_type=CarryLog.THOUSAND_REBETA,
                                     carry_date__lte=pre_date,
                                     status=CarryLog.PENDING,
                                     carry_type=CarryLog.CARRY_IN)

    if xlmm_id:
        c_logs = c_logs.filter(xlmm=xlmm_id)

    for cl in c_logs:
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        # 是否考试通过
        if not xlmm.exam_Passed():
            continue

        # 重新计算pre_date之前订单金额，取消退款订单提成
        carry_date = cl.carry_date
        pre_year, pre_month = get_pre_month(carry_date.year, carry_date.month)

        month_range = calendar.monthrange(pre_year, pre_month)

        date_from = datetime.datetime(pre_year, pre_month, 1, 0, 0, 0)
        date_to = datetime.datetime(pre_year, pre_month, month_range[1], 23, 59, 59)

        thousand_rebeta = calc_Mama_Thousand_Rebeta(xlmm, date_from, date_to)
        commission_fee = thousand_rebeta * xlmm.get_Mama_Thousand_Rate()
        # 将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户

        clog = CarryLog.objects.get(id=cl.id)
        if clog.status != CarryLog.PENDING:
            continue

        clog.value = commission_fee
        clog.save()

        xlmm.push_carrylog_to_cash(cl)


### 代理提成表 的task任务   计算 每个妈妈的代理提成，上交的给推荐人的提成


@app.task()
def task_AgencySubsidy_MamaContribu(target_date):  # 每天 写入记录
    """
    计算每日代理提成
    """
    time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)  # 生成带时间的格式  开始时间
    time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)  # 停止时间

    xlmm_qs = XiaoluMama.objects.normal_queryset
    xlmms = xlmm_qs.filter(charge_status=XiaoluMama.CHARGED)  # 过滤出已经接管的类别是2的代理
    for xlmm in xlmms:
        sub_xlmms = xlmm_qs.filter(referal_from=xlmm.mobile, charge_status=XiaoluMama.CHARGED)  # 找到的本代理的子代理
        sum_wxorderamount = 0  # 昨天订单总额
        for sub_xlmm in sub_xlmms:
            # 扣除记录
            sub_shoppings = StatisticsShopping.objects.filter(linkid=sub_xlmm.id,
                                                              shoptime__range=(time_from, time_to),
                                                              status__in=(StatisticsShopping.WAIT_SEND,
                                                                          StatisticsShopping.FINISHED))
            # 过滤出子代理昨天的订单
            sum_wxorderamount = sub_shoppings.aggregate(total_order_amount=Sum('rebetamount')).get(
                'total_order_amount') or 0

            commission = sum_wxorderamount * xlmm.get_Mama_Agency_Rebeta_Rate()
            if commission == 0:  # 如果订单总额是0则不做记录
                continue

            carry_log_f, state = CarryLog.objects.get_or_create(xlmm=xlmm.id, order_num=sub_xlmm.id,
                                                                carry_date=target_date,
                                                                log_type=CarryLog.AGENCY_SUBSIDY)
            if not state and carry_log_f.status != CarryLog.PENDING:
                continue
            # carry_log_f.xlmm       = xlmm.id  # 锁定本代理
            #             carry_log_f.order_num  = sub_xlmm.id      # 这里写的是子代理的ID
            carry_log_f.buyer_nick = xlmm.mobile
            carry_log_f.carry_type = CarryLog.CARRY_IN
            carry_log_f.value = commission  # 上个月给本代理的分成
            #             carry_log_f.carry_date = target_date
            carry_log_f.status = CarryLog.PENDING
            carry_log_f.save()


@app.task
def task_Calc_Agency_Contribu(pre_day=1):
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)

    task_AgencySubsidy_MamaContribu(pre_date)


@app.task
def task_Calc_Agency_Rebeta_Pending_And_Cash():
    # 计算妈妈昨日代理贡献金额
    task_Calc_Agency_Contribu(pre_day=1)
    # 计算妈妈昨日代理确认金额
    task_Push_Pending_AgencyRebeta_Cash(day_ago=AGENCY_SUBSIDY_DAYS)


def calc_mama_roi(xlmm, dfrom, dto):
    xlmm_id = xlmm.id

    xlmm_ccs = ClickCount.objects.filter(date__range=(dfrom, dto), linkid=xlmm_id)
    valid_num = xlmm_ccs.aggregate(total_validnum=Sum('valid_num')).get('total_validnum') or 0

    xlmm_ssd = StatisticsShoppingByDay.objects.filter(tongjidate__range=(dfrom, dto), linkid=xlmm_id)
    buyer_num = xlmm_ssd.aggregate(total_buyernum=Sum('buyercount')).get('total_buyernum') or 0
    payment = xlmm_ssd.aggregate(total_amount=Sum('orderamountcount')).get('total_amount') or 0

    return valid_num, buyer_num, payment


### 代理提成表 的task任务   计算 每个妈妈的代理提成，上交的给推荐人的提成
@app.task()
def task_Calc_Mama_Lasttwoweek_Stats(pre_day=0):  # 每天 写入记录
    """
    计算每日妈妈过去两周点击转化
    """

    target_date = datetime.date.today() - datetime.timedelta(days=pre_day)

    lweek_from = target_date - datetime.timedelta(days=7)  # 生成带时间的格式  开始时间
    tweek_from = target_date - datetime.timedelta(days=14)  # 停止时间

    xlmms = XiaoluMama.objects.filter(agencylevel__gte=2)
    for xlmm in xlmms:
        lweek_ds = calc_mama_roi(xlmm, lweek_from, target_date)
        tweek_ds = calc_mama_roi(xlmm, tweek_from, target_date)

        mm_stats, state = MamaDayStats.objects.get_or_create(
            xlmm=xlmm.id, day_date=target_date)

        mm_stats.lweek_clicks = lweek_ds[0]
        mm_stats.lweek_buyers = lweek_ds[1]
        mm_stats.lweek_payment = lweek_ds[2]

        mm_stats.tweek_clicks = tweek_ds[0]
        mm_stats.tweek_buyers = tweek_ds[1]
        mm_stats.tweek_payment = tweek_ds[2]

        mm_stats.base_click_price = mm_stats.calc_click_price()
        mm_stats.save()


@app.task()
def task_Push_WXOrder_Finished(pre_days=10):
    """ 定时将待确认状态微信小店订单更新成已完成 """

    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)

    SHIP_STATUS_MAP = {WXOrder.WX_CLOSE: StatisticsShopping.REFUNDED,
                       WXOrder.WX_FINISHED: StatisticsShopping.FINISHED}
    wxorders = WXOrder.objects.filter(order_status=WXOrder.WX_WAIT_CONFIRM)
    for wxorder in wxorders:
        wxorder_id = wxorder.order_id
        mtrades = MergeTrade.objects.filter(tid=wxorder_id, type=MergeTrade.WX_TYPE)
        if mtrades.count() == 0:
            continue

        mtrade = mtrades[0]
        if (mtrade.status == MergeTrade.TRADE_CLOSED or
                    mtrade.sys_status in (MergeTrade.INVALID_STATUS, MergeTrade.EMPTY_STATUS)):
            wxorder.order_status = WXOrder.WX_CLOSE
            wxorder.save()

        elif (mtrade.sys_status == MergeTrade.FINISHED_STATUS):
            if mtrade.weight_time and mtrade.weight_time > day_date:
                continue
            # 如果父订单已称重，并且称重日期达到确认期，则系统自动将订单放入已完成
            if not mtrade.weight_time:
                merge_status = MergeBuyerTrade.getMergeType(mtrade.id)
                if merge_status != MergeBuyerTrade.SUB_MERGE_TYPE:
                    continue
                smergetrade = MergeBuyerTrade.objects.get(sub_tid=mtrade.id)
                ptrade = MergeTrade.objects.get(id=smergetrade.main_tid)
                if not ptrade.weight_time or ptrade.weight_time > day_date:
                    continue

            morders = mtrade.normal_orders.filter(oid=wxorder_id)
            if (morders.count() == 0 or
                        morders[0].status in (MergeTrade.TRADE_CLOSED,
                                              MergeTrade.TRADE_REFUNDED,
                                              MergeTrade.TRADE_REFUNDING)):
                wxorder.order_status = WXOrder.WX_CLOSE
                wxorder.save()
            else:
                wxorder.order_status = WXOrder.WX_FINISHED
                wxorder.save()

        ship_trades = StatisticsShopping.objects.filter(wxorderid=wxorder_id)
        if ship_trades.count() > 0:
            ship_trade = ship_trades[0]
            ship_trade.status = SHIP_STATUS_MAP.get(wxorder.order_status, StatisticsShopping.WAIT_SEND)
            ship_trade.save()


@app.task
def task_Update_Sale_And_Weixin_Order_Status(pre_days=10):
    task_Push_WXOrder_Finished.delay(pre_days=pre_days)

    from flashsale.pay.tasks import task_Push_SaleTrade_Finished

    task_Push_SaleTrade_Finished.delay(pre_days=pre_days)


@app.task()
def task_upgrade_mama_level_to_vip():
    """
    ### 代理升级: 提现金额大于　2000 　的A　类代理升级为 vip
    """
    sys_oa = User.objects.get(username="systemoa")
    mamas = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED,
                                      status=XiaoluMama.EFFECT,
                                      agencylevel=XiaoluMama.A_LEVEL)  # 有效的A类代理
    for mm in mamas.iterator():
        cashs = CashOut.objects.filter(xlmm=mm.id, status=CashOut.APPROVED)  # 代理提现记录　
        t_cashout_amount = cashs.aggregate(s_value=Sum('value')).get('s_value') or 0
        update_fields = []
        old_target_complete = mm.target_complete  # 原来的记录
        if mm.target_complete != t_cashout_amount / 100.0:
            mm.target_complete = t_cashout_amount / 100.0
            update_fields.append("target_complete")
        if update_fields:
            mm.save(update_fields=update_fields)
        if t_cashout_amount >= 2000 * 100:  # 如果超过2000
            mm.upgrade_agencylevel_by_cashout()
            log_action(sys_oa.id, mm, CHANGE, u'A类代理满2000元指标 %s : %s 升级' % (old_target_complete, mm.target_complete))


@app.task()
def xlmmClickTop(time_from, time_to):
    # 妈妈编号 点击数量 订单数量 购买人数 转化率（百分比） 管理员
    clics = ClickCount.objects.filter(write_time__gte=time_from, write_time__lte=time_to)
    dic = {}
    for clik in clics:
        if dic.has_key(clik.linkid):
            dic[clik.linkid] += clik.valid_num  # 有则叠加
        else:
            dic[clik.linkid] = clik.valid_num
    source_data = sorted(dic.items(), key=lambda asd: asd[1], reverse=True)
    cuttop50 = source_data[:50] if len(source_data) >= 50 else source_data
    data = []
    for cut in cuttop50:
        link_id = cut[0]
        valid_num = cut[1]
        # 订单数量
        stps = StatisticsShopping.objects.filter(linkid=link_id, status__in=(StatisticsShopping.FINISHED,
                                                                             StatisticsShopping.WAIT_SEND),
                                                 shoptime__gte=time_from, shoptime__lte=time_to)
        shop_num = stps.count()  # 订单数量
        customet_num = len(stps.values("openid").distinct())  # 购买人数
        conver_rate = customet_num / valid_num if valid_num != 0 else 0  # 转化率　＝　购买人数／有效点击
        try:
            adm = XiaoluMama.objects.get(id=link_id).manager
        except XiaoluMama.DoesNotExist:
            adm = 0
        atm_dic = {link_id: {"valid_num": valid_num, "shop_num": shop_num, "customet_num": customet_num,
                             "conver_rate": conver_rate, "adm": adm}}
        data.append(atm_dic)
    return data


@app.task()
def xlmmOrderTop(time_from, time_to):
    stps = StatisticsShopping.objects.filter(status__in=(StatisticsShopping.FINISHED,
                                                         StatisticsShopping.WAIT_SEND),
                                             shoptime__gte=time_from, shoptime__lte=time_to)
    dic = {}
    for stp in stps:
        if dic.has_key(stp.linkid):
            dic[stp.linkid] += 1  # 订单加１
        else:
            dic[stp.linkid] = 1

    source_data = sorted(dic.items(), key=lambda asd: asd[1], reverse=True)
    cuttop50 = source_data[:50] if len(source_data) >= 50 else source_data
    data = []
    for cut in cuttop50:
        link_id = cut[0]
        shop_num = cut[1]
        clics = ClickCount.objects.filter(linkid=link_id, write_time__gte=time_from, write_time__lte=time_to)
        valid_num = clics.aggregate(total_valid=Sum("valid_num")).get("total_valid") or 0
        customet_num = len(stps.filter(linkid=link_id).values("openid").distinct())
        conver_rate = customet_num / valid_num if valid_num != 0 else 0  # 转化率　＝　购买人数／有效点击
        try:
            adm = XiaoluMama.objects.get(id=link_id).manager
        except XiaoluMama.DoesNotExist:
            adm = 0
        atm_dic = {link_id: {"valid_num": valid_num, "shop_num": shop_num, "customet_num": customet_num,
                             "conver_rate": conver_rate, "adm": adm}}
        data.append(atm_dic)
    return data


@app.task()
def task_period_check_mama_renew_state():
    """
    定时检查代理是否需要续费　
    1. 如果当前时间大于下次续费时间　修改　状态到冻结状态
    """
    now = datetime.datetime.now()
    sys_oa = get_systemoa_user()

    # 续费　状态处理
    effect_elite_mms = XiaoluMama.objects.filter(
        status=XiaoluMama.EFFECT,
        charge_status=XiaoluMama.CHARGED,
        referal_from__in=[XiaoluMama.DIRECT, XiaoluMama.INDIRECT]).exclude(last_renew_type=XiaoluMama.ELITE)  # 有效并接管的
    for emm in effect_elite_mms.iterator():
        try:
            if (emm.renew_time and now >= emm.renew_time) or (not emm.renew_time):
                # 2017-2-7 精英妈妈不冻结,变为单纯精英妈妈，老的99／188妈妈冻结
                if emm.last_renew_type != XiaoluMama.ELITE:
                    emm.last_renew_type = XiaoluMama.ELITE
                    emm.save(update_fields=['last_renew_type'])
                    log_action(sys_oa, emm, CHANGE, u'schedule task: renew timeout,chg to elitemama')
        except TypeError as e:
            logger.error(u"task_period_check_mama_renew_state FROZEN mama:%s, error info: %s" % (emm.id, e))

    max_mmid = 0
    effect_no_elite_mms = XiaoluMama.objects.filter(
        status=XiaoluMama.EFFECT,
        charge_status=XiaoluMama.CHARGED).exclude(referal_from__in=[XiaoluMama.DIRECT, XiaoluMama.INDIRECT])

    max_mmid = XiaoluMama.objects.all().count()

    if effect_no_elite_mms.count() < 10000:
        for emm in effect_no_elite_mms.iterator():
            try:
                if (emm.renew_time and now >= emm.renew_time) or ((not emm.renew_time) and emm.last_renew_type < XiaoluMama.ELITE):
                    emm.status = XiaoluMama.FROZEN
                    emm.save(update_fields=['status'])
                    log_action(sys_oa, emm, CHANGE, u'schedule task: renew timeout,chg to frozen')
            except TypeError as e:
                logger.error(u"task_period_check_mama_renew_state FROZEN mama:%s, error info: %s" % (emm.id, e))
    else:
        mmid = 100000
        while True:
            effect_no_elite_mms = XiaoluMama.objects.filter(
                status=XiaoluMama.EFFECT,
                charge_status=XiaoluMama.CHARGED,
                id__lte=mmid).exclude(
                referal_from__in=[XiaoluMama.DIRECT, XiaoluMama.INDIRECT])
            for emm in effect_no_elite_mms.iterator():
                try:
                    if (emm.renew_time and now >= emm.renew_time) or (
                        (not emm.renew_time) and emm.last_renew_type < XiaoluMama.ELITE):
                        emm.status = XiaoluMama.FROZEN
                        emm.save(update_fields=['status'])
                        log_action(sys_oa, emm, CHANGE, u'schedule task: renew timeout,chg to frozen')
                except TypeError as e:
                    logger.error(u"task_period_check_mama_renew_state FROZEN mama:%s, error info: %s" % (emm.id, e))
            if mmid < max_mmid:
                mmid += 100000
            else:
                break

@app.task()
def task_mama_postphone_renew_time_by_active():
    """
    妈妈(正式)当天有活跃度情况下续费时间向后添加一天
    """
    pass
    # from flashsale.xiaolumm.models.models_fortune import ActiveValue
    # mamas = XiaoluMama.objects.filter(status=XiaoluMama.EFFECT,
    #                                  agencylevel__gte=XiaoluMama.VIP_LEVEL,
    #                                  last_renew_type=XiaoluMama.FULL,  # 年费用户才添加天数
    #                                  charge_status=XiaoluMama.CHARGED)
    # yesterday = datetime.date.today() - datetime.timedelta(days=1)
    # for mama in mamas:
    #    try:
    #        if ActiveValue.objects.filter(mama_id=mama.id, date_field=yesterday).exists():
    #            if isinstance(mama.renew_time, datetime.datetime):
    #                mama.renew_time = mama.renew_time + datetime.timedelta(days=1)
    #                mama.save(update_fields=['renew_time'])
    #    except Exception as exc:
    #        logger.info({'action': 'task_mama_postphone_renew_time_by_active',
    #                     'mama_id': mama.id,
    #                     'message': exc.message})
    #        continue


@app.task()
def task_update_trial_mama_full_member_by_condition(mama):
    """
    检查该妈妈的推荐人是否是　试用用户　
    如果是　试用用户数　
    满足邀请三个188　或者　
    这里用续费天数　判断
    """
    if True:
        return
    trial_mama = XiaoluMama.objects.filter(mobile=mama.referal_from,
                                           status=XiaoluMama.EFFECT,  # 自接管后　15天　变为冻结
                                           last_renew_type=XiaoluMama.TRIAL).first()  # 推荐人(试用用户并且是有效状态的)
    if not trial_mama:
        return
    join_mamas = XiaoluMama.objects.filter(referal_from=trial_mama.mobile,
                                           status=XiaoluMama.EFFECT,
                                           last_renew_type=XiaoluMama.FULL,  # 邀请的是188
                                           agencylevel__gte=XiaoluMama.VIP_LEVEL,
                                           charge_status=XiaoluMama.CHARGED)  # 推荐人邀请的正式妈妈
    if join_mamas.count() >= 3:  # 满足条件
        trial_mama.last_renew_type = XiaoluMama.HALF  # 转正为半年的类型
        trial_mama.renew_time = trial_mama.renew_time + datetime.timedelta(days=XiaoluMama.HALF)
        trial_mama.save(update_fields=['last_renew_type', 'renew_time'])
        sys_oa = get_systemoa_user()
        log_action(sys_oa, trial_mama, CHANGE, u'满足转正条件,转为正式妈妈')
        # 修改潜在小鹿妈妈列表中的　转正状态

        potential = PotentialMama.objects.filter(potential_mama=trial_mama.id, is_full_member=False).first()
        if potential:
            potential.is_full_member = True
            potential.save(update_fields=['is_full_member'])
            log_action(sys_oa, potential, CHANGE, u'满足转正条件,转为正式妈妈')


@app.task()
def task_update_mama_agency_level_in_condition(date=None):
    """
    1. 邀请正式总数4个（含4个）
    2. 单周销售额超过100的代理
    满足1 and 2  才升级代理等级
    """

    from flashsale.xiaolumm.models import MamaFortune, OrderCarry
    from django.db.models import Sum

    if not date:
        date = datetime.date.today() - datetime.timedelta(days=1)
    days = date.weekday()
    monday_date = date - datetime.timedelta(days=days)
    sunday_date = monday_date + datetime.timedelta(days=6)

    xlmms = XiaoluMama.objects.filter(agencylevel=XiaoluMama.A_LEVEL, charge_status=XiaoluMama.CHARGED)
    invite_gte4_mamaid = MamaFortune.objects.filter(mama_id__in=xlmms.values('id'), invite_num__gte=4).values('mama_id')
    past_week_order_value = OrderCarry.objects.filter(
        mama_id__in=invite_gte4_mamaid,
        date_field__gte=monday_date,
        date_field__lte=sunday_date,
        status__in=[OrderCarry.ESTIMATE,
                    OrderCarry.CONFIRM]).values('mama_id').annotate(
        s_order_value=Sum('order_value'))
    week_order_value_gte100 = [x['mama_id'] for x in past_week_order_value if x['s_order_value'] > 10000]

    condition_mama_ids = set(week_order_value_gte100)
    log_ids = ','.join([str(i) for i in condition_mama_ids])
    logger.info({'action': 'task_update_mama_agency_level_in_condition',
                 'condition_mama_ids': log_ids})

    xlmms = XiaoluMama.objects.filter(id__in=condition_mama_ids, agencylevel=XiaoluMama.A_LEVEL)
    xlmms.update(agencylevel=XiaoluMama.VIP_LEVEL)
