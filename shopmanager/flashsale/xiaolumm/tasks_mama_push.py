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
from django.db.models import Count, Sum

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

    to_url = "http://m.xiaolumeimei.com/sale/promotion/appdownload/"

    wp.push_mama_ordercarry(ordercarry, to_url)


@task
def task_weixin_push_update_app(app_visit):

    user_version = app_visit.get_user_version()
    latest_version = app_visit.get_latest_version()
    device_type = app_visit.device_type
    device = ''

    if device_type == app_visit.DEVICE_ANDROID:
        device = 'Android'
    if device_type == app_visit.DEVICE_IOS:
        device = 'IOS'

    if user_version == latest_version:
        # already latest, no need to push udpate reminder
        return

    from shopapp.weixin.weixin_push import WeixinPush
    wp = WeixinPush()

    mama_id = app_visit.mama_id
    to_url = "http://m.xiaolumeimei.com/sale/promotion/appdownload/"

    wp.push_mama_update_app(mama_id, user_version, latest_version, to_url, device=device)


@task
def task_weixin_push_invite_trial(referal_mama_id, potential_mama_id):
    from flashsale.xiaolumm.models import PotentialMama, ReferalRelationship, AwardCarry

    res = PotentialMama.objects.filter(referal_mama=referal_mama_id).values('is_full_member').annotate(n=Count('is_full_member'))
    trial_num,convert_num = 0,0
    for entry in res:
        if entry['is_full_member'] == True:
            convert_num = entry['n']
        if entry['is_full_member'] == False:
            trial_num = entry['n']
    invite_num = trial_num + convert_num

    if invite_num < 2:
        target_num = 2
        award_num = 5
    elif invite_num < 5:
        target_num = 5
        award_num = 10
    elif invite_num < 10:
        target_num = 10
        award_num = 15
    else:
        target_num = (invite_num / 5 + 1)* 5
        award_num = 10

    # 距离下一步推荐1元妈妈奖金人数
    diff_num = target_num - invite_num

    # 一元邀请奖金＋推荐完成新手任务奖金
    ac = AwardCarry.objects.filter(mama_id=referal_mama_id,carry_type__gte=6,carry_type__lte=7).aggregate(n=Sum('carry_num'))
    award_sum = ac['n'] or 0
    award_sum = award_sum * 0.01

    # 当前妈妈目前推荐正式妈妈可获奖金
    from flashsale.xiaolumm import utils
    rr_cnt = ReferalRelationship.objects.filter(referal_from_mama_id=referal_mama_id).count()
    rr_cnt += 1
    carry_num = utils.get_award_carry_num(rr_cnt, XiaoluMama.FULL)
    carry_num = carry_num * 0.01

    from shopapp.weixin.weixin_push import WeixinPush
    wp = WeixinPush()

    wp.push_mama_invite_trial(referal_mama_id,potential_mama_id, diff_num,award_num,invite_num,award_sum,trial_num,carry_num)

@task
def task_app_push_ordercarry(ordercarry):
    from flashsale.push.app_push import AppPush
    AppPush.push_mama_ordercarry(ordercarry)
    # AppPush.push_mama_ordercarry_to_all(ordercarry)


@task
def task_push_new_mama_task(xlmm, current_task, params=None):
    """
    通知完成某新手任务，同时提醒下一个任务
    """
    from shopapp.weixin.weixin_push import WeixinPush
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask

    next_task = xlmm.get_next_new_mama_task()

    header = NewMamaTask.get_push_msg(current_task, params=params)[0]

    if next_task:
        footer = NewMamaTask.get_push_msg(next_task, params=params)[1]
        to_url = NewMamaTask.get_push_msg(next_task, params=params)[2]
    else:
        footer = u'\n恭喜你，完成所有新手任务。'
        to_url = ''

    if not params:
        params = {'task_name': NewMamaTask.get_task_desc(current_task)}
    else:
        params['task_name'] = NewMamaTask.get_task_desc(current_task)

    wxpush = WeixinPush()
    wxpush.push_new_mama_task(xlmm.id, header=header, footer=footer, to_url=to_url, params=params)


@task
def task_sms_push_mama(xlmm):
    """
    新加入一元妈妈，发送短信引导关注小鹿美美
    """
    from shopapp.smsmgr.sms_push import SMSPush

    customer = xlmm.get_customer()
    sms = SMSPush()
    sms.push_mama_subscribe_weixin(customer)
