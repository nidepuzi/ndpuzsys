# coding: utf-8
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

from .mipush import mipush_of_ios, mipush_of_android
from shopapp.weixin.apis import WeixinPush


@app.task(max_retries=3, default_retry_delay=5)
def subscribe(platform, regid, topic):
    mipush_instance = mipush_of_ios if platform == 'ios' else mipush_of_android
    mipush_instance.subscribe_by_regid(regid, topic)


@app.task(max_retries=3, default_retry_delay=5)
def unsubscribe(platform, regid, topic):
    mipush_instance = mipush_of_ios if platform == 'ios' else mipush_of_android
    mipush_instance.unsubscribe_by_regid(regid, topic)


@app.task(max_retries=3, default_retry_delay=30)
def task_push_trade_pay_notify(saletrade):
    weixin_push = WeixinPush()
    weixin_push.push_trade_pay_notify(saletrade)
