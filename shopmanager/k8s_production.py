# coding=utf-8
import os
from .k8s import *

DEBUG = False
DEPLOY_ENV = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 24 * 30 * 60 * 60

# WEB DNS
SITE_URL = 'http://admin.nidepuzi.com/'
#######################  WAP AND WEIXIN CONFIG ########################
M_SITE_URL = 'http://m.nidepuzi.com'

MYSQL_HOST = 'rm-uf632p729ho32369e.mysql.rds.aliyuncs.com'
MYSQL_AUTH = os.environ.get('MYSQL_AUTH')

REDIS_HOST = 'r-uf66d18cf4ce3a44.redis.rds.aliyuncs.com:6379'
REDIS_AUTH = os.environ.get('REDIS_AUTH')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'nidepuzidb',  # Or path to database file if using sqlite3.
        'USER': 'nidepuzidba',  # Not used with sqlite3.
        'PASSWORD': MYSQL_AUTH,  # Not used with sqlite3.
        'HOST': MYSQL_HOST,
    # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        # 'CONN_MAX_AGE': 60, not work well with gevent greenlet
        'OPTIONS': {
            # 'init_command': 'SET storage_engine=Innodb;',
            'charset': 'utf8',
            # 'sql_mode': 'STRICT_TRANS_TABLES',
        },  # storage_engine need mysql>5.4,and table_type need mysql<5.4
    },
    'readonly': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nidepuzidb',
        'USER': 'nidepuzidbo',
        'PASSWORD': MYSQL_AUTH,
        'HOST': MYSQL_HOST,
        'OPTIONS':  {
            'charset': 'utf8',
        }
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': REDIS_HOST,
        'OPTIONS': {
            'DB': 1,
            'PASSWORD': REDIS_AUTH,
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,  # in seconds
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'PICKLE_VERSION': 2,
            # 'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                # 'timeout': 10,
            }
        }
    }
}

##########################CELERY TASK##########################
CELERY_TASK_ALWAYS_EAGER = False
# CELERY_BROKER_URL = 'redis://:{0}@{1}:6379/9'.format(REDIS_AUTH, REDIS_HOST)
CELERY_BROKER_URL = 'redis://:{0}@{1}/9'.format(REDIS_AUTH, REDIS_HOST)
CELERY_RESULT_BACKEND = 'django-db'

##########################SENTRY RAVEN##########################
import raven
RAVEN_CONFIG = {
    'dsn': 'http://f0c0236fdb0a4350a4aa6a5ca9a26c9e:22cfe813c48e4850956251f7a2f1a924@sentry.nidepuzi.com/12',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(PROJECT_ROOT),
}

######################## RESTFRAMEWORK CONFIG ########################
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
})

######################## WEIXIN CONFIG ########################

WX_NOTIFY_URL = 'http://api.nidepuzi.com/rest/notify/{channel}/'
WX_JS_API_CALL_URL ='http://i.nidepuzi.com/pay/?showwxpaytitle=1'

# ================ 你的铺子特卖[公众号] ==================
WEIXIN_SECRET = ''
WEIXIN_APPID = ''

# ================ 你的铺子[公众号] ==================
WX_PUB_APPID = "wxda1c561964d173cc"
WX_PUB_APPSECRET = "a95e2ab3da3a1f8538b112ec96bf86d3"

WX_PUB_MCHID = "1461964902" #受理商ID，身份标识
WX_PUB_KEY   = "wxpubdanlai201786788764237282186" #支付密钥

WX_PUB_KEY_PEM_PATH = '/data/certs/wxpub_key.pem'
WX_PUB_CERT_PEM_PATH = '/data/certs/wxpub.pem'

# ================ 你的铺子[ APP客户端] ==================
WX_APPID = "wxa6e8010fa0b31eb3"
WX_APPSECRET = "a894a72567440fa7317843d76dd7bf03"

WX_MCHID = "1466508202" #受理商ID，身份标识
WX_KEY   = "wxdanlai201769jiyf78h3j9ekid78dh" #支付密钥

WX_CERT_PEM_PATH = '/data/certs/wxapp.pem'
WX_KEY_PEM_PATH  = '/data/certs/wxapp_key.pem'

# ================ 你的铺子[微信小程序] ==================
WEAPP_APPID  = ''
WEAPP_SECRET = ''

WEAPP_MCHID = "" #受理商ID，身份标识
WEAPP_KEY   = "" #支付密钥

WEAPP_CERT_PEM_PATH = '/data/certs/weapp.pem'
WEAPP_KEY_PEM_PATH  = '/data/certs/weapp_key.pem'

################### ALIPAY SETTINGS ##################
ALIPAY_MCHID     = '2088621767170676'
ALIAPY_APPID     = '2017042206893641'

ALIPAY_GATEWAY_URL = 'https://openapi.alipay.com/gateway.do'
ALIPAY_NOTIFY_URL = 'http://api.nidepuzi.com/rest/notify/alipay/'

ALIPAY_RSA_PUBLIC_KEY_PATH = '/data/certs/alipay.pem'
ALIPAY_RSA_PRIVATE_KEY_PATH = '/data/certs/alipay_key.pem'

######################## 小米推送 CONFIG ########################
IOS_APP_SECRET = ''
ANDROID_APP_SECRET = ''

################### PING++ SETTINGS ##################
PINGPP_CLENTIP = "180.97.163.149"
PINGPP_APPID = ""
PINGPP_APPKEY = ""

################### XIAOLU UNIONPAY SETTINGS ##################
XIAOLU_CLENTIP = "118.178.116.5"

########################### Statsd & Prometheus ##############################
# STATSD_HOST = 'statsd.default.svc.cluster.local'
STATSD_HOST = 'localhost'
STATSD_PORT = 9125
# STATSD_CLIENT = 'celery_statsd.oneapm'
# STATSD_CELERY_SIGNALS = True


#################### TAOBAO SETTINGS ###################
APPKEY = '12545735'  # app name guanyi erp ,younishijie
APPSECRET = '5d845250d49aea44c3a07d8c1d513db5'

################### JINGDONG SETTINGS #################
JD_APP_KEY = 'F9653439C316A32BF49DFFDE8381CBC9'
JD_APP_SECRET = 'f4fe333676af4f4eaeaa00ed20c82086'

################### QINIU SETTINGS ##################
# inherit from base

############################# ALIYUN OCR CONFIG ##############################
ALIYUN_APPCODE = '6dc0d0df019d4e83a704b434391e42b1'
IDCARD_OCR_URL = 'https://dm-51.data.aliyun.com/rest/160601/ocr/ocr_idcard.json'

######################## 蜂巢 CONFIG ########################
FENGCHAO_SLYC_VENDOR_CODE  = 'SLYC_FC'  # 十里洋场vendor_code
FENGCHAO_SLYC_CHANNEL_CODE = 'slyc' # 十里洋场的订单channel
FENGCHAO_DEFAULT_CHANNEL_CODE = 'ndpz'
FENGCHAO_API_GETWAY = 'https://api.fcgylapp.cn/omsapi'
FENGCHAO_APPID  = 'fc936892-227d-403d-974d-ad6d7a02f829'
FENGCHAO_SECRET = 'e475e2d6-5ab3-421e-a607-9768741cedc8'