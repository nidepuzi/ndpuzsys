# -*- coding:utf-8 -*-
import datetime
import logging
import random

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel
from core.options import log_action, CHANGE
from .base import PayBaseModel
from .envelope import Envelop
from .. import constants
from .. import managers

logger = logging.getLogger(__name__)

class Register(PayBaseModel):
    MAX_VALID_COUNT = 6
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

    code_time = models.DateTimeField(blank=True, null=True, verbose_name=u'短信发送时间')
    mail_time = models.DateTimeField(blank=True, null=True, verbose_name=u'邮件发送时间')

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
        if self.code_time and (dt - self.code_time).days > 1:
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


class Customer(BaseModel):
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

    id = models.AutoField(primary_key=True, verbose_name=u'客户ID')
    user = models.OneToOneField(DjangoUser, verbose_name=u'原始用户')
    nick = models.CharField(max_length=32, blank=True, default=genCustomerNickname, verbose_name=u'昵称')
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'头像')
    mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'手机')
    email = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'邮箱')
    phone = models.CharField(max_length=18, blank=True, verbose_name=u'电话')

    openid = models.CharField(max_length=28, db_index=True, blank=True, verbose_name=u'微信ID')
    unionid = models.CharField(max_length=28, db_index=True, verbose_name=u'联合ID')

    status = models.IntegerField(choices=USER_STATUS_CHOICES, default=NORMAL, verbose_name=u'状态')

    objects = managers.CustomerManager()
    first_paytime = models.DateTimeField(null=True,blank=True,verbose_name=u'首次购买日期')
    #     latest_paytime  = models.DateTimeField(null=True,blank=True,verbose_name=u'最近购买日期')

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
    def getCustomerByUser(cls, user):

        customers = cls.objects.filter(user=user.id)
        if customers.count() > 0:
            return customers[0]
        return None

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
        if not openid and appkey == settings.WXPAY_APPID:
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
            WeixinUnionID.objects.get(app_key=settings.WXPAY_APPID, unionid=self.unionid)
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

# 2016-4-9 有登陆检查后注释不执行
# def triger_record_xlmm_fans(sender, instance, created, **kwargs):
#     """ 记录粉丝妈妈粉丝信息 """
#     from flashsale.pay.tasks import task_Record_Mama_Fans
#     task_Record_Mama_Fans.delay(instance, created)
#
# post_save.connect(triger_record_xlmm_fans, dispatch_uid='triger_record_xlmm_fans', sender=Customer)


# def release_coupon_for_register(sender, instance, created, **kwargs):
#     if created:
#         from flashsale.coupon.tasks import task_release_coupon_for_register
#         task_release_coupon_for_register.delay(instance)
#
# post_save.connect(release_coupon_for_register, dispatch_uid='release_coupon_for_register', sender=Customer)


def update_weixinuserinfo(sender, instance, created, **kwargs):
    if not instance.unionid:
        return
    from flashsale.pay.tasks import task_customer_update_weixinuserinfo
    task_customer_update_weixinuserinfo.delay(instance)

post_save.connect(update_weixinuserinfo, sender=Customer,
                  dispatch_uid='post_save_update_weixinuserinfo')


def sync_xlmm_fans_nick_thumbnail(sender, instance, created, **kwargs):
    from flashsale.pay.tasks import task_sync_xlmm_fans_nick_thumbnail
    task_sync_xlmm_fans_nick_thumbnail.delay(instance)

post_save.connect(sync_xlmm_fans_nick_thumbnail, sender=Customer,
                  dispatch_uid='post_save_sync_xlmm_fans_nick_thumbnail')


def sync_xlmm_mobile_by_customer(sender, instance, created, **kwargs):
    from flashsale.pay.tasks import task_sync_xlmm_mobile_by_customer
    task_sync_xlmm_mobile_by_customer.delay(instance)

post_save.connect(sync_xlmm_mobile_by_customer, sender=Customer,
                  dispatch_uid='post_save_sync_xlmm_mobile_by_customer')


