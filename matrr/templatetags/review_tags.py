from django import template
from matrr.settings import STATIC_URL


register = template.Library()


@register.inclusion_tag('collision_requests.html')
def colliding_submitted_requests(req_request, monkey):
    collisions = req_request.get_sub_req_collisions_for_monkey(monkey)
    return {
        'collisions': collisions,
        'monkey': monkey,
        'STATIC_URL': STATIC_URL
    }


@register.inclusion_tag('collision_requests.html')
def colliding_accepted_requests(req_request, tissue_type, monkey):
    collisions = req_request.get_acc_req_collisions_for_tissuetype_monkey(tissue_type, monkey)

    return {
        'collisions': collisions,
        'STATIC_URL': STATIC_URL
    }