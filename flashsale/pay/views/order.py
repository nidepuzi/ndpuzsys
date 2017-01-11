# -*- encoding:utf8 -*-
import json
import datetime
from django.shortcuts import render, render
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from core.options import log_action, ADDITION, CHANGE
from shopback.logistics import getLogisticTrace

from shopback.items.models import Product, ProductSku,SkuStock
from flashsale.pay.models import SaleTrade, SaleOrder
from flashsale.pay.models import TeamBuyDetail

from flashsale.pay.constants import BUDGET
from flashsale.pay.tasks import pushTradeRefundTask
from flashsale.coupon.apis.v1.usercoupon import create_user_coupon, UserCoupon

import logging
logger = logging.getLogger(__name__)

ISOTIMEFORMAT = '%Y-%m-%d '
today = datetime.date.today()
real_today = datetime.date.today().strftime("%Y-%m-%d ")

start = 0
end = 100


# 查询功能
def search_flashsale(request):
    print '数字是', 4444
    if request.method == "POST":
        rec1 = []
        number1 = request.POST.get('condition')
        number = number1.strip()
        # print '数字是',number
        if number == "":
            rec1 = []
        else:
            trade_info = SaleTrade.objects.filter(
                Q(receiver_mobile=number) | Q(tid=number) | Q(buyer_nick=number) | Q(receiver_phone=number) | Q(
                    out_sid=number))
            for item in trade_info:
                info = {}
                try:
                    a = getLogisticTrace(item.out_sid, item.logistics_company.code)
                except:
                    a = []
                # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
                print '全部信息是', a
                info['trans'] = a
                info['trade'] = item
                info['detail'] = []
                for order_info in item.sale_orders.all():
                    sum = {}
                    sum['order'] = order_info
                    try:
                        product_info = Product.objects.get(outer_id=order_info.outer_id)
                    except:
                        product_info = []
                    # product_info=Product.objects.get(outer_id=order_info.outer_id)
                    sum['product'] = product_info
                    info['detail'].append(sum)
                rec1.append(info)
                print rec1
        return render(request, 'pay/order_flash.html',
                      {'info': rec1, 'time': real_today, 'yesterday': today, 'start': start})
    else:
        rec1 = []

        return render(request, 'pay/order_flash.html',
                      {'info': rec1, 'time': real_today, 'yesterday': today, 'start': start})


def order_flashsale(request):
    global today
    global start
    global end
    start = 0
    end = 100
    today = datetime.date.today()  ##14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec2 = []
    # a=  getLogisticTrace('718844325420','中通')
    # print '物流信息',a[0][0]
    trade_info = SaleTrade.objects.all().order_by('-created')[start:end]
    # print type(a)
    for item in trade_info:
        print '邮编是', item.out_sid
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        print '全部信息是', a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            sum['product'] = product_info
            info['detail'].append(sum)
        rec2.append(info)
    return render(request, 'pay/order_flash.html',
                  {'info': rec2, 'time': real_today, 'yesterday': today, 'start': start})


def preorder_flashsale(request):
    global today
    global start
    global end
    today = datetime.date.today()  ##14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec = []
    # print '现在',start
    # print '现在',end
    if start == 0:
        start = 0
        end = 100
    else:
        start = start - 100
        end = end - 100
    # print '现在',start
    # print '现在',end
    # trade_info=SaleTrade.objects.all()[start:end]
    trade_info = SaleTrade.objects.all().order_by('-created')[start:end]
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            sum['product'] = product_info
            info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html',
                  {'info': rec, 'time': real_today, 'yesterday': today, 'start': start})


def nextorder_flashsale(request):
    global today
    global start
    global end
    today = datetime.date.today()  ##14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec = []
    start = start + 100
    end = end + 100
    # print '现在',start
    # print '现在',end
    # trade_info=SaleTrade.objects.all()[start:end]
    trade_info = SaleTrade.objects.all().order_by('-created')[start:end]
    for item in trade_info:
        info = {}
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
            # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            sum['product'] = product_info
            info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html',
                  {'info': rec, 'time': real_today, 'yesterday': today, 'start': start})


