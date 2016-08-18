# coding: utf-8

import copy
import time

from django.conf import settings
from django.db import connection
from django.shortcuts import get_object_or_404

from rest_framework import authentication, renderers, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from flashsale.pay.models import Customer

from . import constants, models, serializers, tasks


class PushViewSet(viewsets.ModelViewSet):
    """
    * set_device(post方式)

        - platform  - 平台类型, ios/android
        - regid - 小米提供的regid
        - device_id - 手机设备号
        - ios_token - ios的token, 仅ios需要

        返回{"user_account": "customer-19"}

    """

    queryset = models.PushTopic.objects.all()
    serializer_class = serializers.PushTopicSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = ()
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['post'])
    def set_device(self, request, *args, **kwargs):
        from flashsale.xiaolumm.models import XiaoluMama
        if not request.user or request.user.is_anonymous():
            # 未登录用户不做处理
            return Response({'user_account': ''})
        # 验证表单数据
        now = time.time()
        raw_data = copy.copy(request.data)
        raw_data['update_time'] = now
        serializer = serializers.PushTopicSerializer(data=raw_data)
        if not serializer.is_valid():
            return Response({'user_account': ''})
        validated_data = serializer.validated_data
        platform = validated_data['platform']
        device_id = validated_data.get('device_id') or ''
        regid = validated_data['regid']

        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        if not customer:
            return Response({'user_account': ''})

        def _do_with_topic_by_cat(cat, topic):
            rows = models.PushTopic.objects.filter(cat=cat,
                                                   platform=platform,
                                                   device_id=device_id)
            new_data = copy.copy(validated_data)
            new_data.update({
                'cat': cat,
                'topic': topic,
                'customer_id': customer.id,
                'update_time': now
            })
            flag = False
            if not rows:
                flag = True
                row = serializer.create(new_data)
            else:
                row = rows[0]
                if time.time() - row.update_time > 3600:
                    flag = True
                serializer.update(row, new_data)
            if flag:
                if settings.DEBUG:
                    tasks.subscribe(platform, regid, topic)
                else:
                    tasks.subscribe.delay(platform, regid, topic)

        # 获取用户会员信息
        xlmm = XiaoluMama.objects.filter(openid=customer.unionid).first()
        topic_cats = [(constants.TOPIC_CAT_MEMBER, constants.TOPIC_XLMM)]
        if xlmm and xlmm.openid:
            agency_level = xlmm.agencylevel
            if agency_level == XiaoluMama.VIP_LEVEL:
                topic_cats.append((constants.TOPIC_CAT_MEMBER_LEVEL, constants.TOPIC_XLMM_VIP))
            if agency_level == XiaoluMama.A_LEVEL:
                topic_cats.append((constants.TOPIC_CAT_MEMBER_LEVEL, constants.TOPIC_XLMM_A))
        for cat, topic in topic_cats:
            _do_with_topic_by_cat(cat, topic)
        return Response({'user_account': 'customer-%d' % customer.id})