class UserBudget(PayBaseModel):
    """ 特卖用户钱包 """

    class Meta:
        db_table = 'flashsale_userbudget'
        app_label = 'pay'
        verbose_name = u'特卖/用户钱包'
        verbose_name_plural = u'特卖/用户钱包列表'

    user = models.OneToOneField(Customer, verbose_name=u'原始用户')
    amount = models.IntegerField(default=0, verbose_name=u'账户余额(分)')
    total_income = models.IntegerField(default=0, verbose_name=u'总收入')
    total_expense = models.IntegerField(default=0, verbose_name=u'总支出')

    def __unicode__(self):
        return u'<%s,%s>' % (self.user, self.amount)

    @property
    def budget_cash(self):
        return self.amount / 100.0

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
            urows = UserBudget.objects.filter(
                user=self.user,
                amount__gte=payment
            ).update(amount=models.F('amount') - payment)
            if urows == 0:
                return False
            BudgetLog.objects.create(customer_id=self.user.id,
                                     referal_id=strade_id,
                                     flow_amount=payment,
                                     budget_log_type=BudgetLog.BG_CONSUM,
                                     budget_type=BudgetLog.BUDGET_OUT,
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

        #如果订单超时关闭又支付成功,则余额支付状态页需要改回
        if blog.status ==  BudgetLog.CANCELED:
            blog.status = BudgetLog.PENDING
        return blog.push_pending_to_confirm()


    def charge_cancel(self, strade_id):
        """ 支付取消 """
        blogs = BudgetLog.objects.filter(customer_id=self.user.id,
                                         referal_id=strade_id,
                                         budget_log_type=BudgetLog.BG_CONSUM)
        if blogs.exists():
            return blogs[0].cancel_and_return()

    def is_could_cashout(self):
        """ 设置普通用户钱包是否可以提现控制字段 """
        return constants.IS_USERBUDGET_COULD_CASHOUT

    def action_budget_cashout(self, cash_out_amount):
        """
        用户钱包提现
        cash_out_amount　整型　以分为单位
        """
        from shopapp.weixin.models import WeixinUnionID
        if not isinstance(cash_out_amount, int):  # 参数类型错误(如果不是整型)
            return 3, '参数错误'
        # 如果提现金额小于0　code 1
        if cash_out_amount <= 0:
            return 1, '提现金额小于0'
        # 如果提现金额大于当前用户钱包的金额 code 2
        elif cash_out_amount > self.amount:
            return 2, '提现金额大于账户金额'
        # 提现操作
        else:
            # 提现前金额
            try:
                if not self.user.unionid:
                    return 5, '请扫描二维码'
                wx_union = WeixinUnionID.objects.get(app_key=settings.WXPAY_APPID, unionid=self.user.unionid)
            except WeixinUnionID.DoesNotExist:
                return 4, '请扫描二维码'  # 用户没有公众号提现账户

            # 发放公众号红包
            recipient = wx_union.openid  # 接收人的openid
            body = constants.ENVELOP_BODY  # 红包祝福语
            description = constants.ENVELOP_CASHOUT_DESC.format(self.user.id,
                                                                self.amount)  # 备注信息 用户id, 提现前金额
            # 创建钱包提现记录
            budgelog = BudgetLog.objects.create(customer_id=self.user.id,
                                                flow_amount=cash_out_amount,
                                                budget_type=BudgetLog.BUDGET_OUT,
                                                budget_log_type=BudgetLog.BG_CASHOUT,
                                                budget_date=datetime.date.today(),
                                                status=BudgetLog.CONFIRMED)

            Envelop.objects.create(amount=cash_out_amount,
                                   platform=Envelop.WXPUB,
                                   recipient=recipient,
                                   subject=Envelop.XLAPP_CASHOUT,
                                   body=body,
                                   receiver=self.user.mobile,
                                   description=description,
                                   referal_id=budgelog.id)
            log_action(self.user.user.id, self, CHANGE, u'用户提现')
        return 0, '提现成功'


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
    BG_CONSUM = 'consum'
    BG_CASHOUT = 'cashout'
    BG_MAMA_CASH = 'mmcash'

    BUDGET_LOG_CHOICES = (
        (BG_ENVELOPE, u'红包'),
        (BG_REFUND, u'退款'),
        (BG_CONSUM, u'消费'),
        (BG_CASHOUT, u'提现'),
        (BG_MAMA_CASH, u'代理提现至余额'),
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
    budget_type = models.IntegerField(choices=BUDGET_CHOICES, db_index=True, null=False, verbose_name=u"收支类型")
    budget_log_type = models.CharField(max_length=8, choices=BUDGET_LOG_CHOICES, db_index=True, null=False,
                                       verbose_name=u"记录类型")
    budget_date = models.DateField(default=datetime.date.today, verbose_name=u'业务日期')
    referal_id = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'引用id')
    status = models.IntegerField(choices=STATUS_CHOICES, db_index=True, default=CONFIRMED, verbose_name=u'状态')

    def __unicode__(self):
        return u'<%s,%s>' % (self.customer_id, self.flow_amount)

    def get_flow_amount_display(self):
        """ 返回金额　"""
        return self.flow_amount / 100.0

    def push_pending_to_confirm(self):
        """ 确认待确认钱包收支记录 """
        if self.status == BudgetLog.PENDING:
            self.status = BudgetLog.CONFIRMED
            self.save()
            return True
        return False

    def log_desc(self):
        """ 预留记录的描述字段 """
        return '您通过{0}{1}{2}元.'.format(self.get_budget_log_type_display(),
                                       self.get_budget_type_display(),
                                       self.flow_amount * 0.01)

    def cancel_and_return(self):
        """ 将待确认或已确认的支出取消并返还小鹿账户 """
        if self.status not in (self.CONFIRMED, self.PENDING):
            return False
        if self.budget_type == self.BUDGET_OUT:
            self.status = self.CANCELED
            self.save()
            return True


def budgetlog_update_userbudget(sender, instance, created, **kwargs):

    logger.warning('budgetlog update:%s, %s, %s, %s'%
                   (instance.customer_id, instance.flow_amount, instance.referal_id, instance.status))
    from flashsale.pay.tasks import task_budgetlog_update_userbudget
    task_budgetlog_update_userbudget(instance)


post_save.connect(budgetlog_update_userbudget, sender=BudgetLog,
                  dispatch_uid='post_save_budgetlog_update_userbudget')
