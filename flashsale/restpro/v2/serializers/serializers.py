# coding=utf-8
import collections
import datetime
import random
import time
from django.conf import settings
from django.db.models import Sum, Count
from shopback.trades.models import PackageSkuItem

from rest_framework import serializers

from flashsale.xiaolumm.models.models_fortune import (
    MamaFortune,
    CarryRecord,
    OrderCarry,
    AwardCarry,
    ClickCarry,
    ActiveValue,
    ReferalRelationship,
    GroupRelationship,
    UniqueVisitor,
    DailyStats,
)
from shopback.items.models import Product
from flashsale.pay.models import ProductSku
from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    SaleRefund,
    Productdetail,
    ModelProduct,
    ShoppingCart,
    Customer,
    Register,
    GoodShelf,
    CustomShare,
    UserBudget,
    District,
    UserAddress,
    IntegralLog,
    Integral,
    BudgetLog,
    FaqMainCategory,
    FaqsDetailCategory,
    SaleFaq,
    CustomerShops,
    CuShopPros,
    UserSearchHistory,
)
from flashsale.promotion.models import ActivityEntry, ActivityProduct
from shopback.logistics.models import LogisticsCompany
from shopback.trades.models import TradeWuliu, PackageOrder
from shopback.categorys.models import ProductCategory
from shopapp.weixin.models import WXOrder
from pms.supplier.models import SaleProduct, HotProduct
from shopback.refunds.models_refund_rate import ProRefunRcord

from flashsale.xiaolumm.models.models_advertis import MamaVebViewConf
from flashsale.xiaolumm.models import XiaoluMama, CarryLog, CashOut, MamaCarryTotal, XlmmFans, MamaMissionRecord
from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver
from flashsale.xiaolumm.models.models_fortune import MAMA_FORTUNE_HISTORY_LAST_DAY
from flashsale.xiaolumm.models import XiaoluCoinLog

from flashsale.coupon.models import OrderShareCoupon
from flashsale.clickcount.models import ClickCount, Clicks
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.promotion.models import AppDownloadRecord

from flashsale.promotion.models import XLSampleSku, XLSampleApply, XLFreeSample, XLSampleOrder, XLInviteCode
from flashsale.apprelease.models import AppRelease
from flashsale.restpro import constants

class MamaFortuneBriefSerializer(serializers.ModelSerializer):
    cash_value = serializers.FloatField(source='cash_num_display', read_only=True)
    carry_value = serializers.FloatField(source='cash_total_display', read_only=True)
    class Meta:
        model = MamaFortune
        fields = ('mama_id', 'cash_value', 'carry_value')
        
        
class MamaFortuneSerializer(serializers.ModelSerializer):
    cash_value = serializers.FloatField(source='cash_num_display', read_only=True)
    carry_value = serializers.FloatField(source='cash_total_display', read_only=True)
    # carry_value = serializers.SerializerMethodField('carry_num_display_new', read_only=True)
    extra_info = serializers.SerializerMethodField(read_only=True)
    extra_figures = serializers.SerializerMethodField()
    current_dp_turns_num = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MamaFortune
        fields = ('mama_id', 'mama_name', 'mama_level', 'mama_level_display', 'cash_value',
                  'fans_num', 'invite_num', 'order_num', 'carry_value', 'active_value_num',
                  'carry_pending_display', 'carry_confirmed_display', 'carry_cashout_display',
                  'mama_event_link', 'history_last_day', 'today_visitor_num', 'modified', 'created',
                  "extra_info", 'current_dp_turns_num', 'extra_figures')

    def carry_num_display_new(self, obj):
        """ 累计收益数 """
        his_confirmed_cash_out = CashOut.objects.filter(xlmm=obj.mama_id, status=CashOut.APPROVED,
                                                        approve_time__lt=MAMA_FORTUNE_HISTORY_LAST_DAY).aggregate(
            total=Sum('value')).get('total') or 0
        total = obj.carry_num_display() + float(his_confirmed_cash_out * 0.01)
        return float('%.2f' % (total))

    def get_extra_info(self, obj):
        customer = self.context['customer']
        xlmm = self.context['xlmm']
        invite_url = constants.MAMA_INVITE_AGENTCY_URL.format(**{'site_url': settings.M_SITE_URL})
        surplus_days = (xlmm.renew_time.date() - datetime.date.today()).days if xlmm.renew_time else 0
        surplus_days = max(surplus_days, 0)
        next_level_exam_url = 'http://m.xiaolumeimei.com/mall/activity/exam'
        xlmm_next_level = xlmm.next_agencylevel_info()
        could_cash_out = 1
        tmp_des = []
        if obj.cash_num_display() < 100.0:
            tmp_des.append(u'余额不足')
            could_cash_out = 0
        # if obj.active_value_num < 100:
        #     tmp_des.append(u'活跃度不足')
        #     could_cash_out = 0
        if xlmm.status != XiaoluMama.EFFECT:
            could_cash_out = 0
        cashout_reason = u' '.join(tmp_des) + u'不能提现'
        total_rank = MamaCarryTotal.get_by_mama_id(xlmm.id).total_rank if MamaCarryTotal.get_by_mama_id(xlmm.id) else 0
        his_confirmed_cash_out = CashOut.objects.filter(xlmm=xlmm.id, status=CashOut.APPROVED,
                                                        approve_time__lt=MAMA_FORTUNE_HISTORY_LAST_DAY).aggregate(
            total=Sum('value')).get('total') or 0
        his_confirmed_cash_out = float(his_confirmed_cash_out * 0.01)

        return {
            "total_rank": total_rank,
            "invite_url": invite_url,
            "agencylevel": xlmm.agencylevel,
            "agencylevel_display": xlmm.get_agencylevel_display(),
            "surplus_days": surplus_days,
            "next_agencylevel": xlmm_next_level[0],
            "next_agencylevel_display": xlmm_next_level[1],
            "next_level_exam_url": next_level_exam_url,
            "thumbnail": customer.thumbnail if customer else '',
            "could_cash_out": could_cash_out,
            "cashout_reason": cashout_reason,
            "his_confirmed_cash_out": his_confirmed_cash_out
        }

    def get_extra_figures(self, obj):
        """
        本周累计收益、本周排名、任务完成百分比、个人总体排名、团队总体排名
        """
        default = collections.defaultdict(week_duration_total=0.0, week_duration_rank=0,
                                          personal_total_rank=0, team_total_rank=0,
                                          task_percentage=0.0, today_carry_record=0.0)
        week_mama_carry = obj.week_mama_carry
        week_mama_team_carry = obj.week_mama_team_carry
        mama_carry_records = CarryRecord.objects.filter(mama_id=obj.mama_id).exclude(status=CarryRecord.CANCEL)
        today_mama_carry_records = mama_carry_records.filter(date_field=datetime.date.today())
        today_carry_record_num = today_mama_carry_records.aggregate(t=Sum('carry_num')).get('t') or 0.0
        today_carry_record = round(today_carry_record_num / 100.0, 2) if today_carry_record_num > 0 else 0

        year_week = time.strftime("%Y-%W")
        missions_counts = MamaMissionRecord.mama_mission(obj.mama_id, year_week=year_week) \
            .values('status').annotate(status_count=Count('id'))
        task_percentage = 0
        if missions_counts:
            total_count = 0
            finished = 0
            for missions_count in missions_counts:
                total_count += missions_count['status_count']
                if missions_count['status'] == MamaMissionRecord.FINISHED:  # 已完成的
                    finished += missions_count['status_count']
            task_percentage = round(finished / float(total_count), 3) if total_count else 0
        default.update({'task_percentage': task_percentage})

        default.update({'today_carry_record': today_carry_record})
        if not (week_mama_carry and week_mama_team_carry):
            default.update({'today_carry_record': 0.0})
            return default
        week_duration_total = week_mama_carry.duration_total /100.0 if week_mama_carry.duration_total else 0.0
        default.update({'week_duration_total': week_duration_total,
                        'week_duration_rank': week_mama_carry.duration_rank,
                        'personal_total_rank': week_mama_carry.total_rank,
                        'team_total_rank': week_mama_team_carry.total_rank})
        return default

    def get_current_dp_turns_num(self, obj):
        # type: (MamaFortune) -> int
        """返回每日推送当前已经推送的轮数
        """
        from flashsale.xiaolumm.models import NinePicAdver
        now = datetime.datetime.now()
        init_time = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        return NinePicAdver.objects.filter(start_time__gte=init_time, start_time__lte=now).count()


