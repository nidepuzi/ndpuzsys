# coding=utf-8
from __future__ import absolute_import, unicode_literals

import os
from kombu import Exchange, Queue
from celery.schedules import crontab

########################################################################################################################
#说明:新增queue或定时任务需要注意的地方
#新增queue, 并将queue配置到.drone.yml　启动参数里
#1.CELERY_IMPORTS 增加task实现所在路径
#2.CELERY_QUEUES 增加queue
#3.参考SKU_STATS_ROUTES增加queue专有的route比如your_ROUTES,
#4.并且调用CELERY_ROUTES.update(your_ROUTES)
#
#新增定时任务
#1.CELERY_IMPORTS 增加task实现所在路径
#2.在xx_APP_SCHEDULE里面增加定时任务配置
########################################################################################################################

############################# BASE SETUP ################################

CELERY_BROKER_POOL_LIMIT = 0
CELERY_BROKER_CONNECTION_TIMEOUT = 10
CELERY_WORDER_PREFETCH_MULTIPLIER = 4
if os.environ.get('INSTANCE') == 'celery-gevent':
    # CELERY_BROKER_POOL_LIMIT = 0
    CELERY_WORDER_PREFETCH_MULTIPLIER = 0

# 某个程序中出现的队列，在broker中不存在，则立刻创建它
# CELERY_CREATE_MISSING_QUEUES = True
# 每个worker最多执行40个任务就会被销毁，可防止内存泄露
CELERY_WORKER_MAX_TASKS_PER_CHILD = 300

# 任务发出后，经过一段时间还未收到acknowledge , 就将任务重新交给其他worker执行
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 1800,
    # 'max_connections': 8,
}

# Sensible settings for celery
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_PUBLISH_RETRY = True
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# By default we will ignore result
# If you want to see results and try out tasks interactively, change it to False
# Or change this setting on tasks level
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True
CELERY_SEND_TASK_ERROR_EMAILS = False
CELERY_CHORD_PROPAGATES = True
CELERY_TASK_RESULT_EXPIRES = 24 * 60 * 60  # half hour

# Set redis as celery result backend
CELERY_REDIS_MAX_CONNECTIONS = 8
CELERY_REDIS_SOCKET_CONNECT_TIMEOUT = 30

# Don't use pickle as serializer, json is much safer
CELERY_TASK_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_TIMEZONE = 'Asia/Shanghai'

CELERY_QUEUES = (
    Queue('celery', routing_key='tasks.#'),
    Queue('default', routing_key='tasks.#'),
    Queue('notify', routing_key='notify.#'),
    Queue('weixin', routing_key='weixin.#'),
    Queue('peroid', routing_key='peroid.#'),
    Queue('frency', routing_key='frency.#'),
    Queue('async', routing_key='async.#'),
    Queue('apis', routing_key='apis.#'),
    Queue('mama', routing_key='mama.#'),
    Queue('activevalue', routing_key='activevalue.#'),
    Queue('mamafortune', routing_key='mamafortune.#'),
    Queue('relationship', routing_key='relationship.#'),
    Queue('carryrecord', routing_key='carryrecord.#'),
    Queue('skustats', routing_key='skustats.#'),
    Queue('coupon', routing_key='coupon.#'),
    Queue('integral', routing_key='integral.#'),
    Queue('statistics', routing_key='statistics.#'),
    Queue('logistics', routing_key='logistics.#'),
    Queue('dinghuo', routing_key='dinghuo.#'),
    Queue('carrytotal', routing_key='carrytotal.#'),
    Queue('qrcode', routing_key='qrcode.#'),
    Queue('xiaolupay', routing_key='xiaolupay.#'),
)

CELERY_TASK_QUEUES = CELERY_QUEUES

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

CELERY_IMPORTS = (
    'flashsale.promotion.tasks_activity',
    'shopback.items.tasks_stats',
    'shopback.forecast.apis',
)

APIS_ROUTES = {
    'shopback.forecast.apis.api_create_or_update_forecastinbound_by_orderlist': {
        'queue': 'apis',
        'routing_key': 'apis.api_create_or_update_forecastinbound_by_orderlist',
    },
    'shopback.forecast.apis.api_create_or_update_realinbound_by_inbound': {
        'queue': 'apis',
        'routing_key': 'apis.api_create_or_update_realinbound_by_inbound',
    },
}

XIAOLUPAY_ROUTES = {
    'flashsale.xiaolupay.tasks.tasks_envelope.task_sent_weixin_red_envelope': {
        'queue': 'xiaolupay',
        'routing_key': 'xiaolupay.task_sent_weixin_red_envelope'
    },
    'flashsale.xiaolupay.tasks.tasks_envelope.task_sync_weixin_red_envelope_by_id': {
        'queue': 'xiaolupay',
        'routing_key': 'xiaolupay.task_sync_weixin_red_envelope_by_id'
    },
    'flashsale.xiaolupay.tasks.tasks_envelope.task_sync_weixin_red_envelopes': {
        'queue': 'xiaolupay',
        'routing_key': 'xiaolupay.task_sync_weixin_red_envelopes'
    },
}

DINGHUO_ROUTES = {
    'shopback.dinghuo.tasks.task_check_purchaseorder_booknum': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_check_purchaseorder_booknum',
    },
    'shopback.dinghuo.tasks.task_packageskuitem_check_purchaserecord': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_packageskuitem_check_purchaserecord',
    },
    'shopback.dinghuo.tasks.task_packageskuitem_update_purchase_arrangement': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_packageskuitem_update_purchase_arrangement',
    },
    'shopback.dinghuo.tasks.task_purchase_detail_update_purchase_order': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_purchase_detail_update_purchase_order',
    },
    'shopback.dinghuo.tasks.task_purchasedetail_update_orderdetail': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_purchasedetail_update_orderdetail',
    },
    'shopback.dinghuo.tasks.task_orderdetail_update_orderlist': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_orderdetail_update_orderlist',
    },
    'shopback.dinghuo.tasks.task_purchasearrangement_update_purchasedetail': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_purchasearrangement_update_purchasedetail',
    },
    'shopback.dinghuo.tasks.task_start_booking': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_start_booking',
    },
    'shopback.dinghuo.tasks.task_purchaserecord_adjust_purchasearrangement_overbooking': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_purchaserecord_adjust_purchasearrangement_overbooking',
    },
    'shopback.dinghuo.tasks.task_purchaserecord_sync_purchasearrangement_status': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_purchaserecord_sync_purchasearrangement_status',
    },
    'shopback.dinghuo.tasks.task_check_arrangement': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_check_arrangement',
    },
    'shopback.dinghuo.tasks.task_update_purchasedetail_status': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_update_purchasedetail_status',
    },
    'shopback.dinghuo.tasks.task_update_purchasearrangement_status':{
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_update_purchasearrangement_status',
    },
    'shopback.dinghuo.tasks.task_update_purchasearrangement_initial_book': {
        'queue': 'dinghuo',
        'routing_key':'dinghuo.task_update_purchasearrangement_initial_book',
    },
    'shopback.dinghuo.tasks.task_update_order_group_key': {
        'queue': 'dinghuo',
        'routing_key': 'dinghuo.task_update_order_group_key',
    },
}

