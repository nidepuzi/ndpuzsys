# coding=utf-8
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import logging
import datetime
from flashsale.xiaolumm.models import XiaoluMama
from django.db import IntegrityError

logger = logging.getLogger(__name__)


@app.task(serializer='pickle')
def task_update_tpl_released_coupon_nums(template):
    """
    template : CouponTemplate instance
    has_released_count ++ when the CouponTemplate release success.
    """
    from flashsale.coupon.models import UserCoupon

    count = UserCoupon.objects.filter(template_id=template.id).count()
    template.has_released_count = count
    template.save(update_fields=['has_released_count'])
    from django_statsd.clients import statsd
    from django.utils.timezone import now, timedelta

    start = now().date()
    end = start + timedelta(days=1)
    if template.id == 55:
        statsd.timing('coupon.new_customer_released_count',
                      UserCoupon.objects.filter(template_id=template.id, start_use_time__range=(start, end)).count())
    elif template.id == 67:
        statsd.timing('coupon.share_released_count',
                      UserCoupon.objects.filter(template_id=template.id, start_use_time__range=(start, end)).count())
    elif template.id == 86:
        statsd.timing('coupon.old_customer_share_released_count',
                      UserCoupon.objects.filter(template_id=template.id, start_use_time__range=(start, end)).count())
    return


@app.task()
def task_update_share_coupon_release_count(share_coupon):
    """
    share_coupon : OrderShareCoupon instance
    release_count ++ when the OrderShareCoupon release success
    """
    from flashsale.coupon.models import UserCoupon

    count = UserCoupon.objects.filter(order_coupon_id=share_coupon.id).count()
    share_coupon.release_count = count
    share_coupon.save(update_fields=['release_count'])
    return


@app.task()
def task_update_coupon_use_count(coupon, trade_tid):
    """
    1. count the CouponTemplate 'has_used_count' field when use coupon
    2. count the OrderShareCoupon 'has_used_count' field when use coupon
    """
    from flashsale.coupon.models import UserCoupon

    coupon.finished_time = datetime.datetime.now()  # save the finished time
    coupon.trade_tid = trade_tid  # save the trade tid with trade be binding
    coupon.save(update_fields=['finished_time', 'trade_tid'])
    tpl = coupon.self_template()

    coupons = UserCoupon.objects.all()
    tpl_used_count = coupons.filter(template_id=tpl.id, status=UserCoupon.USED).count()
    tpl.has_used_count = tpl_used_count
    tpl.save(update_fields=['has_used_count'])

    share = coupon.share_record()
    if share:
        share_used_count = coupons.filter(order_coupon_id=share.id, status=UserCoupon.USED).count()
        share.has_used_count = share_used_count
        share.save(update_fields=['has_used_count'])

    from django_statsd.clients import statsd
    from django.utils.timezone import now, timedelta

    start = now().date()
    end = start + timedelta(days=1)

    if coupon.template_id == 55:
        statsd.timing('coupon.new_customer_used_count', coupons.filter(template_id=tpl.id, status=UserCoupon.USED,
                                                                       finished_time__range=(start, end)).count())
    elif coupon.template_id == 67:
        statsd.timing('coupon.share_used_count', coupons.filter(template_id=tpl.id, status=UserCoupon.USED,
                                                                finished_time__range=(start, end)).count())
    elif coupon.template_id == 86:
        statsd.timing('coupon.old_customer_share_used_count', coupons.filter(template_id=tpl.id, status=UserCoupon.USED,
                                                                             finished_time__range=(start, end)).count())
    return


@app.task()
def task_release_coupon_for_order(saletrade):
    """
    - SaleTrade pay confirm single to drive this task.
    """
    from flashsale.coupon.models import CouponTemplate
    from ..apis.v1.usercoupon import create_user_coupon

    extras_info = saletrade.extras_info
    ufrom = extras_info.get('ufrom')
    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_ORDER_BENEFIT).first()
    if not tpl:
        return
    create_user_coupon(customer_id=saletrade.buyer_id, coupon_template_id=tpl.id, trade_id=saletrade.id,
                       ufrom=str(ufrom))


@app.task()
def task_freeze_coupon_by_refund(salerefund):
    """
    - SaleRefund refund signal to drive this task.
    """
    from flashsale.coupon.models import UserCoupon

    trade_tid = salerefund.get_tid()
    cous = UserCoupon.objects.filter(trade_tid=trade_tid,
                                     status=UserCoupon.UNUSED)
    if cous.exists():
        cous.update(status=UserCoupon.FREEZE)


