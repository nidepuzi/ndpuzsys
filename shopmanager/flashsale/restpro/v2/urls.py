# coding: utf-8
from django.conf.urls import patterns, include, url
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

# 2016-3-2 v2
from . import views
from flashsale.xiaolumm.views import views_rank, views_message, award, week_rank

v2_router = routers.DefaultRouter(trailing_slash=False)
v2_router.register(r'categorys', views.SaleCategoryViewSet)
v2_router.register(r'carts', views.ShoppingCartViewSet)
v2_router.register(r'products', views.ProductViewSet)
v2_router.register(r'modelproducts', views.ModelProductV2ViewSet)
v2_router.register(r'trades', views.SaleTradeViewSet)
v2_router.register(r'orders', views.SaleOrderViewSet)
v2_router.register(r'fortune', views.MamaFortuneViewSet)
v2_router.register(r'carry', views.CarryRecordViewSet)
v2_router.register(r'ordercarry', views.OrderCarryViewSet)
v2_router.register(r'awardcarry', views.AwardCarryViewSet)
v2_router.register(r'clickcarry', views.ClickCarryViewSet)
v2_router.register(r'activevalue', views.ActiveValueViewSet)
v2_router.register(r'referal', views.ReferalRelationshipViewSet)
v2_router.register(r'group', views.GroupRelationshipViewSet)
v2_router.register(r'visitor', views.UniqueVisitorViewSet)
v2_router.register(r'fans', views.XlmmFansViewSet)
v2_router.register(r'dailystats', views.DailyStatsViewSet)

from flashsale.restpro.v1 import views_coupon_new
from flashsale.restpro.v2 import views

v2_router.register(r'usercoupons', views_coupon_new.UserCouponsViewSet)
v2_router.register(r'cpntmpl', views_coupon_new.CouponTemplateViewSet)
v2_router.register(r'sharecoupon', views_coupon_new.OrderShareCouponViewSet)
v2_router.register(r'tmpsharecoupon', views_coupon_new.TmpShareCouponViewset)

# v2_router.register(r'rank', views_rank.MamaCarryTotalViewSet)
# v2_router.register(r'teamrank', views_rank.MamaTeamCarryTotalViewSet)
v2_router.register(r'rank', week_rank.WeekMamaCarryTotalViewSet)
v2_router.register(r'teamrank', week_rank.WeekMamaTeamCarryTotalViewSet)
v2_router.register(r'message', views_message.XlmmMessageViewSet)
v2_router.register(r'award', award.PotentialMamaAwardViewset)
v2_router.register(r'mission', views.MamaMissionRecordViewset)

v2_router_urls = v2_router.urls
v2_router_urls += format_suffix_patterns([
    url(r'^mama/order_carry_visitor', views.OrderCarryVisitorView.as_view()),
    url(r'^send_code', views.SendCodeView.as_view()),
    url(r'^verify_code', views.VerifyCodeView.as_view()),
    url(r'^reset_password', views.ResetPasswordView.as_view()),
    url(r'^passwordlogin', views.PasswordLoginView.as_view()),
    url(r'^weixinapplogin', views.WeixinAppLoginView.as_view()),
    url(r'^potential_fans', views.PotentialFansView.as_view()),
    url(r'^administrator', views.xiaolumm.MamaAdministratorViewSet.as_view()),
])

from flashsale.restpro.v2 import views

lesson_router = routers.DefaultRouter(trailing_slash=False)
lesson_router.register(r'lessontopic', views.LessonTopicViewSet)
lesson_router.register(r'lesson', views.LessonViewSet)
lesson_router.register(r'instructor', views.InstructorViewSet)
lesson_router.register(r'lessonattendrecord', views.LessonAttendRecordViewSet)

urlpatterns = patterns('',
                       url(r'^', include(v2_router_urls, namespace='rest_v2')),
                       url(r'^mama/', include(v2_router_urls)),
                       )
