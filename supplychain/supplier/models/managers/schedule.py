# coding=utf-8
import datetime
from core.managers import BaseManager


class ScheduleManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def future_schedules(self):
        # type: () -> List[SaleProductManage]
        """未来排期
        """
        today = datetime.date.today()
        return self.get_queryset().filter(sale_time__gte=today)