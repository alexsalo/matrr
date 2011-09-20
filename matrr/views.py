# Create your views here.
from django.forms.models import modelformset_factory
from django.forms.models import formset_factory
from django.template import RequestContext
from django.http import Http404, HttpResponse
from django.shortcuts import  render_to_response, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.encoding import smart_str
import settings
from matrr.forms import *
from matrr.models import *
import math
from datetime import datetime
from django.db import DatabaseError
from djangosphinx.models import SphinxQuerySet
from process_latex import process_latex


def index_view(request):
	index_context = {'event_list': Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name')[:5],
					 'pub_list': Publication.objects.all().exclude(published_year=None).order_by('-published_year',
																								 '-published_month')[:4]
		,
					 'search_form': FulltextSearchForm(),
					 }

	return render_to_response('matrr/index.html', index_context, context_instance=RequestContext(request))

### Handles all non-dynamic pages.
def pages_view(request, static_page):
	# The issue I was having with file.open('/path/to/text.txt', r) was the inconsistent directory structure between
	# the dev and production environments (laptop vs gleek).  I'm certain there is a combination of settings that would
	# handle that more beautifully, but for the scope of 3 files I've wasted enough time.
	# it didnt stay 3 pages for long....

	template = 'matrr/pages/' + static_page + ".html"
	return render_to_response(template, {}, context_instance=RequestContext(request))

### Handles the display of each cohort and the lists of cohorts
def display_cohorts(request, **kwargs):
	cohort = ''
	cohorts = ''
	template_name = ''

	## If the URL holds a cohort's pk
	if kwargs.has_key('pk'):
		cohort = get_object_or_404(Cohort, pk=kwargs['pk']) # Get that cohort
		template_name = 'matrr/cohort.html' # and display that cohort's page
	# This will display the cohort regardless of its available/upcoming status
	# Which will be good after cohorts go to necropsy, if the user will ever see/manipulate the URL
	## otherwise, display a list of cohorts based on the URL
	elif kwargs['avail_up'] == 'cohort':
		cohorts = Cohort.objects.order_by('coh_cohort_name')
		template_name = 'matrr/cohorts.html'
	elif kwargs['avail_up'] == 'upcoming':
		cohorts = Cohort.objects.filter(coh_upcoming=True).order_by('coh_cohort_name')
		template_name = 'matrr/upcoming_cohorts.html'
	elif kwargs['avail_up'] == 'available':
		cohorts = Cohort.objects.filter(coh_upcoming=False).order_by('coh_cohort_name')
		template_name = 'matrr/available_cohorts.html'

	## Paginator stuff
	if len(cohorts) > 0:
		paginator = Paginator(cohorts, 5)
		# Make sure page request is an int. If not, deliver first page.
		try:
			page = int(request.GET.get('page', '1'))
		except ValueError:
			page = 1
		# If page request (9999) is out of range, deliver last page of results.
		try:
			cohort_list = paginator.page(page)
		except (EmptyPage, InvalidPage):
			cohort_list = paginator.page(paginator.num_pages)
	else:
		cohort_list = cohorts

	return render_to_response(template_name, {'cohort': cohort, 'cohort_list': cohort_list},
							  context_instance=RequestContext(request))

### Currently a very simple hack to tell everyone we don't have any necropsy data.  Placeholder, mostly.
def cohort_necropsy(request, pk):
	# Simple message
	messages.info(request, 'No necropsy date available at this time.')
	# and display the cohort detail page
	cohort = Cohort.objects.get(pk=pk)
	return render_to_response('matrr/cohort.html', {'cohort': cohort}, context_instance=RequestContext(request))


def monkey_cohort_detail_view(request, cohort_id, monkey_id):
	try:
		monkey = Monkey.objects.get(mky_id=monkey_id)
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
		monkey = Monkey.objects.get(mky_real_id=monkey_id)
	except:
		raise Http404((u"No %(verbose_name)s found matching the query") %
					  {'verbose_name': Monkey._meta.verbose_name})

	return render_to_response('matrr/monkey.html', {'monkey': monkey},
							  context_instance=RequestContext(request))


