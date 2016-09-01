# coding=utf-8
__author__ = 'yan.huang'
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions
from core.xlmm_response import SUCCESS_RESPONSE
from flashsale.promotion.serializers import StockSaleSerializers
from flashsale.promotion.models.stocksale import *
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
import logging

log = logging.getLogger('django.request')


class StockSaleViewSet(viewsets.GenericViewSet):
    """
        库存
    """
    queryset = StockSale.objects.all()
    serializer_class = StockSaleSerializers
    authentication_classes = (
    authentication.SessionAuthentication, permissions.DjangoModelPermissions, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET', 'POST'])
    def gen_new_stock_sale(self, request):
        StockSale.gen_new_stock_sale(request.user.username)
        return HttpResponseRedirect('/admin/promotion/batchstocksale/')

    @list_route(methods=['GET', 'POST'])
    def gen_new_activity(self, request):
        StockSale.gen_new_activity(request.user.username)
        return HttpResponseRedirect('/admin/promotion/activitystocksale/')

    @detail_route(methods=['GET', 'POST'])
    def gen_activity_entry(self, request, pk):
        activity = get_object_or_404(ActivityStockSale, pk=pk)
        if not activity.activity:
            try:
                activity.gen_activity_entry()
            except Exception, e:
                raise exceptions.ValidationError(e.message)
        return HttpResponseRedirect('/admin/promotion/activitystocksale/')

    @list_route(methods=['POST'])
    def update_status(self, request):
        ids = request.POST.get('ids')
        sales = StockSale.objects.filter(id__in=ids.split(','))
        if sales.count() == 0:
            raise exceptions.ValidationError(u'找不到指定的库存销售记录')
        status = request.GET.get('status') or request.POST.get('status')
        try:
            status = int(status)
            if status not in [0, 1, 2]:
                raise exceptions.ValidationError(u'库存销售记录的状态只能取0,1,2')
        except:
            raise exceptions.ValidationError(u'库存销售记录的状态只能取0,1,2')
        sales.update(status=status)
        return Response(SUCCESS_RESPONSE)

    @detail_route(methods=['GET', 'POST'])
    def reset_sale(self, request, pk):
        sale = get_object_or_404(StockSale, pk=pk)
        sale.day_batch_num = 0
        sale.status = 0
        sale.save()
        return Response(SUCCESS_RESPONSE)

    @list_route(methods=['POST'])
    def update_stock_safe(self, request):
        ids = request.POST.get('ids')
        sales = StockSale.objects.filter(id__in=ids.split(','))
        if sales.count() == 0:
            raise exceptions.ValidationError(u'找不到指定的库存销售记录')
        stock_safe = request.GET.get('stock_safe') or request.POST.get('stock_safe')
        try:
            stock_safe = int(stock_safe)
            if stock_safe not in [0, 1, 2]:
                raise exceptions.ValidationError(u'库存销售记录的状态只能取0,1')
        except:
            raise exceptions.ValidationError(u'库存销售记录的状态只能取0,1')
        for sale in sales:
            sale.stock_safe = stock_safe
            sale.save()
        return Response(SUCCESS_RESPONSE)
