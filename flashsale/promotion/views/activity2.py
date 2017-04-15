# coding=utf-8
import datetime
import django_filters
from operator import itemgetter
from itertools import groupby

from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from django.shortcuts import get_object_or_404

from pms.supplier.models import SaleProductManage
from ..models.activity import ActivityEntry, ActivityProduct
from ..serializers.activity import ActivitySerializer, ActivityProductSerializer
from ..apis.activity import get_activity_by_id, create_activity, update_activity, get_activity_pros_by_activity_id, \
    get_activity_pro_by_id, create_activity_pro, create_activity_pros_by_schedule_id, update_activity_pro, \
    delete_activity_pro,change_activitygoods_position
from ..utils import choice_2_name_value
from ..deps import get_future_topic_schedules

import logging
from .permission import IsAccessMallActivity
logger = logging.getLogger(__name__)


class ActivityEntryFilter(filters.FilterSet):
    class Meta:
        model = ActivityEntry
        fields = ['id', 'is_active', 'act_type']


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = ActivityEntry.objects.all().order_by('-order_val', '-start_time')
    serializer_class = ActivitySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    permission_classes = (IsAccessMallActivity,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = ActivityEntryFilter

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException(u'不予删除操作')

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        act_type = choice_2_name_value(ActivityEntry.ACT_CHOICES)
        f_schedules = SaleProductManage.objects.activeable_topic_schedules()\
            .order_by('sale_time').values('id', 'upshelf_time', 'offshelf_time')
        return Response({
            'act_type': act_type,
            'schedules': f_schedules,
            'is_active': [{'name': '上线', 'value': True},
                          {'name': '不上线', 'value': False}],
            'login_required': [{'name': '需要登陆', 'value': True},
                               {'name': '无需登陆', 'value': False}],
        })

    def create(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        title = request.data.pop('title')
        act_type = request.data.pop('act_type')
        schedule_id = None
        if request.data.has_key('schedule_id'):
            schedule_id = request.data.pop('schedule_id')
            request.data.update({'extras': {'schedule_id': schedule_id}})
        else:
            request.data.update({'extras': {}})
        start_time = datetime.datetime.strptime(request.data.pop('start_time'), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(request.data.pop('end_time'), '%Y-%m-%d %H:%M:%S')
        activity = create_activity(
            title=title,
            act_type=act_type,
            start_time=start_time,
            end_time=end_time,
            **request.data
        )
        serializer = self.get_serializer(activity)
        headers = self.get_success_headers(serializer.data)
        if schedule_id and activity:
            create_activity_pros_by_schedule_id(activity.id, int(schedule_id))
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        partial = kwargs.pop('partial', False)
        instance_id = kwargs.get('pk')
        activity = get_activity_by_id(instance_id)
        if request.data.has_key('start_time'):
            start_time = datetime.datetime.strptime(request.data.pop('start_time'), '%Y-%m-%d %H:%M:%S')
            request.data.update({'start_time': start_time})
        if request.data.has_key('end_time'):
            end_time = datetime.datetime.strptime(request.data.pop('end_time'), '%Y-%m-%d %H:%M:%S')
            request.data.update({'end_time': end_time})
        # request.data.update({'act_link': activity.act_link})
        serializer = self.get_serializer(activity, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        update_activity(instance_id, **request.data)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def correlate_schedule(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """关联排期
        """
        activity_id = int(kwargs.get('pk'))
        schedule_id = request.POST.get('schedule_id')
        activity = get_activity_by_id(activity_id)
        if not schedule_id:
            schedule_id = activity.schedule_id
        if not schedule_id:
            raise exceptions.APIException(u'没有找到关联的排期Id')
        aps = create_activity_pros_by_schedule_id(activity.id, int(schedule_id))
        serializer = ActivityProductSerializer(aps, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def pro_list_filters(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        pic_type = choice_2_name_value(ActivityProduct.PIC_TYPE_CHOICES)
        return Response({'pic_type': pic_type})

    @list_route(methods=['get'])
    def active_pro(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        pro_id = request.GET.get('id')
        pro = get_activity_pro_by_id(int(pro_id))
        serializer = ActivityProductSerializer(pro)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def active_pros(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        activity_id = int(kwargs.get('pk'))
        activity_pros = get_activity_pros_by_activity_id(activity_id)
        serializer = ActivityProductSerializer(activity_pros, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def create_pro(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        activity_id = kwargs.get('pk')
        product_img = request.data.pop('product_img')
        ap = create_activity_pro(activity_id, product_img, **request.data)
        serializer = ActivityProductSerializer(ap)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def update_pro(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        activity_pro_id = kwargs.get('pk')
        ap = update_activity_pro(activity_pro_id, **request.data)
        serializer = ActivityProductSerializer(ap)
        return Response(serializer.data)

    @list_route(methods=['delete'])
    def destroy_pro(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        activity_pro_id = request.data.pop('id')
        delete_activity_pro(activity_pro_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


    @detail_route(methods=['post'])
    def change_activitygoods_position(self, request,pk):
        direction = request.data.get('direction')
        distance = request.data.get("distance")
        activity_entry_id = request.data.get("activity_entry_id") or pk
        activity_product_id = request.data.get("activity_product_id")
        data = {'activity_entry_id': activity_entry_id, 'direction': direction, 'distance': distance}
        result = change_activitygoods_position(activity_product_id,**data)
        if result:
            return Response({"info": "调整成功"})
        else:
            return Response({"info":"调整失败"},status=400)