def get_or_create_cart(request, cohort):
	"""
	 This function will get the cart for the cohort if it exists.
	 If it does not exist, it will create a new cart for the cohort.
	 In the case that the user has a cart open for a different cohort,
	 this function will return None.  (unless the cart was empty, in which
	 case it will be deleted.)
	 """
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


def tissue_shop_detail_view(request, cohort_id, tissue_id):
	current_cohort = Cohort.objects.get(coh_cohort_id=cohort_id)
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
	current_tissue = TissueType.objects.get(tst_type_id=tissue_id)
	instance = TissueRequest(tissue_type=current_tissue,
							 req_request=cart_request)

	if request.method != 'POST':
		# now we need to create the form for the tissue type
		tissue_request_form = TissueRequestForm(req_request=cart_request, tissue=current_tissue, instance=instance,
												initial={'monkeys': current_cohort.monkey_set.all()})
		# create the response
		return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
																 'cohort': current_cohort,
																 'page_title': current_tissue.tst_tissue_name, },
								  context_instance=RequestContext(request))
	else:
		data = request.POST.copy()
		tissue_request_form = TissueRequestForm(data=data,
												req_request=cart_request,
												tissue=current_tissue,
												instance=instance)
		if tissue_request_form.is_valid():
			url = cart_request.cohort.get_url() + 'tissues/'
			try:
				tissue_request_form.save()
			except:
				messages.error(request,
							   'Error adding tissue to cart.  Possible duplicate tissue request already in cart.')
				return redirect(url)

			messages.success(request, 'Item added to cart')
			return redirect(url)
		else:
			return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
																	 'cohort': current_cohort,
																	 'page_title': current_tissue.tst_tissue_name},
									  context_instance=RequestContext(request))


def cart_view(request):
	# get the context (because it loads the cart as well)
	context = RequestContext(request)
	if context['cart_exists']:
		cart_request = context['cart']
		cohort = cart_request.cohort

		return render_to_response('matrr/cart/cart_page.html', {
			#'form': tissue_request_form,
			'cohort': cohort, },
								  context_instance=RequestContext(request))
	else:
		return render_to_response('matrr/cart/cart_page.html', {},
								  context_instance=RequestContext(request))


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


def cart_item_view(request, tissue_request_id):
	# get the context (because it loads the cart as well)
	context = RequestContext(request)
	# get the cart item
	cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)

	if cart_item not in context['cart_items']:
		raise Http404('This page does not exist.')
	if request.method != 'POST' or request.POST['submit'] == 'edit':
		# create a form so the item can be edited
		tissue_request_form = TissueRequestForm(instance=cart_item,
												req_request=cart_item.req_request,
												tissue=cart_item.get_tissue())
		return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
																'cohort': cart_item.req_request.cohort,
																'tissue': cart_item.get_tissue(),
																'cart_item': cart_item, },
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
													req_request=cart_item.req_request,
													tissue=cart_item.get_tissue())
			if tissue_request_form.is_valid():
				# the form is valid, so update the tissue request
				tissue_request_form.save()
				messages.success(request, 'Item updated.')
				return redirect('/cart')
			else:
				return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
																		'cohort': cart_item.req_request.cohort,
																		'tissue_type': cart_item.get_tissue(),
																		'cart_item': cart_item, },
										  context_instance=context)


def cart_item_delete(request, tissue_request_id):
	# get the context (because it loads the cart as well)
	context = RequestContext(request)
	# get the cart item
	cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)
	if cart_item not in context['cart_items']:
		raise Http404('This page does not exist.')
	return delete_cart_item(request, cart_item)


def delete_cart_item(request, cart_item):
	cart_item.delete()
	messages.success(request, 'Item removed from cart.')
	return redirect('/cart')


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


@user_passes_test(lambda u: u.groups.filter(name='Committee').count() != 0, login_url='/denied/')
def reviews_list_view(request):
	# get a list of all reviews for the current user
	submitted = RequestStatus.objects.get(rqs_status_name='Submitted')
	reviews = Review.objects.filter(user=request.user.id).filter(req_request__request_status=submitted)

	finished_reviews = [review for review in reviews if review.is_finished()]
	unfinished_reviews = [review for review in reviews if not review.is_finished()]

	return render_to_response('matrr/review/reviews.html',
			{'finished_reviews': finished_reviews,
			 'unfinished_reviews': unfinished_reviews,
			 'num_finished': len(finished_reviews),
			 'num_unfinished': len(unfinished_reviews), },
							  context_instance=RequestContext(request))


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
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))


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
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))


