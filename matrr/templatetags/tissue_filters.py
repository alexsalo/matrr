__author__ = 'soltau'

from django import template

register = template.Library()

@register.filter()
def monkey_availability(tissue, monkey):
  return tissue.get_availability(monkey)

@register.filter()
def cohort_availability(tissue, cohort):
  return tissue.get_cohort_availability(cohort)

@register.filter()
def accepted_requests(tissue, monkey):
  return tissue.get_accepted_request_count(monkey)

@register.filter()
def pending_requests(tissue, monkey):
  return tissue.get_pending_request_count(monkey)

@register.filter()
def get_stock(tissue, monkey):
  return tissue.get_stock(monkey)
