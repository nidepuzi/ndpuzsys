#-*- coding:utf8 -*-
import time
import datetime
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions

from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    Customer,
    ShoppingCart,
    UserAddress,
    UserCoupon,
    CouponsPool,
    CouponTemplate,
    genTradeUniqueid
)

from . import permissions as perms
from . import serializers 
from .exceptions import rest_exception
from django.db.models import F
from flashsale.pay.saledao import getUserSkuNumByLast24Hours
from django.forms.models import model_to_dict
from shopback.items.models import Product, ProductSku
from shopback.base import log_action, ADDITION, CHANGE
from common.utils import update_model_fields
import logging
import decimal

logger = logging.getLogger('restapi.errors')

import re
UUID_RE = re.compile('^[a-z]{2}[0-9]{6}[a-z0-9-]{10,14}$')

def isFromWeixin(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent and user_agent.find('MicroMessenger') > 0:
        return True
    return False
        

class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
    ###特卖购物车REST API接口：
    - payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
    - {prefix}/{{pk}}/delete_carts[.formt]: 删除;
    - {prefix}/{{pk}}/plus_product_carts[.formt]: 增加一件;
    - {prefix}/{{pk}}/minus_product_carts[.formt]: 减少一件;
    - {prefix}/show_carts_num[.formt]: 显示购物车数量;
    - {prefix}/show_carts_history[.formt]: 显示购物车历史;
    - {prefix}/sku_num_enough[.formt]: 获取规格数量是否充足;
    > sku_id:规格ID;
    > sku_num:规格数量;
    - {prefix}/carts_payinfo[.formt]: 根据购物车记录获取支付信息;
    > cart_ids：购物车ID列表,如101,102,103,...
    - {prefix}/now_payinfo[.formt]: 根据立即购买获取支付信息;
    > sku_id：要立即购买的商品规格ID
    """
    queryset = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL).order_by('-created')
    serializer_class = serializers.ShoppingCartSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,renderers.TemplateHTMLRenderer)
    template_name = 'homeback.html'
        
    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(buyer_id=customer.id)
        
    def list(self, request, *args, **kwargs):
        """列出购物车中所有的状态为正常的数据"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        data = []
        for a in queryset:
            temp_dict = model_to_dict(a)
            pro = Product.objects.filter(id=a.item_id)
            temp_dict["std_sale_price"] = pro[0].std_sale_price if pro else 0
            data.append(temp_dict)
        return Response(data)
    
    def create(self, request, *args, **kwargs):
        """创建购物车数据"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        data = request.data
        customer_user = Customer.objects.filter(user=request.user)

        if customer_user.count() == 0:
            return Response({"result": "0"}) #登录过期
        customer = customer_user[0]
        product_id = data.get("item_id", None)
        buyer_id = customer.id
        sku_id = data.get("sku_id", None)
        if not (product_id and sku_id):
            raise exceptions.APIException(u'参数错误')
        
        product = get_object_or_404(Product, pk=product_id)
        try:
            assert not product.details.is_seckill,u'秒杀商品不能加购物车'
        except AssertionError,exc:
            raise exceptions.APIException(exc.message)
        except Exception:
            pass
        if not product.is_onshelf():
            raise exceptions.APIException(u'商品已下架')
        
        cart_id = data.get("cart_id", None)
        if cart_id:
            s_temp = ShoppingCart.objects.filter(item_id=product_id, sku_id=sku_id, 
                                                 status=ShoppingCart.CANCEL,buyer_id=customer.id)
            s_temp.delete()
        sku_num = 1
        sku = get_object_or_404(ProductSku, pk=sku_id)
        user_skunum = getUserSkuNumByLast24Hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, user_skunum + sku_num)
        if not lockable:
            raise exceptions.APIException(u'该商品已限购')
        
        if not Product.objects.lockQuantity(sku, sku_num):
            raise exceptions.APIException(u'商品库存不足')

        if product_id and buyer_id and sku_id:
            shop_cart = ShoppingCart.objects.filter(item_id=product_id, buyer_id=buyer_id, sku_id=sku_id,
                                                    status=ShoppingCart.NORMAL)
            if shop_cart.count() > 0:
                shop_cart_temp = shop_cart[0]
                shop_cart_temp.num += int(sku_num) if sku_num else 0
                shop_cart_temp.total_fee = decimal.Decimal(shop_cart_temp.total_fee) + sku.agent_price
                shop_cart_temp.save()
                return Response({"result": "1"}) #购物车已经有了

            new_shop_cart = ShoppingCart()
            new_shop_cart.buyer_id = buyer_id
            for k, v in data.iteritems():
                if v:
                    hasattr(new_shop_cart, k) and setattr(new_shop_cart, k, v)
            new_shop_cart.buyer_nick = customer_user[0].nick if customer_user[0].nick else ""
            new_shop_cart.price = sku.agent_price
            new_shop_cart.num = 1
            new_shop_cart.total_fee = sku.agent_price * int(sku_num) if sku.agent_price else 0
            new_shop_cart.sku_name = sku.properties_alias if len(sku.properties_alias) > 0 else sku.properties_name
            new_shop_cart.pic_path = sku.product.pic_path
            new_shop_cart.title = sku.product.name
            new_shop_cart.remain_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
            new_shop_cart.save()
            for cart in queryset:
                cart.remain_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
                cart.save()
            return Response({"result": "2"}) #购物车没有
        else:
            return Response({"result": "error"})  #未知错误

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def show_carts_num(self, request, *args, **kwargs):
        """显示购物车的数量和保留时间"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.order_by('-created')
        count = 0
        last_created = 0
        if queryset.count() > 0:
            last_created = time.mktime(queryset[0].remain_time.timetuple())
        for item in queryset:
            count += item.num
        return Response({"result": count, "last_created": last_created})

    @list_route(methods=['get'])
    def show_carts_history(self, request, *args, **kwargs):
        """显示该用户12个小时内购物清单历史"""
        before = datetime.datetime.now() - datetime.timedelta(hours=12)
        customer = get_object_or_404(Customer, user=request.user)
        queryset = ShoppingCart.objects.filter(buyer_id=customer.id, status=ShoppingCart.CANCEL,
                                               modified__gt=before).order_by('-modified')
        data = []
        sku_list = []     #保存sku的id来去重
        for a in queryset:
            temp_dict = model_to_dict(a)
            pro = Product.objects.filter(id=a.item_id)
            pro_sku = ProductSku.objects.filter(id=a.sku_id)
            if pro.count() > 0 and pro_sku.count() > 0 and pro_sku[0].id not in sku_list:
                if pro[0].sale_open():
                    sku_list.append(pro_sku[0].id)
                    temp_dict["std_sale_price"] = pro[0].std_sale_price
                    temp_dict["is_sale_out"] = pro_sku[0].sale_out if pro_sku else False
                    data.append(temp_dict)
        return Response(data)
    
    @detail_route(methods=['post', 'delete'])
    def delete_carts(self, request, pk=None, *args, **kwargs):
        """关闭购物车中的某一个数据，调用关闭接口"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data="OK", status=status.HTTP_204_NO_CONTENT)
    
    def perform_destroy(self, instance):
        instance.close_cart()
    
    @detail_route(methods=['post'])
    def plus_product_carts(self, request, pk=None):
        customer = get_object_or_404(Customer, user=request.user)
        cart_item = get_object_or_404(ShoppingCart, pk=pk, buyer_id=customer.id, status=ShoppingCart.NORMAL)
        sku = get_object_or_404(ProductSku, pk=cart_item.sku_id)
        user_skunum = getUserSkuNumByLast24Hours(customer,sku)
        lockable = Product.objects.isQuantityLockable(sku, user_skunum + 1)
        if not lockable:
            raise exceptions.APIException(u'商品数量限购')
        lock_success = Product.objects.lockQuantity(sku, 1)
        if not lock_success:
            raise exceptions.APIException(u'商品库存不足')
        update_status = ShoppingCart.objects.filter(id=pk).update(num=F('num') + 1,total_fee = F('num') * cart_item.price)
        return Response({"status": update_status})

    @detail_route(methods=['post'])
    def minus_product_carts(self, request, pk=None, *args, **kwargs):
        cart_item = get_object_or_404(ShoppingCart, pk=pk)
        if cart_item.num <= 1:
            raise exceptions.APIException(u'至少购买一件')
        update_status = ShoppingCart.objects.filter(id=pk).update(num=F('num') - 1,total_fee = F('num') * cart_item.price)
        sku = get_object_or_404(ProductSku, pk=cart_item.sku_id)
        Product.objects.releaseLockQuantity(sku,1)
        return Response({"status": update_status})
    
    @list_route(methods=['post'])
    def sku_num_enough(self, request, *args, **kwargs):
        """ 规格数量是否充足 """
        sku_id   = request.REQUEST.get('sku_id','')
        sku_num  = request.REQUEST.get('sku_num','')
        if not sku_id.isdigit() or not sku_num.isdigit():
            raise exceptions.APIException(u'规格ID或数量有误')
        sku_num = int(sku_num)
        customer = get_object_or_404(Customer, user=request.user)
        sku      = get_object_or_404(ProductSku, pk=sku_id)
        user_skunum = getUserSkuNumByLast24Hours(customer,sku)
        lockable = Product.objects.isQuantityLockable(sku, user_skunum + sku_num)
        if not lockable:
            raise exceptions.APIException(u'商品数量限购')
        if sku.free_num < sku_num:
            raise exceptions.APIException(u'库存不足赶快下单')
        return Response({"sku_id": sku_id,"sku_num":sku_num})
    
    @list_route(methods=['get','post'])
    def carts_payinfo(self, request, format=None, *args, **kwargs):
        """ 根据购物车ID列表获取支付信息 """
        content = request.GET
        method  = request.method.lower()
        if format == 'html' and method == 'get':
            return Response({})
        
        cartid_list =  content.get('cart_ids','')
        cart_ids = [int(i) for i in cartid_list.split(',') if i.isdigit()]
        if len(cart_ids) == 0:
            raise exceptions.APIException(u'购物车ID不能为空')
        queryset = self.get_owner_queryset(request).filter(id__in=cart_ids)
        serializer = self.get_serializer(queryset, many=True)
        total_fee = 0
        discount_fee = 0
        post_fee = 0
        has_deposite = 0 
        wallet_cash  = 0 
        for cart in queryset:
            total_fee +=  cart.price * cart.num
            has_deposite |= cart.is_deposite()
        xlmm = None
        weixin_payable = False
        customer = get_object_or_404(Customer, user=request.user)
        if customer.unionid.strip():
            weixin_payable = isFromWeixin(request)
            xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
            xlmm = xiaolumms.count() > 0 and xiaolumms[0] or None
                
        alipay_payable = True
        wallet_payable = False
        for cart in queryset:
            discount_fee += cart.calc_discount_fee(xlmm=xlmm)
        
        coupon_id      = content.get('coupon_id','')
        coupon_ticket  = None
        if coupon_id:
            coupon       = get_object_or_404(UserCoupon, id=coupon_id, customer=str(customer.id))
            try:    # 优惠券条件检查
                coupon.check_usercoupon()
                coupon_pool  = coupon.cp_id
                discount_fee    += coupon_pool.template.value
            except Exception, exc:
                raise exceptions.APIException(exc.message)
            coupon_ticket = serializers.UsersCouponSerializer(coupon).data
            coupon_ticket['receive_date'] = coupon.created
            coupon_ticket['coupon_id'] = coupon_id
        total_payment = total_fee + post_fee - discount_fee
        if xlmm:
            wallet_payable = (xlmm.cash > 0 and 
                              xlmm.cash >= int(total_payment * 100) and
                              not has_deposite)
            wallet_cash    = xlmm.cash / 100.0
        response = {'uuid':genTradeUniqueid(),
                    'total_fee':round(total_fee,2),
                    'post_fee':round(post_fee,2),
                    'discount_fee':round(discount_fee,2),
                    'total_payment':round(total_payment,2),
                    'wallet_cash':wallet_cash,
                    'weixin_payable':weixin_payable,
                    'alipay_payable':alipay_payable,
                    'wallet_payable':wallet_payable,
                    'coupon_ticket':coupon_ticket,
                    'cart_ids':','.join([str(c) for c in cart_ids]),
                    'cart_list':serializer.data}

        if format == 'html':
            self.template_name    = 'confirmpay.html' 
            addr_list = UserAddress.normal_objects.filter(cus_uid=customer.id)
            response['addr_list'] = serializers.UserAddressSerializer(addr_list)
        
        return Response(response)
    
    @list_route(methods=['get'])
    def now_payinfo(self, request, format=None, *args, **kwargs):
        """ 立即购买获取支付信息 """
        content     = request.REQUEST
        method  = request.method.lower()
        if format == 'html' and method == 'get':
            return Response({})
        sku_id      = content.get('sku_id','')
        if not sku_id.isdigit():
            raise exceptions.APIException(u'传入规格ID不合法')
        sku_id      = int(sku_id)
        product_sku = get_object_or_404(ProductSku,id=sku_id)
        product     = product_sku.product
        
        total_fee = float(product_sku.agent_price) * 1
        post_fee = 0
        has_deposite = product.is_deposite()
        wallet_cash  = 0 
        
        customer = get_object_or_404(Customer, user=request.user)
        user_skunum = getUserSkuNumByLast24Hours(customer, product_sku)
        lockable = Product.objects.isQuantityLockable(product_sku, user_skunum + 1)
        if not lockable:
            raise exceptions.APIException(u'商品数量限购')
        
        xlmm = None
        weixin_payable = False
        if customer.unionid.strip():
            weixin_payable = isFromWeixin(request)
            xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
            xlmm = xiaolumms.count() > 0 and xiaolumms[0] or None
        alipay_payable = True
        wallet_payable = False
        discount_fee = product_sku.calc_discount_fee(xlmm=xlmm)
        
        coupon_id      = content.get('coupon_id','')
        coupon_ticket  = None
        if coupon_id:
            coupon       = get_object_or_404(UserCoupon, id=coupon_id, customer=str(customer.id),
                                             status=UserCoupon.UNUSED)
            try:
                coupon.check_usercoupon()
                coupon_pool  = coupon.cp_id
                discount_fee    += coupon_pool.template.value
            except Exception, exc:
                raise exceptions.APIException(exc.message)
            
            coupon_ticket   = serializers.UsersCouponSerializer(coupon).data
            coupon_ticket['receive_date'] = coupon.created
            coupon_ticket['coupon_id'] = coupon_id

        total_payment = total_fee + post_fee - discount_fee
        if xlmm:
            wallet_payable = (xlmm.cash > 0 and 
                              total_payment >= 0 and
                              xlmm.cash >= int(total_payment * 100) and
                              not has_deposite)
            wallet_cash    = xlmm.cash_money
            
        product_sku_dict = serializers.ProductSkuSerializer(product_sku).data
        product_sku_dict['product'] = serializers.ProductSerializer(product,
                                         context={'request': request}).data
        response = {'uuid':genTradeUniqueid(),
                    'total_fee':round(total_fee,2),
                    'post_fee':round(post_fee,2),
                    'discount_fee':round(discount_fee,2),
                    'total_payment':round(total_payment,2),
                    'wallet_cash':wallet_cash,
                    'weixin_payable':weixin_payable,
                    'alipay_payable':alipay_payable,
                    'wallet_payable':wallet_payable,
                    'coupon_ticket':coupon_ticket,
                    'sku':product_sku_dict }
        
        if format == 'html':
            self.template_name    = 'confirmpay.html' 
            addr_list = UserAddress.normal_objects.filter(cus_uid=customer.id)
            response['addr_list'] = serializers.UserAddressSerializer(addr_list)
        
        return Response(response)


class SaleOrderViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单明细REST API接口：
    """
    queryset = SaleOrder.objects.all()
    serializer_class = serializers.SaleOrderSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer)
    
    def get_queryset(self,saletrade_id=None,*args,**kwargs):
        """
        获取订单明细QS
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
 
        queryset = self.queryset.filter(sale_trade=saletrade_id)
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset
    
    def list(self, request, pk, *args, **kwargs):
        """ 
        获取用户订单列表 
        """
        queryset = self.filter_queryset(self.get_queryset(saletrade_id=pk))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_object(self):
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        tid =  self.kwargs.get('tid',None)
        queryset = self.filter_queryset(self.get_queryset(saletrade_id=tid))
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def confirm_sign(self, request, pk=None):
        instance = self.queryset.get(id=pk)
        instance.confirm_sign_order()
        log_action(request.user.id, instance, CHANGE, u'通过接口程序－确认签收')
        return Response({"ok": True})

import json
import pingpp
import urlparse
from django.db import models
from django.core.urlresolvers import reverse
from flashsale.xiaolumm.models import XiaoluMama,CarryLog
from flashsale.pay.tasks import confirmTradeChargeTask


class SaleTradeViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单REST API接口：
    - payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
    - {path}/waitpay[.formt]:获取待支付订单；
    - {path}/waitsend[.formt]:获取待发货订单；
    - {path}/{pk}/charge[.formt]:支付待支付订单;
    - {path}/{pk}/details[.formt]:获取订单及明细；
    - {path}/shoppingcart_create[.formt]:pingpp创建订单接口
    > - cart_ids：购物车明细ID，如 `100,101,...` 
    > - addr_id:客户地址ID
    > - channel:支付方式
    > - payment：付款金额
    > - post_fee：快递费用
    > - discount_fee：优惠折扣
    > - total_fee：总费用
    > - uuid：系统分配唯一ID
    - {path}/buynow_create[.formt]:立即支付订单接口
    > - item_id：商品ID，如 `100,101,...` 
    > - sku_id:规格ID
    > - num:购买数量
    > - 其它参数(不包含cart_ids)如上
    """
    queryset = SaleTrade.objects.all()
    serializer_class = serializers.SaleTradeSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    filter_fields = ('tid',)
    paginate_by = 15
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id).order_by('-created')
    
    def get_xlmm(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None
        
    def list(self, request, *args, **kwargs):
        """ 获取用户订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @detail_route(methods=['get'])
    def details(self, request, pk, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        strade   = self.get_object()
        strade_dict = serializers.SaleTradeSerializer(strade,context={'request': request}).data
#         orders_serializer = serializers.SaleOrderSerializer(strade.sale_orders.all(), many=True)
#         strade_dict['orders'] = orders_serializer.data
        return Response(strade_dict)
    
    @list_route(methods=['get'])
    def waitpay(self, request, *args, **kwargs):
        """ 获取用户待支付订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(status=SaleTrade.WAIT_BUYER_PAY)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def waitsend(self, request, *args, **kwargs):
        """ 获取用户待发货订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(status__in=(SaleTrade.WAIT_SELLER_SEND_GOODS,
                                               SaleTrade.WAIT_BUYER_CONFIRM_GOODS))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @rest_exception(errmsg='')
    def wallet_charge(self, sale_trade):
        """ 小鹿钱包支付实现 """
        
        buyer         = Customer.objects.get(pk=sale_trade.buyer_id)
        payment       = int(sale_trade.payment * 100) 
        buyer_unionid = buyer.unionid
        strade_id     = sale_trade.id
        buyer_nick    = sale_trade.buyer_nick
        channel       = sale_trade.channel
        
        xlmm = XiaoluMama.objects.get(openid=buyer_unionid)
        urows = XiaoluMama.objects.filter(
            openid=buyer_unionid,
            cash__gte=payment).update(cash=models.F('cash')-payment)
        assert urows > 0 , u'小鹿钱包余额不足'
        CarryLog.objects.create(xlmm=xlmm.id,
                                order_num=strade_id,
                                buyer_nick=buyer_nick,
                                value=payment,
                                log_type=CarryLog.ORDER_BUY,
                                carry_type=CarryLog.CARRY_OUT)
        #确认付款后保存
        confirmTradeChargeTask.s(strade_id)()
        return {'channel':channel,'success':True,'id':sale_trade.id}
    
    @rest_exception(errmsg=u'订单支付异常')
    def pingpp_charge(self,sale_trade):
        """ pingpp支付实现 """
        payment       = int(sale_trade.payment * 100)
        buyer_openid  = sale_trade.openid
        order_no      = sale_trade.tid
        channel       = sale_trade.channel
        payback_url = urlparse.urljoin(settings.M_SITE_URL,'/pages/zhifucg.html')
        cancel_url  = urlparse.urljoin(settings.M_SITE_URL,'/pages/daizhifu-dd.html')
        extra = {}
        if channel == SaleTrade.WX_PUB:
            extra = {'open_id':buyer_openid,'trade_type':'JSAPI'}

        elif channel == SaleTrade.ALIPAY_WAP:
            extra = {"success_url":payback_url,
                     "cancel_url":cancel_url}

        elif channel == SaleTrade.UPMP_WAP:
            extra = {"result_url":payback_url}

        params ={ 'order_no':'%s'%order_no,
                  'app':dict(id=settings.PINGPP_APPID),
                  'channel':channel,
                  'currency':'cny',
                  'amount':'%d'%payment,
                  'client_ip':settings.PINGPP_CLENTIP,
                  'subject':u'小鹿美美平台交易',
                  'body':u'订单ID(%s),订单金额(%.2f)'%(sale_trade.id,sale_trade.payment),
                  'metadata':dict(color='red'),
                  'extra':extra}
        charge = pingpp.Charge.create(api_key=settings.PINGPP_APPKEY,**params)
        sale_trade.charge = charge.id
        update_model_fields(sale_trade,update_fields=['charge'])
        return charge
    
    @rest_exception(errmsg=u'特卖订单创建异常')
    def create_Saletrade(self,form,address,customer):
        """ 创建特卖订单方法 """
        tuuid = form.get('uuid')
        assert UUID_RE.match(tuuid), u'订单UUID异常'
        sale_trade,state = SaleTrade.objects.get_or_create(tid=tuuid,
                                                           buyer_id=customer.id)
        assert sale_trade.status in (SaleTrade.WAIT_BUYER_PAY,SaleTrade.TRADE_NO_CREATE_PAY), u'订单不可支付'
        params = {
            'channel':form.get('channel'),
            'receiver_name':address.receiver_name,
            'receiver_state':address.receiver_state,
            'receiver_city':address.receiver_city,
            'receiver_district':address.receiver_district,
            'receiver_address':address.receiver_address,
            'receiver_zip':address.receiver_zip,
            'receiver_phone':address.receiver_phone,
            'receiver_mobile':address.receiver_mobile,
            }
        if state:
            params.update({
                'buyer_nick':customer.nick,
                'buyer_message':form.get('buyer_message',''),
                'payment':float(form.get('payment')),
                'total_fee':float(form.get('total_fee')),
                'post_fee':float(form.get('post_fee')),
                'discount_fee':float(form.get('discount_fee')),
                'charge':'',
                'status':SaleTrade.WAIT_BUYER_PAY,
                'openid':customer.openid
                })
        
        for k,v in params.iteritems():
            hasattr(sale_trade,k) and setattr(sale_trade,k,v)
        sale_trade.save()
        return sale_trade,state
    
    @rest_exception(errmsg=u'特卖订单明细创建异常')
    def create_Saleorder_By_Shopcart(self,saletrade,cart_qs):
        """ 根据购物车创建订单明细方法 """
        total_fee = saletrade.total_fee
        total_payment = saletrade.payment - saletrade.post_fee
        discount_fee = saletrade.discount_fee
        for cart in cart_qs:
            product = Product.objects.get(id=cart.item_id)
            sku = ProductSku.objects.get(id=cart.sku_id)
            cart_total_fee = cart.price * cart.num
            cart_payment  = float('%.2f'%(total_payment / total_fee * cart_total_fee))
            cart_discount = float('%.2f'%(discount_fee / total_fee * cart_total_fee))
            SaleOrder.objects.create(
                 sale_trade=saletrade,
                 item_id=cart.item_id,
                 sku_id=cart.sku_id,
                 num=cart.num,
                 outer_id=product.outer_id,
                 outer_sku_id=sku.outer_id,
                 title=product.name,
                 payment=cart_payment,
                 discount_fee=cart_discount,
                 total_fee=cart.total_fee,
                 price=cart.price,
                 pic_path=product.pic_path,
                 sku_name=sku.properties_alias,
                 status=SaleTrade.WAIT_BUYER_PAY
            )
        #清除购物车
        if not settings.DEBUG:
            cart_qs.delete()
            
    @rest_exception(errmsg=u'特卖订单明细创建异常')
    def create_SaleOrder_By_Productsku(self,saletrade,product,sku,num):
        """ 根据商品明细创建订单明细方法 """
        total_fee = saletrade.total_fee
        rnow_payment = saletrade.payment - saletrade.post_fee
        discount_fee = saletrade.discount_fee
        SaleOrder.objects.create(
             sale_trade=saletrade,
             item_id=product.id,
             sku_id=sku.id,
             num=num,
             outer_id=product.outer_id,
             outer_sku_id=sku.outer_id,
             title=product.name,
             payment=rnow_payment,
             total_fee=total_fee,
             price=sku.agent_price,
             discount_fee=discount_fee,
             pic_path=product.pic_path,
             sku_name=sku.properties_alias,
             status=SaleTrade.WAIT_BUYER_PAY
        )
      
            
    @list_route(methods=['post'])
    def shoppingcart_create(self, request, *args, **kwargs):
        """ 购物车订单支付接口 """
        CONTENT  = request.POST
        tuuid    = CONTENT.get('uuid')
        coupon_id, coupon= CONTENT.get('coupon_id',''), None
        customer = get_object_or_404(Customer,user=request.user)
        try:
            SaleTrade.objects.get(tid=tuuid,buyer_id=customer.id)
        except SaleTrade.DoesNotExist:
            cart_ids = [i for i in CONTENT.get('cart_ids','').split(',')]
            cart_qs = ShoppingCart.objects.filter(
                id__in=[i for i in cart_ids if i.isdigit()], 
                buyer_id=customer.id
            )
            #这里不对购物车状态进行过滤，防止订单创建过程中购物车状态发生变化
            if cart_qs.count() != len(cart_ids):
                raise exceptions.ParseError(u'购物车已结算待支付')
            xlmm            = self.get_xlmm(request)
            payment         = int(float(CONTENT.get('payment','0')) * 100)
            post_fee        = int(float(CONTENT.get('post_fee','0')) * 100)
            discount_fee    = int(float(CONTENT.get('discount_fee','0')) * 100)
            cart_total_fee  = 0
            cart_discount   = 0
            for cart in cart_qs:
                if not cart.is_good_enough():
                    raise exceptions.ParseError(u'抱歉,商品已被抢光')
                cart_total_fee += cart.price * cart.num * 100
                cart_discount  += cart.calc_discount_fee(xlmm=xlmm) * cart.num * 100
            
            if coupon_id:
                # 对应用户的未使用的优惠券
                coupon       = get_object_or_404(UserCoupon, id=coupon_id, customer=str(customer.id),
                                                 status=UserCoupon.UNUSED)
                try:  # 优惠券条件检查
                    coupon.check_usercoupon()
                    coupon.cp_id.template.usefee_check((cart_total_fee - cart_discount) / 100.0)  # 检查消费金额是否满足
                    coupon_pool = coupon.cp_id
                except Exception, exc:
                    raise exceptions.APIException(exc.message)
                cart_discount    += int(coupon_pool.template.value * 100)
            
            if discount_fee > cart_discount:
                raise exceptions.ParseError(u'优惠金额异常')
            
            cart_payment = cart_total_fee + post_fee - cart_discount
            if post_fee < 0 or payment < 0  or abs(payment - cart_payment) > 10:
                raise exceptions.ParseError(u'付款金额异常')
        
        addr_id  = CONTENT.get('addr_id')
        address  = get_object_or_404(UserAddress,id=addr_id,cus_uid=customer.id)
        
        channel  = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            raise exceptions.ParseError(u'付款方式有误')
        
        sale_trade,state = self.create_Saletrade(CONTENT, address, customer)
        if state:
            self.create_Saleorder_By_Shopcart(sale_trade, cart_qs)
        #使用优惠券，并修改状态
        if coupon_id and coupon:
            coupon.status = UserCoupon.USED
            coupon.sale_trade = sale_trade.id
            coupon.save()
        if channel == SaleTrade.WALLET:
            #小鹿钱包支付
            response_charge = self.wallet_charge(sale_trade)
        else:
            response_charge = self.pingpp_charge(sale_trade)

        return Response(response_charge)
    
    @list_route(methods=['post'])
    def buynow_create(self, request, *args, **kwargs):
        """ 立即购买订单支付接口 """
        CONTENT  = request.REQUEST
        item_id   = CONTENT.get('item_id')
        sku_id   = CONTENT.get('sku_id')
        sku_num  = int(CONTENT.get('num','1'))
        
        customer = get_object_or_404(Customer,user=request.user)
        product         = get_object_or_404(Product,id=item_id)
        product_sku     = get_object_or_404(ProductSku,id=sku_id)
        payment         = int(float(CONTENT.get('payment','0')) * 100)
        post_fee        = int(float(CONTENT.get('post_fee','0')) * 100)
        discount_fee    = int(float(CONTENT.get('discount_fee','0')) * 100)
        bn_totalfee     = int(product_sku.agent_price * sku_num * 100)
        
        xlmm            = self.get_xlmm(request)
        bn_discount     = product_sku.calc_discount_fee(xlmm) * sku_num
        if product_sku.free_num < sku_num or product.shelf_status == Product.DOWN_SHELF:
            raise exceptions.ParseError(u'商品已被抢光啦！')
        
        coupon_id = CONTENT.get('coupon_id','')
        if coupon_id:
            # 对应用户的未使用的优惠券
            coupon       = get_object_or_404(UserCoupon, id=coupon_id, customer=str(customer.id),
                                             status=UserCoupon.UNUSED)
            try:  # 优惠券条件检查
                coupon.check_usercoupon()
                coupon.cp_id.template.usefee_check((bn_totalfee - bn_discount) / 100.0)  # 检查消费金额是否满足
                coupon_pool = coupon.cp_id
            except Exception, exc:
                raise exceptions.APIException(exc.message)
            bn_discount += int(coupon_pool.template.value * 100)

        if discount_fee > bn_discount:
            raise exceptions.ParseError(u'优惠金额异常')
        
        bn_payment      = bn_totalfee + post_fee - bn_discount
        if post_fee < 0 or payment <= 0 or abs(payment - bn_payment) > 10 :
            raise exceptions.ParseError(u'付款金额异常')
        
        addr_id  = CONTENT.get('addr_id')
        address  = get_object_or_404(UserAddress,id=addr_id,cus_uid=customer.id)
        channel  = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            raise exceptions.ParseError(u'付款方式有误')
        
        try:
            lock_success =  Product.objects.lockQuantity(product_sku,sku_num)
            if not lock_success:
                raise exceptions.APIException(u'商品库存不足')
            sale_trade,state = self.create_Saletrade(CONTENT, address, customer)
            if state:
                self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException,exc:
            raise exc
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            raise exceptions.APIException(u'订单生成异常')
        #使用优惠券，并修改状态
        if coupon_id and coupon:
            coupon.status = UserCoupon.USED
            coupon.sale_trade = sale_trade.id
            coupon.save()
        
        if channel == SaleTrade.WALLET:
            #小鹿钱包支付
            response_charge = self.wallet_charge(sale_trade)
        else:
            #pingpp 支付
            response_charge = self.pingpp_charge(sale_trade)
        return Response(response_charge)
    
    @detail_route(methods=['post'])
    def charge(self, request, *args, **kwargs):
        """ 待支付订单支付 """
        _errmsg = {SaleTrade.WAIT_SELLER_SEND_GOODS:u'订单无需重复付款',
                   SaleTrade.TRADE_CLOSED_BY_SYS:u'订单已关闭或超时',
                   'default':u'订单不在可支付状态'}
         
        instance = self.get_object()
        if instance.status != SaleTrade.WAIT_BUYER_PAY:
            raise exceptions.APIException(_errmsg.get(instance.status,_errmsg.get('default')))
        
        if not instance.is_payable():
            raise exceptions.APIException(_errmsg.get(SaleTrade.TRADE_CLOSED_BY_SYS))   
        
        if instance.channel == SaleTrade.WALLET:
            #小鹿钱包支付
            response_charge = self.wallet_charge(instance)
        else:
            #pingpp 支付
            response_charge = self.pingpp_charge(instance)
        log_action(request.user.id, instance, CHANGE, u'重新支付')
        return Response(response_charge)
    
    def perform_destroy(self, instance):
        # 订单不在 待付款的 或者不在创建状态
        instance.close_trade()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        log_action(request.user.id, instance, CHANGE, u'通过接口程序－取消订单')
        return Response(data={"ok": True})



from django.conf import settings
from shopapp.weixin.models import WXOrder
from shopapp.weixin.models import WeixinUnionID

class WXOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###历史微信订单REST API接口：
    """
    queryset = WXOrder.objects.all()
    serializer_class = serializers.WXOrderSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    paginate_by = 25
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    
    def get_owner_queryset(self,request):
        try:
            customer = Customer.objects.get(user=request.user)
            wxunion  = WeixinUnionID.objects.get(unionid=customer.unionid,app_key=settings.WEIXIN_APPID)
        except Customer.DoesNotExist:
            raise exceptions.APIException('用户不存在')
        except WeixinUnionID.DoesNotExist:
            raise exceptions.APIException('未找到订单')
        return self.queryset.filter(buyer_openid=wxunion.openid).order_by('-order_create_time')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