def account_view(request):
	return account_detail_view(request, request.user.id)


def account_detail_view(request, user_id):
	if request.user.id == user_id:
		edit = True
	else:
		edit = False
	# get information from the act_account relation
	account_info = Account.objects.get(user__id=user_id)
	mta_info = Mta.objects.filter(user__id=user_id)
	order_list = Request.objects.filter(user__id=user_id).exclude(
		request_status=RequestStatus.objects.get(rqs_status_name='Cart')).order_by("-req_request_date")[:20]

	return render_to_response('matrr/account.html',
			{'account_info': account_info,
			 'mta_info': mta_info,
			 'order_list': order_list,
			 'edit': edit,
			 },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.groups.filter(name='Committee').count()or
							u.groups.filter(name='Uberuser').count(),
				  login_url='/denied/')
def account_reviewer_view(request, user_id):
	return account_detail_view(request, user_id)


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


@user_passes_test(lambda u: u.groups.filter(name='Uberuser').count() != 0, login_url='/denied/')
def review_overview_list(request):
	# get a list of all tissue requests that are submitted, but not accepted or rejected
	request_status = RequestStatus.objects.get(rqs_status_name='Submitted')
	req_requests = Request.objects.filter(request_status=request_status)
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
				tissue_request_review.quantity_css_value = int(
					10 - (math.fabs(5 - tissue_request_review.get_quantity()) * 2))


@user_passes_test(lambda u: u.groups.filter(name='Uberuser').count() != 0, login_url='/denied/')
def review_overview(request, req_request_id):
	# get the request being reviewed
	req_request = Request.objects.get(req_request_id=req_request_id)

	TissueRequestFormSet = modelformset_factory(TissueRequest, form=TissueRequestProcessForm, extra=0)

	if request.POST:
		tissue_request_forms = TissueRequestFormSet(request.POST, prefix='tissue_requests')

		if tissue_request_forms.is_valid():
			tissue_request_forms.save()
			return redirect('/reviews_overviews/' + str(req_request_id) + '/process/')
		else:
			# get the reviews for the request
			reviews = list(req_request.review_set.all())
			reviews.sort(key=lambda x: x.user.username)

			sort_tissues_and_add_quantity_css_value(tissue_request_forms)

			return render_to_response('matrr/review/review_overview.html',
					{'reviews': reviews,
					 'req_request': req_request,
					 'tissue_requests': tissue_request_forms,
					 'Availability': Availability,
					 },
									  context_instance=RequestContext(request))

	else:
		# get the tissue requests
		tissue_request_forms = TissueRequestFormSet(queryset=req_request.tissue_request_set.all(),
													prefix='tissue_requests')

		# get the reviews for the request
		reviews = list(req_request.review_set.all())
		reviews.sort(key=lambda x: x.user.username)

		sort_tissues_and_add_quantity_css_value(tissue_request_forms)

		return render_to_response('matrr/review/review_overview.html',
				{'reviews': reviews,
				 'req_request': req_request,
				 'tissue_requests': tissue_request_forms,
				 'Availability': Availability,
				 },
								  context_instance=RequestContext(request))


def orders_list(request):
	# get a list of all requests for the user
	order_list = ''
	orders = Request.objects.filter(user=request.user).exclude(
		request_status=RequestStatus.objects.get(rqs_status_name='Cart')).order_by('-req_request_date')
	## Paginator stuff
	paginator = Paginator(orders, 20)
	# Make sure page request is an int. If not, deliver first page.
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	# If page request (9999) is out of range, deliver last page of results.
	try:
		order_list = paginator.page(page)
	except (EmptyPage, InvalidPage):
		order_list = paginator.page(paginator.num_pages)

	return render_to_response('matrr/orders.html',
			{'order_list': order_list,
			 },
							  context_instance=RequestContext(request))


