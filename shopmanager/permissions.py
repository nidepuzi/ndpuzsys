# coding=utf-8
"""
    自定义的权限尽量在此记录
"""

from django.contrib.auth.models import Permission,Group
from django.contrib.contenttypes.models import ContentType

permission_trades = [
    ('manage_package_order', ('trades', 'packageorder'), 'manage package order', u'管理包裹')
]

permissions = []
permissions.extend(permission_trades)


def update_permissions():
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    for permission in permissions:
        content_type = ContentType.objects.get(app_label=permission[1][0], model=permission[1][1])
        Permission.objects.get_or_create(name=permission[2], content_type=content_type, codename=permission[0])
# 获取权限对应的model
# from django.apps import apps
# apps.get_models('trades', 'packageorder')

def update_salesupplier_permissions():
    content_type = ContentType.objects.get(app_label="supplier", model="salesupplier")
    Permission.objects.get_or_create(name="manage sale supplier", content_type=content_type, codename="manage_sale_supplier")
    perm = Permission.objects.get(name="manage sale supplier",codename="manage_sale_supplier")
    g=Group.objects.get(id=18)
    g.permissions.add(perm.id)

def update_salecategory_permissions():
    content_type = ContentType.objects.get(app_label="supplier", model="salecategory")
    Permission.objects.get_or_create(name="manage sale category", content_type=content_type, codename="manage_sale_category")
    perm = Permission.objects.get(name="manage sale category",codename="manage_sale_category")
    Group.objects.get(id=18).add(perm.id)

def update_saleproduct_permissions():
    content_type = ContentType.objects.get(app_label="supplier", model="saleproduct")
    Permission.objects.get_or_create(name="manage sale product", content_type=content_type, codename="manage_sale_product")
    perm = Permission.objects.get(name="manage sale product",codename="manage_sale_product")
    Group.objects.get(id=18).add(perm.id)

def update_salemanage_permissions():
    content_type = ContentType.objects.get(app_label="supplier", model="saleproductmanage")
    Permission.objects.get_or_create(name="manage sale manage", content_type=content_type, codename="manage_sale_manage")
    perm = Permission.objects.get(name="manage sale manage",codename="manage_sale_manage")
    Group.objects.get(id=18).add(perm.id)

def update_salemanagedetail_permissions():
    content_type = ContentType.objects.get(app_label="supplier", model="saleproductmanagedetail")
    Permission.objects.get_or_create(name="manage sale manage detail", content_type=content_type, codename="manage_sale_manage_detail")
    perm = Permission.objects.get(name="manage sale manage detail",codename="manage_sale_manage_detail")
    Group.objects.get(id=18).add(perm.id)

def update_preferencepool_permissions():
    content_type = ContentType.objects.get(app_label="supplier", model="preferencepool")
    Permission.objects.get_or_create(name="manage preference pool", content_type=content_type, codename="manage_preference_pool")
    perm = Permission.objects.get(name="manage preference pool",codename="manage_preference_pool")
    Group.objects.get(id=18).add(perm.id)

def update_xiaolumama_permissions():
    content_type = ContentType.objects.get(app_label="xiaolumm", model="xiaolumama")
    Permission.objects.get_or_create(name="manage xiaolumama", content_type=content_type, codename="manage_xiaolumama")
    perm = Permission.objects.get(name="manage xiaolumama",codename="manage_xiaolumama")
    Group.objects.get(id=18).add(perm.id)

def update_appfullpush_permissions():
    content_type = ContentType.objects.get(app_label="protocol", model="apppushmsg")
    Permission.objects.get_or_create(name="manage apppushmsg", content_type=content_type, codename="manage_apppushmsg")
    perm = Permission.objects.get(name="manage apppushmsg",codename="manage_apppushmsg")
    Group.objects.get(id=18).add(perm.id)

def update_sendbudgetenvelop_permissions():
    content_type = ContentType.objects.get(app_label="pay", model="userbudget")
    Permission.objects.get_or_create(name="manage user budget", content_type=content_type, codename="manage_user_budget")
    perm = Permission.objects.get(name="manage user budget",codename="manage_user_budget")
    Group.objects.get(id=18).add(perm.id)

def update_usercoupon_permissions():
    content_type = ContentType.objects.get(app_label="coupon", model="usercoupon")
    Permission.objects.get_or_create(name="manage user coupon", content_type=content_type,codename="manage_user_coupon")
    perm = Permission.objects.get(name="manage user coupon",codename="manage_user_coupon")
    Group.objects.get(id=18).add(perm.id)

def update_coupontransferrecord_permissions():
    content_type = ContentType.objects.get(app_label="coupon", model="transfercoupondetail")
    Permission.objects.get_or_create(name="manage transfer coupondetail", content_type=content_type,codename="manage_transfer_coupondetail")
    perm = Permission.objects.get(name="manage transfer coupondetail",codename="manage_transfer_coupondetail")
    Group.objects.get(id=18).add(perm.id)
