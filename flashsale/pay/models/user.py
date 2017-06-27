# coding=utf-8
from __future__ import unicode_literals

import datetime
import logging
import random

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.db import models, transaction
from django.db.models.signals import post_save
from django.db.models import Sum, F
from django.core.cache import cache

from core.models import BaseModel, BaseTagModel
from .base import PayBaseModel
from .envelope import Envelop
from .. import constants
from ..managers import budget, customer

logger = logging.getLogger(__name__)


class Register(PayBaseModel):
    MAX_VALID_COUNT = 3
    MAX_SUBMIT_TIMES = 20

    id = models.AutoField(primary_key=True, verbose_name=u'ID')
    cus_uid = models.BigIntegerField(db_index=True, default=0, null=True, verbose_name=u"客户ID")
    vmobile = models.CharField(max_length=11, unique=True, blank=True, verbose_name=u"待验证手机")
    verify_code = models.CharField(max_length=8, blank=True, verbose_name=u"验证码")

    vemail = models.CharField(max_length=8, db_index=True, blank=True, verbose_name=u"待验证邮箱")
    mail_code = models.CharField(max_length=128, blank=True, verbose_name=u"邮箱验证码")

    verify_count = models.IntegerField(default=0, verbose_name=u'验证次数')
    submit_count = models.IntegerField(default=0, verbose_name=u'提交次数')

    mobile_pass = models.BooleanField(default=False, db_index=True, verbose_name=u"手机验证通过")
    mail_pass = models.BooleanField(default=False, db_index=True, verbose_name=u"邮箱验证通过")

    code_time = models.DateTimeField(blank=True, null=True, verbose_name=u'验证码生成时间')
    mail_time = models.DateTimeField(blank=True, null=True, verbose_name=u'验证码发送时间')

    initialize_pwd = models.BooleanField(default=False, verbose_name=u"初始化密码")

    class Meta:
        db_table = 'flashsale_register'
        app_label = 'pay'
        verbose_name = u'特卖用户/注册'
        verbose_name_plural = u'特卖用户/注册列表'

    def __unicode__(self):
        return '<%s>' % (self.id)

    def genValidCode(self):
        return ''.join(random.sample(list('0123456789'), 6))

    def genMailCode(self):
        return ''.join(random.sample(list('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'), 32))

    def verifyable(self):
        dt = datetime.datetime.now()
        if self.code_time and (dt - self.code_time).days > 0:
            self.verify_count = 1
            self.save()
            return True

        if self.verify_count >= self.MAX_VALID_COUNT:
            return False
        return True

    def is_verifyable(self):
        """ 能否获取验证码 """
        return self.verifyable()

    def is_submitable(self):
        """ 能否提交验证 """
        dt = datetime.datetime.now()
        if self.code_time and (dt - self.code_time).days > 1:
            self.submit_count = 1
            self.save()
            return True
        if self.submit_count > self.MAX_SUBMIT_TIMES:
            return False
        return True

    def check_code(self, vcode):
        """ 检查验证码是否正确 """
        if self.verify_code and self.verify_code == vcode:
            self.submit_count = 0
            self.save()
            return True
        self.submit_count += 1
        self.save()
        return False


def genCustomerNickname():
    """
    生成用户的默认昵称
    """
    chr_list = [''.join(map(chr, range(97, 123))), ''.join(map(chr, range(65, 91))), ''.join(map(chr, range(48, 58)))]
    chr_str = ''.join(chr_list)
    return ''.join(random.sample(chr_str, 6))


