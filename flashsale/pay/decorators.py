# -*- encoding:utf8 -*-
import urllib
from functools import wraps
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login as auth_login, SESSION_KEY
from django.conf import settings

from core.weixin import options
from core.weixin import constants as wxcon
from . import constants

import logging
logger = logging.getLogger(__name__)

def union_wxpub_auth(wxpub_appid, none_wxauth_url='/'):
    """ 统一微信微信授权并创建用户装饰器 """
    def _decorator(view_func):
        @wraps(view_func)
        def _checklogin(request, *args, **kwargs):
            if request.user.is_active:
                # The user is valid. Continue to the admin page.
                return view_func(request, *args, **kwargs)

            code  = request.GET.get('code')
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0 :
                return HttpResponseRedirect(none_wxauth_url)

            if not code:
                openid, unionid = options.get_cookie_openid(request.COOKIES, wxpub_appid)
                if not options.valid_openid(unionid):
                    params = {'appid': wxpub_appid,
                              'redirect_uri': request.build_absolute_uri().split('#')[0],
                              'response_type': 'code',
                              'scope': 'snsapi_userinfo',
                              'state': '135'}
                    redirect_url = options.gen_weixin_redirect_url(params)
                    return redirect(redirect_url)

            user = authenticate(request=request, auth_code=code, wxpub_appid=wxpub_appid)
            if not user or user.is_anonymous:
                return HttpResponseRedirect(none_wxauth_url)

            auth_login(request, user)
            return view_func(request, *args, **kwargs)

        return _checklogin

    return _decorator

def sale_buyer_required(view_func):
    """ deprecated, not use
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """
    @wraps(view_func)
    def _checklogin(request, *args, **kwargs):
        if request.user.is_active:
            # The user is valid. Continue to the admin page.
            return view_func(request, *args, **kwargs)

        code = request.GET.get('code')
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent and user_agent.find('MicroMessenger') >= 0:
            if not code:
                params = {'appid': settings.WX_PUB_APPID,
                          'redirect_uri': request.build_absolute_uri().split('#')[0],
                          'response_type': 'code',
                          'scope': 'snsapi_base',
                          'state': '135'}
                redirect_url = options.gen_weixin_redirect_url(params)
                return HttpResponseRedirect(redirect_url)

            else:
                user = authenticate(request=request, auth_code=code, wxpub_appid=settings.WX_PUB_APPID)
                if not user or user.is_anonymous:
                    return HttpResponseRedirect(reverse('flashsale_login'))

                request.session[SESSION_KEY] = user.id
                auth_login(request, user)

                return view_func(request, *args, **kwargs)

        defaults = {
            REDIRECT_FIELD_NAME: request.build_absolute_uri().split('#')[0]
        }
        return redirect('{}?{}'.format(constants.MALL_LOGIN_URL, urllib.urlencode(defaults)))

    return _checklogin


def weixin_xlmm_auth(redirecto=None):
    """ deprecated, not use
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """

    def _decorator(view_func):
        assert redirecto, u'redirecto 参数必须'

        @wraps(view_func)
        def _checklogin(request, *args, **kwargs):
            if request.user.is_active:
                # The user is valid. Continue to the admin page.
                return view_func(request, *args, **kwargs)

            code = request.GET.get('code')
            user_agent = request.META.get('HTTP_USER_AGENT')
            path = request.get_full_path()
            redirect_url = redirecto
            if redirect_url.find('?') > 0:
                redirect_url += path.find('?') > 0 and path[path.find('?') + 1:] or ''
            else:
                redirect_url += path.find('?') > 0 and path[path.find('?'):] or ''
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return HttpResponseRedirect(redirect_url)

            if not code:
                openid, unionid = options.get_cookie_openid(request.COOKIES, settings.WX_PUB_APPID)
                if not options.valid_openid(unionid):
                    params = {'appid': settings.WX_PUB_APPID,
                              'redirect_uri': request.build_absolute_uri().split('#')[0],
                              'response_type': 'code',
                              'scope': 'snsapi_userinfo',
                              'state': '135'}
                    redirect_url = options.gen_weixin_redirect_url(params)
                    return redirect(redirect_url)

            user = authenticate(request=request, auth_code=code, wxpub_appid=settings.WX_PUB_APPID)
            if not user or user.is_anonymous:
                return HttpResponseRedirect(redirect_url)

            auth_login(request, user)
            return view_func(request, *args, **kwargs)

        return _checklogin

    return _decorator


def weixin_test_auth(redirecto=None):
    """ deprecated, not use
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """

    def _decorator(view_func):

        assert redirecto, u'redirecto 参数必须'

        @wraps(view_func)
        def _checklogin(request, *args, **kwargs):
            if request.user.is_active:
                # The user is valid. Continue to the admin page.
                return view_func(request, *args, **kwargs)

            code = request.GET.get('code')
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return HttpResponseRedirect(redirecto)

            if not code:
                params = {'appid': settings.WX_PUB_APPID,
                          'redirect_uri': request.build_absolute_uri().split('#')[0],
                          'response_type': 'code',
                          'scope': 'snsapi_base',
                          'state': '135'}
                redirect_url = options.gen_weixin_redirect_url(params)
                return HttpResponseRedirect(redirect_url)

            else:
                user = authenticate(request=request, auth_code=code, wxpub_appid=settings.WX_PUB_APPID)
                if not user or user.is_anonymous:
                    return HttpResponseRedirect(redirecto)

                auth_login(request, user)
                return view_func(request, *args, **kwargs)

        return _checklogin

    return _decorator
