__author__ = 'soltau'
from matrr.models import TissueInventoryVerification
from django import template


register = template.Library()


@register.filter()
def monkey_availability(tissue, monkey):
    return tissue.get_monkey_availability(monkey)


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


@register.filter()
def get_verification(tissue_request, monkey):
    return TissueInventoryVerification.objects.get(tissue_request=tissue_request, monkey=monkey,
                                                   tissue_type=tissue_request.tissue_type).tiv_inventory
	