class Customer(BaseTagModel):
    class Meta:
        db_table = 'flashsale_customer'
        app_label = 'pay'
        verbose_name = u'特卖用户/客户'
        verbose_name_plural = u'特卖用户/客户列表'

    INACTIVE = 0  # 未激活
    NORMAL = 1  # 正常
    DELETE = 2  # 删除
    FREEZE = 3  # 冻结
    SUPERVISE = 4  # 监管

    USER_STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (INACTIVE, u'未激活'),
        (DELETE, u'删除'),
        (FREEZE, u'冻结'),
        (SUPERVISE, u'监管'),
    )

    # TODO@MERON.2017.04.14 此处需注释, 显示写出会导致tagging主动加载model对应tags
    # id = models.AutoField(primary_key=True, verbose_name=u'客户ID')
    user = models.OneToOneField(DjangoUser, verbose_name=u'原始用户')
    nick = models.CharField(max_length=32, blank=True, default=genCustomerNickname, verbose_name=u'昵称')
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'头像')
    mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'手机')
    email = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'邮箱')
    phone = models.CharField(max_length=18, blank=True, verbose_name=u'电话')

    openid = models.CharField(max_length=28, db_index=True, blank=True, verbose_name=u'微信ID',
                              help_text='停止使用@2017.6.14')
    unionid = models.CharField(max_length=28, db_index=True, verbose_name=u'联合ID')

    status = models.IntegerField(choices=USER_STATUS_CHOICES, default=NORMAL, verbose_name=u'状态')

    first_paytime = models.DateTimeField(null=True,blank=True,verbose_name=u'首次购买日期')
    #     latest_paytime  = models.DateTimeField(null=True,blank=True,verbose_name=u'最近购买日期')

    objects = customer.CustomerManager()

    def __unicode__(self):
        return '%s(%s)' % (self.nick, self.id)

    def is_loginable(self):
        return self.status == self.NORMAL

    def is_wxauth(self):
        """ 是否微信授权 """
        if (self.unionid.strip() and
                    datetime.datetime.now() > datetime.datetime(2015, 10, 30)):  # 关联用户订单未转移过渡期
            return True
        return False

    @classmethod
    def getCustomerCacheKey(cls, request_user_id):
        return 'flashsale_customer_cache_by_user_id_{}'.format(request_user_id)

    @classmethod
    def getCustomerByUser(cls, user):
        cache_key = cls.getCustomerCacheKey(user.id)
        cache_value = cache.get(cache_key)
        if not cache_value:
            customers = cls.objects.filter(user=user.id)
            cache_value = customers.first()
            cache.set(cache_key, cache_value, 60 * 60)
        return cache_value

    @property
    def mama_id(self):
        if not self.unionid:
            return None
        from flashsale.xiaolumm.models import XiaoluMama
        mama = XiaoluMama.objects.filter(openid=self.unionid).first()
        if not mama:
            return None
        return mama.id

    def get_xiaolumm(self):
        if not self.unionid:
            return None
        if not hasattr(self, '_xiaolumm_'):
            from flashsale.xiaolumm.models import XiaoluMama
            self._xiaolumm_ = XiaoluMama.objects.filter(openid=self.unionid).first()
        return self._xiaolumm_

    def get_charged_mama(self):
        """ 获取当前用户对应的小鹿妈妈 """
        if not self.unionid:
            return None
        if not hasattr(self, '_charged_mama_'):
            from flashsale.xiaolumm.models import XiaoluMama

            self._charged_mama_ = XiaoluMama.objects.filter(openid=self.unionid,
                                                            charge_status=XiaoluMama.CHARGED).first()
        return self._charged_mama_

    def getXiaolumm(self):
        """ 获取当前用户对应的小鹿妈妈 """
        if not self.unionid:
            return None
        if not hasattr(self, '_customer_mama_'):
            from flashsale.xiaolumm.models import XiaoluMama
            self._customer_mama_ = XiaoluMama.objects.filter(
                    openid=self.unionid,status=XiaoluMama.EFFECT,
                    charge_status=XiaoluMama.CHARGED).first()
        return self._customer_mama_

    def get_referal_xlmm(self):
        """ 获取推荐当前用户的小鹿妈妈 """
        if not hasattr(self, '_customer_referal_mama_'):
            from flashsale.xiaolumm.models.models_fans import XlmmFans
            from flashsale.xiaolumm.models import XiaoluMama

            xlmm_fan = XlmmFans.objects.filter(fans_cusid=self.id).first()
            self._customer_referal_mama_ = None
            if xlmm_fan:
                self._customer_referal_mama_ = XiaoluMama.objects.filter(id=xlmm_fan.xlmm).first()
        return self._customer_referal_mama_

    def get_openid_and_unoinid_by_appkey(self, appkey):
        if not self.unionid.strip():
            return ('', '')
        from shopapp.weixin import options
        openid = options.get_openid_by_unionid(self.unionid, appkey)
        if not openid and appkey == settings.WX_PUB_APPID:
            return self.openid, self.unionid
        return openid, self.unionid

    def getBudget(self):
        """特卖用户钱包"""
        try:
            budget = UserBudget.objects.get(user_id=self.id)
            return budget
        except UserBudget.DoesNotExist:
            return None

    def is_attention_wx_public(self):
        """ 是否关注微信公众号 ,存在关注记录返回1否则返回0 """
        from shopapp.weixin.models import WeixinUnionID
        try:
            WeixinUnionID.objects.get(app_key=settings.WX_PUB_APPID, unionid=self.unionid)
            return 1
        except WeixinUnionID.DoesNotExist:
            return 0

    def get_coupon_num(self):
        """ 当前用户的优惠券数量 """
        from flashsale.coupon.models import UserCoupon
        # 过滤截止时间大于现在的优惠券
        now = datetime.datetime.now()
        return UserCoupon.objects.filter(customer_id=self.pk,
                                         expires_time__gte=now,
                                         status=UserCoupon.UNUSED).count()  # 未使用优惠券数量

    def get_waitpay_num(self):
        """ 当前用户的待支付订单数量 """
        from .trade import SaleTrade
        return SaleTrade.objects.filter(buyer_id=self.pk, status=SaleTrade.WAIT_BUYER_PAY).count()

    def get_waitgoods_num(self):
        """ 当前用户的待收货数量 """
        from .trade import SaleTrade
        return SaleTrade.objects.filter(buyer_id=self.pk, status__in=(SaleTrade.WAIT_SELLER_SEND_GOODS,
                                                                      SaleTrade.WAIT_BUYER_CONFIRM_GOODS)).count()

    def get_refunds_num(self):
        """ 当前用户的退换货数量 """
        from .refund import SaleRefund
        return SaleRefund.objects.filter(buyer_id=self.pk).exclude(
            status__in=(SaleRefund.REFUND_CLOSED,
                       SaleRefund.REFUND_SUCCESS,
                       SaleRefund.REFUND_REFUSE_BUYER,
                       SaleRefund.NO_REFUND)).count()

    def has_user_password(self):
        """ 是否有密码 """
        if self.user.password:
            return True
        else:
            return False

    def set_nickname(self, nickname, force_update=False):
        if self.nick and not force_update:
            return
        self.nick = nickname

    @property
    def nick_name(self):
        """
        获取默认昵称如果没有昵称的话
        """
        if (self.nick is None) or (self.nick.strip() == ''):
            self.nick = genCustomerNickname()
            self.save(update_fields=['nick'])
            return self.nick
        else:
            return self.nick

    def get_default_address(self):
        from .address import UserAddress
        queryset = UserAddress.objects.filter(cus_uid=self.id, status=UserAddress.NORMAL).order_by('-default')
        return queryset.first()

