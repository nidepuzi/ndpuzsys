# coding=utf-8
import os
from .base import *

DEBUG = False
DEPLOY_ENV = False

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 24 * 15 * 60 * 60

############################ FUNCTION SWITCH #############################
ORMCACHE_ENABLE = True # ORMCACHE SWITCH
INGORE_SIGNAL_EXCEPTION = False # signal异常捕获而且不再抛出
APP_PUSH_SWITCH = False  # APP推送开关
SMS_PUSH_SWITCH = False  # 短信推送开关
WEIXIN_PUSH_SWITCH = False  # 微信推送开关
MAMA_MISSION_PUSH_SWITCH = False  # 妈妈周激励推送开关


STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "site_media", "static"),
)
STATIC_ROOT = "/data/site_media/static"
M_STATIC_URL = '/'

# WEB DNS
SITE_URL = 'http://staging.xiaolumm.com/'
#######################  WAP AND WEIXIN CONFIG ########################
M_SITE_URL = 'http://staging.xiaolumm.com'

MYSQL_HOST = 'rm-bp17ea269uu21f9i1.mysql.rds.aliyuncs.com'
MYSQL_AUTH = os.environ.get('MYSQL_AUTH')

REDIS_HOST = 'r-bp1b4317ea5c3714.redis.rds.aliyuncs.com:6379'
REDIS_AUTH = os.environ.get('REDIS_AUTH')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'xiaoludb',  # Or path to database file if using sqlite3.
        'USER': 'xiaoludev',  # Not used with sqlite3.
        'PASSWORD': MYSQL_AUTH,  # Not used with sqlite3.
        'HOST': MYSQL_HOST,
    # Set to empty string for localhost. Not used with sqlite3. #192.168.0.28
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            # 'init_command': 'SET storage_engine=Innodb;',
            'charset': 'utf8',
            # 'sql_mode': 'STRICT_TRANS_TABLES',
        },  # storage_engine need mysql>5.4,and table_type need mysql<5.4
        'TEST': {
            'NAME': 'test_xiaoludb',
            'CHARSET': 'utf8',
        }
    }
}

DJANGO_REDIS_IGNORE_EXCEPTIONS = True
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': REDIS_HOST,
        'OPTIONS': {
            'DB': 17,
            'PASSWORD': REDIS_AUTH,
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,  # in seconds
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'PICKLE_VERSION': 2,
            # 'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 5,
                # 'timeout': 10,
            }
        }
    }
}

##########################CELERY TASK##########################
CLOSE_CELERY = False
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# CELERY_BROKER_URL = 'redis://:{0}@{1}:6379/19'.format(REDIS_AUTH, REDIS_HOST)
CELERY_BROKER_URL = 'redis://:{0}@{1}/19'.format(REDIS_AUTH, REDIS_HOST)
CELERY_RESULT_BACKEND = 'django-db'

##########################SENTRY RAVEN##########################
import raven
RAVEN_CONFIG = {
    'dsn': 'http://2d63e1b731cd4e53a32b0bc096fd3566:a38d367f2c644d81b353dabfbb941070@sentry.xiaolumm.com/4',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(PROJECT_ROOT),
}

########################### ONEAPM Statsd ##############################
STATSD_HOST = 'localhost'
STATSD_PORT = 9125
# STATSD_CLIENT = 'celery_statsd.oneapm'
# STATSD_CELERY_SIGNALS = True
MIDDLEWARE_CLASSES = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # 'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    # 'django_statsd.middleware.GraphiteMiddleware',
) + MIDDLEWARE_CLASSES

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'django_prometheus.middleware.PrometheusAfterMiddleware',
    # 'dogslow.WatchdogMiddleware',
)

######################## WEIXIN CONFIG ########################

WX_NOTIFY_URL = 'http://staging.xiaolumm.com/apis/notify/weixin/'
WX_JS_API_CALL_URL ='http://staging.xiaolumm.com/pay/?showwxpaytitle=1'

# ================ 小鹿美美特卖[公众号] ==================
WEIXIN_SECRET = 'bc41b3a535b095afc55cd40d2e808d9c'
WEIXIN_APPID = 'wxc2848fa1e1aa94b5'

# ================ 小鹿美美[公众号] ==================
WX_PUB_APPID = "wxc2848fa1e1aa94b5"
WX_PUB_APPSECRET = "bc41b3a535b095afc55cd40d2e808d9c"

WX_PUB_MCHID = "1219468801" #受理商ID，身份标识
WX_PUB_KEY   = "ff86c2112994affe1ccb6e32770c4b5e" #支付密钥

