# coding=utf-8
import re
import datetime
import django_filters
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.decorators import method_decorator
from django_statsd.clients import statsd
from django.core.cache import cache

from rest_framework import exceptions
from rest_framework import filters
from rest_framework import viewsets, permissions, authentication, renderers
from rest_framework.response import Response
from rest_framework.decorators import list_route

from flashsale.pay.models import Customer
from flashsale.pay.models.product import ModelProduct
from flashsale.promotion.models import ActivityEntry
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver, MamaVebViewConf
from flashsale.xiaolumm.tasks import task_mama_daily_tab_visit_stats
from flashsale.xiaolumm.apis.v1.ninepic import get_nine_pic_by_modelids
from flashsale.pay.apis.v1.customer import get_customer_by_django_user
from flashsale.restpro.local_cache import get_image_watermark_cache
from . import serializers
import logging
from .permission import IsAccessNinePicAdver
logger = logging.getLogger(__name__)


class XlmmAdvertisViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－代理公告API:
    - {prefix}[.format] method:get : 获取登陆用户的代理公告
    """
    queryset = XlmmAdvertis.objects.all()
    serializer_class = serializers.XlmmAdvertisSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)
        return self.queryset.filter(show_people=xlmm.agencylevel, is_valid=True)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        advers = []
        now = datetime.datetime.now()
        for adver in queryset:
            if now >= adver.start_time and now <= adver.end_time:
                advers.append(adver)
        serializer = self.get_serializer(advers, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response({})


class NinePicAdverFilter(filters.FilterSet):
    sale_category = django_filters.NumberFilter(name="sale_category__cid")

    class Meta:
        model = NinePicAdver
        fields = ['id', 'sale_category']


class NinePicAdverViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－九张图API:
    - {prefix}[.format] method:get : 获取九张图
    `could_share`: 标记当前的九张图记录是否可以用来分享
    - page_list :获取特卖推广文案列表(分页支持，截止当前时间已发布的所有推送)
      - model_id: 款式ID(可选)
    """
    queryset = NinePicAdver.objects.all()
    serializer_class = serializers.NinePicAdverSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = '__all__'
    filter_class = NinePicAdverFilter

    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'

    def get_today_queryset(self, queryset):
        yesetoday = datetime.date.today() - datetime.timedelta(days=1)
        # tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        now = datetime.datetime.now()
        queryset = queryset.filter(start_time__range=(yesetoday, now))
        return queryset

    def get_xlmm(self):
        if not hasattr(self, '_xlmm_'):
            customer = get_customer_by_django_user(self.request.user)
            self._xlmm_ = customer and customer.get_xiaolumm() or None
        return self._xlmm_

    def get_serializer_context(self):
        xlmm = self.get_xlmm()
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            "mama_id": xlmm.id if xlmm else 0
        }

    @list_route(methods=['get'])
    def get_nine_pic_by_modelid(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> HttpResponse
        model_id = request.GET.get('model_id')
        model_ids = [i.strip() for i in model_id.split(',') if i.isdigit()]
        ns = get_nine_pic_by_modelids(model_ids)
        serializer = self.get_serializer(ns, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        xlmm = self.get_xlmm()
        object_id = request.GET.get('id')
        if object_id:
            queryset = self.get_queryset().filter(id=object_id)
        else:
            queryset = self.get_today_queryset(self.get_queryset())

        if request.GET.get('ordering') is None:
            queryset = queryset.order_by('-start_time', '-turns_num')
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        # 统计代码
        if not object_id and xlmm:
            statsd.incr('xiaolumm.ninepic_count')
            task_mama_daily_tab_visit_stats.delay(xlmm.id, MamaTabVisitStats.TAB_DAILY_NINEPIC)

        return Response(serializer.data)

    @list_route(methods=['get'])
    def page_list(self, request, *args, **kwargs):
        request_data = request.GET
        # start_time before now
        now_dt = datetime.datetime.now()
        queryset = NinePicAdver.objects
        model_id = request_data.get('model_id')

        if request_data.get('model_id'):
            queryset = queryset.filter_by_modelproduct(request_data.get('model_id'))

        if request_data.get('ordering') is None:
            queryset = queryset.order_by('-start_time', '-turns_num')

        queryset = queryset.filter(start_time__lte=now_dt)
        queryset = self.filter_queryset(queryset)
        pagin_query = self.paginate_queryset(queryset)

        profit = {'max': 0, 'min': 0}
        if model_id:
            mp = ModelProduct.objects.filter(id=model_id).first()
            if mp:
                profit = mp.get_model_product_profit()

        for item in pagin_query:
            item.profit = profit

        serializer = self.get_serializer(pagin_query, many=True)
        response = self.get_paginated_response(serializer.data)
        # 统计代码
        xlmm = self.get_xlmm()
        if xlmm:
            statsd.incr('xiaolumm.ninepic_count')
            task_mama_daily_tab_visit_stats.delay(xlmm.id, MamaTabVisitStats.TAB_DAILY_NINEPIC)
        return response

    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        """
        功能: 用户更新分享次数和保存次数
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        save_times = request.data.get('save_times') or 0
        share_times = request.data.get('share_times') or 0
        save_times = min(int(save_times), 1)
        share_times = min(int(share_times), 1)
        request_data = request.data.copy()
        request_data.update({'save_times': instance.save_times + save_times})
        request_data.update({'share_times': instance.share_times + share_times})
        serializer = serializers.ModifyTimesNinePicAdverSerialize(instance, data=request_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException("方法不允许")


class NinePicViewSet(viewsets.GenericViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication,)

    @list_route(methods=['get'])
    def today(self, req, *args, **kwargs):
        q_hour = req.GET.get('hour')
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        show_profit = False

        try:
            q_hour = int(q_hour)
        except:
            q_hour = None

        if not req.user.is_anonymous:
            customer = Customer.objects.filter(user=req.user).first()
            if customer:
                mama = customer.get_xiaolumm()
                if mama and mama.last_renew_type >= 90:
                    show_profit = True

        if show_profit:
            resp_result = cache.get('rest/v1/pmt/ninepic/today-%s' % q_hour)
        else:
            resp_result = cache.get('rest/v1/pmt/ninepic/today-noprofit-%s' % q_hour)

        if resp_result:
            return Response(resp_result)

        if q_hour:
            start_time = datetime.datetime(today.year, today.month, today.day, q_hour)
            end_time = start_time + datetime.timedelta(hours=1)

            queryset = ActivityEntry.objects.filter(start_time__gte=start_time, start_time__lt=end_time,
                                                    act_type = ActivityEntry.ACT_FOCUS)
        else:
            queryset = ActivityEntry.objects.filter(start_time__lt=today, end_time__gt=today,
                                                    act_type = ActivityEntry.ACT_FOCUS)

        items = []
        for activity in queryset:
            products = activity.activity_products.all()
            activity_id = activity.id
            for product in products:
                model_id = product.model_id
                if not model_id:
                    continue
                item = {
                    'model_id': model_id,
                    'activity_id': activity_id,
                    'start_time': activity.start_time
                }
                if item in items:
                    continue
                items.append(item)

        virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()

        data = []
        for item in items:
            try:
                model_id = item['model_id']
                mp = ModelProduct.objects.filter(id=model_id).first()
                profit = mp.get_model_product_profit(virtual_model_products=virtual_model_products)

                data_item = {
                    'pic': mp.head_img(),
                    'name': mp.name,
                    'price': mp.lowest_agent_price,
                    'profit': {
                        'min': profit.get('min', 0),
                        'max': profit.get('max', 0)
                    },
                    'start_time': item['start_time'],
                    'hour': item['start_time'].hour,
                    'model_id': model_id,
                    'activity_id': item['activity_id'],
                    'watermark_op': get_image_watermark_cache(mark_size=200),
                }
                if not show_profit:
                    data_item['profit'] = {'min': 0, 'max': 0}

                data.append(data_item)
            except Exception, exc:
                logger.error(u'九张图首页接口报错,err=%s' % exc.message, exc_info=True)
                continue

        data = sorted(data, key=lambda x: x['hour'])
        import itertools
        group = itertools.groupby(data, lambda x: x['hour'])
        result = []
        for key, items in group:
            result.append({
                'hour': key,
                'items': list(items)
            })

        if show_profit:
            cache.set('rest/v1/pmt/ninepic/today-%s' % q_hour, result, 60*30)
        else:
            cache.set('rest/v1/pmt/ninepic/today-noprofit-%s' % q_hour, result, 60*30)

        return Response(result)


class MamaVebViewConfFilter(filters.FilterSet):
    class Meta:
        model = MamaVebViewConf
        fields = ['version', "id"]


class MamaVebViewConfViewSet(viewsets.ModelViewSet):
    """
    ### 小鹿妈妈主页webview配置接口:
    - [/rest/v1/mmwebviewconfig](/rest/v1/mmwebviewconfig) 配置列表(仅返回有效配置):
        * method : GET
            * 可过滤字段：　`version`, `id`
    """
    queryset = MamaVebViewConf.objects.filter(is_valid=True)
    serializer_class = serializers.MamaVebViewConfSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = MamaVebViewConfFilter

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')
