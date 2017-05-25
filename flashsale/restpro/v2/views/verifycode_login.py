# -*- coding:utf-8 -*-
import datetime
import logging
import re
import time
from urlparse import urlparse

from django.http.request import validate_host
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User as DjangoUser
from rest_framework import views
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions

from common.auth import WeAppAuthentication
from core.weixin.options import gen_wxlogin_sha1_sign
from core.utils.regex import REGEX_MOBILE
from flashsale.pay.models import Register, Customer
from flashsale.xiaolumm.models.models_fans import login_activate_appdownloadrecord
from shopapp.smsmgr.tasks import task_register_code
from shopback.monitor.models import XiaoluSwitch

logger = logging.getLogger(__name__)

PHONE_NUM_RE = re.compile(REGEX_MOBILE, re.IGNORECASE)
CODE_TIME_LIMIT = 1800
RESEND_TIME_LIMIT = 60
SYSTEMOA_ID = 641
MAX_DAY_LIMIT = 6

def delay_seconds(reg):
    """
    delay seconds
    """
    if reg.mail_time:
        delta = (datetime.datetime.now() - reg.mail_time).seconds
        if delta < RESEND_TIME_LIMIT:
            return max(RESEND_TIME_LIMIT - delta, 3)
    return 0

def check_day_limit(reg):
    """
    whether or not the day_limit is reached.
    """
    if reg.code_time:
        date1 = datetime.date.today()
        date2 = reg.code_time.date()
        if date1 == date2:
            if reg.verify_count >= MAX_DAY_LIMIT or reg.submit_count >= MAX_DAY_LIMIT:
                return True
        else:
            # everyday we restore verify_count/submit_count
            reg.verify_count = 0
            reg.submit_count = 0
            reg.verify_code = ''
            reg.save()
    return False


def get_register(mobile):
    """
    get register record by mobile, create one if not exists.
    return [register, created]
    if created == True, this means register just got created.
    """
    regs = Register.objects.filter(vmobile=mobile)
    if regs.count() > 0:
        return regs[0], False
    reg = Register(vmobile=mobile)
    reg.save()

    return reg, True


def validate_code(mobile, verify_code):
    """
    Only indicate whether or not verify_code is valid.
    """
    if not verify_code:
        return False

    current_time = datetime.datetime.now()
    earliest_send_time = current_time - datetime.timedelta(seconds=CODE_TIME_LIMIT)
    reg = Register.objects.filter(vmobile=mobile).first()

    if not (reg and reg.code_time and reg.verify_code):
        return False

    verify_code = verify_code.strip()
    if reg.code_time > earliest_send_time and reg.verify_code == verify_code:
        reg.submit_count = 0
        reg.verify_count += 1
        reg.verify_code = ''
        reg.save(update_fields=['submit_count', 'verify_count', 'verify_code'])
        return True

    if XiaoluSwitch.is_switch_open(6):
        logger.error(u'validate_code false, reg.verify_code=%s,verify_code=%s' % (reg.verify_code, verify_code))

    return False


def get_customer(request, mobile):
    """
    1) get customer by authenticated user (if logged in);
    2) get customer by mobile if otherwise.
    """
    user = request.user
    if user and user.is_authenticated():
        customers = Customer.objects.filter(user=user).exclude(status=Customer.DELETE)
    else:
        customers = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
    if customers.count() > 0:
        return customers[0]
    return None


def validate_mobile(mobile):
    """
    check mobile format
    """
    if re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
        return True
    return False


def validate_action(action):
    """
    check whether the action is legal.
    """
    d = ["register", "find_pwd", "change_pwd", "bind", "sms_login"]
    if action in d:
        return True
    return False


def customer_exists(mobile):
    """
    check customer existance by mobile.
    """
    customers = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
    if customers.count() > 0:
        return True
    return False


def should_resend_code(reg):
    """
    Only check whether or not mail_time is within RESEND_TIME_LIMIT.
    """
    current_time = datetime.datetime.now()
    earliest_send_time = current_time - datetime.timedelta(seconds=RESEND_TIME_LIMIT)
    if reg.mail_time and reg.mail_time > earliest_send_time:
        return False
    return True


