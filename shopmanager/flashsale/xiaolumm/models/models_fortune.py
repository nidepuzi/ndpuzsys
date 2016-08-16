# coding=utf-8
from django.db import models
from django.db.models import Sum, F
from core.models import BaseModel
from django.db.models.signals import post_save
from django.conf import settings
import datetime, urlparse
from core.fields import JSONCharMyField
import logging

logger = logging.getLogger('django.request')


def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name


#
# Use from flashsale.xiaolumm.models import CashOut
#
# class CashOut(BaseModel):
#    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)
#    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
#    amount = models.IntegerField(default=0, verbose_name=u'数额')
#    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
#
#    class Meta:
#        db_table = 'flashsale_xlmm_cashout'
#        verbose_name = u'妈妈提现'
#        verbose_name_plural = u'妈妈提现列表'
#
#    def is_confirmed(self):
#        return self.status == 2
#
#    def amount_display(self):
#        return float('%.2f' % (self.amount * 0.01))


# The time to switch to xiaolumama v2.0
MAMA_FORTUNE_HISTORY_LAST_DAY = datetime.date(2016, 03, 24)


def default_mama_extras():
    """ other mama information """
    return {
        "qrcode_url":
            {
                "home_page_qrcode_url": "",
                "app_download_qrcode_url": ""
            }
    }


