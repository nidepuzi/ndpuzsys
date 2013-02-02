__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.trades.serializer import MergeTradetSerializer
from shopback.trades.forms import ExchangeTradeForm
from shopback.trades.models import MergeTrade

class TradeResource(ModelResource):
    """ docstring for TradeResource TradeResource """

    fields = ('trade','logistics')
    exclude = ('url',) 
    

class MergeTradeResource(ModelResource):
    """ docstring for MergeTradeResource """
    model   = MergeTrade
    fields = ('id','tid','seller_id','seller_nick','buyer_nick','type','shipping_type','buyer_message','seller_memo','sys_memo'
              ,'pay_time','modified','created','consign_time','out_sid','status','sys_status','receiver_name')
    exclude = ('url',) 

    
class OrderPlusResource(ModelResource):
    """ docstring for TradeResource ModelResource """

    #fields = (('charts','ChartSerializer'),('item_dict',None))
    exclude = ('url',) 
    
class ExchangeOrderResource(ModelResource):
    """ docstring for ExchangeOrderResource ModelResource """

    #fields = (('charts','ChartSerializer'),('item_dict',None))
    form    = ExchangeTradeForm
    exclude = ('url',) 