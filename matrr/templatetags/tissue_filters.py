__author__ = 'soltau'

from django import template
#from matrr.models import

register = template.Library()

@register.filter()
def monkey_availability(tissue, monkey):
  return tissue.get_availability(monkey)

@register.filter()
def cohort_availability(tissue, cohort):
  return tissue.get_cohort_availability(cohort)
