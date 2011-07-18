# Create your views here.
from django.template import RequestContext
from django.views.generic import TemplateView
from django.http import Http404, HttpResponse
from django.shortcuts import  render_to_response, redirect
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from matrr.forms import *
import math
from datetime import datetime
from django.db import DatabaseError
from djangosphinx.models import SphinxQuerySet
from process_latex import process_latex

MEDIA_DIRECTORY = '/web/alpha/media/'

class MatrrTemplateView( TemplateView ):
  template_name = 'matrr/index.html'
  
  def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
    context = super(MatrrTemplateView, self).get_context_data(**kwargs)
    # get a list of upcoming events
    context['event_list'] = Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name')[:5]
    return context


def static_page_view(request, static_page):
 text = ''
 head = ''
 if static_page == "privacy":
   f = open('static/privacy.txt', 'r')
   text = f.read()
   head = 'Privacy Policy'
 elif static_page == "data":
   f = open('static/data.txt', 'r')
   text = f.read()
   head = 'Data Sharing Policy'
 elif static_page == "usage":
   f = open('static/usage.txt', 'r')
   text = f.read()
   head = 'Usage Policy'
 return render_to_response('matrr/static_page.html', {'text': text, 'head': head},
        context_instance=RequestContext(request))


def monkey_cohort_detail_view(request, cohort_id, monkey_id):
  try:
    monkey = Monkey.objects.get(mky_id = monkey_id)
  except:
    raise Http404((u"No %(verbose_name)s found matching the query") %
                {'verbose_name': Monkey._meta.verbose_name})

  if str(monkey.cohort.coh_cohort_id) != cohort_id:
    raise Http404((u"No %(verbose_name)s found matching the query") %
                {'verbose_name': Monkey._meta.verbose_name})
  
  return render_to_response('matrr/monkey.html', {'monkey': monkey},
        context_instance=RequestContext(request))


def monkey_detail_view(request, monkey_id):
  try:
    monkey = Monkey.objects.get(mky_real_id = monkey_id)
  except:
    raise Http404((u"No %(verbose_name)s found matching the query") %
                {'verbose_name': Monkey._meta.verbose_name})
  
  return render_to_response('matrr/monkey.html', {'monkey': monkey},
        context_instance=RequestContext(request))


@login_required()
def get_or_create_cart(request, cohort):
  '''
  This function will get the cart for the cohort if it exists.
  If it does not exist, it will create a new cart for the cohort.
  In the case that the user has a cart open for a different cohort,
  this function will return None.  (unless the cart was empty, in which
  case it will be deleted.)
  '''
  cart_status = RequestStatus.objects.get(rqs_status_name='Cart')

  # get the user's cart if it already exists
  if Request.objects.filter(user=request.user.id, request_status=cart_status.rqs_status_id).count():
    cart_request = Request.objects.get(user=request.user.id, request_status=cart_status.rqs_status_id)
    # check that the cart is for this cohort
    if cart_request.cohort != cohort:
      # take corrective action (display a page that asks the user if they want to abandon their cart and start with this cohort)
      # if the cart is empty, just delete it
      if not cart_request.get_requested_tissue_count():
        cart_request.delete()
        #create a new cart
        cart_request = Request(user=request.user, request_status=cart_status, 
                               cohort=cohort, req_request_date=datetime.now())
        cart_request.save()
      else:
        #the cart was not empty, so give the user the option to delete the cart and continue
        return None
        # it would probably be better to implement this as a custom exception handled with middleware,
        # but for now I will just have this function return None in this case and let the
        # calling function handle the error
  else:
    #create a new cart
    cart_request = Request(user=request.user, request_status=cart_status,
                           cohort=cohort, req_request_date=datetime.now())
    cart_request.save()

  return cart_request


