# -*- coding:utf-8 -*-
import datetime
import re
import sys
import copy
import numpy as np
from django.db import models
from django.db.models import Sum, Count, F, Q
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from core.fields import JSONCharMyField
from shopback.items.models import ProductSku, Product
from shopback.refunds.models import Refund
from supplychain.supplier.models import SaleSupplier, SaleProduct
from .purchase_order import OrderList, OrderDetail
from shopback.warehouse import WARE_SH, WARE_CHOICES
import logging

logger = logging.getLogger(__name__)


class InBound(models.Model):
    INVALID = 0
    PENDING = 1
    WAIT_CHECK = 2
    COMPLETED = 3
    COMPLETE_RETURN = 4

    SUPPLIER = 1
    REFUND = 2

    STATUS_CHOICES = ((INVALID, u'作废'),
                      (PENDING, u'待分配'),
                      (WAIT_CHECK, u'待质检'),
                      (COMPLETED, u'已入库'),
                      (COMPLETE_RETURN, u'已完结'))
    supplier = models.ForeignKey(SaleSupplier,
                                 null=True,
                                 blank=True,
                                 related_name='inbounds',
                                 verbose_name=u'供应商')
    express_no = models.CharField(max_length=32,
                                  verbose_name=u'快递单号')
    ori_orderlist_id = models.CharField(max_length=32, default='',
                                        verbose_name=u'订货单号')
    sent_from = models.SmallIntegerField(
        default=SUPPLIER,
        choices=((SUPPLIER, u'供应商'), (REFUND, u'退货')),
        verbose_name=u'包裹类型')
    refund = models.ForeignKey(Refund,
                               null=True,
                               blank=True,
                               related_name='inbounds',
                               verbose_name=u'退款单', help_text=u"无效字段暂未删除")
    return_goods = models.ForeignKey('ReturnGoods',
                                     null=True,
                                     blank=True,
                                     verbose_name=u'退货单')
    creator = models.ForeignKey(User,
                                related_name='inbounds',
                                verbose_name=u'创建人')
    ware_by = models.IntegerField(default=WARE_SH, db_index=True, choices=WARE_CHOICES, verbose_name=u'所属仓库')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    status = models.SmallIntegerField(default=PENDING,
                                      choices=STATUS_CHOICES,
                                      verbose_name=u'进度')
    images = JSONCharMyField(max_length=10240,
                             blank=True,
                             default='[]',
                             verbose_name=u'图片')
    orderlist_ids = JSONCharMyField(max_length=10240,
                                    blank=True,
                                    default='[]',
                                    verbose_name=u'订货单ID',
                                    help_text=u'冗余的订货单关联')
    forecast_inbound_id = models.IntegerField(null=True, db_index=True, verbose_name=u'关联预测单ID')
    checked = models.BooleanField(default=False, verbose_name=u"是否质检")
    check_time = models.DateTimeField(null=True, verbose_name=u"检查时间")
    wrong = models.BooleanField(default=False, verbose_name=u"有错货")
    out_stock = models.BooleanField(default=False, verbose_name=u"有多货")
    inferior = models.BooleanField(default=False, verbose_name=u"有次品")

    class Meta:
        db_table = 'flashsale_dinghuo_inbound'
        app_label = 'dinghuo'
        verbose_name = u'入仓单'
        verbose_name_plural = u'入仓单列表'

    def __unicode__(self):
        return str(self.id)

    def assign_to_order_detail(self, orderlist_id, orderlist_ids):
        return {}
        orderlist_ids = [x for x in orderlist_ids if x != orderlist_id]
        inbound_skus = dict([(inbound_detail.sku_id,
                              inbound_detail.arrival_quantity)
                             for inbound_detail in self.details.all()])
        order_details_first = OrderDetail.objects.filter(
            orderlist_id=orderlist_id,
            chichu_id__in=inbound_skus.keys()).order_by('created')
        order_details = OrderDetail.objects.filter(
            orderlist_id__in=list(orderlist_ids),
            chichu_id__in=inbound_skus.keys()).order_by('created')
        order_details = list(order_details)
        order_details = list(order_details_first) + order_details
        assign_dict = {}
        for order_detail in order_details:
            if order_detail.not_arrival_quantity < inbound_skus.get(
                    order_detail.chichu_id, 0):
                order_detail.arrival_quantity += order_detail.not_arrival_quantity
                inbound_skus[
                    order_detail.chichu_id] -= order_detail.not_arrival_quantity
                assign_dict[order_detail.id] = order_detail.not_arrival_quantity
                # order_detail.save()
            else:
                order_detail.arrival_quantity += inbound_skus.get(
                    order_detail.chichu_id, 0)
                inbound_skus[order_detail.chichu_id] = 0
                assign_dict[order_detail.id] = inbound_skus.get(
                    order_detail.chichu_id, 0)
        return assign_dict

    def allocate(self, data):
        request_all_sku = {}
        for orderdetail_id in data:
            orderdetail = OrderDetail.objects.get(id=orderdetail_id)
            request_all_sku[int(orderdetail.chichu_id)] = request_all_sku.get(int(orderdetail.chichu_id), 0) + data[
                orderdetail_id]
        sku_data = self.sku_data
        for sku_id in request_all_sku:
            if request_all_sku.get(sku_id, 0) > sku_data[sku_id]:
                raise Exception(u'分配数不能超出总数')
        for orderdetail_id in data:
            orderdetail = OrderDetail.objects.get(id=orderdetail_id)
            OrderDetailInBoundDetail.create(orderdetail, self, data[orderdetail_id])
        self.status = InBound.WAIT_CHECK
        self.set_stat()
        self.save()

    def record_orderlist_ids(self):
        self.orderlist_ids = self.order_list_ids
        self.save()

    def update_orderlist_inbound(self):
        for orderlist_id in self.order_list_ids:
            OrderList.objects.get(id=orderlist_id).set_arrival_process_status()

    def notify_forecast_save_or_update_inbound(self):
        from flashsale.forecast.apis import api_create_or_update_realinbound_by_inbound
        api_create_or_update_realinbound_by_inbound.delay(self.id)

    @property
    def sku_ids(self):
        if not hasattr(self, '_sku_ids_'):
            self._sku_ids_ = [i['sku_id'] for i in self.details.values('sku_id')]
        return self._sku_ids_

    def is_invalid_status(self):
        return self.status == self.INVALID

    @property
    def product_ids(self):
        if not hasattr(self, '_product_ids_'):
            self._product_ids_ = [i['product_id'] for i in self.details.values('product_id').distinct()]
        return self._product_ids_

    @property
    def product_skus(self):
        if not hasattr(self, '_product_skus_'):
            self._product_skus_ = ProductSku.objects.filter(id__in=self.sku_ids)
        return self._product_skus_

    @property
    def products(self):
        if not hasattr(self, '_products_'):
            self._products_ = Product.objects.filter(id__in=self.product_ids)
        return self._products_

    @property
    def order_detail_ids(self):
        if not hasattr(self, '_order_detail_ids_'):
            query = OrderDetailInBoundDetail.objects.filter(inbounddetail__inbound__id=self.id).values('orderdetail_id')
            self._order_detail_ids_ = [item['orderdetail_id'] for item in query]
        return self._order_detail_ids_

    @property
    def order_details(self):
        if not hasattr(self, '_order_details_'):
            self._order_details_ = OrderDetail.objects.filter(id__in=self.order_detail_ids)
        return self._order_details_

    @property
    def order_list_ids(self):
        if not hasattr(self, '_order_list_ids_'):
            query = OrderDetail.objects.filter(id__in=self.order_detail_ids).values('orderlist_id').distinct()
            self._order_list_ids_ = [item['orderlist_id'] for item in query]
        return self._order_list_ids_

    @property
    def order_lists(self):
        if not hasattr(self, '_order_lists_'):
            self._order_lists_ = OrderList.objects.filter(id__in=self.order_list_ids)
        return self._order_lists_

    @property
    def order_list_items(self):
        cache_orderlist = {}
        cache_product = {}
        res = []
        for od in self.order_details:
            if od.orderlist_id not in cache_orderlist:
                cache_orderlist[od.orderlist_id] = od.orderlist
            ol = cache_orderlist[od.orderlist_id]
            if ol not in res:
                ol.inbound_products = []
                res.append(ol)
            if od.product_id not in cache_product:
                cache_product[od.product_id] = od.product
            product = cache_product[od.product_id]
            if product not in ol.inbound_products:
                product.inbound_orderdetails = [od]
                ol.inbound_products.append(product)
            else:
                product.inbound_orderdetails.append(od)
        for ol in res:
            ol.rows = sum([len(p.inbound_orderdetails) for p in ol.inbound_products])
        return res

    def get_order_list_items_dict(self):
        order_list_items = self.order_list_items
        return order_list_items

    @property
    def sku_data(self):
        return {item['sku_id']: item['arrival_quantity'] + item['inferior_quantity']
                for item in self.details.values('sku_id', 'arrival_quantity', 'inferior_quantity')}

    def get_allocate_orderlist_dict(self):
        res = {}
        for orderlist in self.order_lists.all():
            detail_ids = [detail.id for detail in orderlist.order_list.all()]
            res[orderlist.id] = OrderDetailInBoundDetail.objects.filter(inbounddetail__inbound_id=self.id,
                                                                        inbounddetail__checked=True,
                                                                        orderdetail_id__in=detail_ids).aggregate(
                n=Sum('arrival_quantity')).get('n', 0) or 0
        return res.iteritems()

    def all_skus(self):
        orderlist_ids = self.get_may_allocate_order_list_ids()
        query = OrderDetail.objects.filter(orderlist_id__in=orderlist_ids).values('chichu_id').distinct()
        return [int(item['chichu_id']) for item in query]

    def get_set_status_info(self):
        # if self.set_stat():
        #     self.save()
        wrong_str = u'错货%d件' % (self.error_cnt,) if self.wrong else ''
        more = self.all_arrival_quantity - self.all_allocate_quantity
        more_str = u'多货%d件' %(more,) if more>0 else ''
        return u"共%d件SKU（%d正品%d次品%s%s），分配了%d件进订货单" % (self.all_quantity, self.all_arrival_quantity,
                                                    self.all_inferior_quantity, wrong_str, more_str, self.all_allocate_quantity)

    def get_may_allocate_order_list_ids(self):
        query = OrderDetail.objects.filter(orderlist__supplier_id=self.supplier_id, chichu_id__in=self.sku_ids,
                                           orderlist__stage=OrderList.STAGE_RECEIVE).values('orderlist_id').distinct()
        return [item['orderlist_id'] for item in query]

    def may_allocate_order_list_items(inbound):
        orderlist_ids = inbound.get_may_allocate_order_list_ids()
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        product_ids = set()
        sku_ids = set()
        orderlists_dict = {}
        sku_data = inbound.sku_data

        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': orderlist.get_buyer_name(),
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': status_mapping.get(orderlist.status) or '未知',
                'products': {}
            }

        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=orderlist_ids).order_by('id'):
            orderlist_dict = orderlists_dict[orderdetail.orderlist_id]
            product_id = int(orderdetail.product_id)
            sku_id = int(orderdetail.chichu_id)
            product_ids.add(product_id)
            sku_ids.add(sku_id)

            products_dict = orderlist_dict['products']
            skus_dict = products_dict.setdefault(product_id, {})

            skus_dict[sku_id] = {
                'buy_quantity': orderdetail.buy_quantity,
                'plan_quantity': orderdetail.buy_quantity - min(
                    orderdetail.arrival_quantity, orderdetail.buy_quantity),
                'arrival_quantity': orderdetail.arrival_quantity,
                'inferior_quantity': orderdetail.inferior_quantity,
                'all_quantity': orderdetail.inferior_quantity + orderdetail.arrival_quantity,
                'orderdetail_id': orderdetail.id,
                'in_inbound': sku_id in sku_data
            }

        saleproduct_ids = set()
        products_dict = {}
        for product in Product.objects.filter(id__in=list(product_ids)):
            products_dict[product.id] = {
                'id': product.id,
                'name': product.name,
                'saleproduct_id': product.sale_product,
                'outer_id': product.outer_id,
                'pic_path': product.pic_path,
                'ware_by': product.ware_by,
                'product_link': product.get_product_link()
            }
            saleproduct_ids.add(product.sale_product)

        skus_dict = {}
        for sku in ProductSku.objects.filter(id__in=list(sku_ids)):
            skus_dict[sku.id] = {
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias,
                'barcode': sku.barcode,
                'is_inbound': 1
            }

        saleproducts_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=list(saleproduct_ids)):
            saleproducts_dict[saleproduct.id] = {
                'product_link': saleproduct.product_link
            }

        orderlists = []
        for orderlist_id in sorted(orderlists_dict.keys()):
            orderlist_dict = orderlists_dict[orderlist_id]
            orderlist_products_dict = orderlist_dict['products']
            orderlist_products = []
            len_of_skus = 0
            for product_id in sorted(orderlist_products_dict.keys()):
                product_dict = copy.copy(products_dict[product_id])
                product_dict.update(saleproducts_dict.get(product_dict['saleproduct_id']) or {})
                orderlist_skus_dict = orderlist_products_dict[product_id]
                for sku_id in sorted(orderlist_skus_dict.keys()):
                    len_of_skus += 1
                    sku_dict = orderlist_skus_dict[sku_id]
                    sku_dict.update(skus_dict[sku_id])
                    product_dict.setdefault('skus', []).append(sku_dict)
                orderlist_products.append(product_dict)
            orderlist_dict['orderlist_id'] = orderlist_id
            orderlist_dict['products'] = orderlist_products
            orderlist_dict['len_of_skus'] = len_of_skus
            orderlists.append(orderlist_dict)
        return orderlists

    def get_allocate_order_details_dict(self):
        if self.is_finished():
            orderlist_ids = self.order_list_ids
        else:
            orderlist_ids = self.get_may_allocate_order_list_ids()
        orderlists_dict = {}
        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': orderlist.get_buyer_name(),
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': orderlist.get_status_display(),
                'products': []
            }
            cache_products = {}
            for orderdetail in orderlist.order_list.all().order_by('id'):
                product = orderdetail.product
                sku = orderdetail.sku
                if orderdetail.product_id in cache_products:
                    product_dict = cache_products.get(orderdetail.product_id)
                else:
                    product_dict = {'id': product.id,
                                    'name': product.name,
                                    'saleproduct_id': product.sale_product,
                                    'outer_id': product.outer_id,
                                    'pic_path': product.pic_path,
                                    'ware_by': product.ware_by,
                                    'skus': []
                                    }
                sku_dict = {
                    'orderdetail_id': orderdetail.id,
                    'buy_quantity': orderdetail.buy_quantity,
                    'plan_quantity': orderdetail.need_arrival_quantity,
                    'arrival_quantity': orderdetail.arrival_quantity,
                    'inferior_quantity': orderdetail.inferior_quantity,
                    'all_quantity': orderdetail.inferior_quantity + orderdetail.arrival_quantity,
                    'in_inbound': int(orderdetail.chichu_id) in self.sku_data,
                }
                sku_dict.update({
                    'id': sku.id,
                    'properties_name': sku.properties_name or sku.properties_alias,
                    'barcode': sku.barcode
                })
                if self.is_allocated():
                    relation = self.get_relation(orderdetail)
                    sku_dict.update({
                        'has_relation': bool(relation),
                        'has_out_stock': bool(relation.inbounddetail.out_stock_cnt if relation else 0),
                        'inbound_total': self.sku_data.get(sku.id, 0),
                        'inbound_arrival_quantity': relation.arrival_quantity if relation else 0,
                        'inbound_inferior_quantity': relation.inferior_quantity if relation else 0,
                        'inbound_status_info': relation.inbounddetail.get_allocate_info() if relation else '',
                        'inbound_relation_id': relation.id if relation else ''
                    })
                product_dict['skus'].append(sku_dict)
                product_dict['sku_ids'] = [sku['id'] for sku in product_dict['skus']]
                cache_products[orderdetail.product_id] = product_dict
            for product_id in cache_products:
                orderlists_dict[orderlist.id]['products'].append(cache_products[product_id])
        for key, orderlist_dict in orderlists_dict.iteritems():
            orderlist_dict['len_of_sku'] = sum([len(i['skus']) for i in orderlist_dict['products']])
        return orderlists_dict

    def _build_orderlists(self, orderlist_ids):
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        product_ids = set()
        sku_ids = set()
        orderlists_dict = {}

        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            buyer_name = '未知'
            if orderlist.buyer_id:
                buyer_name = '%s%s' % (orderlist.buyer.last_name,
                                       orderlist.buyer.first_name)
                buyer_name = buyer_name or orderlist.buyer.username

            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': buyer_name,
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': status_mapping.get(orderlist.status) or '未知',
                'products': {}
            }

        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=orderlist_ids).order_by('id'):
            orderlist_dict = orderlists_dict[orderdetail.orderlist_id]
            product_id = int(orderdetail.product_id)
            sku_id = int(orderdetail.chichu_id)
            product_ids.add(product_id)
            sku_ids.add(sku_id)

            products_dict = orderlist_dict['products']
            skus_dict = products_dict.setdefault(product_id, {})

            skus_dict[sku_id] = {
                'buy_quantity': orderdetail.buy_quantity,
                'plan_quantity': orderdetail.buy_quantity - min(
                    orderdetail.arrival_quantity, orderdetail.buy_quantity),
                'orderdetail_id': orderdetail.id
            }

        saleproduct_ids = set()
        products_dict = {}
        for product in Product.objects.filter(id__in=list(product_ids)):
            products_dict[product.id] = {
                'id': product.id,
                'name': product.name,
                'saleproduct_id': product.sale_product,
                'outer_id': product.outer_id,
                'pic_path': product.pic_path,
                'ware_by': product.ware_by
            }
            saleproduct_ids.add(product.sale_product)

        skus_dict = {}
        for sku in ProductSku.objects.filter(id__in=list(sku_ids)):
            skus_dict[sku.id] = {
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias,
                'barcode': sku.barcode,
                'is_inbound': 1
            }

        saleproducts_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=list(saleproduct_ids)):
            saleproducts_dict[saleproduct.id] = {
                'product_link': saleproduct.product_link
            }

        orderlists = []
        for orderlist_id in sorted(orderlists_dict.keys()):
            orderlist_dict = orderlists_dict[orderlist_id]
            orderlist_products_dict = orderlist_dict['products']

            orderlist_products = []
            len_of_skus = 0
            for product_id in sorted(orderlist_products_dict.keys()):
                product_dict = copy.copy(products_dict[product_id])
                product_dict.update(saleproducts_dict.get(product_dict[
                                                              'saleproduct_id']) or {})
                orderlist_skus_dict = orderlist_products_dict[product_id]
                for sku_id in sorted(orderlist_skus_dict.keys()):
                    len_of_skus += 1
                    sku_dict = orderlist_skus_dict[sku_id]
                    sku_dict.update(skus_dict[sku_id])
                    product_dict.setdefault('skus', []).append(sku_dict)
                orderlist_products.append(product_dict)
            orderlist_dict['orderlist_id'] = orderlist_id
            orderlist_dict['products'] = orderlist_products
            orderlist_dict['len_of_skus'] = len_of_skus
            orderlists.append(orderlist_dict)
        return orderlists

    def products_item_sku(self):
        products = self.products
        for sku in self.product_skus:
            for product in products:
                if sku.product_id == product.id:
                    if not hasattr(product, 'detail_skus'):
                        product.detail_skus = []
                    product.detail_skus.append(sku)
                    break
                    continue
        for product in products:
            product.detail_sku_ids = [sku.id for sku in product.detail_skus]
            product.detail_length = len(product.detail_sku_ids)
        for detail in self.details.all():
            for product in products:
                if detail.sku_id in product.detail_sku_ids:
                    if not hasattr(product, 'detail_items'):
                        product.detail_items = []
                    product.detail_items.append(detail)
        return products

    def finish_check(self, data):
        """
            完成质检
        :return:
        """
        for inbound_detail_id in data:
            inbound_detail = InBoundDetail.objects.get(id=inbound_detail_id)
            if inbound_detail.checked:
                inbound_detail.set_quantity(data[inbound_detail_id]["arrivalQuantity"],
                                            data[inbound_detail_id]["inferiorQuantity"], update_stock=True)
            else:
                inbound_detail.set_quantity(data[inbound_detail_id]["arrivalQuantity"],
                                            data[inbound_detail_id]["inferiorQuantity"])
                inbound_detail.finish_check2()
        self.status = InBound.COMPLETED
        self.checked = True
        self.check_time = datetime.datetime.now()
        self.set_stat()
        self.save()
        self.update_orderlist_inbound()

    def need_return(self):
        if self.status != InBound.COMPLETE_RETURN:
            return self.wrong or self.out_stock
        else:
            return False

    def generate_return_goods(self, noter):
        from flashsale.dinghuo.models import ReturnGoods
        if self.need_return():
            ReturnGoods.generate_by_inbound(self, noter)
        self.status = InBound.COMPLETE_RETURN
        self.save()

    def reset_to_verify(self):
        self.status = InBound.WAIT_CHECK
        self.checked = False
        self.save()

    def reset_to_allocate(self):
        self.checked = False
        self.status = InBound.PENDING
        self.save()
        for detail in self.details.filter(checked=True):
            detail.reset_to_unchecked()

    def get_optimized_allocate_dict(self):
        """
           获取入库SKU的推荐分配方式
           1/优先分派给填入订货单号的订货单
           # 2/优先分派给可满足的订货单
           3/优先分派给时间早的订货单
        :return:
        """
        orderlist_ids = self.get_may_allocate_order_list_ids()
        first_orderlist = OrderList.objects.filter(id=self.ori_orderlist_id).first()
        if first_orderlist and first_orderlist.id in orderlist_ids:
            orderlists = [first_orderlist] + list(OrderList.objects.filter(id__in=orderlist_ids).exclude(
                id=first_orderlist.id).order_by('id'))
        else:
            orderlists = list(OrderList.objects.filter(id__in=orderlist_ids).order_by('id'))
        sku_data = self.sku_data
        skus = sku_data.keys()
        allocate_dict = {}
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.filter(chichu_id__in=skus):
                if orderdetail.need_arrival_quantity > 0 and sku_data[orderdetail.sku_id] > 0:
                    allocate_dict[orderdetail.id] = min(orderdetail.need_arrival_quantity, sku_data[orderdetail.sku_id])
                    sku_data[orderdetail.sku_id] -= allocate_dict[orderdetail.id]
        return allocate_dict

    def get_optimized_allocate_dict_bak(inbound):
        EXPRESS_NO_SPLIT_PATTERN = re.compile(r'\s+|,|，')
        express_no = inbound.express_no
        orderlist_id = inbound.ori_orderlist_id
        inbound_skus_dict = inbound.sku_data
        orderlist_ids = inbound.get_may_allocate_order_list_ids()
        boxes = []
        orderlists = []
        orderlist_ids_with_express_no = []
        for orderlist in OrderList.objects.filter(
                id__in=orderlist_ids).order_by('id'):
            orderlists.append(orderlist)
            orderlist_express_nos = [
                x.strip()
                for x in EXPRESS_NO_SPLIT_PATTERN.split(
                    orderlist.express_no.strip())
                ]
            if express_no and orderlist.express_no and express_no.strip(
            ) in orderlist_express_nos:
                orderlist_ids_with_express_no.append(orderlist_id)
            orderlist_skus_dict = {}
            for orderdetail in orderlist.order_list.all():
                orderlist_skus_dict[int(orderdetail.chichu_id)] = max(
                    orderdetail.buy_quantity - orderdetail.arrival_quantity, 0)
            row = []
            for sku_id in sorted(inbound_skus_dict.keys()):
                row.append(orderlist_skus_dict.get(sku_id) or 0)
            boxes.append(row)
        boxes = np.matrix(boxes)
        package = np.matrix([inbound_skus_dict[k]
                             for k in sorted(inbound_skus_dict.keys())])
        orderlist_ids = sorted(orderlist_ids)
        n = len(orderlist_ids)
        z = sys.maxint
        solution = 0
        for i in range(1, 1 << n):
            x = np.matrix([int(j) for j in ('{0:0%db}' % n).format(i)])
            tmp = np.dot(boxes.T, x.T) - package.T
            tmp = np.abs(tmp).sum()
            if z > tmp:
                z = tmp
                solution = i
        matched_orderlist_ids = []
        for i, j in enumerate(('{0:0%db}' % n).format(solution)):
            if int(j) > 0:
                matched_orderlist_ids.append(orderlist_ids[i])
        if orderlist_id and orderlist_id not in matched_orderlist_ids:
            matched_orderlist_ids.append(orderlist_id)
        tail_orderlist_ids = []
        for orderlist in orderlists:
            if orderlist.id in matched_orderlist_ids:
                continue
            if orderlist.id in orderlist_ids_with_express_no:
                matched_orderlist_ids.append(orderlist.id)
            else:
                tail_orderlist_ids.append(orderlist.id)
        orderlists = sorted(
            orderlists,
            key=
            lambda x: (matched_orderlist_ids + tail_orderlist_ids).index(x.id))
        allocate_dict = {}
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_num = inbound_skus_dict.get(sku_id)
                if not inbound_sku_num:
                    continue
                delta = min(
                    max(orderdetail.buy_quantity - orderdetail.arrival_quantity,
                        0), inbound_sku_num)
                if delta > 0:
                    allocate_dict[orderdetail.id] = delta
                    inbound_sku_num -= delta
                    if inbound_sku_num <= 0:
                        inbound_skus_dict.pop(sku_id, False)
        return allocate_dict

    def get_relation(self, order_detail):
        return OrderDetailInBoundDetail.objects.filter(inbounddetail__inbound__id=self.id,
                                                       orderdetail__id=order_detail.id).first()

    @property
    def all_quantity(self):
        return self.details.aggregate(n=Sum('arrival_quantity') + Sum('inferior_quantity')).get('n', 0) or 0

    @property
    def all_arrival_quantity(self):
        return self.details.filter(wrong=False).aggregate(n=Sum('arrival_quantity')).get('n', 0) or 0

    @property
    def all_allocate_quantity(self):
        return OrderDetailInBoundDetail.objects.filter(inbounddetail__inbound__id=self.id). \
                   aggregate(n=Sum('arrival_quantity')).get('n', 0) or 0

    @property
    def all_inferior_quantity(self):
        return self.details.filter(wrong=False).aggregate(n=Sum('inferior_quantity')).get('n', 0) or 0

    @property
    def out_stock_cnt(self):
        return sum([d.out_stock_cnt for d in self.details.all()])

    @property
    def error_cnt(self):
        return self.details.filter(wrong=True).aggregate(n=Sum('arrival_quantity')).get('n', 0) or 0

    @property
    def err_detail(self):
        if not hasattr(self, '_err_detail_'):
            self._err_detail_ = self.details.filter(wrong=True).first()
        return self._err_detail_

    def is_allocated(self):
        return self.status > InBound.PENDING

    def is_finished(self):
        return self.status >= InBound.COMPLETED

    def set_stat(self):
        ori_out_stock = self.out_stock
        ori_wrong = self.wrong
        ori_inferior = self.inferior
        self.out_stock = self.all_arrival_quantity > self.all_allocate_quantity
        self.wrong = self.details.filter(wrong=True).exists()
        self.inferior = self.all_inferior_quantity > 0
        if ori_out_stock == self.out_stock and ori_wrong == self.wrong and ori_inferior == self.inferior:
            change = False
        else:
            change = True
        return change

    def add_order_detail(self, orderdetail, num):
        oi = OrderDetailInBoundDetail.create(orderdetail, self, num)
        inbounddetail = self.details.filter(sku=orderdetail.sku).first()
        if inbounddetail.checked:
            ProductSku.objects.filter(id=inbounddetail.sku_id).update(quantity=F('quantity') + oi.arrival_quantity)
        return oi

    class Meta:
        db_table = 'flashsale_dinghuo_inbound'
        app_label = 'dinghuo'
        verbose_name = u'入仓单'
        verbose_name_plural = u'入仓单列表'


