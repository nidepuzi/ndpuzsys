# coding=utf-8
from rest_framework import serializers
from flashsale.coupon.models import CouponTemplate, UserCoupon, OrderShareCoupon, TmpShareCoupon


class CouponTemplateSerialize(serializers.ModelSerializer):
    class Meta:
        model = CouponTemplate


class UserCouponSerialize(serializers.ModelSerializer):
    coupon_value = serializers.FloatField(source='value', read_only=True)
    valid = serializers.BooleanField(source='is_valid_template', read_only=True)
    use_fee = serializers.FloatField(source='min_payment', read_only=True)
    use_fee_des = serializers.CharField(source='coupon_use_fee_des', read_only=True)
    pros_desc = serializers.CharField(source='scope_type_desc', read_only=True)
    start_time = serializers.DateTimeField(source='start_use_time', read_only=True)
    poll_status = serializers.IntegerField(source='get_pool_status', read_only=True)
    customer = serializers.IntegerField(source='customer_id', read_only=True)
    coupon_type_display = serializers.CharField(source='get_coupon_type_display', read_only=True)
    deadline = serializers.DateTimeField(source='expires_time', read_only=True)
    wisecrack = serializers.SerializerMethodField('gen_wisecrack', read_only=True)
    nick = serializers.CharField(source='user_nick_name', read_only=True)
    head_img = serializers.CharField(source='user_head_img', read_only=True)

    class Meta:
        model = UserCoupon
        fields = (
            'id', "template_id", 'coupon_type', "coupon_type_display", "title", 'customer', "coupon_no", "coupon_value",
            "valid", "deadline", "start_use_time", "status", "created",
            "use_fee", "use_fee_des", "pros_desc", "start_time", 'poll_status', 'wisecrack', 'nick', 'head_img'
        )

    def gen_wisecrack(self, obj):
        """ 生成tips """
        return u''


class OrderShareCouponSerialize(serializers.ModelSerializer):
    class Meta:
        model = OrderShareCoupon


class TmpShareCouponSerialize(serializers.ModelSerializer):
    class Meta:
        model = TmpShareCoupon


class TmpShareCouponMapSerialize(serializers.ModelSerializer):
    wisecrack = serializers.SerializerMethodField('gen_wisecrack', read_only=True)
    title = serializers.SerializerMethodField('gen_title', read_only=True)
    start_use_time = serializers.DateTimeField(source='created', read_only=True)
    expires_time = serializers.DateTimeField(source='modify', read_only=True)
    nick = serializers.SerializerMethodField('nick_name', read_only=True)
    thumbnail = serializers.SerializerMethodField('head_img', read_only=True)

    class Meta:
        model = TmpShareCoupon
        fields = (
            "id", "wisecrack", "title", 'nick', "value", 'thumbnail', "start_use_time", "expires_time"
        )

    def gen_wisecrack(self, obj):
        """ 生成tips """
        return u''

    def gen_title(self, obj):
        """ 生成tips """
        return u''

    def nick_name(self, obj):
        return ''.join([obj.mobile[0:3], "****", obj.mobile[7:12]]) if len(obj.mobile)==11 else ""

    def head_img(self, obj):
        return ''


class ShareUserCouponSerialize(serializers.ModelSerializer):
    wisecrack = serializers.SerializerMethodField('gen_wisecrack', read_only=True)
    nick = serializers.SerializerMethodField('nick_name', read_only=True)
    thumbnail = serializers.SerializerMethodField('head_img', read_only=True)

    class Meta:
        model = UserCoupon
        fields = (
            "id", "wisecrack", "title", 'nick', "value", 'thumbnail', "start_use_time", "expires_time"
        )

    def gen_wisecrack(self, obj):
        """ 生成tips """
        return u''

    def nick_name(self, obj):
        return obj.user_nick_name()

    def head_img(self, obj):
        return obj.user_head_img()