# -*- coding:utf-8 -*-
from flashsale.xiaolumm.models.message import XlmmMessage
from ..models.models import CashOut, CarryLog, XiaoluMama
from ..models.carry_total import MamaCarryTotal, MamaTeamCarryTotal
from ..models.rank import WeekMamaTeamCarryTotal, WeekMamaCarryTotal
from ..models.models_advertis import NinePicAdver
from rest_framework import serializers


class CashOutStatusField(serializers.Field):
    def to_representation(self, obj):
        for choice in CashOut.STATUS_CHOICES:
            if choice[0] == obj:
                return choice[1]
        return ""

    def to_internal_value(self, data):
        return data


class CashOutSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%Y-%m-%d")
    status = CashOutStatusField()

    class Meta:
        model = CashOut
        fields = ('xlmm', 'value', 'value_money', 'status', 'created')


class CarryLogSerializer(serializers.ModelSerializer):
    carry_date = serializers.DateTimeField(format="%y-%m-%d")

    class Meta:
        model = CarryLog
        fields = ('xlmm', 'order_num', 'buyer_nick', 'value', 'value_money', 'log_type',
                  'log_type_name', 'carry_type', 'carry_type_name', 'status_name', 'carry_date')


class NinePicAdverSerializer(serializers.ModelSerializer):
    # start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    cate_gory_display = serializers.CharField(source='get_cate_gory_display', read_only=True)

    class Meta:
        model = NinePicAdver
        fields = (
            "id",
            "auther",
            "title",
            "description",
            "cate_gory",
            "pic_arry",
            "start_time",
            "turns_num",
            "is_pushed",
            "detail_modelids",
            "cate_gory_display")


class XiaoluMamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = XiaoluMama
        fields = ('id', 'mobile', 'openid', 'province', 'city', 'address', 'referal_from', 'qrcode_link', 'weikefu',
                  'manager', 'cash', 'pending', 'hasale', 'last_renew_type', 'agencylevel', 'target_complete',
                  'lowest_uncoushout', 'user_group', 'charge_time', 'renew_time', 'created', 'modified', 'status',
                  'charge_status', 'progress')


class MamaCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'mobile', 'total', 'total_display', 'num', 'total', 'rank')


class MamaCarryTotalDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'mobile', 'duration_total', 'duration_total_display', 'duration_rank')


class ActivityMamaCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'mobile', 'duration_num', 'stat_time', 'total',
            'duration_total', 'duration_total_display', 'rank')


class MamaTeamCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'mobile', 'num', 'total', 'duration_total', 'rank')


class MamaTeamCarryTotalDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaTeamCarryTotal
        fields = ('mama', 'mama_nick', 'thumbnail', 'mobile', 'duration_total', 'duration_total_display', 'duration_rank')


class ActivityMamaTeamCarryTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = MamaTeamCarryTotal
        fields = (
            'mama', 'mama_nick', 'thumbnail', 'mobile', 'stat_time', 'duration_num', 'duration_total',
            'duration_total_display', 'rank')


class XlmmMessageSerializers(serializers.ModelSerializer):
    class Meta:
        model = XlmmMessage
        fields = ('id', 'title', 'content_link', 'content', 'dest', 'status', 'read', 'created', 'creator')