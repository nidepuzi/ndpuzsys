#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from shopback import paramconfig as pcfg
from shopback.orders.models import Trade,Order
from shopback.fenxiao.models import PurchaseOrder
from shopback.items.models import Product,ProductSku
from shopback.signals import rule_signal,recalc_fee_signal
from common.utils import update_model_fields


class MergeTradeManager(models.Manager):
    

    def get_queryset(self):
        
        super_tm = super(MergeTradeManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
        
    
    def getMergeQueryset(self,buyer_nick, 
                          receiver_name, 
                          receiver_mobile,
                          receiver_phone,
                          state='',
                          city=''):
        
        q = Q(receiver_name=receiver_name,buyer_nick=buyer_nick)
        if receiver_mobile :
            q = q|Q(receiver_mobile=receiver_mobile)
                
        if receiver_phone:
            q = q|Q(receiver_phone=receiver_phone)
            
        queryset = self.get_queryset().filter(q)\
                .exclude(sys_status__in=(pcfg.EMPTY_STATUS,
                                         pcfg.FINISHED_STATUS,
                                         pcfg.INVALID_STATUS))
        if state and city:
            queryset.filter(receiver_state=state,receiver_city=city)
            
        return queryset
                
    def getMainMergeTrade(self,trade):
        
        merge_queryset = self.getMergeQueryset(
                                            trade.buyer_nick,
                                            trade.receiver_name,
                                            trade.receiver_mobile,
                                            trade.receiver_phone)\
                             .filter(has_merge=True)
        if merge_queryset.count() > 0:
            return merge_queryset[0]
        return None
        
        
    def mergeMaker(self,trade,sub_trade):
        
        from shopback.trades.options import mergeMaker
        return mergeMaker(trade,sub_trade)
    
    def mergeRemover(self,trade):
        
        from shopback.trades.options import mergeRemover
        return mergeRemover(trade)
        
    def driveMergeTrade(self,trade):
        
        from shopback.trades.options import driveMergeTrade
        return driveMergeTrade(trade)
    
    def updateWaitPostNum(self,trade):
        
        for order in trade.inuse_orders:
            
            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                continue
            
            Product.objects.updateWaitPostNumByCode(order.outer_id,
                                                    order.outer_sku_id,
                                                    order.num)
    
    
    def reduceWaitPostNum(self,trade):
        
        for order in trade.inuse_orders:
            
            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                continue
                
            Product.objects.reduceWaitPostNumByCode(order.outer_id,
                                                    order.outer_sku_id,
                                                    order.num)
        
    def isOrderDefect(self,outer_id,outer_sku_id):
        
        try:
            if outer_sku_id :
                ProductSku.objects.get(outer_id=outer_sku_id,
                                       product__outer_id=outer_id)
            else:
                product = Product.objects.get(outer_id=outer_id)
                if product.prod_skus.count() > 0:
                    return True        
        except (Product.DoesNotExist,ProductSku.DoesNotExist):
            return True
        return False
            
        
    def isTradeDefect(self,trade):
        
        for order in trade.inuse_orders:
            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                return True
            
        return False
        
            
    def isTradeOutStock(self,trade):
        
        for order in trade.inuse_orders:
            try:
                if Product.objects.isProductOutOfStock(order.outer_id,
                                                       order.outer_sku_id):
                    return True
            except Product.ProductCodeDefect:
                continue
            
        return False

    
    def isTradeFullRefund(self,trade):
        
        if not isinstance(trade,self.model):
            trade = self.get(id=trade)  

        refund_approval_num = trade.merge_orders.filter(
                            refund_status__in=pcfg.REFUND_APPROVAL_STATUS,
                            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                            is_merge=False)\
                            .count()
                            
        total_orders_num  = trade.merge_orders.filter(
                            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                            is_merge=False).count()

        if refund_approval_num == total_orders_num:
            return True
        return False

    
    def isTradeNewRefund(self,trade):
        
        if not isinstance(trade,self.model):
            trade = self.get(id=trade) 
            
        refund_orders_num   = trade.merge_orders.filter(
                                    gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                                    is_merge=False)\
                              .exclude(refund_status__in=(pcfg.NO_REFUND,
                                                          pcfg.REFUND_CLOSED,
                                                          pcfg.EMPTY_STATUS)).count()
        
        if refund_orders_num > trade.refund_num:
            
            trade.refund_num = refund_orders_num
            update_model_fields(trade,update_fields=['refund_num'])
            return True
        
        return False
        
    def isTradeRefunding(self,trade):
        
        orders = trade.merge_orders.filter(
                        refund_status=pcfg.REFUND_WAIT_SELLER_AGREE)
        if orders.count()>0:
            return True
        return False
        
    def isOrderRuleMatch(self,order):
        try:
            return Product.objects.isProductRuelMatch(order.outer_id,
                                                  order.outer_sku_id)
        except Product.ProductCodeDefect:
            return False
        
    def isTradeRuleMatch(self,trade):
        
        for order in trade.inuse_orders:
            if self.isOrderRuleMatch(order):
                return True
            
        return False
    
        
    def isTradeMergeable(self,trade):
        
        if not isinstance(trade,self.model):
            trade = self.get(id=trade) 
            
        queryset = self.getMergeQueryset(trade.buyer_nick,
                                         trade.receiver_name,
                                         trade.receiver_mobile,
                                         trade.receiver_phone,
                                         state=trade.receiver_state,
                                         city=trade.receiver_city)
        trades = queryset.exclude(id=trade.id)
        
        return trades.count() > 0
    
    def diffTradeAddress(self,trade,sub_trade):
        
        diff_string = []
        if trade.receiver_name != sub_trade.receiver_name:
            diff_string.append('%s|%s'%(trade.receiver_name,
                                        sub_trade.receiver_name))
        
        if trade.receiver_mobile != sub_trade.receiver_mobile:
            diff_string.append('%s|%s'%(trade.receiver_mobile,
                                        sub_trade.receiver_mobile))
        
        if trade.receiver_phone != sub_trade.receiver_phone:
            diff_string.append('%s|%s'%(trade.receiver_phone,
                                        sub_trade.receiver_phone))
            
        if trade.receiver_state != sub_trade.receiver_state:
            diff_string.append('%s|%s'%(trade.receiver_state,
                                        sub_trade.receiver_state))
            
        if trade.receiver_city != sub_trade.receiver_city:
            diff_string.append('%s|%s'%(trade.receiver_city,
                                        sub_trade.receiver_city))
            
        if trade.receiver_district != sub_trade.receiver_district:
            diff_string.append('%s|%s'%(trade.receiver_district,
                                        sub_trade.receiver_district))
            
        if trade.receiver_address != sub_trade.receiver_address:
            diff_string.append('%s|%s'%(trade.receiver_address,
                                        sub_trade.receiver_address))
        return ','.join(diff_string)
            
            
    def isValidPubTime(self,userId,trade,modified):
        
        if not isinstance(trade,self.model):
            try:
                trade = self.get(user__visitor_id=userId,tid=trade) 
            except:
                return True
            
        if (not trade.modified or 
            trade.modified < modified or 
            not trade.sys_status):
            
                return True
        return False
    
    def updatePubTime(self,userId,trade,modified):
        
        if not isinstance(trade,self.model):
            trade = self.get(user__visitor_id=userId,tid=trade) 

        trade.modified = modified
        
        update_model_fields(trade,update_fields=['modified'])
        

    def mapTradeFromToCode(self,trade_from):
        
        from .models import TF_CODE_MAP
        
        from_code = 0
        from_list = trade_from.split(',')
        for f in from_list:
            from_code |= TF_CODE_MAP.get(f.upper(),0)
            
        return from_code
    
    def updateProductStockByTrade(self,trade):
        
        for order in trade.print_orders:
            
            outer_id     = order.outer_id
            outer_sku_id = order.outer_sku_id
            order_num    = order.num
            
            if outer_sku_id:
                psku = ProductSku.objects.get(product__outer_id=outer_id,
                                              outer_id=outer_sku_id)
                psku.update_quantity(order_num,dec_update=True)
                psku.update_wait_post_num(order_num,dec_update=True)
                
            else:
                prod = Product.objects.get(outer_id=outer_id)
                prod.update_collect_num(order_num,dec_update=True)
                prod.update_wait_post_num(order_num,dec_update=True)
                
        for order in trade.return_orders:
            
            outer_id     = order.outer_id
            outer_sku_id = order.outer_sku_id
            order_num    = order.num
            
            if outer_sku_id:
                psku = ProductSku.objects.get(product__outer_id=outer_id,
                                              outer_id=outer_sku_id)
                psku.update_quantity(order_num,dec_update=False)
                
            else:
                prod = Product.objects.get(outer_id=outer_id)
                prod.update_collect_num(order_num,dec_update=False)
    
    
    
    
 
