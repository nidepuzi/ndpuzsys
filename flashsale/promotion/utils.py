# coding=utf-8
from flashsale.promotion.models import XLSampleApply


def get_application(event_id, unionid=None, mobile=None):
    if unionid:
        xls = XLSampleApply.objects.filter(event_id=event_id, user_unionid=unionid).order_by('-created')
        if xls.exists():
            return xls[0]
    if mobile:
        xls = XLSampleApply.objects.filter(event_id=event_id, mobile=mobile).order_by('-created')
        if xls.exists():
            return xls[0]
    return None


def choice_2_name_value(choice):
    # type: (Dict[Any, str]) -> list[Dict[str, Any, str, str]]
    d = []
    for i in choice:
        d.append({'name': i[1], 'value': i[0]})
    return d