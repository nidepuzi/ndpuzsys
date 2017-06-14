# coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os.path
import posixpath

import global_setup
global_setup.install_pymysqldb()
global_setup.cancel_pingpp_charge_ssl_verify()


DEBUG = False
DEPLOY_ENV = False
XIAOLU_UNIONPAY_SWICH = True #切换小鹿支付开关

ADMINS = ()

MANAGERS = (
    ('meixqhi', 'xiuqing.mei@xiaolumeimei.com'),
)

ALLOWED_HOSTS = ['*']

# 微信分享备用域名
STANDBY_DOMAINS = [
    ('m.xiaolumeimei.com', 'http'),
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shopmgr',  # Or path to database file if using sqlite3.
        'USER': 'shopmgr',  # Not used with sqlite3.
        'PASSWORD': '123123',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# USE_TZ = True #if true, 时间日期设置都应传入utc时间
TIME_ZONE = 'Asia/Shanghai'

# DATETIME_INPUT_FORMATS = '%Y-%m-%d %H:%M:%S'
# DATE_INPUT_FORMATS = '%Y-%m-%d'
DATETIME_FORMAT = 'Y-m-d H:i:s'
DATE_FORMAT = 'Y-m-d'

LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True

# USE_L10N = True
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

MEDIA_URL = "/media/"

# STATIC_ROOT = os.path.join(PROJECT_ROOT,"static")

STATIC_URL = '/static/'

DOWNLOAD_ROOT = os.path.join(PROJECT_ROOT, "site_media", 'download')

ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

STATIC_DOC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

STATICFILES_DIRS = (
    # os.path.join(PROJECT_ROOT,"site_media","static"),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'zze(^rvhdz(hxx16a788w6jyqhtq%*v_pl^2#t1dskpb!473f8'
ENCRYPTED_FIELDS_KEYDIR = os.path.join(PROJECT_ROOT, 'core/fields/fieldkeys')

MIDDLEWARE_CLASSES = (
    'core.middleware.middleware.XForwardedForMiddleware',
    'core.middleware.middleware.AttachContentTypeMiddleware',
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'core.middleware.middleware.DisableDRFCSRFCheck',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

)

ROOT_URLCONF = 'shopmanager.urls'
WSGI_APPLICATION = 'shopmanager.wsgi.application'

TEMPLATES_ROOT = os.path.join(PROJECT_ROOT, "site_media", "templates")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS =[
    'admin_view_permission',
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'gunicorn',
    'httpproxy',
    'tagging.apps.TaggingConfig',
    "oauth2_provider",
    # 'oauth2_provider.apps.DOTConfig',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'django_celery_results',
    'django_celery_beat',
    'import_export',

    'core',
    'django_statsd',
    'celery_statsd',

    'shopback.amounts',
    'shopback.categorys',
    'shopback.fenxiao',
    'shopback.items',
    'shopback.logistics',
    'shopback.monitor',
    'shopback.orders',
    'shopback.trades',
    'shopback.refunds',
    'shopback.users',
    'shopback.archives',
    'shopback.purchases',
    'shopback.warehouse',
    'shopback.forecast',

    'shopapp.autolist',
    'shopapp.memorule',
    'shopapp.asynctask',
    'shopapp.modifyfee',
    'shopapp.calendar',
    'shopapp.babylist',
    'shopapp.juhuasuan',
    'shopapp.smsmgr',
    'shopapp.yunda',
    'shopapp.comments',
    'shopapp.weixin',
    # 'shopapp.tmcnotify',

    'shopapp.jingdong',
    'shopapp.intercept',
    'shopapp.examination',
    'shopapp.weixin_sales',
    'shopapp.weixin_score',
    'shopapp.weixin_examination',
    'shopapp.sampleproduct',
    'shopapp.STOthermal',

    # 'pms.wavepick',
    'pms.supplier',
    # 'pms.category',
    # 'pms.temai',
    'games.paint',
    'games.bomb',
    'games.luckyawards',
    'games.weixingroup',
    'games.renewremind',

    'flashsale.complain',
    'flashsale.pay',
    'flashsale.finance',
    'flashsale.xiaolumm',
    'shopback.dinghuo',
    'flashsale.workorder',
    'flashsale.luntan',
    'flashsale.clickcount',
    'flashsale.clickrebeta',
    'flashsale.mmexam',
    'flashsale.restpro',
    'flashsale.kefu',
    'flashsale.push',
    'flashsale.promotion',
    'flashsale.apprelease',
    'flashsale.protocol',
    'flashsale.coupon',
    'flashsale.jimay',

    # 'test.celery',
    'shopapp.notify',
    # 'shopapp.zhongtong'

    'statistics',
    'statistics.daystats',

    'flashsale.xiaolupay',

    'shopback.outware',
    'shopback.outware.fengchao',
]

AUTH_PROFILE_MODULE = 'users.user'

AUTHENTICATION_BACKENDS = (
    # 'flashsale.pay.backends.FlashSaleBackend',
    'flashsale.pay.backends.SMSLoginBackend',
    'flashsale.pay.backends.WeixinPubBackend',
    'flashsale.pay.backends.WeixinAppBackend',
    'shopapp.taobao.backends.TaoBaoBackend',
    'shopapp.jingdong.backends.JingDongBackend',
    'django.contrib.auth.backends.ModelBackend'
)

LOGIN_REDIRECT_URL = '/home/'
LOGIN_URL = '/admin/login/'
LOGOUT_URL = '/accounts/logout/'

####################### TRADE HANDLERS CONFIG ########################
TRADE_HANDLERS_PATH = (
    'shopback.trades.handlers.InitHandler',
    'shopback.trades.handlers.ConfirmHandler',
    'shopback.trades.handlers.SplitHandler',
    'shopback.trades.handlers.MemoHandler',
    'shopback.trades.handlers.DefectHandler',
    'shopback.trades.handlers.RuleMatchHandler',
    'shopback.trades.handlers.StockOutHandler',
    'shopback.trades.handlers.MergeHandler',
    'shopback.trades.handlers.RefundHandler',
    'shopback.trades.handlers.LogisticsHandler',
    #    'shopback.trades.handlers.InterceptHandler',
    'shopback.trades.handlers.RegularSaleHandler',
    'shopback.trades.handlers.FinalHandler',
    #    'shopback.trades.handlers.FlashSaleHandler',
)

################### ALIPAY SETTINGS ##################
ALIPAY_MCHID     = '2088911223385116'
ALIAPY_APPID     = '2016012701123211'

ALIPAY_GATEWAY_URL = 'https://openapi.alipay.com/gateway.do'
ALIPAY_NOTIFY_URL = 'http://i.xiaolumm.com/rest/notify/alipay/'

ALIPAY_RSA_PRIVATE_KEY_PATH = '/data/certs/alipay_key.pem'
ALIPAY_RSA_PUBLIC_KEY_PATH = '/data/certs/alipay.pem'

#################### TAOBAO SETTINGS ###################
APPKEY = '21532915'   #app name super ERP test ,younixiaoxiao
APPSECRET = '7232a740a644ee9ad370b08a1db1cf2d'

TAOBAO_API_HOSTNAME = 'eco.taobao.com'
AUTHRIZE_URL = 'https://oauth.taobao.com/authorize'
AUTHRIZE_TOKEN_URL = 'https://oauth.taobao.com/token'
REDIRECT_URI = '/accounts/login/auth/'
TAOBAO_API_ENDPOINT = 'https://%s/router/rest' % TAOBAO_API_HOSTNAME
TAOBAO_NOTIFY_URL = 'http://stream.api.taobao.com/stream'

SCOPE = 'item,promotion,usergrade'
REFRESH_URL = 'https://oauth.taobao.com/token'

API_REQUEST_INTERVAL_TIME = 10  # (seconds)
API_TIME_OUT_SLEEP = 60  # (seconds)
API_OVER_LIMIT_SLEEP = 180  # (seconds)

GEN_AMOUNT_FILE_MIN_DAYS = 20

#################### JINGDONG SETTINGS ###################
JD_API_HOSTNAME = 'gw.api.360buy.com'
JD_AUTHRIZE_URL = 'https://auth.360buy.com/oauth/authorize'
JD_AUTHRIZE_TOKEN_URL = 'https://auth.360buy.com/oauth/token'
JD_REDIRECT_URI = '/app/jd/login/auth/'
JD_API_ENDPOINT = 'http://%s/routerjson' % JD_API_HOSTNAME

#################### PRINT CONFIG ###################
BASE_FONT_PATH = '/data/fonts/'
FANGZHENG_LANTINGHEI_FONT_PATH = '/data/fonts/fzltbold.ttf'
FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif-Bold.ttf'
ASYNC_FILE_PATH = os.path.join(PROJECT_ROOT, "site_media", "asyncfile")

################### HTTPS/SSL SETTINGS ##################
SECURE_SSL_HOST = 'https://m.xiaolumeimei.com'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
HTTPS_SUPPORT = False
SECURE_REQUIRED_PATHS = (
    '/admin/',
)

# ================ 微信支付 ======================
WX_PUB_KEY_PEM_PATH = '/data/certs/wxpub_key.pem'
WX_PUB_CERT_PEM_PATH = '/data/certs/wxpub.pem'

################### WEIXIN SETTINGS ##################
WEIXIN_API_HOST = "https://api.weixin.qq.com"
WEIXIN_MEDIA_HOST = "http://file.api.weixin.qq.com"
WEIXIN_QRCODE_HOST = "https://mp.weixin.qq.com"
WEIXIN_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"

# ================ 小鹿美美[微信小程序] ==================
WEAPP_APPID  = 'wxea4fd45c52e4a20e'
WEAPP_SECRET = '1246301cdb41c6336d82a12600189283'

WEAPP_MCHID = "1410583302" #受理商ID，身份标识
WEAPP_KEY   = "t5UXHfwR7QEv2jMLFuZm8DdqnAT0ON9a" #支付密钥

WEAPP_CERT_PEM_PATH = '/data/certs/weapp_key.pem'
WEAPP_KEY_PEM_PATH  = '/data/certs/weapp.pem'

# ================ 己美医学[公众号] ==================
WX_JIMAY_APPID  = 'wxaf62312f812ce0d8'

################### Ntalker SETTINGS ##################
NTALKER_NOTIFY_URL = 'http://wx.ntalker.com/agent/weixin'
WX_MESSAGE_URL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send'
WX_MEDIA_UPLOAD_URL = 'https://api.weixin.qq.com/cgi-bin/media/upload'
WX_MEDIA_GET_URL = 'https://api.weixin.qq.com/cgi-bin/media/get'

################### KUAIDI KDN SETTINGS ##################
KDN_EBUSINESSID = 1264368
KDN_APIKEY = "b2983220-a56b-4e28-8ca0-f88225ee2e0b"

############################# EXTENSION CONFIG ##############################
TAOBAO_PAGE_SIZE = 50  # the page_size of  per request
# sale order regular days
REGULAR_DAYS = 10

ELASTICSEARCH_LOGGING_HOST = 'elasticsearch-logging.kube-system.svc.cluster.local:9200'

############################# ALIYUN OCR CONFIG ##############################
ALIYUN_APPCODE = '[OVERRIDE PLEASE]'
IDCARD_OCR_URL = 'https://dm-51.data.aliyun.com/rest/160601/ocr/ocr_idcard.json'

######################## 蜂巢 CONFIG ########################
FENGCHAO_SLYC_VENDOR_CODE  = 'fengchao_slyc'  # 十里洋场vendor_code
FENGCHAO_SLYC_CHANNEL_CODE = 'shiliyangchang' # 十里洋场的订单channel
FENGCHAO_DEFAULT_CHANNEL_CODE = 'xiaolumeimei'
FENGCHAO_API_GETWAY = 'http://fctest02.fcgylapp.cn:30003/api/'
FENGCHAO_APPID = '0d14d2b6-042f-48d1-a0f2-fc5592883ec6'
FENGCHAO_SECRET = 'b4ca5a2a-4b76-456b-b01f-4443fddad28a'

############################# TASK SETTINGS ##############################
from .task_settings import *  # celery config

############################## RESTFRAMEWORK CONFIG #########################
REST_FRAMEWORK = {
    #     'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.TemplateHTMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'flashsale.restpro.exceptions.my_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsSetPagination',
    # 'DEFAULT_AUTHENTICATION_CLASSES': (
    #     'rest_framework.authentication.SessionAuthentication',
    #     'rest_framework.authentication.BasicAuthentication',
    # ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'auth': '500/hour',
        'anon': '10000/hour',
        'user': '10000/hour',
    },
}

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_USE_CACHE': 'default',
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15,
    'DEFAULT_CACHE_KEY_FUNC': 'rest_framework_extensions.utils.default_cache_key_func'
}
JSONFIELD_ENCODER_CLASS = 'core.rest.serializers.RestApiJSONEncoder'
