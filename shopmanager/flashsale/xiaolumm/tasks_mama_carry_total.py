# -*- encoding:utf-8 -*-
from celery.task import task
from common.taskutils import single_instance_task
from flashsale.xiaolumm.models.carry_total import MamaCarryTotal, MamaTeamCarryTotal
from flashsale.xiaolumm.models.rank import WeekMamaCarryTotal, WeekMamaTeamCarryTotal
from django.conf import settings

TIMEOUT = 15 * 60 if not settings.DEBUG else 15

import logging, sys

logger = logging.getLogger('celery.handler')


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_carryrecord_update_carrytotal(mama_id):
    MamaCarryTotal.update_ranking(mama_id)


@task()
def task_fortune_update_week_carry_total(mama_id):
    WeekMamaCarryTotal.update_or_create(mama_id)
    return


@single_instance_task(timeout=TIMEOUT, prefix='flashsale.xiaolumm.tasks_mama_carry_total.')
def task_update_carry_total_ranking():
    return
    MamaCarryTotal.reset_rank()


@task()
def task_schedule_update_carry_total_ranking():
    logger.warn("task_schedule_update_carry_total_ranking: %s" % (get_cur_info(),))
    MamaCarryTotal.reset_rank()
    MamaCarryTotal.reset_rank_duration()
    MamaCarryTotal.reset_de_rank()
    MamaCarryTotal.reset_activite_rank()
    # WeekMamaCarryTotal.reset_rank()
    # WeekMamaCarryTotal.reset_rank_duration()

@task()
def task_schedule_update_team_carry_total_ranking():
    logger.warn(" task_schedule_update_carry_total_ranking: %s" % (get_cur_info(),))
    MamaTeamCarryTotal.reset_rank()
    MamaTeamCarryTotal.reset_rank_duration()
    MamaTeamCarryTotal.reset_de_rank()
    MamaTeamCarryTotal.reset_activite_rank()
    # WeekMamaTeamCarryTotal.reset_rank()
    # WeekMamaTeamCarryTotal.reset_rank_duration()

@single_instance_task(timeout=TIMEOUT, prefix='flashsale.xiaolumm.tasks_mama_carry_total.')
def task_update_carry_duration_total_ranking():
    return
    MamaCarryTotal.reset_rank_duration()


@single_instance_task(timeout=TIMEOUT, prefix='flashsale.xiaolumm.tasks_mama_carry_total.')
def task_update_team_carry_total2(mama_id):
    return
    MamaTeamCarryTotal.get_by_mama_id(mama_id).refresh_data()


@task()
def task_update_team_carry_total(mama_id):
    MamaTeamCarryTotal.get_by_mama_id(mama_id).refresh_data()