SKU_STATS_ROUTES = {
    'shopback.items.tasks_stats.task_productsku_create_productskustats': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_productsku_create_productskustats',
    },
    'flashsale.restpro.tasks.task_add_shoppingcart_num': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_add_shoppingcart_num',
    },
    'shopback.items.tasks_stats.task_shoppingcart_update_productskustats_shoppingcart_num': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_shoppingcart_update_productskustats_shoppingcart_num',
    },
    'shopback.items.tasks_stats.task_packageskuitem_update_productskustats': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_packageskuitem_update_productskustats',
    },
    'shopback.items.tasks_stats.task_saleorder_update_productskustats_waitingpay_num': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_saleorder_update_productskustats_waitingpay_num',
    },
    'shopback.items.tasks_stats.task_update_product_sku_stat_rg_quantity': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_update_product_sku_stat_rg_quantity',
    },
    'shopback.items.tasks_stats.task_refundproduct_update_productskustats_return_quantity': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_refundproduct_update_productskustats_return_quantity',
    },

    'shopback.trades.tasks.tasks.task_packageskuitem_update_productskusalestats_num': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_packageskuitem_update_productskusalestats_num',
    },
    'shopback.trades.tasks.tasks.task_trade_merge': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_trade_merge',
    },

    'shopback.items.tasks_stats.task_product_downshelf_update_productskusalestats': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_product_downshelf_update_productskusalestats',
    },
    'shopback.items.tasks_stats.task_product_upshelf_update_productskusalestats': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_product_upshelf_update_productskusalestats',
    },
    'shopback.items.tasks_stats.task_product_upshelf_notify_favorited_customer': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_product_upshelf_notify_favorited_customer',
    },
    'flashsale.pay.tasks.task_tongji_trade_source': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_tongji_trade_source',
    },
    'flashsale.push.tasks.task_push_trade_pay_notify': {
        'queue': 'skustats',
        'routing_key': 'skustats.task_push_trade_pay_notify',
    },
}


DAILY_STATS_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_confirm_previous_dailystats': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_confirm_previous_dailystats',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_visitor_increment_dailystats': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_visitor_increment_dailystats',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_carryrecord_update_dailystats': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_carryrecord_update_dailystats',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_ordercarry_increment_dailystats': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_ordercarry_increment_dailystats',
    },
}

ACTIVE_VALUE_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_activevalue.task_confirm_previous_activevalue': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_confirm_previous_activevalue',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_activevalue.task_fans_update_activevalue': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_fans_update_activevalue',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_activevalue.task_ordercarry_update_activevalue': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_ordercarry_update_activevalue',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_activevalue.task_referal_update_activevalue': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_referal_update_activevalue',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_activevalue.task_visitor_increment_activevalue': {
        'queue': 'activevalue',
        'routing_key': 'activevalue.task_visitor_increment_activevalue',
    }
}

MAMA_FORTUNE_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_xiaolumama_update_mamafortune': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_xiaolumama_update_mamafortune',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_activevalue_update_mamafortune': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_activevalue_update_mamafortune',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_invite_num': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_invite_num',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_invite_trial_num': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_invite_trial_num',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_fans_num': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_fans_num',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_order_num': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_order_num',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_mama_level': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_mama_level',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_send_activate_award': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_send_activate_award',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_active_num': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_active_num',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_update_mamafortune_hasale_num': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_update_mamafortune_hasale_num',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_mama_daily_app_visit_stats': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_mama_daily_app_visit_stats',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_mama_daily_tab_visit_stats': {
        'queue': 'mamafortune',
        'routing_key': 'mamafortune.task_mama_daily_tab_visit_stats',
    },
}

MAMA_RELATIONSHIP_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_relationship_visitor.task_update_unique_visitor': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_update_unique_visitor',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_relationship_visitor.task_update_referal_relationship': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_update_referal_relationship',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_relationship_visitor.task_update_group_relationship': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_update_group_relationship',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_relationship_visitor.task_login_activate_appdownloadrecord': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_login_activate_appdownloadrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_relationship_visitor.task_login_create_appdownloadrecord': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_login_create_appdownloadrecord',
    },
    'flashsale.promotion.tasks_activity.task_appdownloadrecord_update_fans': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_appdownloadrecord_update_fans',
    },
    'flashsale.promotion.tasks_activity.task_activate_application': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_activate_application',
    },
    'flashsale.promotion.tasks_activity.task_generate_red_envelope': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_generate_red_envelope',
    },
    'flashsale.promotion.tasks_activity.task_envelope_create_budgetlog': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_envelope_create_budgetlog',
    },
    'flashsale.promotion.tasks_activity.task_envelope_update_budgetlog': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_envelope_update_budgetlog',
    },
    'flashsale.promotion.tasks_activity.task_userinfo_update_application': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_userinfo_update_application',
    },
    'flashsale.promotion.tasks_activity.task_decide_award_winner': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_decide_award_winner',
    },
    'flashsale.promotion.tasks_activity.task_sampleapply_update_appdownloadrecord': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_sampleapply_update_appdownloadrecord',
    },
    'flashsale.promotion.tasks_activity.task_create_appdownloadrecord_with_userinfo': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_create_appdownloadrecord_with_userinfo',
    },
    'flashsale.promotion.tasks_activity.task_create_appdownloadrecord_with_mobile': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_create_appdownloadrecord_with_mobile',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_create_lessonattendrecord': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_create_lessonattendrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_create_instructor_application': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_create_instructor_application',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_lessonattendrecord_create_topicattendrecord': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_lessonattendrecord_create_topicattendrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_topicattendrecord_validate_lessonattendrecord': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_topicattendrecord_validate_lessonattendrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_update_topic_attender_num': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_update_topic_attender_num',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_update_lesson_attender_num': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_update_lesson_attender_num',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_lesson_update_instructor_attender_num': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_lesson_update_instructor_attender_num',
    },
    'flashsale.xiaolumm.tasks.tasks_lesson.task_lesson_update_instructor_payment': {
        'queue': 'relationship',
        'routing_key': 'relationship.task_lesson_update_instructor_payment',
    },
}

