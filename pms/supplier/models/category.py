# -*- coding:utf-8 -*-

from collections import defaultdict

from django.db.models.signals import pre_save, post_save
from django.core.cache import cache
from django.db import models

from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)

def recursive_append_child_salecategorys(node, node_maps):
    copy_node = node.copy()
    child_nodes = node_maps.get(copy_node['cid'])
    copy_node.setdefault('childs', [])
    if not child_nodes:
        return copy_node

    for child_node in child_nodes:
        child_node = recursive_append_child_salecategorys(child_node, node_maps)
        copy_node['childs'].append(child_node)
    return copy_node


def get_salecategory_json_data(salecategory_qs):
    districts = salecategory_qs.order_by('parent_cid', '-sort_order')
    districts_values = districts.values('cid', 'parent_cid', 'name', 'cat_pic', 'grade')

    salecategorys_tree_nodes = defaultdict(list)
    for district in districts_values:
        salecategorys_tree_nodes[district['parent_cid']].append(district)

    node_tree = recursive_append_child_salecategorys({'cid':'0' }, salecategorys_tree_nodes)
    return node_tree.get('childs', [])


def default_salecategory_cid():
    """ 请做异常处理，避免model结构改变时无法migrate """
    try:
        sc = SaleCategory.objects.order_by('-id').first()
    except:
        return None
    if sc:
        return '%d' % (sc.id + 1)
    return '1'


class SaleCategory(BaseModel):
    """ 注意接口使用的类目Id一般是cid,用非外键做查询过滤的时候请使用cid """
    NORMAL = 'normal'
    DELETE = 'delete'

    CAT_STATUS = ((NORMAL, u'正常'),
                  (DELETE, u'未使用'))

    FIRST_GRADE = 1
    CACHE_TIME = 24 * 60 * 60
    CACHE_KEY = 'suppliychain_salesategory_list_key'
    VIEWABLE_CACHE_KEY = 'salesategory_viewable_list_key'
    CATEGORY_ID_FULLNAME_MAP_KEY = 'salecategory_id_fullname_map_key'
    SALEPRODUCT_CATEGORY_CACHE_KEY = 'xlmm_saleproduct_category_cache'
    DELIMITER_CHAR = '-'
    ROOT_ID = '0'

    cid = models.CharField(max_length=32, null=False, blank=False, default=default_salecategory_cid,
                           unique=True, verbose_name=u'类目ID', help_text=u'注意接口使用的类目Id一般是cid')
    parent_cid = models.CharField(max_length=32, null=False, blank=False,
                                  default=ROOT_ID, db_index=True, verbose_name=u'父类目ID')
    name = models.CharField(max_length=64, blank=True, verbose_name=u'类目名')
    cat_pic = models.CharField(max_length=256, blank=True, verbose_name=u'展示图片')

    grade = models.IntegerField(default=1, db_index=True, verbose_name=u'类目等级')
    is_parent = models.BooleanField(default=True, verbose_name=u'父类目')
    sort_order = models.IntegerField(default=0, verbose_name=u'权值')

    is_view = models.BooleanField(default=True, verbose_name=u'是否展示给用户')
    status = models.CharField(max_length=7, choices=CAT_STATUS, default=NORMAL, verbose_name=u'状态')

    class Meta:
        db_table = 'supplychain_sale_category'
        app_label = 'supplier'
        verbose_name = u'特卖/选品类目'
        verbose_name_plural = u'特卖/选品类目列表'

    def __unicode__(self):

        if self.parent_cid == self.ROOT_ID:
            return self.name
        try:
            p_cat = self.__class__.objects.get(cid=self.parent_cid)
        except:
            p_cat = u'--'
        return '%s / %s' % (p_cat, self.name)

    def save(self, *args, **kwargs):
        """ repair cid: [parent_cid]-cid """
        if self.parent_cid != self.ROOT_ID:
            parent_cat = SaleCategory.objects.filter(cid=self.parent_cid).first()
            self.grade = parent_cat.grade + 1
            self.cid   = '%s-%s'%(parent_cat.cid.strip(self.DELIMITER_CHAR),
                                  self.cid.split(self.DELIMITER_CHAR)[-1])
        return super(SaleCategory, self).save(*args, **kwargs)

    @classmethod
    def get_normal_categorys(cls):
        return cls.objects.filter(status=cls.NORMAL)

    @classmethod
    def get_viewable_categorys(cls):
        return cls.objects.filter(status=cls.NORMAL, is_view=True)

    @property
    def full_name(self):
        return self.__unicode__()

    @classmethod
    def get_category_names(cls, cid):
        categories = cache.get(cls.SALEPRODUCT_CATEGORY_CACHE_KEY)
        if not categories:
            categories = {}
            for category in cls.objects.filter(
                    status=u'normal').order_by('created'):
                categories[str(category.id)] = {
                    'cid': str(category.id),
                    'pid': str(category.parent_cid or 0),
                    'name': category.name
                }
            cache.set(cls.SALEPRODUCT_CATEGORY_CACHE_KEY, categories)
        level_1_category_name, level_2_category_name = ('-',) * 2
        category = categories.get(str(cid))
        if category:
            pid = category['pid']
            if not pid:
                level_1_category_name = category['name']
            else:
                level_2_category_name = category['name']
                level_1_category_name = (categories.get(pid) or
                                         {}).get('name') or ''
        return level_1_category_name, level_2_category_name

    def get_firstgrade_category(self):
        if self.grade == self.FIRST_GRADE:
            return self

        parant_cat = SaleCategory.objects.filter(cid=self.parent_cid).first()
        cnt = 0
        while parant_cat and cnt < 10:
            tmp_cat = SaleCategory.objects.filter(cid=parant_cat.parent_cid).first()
            if not tmp_cat:
                return parant_cat
            parant_cat = tmp_cat
            cnt += 1
        return None

    @classmethod
    def latest_version(cls):
        # TODO 此处需要使用cache并考虑invalidate
        version = SaleCategoryVersion.get_latest_version()
        if version:
            return {'version': version.version,
                    'download_url': version.download_url,
                    'sha1': version.sha1}
        return {}

    @classmethod
    def get_salecategory_jsontree(cls):
        cache_value = cache.get(cls.CACHE_KEY)
        if not cache_value:
            cat_qs = SaleCategory.get_normal_categorys()
            cache_value = get_salecategory_json_data(cat_qs)
            cache.set(cls.CACHE_KEY, cache_value, cls.CACHE_TIME)
        return cache_value

    @classmethod
    def get_salecategory_viewable_jsontree(cls):
        cache_value = cache.get(cls.VIEWABLE_CACHE_KEY)
        if not cache_value:
            cat_qs = SaleCategory.get_viewable_categorys()
            cache_value = get_salecategory_json_data(cat_qs)
            cache.set(cls.VIEWABLE_CACHE_KEY, cache_value, cls.CACHE_TIME)
        return cache_value

    @classmethod
    def get_salecategory_fullnamemap(cls):
        cache_value = cache.get(cls.CATEGORY_ID_FULLNAME_MAP_KEY)
        if not cache_value:
            cid_fullname_dict = {}
            cat_cid_names = cls.objects.order_by('grade').values('id', 'cid', 'parent_cid', 'name')
            cid_id_maps = dict([(item['cid'], item['id'])  for item in cat_cid_names])
            for cat_item in cat_cid_names:
                cat_name = cat_item['name']
                if cat_item['parent_cid'] in cid_fullname_dict:
                    cat_name = '%s / %s'%(cid_fullname_dict[cat_item['parent_cid']], cat_name)

                cid_fullname_dict[cat_item['cid']] = cat_name

            cache_value = dict([(cid_id_maps[k], v) for k ,v in cid_fullname_dict.iteritems()])
            cache.set(cls.CATEGORY_ID_FULLNAME_MAP_KEY, cache_value, 24 * 3600)
        return cache_value

    def get_product_category(self):
        """ 产品类别map """
        from shopback.categorys.models import ProductCategory
        pcs = ProductCategory.objects.filter(status=ProductCategory.NORMAL)
        pcs_full_names = [{pc.cid: [i.strip() for i in pc.__unicode__().split('/')[-2:] if i.strip() != u'小鹿美美']} for pc in pcs]
        self_names = [x.strip() for x in self.full_name.split('/')]
        for pcnames in pcs_full_names:
            if self_names == pcnames.values()[0]:
                self_cat = pcs.filter(cid=pcnames.keys()[0]).first()
                if self_cat:
                    return self_cat

        cur_cat = pcs.get(name=u'小鹿美美')
        for cname in self_names:
            cur_cat, state = ProductCategory.objects.get_or_create(parent_cid=cur_cat.cid, name=cname)
        return cur_cat