@login_required()
def tissue_shop_detail_view(request, cohort_id, tissue_model, tissue_id):
  current_cohort = Cohort.objects.get(coh_cohort_id = cohort_id)
  cart_request = get_or_create_cart(request, current_cohort)
  if cart_request is None:
    # The user has a cart open with a different cohort
    # display a page that gives the user the option to delete
    # the existing cart and proceed or to go to the existing cart.
    return render_to_response('matrr/cart/cart_delete_or_keep.html',
                              {'cohort': current_cohort},
                              context_instance=RequestContext(request))

  # if we got here, then a request is made with this user and cohort and the status is 'cart'
  
  # get the current tissue
  current_tissue = None
  instance = None
  form_class = None
  if tissue_model == 'regions':
    current_tissue = BrainRegion.objects.get(bre_region_id = tissue_id)
    instance = BrainRegionRequest(brain_region=current_tissue,
      req_request=cart_request)
    form_class = BrainRegionRequestForm
  elif tissue_model == 'peripherals':
    current_tissue = TissueType.objects.get(tst_type_id = tissue_id)
    instance = TissueRequest(tissue_type=current_tissue,
      req_request=cart_request)
    form_class = TissueRequestForm
  
  if request.method != 'POST':
    # now we need to create the form for the tissue type
    tissue_request_form = form_class( req_request = cart_request, tissue=current_tissue, instance=instance,
                                      initial={'monkeys': current_cohort.monkey_set.all()})
    # create the response
    return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
        'cohort': current_cohort, 
        'page_title': current_tissue.get_name(),},
          context_instance=RequestContext(request))
  else: 
    data = request.POST.copy()
    tissue_request_form = form_class(data=data,
        req_request = cart_request,
        tissue=current_tissue,
        instance=instance)
    if tissue_request_form.is_valid():
      try:
        tissue_request_form.save()
      except:
        messages.error(request, 'Error adding tissue to cart.')
      
      url = cart_request.cohort.get_url() + 'tissues/'
      messages.success(request, 'Item added to cart')
      return redirect(url)
    else:
      return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
        'cohort': current_cohort, 
        'page_title': current_tissue.get_name()},
          context_instance=RequestContext(request))


@login_required()
def tissue_shop_custom_detail_view(request, cohort_id):
  current_cohort = Cohort.objects.get(coh_cohort_id = cohort_id)
  cart_request = get_or_create_cart(request, current_cohort)
  if cart_request is None:
    # The user has a cart open with a different cohort
    # display a page that gives the user the option to delete
    # the existing cart and proceed or to go to the existing cart.
    return render_to_response('matrr/cart/cart_delete_or_keep.html',
                              {'cohort': current_cohort},
                              context_instance=RequestContext(request))

  # if we got here, then a request is made with this user and cohort and the status is 'cart'

  tissue_request = CustomTissueRequest(req_request = cart_request)
  if request.method != 'POST':
    # now we need to create the form for the tissue type
    tissue_request_form = CustomTissueRequestForm(instance=tissue_request, req_request=cart_request,
                                                  initial={'monkeys': current_cohort.monkey_set.all()})
    # create the response
    return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
        'cohort': current_cohort,
        'page_title': 'Custom Tissue Request',},
          context_instance=RequestContext(request))
  else:
    data = request.POST.copy()
    tissue_request_form = CustomTissueRequestForm(instance=tissue_request, req_request=cart_request, data=data)
    if tissue_request_form.is_valid():
      try:
        tissue_request_form.save()
      except:
        messages.error(request, 'Error adding tissue to cart.')

      url = cart_request.cohort.get_url() + 'tissues/'
      messages.success(request, 'Item added to cart')
      return redirect(url)
    else:
      return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
        'cohort': current_cohort,
        'page_title': 'Custom Tissue Request',},
          context_instance=RequestContext(request))


@login_required()
def cart_view(request):
  # get the context (because it loads the cart as well)
  context = RequestContext(request)
  if context['cart_exists']:
    cart_request = context['cart']
    cohort = cart_request.cohort
    
    return render_to_response('matrr/cart/cart_page.html', {
          #'form': tissue_request_form,
          'cohort': cohort,},
            context_instance=RequestContext(request))
  else:
    return render_to_response('matrr/cart/cart_page.html', {},
            context_instance=RequestContext(request))


@login_required()
def cart_delete(request):
  # get the context (because it loads the cart as well)
  context = RequestContext(request)
  if request.method != 'POST':
    # provide the cart deletion form
    return render_to_response('matrr/cart/cart_delete.html', {},
            context_instance=RequestContext(request))
  elif request.POST['submit'] == 'yes':
    # delete the cart
    try:
      cart = context['cart']
      cart.delete()
      messages.success(request, 'Cart deleted.')
    except DatabaseError:
      messages.error(request, 'Caught a database exception.')
    except:
      #there is nothing to except here
      messages.error(request, 'There was no cart to delete.')
  else:
    messages.info(request, 'Your cart was not deleted.')
  return redirect('/cart')


