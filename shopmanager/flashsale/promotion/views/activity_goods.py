# coding=utf-8

from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from flashsale.promotion.models import ActivityProduct, ActivityEntry
from flashsale.promotion.serializers import ActivityProductSerializer


class ActivityGoodsViewSet(viewsets.ModelViewSet):
    queryset = ActivityProduct.objects.all()
    serializer_class = ActivityProductSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['get'])
    def get_goods_pics_by_promotionid(self, request):
        content = request.REQUEST
        promotion_id = content.get('promotion_id', None)
        brand_entry = ActivityEntry.objects.filter(id=promotion_id).first()

        if brand_entry:
            act_pics = brand_entry.activity_products.order_by("location_id")
            serializer = self.get_serializer(act_pics, many=True)
            return Response(serializer.data)
        else:
            return Response([])

    # @list_route(methods=['get'])
    # def get_desc_pics_by_promotionid(self, request):
    #     content = request.REQUEST
    #     promotion_id = content.get('promotion_id', None)
    #     desc_pics = ActivityEntry.objects.filter(id=promotion_id)
    #     if desc_pics:
    #         return Response(desc_pics.first().extra_pic)
    #     else:
    #         return Response([])

    @list_route(methods=['post'])
    def save_pics(self, request):

        content = request.REQUEST
        arr = content.get("arr", None)
        act_id = content.get("promotion_id", None)
        data = eval(arr)  # json字符串转化

        activity = ActivityEntry.objects.filter(id=act_id).first()
        # ActivityProduct.objects.filter(brand=brand).delete()
        if activity:
            activity.activity_products.all().delete()
            activity.extras = {}
            activity.save()
        else:
            return Response({"code": 1, "info": "需要先建立这些商品的推广专题-Pay › 特卖/推广专题入口 "})

        for da in data:
            pic_type = int(da['pic_type'])
            model_id = int(da['model_id'])
            product_name = da['product_name']
            pic_path = da['pic_path']
            location_id = int(da['location_id'])
            pics = ActivityProduct.objects.create(activity=activity,
                                               model_id=model_id,
                                               product_name=product_name,
                                               product_img=pic_path,
                                               location_id=location_id,
                                               pic_type=pic_type)

            pics.save()

        return Response({"code": 0, "info": ""})

    @list_route(methods=['get'])
    def get_promotion_topic_pics(self, request):
        from flashsale.promotion.views import get_customer
        customer = get_customer(request)

        content = request.REQUEST
        act_id = content.get("promotion_id", None)
        if act_id:
            act = ActivityEntry.objects.filter(id=act_id).order_by('-start_time').first()
        else:
            act = ActivityEntry.objects.filter(is_active=True).order_by('-start_time').first()

        if not act:
            return Response({"code": 1, "info": "推广活动不存在,请先创建"})

        desc_pics = act.activity_products.all()

        banner = desc_pics.filter(pic_type=ActivityProduct.BANNER_PIC_TYPE).first()
        banner_pic = ''
        if banner:
            banner_pic = banner.product_img

        coupon_getbefore_pic = desc_pics.filter(pic_type=ActivityProduct.COUPON_GETBEFORE_PIC_TYPE).order_by('model_id')
        coupon_getafter_pic = desc_pics.filter(pic_type=ActivityProduct.COUPON_GETAFTER_PIC_TYPE).order_by('model_id')
        if coupon_getafter_pic.count() != coupon_getbefore_pic.count():
            return Response({"code": 2, "info": "优惠券领前,领后数目不一致"})
        coupons = []
        for coupon in coupon_getbefore_pic:
            if not customer:
                isReceived = False
            else:
                from flashsale.coupon.models import UserCoupon
                coupon_queryset=UserCoupon.objects.all().filter(customer_id=customer.id, template_id=coupon.model_id).order_by('-created')
                if coupon_queryset.count() == 0:
                    isReceived = False
                else:
                    isReceived = True
            coupon_dict = {"couponId": coupon.model_id, "isReceived":isReceived, "getBeforePic": coupon.product_img,
                           "getAfterPic": coupon_getafter_pic.filter(model_id=coupon.model_id).first().product_img}
            coupons.append(coupon_dict)

        topics = []
        topics_pic = desc_pics.filter(pic_type=ActivityProduct.TOPIC_PIC_TYPE)
        for topic in topics_pic:
            if (topic.product_img) and (len(topic.product_img) != 0):
                topic_dict = {"pic": topic.product_img}
                topics.append(topic_dict)

        category = desc_pics.filter(pic_type=ActivityProduct.CATEGORY_PIC_TYPE).first()
        category_pic = ''
        if category:
            category_pic = category.product_img
        share = desc_pics.filter(pic_type=ActivityProduct.FOOTER_PIC_TYPE).first()
        share_pic = ''
        if share:
            share_pic=share.product_img

        goods_horizon_pic = desc_pics.filter(pic_type=ActivityProduct.GOODS_HORIZEN_PIC_TYPE).order_by('location_id')
        goods_horizon = []
        for goods in goods_horizon_pic:
            goods_dict = {"modelId": goods.model_id, "pic": goods.product_img, "productName": goods.product_name,
                          "lowestPrice": goods.product_lowest_price(), "stdPrice": goods.product_std_sale_price()}
            goods_horizon.append(goods_dict)

        goods_vertical_pic = desc_pics.filter(pic_type=ActivityProduct.GOODS_VERTICAL_PIC_TYPE).order_by('location_id')
        goods_vertical = []
        for goods in goods_vertical_pic:
            goods_dict = {"modelId": goods.model_id, "pic": goods.product_img, "productName": goods.product_name,
                          "lowestPrice": goods.product_lowest_price(), "stdPrice": goods.product_std_sale_price()}
            goods_vertical.append(goods_dict)

        return_dict = {"title": act.title,
                       "activityId": act.id, "banner": banner_pic,
                       "coupons": coupons, "topics": topics,
                       "category": category_pic, "shareBtn": share_pic,
                       "productsHorizental": goods_horizon, "productsVertical": goods_vertical}
        if desc_pics:
            return Response(return_dict)
        else:
            return Response({})
