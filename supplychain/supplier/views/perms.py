from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission



class IsAccessSaleSupplier(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if "supplier.manage_sale_supplier" in list(own_perms):
            return True
        else:
            return False