def post_save_invalid_customer_cache(sender, instance, created, **kwargs):
    cache_key = Customer.getCustomerCacheKey(instance.user_id)
    cache.delete(cache_key)

post_save.connect(post_save_invalid_customer_cache, sender=Customer,
                  dispatch_uid='post_save_invalid_customer_cache')

def sync_xlmm_fans_nick_thumbnail(sender, instance, created, **kwargs):
    if not created:
        return

    from flashsale.pay.tasks import task_sync_xlmm_fans_nick_thumbnail
    task_sync_xlmm_fans_nick_thumbnail.delay(instance)

post_save.connect(sync_xlmm_fans_nick_thumbnail, sender=Customer,
                  dispatch_uid='post_save_sync_xlmm_fans_nick_thumbnail')


def sync_xlmm_mobile_by_customer(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.pay.tasks import task_sync_xlmm_mobile_by_customer
    task_sync_xlmm_mobile_by_customer.delay(instance)

post_save.connect(sync_xlmm_mobile_by_customer, sender=Customer,
                  dispatch_uid='post_save_sync_xlmm_mobile_by_customer')


class UserBudget(PayBaseModel):
    """ 特卖用户钱包 """

    class Meta:
        db_table = 'flashsale_userbudget'
        app_label = 'pay'
        verbose_name = u'特卖/用户零钱'
        verbose_name_plural = u'特卖/用户零钱列表'

    user = models.OneToOneField(Customer, verbose_name=u'原始用户')
    amount = models.IntegerField(default=0, verbose_name=u'账户余额(分)')
    total_income = models.IntegerField(default=0, verbose_name=u'总收入')
    total_expense = models.IntegerField(default=0, verbose_name=u'总支出')

    def __unicode__(self):
        return u'<%s,%s>' % (self.user, self.amount)

    @property
    def mama_id(self):
        from flashsale.xiaolumm.models import XiaoluMama
        mama = XiaoluMama.objects.filter(openid=self.user.unionid).first()
        if mama:
            return mama.id
        return ''

    @property
    def budget_cash(self):
        return float('%.2f' % (self.amount * 0.01))

    @property
    def pending_cash(self):
        res = BudgetLog.objects.filter(customer_id=self.user.id,status=BudgetLog.PENDING).aggregate(total=Sum('flow_amount'))
        total = res['total'] or 0
        return float('%.2f' % (total * 0.01))

    def get_amount_display(self):
        """ 返回金额　"""
        return self.budget_cash

    def charge_pending(self, strade_id, payment):
        """ 提交支付 """
        try:
            BudgetLog.objects.get(customer_id=self.user.id,
                                  referal_id=strade_id,
                                  budget_log_type=BudgetLog.BG_CONSUM)
        except BudgetLog.DoesNotExist:
            BudgetLog.create(customer_id=self.user.id,
                             budget_type=BudgetLog.BUDGET_OUT,
                             flow_amount=payment,
                             referal_id=strade_id,
                             budget_log_type=BudgetLog.BG_CONSUM,
                             uni_key='st_%s' % strade_id,
                             status=BudgetLog.PENDING)
            return True
        return True

    def charge_confirm(self, strade_id):
        """ 确认支付 """

        blogs = BudgetLog.objects.filter(customer_id=self.user.id,referal_id=strade_id,budget_log_type=BudgetLog.BG_CONSUM)
        blog = blogs.first()
        if not blog:
            logger.error('budget payment log not found: customer=%s, trade_id=%s'%(self.user.id,strade_id))
            return False

        #  如果订单超时关闭又支付成功,则余额支付状态页需要改回
        if blog.status == BudgetLog.CANCELED:
            blog.status = BudgetLog.PENDING
        return blog.confirm_budget_log()

    def charge_cancel(self, strade_id):
        """ 支付取消 """
        blogs = BudgetLog.objects.filter(customer_id=self.user.id,
                                         referal_id=strade_id,
                                         budget_log_type=BudgetLog.BG_CONSUM)
        if blogs.exists():
            return blogs[0].cancel_budget_log()

    def is_could_cashout(self):
        """ 设置普通用户钱包是否可以提现控制字段 """
        return constants.IS_USERBUDGET_COULD_CASHOUT

    def action_budget_cashout(self, cash_out_amount, verify_code=None, channel=None, name=None, card_id=None):
        """
        用户钱包提现
        cash_out_amount　整型　以分为单位
        """
        from flashsale.restpro.v2.views.xiaolumm import CashOutPolicyView
        min_cashout_amount = CashOutPolicyView.MIN_CASHOUT_AMOUNT
        max_cashout_amount = CashOutPolicyView.MAX_CASHOUT_AMOUNT
        audit_cashout_amount = CashOutPolicyView.AUDIT_CASHOUT_AMOUNT

        mobile = self.user.mobile
        if not (mobile and mobile.isdigit() and len(mobile) == 11):
            return 8, '提现请先至个人中心绑定手机号，以便接收验证码！'

        from flashsale.restpro.v2.views.verifycode_login import validate_code
        if not validate_code(mobile, verify_code):
            return 9, '验证码不对或已过期，请重新发送验证码！'

        if not isinstance(cash_out_amount, int):  # 参数类型错误(如果不是整型)
            return 3, '参数错误'

        if cash_out_amount < min_cashout_amount:
            info = u'最小提现额%s元' % int(min_cashout_amount * 0.01)
            return 1, info
        elif cash_out_amount > max_cashout_amount and channel != 'wx_transfer':
            info = u'一次提现不能超过%s元' % int(max_cashout_amount*0.01)
            return 5, info
        elif cash_out_amount > self.amount:
            return 2, '提现金额大于账户余额'

        from shopback.monitor.models import XiaoluSwitch
        if XiaoluSwitch.is_switch_open(4):
            return 11, '系统维护中，提现功能暂时关闭!'

        try:
            if not self.user.unionid:
                return 5, '提现请先关注公众号［小鹿美美］'
            from shopapp.weixin.models import WeixinUnionID
            wx_union = WeixinUnionID.objects.get(app_key=settings.WX_PUB_APPID, unionid=self.user.unionid)
        except WeixinUnionID.DoesNotExist:
            return 4, '提现请先关注公众号［小鹿美美］'  # 用户没有公众号提现账户

        # 发放公众号红包
        recipient = wx_union.openid  # 接收人的openid
        body = constants.ENVELOP_BODY  # 红包祝福语
        description = constants.ENVELOP_CASHOUT_DESC.format(self.user.id, self.amount)  # 备注信息 用户id, 提现前金额

        customer_id = self.user.id
        if BudgetLog.is_cashout_limited(customer_id):
            return 6, '今日提现次数已满，请明天再来哦！'

        uni_key = BudgetLog.gen_uni_key(customer_id, BudgetLog.BUDGET_OUT, BudgetLog.BG_CASHOUT)
        bl = BudgetLog.objects.filter(uni_key=uni_key).first()
        if bl:
            return 7, '您两次提交间隔太短，稍等下再试哦！'

        if channel == 'wx_transfer' and (not name):
            return 101, '请填写真实姓名'

        with transaction.atomic():
            # 创建钱包提现记录
            budget_log = BudgetLog.create(customer_id, BudgetLog.BUDGET_OUT,
                                          cash_out_amount, BudgetLog.BG_CASHOUT,
                                          status=BudgetLog.PENDING, uni_key=uni_key)

            # TODO@meron后面如果要改公众号转账, 则platform需要修改
            if channel in ('wx_transfer', Envelop.SANDPAY):
                platform = channel == Envelop.SANDPAY and Envelop.SANDPAY or Envelop.WX_TRANSFER
                if channel == Envelop.SANDPAY :
                    recipient = card_id
                envelop = Envelop.objects.create(
                    amount=cash_out_amount,
                    platform=platform,
                    recipient=recipient,
                    subject=Envelop.XLAPP_CASHOUT,
                    body=name or '',
                    receiver=self.user.mobile,
                    description=description,
                    referal_id=budget_log.id,
                    customer_id=self.user.id,
                )
            else:
                envelop = Envelop.objects.create(
                    amount=cash_out_amount,
                    platform=Envelop.WXPUB,
                    recipient=recipient,
                    subject=Envelop.XLAPP_CASHOUT,
                    body=body,
                    receiver=self.user.mobile,
                    description=description,
                    referal_id=budget_log.id,
                    customer_id=self.user.id,
                )
            budget_log.referal_id = envelop.id
            budget_log.save()

        # 通过微信公众号小额提现，直接发红包，无需审核，一天限制2次
        if cash_out_amount <= audit_cashout_amount and cash_out_amount >= min_cashout_amount:
            envelop.send_envelop()

        return 0, '提交成功'

def userbudget_post_save_unfreeze_coupon(sender, instance, created, **kwargs):

    try:
        from flashsale.pay.tasks import task_userbudget_post_save_unfreeze_coupon

        transaction.on_commit(lambda: task_userbudget_post_save_unfreeze_coupon(instance))
        logger.info('userbudget update:%s %s, %s, %s' %
            (instance.user.id, instance.amount, instance.total_income, instance.total_expense))
    except Exception,exc:
        logger.error('budgetlog error: %s'%exc, exc_info=True)


post_save.connect(userbudget_post_save_unfreeze_coupon, sender=UserBudget,
                  dispatch_uid='post_save_userbudget')

class BudgetLog(PayBaseModel):
    """ 特卖用户钱包记录 """

    class Meta:
        db_table = 'flashsale_userbudgetlog'
        app_label = 'pay'
        verbose_name = u'特卖/用户钱包收支记录'
        verbose_name_plural = u'特卖/用户钱包收支记录'

    BUDGET_IN = 0
    BUDGET_OUT = 1

    BUDGET_CHOICES = (
        (BUDGET_IN, u'收入'),
        (BUDGET_OUT, u'支出'),
    )

    BG_ENVELOPE = 'envelop'
    BG_REFUND = 'refund'
    BG_REFUND_POSTAGE = 'postage'
    BG_CONSUM = 'consum'
    BG_CASHOUT = 'cashout'
    BG_CASHOUT_FAIL = 'cashfail'
    BG_MAMA_CASH = 'mmcash'
    BG_REFERAL_FANS = 'rfan'
    BG_SUBSCRIBE = 'subs'
    BG_EXCHG_ORDER = 'exchg'
    BG_RETURN_COUPON = 'rtcoup'
    BG_FANDIAN = 'fandian'
    BG_CLICK = 'click'
    BG_ORDER = 'order'
    BG_AWARD = 'award'
    BG_MAMA_CONSUM = 'mmconsum'
    BG_RETURN_EXCHG = 'rtexchg'
    BG_CARRY_CANCEL = 'cancel'

    BUDGET_LOG_CHOICES = (
        # 收入
        (BG_REFUND, u'退款'),
        (BG_REFUND_POSTAGE, u'退款补邮费'),
        (BG_MAMA_CASH, u'代理提现至余额'),
        (BG_REFERAL_FANS, u'推荐粉丝'),
        (BG_SUBSCRIBE, u'关注'),
        (BG_RETURN_COUPON, u'退精品券'),
        (BG_ENVELOPE, u'红包'),
        (BG_FANDIAN, u'精品汇返点'),
        (BG_CLICK, u'点击收益'),
        (BG_ORDER, u'订单收益'),
        (BG_AWARD, u'奖金收益'),
        (BG_EXCHG_ORDER, u'兑换订单'),
        (BG_CASHOUT_FAIL, u'提现失败退回'),
        # 支出
        (BG_CONSUM, u'消费'),
        (BG_CASHOUT, u'提现'),
        (BG_CARRY_CANCEL, u'收益取消'),
        (BG_MAMA_CONSUM, u'妈妈消费'),
        (BG_RETURN_EXCHG, u'取消兑换'),
    )

    CONFIRMED = 0
    CANCELED = 1
    PENDING = 2

    STATUS_CHOICES = (
        (PENDING, u'待确定'),
        (CONFIRMED, u'已确定'),
        (CANCELED, u'已取消'),
    )

    customer_id = models.BigIntegerField(db_index=True, verbose_name=u'用户id')
    flow_amount = models.IntegerField(default=0, verbose_name=u'流水金额(分)')
    balance = models.IntegerField(default=0, verbose_name=u'变动后金额(分)')
    budget_type = models.IntegerField(choices=BUDGET_CHOICES, db_index=True, null=False, verbose_name=u"收支类型")
    budget_log_type = models.CharField(max_length=8, choices=BUDGET_LOG_CHOICES, db_index=True, null=False,
                                       verbose_name=u"记录类型")
    budget_date = models.DateField(default=datetime.date.today, verbose_name=u'业务日期')
    referal_id = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'引用id')
    status = models.IntegerField(choices=STATUS_CHOICES, db_index=True, default=CONFIRMED, verbose_name=u'状态')
    uni_key = models.CharField(max_length=128, unique=True, null=True, verbose_name=u'唯一ID')
    objects = budget.BudgetLogManager()

    def __unicode__(self):
        return u'<%s,%s>' % (self.customer_id, self.flow_amount)

    @classmethod
    def gen_uni_key(cls, customer_id, budget_type, budget_log_type):
        """
        budget_log_type-budget_type-customer_id-count|budget_date
        """
        budget_date = datetime.date.today()
        count = cls.objects.filter(customer_id=customer_id, budget_type=budget_type, budget_log_type=budget_log_type, budget_date=budget_date).count()
        return '%s-%s-%d-%d|%s' % (budget_log_type, budget_type, customer_id, count+1, budget_date)

    @property
    def user_budget(self):
        return UserBudget.objects.get(user__id=self.customer_id)

    @classmethod
    def create(cls, customer_id, budget_type, flow_amount, budget_log_type,
               budget_date=None, referal_id='', status=None, uni_key=None):
        """
        创建收支记录
        """
        from flashsale.xiaolumm.models import AccountEntry

        budget_date = budget_date or datetime.date.today()
        status = status or BudgetLog.CONFIRMED
        customer = Customer.objects.get(id=customer_id)
        uni_key = uni_key or BudgetLog.gen_uni_key(customer_id, budget_type, budget_log_type)

        if status == BudgetLog.CANCELED:
            raise Exception('取消状态不予创建!')

        with transaction.atomic():
            # 更新钱包余额 UserBudget
            budget, created = UserBudget.objects.get_or_create(user=customer, defaults={
                'amount': 0,
                'total_income': 0,
                'total_expense': 0
            })

            if budget_type == BudgetLog.BUDGET_IN:
                if status == BudgetLog.CONFIRMED:
                    budget.amount = F('amount') + flow_amount
                    budget.total_income = F('total_income') + flow_amount
                    if budget_log_type in [BudgetLog.BG_CLICK, BudgetLog.BG_ORDER, BudgetLog.BG_AWARD]:
                        AccountEntry.create(customer_id, AccountEntry.SB_MARKET_FANLI, AccountEntry.SB_PAY_XIAOLU, flow_amount)
                    if budget_log_type == BudgetLog.BG_REFUND:
                        AccountEntry.create(customer_id, AccountEntry.SB_INCOME_REFUND, AccountEntry.SB_PAY_XIAOLU, flow_amount)
                    if budget_log_type == BudgetLog.BG_MAMA_CASH:
                        AccountEntry.create(customer_id, AccountEntry.SB_PAY_MAMA_CONFIRM, AccountEntry.SB_PAY_XIAOLU, flow_amount)
                    if budget_log_type == BudgetLog.BG_ENVELOPE:
                        AccountEntry.create(customer_id, AccountEntry.SB_MARKET_ENVELOPE, AccountEntry.SB_PAY_XIAOLU, flow_amount)

            if budget_type == BudgetLog.BUDGET_OUT:
                budget.amount = F('amount') - flow_amount
                budget.total_expense = F('total_expense') + flow_amount
                if budget_log_type == BudgetLog.BG_CONSUM:
                    AccountEntry.create(customer_id, AccountEntry.SB_PAY_XIAOLU, AccountEntry.SB_RECEIVE_WALLET, flow_amount)
                if budget_log_type == BudgetLog.BG_CASHOUT:
                    if status == BudgetLog.PENDING:
                        AccountEntry.create(customer_id, AccountEntry.SB_PAY_XIAOLU, AccountEntry.SB_PAY_CASHOUT_PENDING, flow_amount)
                    if status == BudgetLog.CONFIRMED:
                        AccountEntry.create(customer_id, AccountEntry.SB_PAY_XIAOLU, AccountEntry.SB_PAY_CASHOUT_CONFIRM, flow_amount)

            budget.save()

            ub = UserBudget.objects.get(user=customer)
            # 创建收支记录 BudgetLog
            budget_log = cls(
                customer_id=customer_id,
                flow_amount=flow_amount,
                balance=ub.amount,
                budget_type=budget_type,
                budget_log_type=budget_log_type,
                budget_date=budget_date,
                referal_id=referal_id,
                status=status,
                uni_key=uni_key
            )
            budget_log.save()

        return budget_log

    @classmethod
    def create_salerefund_log(cls, refund, flow_amount):
        """
        功能：　创建退款单对应的　余额记录
        :arg  refund:SaleRefund instance,  flow_amount:退款金额(分)
        """
        uni_key = cls.gen_uni_key(refund.buyer_id, BudgetLog.BUDGET_IN, BudgetLog.BG_REFUND)
        budget_log = cls.create(customer_id=refund.buyer_id,
                                budget_type=BudgetLog.BUDGET_IN,
                                flow_amount=flow_amount,
                                budget_log_type=BudgetLog.BG_REFUND,
                                referal_id=refund.id,
                                status=BudgetLog.CONFIRMED,
                                uni_key=uni_key)
        return budget_log

    @classmethod
    def create_salerefund_postage_log(cls, refund, flow_amount):
        """
        功能：　创建退款单对应的　补邮费记录
        :arg  refund:SaleRefund instance,  flow_amount:退款金额(分)
        """
        uni_key = cls.gen_uni_key(refund.buyer_id, BudgetLog.BUDGET_IN, BudgetLog.BG_REFUND_POSTAGE)
        budget_log = cls.create(customer_id=refund.buyer_id,
                                flow_amount=flow_amount,
                                budget_type=BudgetLog.BUDGET_IN,
                                budget_log_type=BudgetLog.BG_REFUND_POSTAGE,
                                referal_id=refund.id,
                                status=BudgetLog.CONFIRMED,
                                uni_key=uni_key)
        return budget_log

    @classmethod
    def create_return_coupon_log(cls, customer_id, quote_id, flow_amount):
        # type: (int, int, int) -> BudgetLog
        """用户退还优惠券　兑换　金额 给用户
        """
        uni_key = cls.gen_uni_key(customer_id, BudgetLog.BUDGET_IN, BudgetLog.BG_RETURN_COUPON)
        budget_log = cls.create(customer_id=customer_id,
                                flow_amount=flow_amount,
                                budget_type=BudgetLog.BUDGET_IN,
                                budget_log_type=BudgetLog.BG_RETURN_COUPON,
                                referal_id=quote_id,
                                status=BudgetLog.PENDING,
                                uni_key=uni_key)
        return budget_log

    @classmethod
    def create_mm_cash_out_2_budget(cls, customer_id, value, referal_id):
        # type: (int, int, int) -> BudgetLog
        """妈妈从 妈妈钱包 提现到 小鹿钱包创建小鹿钱包记录
        """
        budget_type = BudgetLog.BUDGET_IN
        budget_log_type = BudgetLog.BG_MAMA_CASH
        uni_key = BudgetLog.gen_uni_key(customer_id, budget_type, budget_log_type)
        bl = cls.create(customer_id, budget_type, value, budget_log_type,
                        referal_id=referal_id, status=cls.CONFIRMED, uni_key=uni_key)
        return bl

    def get_flow_amount_display(self):
        """ 返回金额　"""
        return self.flow_amount / 100.0

    def confirm_budget_log(self):
        # type: () -> bool
        """确定钱包记录
        """
        from flashsale.xiaolumm.models import AccountEntry

        if self.status == BudgetLog.CONFIRMED:
            return False
        user_budget = self.user_budget  # 小鹿钱包

        with transaction.atomic():
            if self.budget_type == BudgetLog.BUDGET_IN:  # 收入
                if self.status in [BudgetLog.PENDING, BudgetLog.CANCELED]:  # 待确定, 取消 => 确定
                    user_budget.amount = F('amount') + self.flow_amount
                    user_budget.total_income = F('total_income') + self.flow_amount
                    if self.budget_log_type in [BudgetLog.BG_CLICK, BudgetLog.BG_ORDER, BudgetLog.BG_AWARD]:
                        AccountEntry.create(self.customer_id, AccountEntry.SB_MARKET_FANLI, AccountEntry.SB_PAY_XIAOLU, self.flow_amount)

            if self.budget_type == BudgetLog.BUDGET_OUT:  # 支出
                if self.status == BudgetLog.CANCELED:  # 取消 => 确定
                    user_budget.amount = F('amount') - self.flow_amount
                    user_budget.total_expense = F('total_expense') + self.flow_amount

                if self.budget_log_type == BudgetLog.BG_CASHOUT:
                    if self.status == BudgetLog.PENDING:
                        AccountEntry.create(self.customer_id, AccountEntry.SB_PAY_CASHOUT_PENDING,
                                            AccountEntry.SB_PAY_CASHOUT_CONFIRM, self.flow_amount)
                    if self.status == BudgetLog.CANCELED:
                        AccountEntry.create(self.customer_id, AccountEntry.SB_PAY_XIAOLU,
                                            AccountEntry.SB_PAY_CASHOUT_CONFIRM, self.flow_amount)


            user_budget.save()  # 保存用户钱包

            ub = UserBudget.objects.get(user=self.customer_id)
            self.balance = ub.amount
            self.status = BudgetLog.CONFIRMED
            self.save()

        return True

    def cancel_budget_log(self):
        # type: () -> bool
        """取消 钱包记录
        """
        from flashsale.xiaolumm.models import AccountEntry

        if self.status == BudgetLog.CANCELED:
            return False
        user_budget = self.user_budget  # 小鹿钱包

        with transaction.atomic():
            if self.budget_type == BudgetLog.BUDGET_IN:  # 收入
                if self.status == BudgetLog.CONFIRMED:  # 确定 => 取消
                    user_budget.amount = F('amount') - self.flow_amount
                    user_budget.total_income = F('total_income') - self.flow_amount
                    if self.budget_log_type in [BudgetLog.BG_CLICK, BudgetLog.BG_ORDER, BudgetLog.BG_AWARD]:
                        AccountEntry.create(self.customer_id, AccountEntry.SB_PAY_XIAOLU, AccountEntry.SB_MARKET_FANLI, self.flow_amount)

            if self.budget_type == BudgetLog.BUDGET_OUT:  # 支出
                if self.status in [BudgetLog.CONFIRMED, BudgetLog.PENDING]:  # 确定, 待确定 => 取消
                    user_budget.amount = F('amount') + self.flow_amount
                    user_budget.total_expense = F('total_expense') - self.flow_amount
                if self.budget_log_type == BudgetLog.BG_CASHOUT:
                    if self.status == BudgetLog.PENDING:
                        AccountEntry.create(self.customer_id, AccountEntry.SB_PAY_CASHOUT_PENDING,
                                            AccountEntry.SB_PAY_XIAOLU, self.flow_amount)
                    if self.status == BudgetLog.CONFIRMED:
                        AccountEntry.create(self.customer_id, AccountEntry.SB_PAY_CASHOUT_CONFIRM,
                                            AccountEntry.SB_PAY_XIAOLU, self.flow_amount)
            user_budget.save()  # 保存用户钱包

            ub = UserBudget.objects.get(user=self.customer_id)
            self.balance = ub.amount
            self.status = BudgetLog.CANCELED
            self.save()

        return True

    def chnage_peding_income_amount(self, new_amount):
        """
        修改预计收益金额
        """
        if self.status != BudgetLog.PENDING or self.budget_type != BudgetLog.BUDGET_IN:
            return

        self.flow_amount = new_amount
        self.save()

    @classmethod
    def is_cashout_limited(cls, customer_id):
        from flashsale.restpro.v2.views.xiaolumm import CashOutPolicyView

        limit_of_cash_out = CashOutPolicyView.DAILY_CASHOUT_TRIES
        budget_date = datetime.date.today()
        cnt = cls.objects.filter(customer_id=customer_id,
                                 budget_type=cls.BUDGET_OUT,
                                 budget_log_type=cls.BG_CASHOUT,
                                 budget_date=budget_date).exclude(status=cls.CANCELED).count()
        if limit_of_cash_out > cnt >= 0:
            return False
        return True

    @property
    def mama_id(self):
        from flashsale.xiaolumm.models import XiaoluMama
        c = Customer.objects.filter(id=self.customer_id).first()
        mama = XiaoluMama.objects.filter(openid=c.unionid).first()
        if mama:
            return mama.id
        return ''

