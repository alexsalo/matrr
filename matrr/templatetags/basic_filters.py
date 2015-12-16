from django import template
import string
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re


register = template.Library()


@register.filter()
def strip_account(value):
    if string.count(value, 'accounts/') != 0:
        return ""
    return value


@register.filter()
def truncate_by_char(value, arg):
    try:
        array = value.split(arg)
    except Exception:
        return value
    return array[0]


@register.filter()
def truncate_three_by_char(value, arg):
    try:
        array = value.split(arg)
    except Exception:
        return value
    return ", ".join(array[:3])


@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)


@register.filter_function
def yesno_truthy(value, arg):
    args = arg.split(',')
    if len(args) == 1:
        args.append('')
    if len(args) > 3:
        raise Exception('This filter takes 1 argument of at most 3 comma-separated values')
    if value is None:
        return args.pop()
    if bool(value):
        return args[0]
    else:
        return args[1]

### Alex
# 14 Jul 2015
@register.filter()
def spacify(value, autoescape=None):
    if autoescape:
	    esc = conditional_escape
    else:
	    esc = lambda x: x
    return mark_safe(re.sub('\s', '&'+'nbsp;', esc(value)))
spacify.needs_autoescape = True
register.filter(spacify)

@register.filter()
def big_num_human_format(value):
    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0
    # add more suffixes if you need them
    return '%.0f%s' % (value, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

