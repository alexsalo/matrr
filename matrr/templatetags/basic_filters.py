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