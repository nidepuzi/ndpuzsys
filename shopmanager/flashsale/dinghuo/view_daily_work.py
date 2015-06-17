# coding:utf-8
__author__ = 'yann'
from django.shortcuts import render_to_response
import datetime
from django.template import RequestContext
from django.views.generic import View
from django.db import connection
import functions

class DailyDingHuoView(View):
    def parseEndDt(self, end_dt):
        if not end_dt:
            dt = datetime.datetime.now()
            return datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        if len(end_dt) > 10:
            return functions.parse_datetime(end_dt)
        return functions.parse_date(end_dt)

    def get(self, request):
        content = request.REQUEST
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        shelve_to_str = content.get("dt", None)
        query_time_str = content.get("showt", None)
        groupname = content.get("groupname", 0)
        dhstatus = content.get("dhstatus", '1')
        groupname = int(groupname)

        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
            if target_date > today:
                target_date = today

        shelve_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = self.parseEndDt(shelve_to_str)
        if time_to - shelve_from > datetime.timedelta(3):
            time_to = shelve_from + datetime.timedelta(3)
        elif time_to - shelve_from < datetime.timedelta(0):
            time_to = shelve_from + datetime.timedelta(1)
        query_time = self.parseEndDt(query_time_str)

        order_sql = "select id,outer_id,sum(num) as sale_num,outer_sku_id,pay_time from " \
                    "shop_trades_mergeorder where sys_status='IN_EFFECT' " \
                    "and merge_trade_id in (select id from shop_trades_mergetrade where type not in ('reissue','exchange') " \
                    "and status in ('WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED') " \
                    "and sys_status not in('INVALID','ON_THE_FLY') " \
                    "and id not in (select id from shop_trades_mergetrade where sys_status='FINISHED' and is_express_print=False))" \
                    "and gift_type !=4 " \
                    "and (pay_time BETWEEN '{0}' and '{1}') " \
                    "and CHAR_LENGTH(outer_id)>=9 " \
                    "and (left(outer_id,1)='9' or left(outer_id,1)='8' or left(outer_id,1)='1') " \
                    "group by outer_id,outer_sku_id".format(shelve_from, time_to)
        if groupname == 0:
            product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.properties_alias,B.quantity,B.id as sku_id,C.exist_stock_num from " \
                          "(select id,name as product_name,outer_id,pic_path from " \
                          "shop_items_product where  sale_time='{0}' " \
                          "and status!='delete' " \
                          "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser))) as A " \
                          "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku) as B " \
                          "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(target_date)
        else:
            product_sql = "select A.id,A.product_name,A.outer_id,A.pic_path,B.outer_id as outer_sku_id,B.quantity,B.properties_alias,B.id as sku_id,C.exist_stock_num from " \
                          "(select id,name as product_name,outer_id,pic_path from " \
                          "shop_items_product where  sale_time='{0}' " \
                          "and status!='delete' " \
                          "and sale_charger in (select username from auth_user where id in (select user_id from suplychain_flashsale_myuser where group_id={1}))) as A " \
                          "left join (select id,product_id,outer_id,properties_alias,quantity from shop_items_productsku) as B " \
                          "on A.id=B.product_id left join flash_sale_product_sku_detail as C on B.id=C.product_sku".format(target_date, groupname)
        print product_sql
        ding_huo_sql = "select outer_id,chichu_id,buy_quantity,arrival_quantity,(buy_quantity-inferior_quantity-non_arrival_quantity) as effect_quantity " \
                       "from suplychain_flashsale_orderdetail " \
                       "where orderlist_id  in(select id from suplychain_flashsale_orderlist where status not in ('作废')) and created BETWEEN '{0}' AND '{1}'".format(
                                                                                                            shelve_from, query_time)
        sql = "select product.outer_id,product.product_name,product.outer_sku_id,product.pic_path,product.properties_alias," \
              "order_info.sale_num,ding_huo_info.buy_quantity,ding_huo_info.effect_quantity,product.sku_id,product.exist_stock_num,product.id,ding_huo_info.arrival_quantity " \
              "from (" + product_sql + ") as product left join (" + order_sql + ") as order_info on product.outer_id=order_info.outer_id and product.outer_sku_id=order_info.outer_sku_id left join (" + ding_huo_sql + ") as ding_huo_info on product.outer_id=ding_huo_info.outer_id and product.sku_id=ding_huo_info.chichu_id"
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        trade_dict = {}
        for product in raw:
            sale_num = int(product[5] or 0)
            ding_huo_num = int(product[6] or 0)
            arrival_num = int(product[11] or 0)
            ding_huo_status, flag_of_more, flag_of_less = functions.get_ding_huo_status(
                sale_num, ding_huo_num, int(product[9] or 0))
            temp_dict = {"product_id": product[10], "sku_id": product[2], "product_name": product[1],
                         "pic_path": product[3], "sale_num": sale_num or 0, "sku_name": product[4],
                         "ding_huo_num": ding_huo_num, "effect_num": product[7] or 0,
                         "ding_huo_status": ding_huo_status,
                         "flag_of_more": flag_of_more, "flag_of_less": flag_of_less,
                         "sku_id": product[8], "ku_cun_num": int(product[9] or 0),
                         "arrival_num": arrival_num}
            if dhstatus == u'0' or ((flag_of_more or flag_of_less) and dhstatus == u'1') or (
                        flag_of_less and dhstatus == u'2') or (flag_of_more and dhstatus == u'3'):
                if product[0] not in trade_dict:
                    trade_dict[product[0]] = [temp_dict]
                else:
                    trade_dict[product[0]].append(temp_dict)
        return render_to_response("dinghuo/dailywork2.html",
                                  {"target_product": trade_dict, "shelve_from": target_date, "time_to": time_to,
                                   "searchDinghuo": query_time, 'groupname': groupname, "dhstatus": dhstatus},
                                  context_instance=RequestContext(request))