@login_required()
def cart_item_view_old(request, tissue_request_id):
  # get the context (because it loads the cart as well)
  context = RequestContext(request)
  # get the cart item
  cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)

  if cart_item not in context['cart_items']:
    raise Http404('This page does not exist.')
  if request.method != 'POST' or request.POST['submit'] == 'edit':
    # create a form so the item can be edited
    tissue_request_form = TissueRequestForm(instance=cart_item,
        req_request = cart_item.req_request, 
        tissue=cart_item.tissue_type)
    return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
        'cohort': cart_item.req_request.cohort, 
        'tissue_type': cart_item.tissue_type,
        'cart_item': cart_item,},
          context_instance=context)
  else:
    if request.POST['submit'] == 'cancel':
      messages.info(request, 'No changes were made.')
      return redirect('/cart')
    elif request.POST['submit'] == 'delete':
      return delete_cart_item(request, cart_item)
    else:
      # validate the form and update the cart_item
      tissue_request_form = TissueRequestForm(instance=cart_item,
          data=request.POST, 
          req_request = cart_item.req_request, 
          tissue=cart_item.tissue_type)
      if tissue_request_form.is_valid():
        # the form is valid, so update the tissue request
        tissue_request_form.save()
        messages.success(request, 'Item updated.')
        return redirect('/cart')
      else:
        return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
          'cohort': cart_item.req_request.cohort, 
          'tissue_type': cart_item.tissue_type,
          'cart_item': cart_item,},
            context_instance=context)


@login_required()
def cart_item_view(request, tissue_model, tissue_request_id):
  # get the context (because it loads the cart as well)
  context = RequestContext(request)
  # get the cart item
  cart_item = None
  form = None
  if tissue_model == 'regions':
    form = BrainRegionRequestForm
    cart_item = BrainRegionRequest.objects.get(rbr_region_request_id=tissue_request_id)
  elif tissue_model == 'peripherals':
    form = TissueRequestForm
    cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)
  elif tissue_model == 'custom':
    form = CustomTissueRequestForm
    cart_item = CustomTissueRequest.objects.get(ctr_id=tissue_request_id)

  if cart_item not in context['cart_items']:
    raise Http404('This page does not exist.')
  if request.method != 'POST' or request.POST['submit'] == 'edit':
    # create a form so the item can be edited
    if tissue_model == 'custom':
      tissue_request_form = form(instance=cart_item,
      req_request = cart_item.req_request,)
    else:
      tissue_request_form = form(instance=cart_item,
        req_request = cart_item.req_request,
        tissue = cart_item.get_tissue())
    return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
        'cohort': cart_item.req_request.cohort,
        'tissue': cart_item.get_tissue(),
        'cart_item': cart_item,},
          context_instance=context)
  else:
    if request.POST['submit'] == 'cancel':
      messages.info(request, 'No changes were made.')
      return redirect('/cart')
    elif request.POST['submit'] == 'delete':
      return delete_cart_item(request, cart_item)
    else:
      # validate the form and update the cart_item
      if tissue_model == 'custom':
        tissue_request_form = form(instance=cart_item,
        data=request.POST,
        req_request = cart_item.req_request,)
      else:
        tissue_request_form = form(instance=cart_item,
          data=request.POST,
          req_request = cart_item.req_request,
          tissue = cart_item.get_tissue())
      if tissue_request_form.is_valid():
        # the form is valid, so update the tissue request
        tissue_request_form.save()
        messages.success(request, 'Item updated.')
        return redirect('/cart')
      else:
        return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
          'cohort': cart_item.req_request.cohort,
          'tissue_type': cart_item.get_tissue(),
          'cart_item': cart_item,},
            context_instance=context)


@login_required()
def cart_item_delete(request, tissue_model, tissue_request_id):
  # get the context (because it loads the cart as well)
  context = RequestContext(request)
  # get the cart item
  cart_item = None
  if tissue_model == 'regions':
    cart_item = BrainRegionRequest.objects.get(rbr_region_request_id=tissue_request_id)
  elif tissue_model == 'peripherals':
    cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)
  if cart_item not in context['cart_items']:
    raise Http404('This page does not exist.')
  return delete_cart_item(request, cart_item)

