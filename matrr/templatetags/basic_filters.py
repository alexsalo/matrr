__author__ = 'JonDev'

from django import template

register = template.Library()

@register.filter()
def truncate_by_char(value, arg):
    try:
        array = value.split(arg)
    except ValueError:
        return value
    return array[0]
  