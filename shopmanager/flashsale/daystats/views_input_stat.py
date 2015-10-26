# *_* coding=utf-8 *_*
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from .tasks import task_calc_performance_by_user, task_calc_performance_by_supplier, task_calc_sale_product
import datetime
from supplychain.supplier.models import SaleCategory
from shopback.items.models import Product, ProductCategory
import flashsale.dinghuo.utils as tools_util
import collections
class ProductInputStatView(generics.ListCreateAPIView):
    """
        录入资料统计
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2saleinput.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        start_date_str = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date_str = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        start_date = tools_util.parse_date(start_date_str)
        year, month, day = end_date_str.split('-')
        end_date = datetime.date(int(year), int(month), int(day))
        all_sale_charger = Product.objects.filter(created__range=(start_date, end_date), status=Product.NORMAL).values(
            "sale_charger").distinct()

        all_nv_product = Product.objects.filter(created__range=(start_date, end_date), status=Product.NORMAL,
                                                category__parent_cid=8)
        all_child_product = Product.objects.filter(created__range=(start_date, end_date), status=Product.NORMAL,
                                                   category__parent_cid=5)

        result_data = {}
        for one_sale_charger in all_sale_charger:
            temp_nv_product = all_nv_product.filter(sale_charger=one_sale_charger["sale_charger"])
            temp_child_product = all_child_product.filter(sale_charger=one_sale_charger["sale_charger"])
            result_data[one_sale_charger["sale_charger"]] = [[temp_nv_product.filter(category__cid=18).count(),
                                                              temp_nv_product.filter(category__cid=19).count(),
                                                              temp_nv_product.filter(category__cid=22).count(),
                                                              temp_nv_product.filter(category__cid=21).count(),
                                                              temp_nv_product.filter(category__cid=20).count(),
                                                              temp_nv_product.filter(category__cid=24).count()],
                                                             [temp_child_product.filter(category__cid=23).count(),
                                                              temp_child_product.filter(category__cid=17).count(),
                                                              temp_child_product.filter(category__cid=16).count(),
                                                              temp_child_product.filter(category__cid=12).count(),
                                                              temp_child_product.filter(category__cid=15).count(),
                                                              temp_child_product.filter(category__cid=14).count(),
                                                              temp_child_product.filter(category__cid=13).count(),
                                                              temp_child_product.filter(category__cid=25).count()]]
        category_list = [u"女装/外套", u"女装/连衣", u"女装/套装", u"女装/下装", u"女装/上装", u"女装/配饰",
                         u"童装/配饰", u"童装/下装", u"童装/哈衣", u"童装/外套", u"童装/套装", u"童装/连身", u"童装/上装", u"童装/亲子"]
        return Response({"result_data": result_data, "category_list": category_list,
                         "start_date_str": start_date_str, "end_date_str": end_date_str})
