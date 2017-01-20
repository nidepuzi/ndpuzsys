# coding=utf-8
from __future__ import absolute_import, unicode_literals
import logging
from core.managers import BaseManager

logger = logging.getLogger(__name__)


class CouponTransferRecordManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def get_effect_transfer_coupons(self):
        # type:() -> Optional[List[CouponTransferRecord]]
        """获取有效的　流通记录
        """
        return self.get_queryset().filter(status=self.model.EFFECT)

    def get_return_transfer_coupons(self):
        # type: () -> Optional[List[CouponTransferRecord]]
        """　获取　退回类型　的有效的　流通记录
        """
        return self.get_effect_transfer_coupons().filter(transfer_type=self.model.IN_RETURN_COUPON)

    def get_out_cash_transfer_coupons(self):
        # type: () -> Optional[List[CouponTransferRecord]]
        """　获取　退回系统类型　的有效的　流通记录
        """
        return self.get_effect_transfer_coupons().filter(transfer_type=self.model.OUT_CASHOUT)

    def get_out_cash_coin_transfer_coupons(self):
        # type: () -> Optional[List[CouponTransferRecord]]
        """　获取　退回系统coin类型　的有效的　流通记录
        """
        return self.get_effect_transfer_coupons().filter(transfer_type=self.model.OUT_CASHOUT_COIN)

    def get_all_return_sys_transfer_coupons(self):
        # type: () -> Optional[List[CouponTransferRecord]]
        """　获取　退回系统coin类型　的有效的　流通记录
        """
        return self.get_effect_transfer_coupons().filter(transfer_type__in=[self.model.OUT_CASHOUT_COIN, self.model.OUT_CASHOUT])
