# coding=utf-8
import re
import datetime
import django_filters
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_statsd.clients import statsd

from rest_framework import exceptions
from rest_framework import filters
from rest_framework import viewsets, permissions, authentication, renderers
from rest_framework.response import Response
from rest_framework.decorators import list_route

from flashsale.pay.models import Customer
from flashsale.pay.models.product import ModelProduct
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver, MamaVebViewConf
from flashsale.xiaolumm.tasks import task_mama_daily_tab_visit_stats
from flashsale.xiaolumm.apis.v1.ninepic import get_nine_pic_by_modelids
from flashsale.pay.apis.v1.customer import get_customer_by_django_user
from . import serializers


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
    """
    queryset = NinePicAdver.objects.all()
    serializer_class = serializers.NinePicAdverSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = '__all__'
    filter_class = NinePicAdverFilter

    def get_today_queryset(self, queryset):
        yesetoday = datetime.date.today() - datetime.timedelta(days=1)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        now = datetime.datetime.now()
        queryset = queryset.filter(start_time__gte=yesetoday,
                                   start_time__lt=tomorrow).filter(start_time__lt=now)
        return queryset

    def get_xlmm(self):
        if not hasattr(self, '_xlmm_'):
            customer = get_customer_by_django_user(self.request.user)
            self._xlmm_ = customer.get_xiaolumm()
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
        queryset = self.get_today_queryset(self.get_queryset())
        if request.data.get('ordering') is None:
            queryset = queryset.order_by('-start_time')
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        # 统计代码
        if xlmm:
            statsd.incr('xiaolumm.ninepic_count')
            task_mama_daily_tab_visit_stats.delay(xlmm.id, MamaTabVisitStats.TAB_DAILY_NINEPIC)
        return Response(serializer.data)

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
    @method_decorator(cache_page(30))
    def today(self, req, *args, **kwargs):
        q_hour = req.GET.get('hour')
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        try:
            q_hour = int(q_hour)
        except:
            q_hour = None

        if q_hour:
            start_time = datetime.datetime(today.year, today.month, today.day, q_hour)
            end_time = start_time + datetime.timedelta(hours=1)
            queryset = NinePicAdver.objects.filter(start_time__gte=start_time, start_time__lt=end_time)
            print start_time, end_time
        else:
            queryset = NinePicAdver.objects.filter(start_time__gte=today, start_time__lt=tomorrow)

        items = []
        for item in queryset:
            for model_id in re.split(u',|，', item.detail_modelids):
                if not model_id or item in items:
                    continue
                item.model_id = model_id.strip()
                items.append(item)

        virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()  # 虚拟商品

        data = []
        for item in items:
            model_id = item.model_id
            mp = ModelProduct.objects.get(id=model_id)
            coupon_template_id = mp.extras.get('payinfo', {}).get('coupon_template_ids', [])
            coupon_template_id = coupon_template_id[0] if coupon_template_id else None

            find_mp = None

            for md in virtual_model_products:
                md_bind_tpl_id = md.extras.get('template_id')
                if md_bind_tpl_id and coupon_template_id == md_bind_tpl_id:
                    find_mp = md
                    break

            if not find_mp:
                continue

            prices = [x.agent_price for x in find_mp.products]
            min_price = min(prices)
            max_price = max(prices)

            data.append({
                'pic': mp.head_img(),
                'name': mp.name,
                'price': mp.lowest_agent_price,
                'profit': {
                    'min': mp.lowest_agent_price - max_price,
                    'max': mp.lowest_agent_price - min_price
                },
                'start_time': item.start_time,
                'hour': item.start_time.hour,
                'model_id': model_id
            })

        data = sorted(data, key=lambda x: x['hour'])
        import itertools
        group = itertools.groupby(data, lambda x: x['hour'])
        result = []
        for key, items in group:
            result.append({
                'hour': key,
                'items': list(items)
            })

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
