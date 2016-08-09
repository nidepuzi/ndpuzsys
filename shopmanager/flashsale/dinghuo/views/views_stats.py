
import datetime
from collections import defaultdict
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response

from shopback.items.models import Product, ProductSku
from flashsale.pay.models import SaleOrder
from flashsale.pay.models import SaleRefund
from flashsale.dinghuo.models import OrderList, OrderDetail, ReturnGoods, RGDetail

def get_orderdetail_buyer_maping(start_time, end_time):
    orderdetails = OrderDetail.objects.filter(orderlist__created__range=(start_time, end_time))
    detail_buyer_values_list = orderdetails.values_list('product_id', 'orderlist__buyer__username').distinct()
    return dict(detail_buyer_values_list)

def get_saleorder_stats(start_dt, end_dt): #, refund_status=0
    sorders = SaleOrder.objects.filter(pay_time__range=(start_dt, end_dt))\
        .exclude(consign_time__isnull=True, status__in=(6,7)).extra(
        where=['TIMESTAMPDIFF(DAY, pay_time, consign_time) > 5 or consign_time is NULL']
    )
    sku_values_list = sorders.annotate(total_num=Sum('num')).values('item_id', 'total_num')
    return sku_values_list

def get_lackrefund_stats(start_dt, end_dt):
    srefunds = SaleRefund.objects.filter(success_time__range=(start_dt,end_dt), is_lackrefund=True)
    refund_values_list = srefunds.annotate(total_num=Sum('refund_num')).values('item_id', 'total_num')
    return refund_values_list

def get_returngoods_stats(start_dt, end_dt):
    srefunds = RGDetail.objects.filter(created__range=(start_dt,end_dt), type=RGDetail.TYPE_REFUND)\
        .exclude(return_goods__status=ReturnGoods.OBSOLETE_RG)
    refund_values_list = srefunds.values('skuid', 'num', 'inferior_num', 'return_goods__status')
    return refund_values_list

def export_file(start_dt, end_dt, product_ids):
    fs = file('/tmp/sz_orders.csv','wb')
    sorders = SaleOrder.objects.filter(pay_time__range=(start_dt, end_dt)) \
        .exclude(consign_time__isnull=True, status__in=(6, 7)).extra(
        where=['TIMESTAMPDIFF(DAY, pay_time, consign_time) > 5 or consign_time is NULL']
    ).filter(item_id__in=product_ids)
    for order in sorders:
        fs.write(','.join([order.oid, order.item_id, order.title, order.num, order.sale_trade.tid, order.sale_trade.status,
                  order.refund_status, order.payment, str(order.pay_time), str(order.consign_time), '\n']))

class PurchaseStatsApiView(APIView):
    """  """
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    template_name = "inventory/purchase_stats.html"

    def get(self, request, *args, **kwargs):

        dt = datetime.datetime.today()
        start_dt = request.GET.get('start_time')
        end_dt   = request.GET.get('end_time')

        start_dt = start_dt and datetime.datetime.strptime(start_dt,'%Y-%m-%d') or dt - datetime.timedelta(days=7)
        end_dt   = end_dt and datetime.datetime.strptime(end_dt, '%Y-%m-%d') or dt

        unpost_stats = []
        lackrefund_stats = []
        returngoods_stats = []

        buyer_map = get_orderdetail_buyer_maping(start_dt, end_dt)
        order_stats = get_saleorder_stats(start_dt, end_dt)
        buyercount_dict = defaultdict(list)
        for stats in order_stats:
            buyer = buyer_map.get(stats['item_id'])
            buyercount_dict[buyer].append(stats)

        for buyer, counts in buyercount_dict.items():
            unpost_stats.append([buyer, len(set([i['item_id'] for i in counts])), sum([i['total_num'] for i in counts])])

        refund_stats = get_lackrefund_stats(start_dt, end_dt)
        refundcount_dict = defaultdict(list)
        for stats in refund_stats:
            buyer = buyer_map.get(str(stats['item_id']))
            refundcount_dict[buyer].append(stats)
        for buyer, counts in refundcount_dict.items():
            lackrefund_stats.append([buyer, len(set([i['item_id'] for i in counts])), sum([i['total_num'] for i in counts])])

        return_stats = get_returngoods_stats(start_dt, end_dt)
        sku_values_list = ProductSku.objects.filter(id__in=[rs['skuid'] for rs in return_stats]).values_list('id', 'product_id')
        sku_dict = dict(sku_values_list)
        returncount_dict = defaultdict(list)
        for stats in return_stats:
            product_id = sku_dict.get(stats['skuid'])
            if not product_id: continue
            buyer = buyer_map.get(str(product_id))
            fail_num = 0
            stats['product_id'] = product_id
            stats['return_num'] = stats['num'] + stats['inferior_num']
            if stats['return_goods__status'] == 5:
                fail_num = stats['return_num']
            stats.update(fail_num=fail_num)
            returncount_dict[buyer].append(stats)

        for buyer, counts in returncount_dict.items():
            returngoods_stats.append([buyer, len(set([i['product_id'] for i in counts])),
                                      sum([i['return_num'] for i in counts]),
                                      sum([i['fail_num'] for i in counts])])

        return Response({
                        'start_time':start_dt,
                        'end_time':end_dt,
                        'unpost_stats':unpost_stats,
                        'lackrefund_stats':lackrefund_stats,
                        'returngoods_stats':returngoods_stats})