MAMA_CARRY_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_clickcarry.task_confirm_previous_zero_order_clickcarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_confirm_previous_zero_order_clickcarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_clickcarry.task_confirm_previous_order_clickcarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_confirm_previous_order_clickcarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_clickcarry.task_visitor_increment_clickcarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_visitor_increment_clickcarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_clickcarry.task_update_clickcarry_order_number': {
        'queue': 'mama',
        'routing_key': 'mama.task_update_clickcarry_order_number',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.task_referal_update_awardcarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_referal_update_awardcarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.task_update_group_awardcarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_update_group_awardcarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.task_update_ordercarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_update_ordercarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.task_update_second_level_ordercarry': {
        'queue': 'mama',
        'routing_key': 'mama.task_update_second_level_ordercarry',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.task_update_second_level_ordercarry_by_trial': {
        'queue': 'mama',
        'routing_key': 'mama.task_update_second_level_ordercarry_by_trial',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.task_order_trigger': {
        'queue': 'mama',
        'routing_key': 'mama.task_order_trigger',
    },
    'flashsale.xiaolumm.tasks.tasks_mama.carryrecord_update_xiaolumama_active_hasale': {
        'queue': 'mama',
        'routing_key': 'mama.carryrecord_update_xiaolumama_active_hasale',
    },
    'flashsale.xiaolumm.tasks.mission.task_create_or_update_mama_mission_state': {
        'queue': 'mama',
        'routing_key': 'mama.task_create_or_update_mama_mission_state',
    },
    'flashsale.xiaolumm.tasks.mission.task_push_mission_state_msg_to_weixin_user': {
        'queue': 'mama',
        'routing_key': 'mama.task_push_mission_state_msg_to_weixin_user',
    },
    'flashsale.xiaolumm.tasks.mission.task_cancel_or_finish_mama_mission_award': {
        'queue': 'mama',
        'routing_key': 'mama.task_cancel_or_finish_mama_mission_award',
    },
}

# MAMA_REGISTER_ROUTE = {
#     'flashsale.xiaolumm.tasks.task_unitary_mama': {
#         'queue': 'mama',
#         'routing_key': 'mama.task_unitary_mama',
#     },
#     'flashsale.xiaolumm.tasks.task_register_mama': {
#         'queue': 'mama',
#         'routing_key': 'mama.task_register_mama',
#     },
#     'flashsale.xiaolumm.tasks.task_renew_mama': {
#         'queue': 'mama',
#         'routing_key': 'mama.task_renew_mama',
#     },
# }

MAMA_CARRYRECORD_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_carryrecord.task_awardcarry_update_carryrecord': {
        'queue': 'carryrecord',
        'routing_key': 'carryrecord.task_awardcarry_update_carryrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_carryrecord.task_ordercarry_update_carryrecord': {
        'queue': 'carryrecord',
        'routing_key': 'carryrecord.task_ordercarry_update_carryrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_carryrecord.task_clickcarry_update_carryrecord': {
        'queue': 'carryrecord',
        'routing_key': 'carryrecord.task_clickcarry_update_carryrecord',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_first_order_send_award': {
        'queue': 'carryrecord',
        'routing_key': 'carryrecord.task_first_order_send_award',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_new_guy_task_complete_send_award': {
        'queue': 'carryrecord',
        'routing_key': 'carryrecord.task_new_guy_task_complete_send_award',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_fortune.task_subscribe_weixin_send_award': {
        'queue': 'carryrecord',
        'routing_key': 'carryrecord.task_subscribe_weixin_send_award',
    },

}
MAMA_CARRYTOTAL_ROUTES = {
    'flashsale.xiaolumm.tasks.tasks_mama_carry_total.task_fortune_update_week_carry_total': {
        'queue': 'carrytotal',
        'routing_key': 'carrytotal.task_fortune_update_week_carry_total',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_carry_total.task_fortune_update_activity_carry_total': {
        'queue': 'carrytotal',
        'routing_key': 'carrytotal.task_fortune_update_activity_carry_total',
    },
}

FLASHSALE_COUPON_ROUTES = {
    'flashsale.coupon.tasks.transfer_coupon.task_send_transfer_coupons': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_send_transfer_coupons',
    },
    'flashsale.coupon.tasks.coupontemplate.task_update_tpl_released_coupon_nums': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_update_tpl_released_coupon_nums',
    },
    'flashsale.coupon.tasks.ordershare_coupon.task_update_share_coupon_release_count': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_update_share_coupon_release_count',
    },
    'flashsale.coupon.tasks.usercoupon.task_update_coupon_use_count': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_update_coupon_use_count',
    },
    'flashsale.coupon.tasks.usercoupon.task_release_coupon_for_order': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_release_coupon_for_order',
    },
    'flashsale.coupon.tasks.usercoupon.task_freeze_coupon_by_refund': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_freeze_coupon_by_refund',
    },
    'flashsale.coupon.tasks.usercoupon.task_release_mama_link_coupon': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_release_mama_link_coupon',
    },
    'flashsale.coupon.tasks.usercoupon.task_return_user_coupon_by_trade': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_return_user_coupon_by_trade',
    },
    'flashsale.coupon.tasks.usercoupon.task_update_mobile_download_record': {
        'queue': 'coupon',
        'routing_key': 'coupon.task_update_mobile_download_record',
    },
}

FLASHSALE_INTEGRAL_ROUTES = {
    'flashsale.pay.tasks.task_add_user_order_integral': {
        'queue': 'integral',
        'routing_key': 'integral.task_add_user_order_integral',
    },
    'flashsale.pay.tasks.task_calculate_total_order_integral': {
        'queue': 'integral',
        'routing_key': 'integral.task_calculate_total_order_integral',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_calc_xlmm_elite_score': {
        'queue': 'integral',
        'routing_key': 'integral.task_calc_xlmm_elite_score',
    },
}

STATISTICS_ROUTES = {
    'shopback.items.tasks.task_supplier_update_product_ware_by': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_supplier_update_product_ware_by',
    },
    'statistics.tasks.task_statistics_product_sale_num': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_statistics_product_sale_num',
    },
    'statistics.tasks.task_update_sale_order_stats_record': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_update_sale_order_stats_record',
    },
    'statistics.tasks.task_statsrecord_update_salestats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_statsrecord_update_salestats',
    },
    'statistics.tasks.task_update_parent_sale_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_update_parent_sale_stats',
    },

    'statistics.tasks.task_update_agg_sale_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_update_agg_sale_stats',
    },
    'statistics.tasks.task_update_product_sku_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_update_product_sku_stats',
    },
    'statistics.tasks.task_update_parent_stock_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_update_parent_stock_stats',
    },
    'statistics.tasks.task_update_agg_stock_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_update_agg_stock_stats',
    },
    'statistics.tasks.task_statsrecord_update_model_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_statsrecord_update_model_stats',
    },
    'pms.supplier.tasks.task_calculate_supplier_stats_data': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_calculate_supplier_stats_data',
    },
}

LOGISTICS_ROUTES = {
    # 'flashsale.restpro.tasks.get_third_apidata': {
    #     'queue': 'logistics',
    #     'routing_key': 'logistics.get_third_apidata',
    # },
    # 'flashsale.restpro.tasks.get_third_apidata_by_packetid': {
    #     'queue': 'logistics',
    #     'routing_key': 'logistics.get_third_apidata_by_packetid',
    # },
    # 'flashsale.restpro.tasks.SaveWuliu_only': {
    #     'queue': 'logistics',
    #     'routing_key': 'logistics.SaveWuliu_only',
    # },  # 更新物流信息
    # 'flashsale.restpro.tasks.SaveWuliu_by_packetid': {
    #     'queue': 'logistics',
    #     'routing_key': 'logistics.SaveWuliu_by_packetid',
    # },
    # 'flashsale.restpro.tasks.SaveReturnWuliu_by_packetid':{ #by huazi 根据物流号和物流公司更新物流状态写入数据库
    #     'queue':'logistics',
    #     'routing_key': 'logistics.SaveReturnWuliu_by_packetid',
    # },
    # 'flashsale.restpro.tasks.get_third_apidata_by_packetid_return':{  #by huazi  调用第三方api 查得最新物流状态
    #     'queue':'logistics',
    #     'routing_key': 'logistics.get_third_apidata_by_packetid_return',
    # },
    'flashsale.restpro.tasks.kdn_sub': {  # by huazi  调用kdn订阅接口
        'queue': 'logistics',
        'routing_key': 'logistics.kdn_sub',
    }
}