def order_detail(request, req_request_id):
	# get the request
	req_request = Request.objects.get(req_request_id=req_request_id)
	# check that the request belongs to this user
	if req_request.user != request.user and Group.objects.get(name='Committee') not in request.user.groups.all():
		# if the request does not belong to the user, return a 404 error (alternately, we could give a permission denied message)
		raise Http404('This page does not exist.')
	status = req_request.request_status.rqs_status_name
	processed = False
	if status == "Accepted" or status == "Rejected" or status == "Partially Accepted":
		processed = True
	return render_to_response('matrr/order_detail.html',
			{'order': req_request,
			 'Acceptance': Acceptance,
			 'shipped': status == 'Shipped',
			 'processed': processed,
			 },
							  context_instance=RequestContext(request))


def experimental_plan_view(request, plan):
	# create the response
	response = HttpResponse(mimetype='application/force-download')
	response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(plan)
	response['X-Sendfile'] = smart_str(settings.MEDIA_ROOT + 'media/experimental_plans/' + plan)

	# serve the file if the user is a committee member or Uberuser
	if request.user.groups.filter(name='Committee').count() != 0 or\
	   request.user.groups.filter(name='Uberuser').count() != 0:
		return response

	# check that the plan belongs to the user
	if Request.objects.filter(user=request.user, req_experimental_plan='experimental_plans/' + plan).count() > 0:
		return response

	#otherwise return a 404 error
	raise Http404('This page does not exist.')


def tissue_shop_landing_view(request, cohort_id):
	cohort = Cohort.objects.get(coh_cohort_id=cohort_id)
	categories = list(TissueCategory.objects.order_by('cat_name').all())
	if TissueCategory.objects.filter(cat_name='Custom'):
		custom = TissueCategory.objects.get(cat_name='Custom')
		categories.remove(custom)
		categories.append(custom)
	return render_to_response('matrr/tissue_shopping_landing.html',
			{'cohort': cohort,
			 'categories': categories},
							  context_instance=RequestContext(request))


def tissue_list(request, tissue_category=None, cohort_id=None):
	cohort = None
	if cohort_id is not None:
		cohort = Cohort.objects.get(coh_cohort_id=cohort_id)
	if tissue_category == "Custom":
		# This breaks the URL scheme
		return tissue_shop_detail_view(request, cohort.coh_cohort_id, TissueType.objects.get(tst_tissue_name="Custom").tst_type_id)
	elif tissue_category:
		tissue_list = TissueType.objects.filter(category__cat_name=tissue_category).order_by('tst_tissue_name')
	else:
		tissue_list = TissueType.objects.order_by('tst_tissue_name')
	available = list()
	unavailable = list()

	for tissue in tissue_list:
		if tissue.get_cohort_availability(cohort):
			available.append(tissue)
		else:
			unavailable.append(tissue)

		#	paginator = Paginator(tissue_list, 60) # Show 20 tissues per page

		#	# Make sure page request is an int. If not, deliver first page.
		#	try:
		#		page = int(request.GET.get('page', '1'))
		#	except ValueError:
		#		page = 1
		#
		#	# If page request (9999) is out of range, deliver last page of results.
		#	try:
		#		tissues = paginator.page(page)
		#	except (EmptyPage, InvalidPage):
		#		tissues = paginator.page(paginator.num_pages)
	# just return the list of tissues

	return render_to_response('matrr/tissues.html', {'tissues': available,
													 'tissues_unavailable': unavailable,
													 'title': tissue_category,
													 'cohort': cohort},
							  context_instance=RequestContext(request))


def remove_values_from_list(the_list, other_list):
	return [value for value in the_list if value not in other_list]


