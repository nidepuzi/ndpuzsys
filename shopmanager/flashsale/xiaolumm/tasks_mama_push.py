# coding=utf-8
"""
代理相关的推送信息
"""
import datetime
from celery.task import task
from flashsale.xiaolumm.models import XiaoluMama, NinePicAdver
from flashsale.push import push_mama
from flashsale.xiaolumm.util_emoji import gen_emoji, match_emoji
from shopapp.weixin.models import WeixinUnionID


@task
def task_push_ninpic_remind(ninpic):
    """
    当有九张图更新的时候推送
    因为考虑到一天有很多的九张图推送，暂定一天值推送第一次九张图
    """
    title = ninpic.title.strip() if ninpic.title else None
    if not title:   # 如果标题为空　则　return
        return
    emoji_message = gen_emoji(title)
    message = match_emoji(emoji_message)
    ninpic.is_pushed = True
    ninpic.save()
    push_mama.push_msg_to_topic_mama(message)


@task
def task_push_ninpic_peroid():
    """　
    定时检查任务 自动执行推送
    1. 检索出当前时间之前15分钟没有执行推送记录的九张图上新记录　注意一定是１５分钟**之前**的记录否则导致推送了但是接口中并没有提供给客户端
    2. 推送执行过后要将九张图记录中的推送字段修改成推送过
    """
    # 2016-4-16 增加定时执行处理(默认每15分钟执行一次)
    now = datetime.datetime.now()  # 执行时间
    fifth_minute_ago = now - datetime.timedelta(minutes=15)  # 15分钟之前的时间
    ninpics = NinePicAdver.objects.filter(start_time__gte=fifth_minute_ago, start_time__lt=now, is_pushed=False)
    if ninpics.exists():
        ninpic = ninpics[0]
        task_push_ninpic_remind(ninpic)


@task
def task_push_mama_cashout_msg(envelop):
    """ 代理提现成功推送 """
    recipient = envelop.recipient
    weixin_records = WeixinUnionID.objects.filter(openid=recipient)
    if weixin_records.exists():
        unionid = weixin_records[0].unionid
        mamas = XiaoluMama.objects.filter(openid=unionid)
        map(push_mama.push_msg_to_mama(None), mamas)


@task
def task_weixin_push_awardcarry(awardcarry):
    from shopapp.weixin.weixin_push import WeixinPush
    wp = WeixinPush()

    from flashsale.xiaolumm import util_description
    courage_remarks = util_description.get_awardcarry_courage_remarks(awardcarry.carry_type)

    urls = ["http://m.xiaolumeimei.com", "http://m.xiaolumeimei.com/sale/promotion/appdownload/"]
    import random
    idx = int(random.random() * 2)

    if idx == 1:
        courage_remarks += u"更新最新版App查看奖金 >>"
    to_url = urls[idx]

    wp.push_mama_award(awardcarry, courage_remarks, to_url)


@task
def task_weixin_push_ordercarry(ordercarry):
    from shopapp.weixin.weixin_push import WeixinPush
    wp = WeixinPush()

    remarks = u"来自好友%s，快打开App看看她买了啥～" % ordercarry.contributor_nick
    to_url = "http://m.xiaolumeimei.com/sale/promotion/appdownload/"

    wp.push_mama_ordercarry(ordercarry, remarks, to_url)


@task
def task_weixin_push_update_app(app_visit):

    user_version = app_visit.get_user_version()
    latest_version = app_visit.get_latest_version()

    if user_version == latest_version:
        # already latest, no need to push udpate reminder
        return

    from shopapp.weixin.weixin_push import WeixinPush
    wp = WeixinPush()

    mama_id = app_visit.mama_id
    remarks = u"新版更快更流畅，请打开App检查更新，或直接点击下载更新！"
    to_url = "http://m.xiaolumeimei.com/sale/promotion/appdownload/"

    wp.push_mama_update_app(mama_id, user_version, latest_version, remarks, to_url)


@task
def task_app_push_ordercarry(ordercarry):
    from flashsale.push.app_push import AppPush
    AppPush.push_mama_ordercarry(ordercarry)
