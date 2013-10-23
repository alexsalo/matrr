from django import template
import string


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