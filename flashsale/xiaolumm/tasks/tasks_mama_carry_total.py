# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime
from flashsale.xiaolumm.models.carry_total import ActivityMamaCarryTotal
from flashsale.xiaolumm.models.rank import WeekMamaCarryTotal, WeekMamaTeamCarryTotal, WeekRank

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


@app.task()
def task_fortune_update_week_carry_total(mama_id):
    WeekMamaCarryTotal.update_or_create(mama_id)


@app.task()
def task_fortune_update_activity_carry_total(activity, mama_id):
    ActivityMamaCarryTotal.update_or_create(activity, mama_id)


@app.task()
def task_schedule_update_carry_total_ranking():
    logger.warn("task_schedule_update_carry_total_ranking: %s" % (get_cur_info(),))
    return
    # 周一把上周的也重设一次排名
    if datetime.datetime.now().weekday() == 1:
        WeekMamaCarryTotal.reset_rank(WeekRank.last_week_time())
        WeekMamaCarryTotal.reset_duration_rank(WeekRank.last_week_time())
    WeekMamaCarryTotal.reset_rank()
    WeekMamaCarryTotal.reset_rank_duration()


@app.task()
def task_schedule_update_team_carry_total_ranking():
    logger.warn(" task_schedule_update_carry_total_ranking: %s" % (get_cur_info(),))
    return
    if datetime.datetime.now().weekday() == 1:
        WeekMamaTeamCarryTotal.reset_rank(WeekRank.last_week_time())
        WeekMamaTeamCarryTotal.reset_duration_rank(WeekRank.last_week_time())
    WeekMamaTeamCarryTotal.reset_rank()
    WeekMamaTeamCarryTotal.reset_rank_duration()
