from matrr.models import *
from django.contrib.auth.views import AuthenticationForm
from string import lower, replace
from settings import PRODUCTION, GLEEK, DEVELOPMENT

def cart(request):
	# get the cart for the user in the request
	context = {}
	if request.user.is_authenticated():
		if Request.objects.cart().filter(user=request.user.id).count() == 1:
			cart = Request.objects.cart().get(user=request.user.id)
			cart_items = TissueRequest.objects.filter(req_request=cart).all()
			cart_num_items = len(cart_items)
			context['cart_exists'] = True
			context['cart'] = cart
			context['cart_items'] = cart_items
			context['cart_num_items'] = cart_num_items
		else:
			context['cart_exists'] = False
	else:
			context['cart_exists'] = False
	return context


def login_form(request):
	if request.user.is_authenticated():
		return {}
	return {'login_form': AuthenticationForm()}


def group_membership(request):
	#context = {}
	# cheezy, should be somewhere else
	context = {'PRODUCTION': PRODUCTION, 'GLEEK': GLEEK, 'DEVELOPMENT': DEVELOPMENT} # no, really, this should be moved.
	if request.user.is_authenticated():
		# if the user is logged in, get the groups the user is a member of
		groups = request.user.groups.all()
		for group in groups:
			key = 'user_is_member_of_' + replace(lower(group.name), ' ', '_')
			context[key] = True
		if request.user.account.verified:
			context['user_is_verified'] = True
	return context


def unsupported_browser(request):
	if 'MSIE' in request.META['HTTP_USER_AGENT'] and 'chromeframe' not in request.META['HTTP_USER_AGENT']:
		return {'unsupported_browser' : request.META['HTTP_USER_AGENT']}
	else:
		return {}