def order_flashsale22(request):
    global today
    today = datetime.date.today()  # 14：24  改正now 改为now2
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # print '现在',now4
    # print '现在',now5
    rec = []
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    for item in trade_info:
        info = {}
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            sum['order'] = order_info
            product_info = Product.objects.get(outer_id=order_info.outer_id)
            sum['product'] = product_info
            info['detail'].append(sum)
        rec.append(info)
    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


def time_rank(request, time_id):
    global today
    realtoday = datetime.date.today().strftime("%Y-%m-%d ")  # 真正的今天的时间
    day = time_id
    print int(day), type(day)
    if int(day) == 1:
        today = today - datetime.timedelta(days=1)
        now2 = today.strftime("%Y-%m-%d ")
        now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        # print '现在',now4
        # print '现在',now5
        rec = []
        trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
        for item in trade_info:
            info = {}
            info['trade'] = item
            info['detail'] = []
            try:
                a = getLogisticTrace(item.out_sid, item.logistics_company.code)
            except:
                a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            print '全部信息是', a
            info['trans'] = a
            for order_info in item.sale_orders.all():
                sum = {}
                print 'orderinfo', order_info
                print 'order2', order_info.outer_id
                sum['order'] = order_info
                try:
                    product_info = Product.objects.get(outer_id=order_info.outer_id)
                except:
                    product_info = []
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                sum['product'] = product_info
                info['detail'].append(sum)
            rec.append(info)
            # print '本次结束',   rec
            # print rec
        return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


    elif int(day) == 0:
        today = datetime.date.today()
        now2 = today.strftime("%Y-%m-%d ")  # 14：24  改正now 改为now2
        print '今天是', type(now2)
        rec = []
        today = datetime.date.today()
        now2 = today.strftime("%Y-%m-%d ")
        now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
        print '现在', now4
        print '现在', now5
        for item in trade_info:
            info = {}
            try:
                a = getLogisticTrace(item.out_sid, item.logistics_company.code)
            except:
                a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            # print '全部信息是',a
            info['trans'] = a
            info['trade'] = item
            info['detail'] = []
            for order_info in item.sale_orders.all():
                sum = {}
                # print 'orderinfo' ,  order_info
                # print 'order2' ,  order_info.outer_id
                sum['order'] = order_info
                try:
                    product_info = Product.objects.get(outer_id=order_info.outer_id)
                except:
                    product_info = []
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                # print product_info,'tttttt'
                sum['product'] = product_info
                info['detail'].append(sum)
            rec.append(info)
            # print '本次结束',   rec
            # print rec
        return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})

    elif int(day) == 2:
        if today.strftime("%Y-%m-%d ") == realtoday:
            today = datetime.date.today()
        else:
            today = today + datetime.timedelta(days=1)
        now2 = today.strftime("%Y-%m-%d ")
        now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
        rec = []
        for item in trade_info:
            info = {}
            try:
                a = getLogisticTrace(item.out_sid, item.logistics_company.code)
            except:
                a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            # print '全部信息是',a
            info['trans'] = a
            info['trade'] = item
            info['detail'] = []
            for order_info in item.sale_orders.all():
                sum = {}
                # print 'orderinfo' ,  order_info
                # print 'order2' ,  order_info.outer_id
                sum['order'] = order_info
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                try:
                    product_info = Product.objects.get(outer_id=order_info.outer_id)
                except:
                    product_info = []
                    # print product_info,'tttttt'
                sum['product'] = product_info
                info['detail'].append(sum)
            rec.append(info)
        return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})

        # 增加交易状态的处理


def sale_state(request, state_id):
    print '编号', type(state_id)
    print '状态是', state_id
    global today
    print today
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    rec = []
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        # print 'order1' ,  item.sale_orders.all()
        for order_info in item.sale_orders.all():
            sum = {}
            # print 'orderinfo' ,  order_info
            # print 'order2' ,  order_info.outer_id
            sum['order'] = order_info
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
                # product_info=Product.objects.get(outer_id=order_info.outer_id)
                # print product_info,'tttttt'
            sum['product'] = product_info
            info['detail'].append(sum)
            # print '状态2是' ,  item.status
        if item.status == long(state_id):
            rec.append(info)
            # print '本次结束',   rec
    # print rec
    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


