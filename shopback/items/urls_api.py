# coding: utf-8

from django.conf.urls import include, url

from rest_framework import routers
from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'product', views.ProductManageViewSet)

router_urls = router.urls
router_urls += ([

])

router_v2 = routers.DefaultRouter(trailing_slash=False)
router_v2.register(r'product', views.ProductManageV2ViewSet)
router_v2_urls = router_v2.urls
router_model = routers.DefaultRouter(trailing_slash=False)
router_model.register(r'model_product', views.ProductManageV2ViewSet)
router_model.register(r'stock_product', views.ProductViewSet)
router_v2_urls += (router_model.urls)
# product_views = views.ProductViewSet.as_view({})#{'get': ['list', 'retrieve'],'post': 'create'})
# router_product = routers.DefaultRouter(trailing_slash=False)
# router_product.register(r'stock_product', )
# router_v2_urls += (router_product.urls)
# router_v2_urls += product_views
urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='items_v1')),
    url(r'^v2/', include(router_v2_urls, namespace='items_v2')),
]
