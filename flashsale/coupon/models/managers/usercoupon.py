# coding=utf-8
from __future__ import absolute_import, unicode_literals
import logging
from core.managers import BaseManager

logger = logging.getLogger(__name__)


class UserCouponManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def get_coupons(self, ids):
        # type: (List[int]) -> Optional[List[UserCoupon]]
        return self.get_queryset().filter(id__in=ids)

    def get_template_coupons(self, coupon_template_id):
        # type: (int) -> Optional[List[UserCoupon]]
        """指定模板的优惠券
        """
        return self.get_queryset().filter(template_id=coupon_template_id).exclude(status=self.model.CANCEL)

    def get_unused_coupons(self):
        # type: () -> Optional[List[UserCoupon]]
        """获取没有使用的用户优惠券
        """
        return self.get_queryset().filter(status=self.model.UNUSED)

    def get_freeze_coupons(self):
        # type: () -> Optional[List[UserCoupon]]
        """获取冻结的用户优惠券
        """
        return self.get_queryset().filter(status=self.model.FREEZE)

    def get_order_share_coupons(self, order_coupon_id):
        # type: (int) -> Optional[List[UserCoupon]]
        return self.get_queryset().filter(order_coupon_id=order_coupon_id)

    def get_unused_boutique_coupons(self):
        # type: () -> Optional[List[UserCoupon]]
        """获取　没有使用状态的　精品券
        """
        return self.get_unused_coupons().filter(coupon_type=self.model.TYPE_TRANSFER)

    def get_freeze_boutique_coupons(self):
        # type: () -> Optional[List[UserCoupon]]
        """获取　冻结状态的　精品券
        """
        return self.get_freeze_coupons().filter(coupon_type=self.model.TYPE_TRANSFER)

    def get_origin_payment_boutique_coupons(self):
        return self.get_queryset().filter(coupon_type=self.model.TYPE_TRANSFER, is_buyed=True)