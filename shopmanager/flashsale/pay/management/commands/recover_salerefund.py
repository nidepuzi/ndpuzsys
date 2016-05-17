# coding=utf-8
__author__ = 'meron'
import os, sys, string
import MySQLdb
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from flashsale.pay.models import SaleRefund
import logging

logger = logging.getLogger(__name__)

TMPDB_HOST = 'staging.xiaolumm.com'
TMPDB_PORT = 30001
TMPDB_USER = 'qiyue'
TMPDB_PWD = 'youni_2014qy'

REFUND_FIELDS = ['created', 'modified', 'id', 'refund_no', 'trade_id', 'order_id', 'buyer_id', 'refund_id', 'charge',
                 'channel', 'item_id', 'title', 'ware_by', 'sku_id', 'sku_name', 'refund_num', 'buyer_nick', 'mobile',
                 'phone', 'total_fee', 'payment', 'refund_fee', 'success_time', 'company_name', 'sid', 'reason',
                 'proof_pic', 'feedback', 'has_good_return', 'has_good_change', 'good_status', 'status',
                 'amount_flow']


def get_temp_conn():
    try:
        conn = MySQLdb.connect(host=TMPDB_HOST, port=TMPDB_PORT, user=TMPDB_USER, passwd=TMPDB_PWD, db='xiaoludb',
                               charset="utf8")
        return conn
    except Exception, e:
        print e
        sys.exit()


def get_refund_list():
    tmp_conn = get_temp_conn()
    t_cursor = tmp_conn.cursor()
    t_cursor.execute(
        "select %s from flashsale_refund where modified > '2016-05-15 00:00:00' " % (','.join(REFUND_FIELDS)))

    refund_tuples = t_cursor.fetchall()
    refund_dict_list = []
    for trade in refund_tuples:
        refund_dict = dict(zip( REFUND_FIELDS, trade))
        refund_dict_list.append(refund_dict)

    t_cursor.close()
    tmp_conn.close()
    return refund_dict_list


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.debug('recover_salerefund start ...')
        refund_list = get_refund_list()
        logger.debug('debug temp trades len: %d' % len(refund_list))
        logger.debug('trade dict:%s' % refund_list[0])

        for refund_dict in refund_list:
            srefund = SaleRefund.objects.filter(trade_id=refund_dict['trade_id'],
                                                order_id=refund_dict['order_id']).first()
            if srefund:
                continue

            srefund = SaleRefund()
            for k,v in refund_dict.items():
                setattr(srefund,k,v)
            srefund.id = None
            srefund.save()