@app.task()
def task_release_mama_link_coupon(saletrade):
    """
    - SaleTrade pay confirm single to drive this task
    - when a customer buy a trade with the mama link url then release a coupon for that mama.
    """
    extras_info = saletrade.extras_info
    mama_id = extras_info.get('mm_linkid') or None
    ufrom = extras_info.get('ufrom')

    order = saletrade.sale_orders.all().first()
    if order and order.item_id in ['22030', '14362', '2731']:  # spacial product id
        return

    if not mama_id:
        return
    mama = XiaoluMama.objects.filter(id=mama_id, charge_status=XiaoluMama.CHARGED).first()
    if not mama:
        return
    customer = mama.get_mama_customer()
    if not customer:
        return
    from flashsale.coupon.models import CouponTemplate
    from ..apis.v1.usercoupon import create_user_coupon

    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_MAMA_INVITE).first()
    if not tpl:
        return
    create_user_coupon(customer_id=customer.id, coupon_template_id=tpl.id, trade_id=saletrade.id, ufrom=str(ufrom))


@app.task()
def task_change_coupon_status_used(saletrade):
    coupon_ids = saletrade.extras_info.get('coupon') or []
    from flashsale.coupon.models import UserCoupon

    for coupon_id in coupon_ids:
        usercoupon = UserCoupon.objects.filter(
            id=coupon_id,
            customer_id=saletrade.buyer_id,
            status=UserCoupon.UNUSED
        ).first()
        if not usercoupon:
            continue
        usercoupon.use_coupon(saletrade.tid)


@app.task()
def task_update_user_coupon_status_2_past():
    """
    - timing to update the user coupon to past.
    """
    from flashsale.coupon.models import UserCoupon

    today = datetime.datetime.today()
    cous = UserCoupon.objects.filter(
        expires_time__lte=today,
        status__in=[UserCoupon.UNUSED, UserCoupon.FREEZE]
    )
    cous.update(status=UserCoupon.PAST)  # 更新为过期优惠券


@app.task()
def task_release_coupon_for_register(instance):
    """
     - release coupon for register a new Customer instance ( when post save created a Customer instance run this task)
    """
    from flashsale.pay.models import Customer

    if not isinstance(instance, Customer):
        return
    from ..apis.v1.usercoupon import create_user_coupon

    tpl_ids = [54, 55, 56, 57, 58, 59, 60]
    for tpl_id in tpl_ids:
        try:
            create_user_coupon(customer_id=instance.id, coupon_template_id=tpl_id)
        except:
            logger.error(u'task_release_coupon_for_register for customer id %s' % instance.id)
            continue
    return


@app.task()
def task_roll_back_usercoupon_by_refund(trade_tid, num):
    from flashsale.coupon.models import UserCoupon
    from flashsale.pay.models import Customer
    from flashsale.coupon.models import CouponTransferRecord

    transfer_coupon_num = 0
    template_id = 0
    customer_id = 0
    for i in range(num):
        cou = UserCoupon.objects.filter(trade_tid=trade_tid, status=UserCoupon.USED).first()
        if cou:
            cou.release_usercoupon()
        if cou and cou.is_transfer_coupon():
            transfer_coupon_num += 1
            template_id = cou.template_id
            customer_id = cou.customer_id

    if transfer_coupon_num > 0:
        customer = Customer.objects.filter(id=customer_id).first()
        CouponTransferRecord.gen_return_record(customer, transfer_coupon_num, template_id, trade_tid)

    return


@app.task()
def task_update_mobile_download_record(tempcoupon):
    from flashsale.coupon.models import OrderShareCoupon

    share = OrderShareCoupon.objects.filter(uniq_id=tempcoupon.share_coupon_id).first()
    if not share:
        return
    from flashsale.promotion.models import DownloadMobileRecord

    uni_key = '/'.join([str(share.share_customer), str(tempcoupon.mobile)])
    dl_record = DownloadMobileRecord.objects.filter(uni_key=uni_key).first()
    if dl_record:  # 记录存在不做处理
        return
    dl_record = DownloadMobileRecord(
        from_customer=share.share_customer,
        mobile=tempcoupon.mobile,
        ufrom=DownloadMobileRecord.REDENVELOPE,
        uni_key=uni_key)
    dl_record.save()