@user_passes_test(lambda u: u.groups.filter(name='Uberuser').count(), login_url='/denied/')
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
						unavailable_list.extend(
							Monkey.objects.filter(mky_id__in=form.cleaned_data[str(tissue_request)]))
						tissue.unavailable_list = unavailable_list
						tissue.save()
				req_request.request_status = RequestStatus.objects.get(rqs_status_name=status)
				req_request.save()
				messages.success(request, "The tissue request has been processed.")
				# Email subject *must not* contain newlines
				subject = ''.join(form.cleaned_data['subject'].splitlines())
				if not settings.DEVELOPMENT:
					send_mail(subject, form.cleaned_data['body'], settings.DEFAULT_FROM_EMAIL, [req_request.user.email])
				messages.success(request, str(
					req_request.user.username) + " was sent an email informing him/her that the request was accepted.")
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
		request_url = '/orders/' + str(req_request.req_request_id) + '/'
		body = render_to_string(email_template,
				{'request_url': request_url,
				 'req_request': req_request,
				 'Acceptance': Acceptance})
		body = re.sub('(\r?\n){2,}', '\n\n', body)
		form = ReviewResponseForm(tissue_requests=req_request.get_requested_tissues(),
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
				subject = ''.join(form.cleaned_data['email_subject'].splitlines())
				subject += '//'
				try:
					if request.user.email:
						subject += request.user.email
				except:
				#					Anonymous user does not have email field.
					pass
				send_mail(subject, form.cleaned_data['email_body'], form.cleaned_data['email_from'],
					["Erich_Baker@Baylor.edu"])
				messages.success(request, "Your message was sent to the MATRR team. You may expect a response shortly.")
				return redirect('/')
			else:
				return render_to_response('matrr/contact_us.html',
						{'form': form},
										  context_instance=RequestContext(request))
		else:
			messages.info(request, "No message has been sent.")
			return redirect('/')
	else:
		try:
			account_info = Account.objects.get(user__id=request.user.id)
			user_email = account_info.user.email
			form = ContactUsForm(initial={'email_from': user_email})
		except Account.DoesNotExist:
			form = ContactUsForm()

		return render_to_response('matrr/contact_us.html',
				{'form': form},
								  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.groups.filter(name='Tech User').count() or
							u.groups.filter(name='Committee').count() or
							u.groups.filter(name='Uberuser').count(),
				  login_url='/denied/')
def shipping_overview(request):
	# get the tissue requests that have been accepted
	accepted_requests = Request.objects.filter(request_status__in=
	RequestStatus.objects.filter(rqs_status_name__in=('Accepted', 'Partially Accepted')))
	# get the tissue requests that have been shipped
	shipped_requests = Request.objects.filter(request_status=RequestStatus.objects.get(rqs_status_name='Shipped'))

	return render_to_response('matrr/shipping/shipping_overview.html',
			{'accepted_requests': accepted_requests,
			 'shipped_requests': shipped_requests},
							  context_instance=RequestContext(request))


def search_index(terms, index, model):
	search = SphinxQuerySet(
		index=index,
		mode='SPH_MATCH_EXTENDED2',
		rankmode='SPH_RANK_NONE')

	results = search.query(terms)
	final_results = list()

	for result in results:
		final_results.append(model.objects.get(pk=result['id']))

	return final_results


def search(request):
	from settings import SEARCH_INDEXES

	results = None
	form = FulltextSearchForm()
	num_results = 0
	user_auth = False

	terms = ''
	results = dict()
	if request.method == 'POST':
		form = FulltextSearchForm(request.POST)
		if form.is_valid():
			terms = form.cleaned_data['terms']

			if request.user.groups.filter(name='Tech User').count() != 0 or\
			   request.user.groups.filter(name='Committee').count() != 0 or\
			   request.user.groups.filter(name='Uberuser').count() != 0:
				user_auth = True
				results['monkeys'] = search_index(terms, SEARCH_INDEXES['monkey_auth'], Monkey)
			else:
				user_auth = False
				results['monkeys'] = search_index(terms, SEARCH_INDEXES['monkey'], Monkey)

			results['cohorts'] = search_index(terms, SEARCH_INDEXES['cohort'], Cohort)

			num_results = len(results['monkeys'])
			num_results += len(results['cohorts'])

	return render_to_response('matrr/search.html',
			{'terms': terms,
			 'results': results,
			 'num_results': num_results,
			 'user_auth': user_auth,
			 'form': form},
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.groups.filter(name='Tech User').count() or
							u.groups.filter(name='Committee').count() or
							u.groups.filter(name='Uberuser').count(),
				  login_url='/denied/')
def build_shipment(request, req_request_id):
	# get the request
	req_request = Request.objects.get(req_request_id=req_request_id)
	# do a sanity check
	if req_request.request_status.rqs_status_name != 'Accepted' and\
	   req_request.request_status.rqs_status_name != 'Partially Accepted':
		raise Exception(
			'You cannot create a shipment for a request that has not been accepted (or has already been shipped.')

	if Shipment.objects.filter(req_request=req_request).count():
		shipment = req_request.shipment
		if 'shipped' in request.POST:
			shipment.shp_shipment_date = datetime.today()
			shipment.user = request.user
			shipment.save()
			req_request.request_status = RequestStatus.objects.get(rqs_status_name='Shipped')
			req_request.save()
	else:
		# create the shipment
		shipment = Shipment(user=req_request.user, req_request=req_request)
		shipment.save()

	return render_to_response('matrr/shipping/build_shipment.html',
			{'req_request': req_request,
			 'shipment': shipment, },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.groups.filter(name='Tech User').count() or
							u.groups.filter(name='Committee').count() or
							u.groups.filter(name='Uberuser').count(),
				  login_url='/denied/')
def make_shipping_manifest_latex(request, req_request_id):
	req_request = Request.objects.get(req_request_id=req_request_id)

	#Create the HttpResponse object with the appropriate PDF headers.
	response = HttpResponse(mimetype='application/pdf')
	response['Content-Disposition'] = 'attachment; filename=manifest-' +\
									  str(req_request.user) + '-' +\
									  str(req_request.cohort) + '.pdf'
	account = req_request.user.account

	return process_latex('latex/shipping_manifest.tex',
														{'req_request': req_request,
														'account': account,
														'time': datetime.today(),
														},
														outfile=response)


def order_delete(request, req_request_id):
	req_request = Request.objects.get(req_request_id=req_request_id)
	if req_request.user != request.user:
		# tissue requests can only be deleted by the
		# user who made the tissue request.
		raise Http404('This page does not exist.')

	status = req_request.request_status.rqs_status_name
	if status == "Accepted" or status == "Rejected" or status == "Partially Accepted":
		messages.error(request, "You cannot delete an order which has been accepted/rejected.")
		return redirect('/orders/')

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
				 'Acceptance': Acceptance, },
								  context_instance=RequestContext(request))


