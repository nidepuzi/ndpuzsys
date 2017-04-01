# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import json
import datetime
from django.db import models
from django.db.models import F

from tagging.fields import TagField
from core.utils.modelutils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseTagModel
from .base import PayBaseModel, BaseModel

from flashsale.promotion.models import ActivityEntry

import logging
logger = logging.getLogger(__name__)

DEFAULT_WEN_POSTER = [
    {
        "subject": ['2折起', '小鹿美美  女装专场'],
        "item_link": "/mall/product/list/lady",
        "app_link": "com.jimei.xlmm://app/v1/products/ladylist",
        "pic_link": ""
    }
]

DEFAULT_CHD_POSTER = [
    {
        "subject": ['2折起', '小鹿美美  童装专场'],
        "item_link": "/mall/product/list/child",
        "app_link": "com.jimei.xlmm://app/v1/products/childlist",
        "pic_link": ""
    }
]

def default_wen_poster():
    return json.dumps(DEFAULT_WEN_POSTER, indent=2)

def default_chd_poster():
    return json.dumps(DEFAULT_WEN_POSTER, indent=2)

class GoodShelf(PayBaseModel):
    DEFAULT_WEN_POSTER = DEFAULT_WEN_POSTER
    DEFAULT_CHD_POSTER = DEFAULT_CHD_POSTER

    CATEGORY_INDEX = 'index'
    CATEGORY_JINGPIN = 'jingpin'
    CATEGORY_CHOICES = (
        (CATEGORY_INDEX, u'首页'),
        (CATEGORY_JINGPIN, u'精品汇页面')
    )

    title = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'海报名称')
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES, default=CATEGORY_INDEX, verbose_name=u'海报类型')

    wem_posters = JSONCharMyField(max_length=10240, blank=True,
                                  default=default_wen_poster,
                                  verbose_name=u'女装海报')
    chd_posters = JSONCharMyField(max_length=10240, blank=True,
                                  default=default_chd_poster,
                                  verbose_name=u'童装海报')

    is_active = models.BooleanField(default=True, verbose_name=u'上线')
    active_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'上线日期')

    class Meta:
        db_table = 'flashsale_goodshelf'
        app_label = 'pay'
        verbose_name = u'特卖商品/海报'
        verbose_name_plural = u'特卖商品/海报列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    def get_cat_imgs(self):
        from pms.supplier.models.category import SaleCategory

        cat_list = []
        lv1_categorys = SaleCategory.get_viewable_categorys()\
            .filter(grade=SaleCategory.FIRST_GRADE).order_by('-sort_order')
        cat_values = lv1_categorys.values('cid', 'name', 'cat_pic')

        for cat in cat_values:
            cat_list.append({
                'id': cat['cid'],
                'name': cat['name'],
                'cat_img': cat['cat_pic'],
                'cat_link': 'com.jimei.xlmm://app/v1/products/category?cid={cid}'.format(cid=cat['cid']),
            })

        return cat_list

    def get_posters(self):
        return self.wem_posters + self.chd_posters

    def get_activity(self):
        from flashsale.promotion.apis.activity import get_default_activity
        return get_default_activity()

    def get_current_activitys(self):
        from flashsale.promotion.apis.activity import get_landing_effect_activities
        return get_landing_effect_activities()
