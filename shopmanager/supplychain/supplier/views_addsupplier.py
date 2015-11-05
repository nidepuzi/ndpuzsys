# -*- encoding:utf8 -*-
from rest_framework import generics
from shopback.categorys.models import ProductCategory

from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from django.db import transaction

from shopback.base import log_action, ADDITION, CHANGE
from django.db.models import F, Q
from supplychain.supplier.models import SaleSupplier, SaleCategory, SaleProductManage
import datetime
from supplychain.supplier.models import SaleProduct

class AddSupplierView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "add_supplier.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        platform_choice = SaleSupplier.PLATFORM_CHOICE
        process_choice = SaleSupplier.PROGRESS_CHOICES
        all_category = SaleCategory.objects.filter()
        return Response({"platform_choice": platform_choice, "all_category": all_category,
                         "process_choice": process_choice})

    @transaction.commit_on_success
    def post(self, request, *args, **kwargs):
        post = request.POST
        supplier_name = post.get("supplier_name")
        supplier_code = post.get("supplier_code", "")
        main_page = post.get("main_page", "")
        platform = post.get("platform")
        category = post.get("category")
        contact_name = post.get("contact_name")
        mobile = post.get("mobile")
        address = post.get("contact_address")
        memo = post.get("note")
        progress = post.get("progress")

        new_supplier = SaleSupplier(supplier_name=supplier_name, supplier_code=supplier_code, main_page=main_page,
                                    platform=platform, category_id=category, contact=contact_name, mobile=mobile,
                                    address=address, memo=memo, progress=progress)
        new_supplier.save()
        log_action(request.user.id, new_supplier, ADDITION, u'新建'.format(""))
        return Response({"supplier_id": new_supplier.id})


class CheckSupplierView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post = request.POST
        supplier_name = post.get("supplier_name", "")
        suppliers = SaleSupplier.objects.filter(supplier_name__contains=supplier_name)
        if suppliers.count() > 10:
            return Response({"result": "more"})
        if suppliers.count() > 0:
            return Response({"result": "10", "supplier": [s.supplier_name for s in suppliers]})
        return Response({"result": "0"})

def get_target_date_detail(target_date):
    target_sch = SaleProductManage.objects.filter(sale_time=target_date)
    result_data = []
    if target_sch.count() > 0:
        all_detail = target_sch[0].normal_detail
        return all_detail
    else:
        return ""


class ScheduleManageView(generics.ListCreateAPIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "schedulemanage.html"

    def get(self, request, *args, **kwargs):
        target_date = request.GET.get("target_date", datetime.date.today())
        result_data = []
        one_data = get_target_date_detail(target_date)
        result_data.append({target_date: one_data})
        return Response({"result_data": result_data, "target_date": target_date})


