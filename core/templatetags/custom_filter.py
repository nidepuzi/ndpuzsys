# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import json
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='displayName')
def displayName(value, arg):
    if not value:
        return ''
    return apply(eval('value.get_'+arg+'_display'), ())

@register.filter(name='regexReplace')
def regexReplace(value, arg=''):
    if not value:
        return ''
    reg = re.compile(arg)
    return re.sub(reg,'*',value)

@register.filter(name='stringBlur')
def stringBlur(value,start=3,end=-3):

    slen = len(value)
    if slen<start or slen<end:
        return value

    es = value[end:]
    plen = slen - len(es)
    return value[0:start].ljust(plen,'*')+es

@register.filter(name='jsonify')
def jsonify(data):
    return mark_safe(json.dumps(data))


@register.filter(name='startswith')
def startswith(data, arg):
    return data.startswith(arg)