@login_required()
def delete_cart_item(request, cart_item):
  cart_item.delete()
  messages.success(request, 'Item removed from cart.')
  return redirect('/cart')


@login_required()
def cart_checkout(request):
  # get the context (because it loads the cart as well)
  context = RequestContext(request)
  if not context['cart_exists']:
    return render_to_response('matrr/cart/cart_checkout.html', {},
            context_instance=context)
  cart_request = context['cart']
  if request.method != 'POST':
    checkout_form = CartCheckoutForm(instance=cart_request)
    return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form},
          context_instance=context)
  else:
    data = request.POST.copy()
    data['user'] = cart_request.user.id
    data['request_status'] = cart_request.request_status.rqs_status_id
    data['cohort'] = cart_request.cohort.coh_cohort_id
    checkout_form = CartCheckoutForm(request.POST, request.FILES, instance=cart_request)
    
    if checkout_form.is_valid() and request.POST['submit'] == 'checkout':
      cart_request.req_experimental_plan = checkout_form.cleaned_data['req_experimental_plan']
      cart_request.req_notes = checkout_form.cleaned_data['req_notes']
      cart_request.request_status = RequestStatus.objects.get(rqs_status_name='Submitted')
      cart_request.req_request_date = datetime.now
      cart_request.save()
      messages.success(request, 'Tissue Request Submitted.')
      return redirect('/')
    else:
      return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form},
          context_instance=context)


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Committee').count() != 0, login_url='/denied/')
def reviews_list_view(request):
  # get a list of all reviews for the current user
  reviews = Review.objects.filter(user=request.user.id)
  finished_reviews = [review for review in reviews if review.is_finished()]
  unfinished_reviews = [review for review in reviews if not review.is_finished()]
    
  return render_to_response('matrr/review/reviews.html',
      {'finished_reviews': finished_reviews,
       'unfinished_reviews': unfinished_reviews,
       'num_finished': len(finished_reviews),
       'num_unfinished': len(unfinished_reviews),},
          context_instance=RequestContext(request))

@login_required()
def mta_upload(request):
  # make blank mta instance 
  mta_object = Mta(user=request.user)
  # make a MTA upload form if one does not exist
  if request.method == 'POST':
    form = MtaForm(request.POST, request.FILES, instance=mta_object)
    if form.is_valid():
      # all the fields in the form are valid, so save the data
      form.save()
      messages.success(request, 'MTA Uploaded Successfully')
      return redirect('/account/')
  else:
    # create the form for the MTA upload
    form = MtaForm(instance=mta_object)
  return render_to_response('matrr/mta_upload_form.html',
      {'form':form,
       'user':request.user
       },
        context_instance=RequestContext(request))

@login_required()
def account_shipping(request):
  # make address form if one does not exist
  if request.method == 'POST':
    form = AccountForm(data=request.POST, instance=request.user.account)
    if form.is_valid():
      # all the fields in the form are valid, so save the data
      form.save()
      messages.success(request, 'Shipping Address Saved')
      return redirect('/account/')
  else:
    #create the form for shipping address
    form = AccountForm(instance=request.user.account)
  return render_to_response('matrr/account_shipping_form.html',
      {'form':form,
      'user':request.user
       },
        context_instance=RequestContext(request))

@login_required()
def account_view(request):
  return account_detail_view(request, request.user.id)

@login_required()
def account_detail_view(request, user_id):
  if request.user.id == user_id:
    edit = True
  else:
    edit = False
  # get information from the act_account relation
  account_info = Account.objects.get(user__id = user_id)
  mta_info = Mta.objects.filter(user__id = user_id)
  order_list = Request.objects.filter(user__id = user_id).exclude(request_status= RequestStatus.objects.get(rqs_status_name='Cart'))

  return render_to_response('matrr/account.html',
    {'account_info': account_info,
     'mta_info': mta_info,
     'order_list': order_list,
     'edit': edit,
    },
    context_instance=RequestContext(request))

@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Committee').count()
                  or u.groups.filter(name='Superuser').count(), login_url='/denied/')
