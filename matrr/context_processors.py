from matrr.models import *
from django.contrib.auth.views import AuthenticationForm
from django.contrib.auth.models import Group
from settings import SITE_ROOT
from string import lower, replace

def cart(request):
  # get the cart for the user in the request
  cart_status = RequestStatus.objects.get(rqs_status_name='Cart')
  context = {}
  if request.user.is_authenticated():
    try:
      cart = Request.objects.get(user=request.user.id, request_status=cart_status.rqs_status_id)
      cart_items = list(TissueRequest.objects.filter(req_request=cart))
      cart_items.extend(BrainRegionRequest.objects.filter(req_request=cart))
      #cart_items.extend(MicrodissectedRegionRequest.objects.filter(req_request=cart))
      cart_items.extend(BloodAndGeneticRequest.objects.filter(req_request=cart))
      cart_items.extend(CustomTissueRequest.objects.filter(req_request=cart))
      cart_num_items = len(cart_items)
      context['cart_exists'] = True
      context['cart'] = cart
      context['cart_items'] = cart_items
      context['cart_num_items'] = cart_num_items
    except:
      context['cart_exists'] = False
  else:
    context['cart_exists'] = False
  return context


def login_form(request):
  if request.user.is_authenticated():
    return {}
  return {'login_form': AuthenticationForm()}


def group_membership(request):
  context = {}
  if request.user.is_authenticated():
    # if the user is logged in, get the groups the user is a member of
    groups = request.user.groups.all()
    for group in groups:
      key = 'user_is_member_of_' + replace( lower(group.name), ' ', '_')
      context[key] = True
  return context

def site_root(request):
  return {'SITE_ROOT': SITE_ROOT}