def should_generate_new_code(reg):
    """
    Only check whether or not code_time is within (CODE_TIME_LIMIT - RESEND_TIME_LIMIT).
    """
    current_time = datetime.datetime.now()
    regenerate_time_limit = CODE_TIME_LIMIT - RESEND_TIME_LIMIT
    earliest_code_time = current_time - datetime.timedelta(seconds=regenerate_time_limit)
    if reg.verify_code and reg.code_time and reg.code_time > earliest_code_time:
        # we dont generate new code, only if this code still have enough time before expire.
        return False
    return True


def is_from_app(params):
    devtype = params.get("devtype")
    if devtype:
        devtype = devtype.lower()
    if devtype == "android" or devtype == "ios":
        return True
    return False


def valid_send_request(request):
    if not settings.DEPLOY_ENV:
        return True
    user_agent = (request.META.get('HTTP_USER_AGENT') or '').lower()
    http_referer = (request.META.get('HTTP_REFERER') or '').lower()
    if not user_agent or user_agent.lower().find('windows') > 0:
        return False
    domain = http_referer and urlparse(http_referer).hostname
    if domain and not validate_host(domain, settings.ALLOWED_HOSTS):
        return False
    return True


class SendCodeView(views.APIView):
    """
    处理所有和验证码相关的请求，暂有5类：
    register，sms_login, find_pwd, change_pwd, bind.

    /send_code
    mobile: mobile number
    action: one of 5 actions (register，sms_login, find_pwd, change_pwd, bind)
    """
    throttle_scope = 'auth'

    def post(self, request):
        content = request.data
        mobile = content.get("mobile", "0")
        action = content.get("action", "")

        valid_request = valid_send_request(request)
        if not valid_request:
            import random
            rnum = random.randint(1, 10)
            if rnum % 2 == 1:
                return Response({"rcode": 0, "code": 0, "msg": u"手机已注册", "info": u"手机已注册"})
            else:
                return Response({"rcode": 0, "code": 0, "msg": u"验证码已发送", "info": u"验证码已发送"})

        # 稳定后，日志可以移到valid_request　之后，降低系统负担
        if XiaoluSwitch.is_switch_open(9):
            logger.info({
                'action': 'api.v2.send_code',
                'ip': request.META.get('REMOTE_ADDR', ''),
                'http_user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'cookie': request.META.get('HTTP_COOKIE', ''),
                'http_origin': request.META.get('HTTP_ORIGIN', ''),
                'http_referer': request.META.get('HTTP_REFERER', ''),
                'mobile': mobile,
                'type': action,
            })

        if not validate_mobile(mobile):
            info = u"亲，手机号码错啦！"
            return Response({"rcode": 1, "code": 1, "msg": info, "info": info})

        if not validate_action(action):
            info = u"亲，操作错误！"
            return Response({"rcode": 1, "code": 1, "msg": info, "info": info})

        customer = get_customer(request, mobile)

        if customer:
            if action == 'register':
                info = u"该用户已经存在啦！"
                return Response({"rcode": 2, "code": 2, "msg": info, "info": info})
        else:
            if action in ['find_pwd', 'change_pwd', 'bind', 'sms_login']:
                info = u"该用户还不存在呢！"
                return Response({"rcode": 3, "code": 3, "msg": info, "info": info})

        reg, created = get_register(mobile)
        if not created:
            # if reg is not just created, we have to check
            # day limit and resend condition.
            if check_day_limit(reg):
                info = u"当日验证次数超过限制!"
                return Response({"rcode": 4, "code": 4, "msg": info, "info": info})
            if not should_resend_code(reg):
                info = u"验证码刚发过咯，请{}秒后重试！".format(delay_seconds(reg))
                return Response({"rcode": 5, "code": 5, "msg": info, "info": info})

        if should_generate_new_code(reg):
            reg.verify_code = reg.genValidCode()
            reg.code_time = datetime.datetime.now()

        reg.mail_time = datetime.datetime.now()
        reg.submit_count += 1
        reg.save()

        task_register_code.delay(mobile, "3")
        return Response({"rcode": 0, "code": 0, "msg": u"验证码已发送！", "info": u"验证码已发送！"})