class CarryRecordSerializer(serializers.ModelSerializer):
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = CarryRecord
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_num', 'carry_type', 'carry_type_name', "carry_description",
                  'status', 'status_display', 'today_carry', 'date_field',
                  'modified', 'created')


class OrderCarrySerializer(serializers.ModelSerializer):
    order_value = serializers.FloatField(source='order_value_display', read_only=True)
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    contributor_nick = serializers.CharField(source='contributor_nick_display', read_only=True)
    packetid = serializers.SerializerMethodField()
    company_code = serializers.SerializerMethodField()

    class Meta:
        model = OrderCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'order_id', 'order_value', 'carry_value', 'carry_num', 'carry_type',
                  'carry_type_name', 'sku_name', 'sku_img', 'contributor_nick', "carry_description",
                  'contributor_img', 'contributor_id', 'agency_level', 'carry_plan_name',
                  'date_field', 'status', 'status_display', 'modified', 'created', 'today_carry',
                  'packetid', 'company_code')

    def get_packetid(self, obj):
        order = PackageSkuItem.objects.filter(oid=obj.order_id).first()
        if not order:
            return ''
        return order.out_sid.strip()

    def get_company_code(self, obj):
        order = PackageSkuItem.objects.filter(oid=obj.order_id).first()
        if not order:
            return ''
        return order.logistics_company_code


class AwardCarrySerializer(serializers.ModelSerializer):
    carry_num = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)
    carry_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = AwardCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'carry_value', 'carry_num', 'carry_type', 'carry_type_name', 'contributor_nick',
                  "carry_description", 'contributor_img', 'contributor_mama_id', 'carry_plan_name',
                  'status', 'status_display', 'today_carry', 'date_field', 'modified', 'created')


class ClickCarrySerializer(serializers.ModelSerializer):
    init_click_price = serializers.FloatField(source='init_click_price_display', read_only=True)
    confirmed_click_price = serializers.FloatField(source='confirmed_click_price_display', read_only=True)
    total_value = serializers.FloatField(source='total_value_display', read_only=True)
    carry_value = serializers.FloatField(source='total_value_display', read_only=True)
    carry_num = serializers.FloatField(source='total_value_display', read_only=True)

    class Meta:
        model = ClickCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'click_num', 'init_order_num', 'init_click_price',
                  'init_click_limit', 'confirmed_order_num', 'confirmed_click_price',
                  'confirmed_click_limit', 'total_value', 'carry_value', 'carry_num', 'carry_description',
                  'carry_plan_name', 'date_field', 'uni_key', 'status', 'status_display',
                  'today_carry', 'modified', 'created')


class ActiveValueSerializer(serializers.ModelSerializer):
    value_type_name = serializers.CharField(read_only=True)

    class Meta:
        model = ActiveValue
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('mama_id', 'value_num', 'value_type', 'value_type_name', 'uni_key', 'value_description',
                  'date_field', 'status', 'status_display', 'today_carry', 'modified', 'created')


class AwardCarry4ReferalRelationshipSerializer(serializers.ModelSerializer):
    carry_value = serializers.FloatField(source='carry_num_display', read_only=True)

    class Meta:
        model = AwardCarry
        extra_kwargs = {'today_carry': {'read_only': True}}
        fields = ('carry_value', 'carry_type', 'carry_type_name', 'status',
                  'status_display')


class ReferalRelationshipSerializer(serializers.ModelSerializer):
    referal_to_mama_nick = serializers.CharField(source='referal_to_mama_nick_display', read_only=True)
    referal_award = AwardCarry4ReferalRelationshipSerializer(source='get_referal_award', read_only=True)

    class Meta:
        model = ReferalRelationship
        fields = ('referal_from_mama_id', 'referal_to_mama_id', 'referal_to_mama_nick',
                  'referal_to_mama_img', 'referal_award', 'modified', 'created')


class GroupRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRelationship
        fields = ('leader_mama_id', 'referal_from_mama_id', 'member_mama_id', 'member_mama_nick',
                  'member_mama_img', 'modified', 'created')


class UniqueVisitorSerializer(serializers.ModelSerializer):
    visitor_nick = serializers.CharField(source='nick_display', read_only=True)

    class Meta:
        model = UniqueVisitor
        fields = ('mama_id', 'visitor_nick', 'visitor_img', 'visitor_description', 'uni_key', 'modified', 'created')