def tissue_verification(request):
	TissueVerificationFormSet = formset_factory(TissueInventoryVerificationForm, extra=0)
	if request.method == "POST":
		formset = TissueVerificationFormSet(request.POST)
		if formset.is_valid():
			for tivform in formset:
				data = tivform.cleaned_data
				tiv = TissueInventoryVerification.objects.get(pk=data['primarykey'])
				tss = tiv.tissue_sample
				tss.tss_location = data['location']
				tss.tss_freezer = data['freezer']
				tss.tss_details = data['details']
				if data['quantity']:
					tss.tss_sample_quantity = data['quantity']
				if data['units']:
					tss.tss_units = data['units']
				if data['inventory']:
					tiv.inventory = data['inventory']
				tss.save()
				tiv.save()
				if "export" in request.POST:
					tiv_list = TissueInventoryVerification.objects.all().order_by('inventory').order_by("monkey")

					#Create the HttpResponse object with the appropriate PDF headers.
					response = HttpResponse(mimetype='application/pdf')
					response['Content-Disposition'] = 'attachment; filename=TissueVerificationForm.pdf'
					return process_latex('latex/tissue_verification.tex',
							{'tiv_list': tiv_list,
							 'user': request.user,
							 'date': datetime.today(),
							 },
										 outfile=response)
			return redirect('/verification')
		else:
			messages.error(request, formset.errors)

	initial = []
	tiv_list = TissueInventoryVerification.objects.all().order_by('inventory')
	for tiv in tiv_list:
		tss = tiv.tissue_sample
		try:
			amount = tiv.tissue_request.get_amount()
		except AttributeError:
			amount = "None"
		tiv_initial = {'primarykey': tiv.tiv_id,
					   'freezer': tss.tss_freezer,
					   'location': tss.tss_location,
					   'quantity': tss.tss_sample_quantity,
					   'inventory': tiv.inventory.pk,
					   'units': tss.units.pk,
					   'details': tss.tss_details,
					   'monkey': tiv.monkey,
					   'tissue': tiv.tissue_type,
					   'notes': tiv.tiv_notes,
					   'amount': amount, }
		initial[len(initial):] = [tiv_initial]
	formset = TissueVerificationFormSet(initial=initial)
	return render_to_response('matrr/verification.html', {"formset": formset}, context_instance=RequestContext(request))