def account_reviewer_view(request, user_id):
  return account_detail_view(request, user_id)


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Committee').count() != 0, login_url='/denied/')
def review_detail(request, review_id):
  # get the review
  review = Review.objects.get(rvs_review_id=review_id)
  if review.user != request.user:
    raise Http404('This page does not exist.') 
  # get the request being reviewed
  req_request = review.req_request
  
  if request.method == 'POST':
    if request.POST['submit'] == 'cancel':
      messages.info(request, 'Review cancelled.')
      return redirect('/reviews/')

    form = ReviewForm(data=request.POST.copy(), instance=review)

    if form.is_valid():
      # all the forms are valid, so save the data
      form.save()
      messages.success(request, 'Review saved.')
      return redirect('/reviews/')
  else:
    # create the forms for the review and the tissue request reviews
    form = ReviewForm(instance=review)
  return render_to_response('matrr/review/review_form.html',
      {'review': review,
       'req_request': req_request,
       'form': form,
       'Availability': Availability,
       },
          context_instance=RequestContext(request))


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Superuser').count() != 0, login_url='/denied/')
def review_overview_list(request):
  # get a list of all tissue requests that are submitted, but not accepted or rejected
  request_status = RequestStatus.objects.get(rqs_status_name='Submitted')
  req_requests = Request.objects.filter(request_status = request_status)
  # get a list of all reviewers
  group = Group.objects.get(name='Committee')
  reviewers = group.user_set.all().order_by('-username')
  for req_request in req_requests:
    req_request.complete = list()
    for reviewer in reviewers:
      for review in req_request.review_set.all():
        if reviewer == review.user:
          if review.is_finished():
            req_request.complete.append("complete")
          else:
            req_request.complete.append("pending")
          
  return render_to_response('matrr/review/reviews_overviews.html',
        {'req_requests': req_requests,
         'reviewers': reviewers,
         },
         context_instance=RequestContext(request))

def sort_tissues_and_add_quantity_css_value(tissue_requests):
  for tissue_request_form in tissue_requests:
    tissue_request = tissue_request_form.instance
    tissue_request.sorted_tissue_request_reviews = sorted(tissue_request.get_reviews(),
                                                          key=lambda x: x.review.user.username)
    for tissue_request_review in tissue_request.sorted_tissue_request_reviews:
      if tissue_request_review.is_finished():
        tissue_request_review.quantity_css_value = int(10 - (math.fabs(5-tissue_request_review.get_quantity()) * 2))
#    tissue_request_form = tissue_request.instance


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Superuser').count() != 0, login_url='/denied/')
def review_overview(request, req_request_id):
  # get the request being reviewed
  req_request = Request.objects.get(req_request_id=req_request_id)
  
  TissueRequestFormSet = modelformset_factory(TissueRequest, form=PeripherialTissueRequestProcessForm, extra=0)
  RegionRequestFormSet = modelformset_factory(BrainRegionRequest, form=BrainRegionRequestProcessForm, extra=0)
  CustomRequestFormSet = modelformset_factory(CustomTissueRequest, form=CustomTissueRequestProcessForm, extra=0)

  if request.POST:
    tissue_request_forms = TissueRequestFormSet(request.POST, prefix='peripherial')
    region_request_forms = RegionRequestFormSet(request.POST, prefix='regions')
    custom_request_forms = CustomRequestFormSet(request.POST, prefix='custom')

    if tissue_request_forms.is_valid() and \
       region_request_forms.is_valid() and \
       custom_request_forms.is_valid():
      tissue_request_forms.save()
      region_request_forms.save()
      custom_request_forms.save()
      return redirect('/reviews_overviews/' + str(req_request_id) + '/process/')
    else:
      # get the reviews for the request
      reviews = list(req_request.review_set.all())
      reviews.sort(key=lambda x: x.user.username)

      sort_tissues_and_add_quantity_css_value(region_request_forms)
      sort_tissues_and_add_quantity_css_value(tissue_request_forms)
      sort_tissues_and_add_quantity_css_value(custom_request_forms)

      return render_to_response('matrr/review/review_overview.html',
          {'reviews': reviews,
           'req_request': req_request,
           'region_requests': region_request_forms,
           'tissue_requests': tissue_request_forms,
           'custom_requests': custom_request_forms,
           'Availability': Availability,
           },
           context_instance=RequestContext(request))
    
  else:
    # get the tissue requests
    tissue_request_forms = TissueRequestFormSet(queryset = req_request.tissue_request_set.all(),
                                                  prefix='peripherial')
    region_request_forms = RegionRequestFormSet(queryset = req_request.brain_region_request_set.all(),
                                                  prefix = 'regions')
    custom_request_forms = CustomRequestFormSet(queryset = req_request.custom_tissue_request_set.all(),
                                                  prefix = 'custom')

    # get the reviews for the request
    reviews = list(req_request.review_set.all())
    reviews.sort(key=lambda x: x.user.username)

    sort_tissues_and_add_quantity_css_value(region_request_forms)
    sort_tissues_and_add_quantity_css_value(tissue_request_forms)
    sort_tissues_and_add_quantity_css_value(custom_request_forms)

    return render_to_response('matrr/review/review_overview.html',
          {'reviews': reviews,
           'req_request': req_request,
           'region_requests': region_request_forms,
           'tissue_requests': tissue_request_forms,
           'custom_requests': custom_request_forms,
           'Availability': Availability,
           },
           context_instance=RequestContext(request))


