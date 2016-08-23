# -*- encoding:utf-8 -*-

import logging
logger = logging.getLogger('celery.handler')

def get_sale_order_mama_id(sale_order):
    sale_trade = sale_order.sale_trade
    extra = sale_trade.extras_info
    mama_id  = 0   # 推荐人妈妈id
    if 'mm_linkid' in extra:
        mama_id = int(extra['mm_linkid'] or '0')
    return mama_id


award_carry_array99 = [[0, 0], [1, 1500], [4, 2000], [8, 2500], [21, 3500], [41, 4500], [101, 5500]]
award_carry_array188 = [[0, 0], [1, 3000], [4, 4000], [8, 5000], [21, 7000], [41, 9000], [101, 11000]]
group_carry_array = [[0, 0], [50, 1000], [200, 1500], [500, 2000], [1000, 3000]]

def get_award_carry_num(num, referal_type):
    """
    find out award_num
    referal_type：　邀请类型
    """
    from flashsale.xiaolumm.models import XiaoluMama

    idx = 0
    carry_map = {
        XiaoluMama.HALF: award_carry_array99,
        XiaoluMama.FULL: award_carry_array188
    }
    award_carry_array = carry_map[referal_type]
    for entry in award_carry_array:
        if num < entry[0]:
            break
        idx += 1

    if idx == 1:
        logger.error("get_award_carry_num | num: %s, referal_type: %s" % (num, referal_type))
    
    return award_carry_array[idx - 1][1]


def get_group_carry_num(num):
    idx = 0
    for entry in group_carry_array:
        if num < entry[0]:
            break
        idx += 1
    return group_carry_array[idx - 1][1]
