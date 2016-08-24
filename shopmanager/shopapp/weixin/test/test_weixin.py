# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
# from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.weixin_push import WeixinPush
from flashsale.pay.models.trade import SaleTrade, SaleOrder
from flashsale.pay.models.refund import SaleRefund
from flashsale.xiaolumm.models.models_fortune import OrderCarry, AwardCarry


def test_main():
    ordercarry = OrderCarry.objects.get(id=10)
    push = WeixinPush()
    remarks = u"来自好友%s，快打开App看看她买了啥～" % ordercarry.contributor_nick
    to_url = "http://m.xiaolumeimei.com/sale/promotion/appdownload/"
    # push.push_mama_ordercarry(ordercarry, remarks, to_url)
    mama_id = 1
    user_version = '1.1'
    latest_version = '1.2'
    # push.push_mama_update_app(mama_id, user_version, latest_version, remarks, to_url)
    # saletrade = SaleTrade.objects.get(id=1)
    # push.push_trade_pay_notify(saletrade)
    # push.push_deliver_notify(saletrade)
    # salerefund = SaleRefund.objects.get(id=11)
    # push.push_refund_notify(salerefund)
    awardcarry = AwardCarry.objects.get(id=1)
    courage_remarks = 'remark'
    to_url = ''
    push.push_mama_award(awardcarry, courage_remarks, to_url)


def test_push_new_mama_task():
    from flashsale.xiaolumm.tasks_mama_push import task_push_new_mama_task
    from flashsale.xiaolumm.models.models import XiaoluMama
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask

    xlmm = XiaoluMama.objects.get(id=1)
    task_push_new_mama_task(xlmm, NewMamaTask.TASK_FIRST_FANS)


if __name__ == '__main__':
    import django
    django.setup()

    test_push_new_mama_task()
