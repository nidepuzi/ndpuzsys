# encoding=utf8
import os
from django.conf import settings
from django.db import connections


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def execute_sql(cursor, sql, params=None):
    with cursor as c:
        if params:
            c.execute(sql, params)
        else:
            c.execute(sql)
        # print c._last_executed
        res = dictfetchall(cursor)
        return res


def get_cursor(conn='readonly'):
    cursor = connections[conn].cursor()
    return cursor