def update_warehouse_receipt_status(sender, instance, created, **kwargs):
    """
    update the warehouse receipt status to opened!
    """
    if created:
        from shopback.warehouse.models import ReceiptGoods
        ReceiptGoods.update_status_by_open(instance.express_no)


post_save.connect(update_warehouse_receipt_status, sender=InBound,
                  dispatch_uid='post_save_update_warehouse_receipt_status')


def refresh_inbound_order_status(sender, instance, created, **kwargs):
    if not created:
        from flashsale.forecast import apis
        apis.api_create_or_update_realinbound_by_inbound.delay(instance.id)


post_save.connect(refresh_inbound_order_status, sender=InBound,
                  dispatch_uid='post_save_refresh_inbound_order_status')


class InBoundDetail(models.Model):
    NORMAL = 1
    PROBLEM = 2

    OUT_ORDERING = 2
    ERR_ORDERING = 3
    ERR_OUT_ORDERING = 4

    inbound = models.ForeignKey(InBound,
                                related_name='details',
                                verbose_name=u'入库单')
    product = models.ForeignKey(Product,
                                null=True,
                                blank=True,
                                related_name='inbound_details',
                                verbose_name=u'入库商品')
    sku = models.ForeignKey(ProductSku,
                            null=True,
                            blank=True,
                            related_name='inbound_details',
                            verbose_name=u'入库规格')

    product_name = models.CharField(max_length=128, verbose_name=u'产品名称')
    outer_id = models.CharField(max_length=32, blank=True, verbose_name=u'颜色编码')
    properties_name = models.CharField(max_length=128,
                                       blank=True,
                                       verbose_name=u'规格')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'已到数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')

    checked = models.BooleanField(default=False, verbose_name=u"是否检查")
    check_time = models.DateTimeField(null=True, verbose_name=u"检查时间")
    wrong = models.BooleanField(default=False, verbose_name=u"是否有错")
    out_stock = models.BooleanField(default=False, verbose_name=u"是否多货")

    status = models.SmallIntegerField(
        default=PROBLEM,
        choices=((NORMAL, u'正常'), (PROBLEM, u'有问题')),
        verbose_name=u'状态')
    district = models.CharField(max_length=64, blank=True, verbose_name=u'库位')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'flashsale_dinghuo_inbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓单明细'
        verbose_name_plural = u'入仓单明细列表'

    def check_sync_quantity(inbounddetail):
        return inbounddetail.arrival_quantity == inbounddetail.records.aggregate(
            n=Sum('arrival_quantity')).get('n') and inbounddetail.inferior_quantity == inbounddetail.records.aggregate(
            n=Sum('inferior_quantity')).get('n')

    def sync_order_detail(self):
        for oi in self.records.all():
            oi.update_orderdetail()

    def change_total_quantity(self, num):
        """
            数量变化，不改变次品数
            如果总数大于分配数，则不改变分配数，如果总数小于分配数，则调整分配数使它重新等于总数
        :param num:
        :return:
        """
        self.arrival_quantity += num
        if self.arrival_quantity < 0:
            raise Exception(u"入库的正品数不可能小于0，请保证次品数正确")
        self.save()
        if self.arrival_quantity < self.all_allocate_quantity:
            change_total = self.all_allocate_quantity - self.arrival_quantity
            if self.records.exists():
                self.change_records_arrival_quantity(change_total, self.checked)

    def change_records_arrival_quantity(self, change_total, change_stock=False):
        """
            inbound_detail的arrival_quantity变化自动体现到records上
        :param change_total:
        :param change_stock:
        :return:
        """
        quantity_add = change_total
        for r in self.records.order_by('-id'):
            if r.arrival_quantity >= change_total:
                r.arrival_quantity -= change_total
                r.save()
                break
            else:
                r.arrival_quantity = 0
                r.save()
                change_total -= r.arrival_quantity
        if change_stock:
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') - quantity_add)

    @property
    def out_stock_num(self):
        all_allocate_quantity = self.all_allocate_quantity
        self.out_stock = self.arrival_quantity > all_allocate_quantity
        return self.arrival_quantity - all_allocate_quantity

    @property
    def all_allocate_quantity(self):
        total = self.records.aggregate(n=Sum("arrival_quantity")).get('n', 0)
        total = total if total else 0
        return total

    def get_status_info(self):
        if self.out_stock:
            return u'多货'
        else:
            return u'完全分配'

    def get_allocate_info(self):
        if self.out_stock_num > 0:
            return u'多货'
        return u'完全分配'

    def reset_out_stock(self):
        ori_out_stock = self.out_stock
        self.out_stock = self.out_stock_num > 0
        if ori_out_stock != self.out_stock:
            InBoundDetail.objects.filter(id=self.id).update(out_stock=self.out_stock)

    def reset_to_unchecked(self):
        if self.checked:
            self.checked = False
            self.save()
            arrival_total = self.records.aggregate(n=Sum("arrival_quantity")).get('n', 0)
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') - arrival_total)

    def finish_change_inferior(self, arrival_quantity, inferior_quantity):
        """
            完成质检同时更改次品数
        :param arrival_quantity:
        :param inferior_quantity:
        :return:
        """
        self.set_quantity(arrival_quantity, inferior_quantity)
        self.finish_check2()

    def finish_check(self):
        """
            完成质检
        :return:
        """
        if self.wrong:
            raise Exception(u"错货无法通过质检")
        if not self.status == InBoundDetail.NORMAL:
            self.status = InBoundDetail.NORMAL
        if not self.checked:
            self.checked = True
            self.check_time = datetime.datetime.now()
            self.status = InBoundDetail.NORMAL
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') + self.all_allocate_quantity)
        self.save()

    def finish_check2(self):
        if self.checked:
            return
        self.checked = True
        self.check_time = datetime.datetime.now()
        self.status = InBoundDetail.NORMAL
        ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') + self.all_allocate_quantity)
        self.save()

    def set_quantity(self, arrival_quantity, inferior_quantity, update_stock=False):
        """
            设置库存
        :param arrival_quantity:
        :param inferior_quantity:
        :param update_stock:
        :return:
        """
        if self.arrival_quantity == arrival_quantity and self.inferior_quantity == inferior_quantity:
            return
        if arrival_quantity + inferior_quantity != self.arrival_quantity + self.inferior_quantity:
            raise Exception(u'改变次品时总数量不能发生变化')
        self.inferior_quantity = inferior_quantity
        self.arrival_quantity = arrival_quantity
        if self.records.exists() and self.arrival_quantity < self.all_allocate_quantity:
            # 已经分配到订货单的必须同步修正订货单
            change = self.all_allocate_quantity - self.arrival_quantity
            self.set_records_quantity(change, update_stock)
        self.save()

    def set_records_quantity(self, change_total, update_stock):
        """
            inbound_detail的arrival_quantity的减少自动体现到records上
        :param change_total:
        :param change_stock:
        :return:
        """
        quantity_change = change_total
        for r in self.records.order_by('-id'):
            if r.arrival_quantity >= change_total:
                r.arrival_quantity -= change_total
                r.save()
                break
            else:
                r.arrival_quantity = 0
                r.save()
                change_total -= r.arrival_quantity
        if update_stock:
            ProductSku.objects.filter(id=self.sku_id).update(quantity=F('quantity') - quantity_change)

    @property
    def out_stock_cnt(self):
        if self.wrong:
            return 0
        total = self.records.aggregate(n=Sum("arrival_quantity")).get('n', None)
        total = 0 if total is None else total
        return self.arrival_quantity - total

    @staticmethod
    def get_inferior_total(sku_id, begin_time=datetime.datetime(2016, 4, 20)):
        res = InBoundDetail.objects.filter(
            sku_id=sku_id, check_time__gte=begin_time, checked=True).aggregate(
            n=Sum("inferior_quantity")).get('n', 0)
        return res or 0


