# coding:utf-8
import json
import datetime

from django.db.models import Count
from django.test import TestCase
from django.core.management import call_command

from flashsale.xiaolumm.models import (
    XiaoluMama, MamaMission,
    MamaMissionRecord,
    ReferalRelationship,
    GroupRelationship,
    AwardCarry,
    PotentialMama
)
from flashsale.pay.models import SaleTrade, SaleRefund, SaleOrder
from flashsale.xiaolumm.signals import signal_xiaolumama_register_success
from flashsale.xiaolumm.tasks import task_update_all_mama_mission_state
from flashsale.pay.signals import signal_saletrade_pay_confirm, signal_saletrade_refund_confirm

import logging
logger = logging.getLogger(__name__)

class MamaWeeklyAwardTestCase(TestCase):
    """ 登陆 / 加入购物车 / 获取支付信息 /付款 /查看付款订单 """
    fixtures = [
        'test.flashsale.customer.json',
        'test.flashsale.xiaolumm.json',
        'test.flashsale.pay.logistics.companys.json',
        'test.shopback.categorys.productcategory.json',
        'test.shopback.items.product.json',
        'test.flashsale.pay.saletrade.json',
        'test.flashsale.xiaolumm.weeklyaward.json'
    ]

    def setUp(self):
        self.mama_id = 44
        self.referal_from_mama_id = 1
        self.year_week = datetime.datetime.now().strftime('%Y-%W')
        MamaMissionRecord.objects.update(year_week=self.year_week)

        print ReferalRelationship.objects.all()

    def testUpdateAllMamaMissionState(self):
        MamaMissionRecord.objects.all().delete()
        task_update_all_mama_mission_state()

        missions = MamaMissionRecord.objects.filter(
            mama_id=self.mama_id,
            year_week=self.year_week,
            status=MamaMissionRecord.STAGING
        )
        missions_agg = dict(missions.annotate(record_count=Count('id')).values_list('mission__cat_type','record_count'))

        self.assertEqual(missions_agg[MamaMission.CAT_TRIAL_MAMA], 1)
        self.assertEqual(missions_agg[MamaMission.CAT_REFER_MAMA], 1)
        self.assertEqual(missions_agg[MamaMission.CAT_SALE_MAMA], 1)

        self.assertEqual(missions_agg[MamaMission.CAT_GROUP_MAMA], 1)
        self.assertEqual(missions_agg[MamaMission.CAT_SALE_GROUP], 1)


    def testFinishMamaMissionReferalAward(self):
        """ 测试妈妈邀请任务及　团队妈妈邀请 """
        now_datetime = datetime.datetime.now()
        referal_mama = XiaoluMama.objects.filter(id=self.mama_id).first()
        referal_mama.charge_time = now_datetime
        referal_mama.last_renew_type = XiaoluMama.TRIAL
        referal_mama.save()

        ReferalRelationship.objects.all().update(created=now_datetime)
        GroupRelationship.objects.all().update(created=now_datetime)
        PotentialMama.objects.all().update(created=now_datetime)

        signal_xiaolumama_register_success.send(sender=XiaoluMama, xiaolumama=referal_mama, renew=False)
        year_week = datetime.datetime.now().strftime('%Y-%W')
        mama_record = MamaMissionRecord.objects.filter(
            mama_id=self.referal_from_mama_id,
            year_week=year_week,
            mission__cat_type=MamaMission.CAT_TRIAL_MAMA)\
            .order_by('created').first()
        mama_award = AwardCarry.objects.filter(uni_key=mama_record.gen_uni_key()).first()
        self.assertEqual(mama_record.status, MamaMissionRecord.FINISHED)
        self.assertIsNone(mama_award)

        referal_mama.last_renew_type = XiaoluMama.FULL
        referal_mama.save()
        signal_xiaolumama_register_success.send(sender=XiaoluMama, xiaolumama=referal_mama, renew=False)
        mama_record = MamaMissionRecord.objects.filter(
            mama_id=self.referal_from_mama_id,
            year_week=year_week,
            mission__cat_type=MamaMission.CAT_REFER_MAMA)\
            .order_by('created').first()
        mama_award = AwardCarry.objects.filter(uni_key=mama_record.gen_uni_key()).first()
        self.assertEqual(mama_record.status, MamaMissionRecord.FINISHED)
        self.assertIsNone(mama_award)

        # TODO@meron　团队妈妈测试
        # self.assertGreaterEqual(mama_record.mission.award_amount, mama_award.carry_num) # >=

    def testFinishMamaMissionSaleAward(self):
        """ 测试妈妈销售激励　团队妈妈销售激励 """
        now_datetime = datetime.datetime.now()
        saletrade = SaleTrade.objects.filter(id=332233).first()
        saletrade.pay_time = now_datetime
        saletrade.save(update_fields=['pay_time'])
        sale_orders = SaleOrder.objects.filter(sale_trade=saletrade)
        for order in sale_orders:
            order.pay_time = now_datetime
            order.created = now_datetime
            order.save()
        signal_saletrade_pay_confirm.send(sender=SaleTrade, obj=saletrade)

        year_week = datetime.datetime.now().strftime('%Y-%W')
        mama_record = MamaMissionRecord.objects.filter(
            mama_id=self.mama_id,
            year_week=year_week,
            mission__cat_type=MamaMission.CAT_SALE_MAMA) \
            .order_by('created').first()
        mama_award = AwardCarry.objects.filter(uni_key=mama_record.gen_uni_key()).first()
        self.assertEqual(mama_record.status, MamaMissionRecord.FINISHED)
        self.assertIsNotNone(mama_award)
        self.assertEqual(mama_record.mission.award_amount, mama_award.carry_num) # ==

        mama_record = MamaMissionRecord.objects.filter(
            mama_id=self.mama_id,
            year_week=year_week,
            mission__cat_type=MamaMission.CAT_SALE_GROUP) \
            .order_by('created').first()
        mama_award = AwardCarry.objects.filter(uni_key=mama_record.gen_uni_key()).first()
        self.assertEqual(mama_record.status, MamaMissionRecord.FINISHED)
        self.assertIsNotNone(mama_award)
        self.assertGreaterEqual(mama_record.mission.award_amount, mama_award.carry_num) # >=

        # refund cancel award
        call_command('loaddata', 'test.flashsale.pay.salerefund.json', verbosity=1)

        salerefund = SaleRefund.objects.filter(trade_id=saletrade.id).first()
        signal_saletrade_refund_confirm.send(sender=SaleRefund, obj=salerefund)

        mama_record = MamaMissionRecord.objects.filter(
            mama_id=self.mama_id,
            year_week=year_week,
            mission__cat_type=MamaMission.CAT_SALE_MAMA) \
            .order_by('created').first()
        mama_award = AwardCarry.objects.filter(uni_key=mama_record.gen_uni_key()).first()
        self.assertEqual(mama_record.status, MamaMissionRecord.STAGING)
        self.assertEqual(mama_award.status, AwardCarry.CANCEL)

        mama_record = MamaMissionRecord.objects.filter(
            mama_id=self.mama_id,
            year_week=year_week,
            mission__cat_type=MamaMission.CAT_SALE_GROUP)\
            .order_by('created').first()
        mama_award = AwardCarry.objects.filter(uni_key=mama_record.gen_uni_key()).first()
        self.assertEqual(mama_record.status, MamaMissionRecord.STAGING)
        self.assertEqual(mama_award.status, AwardCarry.CANCEL)




