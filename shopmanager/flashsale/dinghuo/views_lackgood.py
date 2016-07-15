# coding:utf-8

from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F, Q, Sum, Count
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import authentication
from rest_framework.parsers import JSONParser
from rest_framework.decorators import parser_classes

from .models import LackGoodOrder, OrderList
from flashsale.pay.models import SaleOrder, SaleRefund
from flashsale.coupon.models import UserCoupon
from flashsale.coupon.constants import LACK_REFUND_COUPON_TEMPLATE_ID
from . import serializers

from flashsale.pay import apis

import logging
logger = logging.getLogger(__name__)


class LackGoodOrderViewSet(viewsets.ModelViewSet):
    """ 订货缺货商品单接口 """
    queryset = LackGoodOrder.objects.all()

    serializer_class = serializers.LackGoodOrderSerializer
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,renderers.TemplateHTMLRenderer)

    @list_route(methods=['get','post'])
    @parser_classes(JSONParser)
    def multi_create(self, request, *args, **kwargs):
        data = request.data
        order_group_key = data.get('order_group_key', '')
        order_ids = [s for s in order_group_key.split('-') if s]
        if not order_ids:
            return Response({'code':1 ,'info':'请输入订货单组编号'})

        creator = request.user.username
        order_list = OrderList.objects.filter(id__in=order_ids)
        supplier = order_list.first().supplier
        lackorder_qs = LackGoodOrder.objects.get_objects_by_order_ids(order_ids)
        lack_goods = data.get('lack_goods')
        for good in lack_goods:
            lack_sku = lackorder_qs.filter(sku_id=good['sku_id']).first()
            if not lack_sku:
                lack_sku = LackGoodOrder(supplier=supplier,
                                         order_group_key=order_group_key,
                                         product_id=good['product_id'],
                                         sku_id=good['sku_id'],
                                         lack_num=good['lack_num'],
                                         creator=creator)
                lack_sku.save()
                # TODO logaction
            else:
                if lack_sku.is_canceled:
                    lack_sku.lack_num = good['lack_num']
                    lack_sku.status = LackGoodOrder.NORMAL
                else:
                    lack_sku.lack_num = F('lack_num') + good['lack_num']
                lack_sku.save(update_fields=['supplier','order_group_key','product_id','sku_id','lack_num','status'])

        return Response({'code':0, 'info':u'保存成功','redirect_url':'/apis/dinghuo/v1/lackorder/%s/refund_manage.html'%order_group_key})

    @detail_route(methods=['get'])
    def refund_manage(self, request, pk, *args, **kwargs):

        order_ids = [s for s in pk.split('-') if s]
        if not order_ids:
            return Response({'code': 1, 'info': '请输入订货单组编号'})

        from flashsale.pay.models import SaleOrder

        lackorder_qs = LackGoodOrder.objects.get_objects_by_order_ids(order_ids)
        normal_lackvalues = lackorder_qs.filter(status=LackGoodOrder.NORMAL).values_list('sku_id', 'id')
        lackorder_data = serializers.LackGoodOrderSerializer(lackorder_qs, many=True).data

        normal_lackdict = dict(normal_lackvalues)
        normal_skuids   = normal_lackdict.keys()
        saleorders = SaleOrder.objects.filter(sku_id__in=normal_skuids,status=SaleOrder.WAIT_SELLER_SEND_GOODS)\
            .select_related('sale_trade').values(
            'id', 'oid', 'item_id', 'title', 'pic_path', 'sku_name', 'sku_id', 'pay_time',
            'num', 'payment', 'refund_id' , 'refund_fee', 'refund_status', 'status', 'sale_trade_id',
            'sale_trade__buyer_nick', 'sale_trade__receiver_name','sale_trade__total_fee','sale_trade__receiver_mobile'
        )
        saleorder_list = []
        for order in saleorders:
            order['lackorder_id'] = normal_lackdict.get(int(order['sku_id']))
            order['buyer_nick'] = order.pop('sale_trade__buyer_nick')
            order['receiver_name'] = order.pop('sale_trade__receiver_name')
            order['total_fee'] = order.pop('sale_trade__total_fee')
            order['receiver_mobile'] = order.pop('sale_trade__receiver_mobile')
            saleorder_list.append(order)
        return Response({'lack_orders': lackorder_data,
                         'sale_orders': saleorder_list,
                         'order_group_key': pk},
                        template_name='inventory/lack_refund_manage.html')


    @detail_route(methods=['get','post'])
    def refund_order(self, request, pk, *args, **kwargs):
        data = request.data
        saleorder_id = data.get('saleorder_id')
        refund_num = data.get('refund_num')
        lack_order = self.get_object()
        if not saleorder_id.isdigit() or not refund_num.isdigit():
            return Response({'code': 1, 'info':u'订单编号及数量不对'})

        sale_order  = SaleOrder.objects.filter(id=saleorder_id).first()
        if not sale_order or \
            not lack_order.get_refundable() or\
                int(sale_order.sku_id) != int(lack_order.sku_id) or\
                    not sale_order.get_refundable():
            return Response({'code': 2, 'info':u'自动退款条件不满足'})

        user_id = request.user.id
        refund_num = int(refund_num)
        refund_fee = round((sale_order.payment / (sale_order.num or 0)) * refund_num, 2)
        sale_trade = sale_order.sale_trade
        refund_channel = sale_trade.channel

        try:
            with transaction.atomic():
                refund = apis.api_create_refund_order(
                    user_id, saleorder_id, 0, refund_num, refund_fee, refund_channel,
                    desc=u'订单缺货自动退款,有张优惠券', good_status=SaleRefund.SELLER_OUT_STOCK,
                    modify=None, proof_pic=None, is_lackrefund=True, lackorder_id=lack_order.id
                )
                refund.refund_approve()

                lack_order.refund_num += refund_num
                lack_order.is_refund  = True
                lack_order.save(update_fields=['refund_num', 'is_refund'])
                # 发优惠券
                UserCoupon.objects.create_refund_post_coupon(sale_trade.buyer_id,
                                                             LACK_REFUND_COUPON_TEMPLATE_ID,
                                                             trade_id=sale_trade.id,
                                                             ufrom=None)
                # TODO app推送

        except Exception, exc:
            return Response({'code': 1, 'info': exc.message})
        else:
            # 发送短信
            from shopapp.smsmgr.tasks import task_notify_lack_refund
            task_notify_lack_refund.delay(sale_order)

        return Response({'code': 0, 'info':u'退款成功',
                         'result':{
                                 'id': lack_order.id,
                                 'refund_num': lack_order.refund_num
                             }
                        })



