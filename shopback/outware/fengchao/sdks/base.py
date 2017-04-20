# coding: utf8
from __future__ import absolute_import, unicode_literals

import hashlib
import json
import requests
import datetime

from ... import constants
from shopback.outware.models.base import log_ware_action

from .exceptions import FengchaoApiException

import logging
logger = logging.getLogger(__name__)

FENGCHAO_SLYC_VENDOR_CODE  = 'fengchao_slyc'
FENGCHAO_SLYC_CHANNEL_CODE = 'shiliyangchang' # 十里洋场的订单channel
FENGCHAO_DEFAULT_CHANNEL_CODE = 'xiaolumeimei'

API_GETWAY = 'http://fctest02.fcgylapp.cn:30003/api/'
FENGCHAO_APPID = '0d14d2b6-042f-48d1-a0f2-fc5592883ec6'
FENGCHAO_SECRET = 'b4ca5a2a-4b76-456b-b01f-4443fddad28a'

def sign_string(string, secret):
    return hashlib.md5(str(string + secret)).hexdigest().upper()

def request_getway(data, notify_type, account):
    logger.info({
        'action': 'fengchao_notify_type_%s'%notify_type,
        'action_time': datetime.datetime.now(),
        'data': data,
    })

    data_str = str(json.dumps(data, ensure_ascii=False, encoding='utf8'))
    req_params = {
        'app_id': FENGCHAO_APPID,
        'notify_type': notify_type,
        'sign_type': 'md5',
        'sign': sign_string(data_str, FENGCHAO_SECRET),
        'data': data_str,
    }

    resp = requests.post(API_GETWAY, data=req_params)
    if not resp.status_code == 200:
        raise FengchaoApiException('蜂巢api错误: %s'%resp.text)

    content = json.loads(resp.text)
    if not content.get('success'):
        raise FengchaoApiException('蜂巢api错误: %s' % content.get('error_msg'))

    return content


# @action_decorator(constants.ATION_ORDER_CHANNEL_CREATE['code'])
def create_fengchao_order_channel(channel_client_id, channel_name, channel_type, channel_id):
    """　创建蜂巢订单来源渠道 """
    # TODO 该方法已失效，channelid 通过两个商议来对接

    from ..models import FengchaoOrderChannel
    from shopback.outware.models import OutwareAccount
    ware_account = OutwareAccount.get_fengchao_account()

    channel, state = FengchaoOrderChannel.objects.get_or_create(
        channel_id=channel_id
    )
    if state:
        channel.channel_name = channel_name
        channel.channel_type = channel_type
        channel.channel_client_id = channel_client_id
        channel.save()

    params = {
        'channel_id': channel_id,
        'channel_name': channel_name,
        'channel_type': channel_type,
        'channel_client_id': channel_client_id,
    }

    try:
        request_getway(params, constants.ATION_ORDER_CHANNEL_CREATE['code'], ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        return {'success': False, 'object': channel, 'message': str(exc)}

    channel.status = True
    channel.save()

    return {'success': True, 'object': channel, 'message': '' }


def get_skustock_by_qureyparams(sku_codes, vendor_code=None):
    """　创建蜂巢订单来源渠道 """
    if not sku_codes:
        return []

    from shopback.outware.models import OutwareAccount
    ware_account = OutwareAccount.get_fengchao_account()

    sku_querys = {'skus':[]}
    if vendor_code:
        sku_querys['vendor_code'] = vendor_code

    for sku_code in sku_codes:
        sku_querys['skus'].append({
            'sku_id': sku_code,
            'sku_type': 20
        })

    action_code = constants.ACTION_SKU_STOCK_PULL['code']

    try:
        resp = request_getway(sku_querys, action_code, ware_account)
    except Exception, exc:
        logger.error(str(exc), exc_info=True)
        log_ware_action(ware_account, action_code, state_code=constants.ERROR, message=str(exc))
        return []

    return resp['inventory']


def get_channelid_by_vendor_codes(vendor_codes):
    # vendor_codes: 根据vendor_code　返回对应的channel字典
    channel_maps = {}
    for vendor_code in vendor_codes:
        if vendor_code.lower() == FENGCHAO_SLYC_VENDOR_CODE:
            channel_maps[vendor_code] = FENGCHAO_SLYC_CHANNEL_CODE
        else:
            channel_maps[vendor_code] = FENGCHAO_DEFAULT_CHANNEL_CODE
    return channel_maps

def if_is_slyc_vendor(channel_id):
    return channel_id.lower() == FENGCHAO_SLYC_CHANNEL_CODE

def get_carrier_code_by_logistics_company_code(logistic_company_code):
    """ 系统快递编码对应蜂巢快递编码,返回空字符串表示不支持该快递 """
    maps = {
        'OTHER': 'OTHER',
        'EMS': 'EMS',
        'ZTO': 'ZTO',
        'SF': 'SF',
        'STO': 'STO',
        'CBWL': 'CBWL',
        'ZKWL': 'ZKWL',
        'TTKDEX': 'TTK',
        'POSTB': 'POSTB',
        'YUNDA_QR': 'YUNDA',
        'YTO': 'YTO',
    }
    return maps.get(logistic_company_code,'')