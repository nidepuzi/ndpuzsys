# coding=utf-8
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from django.contrib.auth.models import Permission


class IsAccessSendBudgetEnvelop(permissions.BasePermission):        #管理发送红包: 创建用户budget_log记录
    def has_permission(self, request, view):
        user = request.user
        own_perms = user.get_group_permissions()
        if user.has_perm("pay.manage_user_budget"):
            return True
        else:
            return False