WEIXIN_ROUTES = {
    'shopapp.weixin.tasks.subscribe.task_subscribe_or_unsubscribe_update_userinfo': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_subscribe_or_unsubscribe_update_userinfo',
    },
    'shopapp.weixin.tasks.xiaolumama.task_weixinfans_update_xlmmfans': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_weixinfans_update_xlmmfans',
    },
    'shopapp.weixin.tasks.xiaolumama.task_weixinfans_create_subscribe_awardcarry': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_weixinfans_create_subscribe_awardcarry',
    },
    'shopapp.weixin.tasks.xiaolumama.task_weixinfans_create_fans_awardcarry': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_weixinfans_create_fans_awardcarry',
    },
    'shopapp.weixin.tasks.xiaolumama.task_get_unserinfo_and_create_accounts': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_get_unserinfo_and_create_accounts',
    },
    'shopapp.weixin.tasks.xiaolumama.task_create_scan_customer': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_create_scan_customer',
    },
    'shopapp.weixin.tasks.xiaolumama.task_create_scan_xiaolumama': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_create_scan_xiaolumama',
    },
    'shopapp.weixin.tasks.xiaolumama.task_activate_xiaolumama': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_activate_xiaolumama',
    },
    'shopapp.weixin.tasks.xiaolumama.task_create_scan_potential_mama': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_create_scan_potential_mama',
    },
    'shopapp.weixin.tasks.xiaolumama.task_create_or_update_weixinfans_upon_subscribe_or_scan': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_create_or_update_weixinfans_upon_subscribe_or_scan',
    },
    'shopapp.weixin.tasks.xiaolumama.task_update_weixinfans_upon_unsubscribe': {
        'queue': 'weixin',
        'routing_key': 'weixin.task_update_weixinfans_upon_unsubscribe',
    },
}

QRCODE_ROUTES = {
    'shopapp.weixin.tasks.xiaolumama.task_create_mama_and_response_manager_qrcode': {
        'queue': 'qrcode',
        'routing_key': 'qrcode.task_create_mama_and_response_manager_qrcode',
    },
    'shopapp.weixin.tasks.xiaolumama.task_create_mama_referal_qrcode_and_response_weixin': {
        'queue': 'qrcode',
        'routing_key': 'qrcode.task_create_mama_referal_qrcode_and_response_weixin',
    },
    'shopapp.weixin.tasks.xiaolumama.task_fetch_wxpub_mama_custom_qrcode_url': {
        'queue': 'qrcode',
        'routing_key': 'qrcode.task_fetch_wxpub_mama_custom_qrcode_url',
    },
}

BOUTIQUE_ROUTES = {
    'statistics.daystats.tasks.boutique.task_boutique_sale_and_refund_stats': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_boutique_sale_and_refund_stats',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_check_xlmm_exchg_order': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_check_xlmm_exchg_order',
    },
    'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_check_xlmm_return_exchg_order': {
        'queue': 'statistics',
        'routing_key': 'statistics.task_check_xlmm_return_exchg_order',
    },
}

OUTWARE_ROUTES = {
    'outware.tasks.async.task_outware_union_supplier_and_sku': {
        'queue': 'outware',
        'routing_key': 'outware.task_outware_union_supplier_and_sku',
    },
    'outware.tasks.async.task_sync_sku_stocks': {
        'queue': 'outware',
        'routing_key': 'outware.task_sync_sku_stocks',
    },
}