def update_inferiorsku_inbound_quantity(sender, instance, created, **kwargs):
    if instance.checked:
        from shopback.items.tasks import task_update_inferiorsku_inbound_quantity
        task_update_inferiorsku_inbound_quantity.delay(instance.sku_id)


post_save.connect(update_inferiorsku_inbound_quantity,
                  sender=InBoundDetail,
                  dispatch_uid='post_save_update_inferiorsku_inbound_quantity')


def update_stock(sender, instance, created, **kwargs):
    if instance.checked:
        instance.sync_order_detail()
        instance.reset_out_stock()
        if instance.inbound.set_stat():
            instance.inbound.save()
        from shopback.items.tasks import task_update_productskustats_inferior_num
        task_update_productskustats_inferior_num.delay(instance.sku_id)


post_save.connect(update_stock,
                  sender=InBoundDetail,
                  dispatch_uid='post_save_update_stock')


class OrderDetailInBoundDetail(models.Model):
    INVALID = 0
    NORMAL = 1
    orderdetail = models.ForeignKey(OrderDetail, related_name='records', verbose_name=u'订货明细')
    inbounddetail = models.ForeignKey(InBoundDetail, related_name='records', verbose_name=u'入仓明细')
    arrival_quantity = models.IntegerField(default=0, blank=True, verbose_name=u'正品数')
    inferior_quantity = models.IntegerField(default=0, blank=True, verbose_name=u'次品数')
    status = models.SmallIntegerField(
        default=NORMAL,
        choices=((NORMAL, u'正常'), (INVALID, u'无效')),
        verbose_name=u'状态')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'dinghuo_orderdetailinbounddetail'
        app_label = 'dinghuo'
        verbose_name = u'入仓订货明细对照'
        verbose_name_plural = u'入仓订货明细对照列表'

    @staticmethod
    def create(orderdetail, inbound, arrival_quantity, inferior_quantity=0):
        inbounddetail = inbound.details.get(sku_id=orderdetail.chichu_id)
        oi = OrderDetailInBoundDetail(orderdetail=orderdetail, inbounddetail=inbounddetail,
                                      arrival_quantity=arrival_quantity, inferior_quantity=inferior_quantity)
        oi.save()
        return oi

    def change_arrival_quantity(self, num):
        if self.inbounddetail.out_stock_cnt < num:
            raise Exception(u"入库数不足进行分配")
        if self.orderdetail.need_arrival_quantity < num:
            raise Exception(u"分配数超出订货待入库数")
        self.arrival_quantity += num
        if self.arrival_quantity < 0:
            raise Exception(u"入库数不能小于0")
        self.save()
        if self.inbounddetail.checked:
            ProductSku.objects.filter(id=self.inbounddetail.sku_id).update(quantity=F('quantity') + num)
        return True

    def update_orderdetail(self):
        orderdetail = self.orderdetail
        orderdetail.arrival_quantity = orderdetail.records.filter(
            inbounddetail__checked=True).aggregate(
            n=Sum('arrival_quantity')).get('n') or 0
        orderdetail.inferior_quantity = orderdetail.records.filter(
            inbounddetail__checked=True).aggregate(
            n=Sum('inferior_quantity')).get('n') or 0
        orderdetail.non_arrival_quantity = orderdetail.buy_quantity - orderdetail.arrival_quantity \
                                           - orderdetail.inferior_quantity
        orderdetail.arrival_time = orderdetail.records.order_by('-created').first().created
        orderdetail.save()


def update_inbound_record(sender, instance, created, **kwargs):
    instance.inbounddetail.reset_out_stock()


post_save.connect(update_inbound_record,
                  sender=OrderDetailInBoundDetail,
                  dispatch_uid='post_save_orderdetail_inbounddetail_update_inbound_record')


def update_orderdetail_record(sender, instance, created, **kwargs):
    instance.update_orderdetail()


post_save.connect(update_orderdetail_record,
                  sender=OrderDetailInBoundDetail,
                  dispatch_uid='post_save_orderdetail_inbounddetail_update_orderdetail_record')
