# coding=utf-8
from __future__ import unicode_literals, absolute_import
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import filters
from django.db.models import Sum

from flashsale.pay.models import ModelProduct
from shopback.items.models import Product
from flashsale.pay.apis.v1.customer import get_customer_by_django_user
from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_openid
from flashsale.coupon import serializers
from flashsale.coupon.models import UserCoupon, CouponTransferRecord
from flashsale.coupon.apis.v1.transfer import apply_pending_return_transfer_coupon
import logging

logger = logging.getLogger(__name__)


def get_coupons_elite(user_coupons, mama_level):
    # type: (List[UserCoupon], text_type) -> int
    """计算优惠券 在当前等级的 积分
    """
    virtual_model_products = ModelProduct.objects.get_virtual_modelproducts()  # 虚拟商品
    map_dict = {}
    for md in virtual_model_products:
        md_bind_tpl_id = md.extras.get('template_id')
        if not md_bind_tpl_id:
            continue
        map_dict[md_bind_tpl_id] = md.id
    model_ids = []
    for coupon in user_coupons:
        model_ids.append(map_dict[coupon.template_id])
    products = Product.objects.filter(model_id__in=model_ids).values('model_id', 'name', 'elite_score')
    total_elite_score = 0
    for c in user_coupons:
        model_id = map_dict[c.template_id]
        for p in products:
            if mama_level in p['name'] and p['model_id'] == model_id:  # 款式相同　并且名字含有　对应等级的产品
                total_elite_score += p['elite_score']  # 累加积分
    return total_elite_score


class UserCouponsFilter(filters.FilterSet):
    class Meta:
        model = UserCoupon
        fields = ['status', 'template_id', 'coupon_type']


class UserCouponsViewSet(viewsets.ModelViewSet):
    queryset = UserCoupon.objects.all()
    serializer_class = serializers.UserCouponSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = UserCouponsFilter

    def list(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        customer = get_customer_by_django_user(user=request.user)
        queryset = self.filter_queryset(self.get_queryset().filter(customer_id=customer.id))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.UserCouponListSerialize(queryset, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.UserCouponListSerialize(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        return Response({'code': 1, 'info': 'method not allow'})

    def destroy(self, request, *args, **kwargs):
        return Response({'code': 1, 'info': 'method not allow'})

    @list_route(methods=['get'])
    def get_unused_boutique_coupons(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """获取　未使用状态的　精品类型　优惠券
        """
        from shopback.monitor.models import XiaoluSwitch

        customer = get_customer_by_django_user(user=request.user)
        data = []
        ubcs = UserCoupon.objects.get_unused_boutique_coupons().filter(customer_id=customer.id)
        item = {}
        for coupon in ubcs:
            template_id = coupon.template_id
            if template_id not in item:
                product_img = coupon.self_template().extras.get('product_img')
                item[template_id] = {
                    'product_img': product_img,
                    'coupon_num': 1,
                    'coupon_ids': [],
                    'gift_transfer_coupon_ids': [],
                    'from_sys_coupon_ids': [],
                    'from_mama_coupon_ids': [],
                }
            else:
                item[template_id]['coupon_num'] += 1
            item[template_id]['coupon_ids'].append(coupon.id)
            transfer_coupon_pk = coupon.extras.get('transfer_coupon_pk')
            if transfer_coupon_pk:
                item[template_id]['from_mama_coupon_ids'].append(coupon.id)
            elif coupon.is_gift_transfer_coupon:  # 如果是系统赠送的流通优惠券
                item[template_id]['gift_transfer_coupon_ids'].append(coupon.id)
            else:
                item[template_id]['from_sys_coupon_ids'].append(coupon.id)
        switch = XiaoluSwitch.objects.filter(title='退优惠券给上级').first()
        can_return_upper = switch.status if switch else 0
        for k, v in item.iteritems():
            data.append({
                'template_id': k,
                'can_return_upper': can_return_upper,
                'product_img': v['product_img'],
                'coupon_ids': v['coupon_ids'],
                'coupon_num': v['coupon_num'],
                'from_mama_coupon_ids': v['from_mama_coupon_ids'],
                'gift_transfer_coupon_ids': v['gift_transfer_coupon_ids'],
                'from_sys_coupon_ids': v['from_sys_coupon_ids']
            })
        return Response(data)

    @list_route(methods=['POST'])
    def apply_return_boutique_coupons(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """提交退还　精品券　优惠券　给上级妈妈　的申请
        """
        customer = get_customer_by_django_user(request.user)
        coupon_ids = request.POST.get('coupon_ids')
        if not isinstance(coupon_ids, list):
            coupon_ids = coupon_ids.split(',')
            coupon_ids = [str(i).strip() for i in coupon_ids if i.strip().isdigit()]
        if not coupon_ids:
            return Response({'code': 1, 'info': '参数错误'})
        user_coupons = UserCoupon.objects.get_unused_boutique_coupons().filter(customer_id=customer.id,
                                                                               id__in=coupon_ids)
        coupon_ids = [c['id'] for c in user_coupons.values('id')]
        if not coupon_ids:
            return Response({'code': 3, 'info': '没有找到优惠券'})
        if not customer.unionid:
            return Response({'code': 4, 'info': '用户错误'})
        # 判断积分是否可以退券操作
        mama = get_mama_by_openid(customer.unionid)
        can_return_elite = mama.elite_score - mama.get_level_lowest_elite()  # 当前可退回的积分数
        p_records = CouponTransferRecord.objects.get_return_transfer_coupons().filter(coupon_from_mama_id=mama.id,
                                                                                      transfer_status=CouponTransferRecord.PENDING)
        p_elite_score = p_records.aggregate(s_elite_score=Sum('elite_score')).get('s_elite_score') or 0
        can_return_elite = can_return_elite - p_elite_score  # 这里的可以退还的积分要减去　待审核的积分数量
        coupon_elite = get_coupons_elite(user_coupons, mama.elite_level)  # 计算优惠券在当前等级的积分
        if coupon_elite > can_return_elite:
            return Response({'code': 5, 'info': '您的退券张数太多，会导致您降级，请减少退券数量'})
        state = apply_pending_return_transfer_coupon(coupon_ids)
        if not state:
            return Response({'code': 2, 'info': '申请失败'})
        return Response({'code': 0, 'info': '申请成功'})