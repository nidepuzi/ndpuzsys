# -*- coding:utf-8 -*-
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save

from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.pay.models import Customer, BudgetLog
from flashsale.xiaolumm.models import XiaoluMama


class WeixinUnionID(BaseModel):
    openid = models.CharField(max_length=32, verbose_name=u'OPENID')
    app_key = models.CharField(max_length=24, verbose_name=u'APPKEY')
    unionid = models.CharField(max_length=32, verbose_name=u'UNIONID')

    class Meta:
        db_table = 'shop_weixin_unionid'
        unique_together = [('unionid', 'app_key')]
        index_together = [('openid', 'app_key')]
        app_label = 'weixin'
        verbose_name = u'微信用户授权ID'
        verbose_name_plural = u'微信用户授权ID列表'

    def __unicode__(self):
        return u'<%s>' % self.openid


class WeixinFans(models.Model):
    openid = models.CharField(max_length=32, verbose_name=u'OPENID')
    app_key = models.CharField(max_length=24, verbose_name=u'APPKEY')
    unionid = models.CharField(max_length=32, verbose_name=u'UNIONID')
    subscribe = models.BooleanField(default=False, verbose_name=u"订阅该号")
    subscribe_time = models.DateTimeField(blank=True, null=True, verbose_name=u"订阅时间")
    unsubscribe_time = models.DateTimeField(blank=True, null=True, verbose_name=u"取消订阅时间")
    extras = JSONCharMyField(max_length=512, default={'qrscene':'0'}, verbose_name=u'额外参数')

    class Meta:
        db_table = 'shop_weixin_fans'
        unique_together = [('unionid', 'app_key')]
        index_together = [('openid', 'app_key')]
        app_label = 'weixin'
        verbose_name = u'微信公众号粉丝'
        verbose_name_plural = u'微信公众号粉丝列表'

    @classmethod
    def get_openid_by_unionid(cls, unionid, app_key):
        """
        没关注也返回 None
        """
        fans = cls.objects.filter(unionid=unionid, app_key=app_key, subscribe=True).first()
        if fans:
            return fans.openid
        else:
            return None

    @classmethod
    def get_unionid_by_openid_and_appkey(cls, openid, app_key):
        fans = cls.objects.filter(openid=openid, app_key=app_key, subscribe=True).first()
        if fans:
            return fans.unionid
        return None

    def set_qrscene(self, qrscene, force_update=False):
        if not self.extras:
            self.extras = {}
        if not self.get_qrscene() or force_update:
            self.extras['qrscene'] = qrscene.strip()

    def get_qrscene(self):
        qrscene = self.extras.get('qrscene')
        if qrscene == '0' or qrscene == 0:
            return ''
        return qrscene


def weixinfans_update_xlmmfans(sender, instance, created, **kwargs):
    referal_from_mama_id = instance.extras.get('qrscene')
    if referal_from_mama_id and referal_from_mama_id.isdigit():
        referal_from_mama_id = int(referal_from_mama_id)
    else:
        return
    
    referal_to_unionid = instance.unionid

    from shopapp.weixin.tasks import task_weixinfans_update_xlmmfans
    task_weixinfans_update_xlmmfans.delay(referal_from_mama_id, referal_to_unionid)

post_save.connect(weixinfans_update_xlmmfans,
                  sender=WeixinFans, dispatch_uid='post_save_weixinfans_update_xlmmfans')

def weixinfans_create_budgetlogs(sender, instance, created, **kwargs):
    referal_from_mama_id = instance.extras.get('qrscene')
    if referal_from_mama_id and referal_from_mama_id.isdigit():
        referal_from_mama_id = int(referal_from_mama_id)
    referal_to_unionid = instance.unionid

    if referal_from_mama_id > 100:
        # 内部人员测试
        return
    
    customer = Customer.objects.filter(unionid=referal_to_unionid).first()
    from_mama = XiaoluMama.objects.filter(id=referal_from_mama_id).first()
    from_customer = Customer.objects.filter(unionid=from_mama.openid).first()

    from shopapp.weixin.tasks import task_weixinfans_create_budgetlog
    task_weixinfans_create_budgetlog.delay(customer.id, from_customer.id, BudgetLog.BG_SUBSCRIBE)
    task_weixinfans_create_budgetlog.delay(from_customer.id, customer.id, BudgetLog.BG_REFERAL_FANS)
    
post_save.connect(weixinfans_create_budgetlogs,
                  sender=WeixinFans, dispatch_uid='post_save_weixinfans_create_budgetlogs')


def weixinfans_xlmm_newtask(sender, instance, **kwargs):
    """
    检测新手任务：　关注公众号“小鹿美美”
    """
    from flashsale.xiaolumm.tasks_mama_push import task_push_new_mama_task
    from flashsale.xiaolumm.tasks_mama_fortune import task_subscribe_weixin_send_award
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
    from flashsale.pay.models.user import Customer

    fans = instance

    if not fans.subscribe:
        return

    if fans.app_key != settings.WXPAY_APPID:
        return

    customer = Customer.objects.filter(unionid=fans.unionid).first()

    if not customer:
        return

    xlmm = customer.getXiaolumm()

    if not xlmm:
        return

    # 取消关注，然后重新关注，不计入
    fans_record = WeixinFans.objects.filter(
        unionid=fans.unionid, app_key=settings.WXPAY_APPID).exists()

    if not fans_record:
        # 发５元奖励
        task_subscribe_weixin_send_award.delay(xlmm)
        # 通知完成任务：
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_SUBSCRIBE_WEIXIN)

pre_save.connect(weixinfans_xlmm_newtask,
                 sender=WeixinFans, dispatch_uid='pre_save_weixinfans_xlmm_newtask')


class WeixinTplMsg(models.Model):
    """
    """
    wx_template_id = models.CharField(max_length=255, verbose_name=u'微信模板ID')
    content = models.TextField(blank=True, null=True, verbose_name=u'模板内容')
    header = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'模板消息头部')
    footer = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'模板消息尾部')
    status = models.BooleanField(default=True, verbose_name=u"使用")

    class Meta:
        db_table = 'shop_weixin_template_msg'
        app_label = 'weixin'
        verbose_name = u'微信模板消息'
        verbose_name_plural = u'微信模板消息列表'


from core.weixin import signals


def fetch_weixin_userinfo(sender, appid, resp_data, *args, **kwargs):
    from .tasks import task_Update_Weixin_Userinfo
    openid = resp_data.get('openid')
    if not openid or not appid:
        return

        # 只对WEIXIN_APPID的公众号授权抓取用户信息
    if appid != settings.WEIXIN_APPID:
        return

    if resp_data.has_key('access_token'):
        task_Update_Weixin_Userinfo.delay(openid,
                                          accessToken=resp_data.get('access_token'))
    else:
        task_Update_Weixin_Userinfo.delay(openid, userinfo=resp_data)


signals.signal_weixin_snsauth_response.connect(fetch_weixin_userinfo)


class WeixinUserInfo(BaseModel):
    """
    We make sure every weixin user only have one record in this table.
    -- Zifei 2016-04-12
    """
    unionid = models.CharField(max_length=32, unique=True, verbose_name=u'UNIONID')
    nick = models.CharField(max_length=32, blank=True, verbose_name=u'昵称')
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'头像')

    class Meta:
        db_table = 'shop_weixin_userinfo'
        app_label = 'weixin'
        verbose_name = u'微信用户基本信息'
        verbose_name_plural = u'微信用户基本信息列表'

    def __unicode__(self):
        return u'<%s>' % self.nick