# 退款状态
def refund_state(request, state_id):
    # print '编号' , type( state_id)
    # print '状态是' ,  state_id
    global today
    # print today
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    rec = []
    # print 'order0' ,  trade_info
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
            # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
            # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        for order_info in item.sale_orders.all():
            sum = {}
            # print 'orderinfo' ,  order_info
            #  print 'order2' ,  order_info.outer_id
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
                # print product_info,'tttttt'
            sum['product'] = product_info
            info['detail'].append(sum)
            if order_info.refund_status == long(state_id):
                rec.append(info)
                # print '本次结束',   rec
    # print rec
    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


def refunding_state(request, state_id):
    # print '编号' , type( state_id)
    # print '状态是' ,  state_id
    global today
    now2 = today.strftime("%Y-%m-%d ")
    now4 = datetime.datetime.strptime(now2 + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    now5 = datetime.datetime.strptime(now2 + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    rec = []
    trade_info = SaleTrade.objects.filter(created__range=(now4, now5))
    # print 'order0' ,  trade_info
    for item in trade_info:
        info = {}
        try:
            a = getLogisticTrace(item.out_sid, item.logistics_company.code)
        except:
            a = []
        # a=  getLogisticTrace(item.out_sid,item.logistics_company.code)
        # print '全部信息是',a
        info['trans'] = a
        info['trade'] = item
        info['detail'] = []
        # print 'order1' ,  item.sale_orders.all()
        for order_info in item.sale_orders.all():
            sum = {}
            # print 'orderinfo' ,  order_info
            # print 'order2' ,  order_info.outer_id
            sum['order'] = order_info
            # product_info=Product.objects.get(outer_id=order_info.outer_id)
            try:
                product_info = Product.objects.get(outer_id=order_info.outer_id)
            except:
                product_info = []
            # print product_info,'tttttt'
            sum['product'] = product_info
            info['detail'].append(sum)
            if order_info.refund_status != long(0) and order_info.refund_status != long(7):
                rec.append(info)
                # print '本次结束',   rec
                # print rec

    return render(request, 'pay/order_flash.html', {'info': rec, 'time': real_today, 'yesterday': today})


def get_mrgid(request):
    content = request.POST
    sale_order_id = content.get("sale_order_id", None)
    sale_order = get_object_or_404(SaleOrder, id=sale_order_id)
    try:
        sale_trade = sale_order.sale_trade_id
        sale_order = sale_order.id
        return HttpResponse(
            json.dumps({"res": True, "data": [{"trade_id": sale_trade, "order_id": sale_order}], "desc": ""}))
    except Exception, msg:
        return HttpResponse(json.dumps({"res": False, "data": [], "desc": str(msg)}))


def is_sku_enough(request):
    sku_id = None
    sku_stock = None
    content = request.POST
    sale_order_id = content.get("sale_order_id",None)
    sale_order = SaleOrder.objects.filter(id = sale_order_id).first()
    if sale_order:
        sku_id = sale_order.sku_id
    if not content.get("SKU",None):
        sku_stock = SkuStock.objects.filter(sku_id = sku_id).first()
    else:
        new_sku_id = content.get("SKU",None)
        sku_stock = SkuStock.objects.filter(sku_id=new_sku_id).first()

    if sku_stock and sku_stock.free_num >= sale_order.num:
        return HttpResponse(json.dumps({"res": True, "data": [], "desc": "存在尚未分配的库存"}))
    else:
        return HttpResponse(json.dumps({"res": False, "data": [], "desc": "不存在尚未分配的库存"}))




def sent_sku_item_again(request):
    content = request.POST
    sale_order_id = content.get("sale_order_id", None)
    sale_order = get_object_or_404(SaleOrder, id=sale_order_id)
    sale_trade = sale_order.sale_trade
    try:
        sale_trade.redeliver_sku_item(sale_order)
        return HttpResponse(json.dumps({"res": True, "data": [], "desc": ""}))
    except Exception, e0:
        return HttpResponse(json.dumps({"res": False, "data": [], "desc": str(e0)}))


def change_sku_item(request):
    content = request.POST
    sale_order_id = int(content.get("sale_order_id", None))
    sku = content.get("SKU")
    if not sku:
        return HttpResponse({False})
    if not ProductSku.objects.filter(id=sku).exists():
        return HttpResponse({False})
    num = content.get("num", None)
    try:
        num = int(num)
    except:
        return HttpResponse({False})
    sale_order = get_object_or_404(SaleOrder, id=sale_order_id)
    sale_trade = sale_order.sale_trade
    try:
        sale_trade.change_sku_item(sale_order, sku, num)
    except Exception, e0:
        return HttpResponse(json.dumps({'status': 1, "desc": str(e0)}))
    return HttpResponse(True)


def update_memo(request):
    content = request.POST
    id = content.get("id", None)
    memo = content.get("memo", '')
    try:
        sale_trade = get_object_or_404(SaleTrade, id=id)
        sale_trade.seller_memo = memo
        sale_trade.save()
        log_action(request.user, sale_trade, CHANGE, 'SaleTrade修改备注')
    except Exception, msg:
        logger.error(msg)
        return HttpResponse(json.dumps({"res": False, "data": ["添加备注失败"], "desc": str(msg)}))
    return HttpResponse(json.dumps({"res": True, "data": [memo], "desc": ""}))


class SaleOrderDoRefund(APIView):
    queryset = SaleOrder.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)

    def post(self, request):
        # type: (HttpRequest) -> Response
        """客服操作退款给用户
        """
        order_id = request.POST.get('order_id') or None
        good_status = request.POST.get('good_status') or None
        order = self.queryset.filter(id=order_id).first()
        if not order:
            return Response({'code': 1, 'info': u'参数错误'})
        if order.is_teambuy() and TeamBuyDetail.objects.get(oid=order.oid).teambuy.status == 0:
            return Response({'code': 2, 'info': u"团购到超时失败以后才可退款"})
        if not (SaleOrder.WAIT_SELLER_SEND_GOODS <= order.status < SaleOrder.TRADE_FINISHED):  # 状态为已付款
            return Response({'code': 3, 'info': u"交易状态不是已付款状态"})

        refund = order.do_refund(reason=2, refund_channel=BUDGET, good_status=good_status, creator=request.user)  # reason=2表示缺货
        pushTradeRefundTask.delay(refund.id)
        log_action(request.user, refund, CHANGE, u'SaleRefund退款单创建: good_status=%s' % good_status)
        log_action(request.user, order, CHANGE, u'SaleOrder订单退款')
        return Response({'code': 0, 'info': u'操作成功'})


class RefundCouponForTradeView(APIView):
    queryset = SaleTrade.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # type: (HttpRequest) -> Response
        content = request.POST
        trade_id = content.get("trade_id") or 0
        coupon_template_id = content.get("coupon_template_id") or 0
        coupon_template_id = int(coupon_template_id)
        trade_id = int(trade_id)
        if not (coupon_template_id and trade_id):
            return Response({'code': 2, 'info': u'参数错误'})
        saletrade = self.queryset.filter(id=trade_id).first()
        if UserCoupon.objects.filter(coupon_type=UserCoupon.TYPE_COMPENSATE,
                                     customer_id=saletrade.buyer_id,
                                     uniq_id__contains=saletrade.id).exists():
            return Response({'code': 3, 'info': u'已经发放过了'})
        cou, code, msg = create_user_coupon(customer_id=saletrade.buyer_id,
                                            coupon_template_id=coupon_template_id,
                                            trade_id=saletrade.id)
        if cou and code == 0:
            log_action(request.user, cou, CHANGE, u'发放订单补偿优惠券')
        else:
            return Response({'code': 1, 'info': msg})
        return Response({'code': 0, 'info': u'操作成功'})