CELERY_ROUTES = {
    'flashsale.xiaolumm.tasks.base.task_Push_Pending_Carry_Cash': {
        'queue': 'peroid',
        'routing_key': 'peroid.push_xlmm_pending_cash',
    },  # 结算你的铺子妈妈们待确认提成
    'flashsale.xiaolumm.tasks.mission.task_batch_create_or_update_mama_mission_state': {
        'queue': 'peroid',
        'routing_key': 'peroid.task_batch_create_or_update_mama_mission_state',
    },
    'flashsale.xiaolumm.tasks.mission.task_batch_push_mission_state_msg_to_weixin_user': {
        'queue': 'peroid',
        'routing_key': 'peroid.task_batch_push_mission_state_msg_to_weixin_user',
    },
    #######################################################
    'shopapp.notify.tasks.process_trade_notify_task': {
        'queue': 'notify',
        'routing_key': 'notify.process_trade_notify',
    },  # 淘宝订单消息处理
    'flashsale.pay.tasks.notifyTradePayTask': {
        'queue': 'notify',
        'routing_key': 'notify.pingpp_paycallback',
    },  # 你的铺子特卖平台订单支付消息处理
    'flashsale.pay.tasks.notifyTradeRefundTask': {
        'queue': 'notify',
        'routing_key': 'notify.ping_refundcallback',
    },  # 你的铺子特卖平台订单退款消息处理
    'flashsale.pay.tasks.pushTradeRefundTask': {
        'queue': 'notify',
        'routing_key': 'notify.push_trade_refund',
    },  # 你的铺子特卖平台订单退款更新到仓库订单
    'flashsale.pay.tasks.confirmTradeChargeTask': {
        'queue': 'notify',
        'routing_key': 'notify.confirm_trade_charge',
    },  # 你的铺子订单确认支付
    'flashsale.pay.tasks.task_saleorder_post_update_send_signal': {
        'queue': 'notify',
        'routing_key': 'notify.task_saleorder_post_update_send_signal',
    },  # 你的铺子特卖平台订单更新事件通知
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_push_ninpic_remind': {
        'queue': 'notify',
        'routing_key': 'notify.task_push_ninpic_remind',
    },  # 九张图更新推送代理
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_app_push_ordercarry': {
        'queue': 'notify',
        'routing_key': 'notify.task_app_push_ordercarry',
    },  # 妈妈奖金APP推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_sms_push_mama': {
        'queue': 'notify',
        'routing_key': 'notify.task_sms_push_mama',
    },  # 新加入１元妈妈短信推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_push_mama_cashout_msg': {
        'queue': 'notify',
        'routing_key': 'notify.task_push_mama_cashout_msg',
    },  # 代理有提现成功推送消息提醒
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_weixin_push_awardcarry': {
        'queue': 'notify',
        'routing_key': 'notify.task_weixin_push_awardcarry',
    },  # 妈妈奖金微信推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_weixin_push_clickcarry': {
        'queue': 'notify',
        'routing_key': 'notify.task_weixin_push_clickcarry',
    },  # 妈妈点击收益微信推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_weixin_push_mama_coupon_audit': {
        'queue': 'notify',
        'routing_key': 'notify.task_weixin_push_mama_coupon_audit',
    },  # 妈妈精品券申请审核微信推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_weixin_push_ordercarry': {
        'queue': 'notify',
        'routing_key': 'notify.task_weixin_push_ordercarry',
    },  # 妈妈奖金微信推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_weixin_push_update_app': {
        'queue': 'notify',
        'routing_key': 'notify.task_weixin_push_update_app',
    },  # 妈妈APP更新微信推送
    'flashsale.xiaolumm.tasks.tasks_mama_push.task_weixin_push_invite_trial': {
        'queue': 'notify',
        'routing_key': 'notify.task_weixin_push_invite_trial',
    },  # 妈妈邀请体验妈妈微信推送
    'shopapp.weixin.tasks.tasks_order_push.task_pintuan_success_push': {
        'queue': 'notify',
        'routing_key': 'notify.task_order_push_pintuan_success',
    },  # 拼团成功微信推送
    'shopapp.weixin.tasks.tasks_order_push.task_pintuan_fail_push': {
        'queue': 'notify',
        'routing_key': 'notify.task_order_push_pintuan_fail',
    },  # 拼团失败微信推送
    'flashsale.pay.tasks.task_release_coupon_push': {
        'queue': 'notify',
        'routing_key': 'notify.task_release_coupon_push',
    },  # 用户领取优惠券推送消息
    'shopapp.smsmgr.tasks.task_notify_package_post': {
        'queue': 'notify',
        'routing_key': 'notify.task_notify_package_post',
    },  # 用户钱包更新后解冻冻结的优惠券
    'flashsale.pay.tasks.task_userbudget_post_save_unfreeze_coupon': {
        'queue': 'notify',
        'routing_key': 'notify.task_userbudget_post_save_unfreeze_coupon',
    },  # 更新妈妈钱包金额
    #######################################################
    'flashsale.clickcount.tasks.task_Create_Click_Record': {
        'queue': 'frency',
        'routing_key': 'frency.task_Create_Click_Record',
    },  # 微信用户点击记录
    'flashsale.clickcount.tasks.task_Update_User_Click': {
        'queue': 'frency',
        'routing_key': 'frency.task_Update_User_Click',
    },  # 微信用户点击记录
    'flashsale.pay.tasks.task_Update_Sale_Customer': {
        'queue': 'frency',
        'routing_key': 'frency.update_sale_customer',
    },  # 保存微信用户OPENID信息

    'flashsale.pay.tasks.task_sync_xlmm_fans_nick_thumbnail': {
        'queue': 'frency',
        'routing_key': 'frency.task_sync_xlmm_fans_nick_thumbnail',
    },  # 更新粉丝用户头像以及昵称
    'flashsale.pay.tasks.task_sync_xlmm_mobile_by_customer': {
        'queue': 'frency',
        'routing_key': 'frency.task_sync_xlmm_mobile_by_customer',
    },  # 更新你的铺子妈妈的手机号码

    'shopapp.weixin.tasks.base.task_Update_Weixin_UserInfo': {
        'queue': 'frency',
        'routing_key': 'frency.update_weixin_userinfo',
    },  # 更新微信用户信息
    'shopapp.smsmgr.tasks.task_register_code': {
        'queue': 'frency',
        'routing_key': 'frency.task_register_code',
    },  # 更新物流信息
    'shopapp.smsmgr.tasks.task_notify_lack_refund': {
        'queue': 'frency',
        'routing_key': 'frency.task_notify_lack_refund',
    },  # 缺货退款通知
    #######################################################
    'shopapp.asynctask.tasks.task_print_async': {
        'queue': 'async',
        'routing_key': 'async.async_invoice_print',
    },  # 发货单打印任务
    'shopapp.asynctask.tasks.task_print_async2': {
        'queue': 'async',
        'routing_key': 'async.async_invoice_print',
    },  # 发货单打印任务
    'shopback.trades.tasks.tasks.sendTaobaoTradeTask': {
        'queue': 'async',
        'routing_key': 'async.sendTaobaoTradeTask',
    },  # 订单发货任务
    'shopback.trades.tasks.tasks.sendTradeCallBack': {
        'queue': 'async',
        'routing_key': 'async.sendTradeCallBack',
    },  # 订单发货回调任务
    'shopback.trades.tasks.tasks.send_package_task': {
        'queue': 'async',
        'routing_key': 'async.send_package_task',
    },  # 包裹发货任务
    'shopback.trades.tasks.tasks.send_package_call_Backs': {
        'queue': 'async',
        'routing_key': 'async.send_package_call_Back',
    },  # 包裹发货任务
    'shopback.trades.tasks.tasks.uploadTradeLogisticsTask': {
        'queue': 'async',
        'routing_key': 'async.uploadTradeLogisticsTask',
    },  # 上传订单物流信息任务
    'shopback.trades.tasks.tasks.deliveryTradeCallBack': {
        'queue': 'async',
        'routing_key': 'async.deliveryTradeCallBack',
    },  # 上传订单物流回调任务
    'shopback.dinghuo.tasks.get_sale_amount_by_product': {
        'queue': 'async',
        'routing_key': 'async.get_sale_amount_by_product',
    },  # 获取特卖商品销售统计
    'shopback.dinghuo.tasks.task_supplier_stat': {
        'queue': 'async',
        'routing_key': 'async.task_supplier_stat',
    },  # 获取特卖供应商统计
    'shopback.dinghuo.tasks.task_ding_huo': {
        'queue': 'async',
        'routing_key': 'async.task_ding_huo',
    },  # 大货统计
    'shopback.dinghuo.tasks.task_ding_huo_optimize': {
        'queue': 'async',
        'routing_key': 'async.task_ding_huo_optimize',
    },  # 大货统计优化
    'shopback.dinghuo.tasks.calcu_refund_info_by_pro_v2': {
        'queue': 'async',
        'routing_key': 'async.calcu_refund_info_by_pro_v2',
    },  # 特卖商品退款数统计
    'flashsale.pay.tasks.task_Record_Mama_Fans': {
        'queue': 'async',
        'routing_key': 'async.task_Record_Mama_Fans',
    },  # 特卖商品退款数统计
}