@app.task()
def task_update_unionid_download_record(usercoupon):
    from flashsale.promotion.models import DownloadUnionidRecord, DownloadMobileRecord

    customer = usercoupon.customer
    if not customer:
        return
    if not customer.unionid.strip():  # 没有unionid  写mobilde 记录
        uni_key = '/'.join([str(usercoupon.share_user_id), str(customer.mobile)])
        dl_record = DownloadMobileRecord.objects.filter(uni_key=uni_key).first()
        if dl_record:  # 记录存在不做处理
            return
        dl_record = DownloadMobileRecord(
            from_customer=usercoupon.share_user_id,
            mobile=customer.mobile,
            ufrom=DownloadMobileRecord.REDENVELOPE,
            uni_key=uni_key)
        dl_record.save()
    else:
        uni_key = '/'.join([str(usercoupon.share_user_id), str(customer.unionid)])
        dl_record = DownloadUnionidRecord.objects.filter(uni_key=uni_key).first()
        if dl_record:  # 记录存在不做处理
            return
        dl_record = DownloadUnionidRecord(
            from_customer=usercoupon.share_user_id,
            ufrom=DownloadMobileRecord.REDENVELOPE,
            unionid=customer.unionid,
            uni_key=uni_key,
            headimgurl=customer.thumbnail,
            nick=customer.nick
        )
        dl_record.save()


@app.task()
def task_push_msg_pasting_coupon():
    """
    推送：　明天过期的没有推送过的优惠券将推送用户告知
    """
    from flashsale.coupon.models import UserCoupon
    from flashsale.push.push_usercoupon import user_coupon_release_push

    today = datetime.datetime.today()
    tomorow = today + datetime.timedelta(days=1)
    t_left = datetime.datetime(tomorow.year, tomorow.month, tomorow.day, 0, 0, 0)
    t_right = t_left + datetime.timedelta(days=1)
    coupons = UserCoupon.objects.filter(is_pushed=False,
                                        status=UserCoupon.UNUSED,
                                        expires_time__gte=t_left,
                                        expires_time__lt=t_right)
    customers = coupons.values('customer_id')
    for customer in customers:
        user_coupons = coupons.filter(is_pushed=False, customer_id=customer['customer_id'])
        if user_coupons.exists():
            coupon = user_coupons.first()
            extra_content = '价值%s' % coupon.value
            user_coupon_release_push(coupon.customer_id, push_tpl_id=10, extra_content=extra_content)
        user_coupons.update(is_pushed=True)


@app.tasks()
def task_release_coupon_for_deposit(customer_id, deposit_type):
    from ..apis.v1.usercoupon import create_user_coupon

    deposit_type_tplids_map = {
        XiaoluMama.HALF: [117, 118, 79],  # [121, 124]99+99
        XiaoluMama.FULL: [117, 118, 121, 39]
    }
    if deposit_type not in deposit_type_tplids_map:
        return
    tpl_ids = deposit_type_tplids_map[deposit_type]
    for template_id in tpl_ids:
        create_user_coupon(customer_id=customer_id, coupon_template_id=template_id)


@app.task()
def task_create_transfer_coupon(sale_order):
    # type: (SaleOrder) -> None
    """
    This function temporarily creates UserCoupon. In the future, we should
    create transfer coupon instead.
    """
    from flashsale.coupon.models import CouponTemplate, CouponTransferRecord
    from ..apis.v1.usercoupon import create_user_coupon

    coupon_num = sale_order.num
    customer = sale_order.sale_trade.order_buyer
    product_item_id = sale_order.item_id

    from shopback.items.models import Product
    from flashsale.pay.models import ModelProduct

    product = Product.objects.filter(id=product_item_id).first()
    model_product = ModelProduct.objects.filter(id=product.model_id).first()
    template_id = model_product.extras.get("template_id")

    template = CouponTemplate.objects.get(id=template_id)
    order_id = sale_order.id

    index = 0
    while index < coupon_num:
        unique_key = template.gen_usercoupon_unikey(order_id, index)
        try:
            create_user_coupon(customer.id, template.id, unique_key=unique_key)
        except IntegrityError as exc:
            pass
        index += 1

    to_mama = customer.get_charged_mama()
    to_mama_nick = customer.nick
    to_mama_thumbnail = customer.thumbnail

    coupon_to_mama_id = to_mama.id
    init_from_mama_id = to_mama.id

    coupon_from_mama_id = 0
    from_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'
    from_mama_nick = 'SYSTEM'

    transfer_type = CouponTransferRecord.IN_BUY_COUPON
    date_field = datetime.date.today()
    transfer_status = CouponTransferRecord.DELIVERED
    uni_key = "%s-%s" % (to_mama.id, order_id)
    order_no = sale_order.oid
    coupon_value = int(template.value)
    product_img = template.extras.get("product_img") or ''

    try:
        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,
                                      coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template_id,
                                      product_img=product_img, coupon_num=coupon_num, transfer_type=transfer_type,
                                      uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
        coupon.save()
    except IntegrityError as exc:
        pass

    task_update_tpl_released_coupon_nums(template)  # 统计发放数量
