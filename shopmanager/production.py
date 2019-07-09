# coding=utf-8
import os
from .base import *

DEBUG = False
DEPLOY_ENV = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 24 * 30 * 60 * 60

############################ FUNCTION SWITCH #############################
ORMCACHE_ENABLE = True # ORMCACHE SWITCH
INGORE_SIGNAL_EXCEPTION = True # signal异常捕获而且不再抛出
APP_PUSH_SWITCH = True  # APP推送开关
SMS_PUSH_SWITCH = True  # 短信推送开关
WEIXIN_PUSH_SWITCH = True  # 微信推送开关
MAMA_MISSION_PUSH_SWITCH = True  # 妈妈周激励推送开关

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "site_media", "static"),
)
STATIC_ROOT = "/data/site_media/static"
M_STATIC_URL = '/'

# WEB DNS
SITE_URL = 'http://admin.hongguotang.com/'
#######################  WAP AND WEIXIN CONFIG ########################
M_SITE_URL = 'https://m.hongguotang.com'

MYSQL_HOST = 'rdsvrl2p9pu6536n7d99i.mysql.rds.aliyuncs.com'
MYSQL_AUTH = 'KuTa@t^z' #os.environ.get('MYSQL_AUTH')

REDIS_HOST = 'r-bp1b4317ea5c3714.redis.rds.aliyuncs.com:6379'
REDIS_AUTH = 'Huyiinc12345' #os.environ.get('REDIS_AUTH')

if os.environ.get('INSTANCE') == 'mall':
    LOGIN_URL = '/mall/user/login'

MONGODB_URI = '10.132.54.77:27017'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'db_ndpz',  # Or path to database file if using sqlite3.
        'USER': 'dba_ndpz',  # Not used with sqlite3.
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
        'NAME': 'db_ndpz',
        'USER': 'dba_ndpz',
        'PASSWORD': MYSQL_AUTH,
        'HOST': MYSQL_HOST,
        'OPTIONS':  {
            'charset': 'utf8',
        }
    }
}