CELERY_ROUTES.update(WEIXIN_ROUTES)
CELERY_ROUTES.update(DAILY_STATS_ROUTES)
CELERY_ROUTES.update(ACTIVE_VALUE_ROUTES)
CELERY_ROUTES.update(MAMA_FORTUNE_ROUTES)
CELERY_ROUTES.update(MAMA_RELATIONSHIP_ROUTES)
CELERY_ROUTES.update(MAMA_CARRY_ROUTES)
CELERY_ROUTES.update(MAMA_CARRYRECORD_ROUTES)
CELERY_ROUTES.update(MAMA_CARRYTOTAL_ROUTES)
# CELERY_ROUTES.update(MAMA_REGISTER_ROUTE)
CELERY_ROUTES.update(SKU_STATS_ROUTES)
CELERY_ROUTES.update(FLASHSALE_COUPON_ROUTES)
CELERY_ROUTES.update(FLASHSALE_INTEGRAL_ROUTES)
CELERY_ROUTES.update(STATISTICS_ROUTES)
CELERY_ROUTES.update(LOGISTICS_ROUTES)
CELERY_ROUTES.update(APIS_ROUTES)
CELERY_ROUTES.update(DINGHUO_ROUTES)
CELERY_ROUTES.update(QRCODE_ROUTES)
CELERY_ROUTES.update(BOUTIQUE_ROUTES)
CELERY_ROUTES.update(XIAOLUPAY_ROUTES)
CELERY_ROUTES.update(OUTWARE_ROUTES)

CELERY_TASK_ROUTES = CELERY_ROUTES

