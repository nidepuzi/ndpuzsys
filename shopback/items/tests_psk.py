# -*- coding:utf-8 -*-


# import os
# import sys
# import django
# sys.path.append("/home/fpcnm/myProjects/xiaoluMM4/xiaolusys/shopmanager/")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
# django.setup()


from shopback.categorys.models import ProductCategory
from shopback.items.models.product import Product,ProductSku
from shopback.items.models.stats import SkuStock
from shopback.trades.models import PackageSkuItem
from flashsale.pay.models import SaleOrder,SaleTrade
from django.db.models import Q, Sum
from flashsale.dinghuo.models_purchase import PurchaseArrangement
import datetime

from  django.test import TestCase
from django.core.cache import cache

def create_product_category():
    ProductCategory.objects.filter(cid=23).delete()
    product_category = {"cid":23,"parent_cid":0,"name":"古董/邮币/字画/收藏","is_parent":1,"status":"mormal","sort_order":145,"grade":0}
    product_category = ProductCategory.objects.create(**product_category)
    return product_category

# print create_product_category()

def create_product():
    Product.objects.filter(outer_id="923229320687").delete()
    # product_categoty = create_product_category()
    product = {"outer_id":"923229320687","category_id":23}
    product = Product.objects.create(**product)
    return product

# print create_product()

def create_product_sku():
    ProductSku.objects.filter(id=248181).delete()
    product = Product.objects.filter(outer_id=923229320687).first()
    product_sku = {"id":248181,"outer_id":"9232293206871","product_id":product.id}
    product_sku = ProductSku.objects.create(**product_sku)
    return product_sku

# print create_product_sku()

def create_sale_trade():
    SaleTrade.objects.filter(id=468462).delete()
    sale_trade = {"id":468462,"tid":"xd123123","buyer_id":1,"buyer_nick":"疾风剑豪","payment":27.9,"receiver_name":"剑圣","receiver_address":"德玛西亚",
                  "receiver_mobile":123123,"status":2}
    sale_trade = SaleTrade.objects.create(**sale_trade)
    return sale_trade

# print create_sale_trade()

def create_sale_order():
    SaleOrder.objects.filter(id=248281).delete()
    sale_order = {"id":248281,"oid":"xo123123","item_id":10270,"title":"衬衫","price":29.9,"sku_id":248181,"num":1,"outer_id":'80205508201',"outer_sku_id":4,"total_fee":29.9,
                      "payment":29.9,"sku_name":"XL","status":5,"sale_trade_id":468462,"pay_time":datetime.datetime.now()}
    sale_order = SaleOrder.objects.create(**sale_order)
    return sale_order

# print create_sale_order()

def create_sku_stock():
    SkuStock.objects.filter(id=166779).delete()
    product = create_product()
    product_sku = create_product_sku()
    sku_stock = {"id":166779,"product":product,"sku":product_sku}
    sku_stock = SkuStock.objects.create(**sku_stock)
    return sku_stock

# print create_sku_stock()