DJANGO_REDIS_IGNORE_EXCEPTIONS = True
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': REDIS_HOST,
        'OPTIONS': {
            'DB': 100,
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
CLOSE_CELERY = False
# CELERY_BROKER_URL = 'redis://:{0}@{1}:6379/9'.format(REDIS_AUTH, REDIS_HOST)
CELERY_BROKER_URL = 'redis://:{0}@{1}/109'.format(REDIS_AUTH, REDIS_HOST)
CELERY_RESULT_BACKEND = 'django-db'

##########################SENTRY RAVEN##########################
import raven
RAVEN_CONFIG = {
    'dsn': 'http://1e0aad4415454d5c9bbc22ac02a14b2e:42d9a07d79a2462fbc76eb543ac25fbf@sentry.nidepuzi.com/5',
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
WEIXIN_SECRET = 'dbd2103bb55c46c7a019ae1c1089f2fa'
WEIXIN_APPID = 'wx3f91056a2928ad2d'

# ================ 你的铺子[公众号] ==================
WX_PUB_APPID = "wxda1c561964d173cc"
WX_PUB_APPSECRET = "a95e2ab3da3a1f8538b112ec96bf86d3"

WX_PUB_MCHID = "1236482102" #受理商ID，身份标识
WX_PUB_KEY   = "t5UXHfwR7QEv2jMLFuZm8DdqnAT0ON9a" #支付密钥

WX_PUB_CERT_PEM_PATH = '/data/certs/wx_pub/apiclient_cert.pem'
WX_PUB_KEY_PEM_PATH = '/data/certs/wx_pub/apiclient_key.pem'

# ================ 你的铺子[ APP客户端] ==================
WX_APPID = "wx25fcb32689872499"
WX_APPSECRET = "3c7b4e3eb5ae4cfb132b2ac060a872ee"

WX_MCHID = "1268398601" #受理商ID，身份标识
WX_KEY   = "t5UXHfwR7QEv2jMLFuZm8DdqnAT0ON9a" #支付密钥

WX_CERT_PEM_PATH = '/data/certs/wx/apiclient_cert.pem'
WX_KEY_PEM_PATH  = '/data/certs/wx/apiclient_key.pem'

# ================ 你的铺子[微信小程序] ==================
WEAPP_APPID  = 'wxea4fd45c52e4a20e'
WEAPP_SECRET = '1246301cdb41c6336d82a12600189283'

WEAPP_MCHID = "1410583302" #受理商ID，身份标识
WEAPP_KEY   = "t5UXHfwR7QEv2jMLFuZm8DdqnAT0ON9a" #支付密钥

WEAPP_CERT_PEM_PATH = '/data/certs/weapp/apiclient_cert.pem'
WEAPP_KEY_PEM_PATH  = '/data/certs/weapp/apiclient_key.pem'

################### ALIPAY SETTINGS ##################
ALIPAY_MCHID     = '2088911223385116'
ALIAPY_APPID     = '2016012701123211'

ALIPAY_GATEWAY_URL = 'https://openapi.alipay.com/gateway.do'
ALIPAY_NOTIFY_URL = 'http://api.nidepuzi.com/rest/notify/alipay/'

######################## 小米推送 CONFIG ########################
IOS_APP_SECRET = 'UN+ohC2HYHUlDECbvVKefA=='
ANDROID_APP_SECRET = 'WHdmdNYgnXWokStntg87sg=='

################### PING++ SETTINGS ##################
PINGPP_CLENTIP = "180.97.163.149"
PINGPP_APPID = "app_LOOajDn9u9WDjfHa"
PINGPP_APPKEY = "sk_live_HOS4OSW10u5CDyrn5Gn9izLC"

################### XIAOLU UNIONPAY SETTINGS ##################
XIAOLU_CLENTIP = "118.178.116.5"

########################### ONEAPM Statsd ##############################
STATSD_HOST = '121.199.26.226'
STATSD_PORT = 9125
# STATSD_CLIENT = 'celery_statsd.oneapm'
# STATSD_CELERY_SIGNALS = True
MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
) + MIDDLEWARE_CLASSES


#################### TAOBAO SETTINGS ###################
APPKEY = '12545735'  # app name guanyi erp ,younishijie
APPSECRET = '5d845250d49aea44c3a07d8c1d513db5'

################### JINGDONG SETTINGS #################
JD_APP_KEY = 'F9653439C316A32BF49DFFDE8381CBC9'
JD_APP_SECRET = 'f4fe333676af4f4eaeaa00ed20c82086'

################### QINIU SETTINGS ##################
QINIU_ACCESS_KEY = "AeJdr1yBmZhMe56bJ3OpRJ8enHpHa-ShXWc8PHLZ"
QINIU_SECRET_KEY = "a80RgU1FPEh8uh_YEvZKO69KzZc7DxWbP7d4m3Us"

QINIU_PRIVATE_BUCKET = 'private'
QINIU_PRIVATE_DOMAIN = 'oon022osk.bkt.clouddn.com'
QINIU_PUBLIC_BUCKET = 'image'
QINIU_PUBLIC_DOMAIN = 'oon0iwvsw.bkt.clouddn.com'

############### REMOTE MEDIA STORAGE ################
QINIU_BUCKET_NAME   = 'image'
QINIU_BUCKET_DOMAIN = 'oon0iwvsw.bkt.clouddn.com'

QINIU_SECURE_URL    = 0
DEFAULT_FILE_STORAGE = 'qiniustorage.backends.QiniuStorage'
MEDIA_URL = "http://%s/" % QINIU_BUCKET_DOMAIN

############################# ALIYUN OCR CONFIG ##############################
ALIYUN_APPCODE = '6dc0d0df019d4e83a704b434391e42b1'
IDCARD_OCR_URL = 'https://dm-51.data.aliyun.com/rest/160601/ocr/ocr_idcard.json'

LOGGER_HANDLERS = [
    ('outware', 'sentry,jsonfile'),
    ('service', 'sentry,jsonfile'),
    ('shopback', 'sentry,file'),
    ('shopapp', 'sentry,file'),
    ('flashsale', 'sentry,file'),
    ('core', 'sentry,file'),
    ('auth', 'sentry,file'),
    ('pms', 'sentry,file'),
    ('statistics', 'sentry,file'),
    ('dogslow', 'sentry,file'),
    ('django.request', 'sentry,file'),
    ('raven', 'sentry,file'),
    ('sentry.errors', 'sentry,file'),
    ('celery.handler', 'sentry,file'),
    ('notifyserver.handler', 'sentry,file'),
    ('yunda.handler', 'sentry,file'),
    ('mail.handler', 'sentry,file'),
    ('mall', 'sentry,file'),
    ('xhtml2pdf', 'sentry,file'),
    ('restapi.errors', 'sentry,file'),
    ('weixin.proxy', 'sentry,file'),
]

LOGGER_TEMPLATE = {
    'handlers': ['sentry'],
    'level': 'DEBUG',
    'propagate': True,
}

def comb_logger(log_tuple, temp):
    if isinstance(log_tuple, (list, tuple)) and len(log_tuple) == 2:
        temp.update(handlers=log_tuple[1].split(','))
        return log_tuple[0], temp
    return log_tuple[0], temp


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'json': {
            '()': 'core.logger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s  %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/data/log/django/debug-production.log',
            'formatter': 'json'
        },
        'jsonfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/data/log/django/service-production.log',
            'formatter': 'json'
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': dict([comb_logger(handler, LOGGER_TEMPLATE.copy()) for handler in LOGGER_HANDLERS]),
}