@login_required()
def orders_list(request):
  # get a list of all requests for the user
  order_list = Request.objects.filter(user = request.user).exclude(request_status= RequestStatus.objects.get(rqs_status_name='Cart'))
  return render_to_response('matrr/orders.html',
        {'order_list': order_list,
         },
         context_instance=RequestContext(request))


@login_required()
def order_detail(request, req_request_id):
  # get the request
  req_request = Request.objects.get(req_request_id=req_request_id)
  # check that the request belongs to this user
  if req_request.user != request.user and Group.objects.get(name='Committee') not in request.user.groups.all():
    # if the request does not belong to the user, return a 404 error (alternately, we could give a permission denied message)
    raise Http404('This page does not exist.')
  return render_to_response('matrr/order_detail.html',
        {'order': req_request,
         'Acceptance': Acceptance,
         },
         context_instance=RequestContext(request))
  

@login_required()
def experimental_plan_view(request, plan):
  # create the response
  response = HttpResponse(mimetype='application/force-download')
  response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(plan)
  response['X-Sendfile'] = smart_str(MEDIA_DIRECTORY + 'media/experimental_plans/' + plan)
  
  # serve the file if the user is a committee member or superuser
  if request.user.groups.filter(name='Committee').count() != 0 or \
      request.user.groups.filter(name='Superuser').count() != 0:
    return response
  
  # check that the plan belongs to the user
  if Request.objects.filter(user=request.user, req_experimental_plan='experimental_plans/' + plan).count() > 0 or \
      RequestRevision.objects.filter(req_request__in=Request.objects.filter(user=request.user), rqv_experimental_plan='experimental_plans/' + plan).count() > 0:
    return response
  
  #otherwise return a 404 error
  raise Http404('This page does not exist.')


def tissue_list(request, tissue_model, cohort_id = None):
  model = None
  order = None
  title = None
  if tissue_model == 'regions':
    model = BrainRegion
    order = 'bre_region_name'
    title = 'Brain Regions'
  elif tissue_model == 'peripherals':
    model = TissueType
    order = 'tst_tissue_name'
    title = 'Peripheral Tissues'

  cohort = None
  if cohort_id is not None:
    cohort = Cohort.objects.get(coh_cohort_id = cohort_id)
  c = RequestContext(request, {
    'cohort': cohort,
    })
  
  tissue_list = model.objects.order_by(order)
  
  paginator = Paginator(tissue_list, 60) # Show 20 tissues per page

  # Make sure page request is an int. If not, deliver first page.
  try:
    page = int(request.GET.get('page', '1'))
  except ValueError:
    page = 1

  # If page request (9999) is out of range, deliver last page of results.
  try:
    tissues = paginator.page(page)
  except (EmptyPage, InvalidPage):
    tissues = paginator.page(paginator.num_pages)
  # just return the list of tissues
  
  return render_to_response('matrr/tissues.html', {'tissues': tissues,
                                                   'title': title},
      context_instance=c)


def remove_values_from_list(the_list, other_list):
   return [value for value in the_list if value not in other_list]


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Superuser').count(),
                  login_url='/denied/')
