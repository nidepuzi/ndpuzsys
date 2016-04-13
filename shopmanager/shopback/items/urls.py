# coding: utf-8

from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from shopback.items.views import (ProductListView,
                                  ProductItemView,
                                  ProductModifyView,
                                  ProductUpdateView,
    # ProductSkuCreateView,
                                  ProductSkuInstanceView,
                                  ProductSearchView,
                                  ProductDistrictView,
                                  ProductBarCodeView,
                                  ProductWarnMgrView,
                                  ProductNumAssignView,
                                  ProductOrSkuStatusMdView,
                                  ProductView,
                                  ProductSkuView,
                                  StatProductSaleView,
                                  StatProductSaleAsyncView,
                                  ProductScanView)
# from shopback.items.resources import (ProductListResource,
#                                       ProductItemResource,
#                                       ProductResource,
#                                       ProductSkuResource,
#                                       ProductDistrictResource,
#                                       ProductDaySaleResource,
#                                       ProductScanResource)
# from shopback.items.renderers import (ProductListHtmlRenderer,
#                                       JSONRenderer,
#                                       ProductItemHtmlRenderer,
#                                       ProductUpdateHtmlRenderer,
#                                       ProductSkuHtmlRenderer,
#                                       ProductDistrictHtmlRenderer,
#                                       ProductHtmlRenderer,
#                                       ProductBarcodeHtmlRenderer,
#                                       ProductWarnHtmlRenderer,
#                                       ProductSaleHtmlRenderer,
#                                       ProductScanRenderer)
# from core.options.renderers  import BaseJsonRenderer
# from core.options.permissions import IsAuthenticated
from shopback.base.authentication import login_required_ajax
from shopback.items.views_rest import ProductInvalidConfirmView
from .select_sale_time import change_Sale_Time
from .views_add import AddItemView, GetCategory, GetSupplier, GetSkuDetail, PreviewSkuDetail, BatchSetTime, \
    ProductScheduleView, ProductScheduleAPIView

urlpatterns = patterns('shopback.items.views',

                       url('update/items/$', 'update_user_items', name='update_items'),
                       url('update/item/$', 'update_user_item', name='update_item'),
                       url('update/stock/$', 'update_product_stock', name='update_stock'),
                       url('district/query/$', 'deposite_district_query', name='query_district'),
                       url('invalid/$', ProductInvalidConfirmView.as_view(), name='invalid_product'),
                       url('product/district/delete/$', 'delete_product_district', name='delete_district'),
                       (r'^split/$', TemplateView.as_view(template_name="items/split_product_template.html")),
                       (r'^product/(?P<id>[0-9]+)/$', ProductView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(ProductHtmlRenderer,BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/(?P<pid>[0-9]+)/(?P<sku_id>[0-9]+)/$', ProductSkuView.as_view(
                           #         resource=ProductSkuResource,
                           #         renderers=(BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),

                       (r'^product/$', ProductListView.as_view({'get': 'list'}
                                                               #         resource=ProductListResource,
                                                               #         renderers=(ProductListHtmlRenderer,JSONRenderer),
                                                               #         authentication=(UserLoggedInAuthentication,),
                                                               #         permissions=(IsAuthenticated,)
                                                               )),
                       (r'^product/item/(?P<outer_id>[\w^_]+)/$', ProductItemView.as_view(
                           #         resource=ProductItemResource,
                           #         renderers=(ProductItemHtmlRenderer,JSONRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/modify/(?P<outer_id>[\w^_]+)/$', ProductModifyView.as_view(
                           #         resource=ProductItemResource,
                           #         renderers=(JSONRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/update/(?P<outer_id>[\w^_]+)/$', ProductUpdateView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(ProductUpdateHtmlRenderer,JSONRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/sku/(?P<sku_id>[\w^_]+)/$', ProductSkuInstanceView.as_view(
                           #         resource=ProductSkuResource,
                           #         renderers=(ProductSkuHtmlRenderer,JSONRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^query/$', ProductSearchView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/barcode/$', ProductBarCodeView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(BaseJsonRenderer,ProductBarcodeHtmlRenderer),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/district/(?P<id>[0-9]+)/$', ProductDistrictView.as_view()),
                       (r'^podorsku/status/$', ProductOrSkuStatusMdView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/warn/$', ProductWarnMgrView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(BaseJsonRenderer,ProductWarnHtmlRenderer),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/assign/$', ProductNumAssignView.as_view(
                           #         resource=ProductResource,
                           #         renderers=(BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/sale/$', StatProductSaleView.as_view(
                           #         resource=ProductDaySaleResource,
                           #         renderers=(BaseJsonRenderer,ProductSaleHtmlRenderer),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^product/sale_async/$', StatProductSaleAsyncView.as_view()),
                       (r'^product/scan/$', ProductScanView.as_view(
                           #         resource=ProductScanResource,
                           #         renderers=(BaseJsonRenderer,ProductScanRenderer),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       url(r'^test/$', TemplateView.as_view(
                           template_name="items/product_sku_diff.html"),
                           name='test_diff'),
                       # (r'^product_lookup/$', 'shopback.items.views.json_lookup', product_lookup),
                       url(r'^select_sale_time/$', change_Sale_Time, name='select_sale_time'),
                       url(r'^add_item/$', AddItemView.as_view(), name='select_sale_time'),
                       url(r'^get_category/$', GetCategory.as_view(), name='get_category'),
                       url(r'^get_supplier/$', GetSupplier.as_view(), name='get_supplier'),
                       url(r'^get_sku/$', GetSkuDetail.as_view(), name='get_sku'),
                       url(r'^preview_sku/$', PreviewSkuDetail.as_view(), name='preview_sku'),
                       url(r'^batch_settime/$', BatchSetTime.as_view(), name='batch_settime'),
                       url(r'^product_schedule/$', ProductScheduleView.as_view(), name='product_schedule'),
                       url(r'^product_schedule/(?P<p>\d+)/$', ProductScheduleView.as_view(), name='product_schedule'),
                       url(r'^product_schedule_api/$', ProductScheduleAPIView.as_view(), name='product_schedule_api')
                       )
