# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE shop_trades_mergeorder ADD INDEX IDX_OU_OU_ME (OUTER_ID,OUTER_SKU_ID,MERGE_TRADE_ID);"),
    ]