WX_PUB_CERT_PEM_PATH = '/data/certs/wx_pub/apiclient_cert.pem'
WX_PUB_KEY_PEM_PATH = '/data/certs/wx_pub/apiclient_key.pem'

WX_PUB_REFUND_USER_ID = 'refundem1@1236482102'
# ================ 小鹿美美[ APP客户端] ==================
WX_APPID = "wx25fcb32689872499"
WX_APPSECRET = "3c7b4e3eb5ae4cfb132b2ac060a872ee"

WX_MCHID = "1268398601" #受理商ID，身份标识
WX_KEY   = "t5UXHfwR7QEv2jMLFuZm8DdqnAT0ON9a" #支付密钥

WX_CERT_PEM_PATH = '/data/certs/wx/apiclient_cert.pem'
WX_KEY_PEM_PATH = '/data/certs/wx/apiclient_key.pem'

WX_REFUND_USER_ID = 'refundem2'
# ================ 小鹿美美[微信小程序] ==================
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
ALIPAY_NOTIFY_URL = 'http://warden.xiaolumm.com/rest/notify/alipay/'

################### SANDPAY SETTINGS ##################
SANDPAY_API_GETWAY           = "http://61.129.71.103:7970/agent-main/openapi"
SANDPAY_RSA_KEY_PATH         = '/data/certs/sandpay_key.pem'
SANDPAY_RSA_CERT_PATH        = "/data/certs/sandpay.pem"
SANDPAY_AGENT_PAY_NOTICE_URL = ""

######################## 小米推送 CONFIG ########################
IOS_APP_SECRET = ''
ANDROID_APP_SECRET = ''

############################## PING++ SETTINGS #########################
PINGPP_CLENTIP = "180.97.163.149"
PINGPP_APPID = "app_LOOajDn9u9WDjfHa"
PINGPP_APPKEY = "sk_test_8y58u9zbPWTKTGGa1GrTi1mT"

#################### TAOBAO SETTINGS ###################
APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

################### JINGDONG SETTINGS #################
JD_APP_KEY = 'F9653439C316A32BF49DFFDE8381CBC9'
JD_APP_SECRET = 'f4fe333676af4f4eaeaa00ed20c82086'

################### QINIU SETTINGS ##################
QINIU_ACCESS_KEY = "M7M4hlQTLlz_wa5-rGKaQ2sh8zzTrdY8JNKNtvKN"
QINIU_SECRET_KEY = "8MkzPO_X7KhYQjINrnxsJ2eq5bsxKU1XmE8oMi4x"
QINIU_PRIVATE_BUCKET = 'invoiceroom'
QINIU_PRIVATE_DOMAIN = '7xrpt3.com2.z0.glb.qiniucdn.com'
QINIU_PUBLIC_BUCKET = 'xiaolumama'
QINIU_PUBLIC_DOMAIN = '7xrst8.com2.z0.glb.qiniucdn.com'

############### REMOTE MEDIA STORAGE ################
QINIU_BUCKET_NAME   = 'mediaroom'
QINIU_BUCKET_DOMAIN = '7xogkj.com1.z0.glb.clouddn.com'

QINIU_SECURE_URL    = 0
DEFAULT_FILE_STORAGE = 'qiniustorage.backends.QiniuStorage'
MEDIA_URL = "http://%s/" % QINIU_BUCKET_DOMAIN

######################## RESTFRAME WORK #########################
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': {
        'auth': '500/hour',
        'anon': '2000/hour',
        'user': '2000/hour'
    },
})

LOGGER_HANDLERS = [
    ('outware', 'sentry,jsonfile'),
    ('service', 'sentry,jsonfile'),
    ('shopback', 'sentry,jsonfile'),
    ('shopapp', 'sentry,jsonfile'),
    ('flashsale', 'sentry,jsonfile'),
    ('core', 'sentry,jsonfile'),
    ('auth', 'sentry,jsonfile'),
    ('pms', 'sentry,jsonfile'),
    ('statistics', 'sentry,jsonfile'),
    ('django.request', 'sentry,jsonfile'),
    ('sentry.errors', 'sentry,jsonfile'),
    ('celery.handler', 'sentry,jsonfile'),
    ('notifyserver.handler', 'sentry,jsonfile'),
    ('yunda.handler', 'sentry,jsonfile'),
    ('mail.handler', 'sentry,jsonfile'),
    ('xhtml2pdf', 'sentry,jsonfile'),
    ('restapi.errors', 'sentry,jsonfile'),
    ('weixin.proxy', 'sentry,jsonfile'),
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
        'jsonfile': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
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

