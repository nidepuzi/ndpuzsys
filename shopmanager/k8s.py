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
LOGIN_URL = '/mall/user/login'
M_STATIC_URL = '/'

# WEB DNS
SITE_URL = 'http://staging.nidepuzi.com/'
#######################  WAP AND WEIXIN CONFIG ########################
M_SITE_URL = 'https://staging.nidepuzi.com'

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

DJANGO_REDIS_IGNORE_EXCEPTIONS = True
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': REDIS_HOST,
        'OPTIONS': {
            'DB': 11,
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
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
# CELERY_BROKER_URL = 'redis://:{0}@{1}:6379/9'.format(REDIS_AUTH, REDIS_HOST)
CELERY_BROKER_URL = 'redis://:{0}@{1}/19'.format(REDIS_AUTH, REDIS_HOST)
CELERY_RESULT_BACKEND = 'django-db'

##########################SENTRY RAVEN##########################
import raven
RAVEN_CONFIG = {
    'dsn': 'http://c10dc87141bf43c5a03ca5e615893669:ca2792b29a684b2ebd396107f666ffbb@sentry.xiaolumm.com/13',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(PROJECT_ROOT),
}

######################## RESTFRAMEWORK CONFIG ########################
REST_FRAMEWORK.update({
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # ),
})

######################## WEIXIN CONFIG ########################

WX_NOTIFY_URL = 'http://staging.nidepuzi.com/rest/notify/{channel}/'
WX_JS_API_CALL_URL ='http://staging.nidepuzi.com/pay/?showwxpaytitle=1'

# ================ 小鹿美美特卖[公众号] ==================
WEIXIN_SECRET = ''
WEIXIN_APPID = ''

# ================ 小鹿美美[公众号] ==================
WX_PUB_APPID = ""
WX_PUB_APPSECRET = ""

WX_PUB_MCHID = "" #受理商ID，身份标识
WX_PUB_KEY   = "" #支付密钥

WX_PUB_KEY_PEM_PATH = '/data/certs/wxpub_key.pem'
WX_PUB_CERT_PEM_PATH = '/data/certs/wxpub.pem'

# ================ 小鹿美美[ APP客户端] ==================
WX_APPID = ""
WX_APPSECRET = ""

WX_MCHID = "" #受理商ID，身份标识
WX_KEY   = "" #支付密钥

WX_CERT_PEM_PATH = '/data/certs/wxapp.pem'
WX_KEY_PEM_PATH  = '/data/certs/wxapp_key.pem'

# ================ 小鹿美美[微信小程序] ==================
WEAPP_APPID  = ''
WEAPP_SECRET = ''

WEAPP_MCHID = "" #受理商ID，身份标识
WEAPP_KEY   = "" #支付密钥

WEAPP_CERT_PEM_PATH = '/data/certs/weapp.pem'
WEAPP_KEY_PEM_PATH  = '/data/certs/weapp_key.pem'

################### ALIPAY SETTINGS ##################
ALIPAY_MCHID     = ''
ALIAPY_APPID     = ''

ALIPAY_GATEWAY_URL = 'https://openapi.alipay.com/gateway.do'
ALIPAY_NOTIFY_URL = 'http://staging.nidepuzi.com/rest/notify/alipay/'

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
STATSD_HOST = 'localhost'
STATSD_PORT = 9125
# STATSD_CLIENT = 'celery_statsd.oneapm'
# STATSD_CELERY_SIGNALS = True

INSTALLED_APPS.extend([
    'django_prometheus',
])

MIDDLEWARE_CLASSES = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
) + MIDDLEWARE_CLASSES

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'django_prometheus.middleware.PrometheusAfterMiddleware',
    'dogslow.WatchdogMiddleware',
)

########################### DOGSLOW FOR PROMETHEUS ################################
# Watchdog is enabled by default, to temporarily disable, set to False:
DOGSLOW = True

# By default, Watchdog will create log files with the backtraces.
# You can also set the location of where it stores them:
DOGSLOW_LOG_TO_FILE = False

# Log requests taking longer than 25 seconds:
DOGSLOW_TIMER = 3

# Also log to this logger (defaults to none):
DOGSLOW_LOGGER = 'dogslow'
DOGSLOW_LOG_LEVEL = 'WARNING'

# Print (potentially huge!) local stack variables (off by default, use
# True for more detailed, but less manageable reports)
DOGSLOW_STACK_VARS = False

#################### TAOBAO SETTINGS ###################
APPKEY = ''  # app name guanyi erp ,younishijie
APPSECRET = ''

################### JINGDONG SETTINGS #################
JD_APP_KEY = ''
JD_APP_SECRET = ''

################### QINIU SETTINGS ##################
QINIU_ACCESS_KEY = "AeJdr1yBmZhMe56bJ3OpRJ8enHpHa-ShXWc8PHLZ"
QINIU_SECRET_KEY = "a80RgU1FPEh8uh_YEvZKO69KzZc7DxWbP7d4m3Us"
QINIU_PRIVATE_BUCKET = 'private'
QINIU_PRIVATE_DOMAIN = 'oog0oqtpe.bkt.clouddn.com'
QINIU_PUBLIC_BUCKET = 'image'
QINIU_PUBLIC_DOMAIN = 'oog0dvroy.bkt.clouddn.com'

############### REMOTE MEDIA STORAGE ################
QINIU_BUCKET_NAME   = 'image'
QINIU_BUCKET_DOMAIN = 'oog0dvroy.bkt.clouddn.com'
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