class TestPSK(TestCase):
    def setUp(self):
        cache.clear()
        self.product_category = create_product_category()
        self.product = create_product()
        self.product_sku = create_product_sku()
        self.sale_trade = create_sale_trade()
        self.sale_order = create_sale_order()
        self.sku_stock = create_sku_stock()
        self.package_sku_item = None
        self.purchase_arragement = None

    def test_no_assign_create(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.purchase_arragement = PurchaseArrangement.objects.filter(package_sku_item_id=self.package_sku_item.id).first()
        self.package_sku_item.status = "paid"
        self.package_sku_item.assign_status = 0
        self.assertEqual(self.package_sku_item.status,"paid")
        self.assertEqual(self.package_sku_item.assign_status,0)
        self.assertEqual(self.purchase_arragement.status,PurchaseArrangement.EFFECT)
        self.assertEqual(self.purchase_arragement.purchase_record_unikey,self.package_sku_item.oid+"-1")

    def test_assign_create(self):
        self.sku_stock.history_quantity = 10
        self.sku_stock.save()
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.assertEqual(self.package_sku_item.status,"assigned")
        self.assertEqual(self.package_sku_item.assign_status,1)

    def test_set_status_prepare_book(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        pre = [self.sku_stock.psi_paid_num, self.sku_stock.psi_prepare_book_num]
        self.package_sku_item.set_status_prepare_book()
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        next = [self.sku_stock.psi_paid_num, self.sku_stock.psi_prepare_book_num]
        self.assertEqual(self.package_sku_item.status,'prepare_book')
        self.assertEqual(pre[0]-self.package_sku_item.num,next[0])
        self.assertEqual(pre[1]+self.package_sku_item.num,next[1])


    def test_set_status_booked(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.package_sku_item.set_status_booked()
        self.assertEqual(self.package_sku_item.status,"booked")
    #
    def test_set_status_ready(self):
        print "123"
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['psi_booked_num', 'psi_ready_num']
        pre = [self.sku_stock.psi_booked_num,self.sku_stock.psi_ready_num]
        self.package_sku_item.set_status_ready()
        next = [self.sku_stock.psi_booked_num,self.sku_stock.psi_ready_num]
        self.assertEqual(self.package_sku_item.status,"ready")
        self.assertEqual(self.package_sku_item.assign_status,1)
        self.assertEqual(pre[0] - self.package_sku_item.num, next[0])
        self.assertEqual(pre[1] + self.package_sku_item.num, next[1])
    #
    def test_set_status_assigned(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['psi_booked_num', 'psi_ready_num']
        pre = [self.sku_stock.psi_booked_num,self.sku_stock.psi_ready_num]
        self.package_sku_item.set_status_assigned()
        next = [self.sku_stock.psi_booked_num,self.sku_stock.psi_ready_num]
        self.assertEqual(self.package_sku_item.status,"assigned")
        self.assertEqual(self.package_sku_item.assign_status,1)
    #
    def test_set_status_not_assigned(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['assign_num', 'psi_paid_num', 'psi_assigned_num']
        pre = [self.sku_stock.assign_num,self.sku_stock.psi_paid_num,self.sku_stock.psi_assigned_num]
        self.package_sku_item.set_status_not_assigned()
        next = [self.sku_stock.assign_num,self.sku_stock.psi_paid_num,self.sku_stock.psi_assigned_num]
        self.assertEqual(self.package_sku_item.status,"paid")
        self.assertEqual(self.package_sku_item.assign_status,0)
        self.assertEqual(pre[0] - self.package_sku_item.num, next[0])
        self.assertEqual(pre[1] + self.package_sku_item.num, next[1])
        self.assertEqual(pre[12] - self.package_sku_item.num, next[2])
    #
    # def test_merge(self):
    #     pass
    #
    def test_set_status_waitscan(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['psi_merged_num', 'psi_waitscan_num']
        pre = [self.sku_stock.psi_merged_num,self.sku_stock.psi_waitscan_num]
        self.package_sku_item.set_status_waitscan()
        next = [self.sku_stock.psi_merged_num,self.sku_stock.psi_waitscan_num]
        self.assertEqual(self.package_sku_item.status,"waitscan")
        self.assertEqual(pre[0] - self.package_sku_item.num, next[0])
        self.assertEqual(pre[1] + self.package_sku_item.num, next[1])
    #
    def test_set_status_waitpost(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['psi_waitpost_num', 'psi_waitscan_num']
        pre = [self.sku_stock.psi_waitpost_num,self.sku_stock.psi_waitscan_num]
        self.package_sku_item.set_status_waitpost()
        next = [self.sku_stock.psi_waitpost_num,self.sku_stock.psi_waitscan_num]
        self.assertEqual(self.package_sku_item.status,"waitpost")
        self.assertEqual(self.package_sku_item.assign_status, 1)
        self.assertEqual(pre[0] - self.package_sku_item.num, next[0])
        self.assertEqual(pre[1] + self.package_sku_item.num, next[1])
    #
    def test_set_status_sent(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['psi_waitpost_num', 'psi_sent_num', 'post_num']
        pre = [self.sku_stock.psi_waitpost_num,self.sku_stock.psi_sent_num,self.sku_stock.post_num]
        self.package_sku_item.set_status_sent()
        next = [self.sku_stock.psi_waitpost_num,self.sku_stock.psi_sent_num,self.sku_stock.post_num]
        self.assertEqual(self.package_sku_item.status,"sent")
        self.assertEqual(self.package_sku_item.assign_status, 2)
        self.assertEqual(pre[0] - self.package_sku_item.num, next[0])
        self.assertEqual(pre[1] + self.package_sku_item.num, next[1])
        self.assertEqual(pre[12] + self.package_sku_item.num, next[2])
    #
    def test_set_status_finish(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        ['psi_finish_num', 'psi_sent_num']
        pre = [self.sku_stock.psi_finish_num,self.sku_stock.psi_sent_num]
        self.package_sku_item.set_status_finish()
        next = [self.sku_stock.psi_finish_num,self.sku_stock.psi_sent_num]
        self.assertEqual(self.package_sku_item.status,"sent")
        self.assertEqual(self.package_sku_item.assign_status, 1)
        self.assertEqual(pre[0] + self.package_sku_item.num, next[0])
        self.assertEqual(pre[1] - self.package_sku_item.num, next[1])
    #
    def test_set_status_cancel(self):
        self.package_sku_item = PackageSkuItem.create(self.sale_order)
        self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
        field_status = ['paid','prepare_book','booked','ready','assigned','merged','waitscan','waitpost','sent','finish']
        for i in field_status:
            self.package_sku_item.status = i
            self.save()
            pre_num = "self.sku_stock."+'psi_%s_num' % i
            self.package_sku_item.set_status_cancel()
            field = [self.package_sku_item.status, self.package_sku_item.assign_status]
            field_value = ['cancel',1]
            self.assertEqual(field,field_value)
            sku_sock_num = "self.sku_stock."+'psi_%s_num' % i
            eval()
            self.assertEqual(eval(sku_sock_num),)
    #
    # def test_unsend_orders_cnt(self):
    #     PackageSkuItem.unsend_orders_cnt(1)  #需要模拟多个saleorder
    #
    # def test_finish_third_send(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.sku_stock = SkuStock.objects.get(id=self.sku_stock.id)
    #     pre = [self.sku_stock.psot_num]
    #     self.package_sku_item.finish_third_send()
    #     next = [self.sku_stock.psot_num]
    #     self.assertEqual(pre[0] + self.package_sku_item.num, next[0])

    # def test_gen_package(self):
    #     pass
    #
    # def test_get_purchase_uni_key(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     key = self.package_sku_item.get_purchase_uni_key()
    #     self.assertEqual(key,self.package_sku_item.oid+"-1")
    #
    # def test_is_canceled(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.is_canceled()
    #     self.assertEqual(self.package_sku_item.assign_status,PackageSkuItem.CANCELED)
    #
    #
    # def test_is_booking_needed(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.is_booking_needed()
    #     self.assertEqual(self.package_sku_item.assign_status,PackageSkuItem.NOT_ASSIGNED)
    #
    # def test_is_booking_assigned(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.assign_status = PackageSkuItem.ASSIGNED
    #     self.package_sku_item.save()
    #     res = self.package_sku_item.is_booking_assigned()
    #     self.assertEqual(self.res,True)
    #     self.package_sku_item.assign_status = PackageSkuItem.FINISHED
    #     self.package_sku_item.save()
    #     res = self.package_sku_item.is_booking_assigned()
    #     self.assertEqual(self.res,True)
    #     for i in [0,3,4]:
    #         self.package_sku_item.assign_status = i
    #         self.package_sku_item.save()
    #         res = self.package_sku_item.is_booking_assigned()
    #         self.assertEqual(self.res, False)
    #
    # def test_is_booked(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.purchase_order_unikey = None
    #     self.package_sku_item.save()
    #     res = self.package_sku_item.is_booked()
    #     self.assertEqual(res,False)
    #     self.package_sku_item.purchase_order_unikey = "exist"
    #     self.package_sku_item.save()
    #     res = self.package_sku_item.is_booked()
    #     self.assertEqual(res,True)
    #
    # def test_clear_order_info(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.assign_status = 2
    #     self.package_sku_item.save()
    #     res = self.package_sku_item.clear_order_info()
    #     self.assertEqual(res,None)
    #     for i in [0,1,3,4]:
    #         self.package_sku_item.assign_status = i
    #         self.package_sku_item.save()
    #         res = self.package_sku_item.clear_order_info()
    #         field = [self.package_sku_item.package_order_id,self.package_sku_item.package_order_pid,
    #          self.package_sku_item.logistics_company_code,self.package_sku_item.logistics_company_name,
    #          self.package_sku_item.out_sid]
    #         res = [None,None,None,'','']
    #         self.assertEqual(field,res)
    #
    # def test_set_assign_status_time(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.finish_time = datetime.datetime.now() - datetime.timedelta(days=2)
    #     self.package_sku_item.assign_time = datetime.datetime.now() - datetime.timedelta(days=2)
    #     self.package_sku_item.assign_time = datetime.datetime.now() - datetime.timedelta(days=2)
    #     self.package_sku_item.save()
    #     test_map = {2:self.package_sku_item.finish_time[0:10],1:self.package_sku_item.assign_time[0:10],3:self.package_sku_item.cancel_time[0:10]}
    #     for i in [1,2,3]:
    #         self.package_sku_item.assign_status = i
    #         self.package_sku_item.set_assign_status_time()
    #         self.assertEqual(test_map[i],str(datetime.datetime.now())[0:10])
    #
    # def test_reset_assign_status(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.package_order_id = None
    #     self.package_sku_item.save()
    #     field = [self.package_sku_item.package_order_id,self.package_sku_item.package_order_pid,self.package_sku_item.assign_status]
    #     res = [None,None.PackageSkuItem.NOT_ASSIGNED]
    #     self.assertEqual(field,res)
    #     pass #当package_order_id 不为空的情况,代码尚未实现
    #
    # def test_reset_assign_package(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     field_value = [PackageSkuItem.NOT_ASSIGNED,PackageSkuItem.ASSIGNED]
    #     for i in field_value:
    #         self.package_sku_item.assign_status = i
    #         self.package_sku_item.save()
    #         self.package_sku_item.reset_assign_package()
    #         self.assertEqual()
    #
    # def test_get_not_assign_num(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.assign_status = PackageSkuItem.NOT_ASSIGNED
    #     self.package_sku_item.save()
    #     res = self.package_sku_item.get_not_assign_num(248181)
    #     expect_value = PackageSkuItem.objects.filter(sku_id=248181, assign_status=PackageSkuItem.NOT_ASSIGNED).aggregate(
    #         total=Sum('num')).get('total') or 0
    #     self.assertEqual(res,expect_value)
    #
    # def test_is_finished(self):
    #     self.package_sku_item = PackageSkuItem.create(self.sale_order)
    #     self.package_sku_item.assign_status = PackageSkuItem.FINISHED
    #     self.package_sku_item.save()