class XlmmFansSerializer(serializers.ModelSerializer):
    fans_nick = serializers.CharField(source='nick_display', read_only=True)
    fans_mobile = serializers.SerializerMethodField(method_name='fans_mobile_display', read_only=True)

    class Meta:
        model = XlmmFans
        fields = ('fans_nick', 'fans_thumbnail', 'fans_description', 'fans_mobile', 'created')

    def fans_mobile_display(self, obj):
        fans_customer = obj.getCustomer()
        m = fans_customer.mobile if fans_customer else ''
        mobile = m.strip()
        if len(mobile) == 11:
            m = ''.join([m.strip()[0:3], '****', m.strip()[7::]])
        # else:
        #     m = u'异常用户'
        return m


class DailyStatsSerializer(serializers.ModelSerializer):
    order_num = serializers.IntegerField(source='today_order_num', read_only=True)
    visitor_num = serializers.IntegerField(source='today_visitor_num', read_only=True)
    carry = serializers.FloatField(source='today_carry_num_display', read_only=True)
    today_carry_num = serializers.FloatField(source='today_carry_num_display', read_only=True)

    class Meta:
        model = DailyStats
        fields = ('id', 'order_num', 'visitor_num', 'carry', 'today_carry_num', 'mama_id',
                  'today_visitor_num', 'today_order_num', 'today_carry_num', 'today_active_value',
                  'date_field', 'status')


class ProductSimpleSerializerV2(serializers.ModelSerializer):
    level_info = serializers.SerializerMethodField('agencylevel_info', read_only=True)
    shop_product_num = serializers.SerializerMethodField('shop_products_info', read_only=True)

    class Meta:
        model = Product
        extra_kwargs = {'in_customer_shop': {}, 'shop_product_num': {}}
        fields = ('id', 'pic_path', 'name', 'std_sale_price', 'agent_price', 'remain_num',
                  'in_customer_shop', 'shop_product_num', 'model_id',
                  "level_info")


    def mama_agency_level_info(self, xlmm):
        default_info = collections.defaultdict(agencylevel=XiaoluMama.INNER_LEVEL,
                                               agencylevel_desc=XiaoluMama.AGENCY_LEVEL[0][1],
                                               next_agencylevel=XiaoluMama.A_LEVEL,
                                               next_agencylevel_desc=XiaoluMama.AGENCY_LEVEL[2][1])

        if not xlmm:
            return default_info
        next_agencylevel, next_agencylevel_desc = xlmm.next_agencylevel_info()
        default_info.update({
            "agencylevel": xlmm.agencylevel,
            "agencylevel_desc": xlmm.get_agencylevel_display(),
            "next_agencylevel": next_agencylevel,
            "next_agencylevel_desc": next_agencylevel_desc
        })
        return default_info

    def agencylevel_info(self, obj):
        xlmm = self.context['xlmm']
        info = self.mama_agency_level_info(xlmm)
        sale_num = obj.remain_num * 19 + random.choice(xrange(19))
        sale_num_des = '{0}人在卖'.format(sale_num)

        info.update({
            "sale_num": sale_num,
            "sale_num_des": sale_num_des,
            "rebet_amount": obj.rebet_amount,
            "rebet_amount_des": obj.rebet_amount_des,
            "next_rebet_amount": obj.next_rebet_amount,
            "next_rebet_amount_des": obj.next_rebet_amount_des
        })
        return info

    def shop_products_info(self, obj):
        shop_products_num = self.context['shop_product_num']
        return shop_products_num


class AppDownloadRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppDownloadRecord
        fields = ('headimgurl', 'nick', 'mobile', 'note', 'modified', 'created')


class RegisterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Register
        fields = ('id', 'vmobile')


class XiaoluMamaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = XiaoluMama
        fields = ('id', 'cash', 'agencylevel', 'created', 'status')


class UserBudgetSerialize(serializers.HyperlinkedModelSerializer):
    budget_cash = serializers.FloatField(source='get_amount_display', read_only=True)
    is_cash_out = serializers.IntegerField(source='is_could_cashout', read_only=True)

    class Meta:
        model = UserBudget
        fields = ('budget_cash', 'is_cash_out')


class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:customer-detail')
    user_id = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    xiaolumm = XiaoluMamaSerializer(source='getXiaolumm', read_only=True)
    user_budget = UserBudgetSerialize(source='getBudget', read_only=True)
    has_usable_password = serializers.BooleanField(source='user.has_usable_password', read_only=True)
    has_password = serializers.BooleanField(source='has_user_password', read_only=True)
    is_attention_public = serializers.IntegerField(source='is_attention_wx_public', read_only=True)

    coupon_num = serializers.IntegerField(source='get_coupon_num', read_only=True)
    waitpay_num = serializers.IntegerField(source='get_waitpay_num', read_only=True)
    waitgoods_num = serializers.IntegerField(source='get_waitgoods_num', read_only=True)
    refunds_num = serializers.IntegerField(source='get_refunds_num', read_only=True)

    class Meta:
        model = Customer
        fields = ('id', 'url', 'user_id', 'username', 'nick', 'mobile', 'email', 'phone',
                  'thumbnail', 'status', 'created', 'modified', 'xiaolumm', 'has_usable_password', 'has_password',
                  'user_budget', 'is_attention_public', 'coupon_num', 'waitpay_num', 'waitgoods_num', 'refunds_num')


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('cid', 'parent_cid', 'name', 'status', 'sort_order')


class ProductSkuSerializer(serializers.ModelSerializer):
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)

    class Meta:
        model = ProductSku
        fields = ('id', 'outer_id', 'name', 'remain_num', 'size_of_sku', 'is_saleout', 'std_sale_price', 'agent_price')

class JSONParseField(serializers.Field):
    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        return data


class JsonListField(serializers.Field):
    def to_representation(self, obj):
        return [s.strip() for s in obj.split() if s.startswith(('http://', 'https://'))]

    def to_internal_value(self, data):
        return data


class ProductdetailSerializer(serializers.ModelSerializer):
    head_imgs = JsonListField(read_only=True, required=False)
    content_imgs = JsonListField(read_only=True, required=False)

    class Meta:
        model = Productdetail
        fields = ('head_imgs', 'content_imgs', 'mama_discount', 'is_recommend',
                  'buy_limit', 'per_limit', 'mama_rebeta', 'material', 'wash_instructions', 'note', 'color')


class ModelProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    head_imgs = JsonListField(read_only=True, required=False)
    content_imgs = JsonListField(read_only=True, required=False)
    is_single_spec = serializers.BooleanField(read_only=True)
    is_sale_out = serializers.BooleanField(read_only=True)
    buy_limit = serializers.SerializerMethodField()
    per_limit = serializers.SerializerMethodField()

    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'head_imgs', 'content_imgs', 'is_single_spec', 'is_sale_out', 'buy_limit', 'per_limit', 'extras')

    def get_buy_limit(self, obj):
        return False

    def get_per_limit(self, obj):
        return 3


class SimpleModelProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    is_single_spec = serializers.BooleanField(read_only=True)
    is_sale_out = serializers.BooleanField(read_only=True)
    head_imgs = serializers.SerializerMethodField()
    content_imgs = serializers.SerializerMethodField()
    buy_limit = serializers.SerializerMethodField()
    per_limit = serializers.SerializerMethodField()

    class Meta:
        model = ModelProduct
        fields = ('id', 'name', 'is_single_spec', 'is_sale_out', 'head_imgs', 'content_imgs', 'buy_limit', 'per_limit')

    def get_buy_limit(self, obj):
        return False

    def get_per_limit(self, obj):
        return 3

    def get_head_imgs(self, obj):
        return []

    def get_content_imgs(self, obj):
        return []


class CreateModelProductSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    extras = serializers.JSONField()
    is_onsale = serializers.BooleanField(required=False)
    is_teambuy = serializers.BooleanField(required=False)
    is_recommend = serializers.BooleanField(required=False)
    is_topic = serializers.BooleanField(required=False)
    is_flatten = serializers.BooleanField(required=False)
    is_boutique = serializers.BooleanField(required=False)
    is_outside = serializers.BooleanField(required=False)
    product_id = serializers.IntegerField()
    teambuy_price = serializers.IntegerField(required=False)
    teambuy_person_num = serializers.IntegerField(required=False)
    # class Meta:
    #     model = ModelProduct
    #     fields = ('product_id', 'name', 'extras')

    def save(self, data, user, instance=None):
        product = Product.objects.get(id=data.get('product_id'))
        if instance:
            instance.name = data.get('name', product.name)
            instance.extras['new_properties'] = data.get('extras', {}).get('new_properties', [])
            instance.extras['sources'] = data.get('extras', {}).get('sources', [])
            instance.is_onsale = bool(data.get('is_onsale'))
            instance.is_teambuy = bool(data.get('is_teambuy'))
            instance.is_recommend = bool(data.get('is_recommend'))
            instance.is_topic = bool(data.get('is_topic'))
            instance.is_flatten = bool(data.get('is_flatten'))
            instance.is_boutique = bool(data.get('is_boutique'))
            instance.is_outside = bool(data.get('is_outside'))
            if instance.is_teambuy:
                instance.teambuy_price = int(data.get('teambuy_price', 0))
                instance.teambuy_person_num = int(data.get('teambuy_person_num', 0))
            if int(data.get('is_outside', 0)):
                instance.set_product_source_type(3)
            instance.save()
            instance.set_lowest_price()
            instance.set_title_imgs_key()
            instance.set_title_imgs_values()
            try:
                instance.salecategory = product.category.get_sale_category()
            except:
                pass
            instance.save()
            instance.set_sale_product()
            if instance.is_boutique and instance.product_type == 1 and not instance.extras.get("template_id"):
                instance.set_boutique_coupon()

            return instance
        else:
            modelproduct = ModelProduct.create(
                product=product,
                name=data.get('name'),
                extras=data.get('extras'),
                is_onsale=bool(data.get('is_onsale')),
                is_teambuy=bool(data.get('is_teambuy')),
                is_recommend=bool(data.get('is_recommend')),
                is_topic=bool(data.get('is_topic')),
                is_flatten=bool(data.get('is_flatten')),
                is_boutique=bool(data.get('is_boutique')),
                is_outside=bool(data.get('is_outside'))
            )

            return modelproduct


class ProductPictureSerializer(serializers.Serializer):
    # product_id = serializers.CharField()
    content_imgs = serializers.ListField()
    respective_imgs = serializers.ListField()
    detail_first_img = serializers.CharField(allow_blank=True)
    head_imgs = serializers.CharField()

    def save(self, data, model_product):
        model_product.head_imgs = data.get('head_imgs')
        model_product.detail_first_img = data.get('detail_first_img')
        content_imgs = [model_product.detail_first_img] if model_product.detail_first_img else []
        content_imgs.extend(data.get('content_imgs', []))
        model_product.content_imgs = '\n'.join(content_imgs)
        respective_imgs = dict(data.get('respective_imgs', []))
        model_product.set_title_imgs_values(respective_imgs)
        model_product.save()
        return model_product


class ActivityProductSerializer(serializers.ModelSerializer):
    web_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ActivityProduct
        fields = ('id', 'product_id', 'model_id', 'product_name', 'product_img',
                  'product_lowest_price', 'product_std_sale_price', 'web_url')

    def get_web_url(self, obj):
        if obj.product:
            return obj.product.get_weburl()
        return ''


class ActivityEntrySerializer(serializers.ModelSerializer):
    products = ActivityProductSerializer(source='activity_products', many=True)
    extras = JSONParseField(read_only=True, required=False)

    class Meta:
        model = ActivityEntry
        fields = ('id', 'title', 'login_required', 'act_desc', 'act_img', 'act_logo', 'mask_link', 'act_link',
                  'act_type', 'act_applink', 'start_time', 'end_time', 'order_val', 'extras',
                  'total_member_num', 'friend_member_num', 'is_active', 'products')


class SimpleActivityEntrySerializer(serializers.ModelSerializer):
    extras = JSONParseField(read_only=True, required=False)

    class Meta:
        model = ActivityEntry
        fields = ('id', 'title', 'login_required', 'act_desc', 'act_img', 'act_logo', 'mask_link', 'act_link',
                  'act_type', 'act_applink', 'start_time', 'end_time', 'order_val',
                  'total_member_num', 'friend_member_num', 'is_active', 'extras')


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    # normal_skus = ProductSkuSerializer(many=True, read_only=True)
    product_model = ModelProductSerializer(source="get_product_model", read_only=True)
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen = serializers.BooleanField(source='sale_open', read_only=True)
    is_newgood = serializers.BooleanField(source='new_good', read_only=True)
    watermark_op = serializers.CharField(read_only=True)
    web_url = serializers.CharField(source='get_weburl', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'category', 'pic_path', 'remain_num', 'is_saleout', 'head_img',
                  'is_saleopen', 'is_newgood', 'std_sale_price', 'agent_price', 'sale_time', 'offshelf_time', 'memo',
                  'lowest_price', 'product_lowest_price', 'product_model', 'ware_by', 'is_verify', "model_id",
                  'watermark_op', 'web_url', 'sale_product')

    def get_name(self, obj):
        if obj.is_flatten:
            return obj.name
        return obj.name.split('/')[0]


class ProductSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        extra_kwargs = {'in_customer_shop': {}, 'shop_product_num': {}, 'rebet_amount': {},
                        'rebet_amount_des': {}, 'sale_num_des': {}}
        fields = ('id', 'pic_path', 'name', 'std_sale_price', 'agent_price', 'remain_num', 'sale_num',
                  'in_customer_shop', 'shop_product_num', 'rebet_amount', 'sale_num_des', 'rebet_amount_des')


class SimpleProductSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    # normal_skus = ProductSkuSerializer(many=True, read_only=True)
    product_model = SimpleModelProductSerializer(source="get_product_model", read_only=True)
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen = serializers.BooleanField(source='sale_open', read_only=True)
    is_newgood = serializers.BooleanField(source='new_good', read_only=True)
    watermark_op = serializers.CharField(read_only=True)
    web_url = serializers.CharField(source='get_weburl', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'category', 'pic_path', 'head_img', 'std_sale_price', 'agent_price'
                  , 'sale_time', 'offshelf_time', 'lowest_price', 'product_lowest_price', 'product_model', 'model_id',
                  'is_saleout', 'is_saleopen', 'is_newgood', 'is_flatten', 'watermark_op', 'web_url')

    def get_name(self, obj):
        if obj.is_flatten:
            return obj.name
        return obj.name.split('/')[0]


class DepositProductSerializer(serializers.ModelSerializer):
    normal_skus = ProductSkuSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'outer_id', 'pic_path', 'head_img',
                  'std_sale_price', 'agent_price', 'sale_time', 'offshelf_time',
                  'product_lowest_price', 'normal_skus')


class ProductPreviewSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:product-detail')
    category = ProductCategorySerializer(read_only=True)
    product_model = ModelProductSerializer(read_only=True)
    is_saleout = serializers.BooleanField(source='sale_out', read_only=True)
    is_saleopen = serializers.BooleanField(source='sale_open', read_only=True)
    is_newgood = serializers.BooleanField(source='new_good', read_only=True)
    sale_charger = serializers.CharField(source="get_supplier_contactor", read_only=True)
    watermark_op = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'url', 'name', 'outer_id', 'category', 'pic_path', 'remain_num', 'is_saleout', 'head_img',
                  'is_saleopen', 'is_newgood', 'std_sale_price', 'agent_price', 'sale_time', 'memo', 'lowest_price',
                  'product_model', 'product_lowest_price', 'ware_by', 'is_verify', "model_id", "sale_charger",
                  'watermark_op')