####### schedule task  ########
SYNC_MODEL_SCHEDULE = {
    u'定时淘宝商城订单增量下载任务': {
        'task': 'shopback.orders.tasks.updateAllUserIncrementTradesTask',
        'schedule': crontab(minute="0", hour="*/6"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.updateAllUserIncrementTradesTask'}
    },
    u'定时淘宝商城待发货订单下载任务': {
        'task': 'shopback.orders.tasks.updateAllUserWaitPostOrderTask',
        'schedule': crontab(minute="*/30", hour="8,10,12,14,16,17,18,19"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.updateAllUserWaitPostOrderTask'}
    },
    u'定时淘宝退款订单下载任务':{     #更新昨日退货退款单
         'task':'shopback.refunds.tasks.updateAllUserRefundOrderTask',
         'schedule':crontab(minute="0",hour='8,12,16'),
         'args':(1,None,None,),
         'options': {'queue': 'peroid', 'routing_key': 'peroid.updateAllUserRefundOrderTask'}
     },
    u'定时更新设置提醒的订单入问题单': {  # 更新定时提醒订单
        'task': 'shopback.trades.tasks.tasks.regularRemainOrderTask',
        'schedule': crontab(minute="0", hour='0,12,17'),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.regularRemainOrderTask'}
    },
    u'定时更新商品待发数': {  # 更新库存
        'task': 'shopback.items.tasks.updateProductWaitPostNumTask',
        'schedule': crontab(minute="0", hour="5,13"),  #
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.updateProductWaitPostNumTask'}
    },
    u'定时更新淘宝商品库存': {  # 更新库存
        'task': 'shopback.items.tasks.updateAllUserItemNumTask',
        'schedule': crontab(minute="0", hour="7"),  #
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.updateAllUserItemNumTask'}
    },
    u'定时下载更新你的铺子特卖订单': {
        'task': 'flashsale.pay.tasks.pull_Paid_SaleTrade',
        'schedule': crontab(minute="30", hour="*/1"),
        'args': (),
        'kwargs': {'pre_day': 0, 'interval': 1},
        'options': {'queue': 'peroid', 'routing_key': 'peroid.pull_Paid_SaleTrade'}
    },
    u'每小时更新精英妈妈活跃状态数据': {
        'task': 'flashsale.xiaolumm.tasks.elitemama.task_fresh_elitemama_active_status',
        'schedule': crontab(minute="30", hour="*/1"),
        'args': (),
        'kwargs': {},
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_fresh_elitemama_active_status'}
    },
}

SHOP_APP_SCHEDULE = {
    u'定时韵达录单任务': {
        'task': 'shopapp.yunda.tasks.task_update_yunda_order_addr',
        'schedule': crontab(minute="0", hour="10,13"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_update_yunda_order_addr'}
    },
    u'定时取消二维码未揽件单号': {
        'task': 'shopapp.yunda.tasks.task_cancel_unused_yunda_sid',
        'schedule': crontab(minute="0", hour="4"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_cancel_unused_yunda_sid'}
    },
    u'定时系统订单重量更新至韵达对接系统': {
        'task': 'shopapp.yunda.tasks.task_push_yunda_package_weight',
        'schedule': crontab(minute="*/15", hour="17,18,19,20,21,22,23"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_push_yunda_package_weight'}
    },
    u'定时更新特卖订单状态': {
        'task': 'flashsale.pay.tasks.task_Push_SaleTrade_Finished',
        'schedule': crontab(minute="0", hour="6"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_Push_SaleTrade_Finished'}
    },
    u'定时短信通知微信用户': {
        'task': 'shopapp.weixin_sales.tasks.task_notify_parent_award',
        'schedule': crontab(minute="*/5", ),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_notify_parent_award'}
    },
    u'定时统计昨日你的铺子妈妈点击': {
        'task': 'flashsale.clickcount.tasks.task_Record_User_Click',
        'schedule': crontab(minute="30", hour='4'),
        'args': (),
        #         'kwargs':{'pre_day':1},
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_Record_User_Click'}
    },
    u'定时统计昨日代理的订单': {
        'task': 'flashsale.clickrebeta.tasks.task_Tongji_User_Order',
        'schedule': crontab(minute="40", hour='0'),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_Tongji_User_Order'}
    },
    u'定时统计每日特卖综合数据': {
        'task': 'statistics.daystats.tasks.flashsale.task_Calc_Sales_Stat_By_Day',
        'schedule': crontab(minute="40", hour='2'),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_Calc_Sales_Stat_By_Day'}
    },
    u'定时统计每天商品数据': {
        'task': 'shopback.dinghuo.tasks.task_stats_daily_product',
        'schedule': crontab(minute="10", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_stats_daily_product'}
    },
    u'定时统计所有商品数据': {
        'task': 'shopback.dinghuo.tasks.task_stats_product',
        'schedule': crontab(minute="30", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_stats_product'}
    },
    u'定时更新妈妈提成订单状态': {
        'task': 'flashsale.clickrebeta.tasks.task_Update_Shoppingorder_Status',
        'schedule': crontab(minute="40", hour='3'),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_Update_Shoppingorder_Status'}
    },
    u'定时发货速度': {
        'task': 'shopback.dinghuo.tasks.task_daily_preview',
        'schedule': crontab(minute="50", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_daily_preview'}
    },
    u'定时统计每天推广支出情况': {
        'task': 'statistics.daystats.tasks.flashsale.task_PopularizeCost_By_Day',
        'schedule': crontab(minute="30", hour="8"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_PopularizeCost_By_Day'}
    },
    u'定时生成管理员代理状况汇总csv文件': {
        'task': 'flashsale.xiaolumm.tasks.tasks_manager_summary.task_make_Manager_Summary_Cvs',
        'schedule': crontab(minute="45", hour="4"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_make_Manager_Summary_Cvs'}
    },
    u'定时升级代理级别为A类到VIP类任务': {
        'task': 'flashsale.xiaolumm.tasks.task_upgrade_mama_level_to_vip',
        'schedule': crontab(minute="50", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_upgrade_mama_level_to_vip'}
    },
    u'定时更新用户优惠券状态': {
        'task': 'flashsale.coupon.tasks.usercoupon.task_update_user_coupon_status_2_past',
        'schedule': crontab(minute="15", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_update_user_coupon_status_2_past'}
    },
    u'定时更新购物车和订单状态': {
        'task': 'flashsale.restpro.tasks.task_off_the_shelf',
        'schedule': crontab(minute="20", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_off_the_shelf'}
    },
    u'定时清理购物车和待支付订单任务': {
        'task': 'flashsale.restpro.tasks.task_schedule_cart',
        'schedule': crontab(minute="*/5"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_cart'}
    },
    u'定时统计特卖平台退款率任务': {
        'task': 'shopback.refunds.tasks.fifDaysRateFlush',
        'schedule': crontab(minute="10", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.fifDaysRateFlush'}
    },
    u'定时统计供应商的平均发货速度任务': {
        'task': 'shopback.dinghuo.tasks.task_supplier_avg_post_time',
        'schedule': crontab(minute="30", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_supplier_avg_post_time'}
    },
    u'定时统计产品分类的坑位数量任务': {
        'task': 'shopback.categorys.tasks.category_pit_num_stat',
        'schedule': crontab(minute="30", hour="11"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.category_pit_num_stat'}
    },
    u'定时统计产品分类的订货数量和订货金额任务': {
        'task': 'shopback.dinghuo.tasks.task_category_stock_data',
        'schedule': crontab(minute="50", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_category_stock_data'}
    },
    u'定时统计产品分类的库存数量和库存金额任务': {
        'task': 'shopback.categorys.tasks.task_category_collect_num',
        'schedule': crontab(minute="10", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_category_collect_num'}
    },
    u'定时统计发出库存和新增订货任务': {
        'task': 'shopback.dinghuo.tasks.task_stat_category_inventory_data',
        'schedule': crontab(minute="0", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_stat_category_inventory_data'}
    },
    u'定时提醒管理员需要续费的后台服务': {
        'task': 'games.renewremind.tasks.trace_renew_remind_send_msm',
        'schedule': crontab(minute="10", hour="8", day_of_week='mon'),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.trace_renew_remind_send_msm'}
    },
    u'自动生成订货单': {
        'task': 'shopback.dinghuo.tasks.create_dinghuo',
        'schedule': crontab(minute="15", hour="10"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.create_dinghuo'}
    },
    u'定时关闭特卖退款单': {
        'task': 'flashsale.pay.tasks.task_close_refund',
        'schedule': crontab(minute="30", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_close_refund'}
    },
    u'定时推送九张图上新内容': {
        'task': 'flashsale.xiaolumm.tasks.tasks_mama_push.task_push_ninpic_peroid',
        'schedule': crontab(minute="*/15"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_push_ninpic_peroid'}
    },
    u'定时检查全站推送': {
        'task': 'flashsale.protocol.tasks.task_site_push',
        'schedule': crontab(minute="*/30"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_site_push'}
    },
    u'定时检查你的铺子妈妈活跃更新续费时间': {
        'task': 'flashsale.xiaolumm.tasks.base.task_mama_postphone_renew_time_by_active',
        'schedule': crontab(minute="45", hour="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'定时检查你的铺子妈妈续费状态': {
        'task': 'flashsale.xiaolumm.tasks.base.task_period_check_mama_renew_state',
        'schedule': crontab(minute="45", hour="1"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_period_check_mama_renew_state'}
    },
    u'每10分钟定时检查告警':{
        'task': 'shopback.trades.tasks.tasks_alarm.alarms_shopback_trades',
        'schedule': crontab(minute="*/10"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.alarms_shopback_trades'}
    },
    u'删除数据库中三个月前的物流数据' :{
        'task': 'flashsale.restpro.tasks.delete_logistics_three_month_ago',
        'schedule': crontab(minute="0", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.delete_logistics_three_month_ago'}
    },
    u'实时统计当前待发货准备的packageskuitem的数据':{
        'task': 'shopback.trades.tasks.tasks.task_schedule_check_packageskuitem_cnt',
        'schedule': crontab(minute="0"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_packageskuitem_cnt'}
    },
    u'实时统计备货的packageskuitem':{
        'task': 'shopback.trades.tasks.tasks.task_schedule_check_assign_num',
        'schedule': crontab(minute="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_assign_num'}
    },
    u'实时统计可备货但未备货的packageskuitem和空包裹':{
        'task': 'shopback.trades.tasks.tasks.task_schedule_check_stock_not_assign',
        'schedule': crontab(minute="3"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_stock_not_assign'}
    },
    u'实时统计购物车中sku数':{
        'task': 'shopback.trades.tasks.tasks.task_schedule_check_shoppingcart_cnt',
        'schedule': crontab(minute="4"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_shoppingcart_cnt'}
    },
    u'实时统计待支付的sku数':{
        'task': 'shopback.trades.tasks.tasks.task_schedule_check_waitingpay_cnt',
        'schedule': crontab(minute="6"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_waitingpay_cnt'}
    },
    u'你的铺子每日统计总额':{
        'task': 'statistics.tasks.task_xiaolu_daily_stat',
        'schedule': crontab(minute="2", hour="0"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_xiaolu_daily_stat'}
    },
    u'每10分钟定时订货':{
        'task': 'shopback.dinghuo.tasks.task_purchase_arrangement_gen_order',
        'schedule': crontab(minute="*/10"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_purchase_arrangement_gen_order'}
    },
    u'每日统计订单延时发货数量': {
        'task': 'shopback.dinghuo.tasks.task_save_package_backorder_stats',
        'schedule': crontab(minute="30", hour="23"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_save_package_backorder_stats'}
    },
    u'定时自动上下架库存商品': {
        'task': 'shopback.items.tasks.task_auto_shelf_prods',
        'schedule': crontab(minute="0", hour="*/1"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_auto_shelf_prods'}
    },
    u'定时用户优惠券优惠券过期推送消息': {
        'task': 'flashsale.coupon.tasks.usercoupon.task_push_msg_pasting_coupon',
        'schedule': crontab(minute="30", hour="12"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_push_msg_pasting_coupon'}
    },
    u'定时检查优惠券流通记录': {
        'task': 'flashsale.coupon.tasks.transfer_coupon.task_check_transfer_coupon_record',
        'schedule': crontab(minute="0", hour="*/2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_check_transfer_coupon_record'}
    },
    u'定时检查订单和收益一致性 ': {
        'task': 'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_check_order_carry_record',
        'schedule': crontab(minute="10", hour="*/4"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_check_order_carry_record'}
    },
    u'定时设定APP下载用户是否注册': {
        'task': 'flashsale.promotion.tasks.task_update_appdownload_record',
        'schedule': crontab(minute="30", hour="0"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_update_appdownload_record'}
    },
    # u'定时更新你的铺子妈妈排名3分钟': {
    #     'task': 'flashsale.xiaolumm.tasks.tasks_mama_carry_total.task_schedule_update_carry_total_ranking',
    #     'schedule': crontab(minute="30", hour="0"),
    #     'args': (),
    #     'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    # },
    # u'定时更新妈妈团队排名30分钟': {
    #     'task': 'flashsale.xiaolumm.tasks.tasks_mama_carry_total.task_schedule_update_team_carry_total_ranking',
    #     'schedule': crontab(minute="59", hour="0"),
    #     'args': (),
    #     'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    # },
    # u'妈妈及团队妈妈周激励任务更新': {
    #     'task': 'flashsale.xiaolumm.tasks.mission.task_update_all_mama_mission_state',
    #     'schedule': crontab(minute="0", hour="1"),
    #     'args': (),
    #     'options': {'queue': 'peroid', 'routing_key': 'peroid.task_update_all_mama_mission_state'}
    # },
    # u'妈妈及团队未完成任务每日提醒': {
    #     'task': 'flashsale.xiaolumm.tasks.mission.task_notify_all_mama_staging_mission',
    #     'schedule': crontab(minute="30", hour="19", day_of_week='mon,wed,fri,sat'),
    #     'args': (),
    #     'options': {'queue': 'peroid', 'routing_key': 'peroid.task_notify_all_mama_staging_mission'}
    # },
    # u'妈妈及团队周激励任务奖励确认': {
    #     'task': 'flashsale.xiaolumm.tasks.mission.task_update_all_mama_mission_award_states',
    #     'schedule': crontab(minute="30", hour="23"),
    #     'args': (),
    #     'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    # },
    u'每30分钟刷新微信公众号accesstoken&jsticket': {
        'task': 'shopapp.weixin.tasks.base.task_refresh_weixin_access_token',
        'schedule': crontab(minute="*/30"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'每五分钟重设团购状态': {
        'task': 'flashsale.pay.tasks.task_schedule_check_teambuy',
        'schedule': crontab(minute="*/5"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_teambuy'}
    },
    u'每小时发送拼团人数不足提醒': {
        'task': 'shopapp.weixin.tasks.tasks_order_push.task_pintuan_need_more_people_push',
        'schedule': crontab(minute="0"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_pintuan_need_more_people_push'}
    },
    u'每天自动下架已经过期的活动': {
        'task': 'flashsale.promotion.tasks_activity.task_close_activity_everday',
        'schedule': crontab(minute="00", hour="7"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_close_activity_everday'}
    },
    u'每天检查排期有没有锁定': {
        'task': 'pms.supplier.tasks.task_check_schedule_is_lock',
        'schedule': crontab(minute="0", hour="18"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_check_schedule_is_lock'}
    },
    u'定时统计你的铺子妈妈精品积分': {
        'task': 'flashsale.xiaolumm.tasks.tasks_mama_dailystats.task_calc_all_xlmm_elite_score',
        'schedule': crontab(minute="00", hour='3'),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
    },
    u'每小时同步微信红包状态': {
        'task': 'flashsale.xiaolupay.tasks.tasks_envelope.task_sync_weixin_red_envelopes',
        'schedule': crontab(minute="0"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_sync_weixin_red_envelopes'}
    },
    u'定时检查用户钱包不一致问题': {
        'task': 'flashsale.pay.tasks.task_schedule_check_user_budget',
        'schedule': crontab(minute="0", hour="10"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_user_budget'}
    },
    u'定时检查用户支付和订单不一致问题': {
        'task': 'flashsale.pay.tasks.task_schedule_check_trades_and_budget',
        'schedule': crontab(minute="0", hour="8"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_trades_and_budget'}
    },
}

STATISTIC_SCHEDULE = {
    u'每日统计sku规格发货速度及未发货单数': {
        'task': 'statistics.daystats.tasks.saleorder.task_call_all_sku_delivery_stats',
        'schedule': crontab(minute="15", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_call_all_sku_delivery_stats'}
    },
    u'每日统计sku规格实际销售金额(分项)': {
        'task': 'statistics.daystats.tasks.saleorder.task_calc_all_sku_amount_stat_by_schedule',
        'schedule': crontab(minute="20", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_calc_all_sku_amount_stat_by_schedule'}
    },
    u'每半小时统计商城精品券sku销量及发货速度': {
        'task': 'statistics.daystats.tasks.saleorder.task_calc_today_sku_boutique_sales_delivery_stats',
        'schedule': crontab(minute="*/30", hour=','.join([str(i) for i in range(9, 23)])),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_calc_today_sku_boutique_sales_delivery_stats'}
    },
}

BOUTIQUE_SCHEDULE = {
    u'每日统计昨日精品商品及券库存和销量': {
        'task': 'statistics.daystats.tasks.boutique.task_all_boutique_stats',
        'schedule': crontab(minute="0", hour="2"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_all_boutique_stats'}
    },
    u'定时检查boutique product配置问题': {
        'task': 'flashsale.pay.tasks.task_schedule_check_boutique_modelproduct',
        'schedule': crontab(minute="0", hour="12, 20"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_schedule_check_boutique_modelproduct'}
    },
}

WDT_SCHEDULE = {
    u'每小时同步旺店通订单物流信息': {
        'task': 'shopback.trades.tasks.tasks_erp.task_sync_erp_deliver',
        'schedule': crontab(minute="15"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_sync_erp_deliver'}
    }
}


FENGCHAO_SCHEDULE = {
    u'每30分钟同步订单到蜂巢三方仓': {
        'task': 'shopback.trades.tasks.fengchao.task_push_packageorder_to_fengchao',
        'schedule': crontab(minute="*/30"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_push_packageorder_to_fengchao'}
    },
}

# 业务指数据标监控任务
STATSD_SCHEDULE = {
    u'每分钟发送任务队列待处理消息数量': {
        'task': 'celery_statsd.tasks.task_celery_queue_message_statsd',
        'schedule': crontab(minute="*/1"),
        'args': (),
        'options': {'queue': 'peroid', 'routing_key': 'peroid.task_celery_queue_message_statsd'}
    },
}


# nihao = {
#     u'定时更新订阅客户退货的物流信息通过快递鸟': {  # by huazi
#         'task': 'flashsale.restpro.tasks.update_all_return_logistics_bykdn',
#         'schedule': crontab(),
#         'args': (),
#         'options': {'queue': 'peroid', 'routing_key': 'peroid.task'}
#     }
# }


CELERYBEAT_SCHEDULE = {}

CELERYBEAT_SCHEDULE.update(SYNC_MODEL_SCHEDULE)
CELERYBEAT_SCHEDULE.update(SHOP_APP_SCHEDULE)
CELERYBEAT_SCHEDULE.update(WDT_SCHEDULE)
CELERYBEAT_SCHEDULE.update(BOUTIQUE_SCHEDULE)
CELERYBEAT_SCHEDULE.update(STATSD_SCHEDULE)
CELERYBEAT_SCHEDULE.update(STATISTIC_SCHEDULE)
CELERYBEAT_SCHEDULE.update(FENGCHAO_SCHEDULE)

CELERY_BEAT_SCHEDULE = CELERYBEAT_SCHEDULE
