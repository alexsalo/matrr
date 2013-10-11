from django.contrib.auth.views import AuthenticationForm

from matrr.models import *
from matrr.settings import PRODUCTION, GLEEK, DEVELOPMENT, DEBUG


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


def global_context(request):
    context = {'PRODUCTION': PRODUCTION, 'GLEEK': GLEEK, 'DEVELOPMENT': DEVELOPMENT, 'DEBUG': DEBUG}
    if request.user.is_authenticated():
        if request.user.account.verified:
            context['user_is_verified'] = True
    return context


def unsupported_browser(request):
    hua = request.META.get('HTTP_USER_AGENT', '')
    if 'MSIE' in hua and 'chromeframe' not in hua:
        return {'unsupported_browser': request.META['HTTP_USER_AGENT']}
    else:
        return {}
