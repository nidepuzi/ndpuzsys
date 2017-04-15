# coding=utf-8
__ALL__ = [
    'get_default_activity',
    'get_activity_by_id',
    'get_effect_activitys',
    'get_mama_effect_activities',
    'get_landing_effect_activitys',
    'create_activity',
    'update_activity',
    'get_activity_pro_by_id',
    'get_activity_pros_by_activity_id',
    'create_activity_pro',
    'create_activity_pros_by_schedule_id',
    'update_activity_pro',
    'delete_activity_pro'
]
import datetime
from ..models import ActivityEntry, ActivityProduct
from ..deps import get_schedule_products_by_schedule_id, get_modelproduct_by_id


def get_activity_by_id(id):
    # type: (int) -> ActivityEntry
    return ActivityEntry.objects.get(id=id)


def get_default_activity():
    # type: () -> Optional[ActivityEntry]
    """获取默认有效的活动（排除了代理活动　和　品牌专场）
    """
    return ActivityEntry.objects.default_activities().first()


def get_effect_activities(time=None):
    # type: (datetime.datetime) -> List[ActivityEntry]
    """ 根据时间获取活动列表
    """
    return ActivityEntry.objects.effect_activities(time)


def get_mama_effect_activities():
    # type: () -> List[ActivityEntry]
    """获取有效的妈妈活动列表
    """
    return ActivityEntry.objects.mama_effect_activities()


def get_landing_effect_activities():
    # type: () -> List[ActivityEntry]
    """ 根据时间获取活动列表app首页展示 """
    return ActivityEntry.objects.sale_home_page_activities()

def get_jingpin_effect_activities():
    return ActivityEntry.objects.jingpin_page_activities();


def _validate_start_end_time(start_time, end_time):
    # type: (datetime.datetime, datetime.datetime) -> None
    """时间校验
    """
    now = datetime.datetime.now()
    if not start_time < end_time:
        raise Exception(u'活动开始和结束时间设置错误!')
    if not now < end_time:
        raise Exception(u'活动结束时间应该大于当前时间!')
    return


class Activity(object):  # 特卖商城活动(pay.models.ActivityEntry)
    def __init__(self, title, act_type, start_time, end_time,
                 act_img='', act_logo='', act_link='', mask_link='', act_applink='', share_icon='', share_link='',
                 order_val=0, extras='', is_active=False, login_required=False, act_desc=''):
        self.title = title  # 活动/品牌名称
        self.act_type = act_type  # 活动类型
        self.start_time = start_time  # 结束时间
        self.end_time = end_time  # 开始时间
        self.act_img = act_img  # 活动入口图片
        self.act_logo = act_logo  # 品牌LOGO
        self.act_link = act_link  # 活动链接
        self.mask_link = mask_link  # 活动弹窗提示图
        self.act_applink = act_applink  # 活动APP协议链接
        self.share_icon = share_icon  # 活动分享图片
        self.share_link = share_link  # 活动分享链接
        self.order_val = order_val  # 排序值
        self.extras = extras  # 活动数据
        self.is_active = is_active  # 上线
        self.login_required = login_required  # 需要登陆
        self.act_desc = act_desc  # 活动描述

    def create(self):
        # type: () -> ActivityEntry
        """保存到活动记录到数据库
        """
        from flashsale.promotion.models import ActivityEntry

        activity = ActivityEntry(
            title=self.title,
            act_type=self.act_type,
            start_time=self.start_time,
            end_time=self.end_time,
            act_img=self.act_img,
            act_logo=self.act_logo,
            act_link=self.act_link,
            mask_link=self.mask_link,
            act_applink=self.act_applink,
            share_icon=self.share_icon,
            share_link=self.share_link,
            order_val=self.order_val,
            extras=self.extras,
            is_active=self.is_active,
            login_required=self.login_required,
            act_desc=self.act_desc,
        )
        activity.save()
        return activity