class RequestCashoutVerifyCode(views.APIView):
    """
    Reqest cashout verify_code.

    /rest/v2/request_cashout_verify_code
    """

    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'auth'

    def post(self, request):
        user = request.user
        customer = Customer.objects.filter(user=user).exclude(status=Customer.DELETE).first()
        mobile = customer.mobile
        from shopback.monitor.models import XiaoluSwitch

        switch = XiaoluSwitch.objects.filter(id=7).first()
        if switch and switch.status == 1:
            return Response({"code": 2, "info": u"系统维护中，请稍后再试!"})

        if not validate_mobile(mobile):
            return Response({"code": 1, "info": u"帐户未绑定手机号或手机号错误！"})

        reg, created = get_register(mobile)
        if not created:
            # if reg is not just created, we have to check
            # day limit and resend condition.
            if check_day_limit(reg):
                return Response({"code": 4, "info": u"当日验证次数超过限制！"})
            if not should_resend_code(reg):
                return Response({"code": 5, "info": u"验证码刚发过咯，请{}秒后重试！".format(delay_seconds(reg))})

        if should_generate_new_code(reg):
            reg.verify_code = reg.genValidCode()
            reg.code_time = datetime.datetime.now()

        reg.mail_time = datetime.datetime.now()
        reg.submit_count += 1
        reg.save()

        task_register_code.delay(mobile, "4")
        return Response({"code": 0, "info": u"验证码已发送！"})


class VerifyCodeView(views.APIView):
    """
    verify code under 4 action cases:
    find_pwd, change_pwd, bind, sms_login --- 20170406 del regitster,because main scene is weixin, need wx openid first

    /verify_code
    mobile: mobile number
    action: one of 4 actions (sms_login, find_pwd, change_pwd, bind)
    nickname： if action is bind , this field need
    """
    throttle_scope = 'auth'

    def post(self, request):
        content = {}
        for k,v in request.POST.iteritems():
            content[k] = v

        mobile = content.get("mobile", "0")
        action = content.get("action", "")
        nickname = content.get('nickname', "")
        verify_code = content.get("verify_code", "")

        if not validate_mobile(mobile):
            return Response({"rcode": 1, "msg": u"亲，手机号码错啦！"})

        if not validate_action(action):
            return Response({"rcode": 1, "msg": u"亲，操作错误！"})

        customer = get_customer(request, mobile)

        if not validate_code(mobile, verify_code):
            return Response({"rcode": 4, "msg": u"验证码不对或过期啦！"})  # 验证码过期或者不对

        if customer:
            if action == 'register':
                return Response({"rcode": 2, "msg": u"该用户已经存在啦！"})  # 已经有用户了
            if action == 'bind':
                # 如果已绑定过微信,则不能重复绑定
                customers = Customer.objects.filter(mobile=mobile).exclude(unionid='')
                if customers.exists():
                    return Response({"rcode": 2, "msg": u"该手机号码已注册！"})  # 已经有用户了
        else:
            if action == 'find_pwd' or action == 'change_pwd' or action == 'bind':
                return Response({"rcode": 3, "msg": u"该用户还不存在呢！"})
        if not customer:
            # django_user, state = DjangoUser.objects.get_or_create(username=mobile, is_active=True)
            # customer, state = Customer.objects.get_or_create(user=django_user)
            return Response({"rcode": 5, "msg": u"该用户还不存在呢,请使用微信登录然后绑定手机号，就可以使用手机号登录了！"})

        if action == 'bind' and nickname:
            customer.set_nickname(nickname, force_update=True)

        customer.mobile = mobile
        customer.save()
        if action == 'register' or action == 'sms_login':
            # force to use SMSLoginBackend for authentication
            # content['sms_code'] = verify_code (ERROR)
            # request.data._mutable = True  # 开启可变
            content.update({'sms_code': verify_code})
            # request.data._mutable = False  # 关闭可变

            user = authenticate(request=request, **content)
            if not user or user.is_anonymous:
                return Response({"rcode": 5, "msg": u'登录异常！'})

            login(request, user)

            # if is_from_app(content):
            #    login_activate_appdownloadrecord(user)

            return Response({"rcode": 0, "msg": u"登录成功！"})

        return Response({"rcode": 0, "msg": u"验证码校验通过！"})


