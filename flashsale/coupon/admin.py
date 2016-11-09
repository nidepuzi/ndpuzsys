# coding=utf-8
from django.contrib import admin

from core.filters import DateFieldListFilter
from flashsale.coupon.models import CouponTemplate, OrderShareCoupon, UserCoupon, TmpShareCoupon, CouponTransferRecord


class CouponTemplateAdmin(admin.ModelAdmin):
    fieldsets = (
        (u'标题信息:', {
            'classes': ('expand',),
            'fields': (('title', 'description', 'status'), )
        }),
        (u'数值信息:', {
            'classes': ('expand',),
            'fields': (('value', 'is_random_val', 'has_released_count', 'prepare_release_num'),)
        }),
        (u'时间信息:', {
            'classes': ('expand',),
            'fields': (('release_start_time', 'release_end_time', 'use_deadline'), )
        }),
        (u'其他信息:', {
            'classes': ('expand',),
            'fields': (('coupon_type', 'target_user', 'scope_type', 'is_flextime'),
                       'extras')
        }),
    )

    list_display = (
        'id', 'title', 'value', 'is_random_val', 'coupon_type', 'scope_type', 'has_released_count', 'has_used_count',
        'status', 'release_start_time', 'release_end_time', 'use_deadline')

    list_filter = ('coupon_type', 'scope_type', )
    search_fields = ['=id', ]
    date_hierarchy = 'created'


admin.site.register(CouponTemplate, CouponTemplateAdmin)


class OrderShareCouponAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'template_id', 'share_customer', 'share_start_time',
        'share_end_time', 'release_count', "has_used_count",
        'status')

    list_filter = ('share_end_time', 'share_start_time')
    search_fields = ['=id', '=share_customer', '=template_id']
    date_hierarchy = 'created'


admin.site.register(OrderShareCoupon, OrderShareCouponAdmin)


class UserCouponAdmin(admin.ModelAdmin):
    fieldsets = (
        (u'标题信息:', {
            'classes': ('expand',),
            'fields': (('template_id', 'title', 'customer_id', 'value', 'status'), )
        }),

        (u'时间信息:', {
            'classes': ('expand',),
            'fields': (('finished_time', 'start_use_time', 'expires_time'), )
        }),

        (u'其他信息:', {
            'classes': ('expand',),
            'fields': (('coupon_no', 'trade_tid', 'uniq_id'),
                       ('coupon_type', 'ufrom', 'is_pushed'),
                       ('extras', ))
        }),
    )

    list_display = ('id', 'title', "customer_id", 'status', "uniq_id", 'finished_time', 'expires_time', 'is_pushed', 'modified', 'created')

    list_filter = ('coupon_type', 'status', 'expires_time', 'finished_time', ('created', DateFieldListFilter))
    search_fields = ['=id', '=template_id', '=customer_id']


admin.site.register(UserCoupon, UserCouponAdmin)


class TmpShareCouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'mobile', 'share_coupon_id', 'value', 'status')

    list_filter = ('created', )
    search_fields = ['=id', '=mobile', '=share_coupon_id']
    date_hierarchy = 'created'


admin.site.register(TmpShareCoupon, TmpShareCouponAdmin)


class CouponTransferRecordAdmin(admin.ModelAdmin):
    list_display = ('coupon_from_mama_id', 'from_mama_nick', 'coupon_to_mama_id', 'to_mama_nick', 'template_id', 'template_name',
                    'coupon_value', 'coupon_num', 'transfer_type', 'transfer_status', 'status', 'uni_key', 'date_field',
                    'init_from_mama_id','order_no', 'modified', 'created')
    list_filter = ('transfer_type', 'transfer_status', 'status', ('created', DateFieldListFilter))
    search_fields = ['=coupon_from_mama_id', '=coupon_to_mama_id']

    def template_name(self, obj):
        ct = CouponTemplate.objects.filter(id=obj.template_id).first()
        if ct:
            return ct.title
        return ''

admin.site.register(CouponTransferRecord, CouponTransferRecordAdmin)