def request_review_process(request, req_request_id):
  # get the tissue request
  req_request = Request.objects.get(req_request_id=req_request_id)

  # check the status
  accepted = False
  partial = False
  for tissue_request in req_request.get_requested_tissues():
    if tissue_request.get_accepted() != Acceptance.Rejected:
      accepted = True
    if tissue_request.get_accepted() != Acceptance.Accepted:
      partial = True
  if accepted and not partial:
    status = 'Accepted'
    email_template = 'matrr/review/request_accepted_email.txt'
  elif accepted and partial:
    status = 'Partially Accepted'
    email_template = 'matrr/review/request_partially_accepted_email.txt'
  else:
    status = 'Rejected'
    email_template = 'matrr/review/request_rejected_email.txt'

  if request.POST:
    if request.POST['submit'] == 'Finalize and Send Email':
      # get the submitted form
      form = ReviewResponseForm(data=request.POST, tissue_requests=req_request.get_requested_tissues())
      if form.is_valid():
        # update the unavailable_lists
        for tissue_request in req_request.get_requested_tissues():
          if tissue_request.get_tissue():
            tissue = tissue_request.get_tissue()
            unavailable_list = tissue.unavailable_list.all()
            monkey_list = tissue_request.monkeys.all()
            # remove any monkeys in the request from the list
            unavailable_list = remove_values_from_list(unavailable_list, monkey_list)
            unavailable_list.extend(Monkey.objects.filter(mky_id__in=form.cleaned_data[str(tissue_request)]))
            tissue.unavailable_list = unavailable_list
            tissue.save()
        req_request.request_status = RequestStatus.objects.get(rqs_status_name=status)
        req_request.save()
        messages.success(request, "The tissue request has been processed.")
        # Email subject *must not* contain newlines
        subject = ''.join(form.cleaned_data['subject'].splitlines())
        send_mail(subject, form.cleaned_data['body'], settings.DEFAULT_FROM_EMAIL, [req_request.user.email] )
        messages.success(request, str(req_request.user.username) + " was sent an email informing him/her that the request was accepted.")
        return redirect('/reviews_overviews/')
      else:
        return render_to_response('matrr/review/process.html',
                                  {'form': form,
                                   'req_request': req_request,
                                   'Availability': Availability,
                                   'Acceptance': Acceptance},
                                  context_instance=RequestContext(request))
    else:
      messages.info(request, "The tissue request has not been processed.  No email was sent.")
      return redirect('/reviews_overviews/')
  else:
    # get the subject
    subject = render_to_string('matrr/review/request_email_subject.txt',
                                {'status': status})
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    request_url = settings.SITE_ROOT + '/orders/' + str(req_request.req_request_id) + '/'
    body = render_to_string(email_template,
                      {'request_url': request_url,
                       'req_request': req_request,
                       'Acceptance': Acceptance})
    body = re.sub('(\r?\n){2,}', '\n\n', body)
    form = ReviewResponseForm( tissue_requests=req_request.get_requested_tissues(),
                              initial={'subject': subject, 'body': body})
    return render_to_response('matrr/review/process.html',
                              {'form': form,
                               'req_request': req_request,
                               'Availability': Availability,
                               'Acceptance': Acceptance},
                              context_instance=RequestContext(request))


def contact_us(request):
  if request.POST:
    if request.POST['submit'] == 'Send Message':
      # get the submitted form
      form = ContactUsForm(data=request.POST)
      if form.is_valid():
        subject = ''.join(form.cleaned_data['subject'].splitlines())
        subject += '//'
        if request.user.email:
          subject += request.user.email
        fromEmail = 'contact_us@matrr.com'
        send_mail(subject, form.cleaned_data['body'], fromEmail, ["Erich_Baker@Baylor.edu"])
        messages.success(request, "Your message was sent to the MATRR team. You may expect a response shortly.")
        return redirect('/')
      else:
        return render_to_response('matrr/contact_us.html',
                                  {'form': form },
                                  context_instance=RequestContext(request))
    else:
      messages.info(request, "No message has been sent.")
      return redirect('/')
  else:
    form = ContactUsForm()
    return render_to_response('matrr/contact_us.html',
                              {'form': form},
                              context_instance=RequestContext(request))


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Tech User').count() or \
                            u.groups.filter(name='Committee').count() or \
                            u.groups.filter(name='Superuser').count(),
                  login_url='/denied/')
