from django.db import IntegrityError
from django.db.models import Sum
from celery.task import task

import logging
logger = logging.getLogger(__name__)


@task()
def task_productsku_create_productskustats(sku_id, product_id):
    from shopback.items.models import ProductSkuStats
    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        stat = ProductSkuStats(sku_id=sku_id,product_id=product_id)
        stat.save()


@task(max_retries=3, default_retry_delay=6)
def task_product_upshelf_update_productskusalestats(sku_id):
    """
    Recalculate and update init_waitassign_num,sale_start_time.
    """
    from shopback.items.models import ProductSku, ProductSkuStats, \
        ProductSkuSaleStats, gen_productsksalestats_unikey

    product = ProductSku.objects.get(id=sku_id).product
    product_id = product.id
    sku_stats,state = ProductSkuStats.objects.get_or_create(sku_id=sku_id,product_id=product_id)

    wait_assign_num = sku_stats.wait_assign_num

    stats_uni_key = gen_productsksalestats_unikey(sku_id)
    stats = ProductSkuSaleStats.objects.filter(uni_key= stats_uni_key, sku_id=sku_id)

    if stats.count() == 0:
        try:
            stat = ProductSkuSaleStats(uni_key=stats_uni_key,
                                   sku_id=sku_id,
                                   product_id=product_id,
                                   init_waitassign_num=wait_assign_num,
                                   sale_start_time=product.sale_time)
            stat.save()
        except IntegrityError as exc:
            logger.warn("IntegrityError - productskusalestat/init_waitassign_num | sku_id: %s, init_waitassign_num: %s" % (
                sku_id, wait_assign_num))
            raise task_product_upshelf_update_productskusalestats.retry(exc=exc)
    else:
        logger.warn("RepeatUpshelf- productskusalestat/init_waitassign_num | sku_id: %s, init_waitassign_num: %s" % (
        sku_id, wait_assign_num))


@task(max_retries=3, default_retry_delay=6)
def task_product_downshelf_update_productskusalestats(sku_id, sale_end_time):
    """
    Recalculate and update sale_end_time,status.
    """
    from shopback.items.models import ProductSku, ProductSkuStats, \
        ProductSkuSaleStats, gen_productsksalestats_unikey

    product = ProductSku.objects.get(id=sku_id).product
    product_id = product.id

    stats_uni_key   = gen_productsksalestats_unikey(sku_id)
    stats = ProductSkuSaleStats.objects.filter(uni_key= stats_uni_key, sku_id=sku_id)

    if stats.count() > 0:
        try:
            stat = stats[0]
            stat.sale_end_time = sale_end_time
            stat.status = ProductSkuSaleStats.ST_FINISH
            stat.save(update_fields=["sale_end_time","status"])
        except IntegrityError as exc:
            logger.warn("IntegrityError - productskusalestat/init_waitassign_num | sku_id: %s, sale_end_time: %s" % (
                sku_id, sale_end_time))
            raise task_product_downshelf_update_productskusalestats.retry(exc=exc)

    else:
        logger.warn("RepeatDownshelf- productskusalestat/init_waitassign_num | sku_id: %s, sale_end_time: %s" % (
            sku_id, sale_end_time))


@task()
def task_product_upshelf_notify_favorited_customer(product):
    from flashsale.push.app_push import AppPush
    model = product.product_model
    customer_ids = model.favorites_set.values('customer_id')

    for customer_id in customer_ids:
        AppPush.push_product_to_customer(customer_id, model)
