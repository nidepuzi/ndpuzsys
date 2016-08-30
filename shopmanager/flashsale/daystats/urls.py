# -*- coding:utf-8 -*-
# __author__ = 'linjie'
from django.conf.urls import patterns, include, url

from django.contrib.admin.views.decorators import staff_member_required

from rest_framework import routers, viewsets

from view_repeat_stats import StatsRepeatView, StatsSaleView, StatsSalePeopleView
from views_stats_performance import StatsPerformanceView, StatsSupplierView, StatsSaleProdcutView
import views_operate
import views_input_stat
import views_stats_fahuo

from .view import popularize_Cost, DailyStatsViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'daily_stats', DailyStatsViewSet, 'daily_stats')

urlpatterns = patterns('',
    url(r'^popu_cost/', popularize_Cost, name="popularize_Cost"),
    url(r'^stats_repeat/$', staff_member_required(StatsRepeatView.as_view()), name="stats_repeat"),
    url(r'^stats_sale/$', staff_member_required(StatsSaleView.as_view()), name="stats_sale"),
    url(r'^stats_people/$', staff_member_required(StatsSalePeopleView.as_view()),
       name="stats_people"),
    url(r'^stats_performance/$', staff_member_required(StatsPerformanceView.as_view()),
       name="stats_performance"),
    url(r'^stats_supplier/$', staff_member_required(StatsSupplierView.as_view()),
       name="stats_supplier"),
    url(r'^stats_sale_product/$', staff_member_required(StatsSaleProdcutView.as_view()),
       name="stats_sale_product"),
    url(r'^operate_sale/$', staff_member_required(views_operate.StatsDataView.as_view())),
    url(r'^daily_check/$', staff_member_required(views_operate.DailyCheckView.as_view())),
    url(r'^stat_input/$', staff_member_required(views_input_stat.ProductInputStatView.as_view())),
    # 录入资料统计
    url(r'^stattemp/$', staff_member_required(views_input_stat.TempView.as_view())),  # 临时测试使用
    url(r'^supplier_preview/$', staff_member_required(views_operate.SupplierPreviewView.as_view())),
    # 供应所预览
    url(r'^daily_hui/$', staff_member_required(views_stats_fahuo.StatsFahuoView.as_view())),  # 每日汇总
)


urlpatterns += patterns(
    'flashsale.daystats.views',
    url(r'^yunying/$', 'yunying.index', name='yy-index'),
    url(r'^yunying/customer/$', 'customer.index', name='yy-customer-index'),
    url(r'^yunying/product/$', 'product.index', name='yy-product-index'),
    url(r'^yunying/product/category$', 'product.salecategory', name='yy-product-salecategory'),
    url(r'^yunying/product/(?P<id>.*)', 'product.show', name='yy-product-show'),
    url(r'^yunying/mama/$', 'mama.index', name='yy-mama-index'),
    url(r'^yunying/mama/home$', 'mama.home', name='yy-mama-home'),
    url(r'^yunying/mama/tab$', 'mama.tab', name='yy-mama-tab'),
    url(r'^yunying/mama/new_task$', 'mama.new_task', name='yy-mama-new_task'),
    url(r'^yunying/mama/new_mama$', 'mama.new_mama', name='yy-mama-new_mama'),
    url(r'^yunying/sql/$', 'sql.index', name='yy-sql-index'),
    url(r'^yunying/sql/(?P<id>.*)/destroy$', 'sql.destroy', name='yy-sql-destroy'),
    url(r'^yunying/sql/create$', 'sql.create', name='yy-sql-create'),
    url(r'^yunying/databse/index$', 'database.index', name='yy-database-index'),
    url(r'^yunying/databse/table/(?P<name>.*)$', 'database.table', name='yy-database-table'),
)


urlpatterns += router.urls