class PosterSerializer(serializers.HyperlinkedModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = GoodShelf
        fields = ('id', 'title', 'category', 'items', 'is_active', 'active_time', 'created')

    def get_items(self, obj):
        return obj.wem_posters + obj.chd_posters


class PortalSerializer(serializers.ModelSerializer):
    """ 商城入口初始加载数据 """
    posters = JSONParseField(source='get_posters', read_only=True)
    categorys = JSONParseField(source='get_cat_imgs', read_only=True)
    activitys = serializers.SerializerMethodField(read_only=True)
    promotion_brands = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GoodShelf
        fields = ('id', 'posters', 'categorys', 'activitys', 'promotion_brands', 'active_time')

    def get_activitys(self, obj):
        from flashsale.promotion.apis.activity import get_landing_effect_activities
        activitys = get_landing_effect_activities()
        brands_data = SimpleActivityEntrySerializer(activitys, many=True).data
        return brands_data

    def get_promotion_brands(self, obj):
        from flashsale.promotion.apis.activity import get_effect_activities
        activitys = get_effect_activities().filter(act_type=ActivityEntry.ACT_BRAND)
        brands_data = SimpleActivityEntrySerializer(activitys, many=True).data
        return brands_data


class LogisticsCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsCompany
        fields = ('id','code', 'name')


class ShoppingCartSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:shoppingcart-detail')
    status = serializers.ChoiceField(choices=ShoppingCart.STATUS_CHOICE)
    item_weburl = serializers.CharField(source='get_item_weburl', read_only=True)
    model_id = serializers.IntegerField(source='product.model_id', read_only=True)
    is_bonded_goods = serializers.SerializerMethodField('gen_is_bonded_goods', read_only=True)
    elite_score = serializers.IntegerField(source='product.elite_score', read_only=True)
    product_type = serializers.IntegerField(source='product.type', read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'url', 'buyer_id', 'buyer_nick', 'item_id', 'title', 'price',
                  'std_sale_price', 'sku_id', 'num', 'total_fee', 'sku_name', 'model_id',
                  'pic_path', 'created', 'is_repayable', 'status', 'item_weburl', 'type', 'is_bonded_goods',
                  'elite_score', 'product_type')

    def gen_is_bonded_goods(self, obj):
        from flashsale.pay.models.product import ModelProduct
        model_product = ModelProduct.objects.filter(id=obj.product.model_id).first()
        if model_product:
            if model_product.extras.has_key('saleinfos') and model_product.extras['saleinfos'].has_key(
                    'is_bonded_goods'):
                return model_product.extras['saleinfos']['is_bonded_goods']
        return False


class SaleOrderSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:saleorder-detail')
    status = serializers.ChoiceField(choices=SaleOrder.ORDER_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refund_status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)
    kill_title = serializers.BooleanField(source='second_kill_title', read_only=True)
    package_order_id = serializers.SerializerMethodField('gen_package_order_id', read_only=True)
    model_id = serializers.IntegerField(source='item_product.model_id', read_only=True)
    can_refund = serializers.BooleanField(source='get_refundable', read_only=True)
    is_bonded_goods = serializers.SerializerMethodField('gen_is_bonded_goods', read_only=True)

    class Meta:
        model = SaleOrder
        fields = ('id', 'oid', 'item_id', 'title', 'sku_id', 'num', 'outer_id', 'total_fee',
                  'payment', 'discount_fee', 'sku_name', 'pic_path', 'status', 'status_display',
                  'refund_status', 'refund_status_display', "refund_id", 'kill_title', 'model_id',
                  'is_seckill', 'package_order_id', 'can_refund', 'is_bonded_goods')

    def gen_package_order_id(self, obj):
        if obj.package_sku:
            return obj.package_sku.package_order_id or ''
        else:
            return ''

    def gen_is_bonded_goods(self, obj):
        from flashsale.pay.models.product import ModelProduct
        model_product = ModelProduct.objects.filter(id=obj.item_product.model_id).first()
        if model_product:
            if model_product.extras.has_key('saleinfos') and model_product.extras['saleinfos'].has_key('is_bonded_goods'):
                return model_product.extras['saleinfos']['is_bonded_goods']
        return False


def generate_refund_choices(obj):
    """ obj is a saletrade object """
    if not obj.status in (SaleTrade.WAIT_SELLER_SEND_GOODS,
                          SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                          SaleTrade.TRADE_BUYER_SIGNED):
        return {}

    _default = {
        obj.BUDGET: {'name': u'极速退款', 'desc_name': u'小鹿钱包',
                     'desc_tpl': u'{refund_title}，退款金额立即退到{desc_name}，并可立即支付使用，无需等待.'},
        obj.WX: {'name': u'退微信支付', 'desc_name': u'微信钱包或微信银行卡',
                 'desc_tpl': u'{refund_title}，退款金额立即退到{desc_name}，需要等待支付渠道审核３至５个工作日到账.'},
        obj.ALIPAY: {'name': u'退支付宝', 'desc_name': u'支付宝账户',
                     'desc_tpl': u'{refund_title}，退款金额立即退到{desc_name}，需要等待支付渠道审核３至５个工作日到账.'},
        'refund_title_choice': (u'申请退款后', u'退货成功后'),
    }
    is_post_refund = obj.status != SaleTrade.WAIT_SELLER_SEND_GOODS
    refund_title = _default['refund_title_choice'][is_post_refund and 1 or 0]
    refund_channels = [obj.BUDGET]
    # if obj.channel != obj.BUDGET and not obj.has_budget_paid and obj.channel not in [SaleTrade.ALIPAY,
    #                                                                                  SaleTrade.ALIPAY_WAP]:
    #     refund_channels.append(obj.channel)

    refund_resp_list = []
    for channel in refund_channels:
        channel_alias = channel.split('_')[0]
        refund_param = _default.get(channel_alias)
        refund_resp_list.append({
            'refund_channel': channel,
            'name': refund_param['name'],
            'desc': refund_param['desc_tpl'].format(refund_title=refund_title,
                                                    desc_name=refund_param['desc_name'])
        })
    return {
        'refund_choices': refund_resp_list
    }


class SaleOrderDetailSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:saleorder-detail')
    status = serializers.ChoiceField(choices=SaleOrder.ORDER_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refund_status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)
    kill_title = serializers.BooleanField(source='second_kill_title', read_only=True)
    package_order_id = serializers.SerializerMethodField('gen_package_order_id', read_only=True)
    extras = serializers.SerializerMethodField('gen_extras_info', read_only=True)

    class Meta:
        model = SaleOrder
        fields = ('id', 'oid', 'item_id', 'title', 'sku_id', 'num', 'outer_id', 'total_fee',
                  'payment', 'discount_fee', 'sku_name', 'pic_path', 'status', 'status_display',
                  'refund_status', 'refund_status_display', "refund_id", 'kill_title',
                  'is_seckill', 'package_order_id', 'extras')

    def gen_package_order_id(self, obj):
        if obj.package_sku:
            return obj.package_sku.package_order_id or ''
        else:
            return ''

    def gen_extras_info(self, obj):
        return generate_refund_choices(obj.sale_trade)


class SaleTradeSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:saletrade-detail')
    orders = SaleOrderSerializer(source='sale_orders', many=True, read_only=True)
    # orders = serializers.HyperlinkedIdentityField(view_name='rest_v1:saletrade-saleorder')
    channel = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    status = serializers.ChoiceField(choices=SaleTrade.TRADE_STATUS)
    status_display = serializers.CharField(source='status_name', read_only=True)
    order_pic = serializers.CharField(read_only=True)
    red_packer_num = serializers.SerializerMethodField('order_share_red_packer_num', read_only=True)

    class Meta:
        model = SaleTrade
        fields = ('id', 'orders', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment',
                  'post_fee', 'total_fee', 'discount_fee', 'status', 'status_display', 'order_pic',
                  'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid',
                  'logistics_company', 'receiver_name', 'receiver_state', 'receiver_city', 'red_packer_num',
                  'receiver_district', 'receiver_address', 'receiver_mobile', 'receiver_phone', 'order_type')

    def order_share_red_packer_num(self, obj):
        share = OrderShareCoupon.objects.filter(uniq_id=obj.tid).first()
        if share:
            return share.remain_num
        return 0


class PackageOrderSerializer(serializers.ModelSerializer):
    pay_time = serializers.CharField(source='first_package_sku_item.pay_time', read_only=True)
    process_time = serializers.CharField(source='first_package_sku_item.process_time', read_only=True)
    book_time = serializers.CharField(source='first_package_sku_item.book_time', read_only=True)
    assign_time = serializers.CharField(source='first_package_sku_item.assign_time', read_only=True)
    finish_time = serializers.CharField(source='first_package_sku_item.finish_time', read_only=True)
    weight_time = serializers.CharField(read_only=True)
    cancel_time = serializers.CharField(source='first_package_sku_item.cancel_time', read_only=True)
    ware_by_display = serializers.CharField(source='get_ware_by_display', read_only=True)
    assign_status_display = serializers.CharField(source='get_sys_status_display', read_only=True)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    note = serializers.CharField(read_only=True)
    out_sid = serializers.SerializerMethodField('gen_out_sid_strip', read_only=True)

    class Meta:
        model = PackageOrder
        fields = ('id', 'logistics_company', 'process_time', 'pay_time', 'book_time', 'assign_time',
                  'finish_time', 'weight_time','cancel_time', 'assign_status_display', 'ware_by_display', 'out_sid', 'note')

    def gen_out_sid_strip(self, obj):
        return obj.out_sid.strip()


class SaleTradeDetailSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v2:saletrade-detail')
    orders = serializers.SerializerMethodField('gen_sale_orders', read_only=True)
    # TODO 根据订单信息，显示未分包商品及已分包商品列表
    is_paid = serializers.SerializerMethodField(read_only=True)
    channel = serializers.ChoiceField(choices=SaleTrade.CHANNEL_CHOICES)
    trade_type = serializers.ChoiceField(choices=SaleTrade.TRADE_TYPE_CHOICES)
    logistics_company = LogisticsCompanySerializer(read_only=True)
    status = serializers.ChoiceField(choices=SaleTrade.TRADE_STATUS)
    status_display = serializers.CharField(source='status_name', read_only=True)
    package_orders = serializers.SerializerMethodField('gen_package_orders', read_only=True)
    extras = serializers.SerializerMethodField('gen_extras_info', read_only=True)

    class Meta:
        model = SaleTrade
        fields = ('id', 'orders', 'tid', 'buyer_nick', 'buyer_id', 'channel', 'payment', 'pay_cash',
                  'post_fee', 'total_fee', 'discount_fee', 'has_budget_paid', 'status', 'status_display',
                  'buyer_message', 'trade_type', 'created', 'pay_time', 'consign_time', 'out_sid',
                  'logistics_company', 'user_adress', 'package_orders', 'extras', 'order_type', 'can_refund',
                  'can_change_address', 'is_paid')

    def gen_sale_orders(self, obj):
        order_data_list = SaleOrderSerializer(obj.sale_orders, many=True).data
        order_data_list.sort(key=lambda x: x['package_order_id'])
        return order_data_list

    def gen_package_orders(self, obj):
        if obj.status not in SaleTrade.INGOOD_STATUS:
            return []
        package_list = PackageOrderSerializer(obj.package_orders, many=True).data

        for sale_order in obj.sale_orders.all():
            if not sale_order.is_packaged():
                package_sku_item = sale_order.package_sku
                package_list.insert(0, {
                    'id': '',
                    'logistics_company': None,
                    'process_time': package_sku_item and package_sku_item.process_time,
                    'pay_time': package_sku_item and package_sku_item.pay_time or obj.pay_time,
                    'book_time': package_sku_item and package_sku_item.booked_time,
                    'can_refund': sale_order.can_refund(),
                    'assign_time': package_sku_item and package_sku_item.assign_time,
                    'finish_time': package_sku_item and package_sku_item.finish_time,
                    'weight_time': package_sku_item and package_sku_item.weight_time,
                    'cancel_time': package_sku_item and package_sku_item.cancel_time,
                    'assign_status_display': package_sku_item and package_sku_item.get_assign_status_display() or '',
                    'ware_by_display': package_sku_item and package_sku_item.get_ware_by_display() or '',
                    'out_sid': '',
                    'note': ''
                })
                continue
        package_list.sort(key=lambda x: x['id'])
        return package_list

    def gen_extras_info(self, obj):
        refund_dict = generate_refund_choices(obj)
        return refund_dict or {}

    def get_is_paid(self, obj):
        if self.context.has_key('is_paid'):
            return self.context['is_paid']
        else:
            return obj.is_paid



class SaleRefundSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:salerefund-detail')
    good_status = serializers.ChoiceField(choices=SaleRefund.GOOD_STATUS_CHOICES)
    status = serializers.ChoiceField(choices=SaleRefund.REFUND_STATUS)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    return_address = serializers.CharField(source='get_return_address', read_only=True)
    status_shaft = JSONParseField(source='refund_status_shaft', read_only=True)
    proof_pic = JSONParseField()
    amount_flow = JSONParseField()

    class Meta:
        model = SaleRefund
        fields = ('id', 'url', 'refund_no', 'trade_id', 'order_id', 'buyer_id', 'item_id', 'title',
                  'sku_id', 'sku_name', 'refund_num', 'buyer_nick', 'mobile', 'phone', 'proof_pic',
                  'total_fee', 'payment', 'created', 'modified', 'company_name', 'sid', 'reason', 'pic_path',
                  'desc', 'feedback', 'has_good_return', 'has_good_change', 'good_status', 'status', 'refund_fee',
                  "return_address", "status_display", "amount_flow", "status_shaft", "refund_channel")


class UserAddressSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:useraddress-detail')
    status = serializers.ChoiceField(choices=UserAddress.STATUS_CHOICES)

    class Meta:
        model = UserAddress
        fields = ('id', 'url', 'cus_uid', 'receiver_name', 'receiver_state', 'receiver_city',
                  'receiver_district', 'receiver_address', 'receiver_zip', 'receiver_mobile',
                  'receiver_phone', 'logistic_company_code', 'default', 'status', 'created')


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:district-detail')

    class Meta:
        model = District
        fields = ('id', 'url', 'parent_id', 'name', 'grade', 'sort_order')


class UserIntegralSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:user-intergral')

    class Meta:
        model = Integral
        fields = ('id', 'integral_user', 'integral_value')


class UserIntegralLogSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='rest_v1:user-IntegralLog')

    class Meta:
        model = IntegralLog
        fields = (
            'id', 'integral_user', 'mobile', 'order_info', 'log_value', 'log_status', 'log_type', 'in_out', 'created',
            'modified')


class TradeWuliuSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeWuliu
        exclude = ()


class WXOrderSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:wxorder-detail')
    order_status_display = serializers.CharField(source='get_order_status_display', read_only=True)

    class Meta:
        model = WXOrder
        fields = ('url', 'order_id', 'buyer_nick', 'order_total_price', 'order_express_price', 'order_create_time',
                  'order_status',
                  'receiver_name', 'receiver_province', 'receiver_city', 'receiver_zone', 'receiver_address',
                  'receiver_mobile',
                  'receiver_phone', 'product_id', 'product_name', 'product_price', 'product_sku', 'product_count',
                  'order_status_display', 'product_img', 'delivery_id', 'delivery_company')


class CustomShareSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='rest_v1:customshare-detail')

    class Meta:
        model = CustomShare
        fields = ('url', 'id', 'title', 'desc', 'share_img', 'active_at', 'created', 'status')


class SaleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleProduct
        fields = ('id', 'outer_id', 'title', 'price', 'pic_url', 'voting', 'created', 'modified', 'hot_value')


class HotProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotProduct
        fields = ('id', 'name', 'proid', 'pic_pth', 'site_url', 'price', 'hot_value', 'voting', 'memo', 'status', 'status')


class ProRefunRcordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProRefunRcord
        fields = ('product', 'ref_num_out', 'ref_num_in', 'ref_sed_num', 'pro_contactor', 'pro_model', 'sale_time',
                  'pro_supplier', 'same_mod_sale_num', 'pro_pic')


class ProRefunRcdSerializer(serializers.ModelSerializer):
    """ # 针对商品的退款统计内容　
        - ProRefunRcordSerializer　fields　is to many, it makes the http request 404 return
        - To extend for client to handler the data of the pro rcd
    """

    class Meta:
        model = ProRefunRcord
        fields = ('product', 'ref_num_out', 'ref_num_in', 'ref_sed_num', 'sale_date', 'is_female', 'is_child')


class XiaoluMamaSerialize(serializers.ModelSerializer):
    coulde_cashout = serializers.FloatField(source='get_cash_iters', read_only=True)
    can_trial = serializers.SerializerMethodField('can_trial_judgement', read_only=True)

    class Meta:
        model = XiaoluMama
        fields = (
            "id", "get_cash_display", "charge_status", "agencylevel", "manager", "referal_from", "mobile", "weikefu",
            "charge_time", 'coulde_cashout', 'last_renew_type', 'can_trial')

    def can_trial_judgement(self, obj):
        if obj.last_renew_type == XiaoluMama.TRIAL:
            return False
        if obj.charge_status == XiaoluMama.CHARGED:
            return False
        return True