class MamaFortune(BaseModel):
    MAMA_LEVELS = ((0, u'新手妈妈'), (1, u'金牌妈妈'), (2, u'钻石妈妈'), (3, u'皇冠妈妈'), (4, u'金冠妈妈'))
    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
    mama_name = models.CharField(max_length=32, blank=True, verbose_name=u'名称')
    mama_level = models.IntegerField(default=0, choices=MAMA_LEVELS, verbose_name=u'级别')

    fans_num = models.IntegerField(default=0, verbose_name=u'粉丝数')
    invite_num = models.IntegerField(default=0, verbose_name=u'邀请数')
    invite_trial_num = models.IntegerField(default=0, verbose_name=u'试用妈妈邀请数')
    invite_all_num = models.IntegerField(default=0, verbose_name=u'总邀请数')
    active_normal_num = models.IntegerField(default=0, verbose_name=u'普通妈妈激活数')
    active_trial_num = models.IntegerField(default=0, verbose_name=u'试用妈妈激活数')
    active_all_num = models.IntegerField(default=0, verbose_name=u'总激活数')
    hasale_normal_num = models.IntegerField(default=0, verbose_name=u'出货普通妈妈数')
    hasale_trial_num = models.IntegerField(default=0, verbose_name=u'出货试用妈妈数')
    hasale_all_num = models.IntegerField(default=0, verbose_name=u'出货妈妈总数')

    order_num = models.IntegerField(default=0, verbose_name=u'订单数')

    carry_pending = models.IntegerField(default=0, verbose_name=u'待确定收益')
    carry_confirmed = models.IntegerField(default=0, verbose_name=u'已确定收益')
    carry_cashout = models.IntegerField(default=0, verbose_name=u'已提现金额')

    history_pending = models.IntegerField(default=0, verbose_name=u'历史待确定收益')
    history_confirmed = models.IntegerField(default=0, verbose_name=u'历史已确定收益')
    history_cashout = models.IntegerField(default=0, verbose_name=u'历史已提现收益')
    history_last_day = models.DateField(default=MAMA_FORTUNE_HISTORY_LAST_DAY, verbose_name=u'历史结束日期')

    active_value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')
    extras = JSONCharMyField(max_length=1024, default=default_mama_extras, blank=True,
                             null=True, verbose_name=u"附加信息")

    class Meta:
        db_table = 'flashsale_xlmm_fortune'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈财富表'
        verbose_name_plural = u'V2/妈妈财富列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.mama_name)

    @staticmethod
    def get_by_mamaid(mama_id):
        fortune = MamaFortune.objects.filter(mama_id=mama_id).first()
        if fortune:
            return fortune
        fortune = MamaFortune(mama_id=mama_id)
        fortune.save()
        return fortune

    def mama_level_display(self):
        return get_choice_name(self.MAMA_LEVELS, self.mama_level)

    @property
    def cash_total(self):
        return self.carry_pending + self.carry_confirmed + self.history_pending + self.history_confirmed + self.history_cashout

    def cash_total_display(self):
        return float('%.2f' % (self.cash_total * 0.01))

    cash_total_display.short_description = u"总收益"
    cash_total_display.admin_order_field = 'cash_total'

    def carry_num_display(self):
        """ 累计收益数 """
        total = self.carry_pending + self.carry_confirmed + self.history_pending + self.history_confirmed
        return float('%.2f' % (total * 0.01))

    carry_num_display.short_description = u"累计收益"
    carry_num_display.admin_order_field = 'carry_num'

    def cash_num_display(self):
        """ 余额 """
        total = self.carry_confirmed + self.history_confirmed - self.carry_cashout
        return float('%.2f' % (total * 0.01))

    cash_num_display.short_description = u"账户金额"
    cash_num_display.admin_order_field = 'cash_num'

    def carry_pending_display(self):
        total = self.carry_pending + self.history_pending
        return float('%.2f' % (total * 0.01))

    carry_pending_display.short_description = u"待确认收益"

    def carry_confirmed_display(self):
        total = self.carry_confirmed + self.history_confirmed
        return float('%.2f' % (total * 0.01))

    carry_confirmed_display.short_description = u"已确定收益"

    def carry_cashout_display(self):
        return float('%.2f' % (self.carry_cashout * 0.01))

    carry_cashout_display.short_description = u"已提现金额"

    def mama_event_link(self):
        """ 活动页面链接 """
        activity_link = 'pages/featuredEvent.html'

        return settings.M_SITE_URL + settings.M_STATIC_URL + activity_link

    @property
    def home_page_qrcode_url(self):
        return self.extras['qrcode_url']['home_page_qrcode_url']

    @property
    def app_download_qrcode_url(self):
        return self.extras['qrcode_url']['app_download_qrcode_url']

    def get_history_cash_out(self):
        from flashsale.xiaolumm.models import CashOut
        history_last_day= self.history_last_day or MAMA_FORTUNE_HISTORY_LAST_DAY
        return CashOut.objects.filter(xlmm=self.mama_id, status=CashOut.APPROVED, approve_time__lt=history_last_day
                                      ).aggregate(total=Sum('value')).get('total') or 0

    def update_extras_qrcode_url(self, **kwargs):
        """ 更新附加里面的二维码链接信息 """
        extras = self.extras
        change_flag = False
        for k, v in kwargs.items():
            qrcode_url = extras['qrcode_url']
            if qrcode_url.has_key(k) and qrcode_url.get(k) != v:  # 如果当前的和传过来的参数不等则更新
                qrcode_url.update({k: v})
                change_flag = True
        if change_flag:
            self.extras = extras
            self.save()

    @property
    def xlmm(self):
        if not hasattr(self, '_xiaolumm_xlmm_'):
            from flashsale.xiaolumm.models.models import XiaoluMama
            self._xiaolumm_xlmm_ = XiaoluMama.objects.filter(id=self.mama_id).first()
        return self._xiaolumm_xlmm_