def create_activity(title, act_type, start_time, end_time, **kwargs):
    # type: (text_type, text_type, datetime.datetime, datetime.datetime, **Any) -> ActivityEntry
    """创建活动
    """
    if act_type == ActivityEntry.ACT_TOPIC and kwargs.has_key('act_link'):
        # http://m.xiaolumeimei.com/mall/activity/topTen/model/2?id=264 # 专题类型活动链接固定格式
        kwargs.pop('act_link')  # 去除传来的act_link 如果有的话
    activity = Activity(title=title,
                        act_type=act_type,
                        start_time=start_time,
                        end_time=end_time)
    for k, v in kwargs.iteritems():
        if hasattr(activity, k) and getattr(activity, k) != v:
            setattr(activity, k, v)
    _validate_start_end_time(start_time, end_time)
    activity = activity.create()
    if act_type == ActivityEntry.ACT_TOPIC:
        activity.act_link = 'https://m.xiaolumeimei.com/mall/activity/topTen/model/2?id={0}'.format(activity.id)
    activity.share_link = 'https://m.xiaolumeimei.com/m/{mama_id}?next=' + activity.act_link
    activity.order_val = activity.id  # 默认排序值是当前id
    activity.save()
    return activity


def update_activity(id, **kwargs):
    # type: (int, **Any) -> ActivityEntry
    """更新活动
    """
    activity = get_activity_by_id(id=id)
    start_time, end_time = kwargs.get('start_time'), kwargs.get('end_time')
    act_type = kwargs.get('act_type')
    if act_type == ActivityEntry.ACT_TOPIC:
        if kwargs.has_key('act_link'):
            kwargs.pop('act_link')  # 在创建的时候已经填写过act_link了不需要重新填写
    else:
        if kwargs.has_key('act_link'):
            kwargs['share_link'] = 'https://m.xiaolumeimei.com/m/{mama_id}?next=' + kwargs['act_link']
    for k, v in kwargs.iteritems():
        if hasattr(activity, k) and getattr(activity, k) != v:
            setattr(activity, k, v)
    _validate_start_end_time(start_time, end_time)
    activity.save()
    return activity


def get_activity_pro_by_id(id):
    # type: (int) -> ActivityProduct
    return ActivityProduct.objects.get(id=id)


def get_activity_pros_by_activity_id(activity_id):
    # type: (int) -> List[ActivityProduct]
    """根据活动id获取相关的产品
    """
    return ActivityProduct.objects.pros_by_activity_id(activity_id).order_by('location_id')


class ActivityPro(object):  # 活动更随的产品（包含图片）
    def __init__(self, activity_id, product_img, location_id=1, product_name='', pic_type=6, model_id=0, jump_url=''):
        self.activity_id = activity_id
        self.product_name = product_name
        self.product_img = product_img
        self.pic_type = pic_type
        self.location_id = location_id
        self.model_id = model_id
        self.jump_url = jump_url

    def create(self):
        ap = ActivityProduct(
            activity_id=self.activity_id,
            model_id=self.model_id,
            product_name=self.product_name,
            product_img=self.product_img,
            location_id=self.location_id,
            pic_type=self.pic_type,
            jump_url=self.jump_url,
        )
        ap.save()
        return ap


def _set_footer_pic_location(activity_id, location_id):
    # type: (int, int) -> None
    """挪动底部图片
    """
    pros = get_activity_pros_by_activity_id(activity_id).filter(pic_type=ActivityProduct.FOOTER_PIC_TYPE)
    location_id += 1
    for p in pros:
        p.location_id = location_id
        location_id += 1
        p.save()


def create_activity_pro(activity_id, product_img, **kwargs):
    # type: (int, text_type, **Any)
    """创建活动商品
    """
    foot_share_img = 'http://img.xiaolumeimei.com/top101476965460253.jpg'
    pros = get_activity_pros_by_activity_id(activity_id)
    pic_type = kwargs.get('pic_type')
    if pic_type == ActivityProduct.BANNER_PIC_TYPE:  # 头图
        banner = pros.filter(pic_type=ActivityProduct.BANNER_PIC_TYPE).first()
        if banner:
            location_id = banner.location_id - 1  # banner图片向前递减
        else:
            location_id = 1
    else:
        try:
            latest_pro = pros.latest('location_id')
        except:
            latest_pro = None
        location_id = latest_pro.location_id + 1 if latest_pro else 2
        # 如果是非底部图片　当前活动有底部图片则要挪动底部图片到底部
        _set_footer_pic_location(activity_id, location_id)
    if pic_type and pic_type == ActivityProduct.FOOTER_PIC_TYPE:  # 头图
        product_img = foot_share_img
    location_id = kwargs.pop('location_id') if kwargs.has_key('location_id') else location_id
    ap = ActivityPro(
        activity_id=activity_id,
        product_img=product_img,
    )
    kwargs['location_id'] = location_id
    for k, v in kwargs.iteritems():
        if hasattr(ap, k) and getattr(ap, k) != v:
            setattr(ap, k, v)
    ap = ap.create()
    return ap