class ResetPasswordView(views.APIView):
    """
    Reset password:

    /reset_password?mobile=xxx&password1=xxx&password2=xxx&verify_code=xxx
    """
    throttle_scope = 'auth'

    def post(self, request):
        """
        reset password after verifying code
        """
        content = request.data
        mobile = content.get("mobile", "0")
        pwd1 = content.get("password1", "")
        pwd2 = content.get("password2", "")
        verify_code = content.get("verify_code", "")

        if not validate_mobile(mobile):
            return Response({"rcode": 1, "msg": u"亲，手机号码错啦！"})

        if not mobile or not pwd1 or not pwd2 or not verify_code or pwd1 != pwd2:
            return Response({"rcode": 2, "msg": "提交的参数有误呀！"})

        if len(pwd1) < 6:
            return Response({"rcode": 2, "msg": "密码长度不得少于6位！"})

        customer = get_customer(request, mobile)
        if not customer:
            return Response({"rcode": 3, "msg": u"该用户还不存在呢！"})

        # wulei 20160929 重置密码前已经验证过手机号了,那么不需要再验证码检查
        #if not validate_code(mobile, verify_code):
        #    return Response({"rcode": 4, "msg": u"验证码不对或过期啦！"})  # 验证码过期或者不对

        django_user = customer.user
        django_user.set_password(pwd1)
        django_user.save()

        return Response({"rcode": 0, "msg": u"密码设置成功啦！"})


class PasswordLoginView(views.APIView):
    """
    User login with username and password. She can login either via APP or H5 Web.

    """
    throttle_scope = 'auth'

    def post(self, request):
        content = request.data
        username = content.get('username', '0')
        password = content.get('password', '')
        next_url = content.get('next', '/index.html')
        if not username or not password:
            return Response({"rcode": 1, "msg": u"用户名和密码不全呢！", 'next': ''})

        customers = Customer.objects.filter(mobile=username, status=Customer.NORMAL)
        customer = None
        if customers.count() > 1:
            customer = customers.filter(user__username=username).first()

        if not customer:
            customer = customers.first()

        if customer:
            # 若是微信授权创建的账户，django user的username不是手机号。
            username = customer.user.username

        user = authenticate(username=username, password=password)
        if not user or user.is_anonymous:
            return Response({"rcode": 2, "msg": u"用户名或密码错误呢！", 'next': ''})

        login(request, user)

        if is_from_app(content):
            login_activate_appdownloadrecord(user)

        return Response({"rcode": 0, "msg": u"登录成功", "next": next_url})


def check_sign(request):
    """
    功能：微信app 登录接口数据校验算法:
    参数：params = {'a':1,'c':2,'b':3}
    时间戳：timestamp = 1442995986
    随机字符串：noncestr = 8位随机字符串，如abcdef45
        　 　secret : 3c7b4e3eb5ae4c (测试值)

       签名步骤:
       1，获得所有签名参数：　sign_params = {timestamp:时间戳,noncestr:随机值,secret:密钥值}
        如　{'timestamp':'1442995986','noncestr':'1442995986abcdef','secret':'3c7b4e3eb5ae4c'}
       2,根据参数的字符串key，进行升序排列,并组装成新的字符串，如：
        sign_string = '&'.join(sort([k=v for k,v in sign_params],asc=true))
       如　'noncestr=1442995986abcdef&secret=3c7b4e3eb5ae4c&timestamp=1442995986'
       3,签名算法
        sign = hash.sha1(sign_string).hexdigest()
        如　签名值＝'39ae931c59394c9b4b0973b3902956f63a35c21e'
       4,最后传递给服务器的参数：
       URL:~?noncestr=1442995986abcdef&timestamp=1442995986&sign=366a83819b064149a7f4e9f6c06f1e60eaeb02f7
       POST: 'a=1&b=3&c=2'
    """
    params = {}
    for k, v in request.GET.iteritems():
        params[k] = v
    timestamp = params.get('timestamp')
    if not timestamp or time.time() - int(timestamp) > 6 * 60 * 60:
        logger.error('wxapp sign timeout: %s' % params)
        return False
    origin_sign = params.pop('sign')
    new_sign = gen_wxlogin_sha1_sign(params, settings.WX_APPSECRET)
    if origin_sign and origin_sign == new_sign:
        return True
    params.update({'sign': origin_sign})
    logger.error('%s' % params)
    return False


class WeixinAppLoginView(views.APIView):
    """
    User login with Weixin authorization via APP.

    """
    throttle_scope = 'auth'

    def post(self, request):
        """
        app客户端微信授权登陆
        """
        params = {}
        for k, v in request.POST.iteritems():
            params[k] = v

        if not check_sign(request):
            return Response({"rcode": 1, "msg": u'登录失败'})

        user = authenticate(request=request, **params)
        if not user or user.is_anonymous:
            return Response({"rcode": 2, "msg": u'登录异常'})

        login(request, user)
        if is_from_app(params):
            login_activate_appdownloadrecord(user)

        return Response({"rcode": 0, "msg": u'登录成功'})