class XiaoluMamaInfoSerialize(serializers.ModelSerializer):
    nick = serializers.SerializerMethodField('mama_customer_nick', read_only=True)
    thumbnail = serializers.SerializerMethodField('mama_customer_thumbnail', read_only=True)
    award = serializers.SerializerMethodField('mama_award_info', read_only=True)

    class Meta:
        model = XiaoluMama
        fields = ("id", "agencylevel", "nick", 'thumbnail', "charge_time", "award")

    def mama_customer_nick(self, obj):
        customer = obj.get_mama_customer()
        return customer.nick if customer else ''

    def mama_customer_thumbnail(self, obj):
        customer = obj.get_mama_customer()
        return customer.thumbnail if customer else ''

    def mama_award_info(self, obj):
        referal_from_mama_id = self.context['current_mm'].id
        award_carry = AwardCarry.objects.filter(mama_id=referal_from_mama_id,
                                                contributor_mama_id=obj.id).first()
        if award_carry:
            return award_carry.carry_num / 100.0


class CarryLogSerialize(serializers.ModelSerializer):
    dayly_in_amount = serializers.FloatField(source='dayly_in_value', read_only=True)
    dayly_clk_amount = serializers.FloatField(source='dayly_clk_value', read_only=True)
    desc = serializers.CharField(source='get_carry_desc', read_only=True)

    class Meta:
        model = CarryLog
        fields = ("id", "carry_type", "xlmm", "value_money", "carry_type_name", "log_type", "carry_date", "created",
                  'dayly_in_amount', 'dayly_clk_amount', 'desc', 'get_log_type_display')


class ClickCountSerialize(serializers.ModelSerializer):
    class Meta:
        model = ClickCount
        fields = ("linkid", "agencylevel", "user_num", "valid_num", "click_num", "date")


class ClickSerialize(serializers.ModelSerializer):
    class Meta:
        model = Clicks
        fields = ("id", "linkid", "openid", "app_key", "click_time", "created")


class StatisticsShoppingSerialize(serializers.ModelSerializer):
    pic_path = serializers.CharField(source='pro_pic', read_only=True)
    time_display = serializers.CharField(source='day_time', read_only=True)
    dayly_amount = serializers.FloatField(source='dayly_ticheng', read_only=True)

    class Meta:
        model = StatisticsShopping
        fields = ("linkid", "linkname", "wxorderid", "wxordernick", "order_cash", "rebeta_cash", "ticheng_cash",
                  "shoptime", "status", "get_status_display", "pic_path", "time_display", "dayly_amount")


class CashOutSerialize(serializers.ModelSerializer):
    class Meta:
        model = CashOut
        fields = ('id', "xlmm", "value_money", "get_status_display", "status", "created")


class XlmmAdvertisSerialize(serializers.ModelSerializer):
    class Meta:
        model = XlmmAdvertis
        fields = ("title", "cntnt")


class MamaVebViewConfSerialize(serializers.ModelSerializer):
    extra = JSONParseField()

    class Meta:
        model = MamaVebViewConf
        fields = ('id', 'version', "is_valid", "extra", "created", "modified")


class CustomerShopsSerialize(serializers.ModelSerializer):
    class Meta:
        model = CustomerShops
        exclude = ()


class CuShopProsSerialize(serializers.ModelSerializer):
    sale_num = serializers.IntegerField(source='sale_num_salt', read_only=True)

    class Meta:
        model = CuShopPros
        fields = ('id', "product", "model", "pro_status", "name", "pic_path", 'std_sale_price', 'agent_price',
                  "carry_amount", 'position', 'sale_num', 'modified', 'created', 'offshelf_time')


class XLSampleOrderSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLSampleOrder
        exclude = ()


class XLFreeSampleSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLFreeSample
        exclude = ()


class XLSampleSkuSerialize(serializers.ModelSerializer):
    class Meta:
        model = XLSampleSku
        exclude = ()


class BudgetLogSerialize(serializers.ModelSerializer):
    budeget_detail_cash = serializers.FloatField(source='get_flow_amount_display', read_only=True)
    desc = serializers.SerializerMethodField()
    mama = serializers.SerializerMethodField()

    class Meta:
        model = BudgetLog
        fields = (
            'customer_id',
            'mama',
            'desc',
            'budget_type',
            'budget_log_type',
            'budget_date',
            'get_status_display',
            'status',
            'budeget_detail_cash',
            'modified'
        )

    def get_desc(self, obj):
        return u'您通过{0}{1}{2}元.'.format(obj.get_budget_log_type_display(),
            obj.get_budget_type_display(),
            obj.flow_amount * 0.01)

    def get_mama(self, obj):
        customer = Customer.objects.get(id=obj.customer_id)
        return {
            'mama_id': customer.mama_id,
            'nick': customer.nick,
            'thumbnail': customer.thumbnail
        }


class XlmmFansCustomerInfoSerialize(serializers.ModelSerializer):
    """ 小鹿妈妈粉丝列表的用户信息 """

    class Meta:
        model = Customer
        fields = ('nick', 'thumbnail', 'status', 'get_status_display')


class AppReleaseSerialize(serializers.ModelSerializer):
    class Meta:
        model = AppRelease
        fields = ('nick', 'thumbnail', 'status', 'get_status_display')


class SaleFaqDetailCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqsDetailCategory
        fields = ('id', 'download_link', 'qrcode_link', 'status', 'release_time', 'auto_update', 'hash_value', 'version', 'version_code', 'device_type')


class SaleFaqCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqMainCategory
        fields = ('id', 'icon_url', 'category_name', 'description')


class SaleFaqerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleFaq
        fields = ('id', 'main_category', 'detail_category', 'question', 'answer')


class UserSearchHistorySerialize(serializers.ModelSerializer):
    class Meta:
        model = UserSearchHistory
        fields = (
            'id',
            'user_id',
            'content',
            'target',
            'result_count',
            'status',
        )

class XiaoluCoinLogSerializer(serializers.ModelSerializer):

    subject = serializers.SerializerMethodField()
    iro_type = serializers.SerializerMethodField()

    class Meta:
        model = XiaoluCoinLog
        fields = ('id', 'mama_id', 'iro_type', 'amount', 'subject', 'date_field', 'created')

    def get_subject(self, obj):
        return dict(XiaoluCoinLog.SUBJECT_CHOICES).get(obj.subject, '')

    def get_iro_type(self, obj):
        return dict(XiaoluCoinLog.IRO_CHOICES).get(obj.iro_type, '')

