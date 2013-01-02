import time
import json
import urllib
import urllib2
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import SiteProfileNotAvailable
from auth.utils import verifySignature,decodeBase64String,parse_urlparams
from django.conf import settings
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')

"""
token {
    "w2_expires_in": 0,
    "taobao_user_id": "121741189",
    "taobao_user_nick": "%E4%BC%98%E5%B0%BC%E5%B0%8F%E5%B0%8F%E4%B8%96%E7%95%8C",
    "w1_expires_in": 1800,
    "re_expires_in": 2592000,
    "r2_expires_in": 0,
    "hra_expires_in": "1800",
    "expires_in": 86400,
    "token_type": "Bearer",
    "refresh_token": "6201a02d59ZZ5a04911942af136db8a901de3efa62ff63c121741189",
    "access_token": "6202b025cfhj953ffb3b2bdba4aedac383f01cf6ed27e48121741189",
    "r1_expires_in": 1800
}
"""
class TaoBaoBackend:
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, request, user=None):
        """{u'state': [u''], u'code': [u'sVT2F1nZtnkVLaEnhKiy5gS832237']}"""
        content = request.REQUEST
        code    = content.get('code')
        state   = content.get('state')
        
        if not code:
            return None

        params = {
            'client_id':settings.APPKEY,
            'client_secret':settings.APPSECRET,
            'grant_type':'authorization_code',
            'code':code,
            'redirect_uri':settings.REDIRECT_URI,
            'scope':settings.SCOPE,
            'state':state,
            'view':'web'
        }
        req = urllib2.urlopen(settings.AUTHRIZE_TOKEN_URL,urllib.urlencode(params))
        top_parameters = json.loads(req.read())
        
        request.session['top_session']    = top_parameters['access_token']
        request.session['top_parameters'] = top_parameters
        top_parameters['ts']  = time.time()
        
        try:
            app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        except ValueError:
            raise SiteProfileNotAvailable('app_label and model_name should'
                                          ' be separated by a dot in the AUTH_PROFILE_MODULE set'
                                          'ting')

        try:
            model = models.get_model(app_label, model_name)
            if model is None:
                raise SiteProfileNotAvailable('Unable to load the profile '
                                              'model, check AUTH_PROFILE_MODULE in your project sett'
                                              'ings')
        except (ImportError,ImproperlyConfigured):
            raise SiteProfileNotAvailable('ImportError, ImproperlyConfigured error')

        user_id  =  top_parameters['taobao_user_id']

        try:
            profile = model.objects.get(visitor_id=user_id)
            profile.top_session    = top_parameters['access_token']
            profile.top_parameters = json.dumps(top_parameters)
            profile.save()

            if profile.user:
                if not profile.user.is_active:
                    profile.user.is_active = True
                    profile.user.save()
                return profile.user
            else:
                user,state = User.objects.get_or_create(username=user_id,is_active=True)
                profile.user = user
                profile.save()
                return user
        except model.DoesNotExist:
            user,state = User.objects.get_or_create(username=user_id,is_active=True)
            profile,state = model.objects.get_or_create(user=user,visitor_id=user_id)
            profile.top_session    = top_parameters['access_token']
            profile.top_parameters = json.dumps(top_parameters)
            profile.save()
            return user


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
  
