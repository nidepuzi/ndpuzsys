# encoding=utf8
import json
import logging
from datetime import datetime
from django.conf import settings
from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.models_base import (
    WeixinFans,
    WeixinTplMsg,
)
from shopapp.weixin import utils
from shopapp.smsmgr.sms_push import SMSPush


logger = logging.getLogger(__name__)


class WeixinPush(object):

    def __init__(self):
        self.mm_api = WeiXinAPI()
        self.mm_api.setAccountId(appKey=settings.WXPAY_APPID)
        self.temai_api = WeiXinAPI()
        self.temai_api.setAccountId(appKey=settings.WEIXIN_APPID)

    def need_sms_push(self, customer):
        """
        如果两个公众账号（小鹿美美，小鹿美美特卖）都没关注，需要发短信
        """
        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)

        if not temai_openid and not mm_openid:
            return True
        else:
            return False

    def push(self, customer, template_ids, template_data, to_url):

        if not settings.PUSH_SWITCH:
            return

        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)

        if mm_openid:
            template_id = template_ids.get('meimei')
            resp = self.mm_api.sendTemplate(mm_openid, template_id, to_url, template_data)
        elif temai_openid:
            template_id = template_ids.get('temai')
            resp = self.temai_api.sendTemplate(temai_openid, template_id, to_url, template_data)
        else:
            resp = None

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
                'value': template.footer.decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id
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

    def push_refund_notify(self, salerefund):
        """
        {{first.DATA}}

        退款原因：{{reason.DATA}}
        退款金额：{{refund.DATA}}
        {{remark.DATA}}
        """
        customer = salerefund.get_refund_customer()
        template_ids = {
            'meimei': 'S9cIRfdDTM9yKeMTOj-HH5FPw79OofsfK6G4VRbKYQQ',
            'temai': '4TlQaNHO8MtVef33iCcPvxhRYS8Q1Nr3j_A9S-BtbLo'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(customer.nick, salerefund.title).decode('string_escape'),
                'color': '#000000',
            },
            'reason': {
                'value': u'%s' % salerefund.desc,
                'color': '#c0392b',
            },
            'refund': {
                'value': u'¥%.2f' % salerefund.refund_fee,
                'color': '#c0392b',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % salerefund.sale_trade.id
        return self.push(customer, template_ids, template_data, to_url)

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
                'value': u'%s' % awardcarry.created,
                'color': '#000000',
            },
            'remark': {
                'value': courage_remarks,
                'color': '#F87217',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_ordercarry(self, ordercarry, to_url):
        """
        {{first.DATA}}
        收益金额：{{keyword1.DATA}}
        收益来源：{{keyword2.DATA}}
        到账时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        # CARRY_TYPES = ((1, u'微商城订单'), (2, u'App订单额外+10%'), (3, u'下属订单+20%'),)
        description = ""
        if ordercarry.carry_type == 1:
            description = u'微商城订单'
        if ordercarry.carry_type == 2:
            description = u'App订单（佣金更高哦！）'
        if ordercarry.carry_type == 3:
            description = u'下属订单'

        customer = utils.get_mama_customer(ordercarry.mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            money = u'¥%.2f' % ordercarry.carry_num_display()
            sms.push_mama_ordercarry(customer, money=money)
            return

        template_ids = {
            'meimei': 'jorNMI-K3ewxBXHTgTKpePCF6yn5O5oLZK6azNNoWK4',
            'temai': 'AnAQcK0rgPYLdqi8HM4_MIjcXyhfOyMDrkLChV6aXrQ'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'¥%.2f' % ordercarry.carry_num_display(),
                'color': '#ff0000',
            },
            'keyword2': {
                'value': description,
                'color': '#000000',
            },
            'keyword3': {
                'value': u'%s (订单时间)' % ordercarry.created,
                'color': '#000000',
            },
            'remark': {
                'value': template.footer.format(ordercarry.contributor_nick).decode('string_escape'),
                'color': '#F87217',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

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

    def push_mama_invite_trial(
            self, referal_mama_id, potential_mama_id, diff_num, award_num,
            invite_num, award_sum, trial_num, carry_num):
        """
        {{first.DATA}}
        姓名：{{keyword1.DATA}}
        手机：{{keyword2.DATA}}
        会员等级：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        referal_customer = utils.get_mama_customer(referal_mama_id)
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
                'value': u'新手任务',
                'color': '#4CC417',
            },
            'keyword3': {
                'value': datetime.now().strftime('%Y-%m-%d'),
                'color': '#4CC417',
            },
            'remark': {
                'value': footer,
                'color': '#4CC417',
            },
        }
        return self.push(customer, template_ids, template_data, to_url)
