import os
import urllib2

def is_staging_environment():
    return os.environ.get('TARGET') == 'staging'

def setup_djagno_environ():
    if os.environ.get('TARGET') in ('production', 'django18'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    elif os.environ.get('TARGET') in ('staging',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    elif os.environ.get('TARGET') in ('prometheus',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.prometheus")

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")


def install_pymysqldb():
    if not os.environ.get('TARGET') in ('production', 'django18', 'staging', 'prometheus'):
        return
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        print 'pymysql module not found'


def install_redis_with_gevent_socket():
    if not os.environ.get('TARGET') in ('production', 'django18', 'staging', 'prometheus'):
        return
    try:
        from gevent import socket
        import redis.connection
        redis.connection.socket = socket
    except ImportError:
        print 'gevent or redis.connection module not found'


def enable_urllib2_debugmode():
    httpHandler = urllib2.HTTPHandler(debuglevel=1)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
    opener = urllib2.build_opener(httpHandler, httpsHandler)

    urllib2.install_opener(opener)

def cancel_pingpp_charge_ssl_verify():
    try:
        import pingpp
        pingpp.verify_ssl_certs = False
    except Exception, exc:
        print 'cancel pingpp verify error:%s'% exc

def patch_django1_10_core_get_cache():
    try:
        from django.core import cache
        cache.get_cache = lambda name: None
    except Exception, exc:
        print 'patch django core get_cache error:%s'% exc