def shipping_overview(request):
  # get the tissue requests that have been accepted
  accepted_requests = Request.objects.filter(request_status__in =
        RequestStatus.objects.filter(rqs_status_name__in=('Accepted', 'Partially Accepted')))
  # get the tissue requests that have been shipped
  shipped_requests = Request.objects.filter(request_status = RequestStatus.objects.get(rqs_status_name='Shipped'))

  return render_to_response('matrr/shipping/shipping_overview.html',
            {'accepted_requests': accepted_requests,
             'shipped_requests': shipped_requests},
            context_instance=RequestContext(request))



def search_index(terms, index, model):
  search = SphinxQuerySet(
    index = index,
    mode = 'SPH_MATCH_EXTENDED2',
    rankmode = 'SPH_RANK_NONE')

  results = search.query(terms)
  final_results = list()
  for result in results:
    final_results.append(model.objects.get(pk=result['id']))
  return final_results

def search(request):
  terms = request.GET['terms']

  results = dict()
  if request.user.groups.filter(name='Tech User').count() != 0 or \
    request.user.groups.filter(name='Committee').count() != 0 or \
    request.user.groups.filter(name='Superuser').count() != 0:
    results['monkeys'] = search_index(terms, 'monkey_auth', Monkey)
  else:
    results['monkeys'] = search_index(terms, 'monkey', Monkey)
  results['cohorts'] = search_index(terms, 'cohort', Cohort)

  num_results = len(results['monkeys'])
  num_results += len(results['cohorts'])

  return render_to_response('matrr/search.html',
      {'terms': terms,
       'results': results,
       'num_results': num_results},
      context_instance=RequestContext(request))

@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Tech User').count() or \
                            u.groups.filter(name='Committee').count() or \
                            u.groups.filter(name='Superuser').count(),
                  login_url='/denied/')
def build_shipment(request, req_request_id):
  # get the request
  req_request = Request.objects.get(req_request_id = req_request_id)
  # do a sanity check
  if req_request.request_status.rqs_status_name != 'Accepted' and \
     req_request.request_status.rqs_status_name != 'Partially Accepted':
    raise Exception('You cannot create a shipment for a request that has not been accepted (or has already been shipped.')

  if Shipment.objects.filter(req_request=req_request).count():
    shipment = req_request.shipment
  else:
    # create the shipment
    shipment = Shipment(user=req_request.user, req_request=req_request)
    shipment.save()

  return render_to_response('matrr/shipping/build_shipment.html',
                            {'req_request': req_request,
                            'shipment': shipment,},
                            context_instance=RequestContext(request))


@login_required()
@user_passes_test(lambda u: u.groups.filter(name='Tech User').count() or \
                            u.groups.filter(name='Committee').count() or \
                            u.groups.filter(name='Superuser').count(),
                  login_url='/denied/')
def make_shipping_manifest_latex(request, req_request_id):
  req_request = Request.objects.get(req_request_id=req_request_id)

  #Create the HttpResponse object with the appropriate PDF headers.
  response = HttpResponse(mimetype='application/pdf')
  response['Content-Disposition'] = 'attachment; filename=manifest-' + \
                                    str(req_request.user) + '-' + \
                                    str(req_request.cohort) + '.pdf'
  account = req_request.user.account

  return process_latex('latex/shipping_manifest.tex',
                        {'req_request': req_request,
                         'account': req_request.user.account,
                         'time': datetime.today(),
                         },
                       outfile=response)

@login_required()
def order_delete(request, req_request_id):
  req_request = Request.objects.get(req_request_id=req_request_id)
  if req_request.user != request.user:
    # tissue requests can only be deleted by the
    # user who made the tissue request.
    raise Http404('This page does not exist.')
  if request.POST:
    if request.POST['submit'] == 'yes':
      req_request.delete()
      messages.success(request, 'The order was deleted.')
    else:
      messages.info(request, 'The order was not deleted.')
    return redirect('/orders/')
  else:
    return render_to_response('matrr/order_delete.html',
                              {'order': req_request,
                               'Acceptance': Acceptance,},
                              context_instance=RequestContext(request))