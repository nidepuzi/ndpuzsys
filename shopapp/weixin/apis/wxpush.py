# coding: utf8
from __future__ import absolute_import, unicode_literals

# encoding=utf8
import json
import random
import logging
import datetime
from django.conf import settings

from flashsale.coupon.models import CouponTransferRecord
from flashsale.xiaolumm.models import XiaoluMama, WeixinPushEvent
from flashsale.pay.models.teambuy import TeamBuyDetail
from flashsale.pay.models.trade import SaleTrade
from ..apis.wxpubsdk import WeiXinAPI
from shopapp.weixin.models import (
    WeixinFans,
    WeixinTplMsg,
)
from shopapp.weixin import utils
from shopapp.smsmgr.sms_push import SMSPush


logger = logging.getLogger(__name__)


class WeixinPush(object):

    def __init__(self):
        self.mm_api = WeiXinAPI()
        if settings.WEIXIN_PUSH_SWITCH:
            self.mm_api.setAccountId(appKey=settings.WX_PUB_APPID)
            self.temai_api = WeiXinAPI()
            self.temai_api.setAccountId(appKey=settings.WEIXIN_APPID)

    def need_sms_push(self, customer):
        """
        如果两个公众账号（小鹿美美，小鹿美美特卖）都没关注，需要发短信
        """
        if not (customer and customer.mobile):
            return False

        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WX_PUB_APPID)

        if not temai_openid and not mm_openid:
            return True
        else:
            return False

    def push(self, customer, template_ids, template_data, to_url):

        if not settings.WEIXIN_PUSH_SWITCH:
            return

        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WX_PUB_APPID)

        # mm_openid = 'our5huD8xO6QY-lJc1DTrqRut3us'  # bo.zhang
        # mm_openid = 'our5huPpwbdmUz4pFHKL0DW5Hm34'  # jie.lin
        # temai_openid = None

        resp = None
        if mm_openid:
            template_id = template_ids.get('meimei')
            if template_id:
                resp = self.mm_api.sendTemplate(mm_openid, template_id, to_url, template_data)

        if temai_openid and not resp:
            template_id = template_ids.get('temai')
            if template_id:
                resp = self.temai_api.sendTemplate(temai_openid, template_id, to_url, template_data)

        if resp:
            logger.info({
                'action': 'push.weixinpush',
                'customer': customer.id,
                'openid': mm_openid or temai_openid,
                'template_id': json.dumps(template_ids),
                'to_url': to_url,
            })

        return resp

    def push_trade_pay_notify(self, saletrade):
        """
        {{first.DATA}}

        支付金额：{{orderMoneySum.DATA}}
        商品信息：{{orderProductName.DATA}}
        {{Remark.DATA}}
        """
        customer = saletrade.order_buyer

        template_ids = {
            'meimei': 'K3R9wpw_yC2aXEW1PP6586l9UhMjXMwn_-Is4xcgjuA',
            'temai': 'zFO-Dw936B9TwsJM4BD2Ih3zu3ygtQ_D_QXuNja6J6w'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        # 购买小鹿全球精品会员注册礼包
        is_boutique_register_product = False
        saleorders = saletrade.sale_orders.all()
        for order in saleorders:
            model_id = order.item_product.model_id
            if model_id == 25514:
                is_boutique_register_product = True
                break

        if is_boutique_register_product:
            footer = u'恭喜你开通小鹿精品代理！活动期间，推荐新代理奖励30元！请点击【详情】查看新手教程如何赚钱！'
            to_url = 'http://m.xiaolumeimei.com/mama_shop/html/intro_march.html'
        else:
            footer = template.footer.decode('string_escape')
            to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id

        template_data = {
            'first': {
                'value': template.header.format(customer.nick).decode('string_escape'),
                'color': '#000000',
            },
            'orderMoneySum': {
                'value': u'%s元' % saletrade.total_fee,
                'color': '#c0392b',
            },
            'orderProductName': {
                'value': saletrade.order_title,
                'color': '#c0392b',
            },
            'Remark': {
                'value': footer,
                'color': '#000000',
            },
        }
        return self.push(customer, template_ids, template_data, to_url)

    def push_deliver_notify(self, saletrade):
        """
        {{first.DATA}}

        订单金额：{{orderProductPrice.DATA}}
        商品详情：{{orderProductName.DATA}}
        收货信息：{{orderAddress.DATA}}
        订单编号：{{orderName.DATA}}
        {{remark.DATA}}
        """
        customer = saletrade.order_buyer
        order_address = '%s %s%s%s%s %s' % (
            saletrade.receiver_name,
            saletrade.receiver_state,
            saletrade.receiver_city,
            saletrade.receiver_district,
            saletrade.receiver_address,
            saletrade.receiver_mobile,
        )
        template_ids = {
            'meimei': 'ioBWcEsY40yg3NAQPnzE4LxfuHFFS20JnnAlVr96LXs',
            'temai': 'vVEY-AOiyiTEVF5AzUupI-H9WeG0tXA3YMYTn8l35VI'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(customer.nick).decode('string_escape'),
                'color': '#000000',
            },
            'orderProductPrice': {
                'value': u'%s元' % saletrade.total_fee,
                'color': '#c0392b',
            },
            'orderProductName': {
                'value': saletrade.order_title,
                'color': '#c0392b',
            },
            'orderAddress': {
                'value': order_address,
                'color': '#c0392b',
            },
            'orderName': {
                'value': saletrade.tid,
                'color': '#c0392b',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id
        return self.push(customer, template_ids, template_data, to_url)

    def push_refund_notify(self, salerefund, event_type):
        """
        {{first.DATA}}

        退款原因：{{reason.DATA}}
        退款金额：{{refund.DATA}}
        {{remark.DATA}}
        """
        customer = salerefund.customer
        template_ids = {
            'meimei': 'S9cIRfdDTM9yKeMTOj-HH5FPw79OofsfK6G4VRbKYQQ',
            'temai': '4TlQaNHO8MtVef33iCcPvxhRYS8Q1Nr3j_A9S-BtbLo'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        uni_key = '{customer_id}-{date}-salerefund-{salerefund}-{salerefund_status}'.format(**{
            'customer_id': customer.id,
            'date': datetime.datetime.now().date().strftime('%Y%m%d'),
            'salerefund': salerefund.id,
            'salerefund_status': salerefund.status
        })
        postage_coupon_info = u'附加信息: '
        if (salerefund.coupon_num + salerefund.postage_num) == 0:
            postage_coupon_info = u''
        else:
            if salerefund.postage_num > 0:
                postage_coupon_info += u'补邮费:￥%s  ' % str(salerefund.postage_num / 100.0)
            if salerefund.coupon_num > 0:
                postage_coupon_info += u'现金券:￥%s' % str(salerefund.coupon_num / 100.0)
        template_data = {
            'first': {
                'value': template.header.format(customer.nick,
                                                salerefund.title,
                                                salerefund.get_weixin_push_content(event_type)).decode('string_escape'),
                'color': '#000000',
            },
            'reason': {
                'value': u'%s' % salerefund.reason,
                'color': '#c0392b',
            },
            'refund': {
                'value': u'¥%.2f' % salerefund.refund_fee,
                'color': '#c0392b',
            },
            'remark': {
                'value': template.footer.format(postage_coupon_info).decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/refunds/details/%s' % salerefund.id
        try:
            event = WeixinPushEvent(customer_id=customer.id,
                                    uni_key=uni_key,
                                    tid=template.id,
                                    event_type=event_type,
                                    params=template_data,
                                    to_url=to_url)
            event.save()
        except:
            pass
        # return self.push(customer, template_ids, template_data, to_url)

    def push_mama_award(self, awardcarry, courage_remarks, to_url):
        """
        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        奖励金额：{{keyword2.DATA}}
        时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        customer = utils.get_mama_customer(awardcarry.mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            money = u'¥%.2f' % awardcarry.carry_num_display()
            sms.push_mama_ordercarry(customer, money=money)
            return

        template_ids = {
            'meimei': 'K2RVQnhIh6psYkGrkjLclLWmNXQ-hqoc-yumdsLuqC4',
            'temai': 'ATPs2YP1ynKfgtXRl1fhhZ2Kne3AmDmU8Rghax31edg'
        }
        template_data = {
            'first': {
                'value': u'报！公主殿下, 您的小鹿美美App奖金又来啦！',
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s' % awardcarry.carry_type_name(),
                'color': '#000000',
            },
            'keyword2': {
                'value': u'¥%.2f' % awardcarry.carry_num_display(),
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % awardcarry.created.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'remark': {
                'value': courage_remarks,
                'color': '#F87217',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_invite_award(self, mama, buy_customer, amount, level_1_customer=None):
        """
        购买小鹿全球精品会员注册礼包,给推荐人发推送

        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        奖励金额：{{keyword2.DATA}}
        时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """
        customer = utils.get_mama_customer(mama.id)
        now = datetime.datetime.now()

        if level_1_customer:
            first = u'恭喜你团队{}增加一名新成员{}！'.format(level_1_customer.nick, buy_customer.nick)
        else:
            first = u'恭喜你团队增加一名成员{}, 请邀请你朋友加入到团队群！'.format(buy_customer.nick)

        if type(amount) == str or type(amount) == unicode:
            amount = u'%s' % amount
        else:
            amount = u'¥%.2f' % amount,

        template_ids = {
            'meimei': 'K2RVQnhIh6psYkGrkjLclLWmNXQ-hqoc-yumdsLuqC4',
            'temai': 'ATPs2YP1ynKfgtXRl1fhhZ2Kne3AmDmU8Rghax31edg'
        }
        template_data = {
            'first': {
                'value': first,
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'推荐新人',
                'color': '#000000',
            },
            'keyword2': {
                'value': amount,
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % now.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'remark': {
                'value': u'',
                'color': '#F87217',
            },
        }
        to_url = 'https://m.xiaolumeimei.com'

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_ordercarry(self, ordercarry, to_url):
        """
        {{first.DATA}}

        提交时间：{{tradeDateTime.DATA}}
        订单类型：{{orderType.DATA}}
        客户信息：{{customerInfo.DATA}}
        {{orderItemName.DATA}}：{{orderItemData.DATA}}
        {{remark.DATA}}
        """
        # CARRY_TYPES = ((1, u'微商城订单'), (2, u'App订单额外+10%'), (3, u'下属订单+20%'),)
        order_type = ""
        if ordercarry.carry_type == 1:
            order_type = u'微商城订单'
        if ordercarry.carry_type == 2:
            order_type = u'App订单（佣金更高哦！）'
        if ordercarry.carry_type == 3:
            order_type = u'下属订单'

        customer = utils.get_mama_customer(ordercarry.mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            money = u'¥%.2f' % ordercarry.carry_num_display()
            sms.push_mama_ordercarry(customer, money=money)
            return

        template_ids = {
            'meimei': 'eBAuTQQxeGw9NFmheYd8Fc5X7CQbMKpfUSmqxnJOyEc',
            'temai': 'IDXvfqC9j_Y1NhVmtRdBcc6W7MNTNCiLdGTrikgdHoJ3E'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#F87217',
            },
            'tradeDateTime': {
                'value': ordercarry.created.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'orderType': {
                'value': order_type,
                'color': '#000000',
            },
            'customerInfo': {
                'value': ordercarry.contributor_nick,
                'color': '#000000',
            },
            'orderItemName':{
                'value': u'订单佣金',
                'color': '#ff0000',
            },
            'orderItemData':{
                'value': '¥%.2f' % ordercarry.carry_num_display(),
                'color': '#ff0000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#F87217',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_pintuan_success(self, teambuy, customer):
        """
        拼团成功通知

        {{first.DATA}}
        商品名称：{{keyword1.DATA}}
        团长：{{keyword2.DATA}}
        成团人数：{{keyword3.DATA}}
        {{remark.DATA}}
        """
        mama = customer.get_xiaolumm()
        mama_id = mama.id if mama else 0

        template_id = 'ZlEFblgBFQqCSabHyr0MrSS6nREGxQHKjEMnrgs3w5Q'
        template = WeixinTplMsg.objects.filter(wx_template_id=template_id, status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s' % teambuy.sku.product.name,
                'color': '#000000',
            },
            'keyword2': {
                'value': u'%s' % teambuy.get_creator().nick,
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % teambuy.limit_person_num,
                'color': '#000000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#F87217',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/order/spell/group/{teambuy_id}?mm_linkid={mama_id}&from_page=wx_push'.format(**{
            'teambuy_id': teambuy.id,
            'mama_id': teambuy.share_xlmm_id
        })

        uni_key = 'pintuan_success-{teambuy_id}-{customer_id}'.format(**{
            'teambuy_id': teambuy.id,
            'customer_id': customer.id,
        })
        event_type = WeixinPushEvent.PINTUAN_SUCCESS

        event = WeixinPushEvent(customer_id=customer.id, mama_id=mama_id, uni_key=uni_key, tid=template.id,
                                event_type=event_type, params=template_data, to_url=to_url)
        event.save()

    def push_pintuan_fail(self, teambuy, customer):
        """
        拼团失败通知

        {{first.DATA}}
        拼团商品：{{keyword1.DATA}}
        商品金额：{{keyword2.DATA}}
        退款金额：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        mama = customer.get_xiaolumm()
        mama_id = mama.id if mama else 0

        template_id = 'wUOE2gHR9DdCcmtXXlWeSGHngl30i3bwZjMS7ZaVq7E'
        template = WeixinTplMsg.objects.filter(wx_template_id=template_id, status=True).first()

        detail = TeamBuyDetail.objects.filter(teambuy_id=teambuy.id, customer_id=customer.id).first()
        trade = SaleTrade.objects.get(tid=detail.tid)

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s' % teambuy.sku.product.name,
                'color': '#000000',
            },
            'keyword2': {
                'value': u'%.2f' % trade.total_fee,
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%.2f' % trade.total_fee,
                'color': '#000000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#F87217',
            },
        }

        to_url = 'http://m.xiaolumeimei.com/mall/order/spell/group/{teambuy_id}?mm_linkid={mama_id}&from_page=wx_push'.format(**{
            'teambuy_id': teambuy.id,
            'mama_id': teambuy.share_xlmm_id
        })

        uni_key = 'pintuan_fail-{teambuy_id}-{customer_id}'.format(**{
            'teambuy_id': teambuy.id,
            'customer_id': customer.id,
        })

        event_type = WeixinPushEvent.PINTUAN_FAIL
        event = WeixinPushEvent(customer_id=customer.id, mama_id=mama_id, uni_key=uni_key, tid=template.id,
                                event_type=event_type, params=template_data, to_url=to_url)
        event.save()

    def push_pintuan_need_more_people(self, teambuy, customer):
        """
        参团人数不足提醒

        {{first.DATA}}
        团购商品：{{keyword1.DATA}}
        剩余拼团时间：{{keyword2.DATA}}
        剩余拼团人数：{{keyword3.DATA}}
        {{remark.DATA}}
        """
        mama = customer.get_xiaolumm()
        mama_id = mama.id if mama else 0

        template_id = 'V14lbfObhpoyEltUUnk-pxzpow66kOO7CeKC6hIawGM'
        template = WeixinTplMsg.objects.filter(wx_template_id=template_id, status=True).first()

        if teambuy.status != 0:  # 不是开团状态
            return

        remain_person_num = teambuy.limit_person_num - TeamBuyDetail.objects.filter(teambuy_id=teambuy.id).count()
        remain_hour = (teambuy.limit_time - datetime.datetime.now()).seconds / 3600

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s' % teambuy.sku.product.name,
                'color': '#000000',
            },
            'keyword2': {
                'value': u'%s小时' % remain_hour,
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s人' % remain_person_num,
                'color': '#000000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#F87217',
            },
        }

        to_url = 'http://m.xiaolumeimei.com/mall/order/spell/group/{teambuy_id}?mm_linkid={mama_id}&from_page=wx_push'.format(**{
            'teambuy_id': teambuy.id,
            'mama_id': teambuy.share_xlmm_id
        })

        uni_key = 'pintuan_need_more_people-{teambuy_id}-{customer_id}'.format(**{
            'teambuy_id': teambuy.id,
            'customer_id': customer.id,
        })
        event_type = WeixinPushEvent.PINTUAN_NEED_MORE_PEOPLE
        event = WeixinPushEvent(customer_id=customer.id, mama_id=mama_id, uni_key=uni_key, tid=template.id,
                                event_type=event_type, params=template_data, to_url=to_url)
        event.save()

    def push_mama_clickcarry(self, clickcarry, fake=False, advertising=False):
        """
        推送点击收益

        ---
        收益通知

        {{first.DATA}}
        收益类型：{{keyword1.DATA}}
        收益金额：{{keyword2.DATA}}
        收益时间：{{keyword3.DATA}}
        剩余金额：{{keyword4.DATA}}
        {{remark.DATA}}


        """
        mama_id = clickcarry.mama_id
        customer = utils.get_mama_customer(mama_id)
        try:
            userbudget = customer.userbudget
        except Exception:
            return

        if fake:
            event_type = WeixinPushEvent.FAKE_CLICK_CARRY
        else:
            event_type = WeixinPushEvent.CLICK_CARRY

        template_id = 'n9kUgavs_10Dz8RbIgY2F9r6rNdlNw3I6D1KLft0_2I'
        template = WeixinTplMsg.objects.filter(wx_template_id=template_id, status=True).first()

        if not template:
            return

        today = datetime.datetime.now().date()
        last_event = WeixinPushEvent.objects.filter(
            mama_id=mama_id, date_field=today, event_type=event_type).order_by('-created').first()

        if last_event:
            if last_event.uni_key.startswith('fake'):
                _, _, _, _, last_click_num, last_total_value = last_event.uni_key.split('-')
            else:
                _, _, _, last_click_num, last_total_value = last_event.uni_key.split('-')
            carry_count = clickcarry.click_num - int(last_click_num)
            carry_money = clickcarry.total_value - int(last_total_value)

            # 一段时间内不许重复推送
            delta = datetime.datetime.now() - last_event.created
            if delta.seconds < 60*60*3 and clickcarry.click_num < clickcarry.init_click_limit:
                return
            if carry_count < 0 or carry_money < 0:
                return 
        else:
            carry_count = clickcarry.click_num
            carry_money = clickcarry.total_value

        uni_key = '{mama_id}-{date}-clickcarry-{click_num}-{total_value}'.format(**{
            'mama_id': mama_id,
            'date': clickcarry.date_field.strftime('%Y%m%d'),
            'click_num': clickcarry.click_num,
            'total_value': clickcarry.total_value
        })
        if fake:
            uni_key = 'fake-' + uni_key

        header = template.header.format(carry_count).decode('string_escape')
        footer = template.footer.format('%.2f' % (clickcarry.total_value * 0.01)).decode('string_escape')
        to_url = 'http://m.xiaolumeimei.com/rest/v2/mama/redirect_stats_link?link_id=4'
        footer_color = '#F87217'

        # 模板消息底部替换为小广告
        if fake or advertising:
            from flashsale.pay.models.admanager import ADManager
            ads = ADManager.objects.filter(status=True)
            if ads.count() > 0:
                ad = random.choice(ads)
                footer = u'\n%s' % ad.title
                footer_color = '#ff0000'
                to_url = ad.url


        template_data = {
            'first': {
                'value': header,
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'点击收益',
                'color': '#000000',
            },
            'keyword2': {
                'value': u'%.2f元' % (carry_money * 0.01),
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % clickcarry.modified.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'keyword4': {
                'value': u'%.2f元（可提现）' % (userbudget.amount * 0.01),
                'color': '#000000',
            },
            'remark': {
                'value': footer,
                'color': footer_color,
            },
        }

        event = WeixinPushEvent(customer_id=customer.id, mama_id=mama_id, uni_key=uni_key, tid=template.id,
                                event_type=event_type, params=template_data, to_url=to_url)
        event.save()

    def push_mama_coupon_audit(self, coupon_record):
        """
        审核申请提醒

        {{first.DATA}}
        审核内容：{{keyword1.DATA}}
        客户名称：{{keyword2.DATA}}
        商品名称：{{keyword3.DATA}}
        申请金额：{{keyword4.DATA}}
        {{remark.DATA}}
        """
        from flashsale.coupon.models import CouponTemplate

        if coupon_record.transfer_type in [CouponTransferRecord.OUT_TRANSFER]:
            mama_id = coupon_record.coupon_from_mama_id
        elif coupon_record.transfer_type in [CouponTransferRecord.OUT_CASHOUT, CouponTransferRecord.IN_RETURN_COUPON]:
            mama_id = coupon_record.coupon_to_mama_id
        else:
            return

        customer = utils.get_mama_customer(mama_id)
        if not customer:
            return

        event_type = WeixinPushEvent.COUPON_TRANSFER_AUDIT
        template_id = 'GQqbrGtAmmKdUnknaaIEmW7DakgvQK6apfROTxzYkUs'
        template = WeixinTplMsg.objects.filter(wx_template_id=template_id, status=True).first()

        if not template:
            return

        today = datetime.datetime.now().date()
        uni_key = '{mama_id}-{date}-coupon_audit-{coupon_record_id}'.format(**{
            'mama_id': mama_id,
            'date': today.strftime('%Y%m%d'),
            'coupon_record_id': coupon_record.id
        })

        coupon_template = CouponTemplate.objects.filter(id=coupon_record.template_id).first()

        header = template.header.format().decode('string_escape')
        footer = template.footer.format().decode('string_escape')
        to_url = 'https://m.xiaolumeimei.com/rest/v1/users/weixin_login/?next=https://m.xiaolumeimei.com/tran_coupon/html/trancoupon.html'
        footer_color = '#F87217'

        template_data = {
            'first': {
                'value': header,
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'精品券申请',
                'color': '#000000',
            },
            'keyword2': {
                'value': u'%s' % coupon_record.to_mama_nick,
                'color': '#000000',
            },
            'keyword3': {
                'value': u'%s' % coupon_template.title,
                'color': '#000000',
            },
            'keyword4': {
                'value': u'%.2f元 x %s个' % (coupon_record.coupon_value, coupon_record.coupon_num),
                'color': '#000000',
            },
            'remark': {
                'value': footer,
                'color': footer_color,
            },
        }

        event = WeixinPushEvent(customer_id=customer.id, mama_id=mama_id, uni_key=uni_key, tid=template.id,
                                event_type=event_type, params=template_data, to_url=to_url)
        event.save()

    def push_mama_update_app(self, mama_id, user_version, latest_version, to_url, device=''):
        """
        {{first.DATA}}
        系统名称：{{keyword1.DATA}}
        运维状态：{{keyword2.DATA}}
        {{remark.DATA}}
        """
        customer = utils.get_mama_customer(mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            sms.push_mama_update_app(customer)
            return

        template_ids = {
            'meimei': 'l9QBpAojbpQmFIRmhSN4M-eQDzkw76yBpfrYcBoakK0',
            'temai': 'x_nPMjWKodG0V4w334I_u5LAFpoTH1fSqjAv5jPmA7Y'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#4CC417',
            },
            'keyword1': {
                'value': u'您的当前%s版本：%s' % (device, user_version),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': u'最新发布%s版本：%s' % (device, latest_version),
                'color': '#ff0000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#4CC417',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_invite_trial(self, referal_mama_id, potential_mama_id, diff_num, award_num,
                               invite_num, award_sum, trial_num, carry_num):
        """
        {{first.DATA}}
        姓名：{{keyword1.DATA}}
        手机：{{keyword2.DATA}}
        会员等级：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        referal_customer = utils.get_mama_customer(referal_mama_id)

        if not referal_customer:
            return

        potential_customer = utils.get_mama_customer(potential_mama_id)
        mobile_string = ''
        if potential_customer.mobile:
            mobile = potential_customer.mobile
            mobile_string = '%s****%s' % (mobile[0:3], mobile[7:])

        template_ids = {
            'meimei': 'tvns3YwYkRkkd2mycvxKsbRtuQl1spBHxtm9PLFIlFI',
            'temai': 'O6SYsBHUpYpk9UTUzmUrhybU7arHuFsz2shox0JOg1s'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(diff_num=diff_num, award_num=award_num).decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s (ID:%s)' % (potential_customer.nick, potential_mama_id),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': mobile_string,
                'color': '#4CC417',
            },
            'keyword3': {
                'value': u'15天体验试用',
                'color': '#4CC417',
            },
            'remark': {
                'value': template.footer.format(
                    invite_num=invite_num, award_sum=award_sum,
                    trial_num=trial_num, award_total=trial_num*carry_num).decode('string_escape'),
                'color': '#F87217',
            },
        }
        to_url = 'http://m.xiaolumeimei.com'
        return self.push(referal_customer, template_ids, template_data, to_url)

    def push_new_mama_task(self, mama_id, header='', footer='', to_url='', params=None):
        """
        任务完成通知

        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        任务类型：{{keyword2.DATA}}
        完成时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """
        customer = utils.get_mama_customer(mama_id)
        if not params:
            params = {}

        template_ids = {
            'meimei': 'Lvw0t5ttadeEzRV2tczPclzpPnLXGEQZZJVdWxHyS4g',
            'temai': 'frGeesnAWDCmn5CinuzVGb1VbS5610J8xjM-tgPV7XQ'
        }
        template_data = {
            'first': {
                'value': header,
                'color': '#4CC417',
            },
            'keyword1': {
                'value': params.get('task_name', ''),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': params.get('task_type', u'新手任务'),
                'color': '#4CC417',
            },
            'keyword3': {
                'value': (params.get('finish_time') or datetime.datetime.now()).strftime('%Y-%m-%d'),
                'color': '#4CC417',
            },
            'remark': {
                'value': footer,
                'color': '#4CC417',
            },
        }
        return self.push(customer, template_ids, template_data, to_url)

    push_mission_finish_task = push_new_mama_task

    def push_mission_state_task(self, mama_id, header='', footer='', to_url='', params=None):
        """
        新任务提醒

        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        奖励金额：{{keyword2.DATA}}
        截止时间：{{keyword3.DATA}}
        需求数量：{{keyword4.DATA}}
        任务简介：{{keyword5.DATA}}
        {{remark.DATA}}
        """
        customer = utils.get_mama_customer(mama_id)
        if not params:
            params = {}

        template_ids = {
            'meimei': '5dmrReey6YXG-eRuNWsfpK0xFL35xzk0UoJ43DJHwJ4',
            'temai': '98pFo0KBn5WFLecvFnC2Ve_atd9wNYXdBc5zO4jJO9g'
        }
        template_data = {
            'first': {
                'value': header,
                'color': '#4CC417',
            },
            'keyword1': {
                'value': params.get('task_name', ''),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': params.get('award_amount', u'不限额'),
                'color': '#4CC417',
            },
            'keyword3': {
                'value': params.get('deadline', ''),
                'color': '#4CC417',
            },
            'keyword4': {
                'value': params.get('target_state', ''),
                'color': '#4CC417',
            },
            'keyword5': {
                'value': params.get('description', ''),
                'color': '#4CC417',
            },
            'remark': {
                'value': footer,
                'color': '#4CC417',
            },
        }
        return self.push(customer, template_ids, template_data, to_url)

    def push_event(self, event_instance):
        customer = event_instance.get_effect_customer()
        if not customer:
            return

        tid = event_instance.tid
        template = WeixinTplMsg.objects.filter(id=tid, status=True).first()
        if not template:
            return

        template_ids = template.template_ids
        template_data = event_instance.params

        header = template_data.get('first')
        if not header:
            template_data.update({'first': {'value': template.header.decode('string_escape'), 'color':'#F87217'}})
        footer = template_data.get('remark')
        if not footer:
            template_data.update({'remark': {'value': template.footer.decode('string_escape'), 'color':'#F87217'}})
        to_url = event_instance.to_url
        if not to_url:
            from flashsale.promotion.apis.activity import get_effect_activities
            active_time = datetime.datetime.now() - datetime.timedelta(hours=6)
            activitys = get_effect_activities(active_time)
            entry = random.choice(activitys)
            login_url = 'http://m.xiaolumeimei.com/rest/v1/users/weixin_login/?next='
            redirect_url = '/rest/v2/mama/redirect_activity_entry?activity_id=%s' % entry.id
            to_url = login_url + redirect_url
            remark = template_data.get('remark')
            desc = ''
            if remark:
                desc = remark.get('value')

            desc += u'\n\n今日热门:\n［%s］%s' % (entry.title, entry.act_desc)
            template_data.update({'remark': {'value': desc, 'color':'#ff6633'}})

        return self.push(customer, template_ids, template_data, to_url)