def invalid_salecategory_data_cache(sender, instance, created, **kwargs):
    logger.info('salecategory: invalid cachekey %s'% SaleCategory.CACHE_KEY)
    cache.delete(SaleCategory.CACHE_KEY)
    cache.delete(SaleCategory.VIEWABLE_CACHE_KEY)
    cache.delete(SaleCategory.SALEPRODUCT_CATEGORY_CACHE_KEY)
    cache.delete(SaleCategory.CATEGORY_ID_FULLNAME_MAP_KEY)

post_save.connect(invalid_salecategory_data_cache,
                  sender=SaleCategory,
                  dispatch_uid='post_save_invalid_salecategory_data_cache')


class SaleCategoryVersion(BaseModel):

    version = models.CharField(max_length=32, unique=True, verbose_name=u'版本号', help_text=u'需填写')
    download_url = models.CharField(max_length=256, blank=True, verbose_name=u'下载链接', help_text=u'不用填写,第二次保存时会自动生成')
    sha1 = models.CharField(max_length=128, blank=True, verbose_name=u'sha1值', help_text=u'不用填写,第二次保存时会自动生成')
    memo = models.TextField(blank=True, verbose_name=u'备注', help_text=u'需填写')
    status = models.BooleanField(default=False, verbose_name=u'生效', help_text=u'需勾选,表示需要马上更新')

    class Meta:
        db_table = 'supplychain_salecategory_version'
        app_label = 'supplier'
        verbose_name = u'特卖类目版本'
        verbose_name_plural = u'特卖类目版本更新列表'

    def __unicode__(self):
        return '<%s, %s>' % (self.id, self.version)

    def gen_filepath(self):
        return 'category/xiaolumm-category-%s.json'%self.version

    @classmethod
    def get_latest_version(cls):
        latest_version = cls.objects.filter(status=True).order_by('-created').first()
        return latest_version