def send_activate_award(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    if instance.invite_trial_num >= 2:
        tasks_mama_fortune.task_send_activate_award.delay(instance.mama_id)

post_save.connect(send_activate_award,
                  sender=MamaFortune, dispatch_uid='post_save_send_activate_award')


def update_week_carry_total(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carry_total
    if not instance.xlmm.is_staff and instance.xlmm.is_available():
        tasks_mama_carry_total.task_fortune_update_week_carry_total.delay(instance.mama_id)

post_save.connect(update_week_carry_total,
                  sender=MamaFortune, dispatch_uid='post_save_task_fortune_update_week_carry_total')


class DailyStats(BaseModel):
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'),)
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')
    today_order_num = models.IntegerField(default=0, verbose_name=u'今日订单数')
    today_carry_num = models.IntegerField(default=0, verbose_name=u'今日收益数')
    today_active_value = models.IntegerField(default=0, verbose_name=u'今日活跃值')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=1, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定

    class Meta:
        db_table = 'flashsale_xlmm_daily_stats'
        app_label = 'xiaolumm'
        verbose_name = u'V2/每日数据'
        verbose_name_plural = u'V2/每日数据列表'

    def today_carry_num_display(self):
        return float('%.2f' % (self.today_carry_num * 0.01))


def confirm_previous_dailystats(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_dailystats
    if created:
        mama_id = instance.mama_id
        date_field = instance.date_field
        tasks_mama_dailystats.task_confirm_previous_dailystats.delay(mama_id, date_field, 2)


post_save.connect(confirm_previous_dailystats,
                  sender=DailyStats, dispatch_uid='post_save_confirm_previous_dailystats')


class CarryRecord(BaseModel):
    PENDING = 1
    CONFIRMED = 2
    CANCEL = 3

    STATUS_TYPES = ((PENDING, u'预计收益'),
                    (CONFIRMED, u'确定收益'),
                    (CANCEL, u'已取消'),)

    CR_CLICK = 1
    CR_ORDER = 2
    CR_RECOMMEND = 3
    CARRY_TYPES = ((CR_CLICK, u'返现'),
                   (CR_ORDER, u'佣金'),
                   (CR_RECOMMEND, u'奖金'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'收益数')
    carry_type = models.IntegerField(default=0, choices=CARRY_TYPES, verbose_name=u'收益类型')  # 返/佣/奖
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_carry_record'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈收入记录'
        verbose_name_plural = u'V2/妈妈收入记录列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num)

    @property
    def mama(self):
        from flashsale.xiaolumm.models import XiaoluMama
        return XiaoluMama.objects.get(id=self.mama_id)

    def carry_type_name(self):
        return get_choice_name(self.CARRY_TYPES, self.carry_type)

    def carry_num_display(self):
        return float('%.2f' % (self.carry_num * 0.01))

    carry_num_display.short_description = u"收益金额"

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def is_carry_confirmed(self):
        return self.status == 2

    def is_carry_pending(self):
        return self.status == 1

    def is_carry_canceled(self):
        return self.status == 0

    def is_award_carry(self):
        return self.carry_type == 3

    def is_order_carry(self):
        return self.carry_type == 2

    def is_click_carry(self):
        return self.carry_type == 1


def carryrecord_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_carryrecord_update_mamafortune.delay(instance.mama_id)

    from flashsale.xiaolumm import tasks_mama_dailystats
    tasks_mama_dailystats.task_carryrecord_update_dailystats.delay(instance.mama_id, instance.date_field)


post_save.connect(carryrecord_update_mamafortune,
                  sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_mamafortune')


def carryrecord_update_xiaolumama_active_hasale(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama
    if not instance.mama.active:
        tasks_mama.carryrecord_update_xiaolumama_active_hasale.delay(instance.mama_id)


post_save.connect(carryrecord_update_xiaolumama_active_hasale,
                  sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_xiaolumama_active_hasale')


def carryrecord_update_carrytotal(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks_mama_carry_total import task_carryrecord_update_carrytotal
    task_carryrecord_update_carrytotal.delay(instance.mama_id)


post_save.connect(carryrecord_update_carrytotal,
                  sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_carrytotal')


class OrderCarry(BaseModel):
    CARRY_TYPES = ((1, u'微商城订单'), (2, u'App订单额外+10%'), (3, u'下属订单+20%'),)
    STATUS_TYPES = ((0, u'待付款'), (1, u'预计收益'), (2, u'确定收益'), (3, u'买家取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    order_id = models.CharField(max_length=64, blank=True, verbose_name=u'订单ID')
    order_value = models.IntegerField(default=0, verbose_name=u'订单金额')
    carry_num = models.IntegerField(default=0, verbose_name=u'提成金额')
    carry_type = models.IntegerField(default=1, choices=CARRY_TYPES, verbose_name=u'提成类型')  # 直接订单提成/粉丝订单提成/下属订单提成
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'sku名称')
    sku_img = models.CharField(max_length=256, blank=True, verbose_name=u'sku图片')
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')
    contributor_id = models.BigIntegerField(default=0, verbose_name=u'贡献者ID')
    carry_plan_name = models.CharField(max_length=32, blank=True, verbose_name=u'佣金计划')
    agency_level = models.IntegerField(default=0, verbose_name=u'佣金级别')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  #
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_order_carry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/订单提成'
        verbose_name_plural = u'V2/订单提成列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num, self.date_field)

    def carry_type_name(self):
        # web order, we currently dont show name
        if self.carry_type == 1:
            return ''
        return get_choice_name(self.CARRY_TYPES, self.carry_type)

    def order_value_display(self):
        return '%.2f' % (self.order_value * 0.01)

    def carry_num_display(self):
        return float('%.2f' % (self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def contributor_nick_display(self):
        if self.contributor_nick == "":
            return u"匿名用户"
        return self.contributor_nick

    def is_pending(self):
        return self.status == 1

    def is_confirmed(self):
        return self.status == 2

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    #def get_mama_customer(self):
    #    from flashsale.xiaolumm.models.models import XiaoluMama
    #    mama = XiaoluMama.objects.filter(id=self.mama_id).first()
    #    return mama.get_mama_customer()

    @property
    def mama(self):
        from flashsale.xiaolumm.models.models import XiaoluMama
        return XiaoluMama.objects.get(id=self.mama_id)

    def is_direct_or_fans_carry(self):
        return self.carry_type == 1 or self.carry_type == 2


def ordercarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carryrecord
    tasks_mama_carryrecord.task_ordercarry_update_carryrecord.delay(instance)


post_save.connect(ordercarry_update_carryrecord,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_carryrecord')


def ordercarry_weixin_push(sender, instance, created, **kwargs):
    """
    订单提成推送到微信
    """
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama_push
    tasks_mama_push.task_weixin_push_ordercarry.delay(instance)

post_save.connect(ordercarry_weixin_push,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_weixin_push')


def ordercarry_app_push(sender, instance, created, **kwargs):
    """
    """
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama_push
    tasks_mama_push.task_app_push_ordercarry.delay(instance)

post_save.connect(ordercarry_app_push,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_app_push')


# 首单奖励
def ordercarry_send_first_award(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    from flashsale.xiaolumm.models.models import XiaoluMama
    if instance.mama.last_renew_type == XiaoluMama.TRIAL:
        tasks_mama_fortune.task_first_order_send_award.delay(instance.mama)
    tasks_mama_fortune.task_update_mamafortune_hasale_num.delay(instance.mama_id)

post_save.connect(ordercarry_send_first_award,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_send_first_alwad')


def ordercarry_update_ordercarry(sender, instance, created, **kwargs):
    if instance.is_direct_or_fans_carry():
        # find out parent mama_id, and this relationship must be established before the order creation date.
        referal_relationships = ReferalRelationship.objects.filter(referal_to_mama_id=instance.mama_id,
                                                                   created__lt=instance.created)
        from flashsale.xiaolumm import tasks_mama
        if referal_relationships.count() > 0:
            referal_relationship = referal_relationships[0]
            tasks_mama.task_update_second_level_ordercarry.delay(referal_relationship, instance)
        else:
            # 看潜在关系列表
            from flashsale.xiaolumm.models import PotentialMama
            try:
                potential = PotentialMama.objects.filter(potential_mama=instance.mama_id,
                                                         is_full_member=False).latest('created')
            except PotentialMama.DoesNotExist:
                return
            tasks_mama.task_update_second_level_ordercarry_by_trial.delay(potential, instance)


post_save.connect(ordercarry_update_ordercarry,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_ordercarry')


def ordercarry_update_activevalue(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_activevalue
    tasks_mama_activevalue.task_ordercarry_update_activevalue.delay(instance.uni_key)


post_save.connect(ordercarry_update_activevalue,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_activevalue')


def ordercarry_update_order_number(sender, instance, created, **kwargs):
    mama_id = instance.mama_id
    date_field = instance.date_field

    from flashsale.xiaolumm import tasks_mama_clickcarry
    tasks_mama_clickcarry.task_update_clickcarry_order_number.delay(mama_id, date_field)

    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_update_mamafortune_order_num.delay(mama_id)

    if created:
        from flashsale.xiaolumm import tasks_mama_dailystats
        tasks_mama_dailystats.task_ordercarry_increment_dailystats.delay(mama_id, date_field)


post_save.connect(ordercarry_update_order_number,
                  sender=OrderCarry, dispatch_uid='post_save_order_carry_update_order_number')


class AwardCarry(BaseModel):
    AWARD_TYPES = ((1, u'直荐奖励'),(2, u'团队奖励'),(3, u'授课奖金'),(4, u'新手任务'),(5, u'首单奖励'),(6, u'推荐新手任务'),(7, u'一元邀请'))
    STATUS_TYPES = ((1, u'预计收益'), (2, u'确定收益'), (3, u'已取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'奖励金额')
    carry_type = models.IntegerField(default=0, choices=AWARD_TYPES, verbose_name=u'奖励类型')  # 直接推荐奖励/团队成员奖励
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    contributor_nick = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'贡献者昵称')
    contributor_img = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'贡献者头像')
    contributor_mama_id = models.BigIntegerField(default=0, null=True, verbose_name=u'贡献者mama_id')
    carry_plan_name = models.CharField(max_length=32, blank=True, verbose_name=u'佣金计划')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_award_carry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈邀请奖励'
        verbose_name_plural = u'V2/妈妈邀请奖励列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num, self.date_field)

    def is_pending(self):
        return self.status == 1

    def is_confirmed(self):
        return self.status == 2

    def carry_type_name(self):
        return get_choice_name(self.AWARD_TYPES, self.carry_type)

    def carry_num_display(self):
        return float('%.2f' % (self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    @staticmethod
    def send_award(mama, num, name, description, uni_key, status, carry_type,
                   contributor_nick=None, contributor_img=None, contributor_mama_id=None):
        repeat_one = AwardCarry.objects.filter(uni_key=uni_key).first()
        if repeat_one:
            return repeat_one
        ac = AwardCarry(
            mama_id=mama.id,
            carry_num=num * 100,
            carry_type=carry_type,
            date_field=datetime.datetime.now().date(),
            carry_plan_name=name,
            carry_description=description,
            uni_key=uni_key,
            status=status,
            contributor_nick=contributor_nick if contributor_nick else mama.get_mama_customer().nick,
            contributor_img=contributor_img if contributor_img else mama.get_mama_customer().thumbnail,
            contributor_mama_id=contributor_mama_id if contributor_mama_id else mama.id
        )
        ac.save()
        return ac


def awardcarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carryrecord
    tasks_mama_carryrecord.task_awardcarry_update_carryrecord.delay(instance)


post_save.connect(awardcarry_update_carryrecord,
                  sender=AwardCarry, dispatch_uid='post_save_awardcarry_update_carryrecord')


def awardcarry_weixin_push(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama_push
    tasks_mama_push.task_weixin_push_awardcarry.delay(instance)

post_save.connect(awardcarry_weixin_push,
                  sender=AwardCarry, dispatch_uid='post_save_awardcarry_weixin_push')


class ClickPlan(BaseModel):
    STATUS_TYPES = ((0, u'使用'), (1, u'取消'),)
    name = models.CharField(max_length=32, verbose_name=u'名字')

    # {"0":[10, 10], "1":[20, 60], "2":[30, 110], "3":[40, 160], "4":[50, 210], "5":[60, 260]}
    order_rules = JSONCharMyField(max_length=256, blank=True, default={}, verbose_name=u'规则')
    max_order_num = models.IntegerField(default=0, verbose_name=u'最大订单人数')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'生效时间')
    end_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'结束时间')

    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
    default = models.BooleanField(default=False, verbose_name=u'缺省设置')

    class Meta:
        db_table = 'flashsale_xlmm_click_plan'
        app_label = 'xiaolumm'
        ordering = ['-created']
        verbose_name = u'V2/点击计划'
        verbose_name_plural = u'V2/点击计划列表'

    @classmethod
    def get_active_clickplan(cls):
        time_now = datetime.datetime.now()
        plan = cls.objects.filter(status=0, end_time__gte=time_now,
                                  start_time__lte=time_now).order_by('-created').first()
        if plan:
            return plan
        default = cls.objects.filter(status=0, default=True).first()
        return default


class ClickCarry(BaseModel):
    STATUS_TYPES = ((1, u'预计收益'), (2, u'确定收益'), (3, u'已取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    click_num = models.IntegerField(default=0, verbose_name=u'初始点击数')
    init_order_num = models.IntegerField(default=0, verbose_name=u'初始订单人数')
    init_click_price = models.IntegerField(default=0, verbose_name=u'初始点击价')
    init_click_limit = models.IntegerField(default=0, verbose_name=u'初始点击上限')
    confirmed_order_num = models.IntegerField(default=0, verbose_name=u'确定订单人数')
    confirmed_click_price = models.IntegerField(default=0, verbose_name=u'确定点击价')
    confirmed_click_limit = models.IntegerField(default=0, verbose_name=u'确定点击上限')
    carry_plan_name = models.CharField(max_length=32, blank=True, verbose_name=u'佣金计划')
    carry_plan_id = models.IntegerField(default=1, verbose_name=u'佣金计划ID')
    total_value = models.IntegerField(default=0, verbose_name=u'点击总价')
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # date+mama_id
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_click_carry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈点击返现'
        verbose_name_plural = u'V2/妈妈点击返现列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.total_value)

    def is_confirmed(self):
        return self.status == 2

    def init_click_price_display(self):
        return '%.2f' % (self.init_click_price * 0.01)

    def confirmed_click_price_display(self):
        return '%.2f' % (self.confirmed_click_price * 0.01)

    def total_value_display(self):
        return '%.2f' % (self.total_value * 0.01)

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None


def clickcarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carryrecord
    tasks_mama_carryrecord.task_clickcarry_update_carryrecord.delay(instance)


post_save.connect(clickcarry_update_carryrecord,
                  sender=ClickCarry, dispatch_uid='post_save_clickcarry_update_carryrecord')


def confirm_previous_clickcarry(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_clickcarry
    if created:
        mama_id = instance.mama_id
        date_field = instance.date_field
        tasks_mama_clickcarry.task_confirm_previous_zero_order_clickcarry.delay(mama_id, date_field, 2)
        tasks_mama_clickcarry.task_confirm_previous_order_clickcarry.delay(mama_id, date_field, 7)


post_save.connect(confirm_previous_clickcarry,
                  sender=ClickCarry, dispatch_uid='post_save_confirm_previous_clickcarry')


def gauge_active_mama(sender, instance, created, **kwargs):
    from django_statsd.clients import statsd
    if created:
        date_field = datetime.datetime.now().date()
        active_mama_count = ClickCarry.objects.filter(date_field=date_field).count()
        key = "clickcarry.active_mama"
        statsd.timing(key, active_mama_count)


post_save.connect(gauge_active_mama, sender=ClickCarry, dispatch_uid='post_save_gauge_active_mama')


class ActiveValue(BaseModel):
    VALUE_MAP = {"1": 1, "2": 10, "3": 50, "4": 5}
    VALUE_TYPES = ((1, u'点击'), (2, u'订单'), (3, u'推荐'), (4, u'粉丝'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'已取消'), (4, u'已过期'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    value_type = models.IntegerField(default=0, choices=VALUE_TYPES, verbose_name=u'类型')  # 点击/订单/推荐/粉丝
    value_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  #
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_active_value_record'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈活跃值'
        verbose_name_plural = u'V2/妈妈活跃值列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.value_type, self.value_num)

    def value_type_name(self):
        return get_choice_name(self.VALUE_TYPES, self.value_type)

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def is_confirmed(self):
        return self.status == 2

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None


def activevalue_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    mama_id = instance.mama_id
    tasks_mama_fortune.task_activevalue_update_mamafortune.delay(mama_id)


post_save.connect(activevalue_update_mamafortune,
                  sender=ActiveValue, dispatch_uid='post_save_activevalue_update_mamafortune')


def confirm_previous_activevalue(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_activevalue
    if created and instance.value_type == 1:
        mama_id = instance.mama_id
        date_field = instance.date_field
        tasks_mama_activevalue.task_confirm_previous_activevalue.delay(mama_id, date_field, 2)


post_save.connect(confirm_previous_activevalue,
                  sender=ActiveValue, dispatch_uid='post_save_confirm_previous_activevalue')


class ReferalRelationship(BaseModel):
    """
    xiaolu mama referal relationship
    """
    referal_from_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    referal_to_mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'被推荐妈妈id')
    referal_to_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'被推荐者昵称')
    referal_to_mama_img = models.CharField(max_length=256, blank=True, verbose_name=u'被推荐者头像')

    class Meta:
        db_table = 'flashsale_xlmm_referal_relationship'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈推荐关系'
        verbose_name_plural = u'V2/妈妈推荐关系列表'

    def referal_to_mama_nick_display(self):
        if self.referal_to_mama_nick == "":
            return u"匿名用户"
        return self.referal_to_mama_nick

    def get_referal_award(self):
        """ 获取妈妈的推荐红包 """
        award_carrys = AwardCarry.objects.filter(mama_id=self.referal_from_mama_id,
                                                 contributor_mama_id=self.referal_to_mama_id)
        if award_carrys.exists():
            award_carry = award_carrys[0]
            return award_carry
        else:
            return None

    @classmethod
    def create_relationship_by_potential(cls, potential_record):
        """ 通过潜在妈妈列表中的记录创建推荐关系 """
        # 先查看是否有推荐关系存在(被推荐人　potential_record.potential_mama 潜在妈妈)
        ship = cls.objects.filter(referal_to_mama_id=potential_record.potential_mama).first()
        if ship:
            return ship, False
        ship = cls(referal_from_mama_id=potential_record.referal_mama,
                   referal_to_mama_id=potential_record.potential_mama,
                   referal_to_mama_nick=potential_record.nick,
                   referal_to_mama_img=potential_record.thumbnail)
        ship.save()
        return ship, True


def update_mamafortune_invite_num(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    mama_id = instance.referal_from_mama_id
    tasks_mama_fortune.task_update_mamafortune_invite_num.delay(mama_id)
    tasks_mama_fortune.task_update_mamafortune_mama_level.delay(mama_id)


post_save.connect(update_mamafortune_invite_num,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_mamafortune_invite_num')


def update_group_relationship(sender, instance, created, **kwargs):
    if not created:
        return

    from flashsale.xiaolumm.tasks_mama_relationship_visitor import task_update_group_relationship
    records = ReferalRelationship.objects.filter(referal_to_mama_id=instance.referal_from_mama_id)
    if records.count() > 0:
        record = records[0]
        task_update_group_relationship.delay(record.referal_from_mama_id, instance)


post_save.connect(update_group_relationship,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_group_relationship')


def referal_update_activevalue(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.tasks_mama_activevalue import task_referal_update_activevalue
    mama_id = instance.referal_from_mama_id
    date_field = instance.created.date()
    contributor_id = instance.referal_to_mama_id
    task_referal_update_activevalue.delay(mama_id, date_field, contributor_id)


post_save.connect(referal_update_activevalue,
                  sender=ReferalRelationship, dispatch_uid='post_save_referal_update_activevalue')


def referal_update_awardcarry(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.tasks_mama import task_referal_update_awardcarry
    task_referal_update_awardcarry.delay(instance)


post_save.connect(referal_update_awardcarry,
                  sender=ReferalRelationship, dispatch_uid='post_save_referal_update_awardcarry')


class GroupRelationship(BaseModel):
    """
    xiaolu mama group relationship
    """
    leader_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'领队妈妈id')
    referal_from_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'推荐妈妈id')
    member_mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'成员妈妈id')
    member_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    member_mama_img = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')

    class Meta:
        db_table = 'flashsale_xlmm_group_relationship'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈团队关系'
        verbose_name_plural = u'V2/妈妈团队关系列表'


def group_update_awardcarry(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama
    tasks_mama.task_group_update_awardcarry.delay(instance)

    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_update_mamafortune_mama_level.delay(instance.leader_mama_id)


post_save.connect(group_update_awardcarry,
                  sender=GroupRelationship, dispatch_uid='post_save_group_update_awardcarry')


class UniqueVisitor(BaseModel):
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    visitor_unionid = models.CharField(max_length=64, verbose_name=u"访客UnionID")
    visitor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'访客昵称')
    visitor_img = models.CharField(max_length=256, blank=True, verbose_name=u'访客头像')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # unionid+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')

    class Meta:
        db_table = 'flashsale_xlmm_unique_visitor'
        app_label = 'xiaolumm'
        verbose_name = u'V2/独立访客'
        verbose_name_plural = u'V2/独立访客列表'

    def visitor_description(self):
        return u"来自微信点击访问"

    def nick_display(self):
        if self.visitor_nick == '':
            return u"匿名用户"
        return self.visitor_nick


def visitor_update_clickcarry_and_activevalue(sender, instance, created, **kwargs):
    if not created:
        return

    mama_id = instance.mama_id
    date_field = instance.date_field

    try:
        from flashsale.xiaolumm.models import XiaoluMama
        mama = XiaoluMama.objects.get(id=mama_id)
        if not mama.is_click_countable():
            return
    except XiaoluMama.DoesNotExist:
        return

    from flashsale.xiaolumm.tasks_mama_clickcarry import task_visitor_increment_clickcarry
    task_visitor_increment_clickcarry.delay(mama_id, date_field)

    from flashsale.xiaolumm.tasks_mama_activevalue import task_visitor_increment_activevalue
    task_visitor_increment_activevalue.delay(mama_id, date_field)

    from flashsale.xiaolumm.tasks_mama_dailystats import task_visitor_increment_dailystats
    task_visitor_increment_dailystats.delay(mama_id, date_field)


post_save.connect(visitor_update_clickcarry_and_activevalue,
                  sender=UniqueVisitor, dispatch_uid='post_save_visitor_update_clickcarry_and_activevalue')



class MamaDailyAppVisit(BaseModel):
    DEVICE_UNKNOWN = 0
    DEVICE_ANDROID = 1
    DEVICE_IOS = 2

    DEVICE_TYPES = ((DEVICE_UNKNOWN, 'Unknown'), (DEVICE_ANDROID, 'Android'), (DEVICE_IOS, 'IOS'))

    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # mama_id+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    device_type = models.IntegerField(default=0, choices=DEVICE_TYPES, db_index=True, verbose_name=u'设备')
    version = models.CharField(max_length=32, blank=True, verbose_name=u'版本信息')
    user_agent = models.CharField(max_length=128, blank=True, verbose_name=u'UserAgent')

    class Meta:
        db_table = 'flashsale_xlmm_mamadailyappvisit'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈app访问'
        verbose_name_plural = u'V2/妈妈app访问列表'

    def get_user_version(self):
        from flashsale.apprelease.models import AppRelease
        if self.device_type == AppRelease.DEVICE_ANDROID:
            version_code = self.version
            version = AppRelease.get_version_info(self.device_type, version_code)
            return version # Android
        return self.version #IOS

    def get_latest_version(self):
        from flashsale.apprelease.models import AppRelease
        version = AppRelease.get_latest_version(self.device_type)
        return version

def mama_daily_app_visit_stats(sender, instance, created, **kwargs):
    if not created:
        return

    from django_statsd.clients import statsd
    today_date = datetime.date.today()
    visit_count = MamaDailyAppVisit.objects.filter(date_field=today_date).count()
    key = "mama.daily_app_visit"
    statsd.timing(key, visit_count)

post_save.connect(mama_daily_app_visit_stats,
                  sender=MamaDailyAppVisit, dispatch_uid='post_save_mama_daily_app_visit_stats')


def mama_app_version_check(sender, instance, created, **kwargs):
    if not created:
        return

    from flashsale.xiaolumm.tasks_mama_push import task_weixin_push_update_app
    task_weixin_push_update_app.delay(instance)

post_save.connect(mama_app_version_check,
                  sender=MamaDailyAppVisit, dispatch_uid='post_save_mama_app_version_check')


def mama_update_device_stats(sender, instance, created, **kwargs):
    if not created:
        return

    user_version = instance.get_user_version()
    latest_version = instance.get_latest_version()

    uni_key = "%s-%s" % (instance.device_type, instance.date_field)
    md = MamaDeviceStats.objects.filter(uni_key=uni_key).first()
    if not md:
        md = MamaDeviceStats(device_type=instance.device_type, uni_key=uni_key, date_field=instance.date_field)
        md.save()
        
    if user_version == latest_version:
        # already latest, no need to push udpate reminder
        md.num_latest += 1
        md.save(update_fields=['num_latest', 'modified'])
        return

    md.num_outdated += 1
    md.save(update_fields=['num_outdated', 'modified'])

post_save.connect(mama_update_device_stats,
                  sender=MamaDailyAppVisit, dispatch_uid='post_save_mama_update_device_stats')
