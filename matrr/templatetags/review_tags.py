from django import template
from matrr.models import Request
register = template.Library()
from settings import STATIC_URL

@register.inclusion_tag('review/collision_requests.html')
def colliding_requests(request, monkey):

    collisions = request.get_sub_req_collisions_for_monkey(monkey)


    return {
            'collisions' : collisions,
            'monkey': monkey,
            'STATIC_URL': STATIC_URL
            }
    