def update_activity_pro(id, **kwargs):
    # type: () -> ActivityProduct
    """更新活动产品
    """
    ap = get_activity_pro_by_id(id)
    head_img_url = None
    for k, v in kwargs.iteritems():
        if k == 'pic_type' and v == ActivityProduct.GOODS_VERTICAL_PIC_TYPE and ap.model_id:  # 图片竖放 有款式　则选头图
            modelproduct = get_modelproduct_by_id(ap.model_id)
            head_img_url = modelproduct.head_img_url if modelproduct else ''
        if hasattr(ap, k) and getattr(ap, k) != v:
            setattr(ap, k, v)
    if head_img_url:
        ap.product_img = head_img_url
    ap = ap.save()
    return ap

def change_activitygoods_position(id ,**kwargs):
    """修改活动产品位置"""
    direction = kwargs.get("direction")
    distance = kwargs.get("distance")
    activity_entry_id = kwargs.get("activity_entry_id")
    activity_products = ActivityProduct.objects.filter(activity_id=activity_entry_id)
    activity_product = ActivityProduct.objects.filter(id=id).first()
    if direction == 'minus':
        small_activity_products = [i for i in activity_products if i.location_id < activity_product.location_id]
        if not small_activity_products:
            # print "这是最小的位置了"
            return False
        bigger_activity_products = [i for i in small_activity_products if
                                     i.location_id >= activity_product.location_id - int(distance)]
        for i in bigger_activity_products:
            i.location_id += 1
            i.save(update_fields=['location_id'])
        activity_product.location_id = activity_product.location_id - int(distance)
        activity_product.save(update_fields=['location_id'])
        return True
    if direction == 'plus':
        bigger_activity_products = [i for i in activity_products if i.location_id > activity_product.location_id]
        if not bigger_activity_products:
            # print "这是最大的位置了"
            return False
        smaller_activity_products = [i for i in bigger_activity_products if
                                     i.location_id <= activity_product.location_id + int(distance)]
        for i in smaller_activity_products:
            i.location_id -= 1
            i.save(update_fields=['location_id'])
        activity_product.location_id = activity_product.location_id + int(distance)
        activity_product.save(update_fields=['location_id'])
        return True
    return False


def delete_activity_pro(id):
    # type: () -> ActivityProduct
    """删除活动产品
    """
    ap = get_activity_pro_by_id(id)
    ap.delete()
    return True


def create_activity_pros_by_schedule_id(activity_id, schedule_id):
    # type: (int, int) -> List[Optional[ActivityProduct]]
    """更具活动id和排期id创建活动产品
    """
    activity = get_activity_by_id(activity_id)
    schedule_pros = get_schedule_products_by_schedule_id(int(schedule_id)).order_by('order_weight')
    aps = []
    ac_model_ids = [i['model_id'] for i in activity.activity_products.values('model_id')]
    location_id = 2
    schedule_model_ids = []
    for pro in schedule_pros:
        modelproduct = pro.modelproduct
        if modelproduct:
            schedule_model_ids.append(modelproduct.id)  # 待用
            if modelproduct.id not in ac_model_ids:  # 存在款式并且没有设置在本活动中则添加到本活动中
                kwargs = {
                    'product_name': modelproduct.name,
                    'model_id': modelproduct.id,
                    'location_id': location_id,
                }
                ap = create_activity_pro(activity_id, modelproduct.head_img_url, **kwargs)
                aps.append(ap)
        location_id += 1
    # 纯粹的产品类型记录
    pure_acps = activity.activity_products.filter(pic_type__in=[ActivityProduct.GOODS_HORIZEN_PIC_TYPE,
                                                                ActivityProduct.GOODS_VERTICAL_PIC_TYPE])
    pure_model_ids = [p['model_id'] for p in pure_acps.values('model_id')]
    xx = set(pure_model_ids) - set(schedule_model_ids)  # 在活动里面的产品　但是　不在　排期里面的　删除掉
    activity.activity_products.filter(model_id__in=xx).delete()
    return aps

