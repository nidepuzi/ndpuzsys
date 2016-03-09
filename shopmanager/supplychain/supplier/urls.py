# coding: utf-8

from django.conf.urls import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns
from django.views.decorators.csrf import csrf_exempt

from . import views, views_buyer_group, views_aggregate, views_addsupplier, views_hot, views_change_fields


urlpatterns = [
    url(r'^brand/$', views.SaleSupplierList.as_view()),
    url(r'^brand/(?P<pk>[0-9]+)/$', views.SaleSupplierDetail.as_view()),
    url(r'^brand/charge/(?P<pk>[0-9]+)/$', views.chargeSupplier),

    url(r'^brand/fetch/(?P<pk>[0-9]+)/$', views.FetchAndCreateProduct.as_view()),

    url(r'^product/$', views.SaleProductList.as_view()),
    url(r'^line_product/$', views.SaleProductAdd.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$', views.SaleProductDetail.as_view()),
    url(r'^buyer_group/$', csrf_exempt(views_buyer_group.BuyerGroupSave.as_view())),
    url(r'^qiniu/$', views.QiniuApi.as_view()),
    # select sale_time
    url(r'^select_sale_time/$', views.change_Sale_Time),
    url(r'^bdproduct/(?P<pk>[0-9]+)/$', views_aggregate.AggregateProductView.as_view()),
    url(r'^addsupplier/$', views_addsupplier.AddSupplierView.as_view()),
    url(r'^checksupplier/$', views_addsupplier.CheckSupplierView.as_view()),
    url(r'^hotpro/$', views_hot.HotProductView.as_view()),
    url(r'^manage_schedule/$', views_addsupplier.ScheduleManageView.as_view()),
    url(r'^schedule_detail/$', views.ScheduleDetailView.as_view()),
    url(r'^schedule_detail_api/$', views.ScheduleDetailAPIView.as_view()),
    url(r'^schedule_export/$', views.ScheduleExportView.as_view()),
    url(r'^collect_num_api/$', views.CollectNumAPIView.as_view()),
    url(r'^remain_num_api/$', views.RemainNumAPIView.as_view()),
    url(r'^sync_stock_api/$', views.SyncStockAPIView.as_view()),
    url(r'^compare_schedule/$', views_addsupplier.ScheduleCompareView.as_view()),
    url(r'^sale_product_api/$', views_addsupplier.SaleProductAPIView.as_view()),
    url(r'^change_list_fields/$', views_change_fields.SupplierFieldsChange.as_view()),
    url(r'^product_change/([0-9]+)/$', views.SaleProductChange.as_view()),
    url(r'^schedule_batch_set/$', views_addsupplier.ScheduleBatchSetView.as_view()),
    url(r'^category_mapping/$', views.CategoryMappingView.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
