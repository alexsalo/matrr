from django import template
from matrr.models import Request
register = template.Library()
from settings import STATIC_URL

@register.inclusion_tag('review/collision_requests.html')
def pokus(request, monkey):
#    import pdb
#    pdb.set_trace()
    collisions = request.get_sub_req_collisions_for_monkey(monkey)
#    collisions = Request.objects.filter(request_status=4)
#    for collision in collisions:
#        print collision.review_set.all()
#    print request.review_set.all()

    return {
            'collisions' : collisions,
            'monkey': monkey,
            'STATIC_URL': STATIC_URL
            }
    
