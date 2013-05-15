# Create your views here.
import json
from django.db import DatabaseError
from django.db.models import Q, Count
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import modelformset_factory
from django.forms.models import formset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import  render_to_response, redirect, get_object_or_404
from django.template import RequestContext, loader
from django.template.context import Context
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils.safestring import mark_safe
from djangosphinx.models import SphinxQuerySet
import settings
from matrr import helper, emails
from matrr.forms import *
from matrr.models import *
import math
from datetime import date, timedelta
from utils import plotting, plotting_beta, apriori
from matrr.decorators import user_owner_test
import urllib


def __paginator_stuff(request, queryset, count):
	if len(queryset) > 0:
		paginator = Paginator(queryset, count)
		# Make sure page request is an int. If not, deliver first page.
		try:
			page = int(request.GET.get('page', '1'))
		except ValueError:
			page = 1
		# If page request (9999) is out of range, deliver last page of results.
		try:
			paged = paginator.page(page)
		except (EmptyPage, InvalidPage):
			paged = paginator.page(paginator.num_pages)
	else:
		paged = queryset
	return paged


def redirect_with_get(url_name, *args, **kwargs):
	url = reverse(url_name, args=args)
	params = urllib.urlencode(kwargs)
	return HttpResponseRedirect(url + "?%s" % params)


def registration(request):
	from registration.views import register

	return register(request, form_class=MatrrRegistrationForm)


def logout(request, next_page=None):
	from django.contrib.auth import logout as auth_logout

	auth_logout(request)
	return HttpResponseRedirect(next_page or "/")


def index_view(request):
	index_context = {'event_list': Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name')[:5],
					 'pub_list': Publication.objects.all().exclude(published_year=None).order_by('-published_year',
																								 '-published_month')[:2]
		,
					 'search_form': FulltextSearchForm(),
					 'plot_gallery': True,
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
def cohorts_view_available(request):
	cohorts = Cohort.objects.nicotine_filter(request.user).filter(coh_upcoming=False).order_by('coh_cohort_name')
	template_name = 'matrr/available_cohorts.html'
	return __cohorts_view(request, cohorts, template_name)


def cohorts_view_upcoming(request):
	cohorts = Cohort.objects.nicotine_filter(request.user).filter(coh_upcoming=True).order_by('coh_cohort_name')
	template_name = 'matrr/upcoming_cohorts.html'
	return __cohorts_view(request, cohorts, template_name)


def cohorts_view_all(request):
	cohorts = Cohort.objects.nicotine_filter(request.user).order_by('coh_cohort_name')
	template_name = 'matrr/cohorts.html'
	return __cohorts_view(request, cohorts, template_name)


def cohorts_view_assay(request):
	return redirect(reverse('tissue-shop-landing', args=[Cohort.objects.get(coh_cohort_name__iexact="Assay Development").pk, ]))


def matrr_handler500(request):
	from django.core.context_processors import static

	return render_to_response('500.html', static(request), context_instance=RequestContext(request)
	)


def __set_images(cohort, user):
	cohort.images = cohort.image_set.filter(canonical=True).vip_filter(user)
	return cohort


def __cohorts_view(request, cohorts, template_name):
	cohorts = [__set_images(cohort, request.user) for cohort in cohorts]

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

	return render_to_response(template_name, {'cohort_list': cohort_list},
							  context_instance=RequestContext(request))


def cohort_details(request, **kwargs):
	# Handle the displaying of cohort details
	if kwargs.has_key('pk'):
		cohort = get_object_or_404(Cohort, pk=kwargs['pk'])
		coh_data = True if cohort.cod_set.all().count() else False
		images = CohortImage.objects.filter(cohort=cohort, canonical=True).vip_filter(request.user)
	else:
		return redirect(reverse('cohorts'))
	return render_to_response('matrr/cohort.html', {'cohort': cohort, 'images': images, 'coh_data': coh_data, 'plot_gallery': True}, context_instance=RequestContext(request))


def __monkey_detail(request, mky_id, coh_id=0):
	try:
		monkey = Monkey.objects.get(mky_id=mky_id)
	except:
		raise Http404(u"No %(verbose_name)s found matching the query" %
					  {'verbose_name': Monkey._meta.verbose_name})

	if coh_id and str(monkey.cohort.coh_cohort_id) != coh_id:
		raise Http404(u"No %(verbose_name)s found matching the query" %
					  {'verbose_name': Monkey._meta.verbose_name})

	images = MonkeyImage.objects.filter(monkey=monkey, canonical=True).vip_filter(request.user).order_by('method')
	return render_to_response('matrr/monkey.html', {'monkey': monkey, 'images': images, 'plot_gallery': True},
							  context_instance=RequestContext(request))

#todo: change the urls file to handle these in the same view, if possible
def monkey_cohort_detail_view(request, coh_id, mky_id):
	return __monkey_detail(request, mky_id, coh_id=coh_id)

def monkey_detail_view(request, mky_id):
	return __monkey_detail(request, mky_id)


def get_or_create_cart(request, cohort):
	# get the user's cart if it already exists
	if Request.objects.cart().filter(user=request.user.id).count():
		cart_request = Request.objects.cart().get(user=request.user.id)
		# check that the cart is for this cohort
		if cart_request.cohort != cohort:
			# take corrective action (display a page that asks the user if they want to abandon their cart and start with this cohort)
			# if the cart is empty, just delete it
			if not cart_request.get_requested_tissue_count():
				cart_request.delete()
				#create a new cart
				cart_request = Request(user=request.user, req_status=RequestStatus.Cart,
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
		cart_request = Request(user=request.user, req_status=RequestStatus.Cart,
							   cohort=cohort, req_request_date=datetime.now())
		cart_request.save()

	return cart_request


def tissue_shop_detail_view(request, coh_id, tissue_id):
	current_cohort = Cohort.objects.get(coh_cohort_id=coh_id)
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
	if current_tissue.tst_tissue_name == "Plasma":
		messages.info(request, "The policy for blood samples is not the same as most of the other tissue.")
		messages.info(request,
					  """
					  You will need to contact Kathy Grant directly (grantka@ohsu.edu) due to the
					  many NIH supported projects currently underway using these samples.
					  Nevertheless, each of these projects will begin posting the data (such as
					  protein and hormone data).  Helping labs with in silico hypothesis testing
					  is a future aim of the MATRR.
					  """)


	instance = TissueRequest(tissue_type=current_tissue, req_request=cart_request)

	# Upcoming cohort warning
	if current_cohort.coh_upcoming:
		import datetime

		today = datetime.date.today()
		try:
			necropsy_date = current_cohort.cohort_event_set.filter(event__evt_name="Necropsy Start")[0].cev_date
			days_to_necropsy = (necropsy_date - today).days
			if days_to_necropsy >= 6 * 60:
				messages.warning(request,
								 "Warning:  Because this cohort has not yet gone to necropsy, we cannot guarantee all tissue from all monkeys will be available for request, due to uncontrollable events (illness, accidental death, etc).  If a requested tissue was approved but is not available after necropsy the user will be notified and the request and its cost will be corrected.  Thank you for your understanding regarding this uncertainty.")
		except:
			messages.warning(request,
							 "Warning:  Because this cohort has not yet gone to necropsy, we cannot guarantee all tissue from all monkeys will be available for request, due to uncontrollable events (illness, accidental death, etc).  If a requested tissue was approved but is not available after necropsy the user will be notified and the request and its cost will be corrected.  Thank you for your understanding regarding this uncertainty.")

	if request.method != 'POST':
		# now we need to create the form for the tissue type
		tissue_request_form = TissueRequestForm(req_request=cart_request, tissue=current_tissue, instance=instance,
												initial={'monkeys': current_cohort.monkey_set.all()})
		# create the response
		tissue_request_form.visible_fields()
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
			url = reverse('tissue-shop-landing', args=[cart_request.cohort.coh_cohort_id, ])
			try:
				tissue_request_form.save()
			except Exception as e:
				print e
				messages.error(request, 'Error adding tissue to cart.  Possible duplicate tissue request already in cart.')
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
		data['req_status'] = cart_request.req_status
		data['cohort'] = cart_request.cohort.coh_cohort_id
		checkout_form = CartCheckoutForm(request.POST, request.FILES, instance=cart_request)

		if checkout_form.is_valid() and request.POST['submit'] == 'checkout':
			cart_request.req_experimental_plan = checkout_form.cleaned_data['req_experimental_plan']
			cart_request.req_notes = checkout_form.cleaned_data['req_notes']
			cart_request.req_request_date = datetime.now
			cart_request.submit_request()
			cart_request.save()

			messages.success(request, 'Tissue Request Submitted.')
			return redirect('/')
		else:
			return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form},
									  context_instance=context)


@user_passes_test(lambda u: u.has_perm('matrr.change_review'), login_url='/denied/')
def reviews_list_view(request):
	# get a list of all reviews for the current user
	reviews = Review.objects.filter(user=request.user.id).filter(req_request__req_status=RequestStatus.Submitted)

	finished_reviews = [review for review in reviews if review.is_finished()]
	unfinished_reviews = [review for review in reviews if not review.is_finished()]

	return render_to_response('matrr/review/reviews.html',
			{'finished_reviews': finished_reviews,
			 'unfinished_reviews': unfinished_reviews,
			 'num_finished': len(finished_reviews),
			 'num_unfinished': len(unfinished_reviews), },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.verify_mta'), login_url='/denied/')
def mta_list(request):
	MTAValidationFormSet = formset_factory(MTAValidationForm, extra=0)
	if request.method == "POST":
		formset = MTAValidationFormSet(request.POST)
		if formset.is_valid():
			for mtaform in formset:
				data = mtaform.cleaned_data
				mta = Mta.objects.get(pk=data['primarykey'])
				if data['is_valid'] != mta.mta_is_valid:
					mta.mta_is_valid = data['is_valid']
					mta.save()
			messages.success(request, message="This page of MTAs has been successfully updated.")
		else:
			messages.error(request, formset.errors)

	all_mta = Mta.objects.all().order_by('user', 'pk')
	paginator = Paginator(all_mta, 15)

	if request.GET and 'page' in request.GET:
		page = request.GET.get('page')
	else:
		page = 1
	try:
		mta_list = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		mta_list = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		mta_list = paginator.page(paginator.num_pages)

	initial = []
	for mta in mta_list.object_list:
		mta_initial = {'is_valid': mta.mta_is_valid, 'username': mta.user.username, 'title': mta.mta_title, 'url': mta.mta_file.url, 'primarykey': mta.pk}
		initial.append(mta_initial)

	formset = MTAValidationFormSet(initial=initial)
	return render_to_response('matrr/mta_list.html', {'formset': formset, 'mta_list': mta_list}, context_instance=RequestContext(request))


def mta_upload(request):
	# make blank mta instance
	mta_object = Mta(user=request.user)
	# make a MTA upload form if one does not exist
	if request.method == 'POST':
		if 'request_form' in request.POST:
			if settings.PRODUCTION:
				account = request.user.account
				emails.send_mta_uploaded_email(account)
			else:
				print "%s - New request email not sent, settings.PRODUCTION = %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), settings.PRODUCTION)
			messages.success(request, 'A MATRR administrator has been notified of your MTA request and will contact you with more information.')
			return redirect(reverse('account-view'))
		form = MtaForm(request.POST, request.FILES, instance=mta_object)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			emails.notify_mta_uploaded(form.instance)
			messages.success(request, 'MTA Uploaded Successfully')
			return redirect(reverse('account-view'))
	else:
		# create the form for the MTA upload
		form = MtaForm(instance=mta_object)
	return render_to_response('matrr/upload_forms/mta_upload_form.html',
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.add_cohortdata'), login_url='/denied/')
def cod_upload(request, coh_id=1):
	if request.method == 'POST':
		form = CodForm(request.POST, request.FILES, user=request.user)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			messages.success(request, 'Upload Successful')
			return redirect(reverse('cohort-details', args=[str(coh_id)]))
	else:
		cohort = Cohort.objects.get(pk=coh_id)
		form = CodForm(cohort=cohort, user=request.user)
	return render_to_response('matrr/upload_forms/cod_upload_form.html', {'form': form, }, context_instance=RequestContext(request))

@staff_member_required
def account_verify(request, user_id):
	account = get_object_or_404(Account, pk=user_id)
	if not account.verified:
		account.verified = True
		account.save()
		#		send email
		emails.send_account_verified_email(account)
		messages.success(request, "Account %s was successfully verified." % account.user.username)
	else:
		messages.info(request, "Account %s is already verified." % account.user.username)
	return render_to_response('base.html', {}, context_instance=RequestContext(request))


def account_info(request):
	# make address form if one does not exist
	if request.method == 'POST':
		form = AccountForm(data=request.POST, instance=request.user.account)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			messages.success(request, 'Account Info Saved')
			return redirect(reverse('account-view'))
	else:
		#create the form for shipping address
		form = AccountForm(instance=request.user.account)
	return render_to_response('matrr/account/account_info_form.html',
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))


def account_mta(request):
	account = request.user.account
	if request.method == 'POST':
		form = AccountMTAForm(data=request.POST)
		if form.is_valid():
			institution = form.cleaned_data['institution'].ins_institution_name
			account.act_mta = institution
			account.save()

			if institution == "Non-UBMTA Institution":
				return redirect('mta-upload')
			#				messages.info(request, "If your institution is not part of the <acronym>, you must download, sign, scan, and upload a Material Transfer Agreement.  ")
			else:
				messages.success(request, 'Account Info Saved')
				return redirect(reverse('account-view'))
	else:
		try:
			institution = Institution.objects.get(ins_institution_name=account.act_mta)
		except Institution.DoesNotExist:
			institution = Institution.objects.get(ins_institution_name='Non-UBMTA Institution')
		form = AccountMTAForm(initial={'institution': institution})
	return render_to_response('matrr/account/account_mta.html',
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))


def account_address(request):
	# make address form if one does not exist
	if request.method == 'POST':
		form = AddressAccountForm(data=request.POST, instance=request.user.account)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			messages.success(request, 'Account Address Saved')
			return redirect(reverse('account-view'))
	else:
		#create the form for shipping address
		form = AddressAccountForm(instance=request.user.account)
	return render_to_response('matrr/account/account_address_form.html',
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))


def account_shipping(request):
	# make address form if one does not exist
	if request.method == 'POST':
		form = ShippingAccountForm(data=request.POST, instance=request.user.account)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			messages.success(request, 'Shipping Address Saved')
			return redirect(reverse('account-view'))
	else:
		#create the form for shipping address
		form = ShippingAccountForm(instance=request.user.account)
	return render_to_response('matrr/account/account_shipping_form.html',
			{'form': form,
			 'user': request.user
		},
							  context_instance=RequestContext(request))


def account_view(request):
	return account_detail_view(request=request, user_id=request.user.id)


def account_detail_view(request, user_id):
	if request.user.id == user_id:
		edit = True
	else:
		edit = False
	# get information from the act_account relation

	account_info = get_object_or_404(Account, pk=user_id)
	mta_info = Mta.objects.filter(user__id=user_id)
	data_files = DataFile.objects.filter(account__user=user_id)
	display_rud_from = date.today() - timedelta(days=30)
	urge_rud_from = date.today() - timedelta(days=90)
	pending_rud = Shipment.objects.filter(req_request__user=user_id, shp_shipment_date__lte=display_rud_from,
										  shp_shipment_date__gte=urge_rud_from, req_request__rud_set=None)
	urged_rud = Shipment.objects.filter(req_request__user=user_id, shp_shipment_date__lte=urge_rud_from,
										req_request__rud_set=None)

	rud_info = ResearchUpdate.objects.filter(req_request__user=user_id)

	if pending_rud or urged_rud or rud_info:
		rud_on = True
	else:
		rud_on = False

	order_list = Request.objects.processed().filter(user__id=user_id).order_by("-req_request_date")[:20]

	return render_to_response('matrr/account/account.html',
			{'account_info': account_info,
			 'mta_info': mta_info,
			 'data_files': data_files,
			 'rud_info': rud_info,
			 'rud_on': rud_on,
			 'pending_rud': pending_rud,
			 'urged_rud': urged_rud,
			 'order_list': order_list,
			 'edit': edit,
			 },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_other_accounts'), login_url='/denied/')
def account_reviewer_view(request, user_id):
	return account_detail_view(request, user_id)


@user_passes_test(lambda u: u.has_perm('matrr.change_review'), login_url='/denied/')
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
			return redirect(reverse('review-list'))

		form = ReviewForm(data=request.POST.copy(), instance=review)

		if form.is_valid():
			# all the forms are valid, so save the data
			form.save()
			messages.success(request, 'Review saved.')
			return redirect(reverse('review-list'))
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


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_history_list(request):
	req_requests = Request.objects.evaluated().order_by('-req_modified_date')
	req_requests = req_requests.distinct()

	reviewers = Account.objects.users_with_perm('change_review').order_by('-username')

	paginator = Paginator(req_requests, 20) # Show 25 contacts per page

	if request.GET and 'page' in request.GET:
		page = request.GET.get('page')
	else:
		page = 1

	try:
		verified_requests = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		verified_requests = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		verified_requests = paginator.page(paginator.num_pages)

	return render_to_response('matrr/review/reviews_history.html',
			{'req_requests': verified_requests,
			 'reviewers': reviewers,
			 },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_overview_list(request):
	# get a list of all tissue requests that are submitted, but not accepted or rejected

	req_requests = Request.objects.submitted()
	# get a list of all reviewers
	overviewers = Account.objects.users_with_perm('change_review')
	for req_request in req_requests:
		req_request.complete = list()
		for reviewer in overviewers:
			for review in req_request.review_set.filter(user=reviewer):
				if review.is_finished():
					req_request.complete.append("complete")
				else:
					req_request.complete.append("pending")

	return render_to_response('matrr/review/reviews_overviews.html',
			{'req_requests': req_requests,
			 'reviewers': overviewers,
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
					10 - (math.fabs(5 - tissue_request_review.get_quantity(css=True)) * 2))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_overview_price(request, req_request_id):
	req = get_object_or_404(Request, req_request_id=req_request_id)
	#	est_cost = req.get_total_estimated_cost()

	accepted_or_partial = False
	PriceFormset = modelformset_factory(TissueRequest, fields=['rtt_estimated_cost'], extra=0)

	for tissue_request in req.get_requested_tissues():
		if tissue_request.get_accepted() != Acceptance.Rejected:
			accepted_or_partial = True

	if not accepted_or_partial:
		for tr in req.tissue_request_set.all():
			tr.rtt_estimated_cost = 0
			tr.save()
		return redirect(reverse('review-overview-process', args=[req_request_id]))

	if request.POST:
		cost_forms = PriceFormset(request.POST)
		if cost_forms.is_valid():
			rtts = cost_forms.save()
			#			for cost_form in cost_forms:
			#				print cost_form.cleaned_data['rtt_estimated_cost']
			#				print cost_form.instance.get_estimated_cost()
			#				if cost_form.cleaned_data['rtt_estimated_cost'] != cost_form.instance.get_estimated_cost():
			#					tr = get_object_or_404(TissueRequest, pk = cost_form.instance.pk)
			#					tr.rtt_estimated_cost = cost_form.cleaned_data['rtt_estimated_cost']
			#					print "tr"
			#					print tr.rtt_estimated_cost
			#					tr.save()
			#				cost_form.save()
			#				print cost_form.instance.pk
			#				print req.get_requested_tissues()[0].pk
			#				rtt_id = cost_form.cleaned_data['rtt']
			#				try:
			#					tr = TissueRequest.objects.get(pk=rtt_id)
			#				except:
			#					raise Http404("This page does not exist")
			#				if tr not in req.tissue_request_set.all():
			#					raise Http404("This page does not exist")
			#				tr.rtt_estimated_cost = cost_form.cleaned_data['cost']
			#				tr.save()
			#			print "redirect"
			#			print req.get_requested_tissues()[0].get_estimated_cost()
			#			print "reds"
			return redirect(reverse('review-overview-process', args=[req_request_id]))
		else:
			return render_to_response('matrr/review/review_overview_price.html',
					{'req': req, 'forms': cost_forms},
									  context_instance=RequestContext(request))
	else:
		queryset = req.tissue_request_set.all()
		accepted_queryset = set()
		for tr in queryset:
			if tr.get_accepted() != Acceptance.Rejected:
				accepted_queryset.add(tr.pk)

		quer = TissueRequest.objects.filter(pk__in=accepted_queryset)
		for tr in quer:
			if tr.rtt_estimated_cost is None:
				tr.rtt_estimated_cost = tr.get_estimated_cost()
				tr.save()
		cost_forms = PriceFormset(queryset=quer)
		#		import pdb
		#		pdb.set_trace()
		#		for cost_form in cost_forms.forms:
		#			if cost_form.fields['rtt_estimated_cost'].initial == None:
		#				cost_form.fields['rtt_estimated_cost'].initial = cost_form.instance.get_estimated_cost()

		#		cost_form.fields['cost'].initial = est_cost
		return render_to_response('matrr/review/review_overview_price.html',
				{'req': req, 'forms': cost_forms},
								  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_overview(request, req_request_id):
	# get the request being reviewed
	req_request = get_object_or_404(Request, pk=req_request_id) # get or 404 ?
	no_monkeys = False

	if req_request.is_evaluated():
		no_monkeys = True
	if  'HTTP_REFERER' in request.META:
		back_url = request.META['HTTP_REFERER']
	else:
		back_url = ""

	for tr in req_request.tissue_request_set.all():
		tr.rtt_estimated_cost = None
		tr.save()
	req_request.save()

	TissueRequestFormSet = modelformset_factory(TissueRequest, form=TissueRequestProcessForm, extra=0)
	if request.POST:
		tissue_request_forms = TissueRequestFormSet(request.POST, prefix='tissue_requests')

		if tissue_request_forms.is_valid():
			tissue_request_forms.save()
			#return redirect(reverse('review-overview-process', args=[req_request_id]))
			# move to price confirmation

			#			req_request.req_estimated_cost = None # discard the manual price, do not use price from previous unsuccessful process attempts
			for tr in req_request.tissue_request_set.all():
				tr.rtt_estimated_cost = None
				tr.save()
			req_request.save()
			return redirect(reverse('review-overview-price', args=[req_request_id]))
		else:
			# get the reviews for the request
			reviews = list(req_request.review_set.all())
			reviews.sort(key=lambda x: x.user.username)

			sort_tissues_and_add_quantity_css_value(tissue_request_forms)

			for form in tissue_request_forms:
				form.instance.not_accepted_monkeys = list()
				for monkey in form.instance.monkeys.all():
					if monkey not in form.instance.accepted_monkeys.all():
						form.instance.not_accepted_monkeys.append(monkey)

			return render_to_response('matrr/review/review_overview.html',
					{'reviews': reviews,
					 'req_request': req_request,
					 'tissue_requests': tissue_request_forms,
					 'Availability': Availability,
					 'back_url': back_url,
					 'no_monkeys': no_monkeys
				},
									  context_instance=RequestContext(request))

	else:
		# get the tissue requests
		tissue_request_forms = TissueRequestFormSet(queryset=req_request.tissue_request_set.all(),
													prefix='tissue_requests')
		for form in tissue_request_forms:
			form.instance.not_accepted_monkeys = list()
			for monkey in form.instance.monkeys.all():
				if monkey not in form.instance.accepted_monkeys.all():
					form.instance.not_accepted_monkeys.append(monkey)

		# get the reviews for the request
		reviews = list(req_request.review_set.all())
		reviews.sort(key=lambda x: x.user.username)

		sort_tissues_and_add_quantity_css_value(tissue_request_forms)

		return render_to_response('matrr/review/review_overview.html',
				{'reviews': reviews,
				 'req_request': req_request,
				 'tissue_requests': tissue_request_forms,
				 'Availability': Availability,
				 'back_url': back_url,
				 'no_monkeys': no_monkeys
			},
								  context_instance=RequestContext(request))


def orders_list(request):
	# get a list of all requests for the user
	order_list = ''
	orders = Request.objects.processed().filter(user=request.user).order_by('-req_request_date')
	revised = Request.objects.revised_or_duplicated().filter(user=request.user)
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

	return render_to_response('matrr/order/orders.html',
			{'order_list': order_list, 'revised': revised,
			 },
							  context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user or u.has_perm('matrr.change_shipment'), arg_name='req_request_id', redirect_url='/denied/')
def order_detail(request, req_request_id, edit=False):
	# get the request
	req_request = Request.objects.get(req_request_id=req_request_id)
	# check that the request belongs to this user
	#	if req_request.user != request.user and Group.objects.get(name='Committee') not in request.user.groups.all():
	#		# if the request does not belong to the user, return a 404 error (alternately, we could give a permission denied message)
	#		raise Http404('This page does not exist.')

	shipments = req_request.get_shipments()
	eval = req_request.is_evaluated()
	po_form = ''
	if not req_request.req_status == 'SH' and not req_request.req_status == 'RJ':
		if request.user == req_request.user or request.user.is_superuser:
			po_form = PurchaseOrderForm(instance=req_request)
		if request.method == 'POST':
			_prev_shippable = req_request.can_be_shipped()
			po_form = PurchaseOrderForm(instance=req_request, data=request.POST)
			if po_form.is_valid():
				po_form.save()
				messages.success(request, "Purchase Order number has been saved.")
				if not _prev_shippable and req_request.can_be_shipped():  # couldn't be shipped, but now can
					from matrr.emails import send_shipment_ready_notification

					send_shipment_ready_notification(req_request)
			else:
				messages.error(request, "Purchase Order form invalid, please try again.  Please notify a MATRR admin if this message is erroneous.")
	if request.GET.get('export', False):
		#Create the HttpResponse object with the appropriate PDF headers.
		response = HttpResponse(mimetype='application/pdf')
		response['Content-Disposition'] = 'attachment; filename=Invoice-%d.pdf' % req_request.pk
		context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
		helper.export_template_to_pdf('pdf_templates/invoice.html', context, outfile=response)
		return response

	return render_to_response('matrr/order/order_detail.html',
			{'order': req_request,
			 'Acceptance': Acceptance,
			 'RequestStatus': RequestStatus,
			 'shipped': req_request.is_shipped(),
			 'shipments': shipments,
			 'after_submitted': eval,
			 'edit': edit,
			 'po_form': po_form,
			 },
							  context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_revise(request, req_request_id):
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_revised():
		raise Http404('This page does not exist.')
	return render_to_response('matrr/order/order_revise.html', {'req_id': req_request_id}, context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_revise_confirm(request, req_request_id):
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_revised() or not request.POST or request.POST['submit'] != "duplicate":
		raise Http404('This page does not exist.')
	req.create_revised_duplicate()
	messages.success(request, 'A new editable copy has been created. You can find it under Revised Orders.')
	return redirect(reverse('order-list'))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_duplicate(request, req_request_id):
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_duplicated():
		raise Http404('This page does not exist.')

	tissues = list() # Tissues to be duplicated,
	for rtt in req.tissue_request_set.all():
		if rtt.accepted_monkeys.all(): # only test tissues with accepted monkeys.  Rejected tissues won't be duplicated anyway
			if rtt.accepted_monkeys.all().count() == req.cohort.monkey_set.all().count():
				tissues.append(rtt.tissue_type)

	queryset = Cohort.objects.nicotine_filter(request.user).exclude(pk=req.cohort.pk).order_by('coh_cohort_name')
	return render_to_response('matrr/order/order_duplicate.html', {'req_id': req_request_id, 'cohort_form': CohortSelectForm(subject_queryset=queryset, subject_widget=widgets.Select)}, context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_duplicate_confirm(request, req_request_id):
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_duplicated() or not request.POST or request.POST['submit'] != "duplicate":
		raise Http404('This page does not exist.')

	cohort_form = CohortSelectForm(data=request.POST)
	if cohort_form.is_valid():
		coh = cohort_form.cleaned_data['subject']
		req.create_duplicate(coh)
		messages.success(request, 'A new editable copy has been created. You can find it under Revised Orders.')
	else:
		messages.error(request, "Invalid form")
		return redirect(reverse('order-duplicate'))
	return redirect(reverse('order-list'))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_edit(request, req_request_id):
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_edited():
		raise Http404('This page does not exist.')

	return order_detail(request, req_request_id=req_request_id, edit=True)


@user_owner_test(lambda u, rtt_id: u == TissueRequest.objects.get(rtt_tissue_request_id=rtt_id).req_request.user, arg_name='req_rtt_id', redirect_url='/denied/')
def order_delete_tissue(request, req_rtt_id):
	rtt = TissueRequest.objects.get(rtt_tissue_request_id=req_rtt_id)
	if not rtt.req_request.can_be_edited() or not request.POST or request.POST['submit'] != "delete":
		raise Http404('This page does not exist.')
	rtt.delete()
	messages.success(request, 'Tissue request deleted.')
	return redirect(reverse('order-edit', args=[rtt.req_request.req_request_id, ]))


@user_owner_test(lambda u, rtt_id: u == TissueRequest.objects.get(rtt_tissue_request_id=rtt_id).req_request.user, arg_name='req_rtt_id', redirect_url='/denied/')
def order_edit_tissue(request, req_rtt_id):
	rtt = TissueRequest.objects.get(rtt_tissue_request_id=req_rtt_id)
	if not rtt.req_request.can_be_edited():
		raise Http404('This page does not exist.')

	if request.method != 'POST': #or request.POST['submit'] == 'edit':
		# create a form so the item can be edited
		tissue_request_form = TissueRequestForm(instance=rtt,
												req_request=rtt.req_request,
												tissue=rtt.get_tissue())
		return render_to_response('matrr/order/orders_tissue_edit.html', {'form': tissue_request_form,
																		  'cohort': rtt.req_request.cohort,
																		  'tissue': rtt.get_tissue(),
																		  'cart_item': rtt, },
								  context_instance=RequestContext(request))
	else:
		if request.POST['submit'] == 'cancel':
			messages.info(request, 'No changes were made.')
			return redirect(reverse('order-edit', args=[rtt.req_request.req_request_id, ]))
		elif request.POST['submit'] == 'delete':
			return order_delete_tissue(request, req_rtt_id=req_rtt_id) # order_delete_tissue's decorator looks for this as a kwarg, not an arg.  The URL passes the function a kwarg.
		else:
			# validate the form and update the cart_item
			tissue_request_form = TissueRequestForm(instance=rtt,
													data=request.POST,
													req_request=rtt.req_request,
													tissue=rtt.get_tissue())
			if tissue_request_form.is_valid():
				# the form is valid, so update the tissue request
				tissue_request_form.save()
				messages.success(request, 'Tissue request updated.')
				return redirect(reverse('order-edit', args=[rtt.req_request.req_request_id, ]))
			else:
				return render_to_response('matrr/order/orders_tissue_edit.html', {'form': tissue_request_form,
																				  'cohort': rtt.req_request.cohort,
																				  'tissue_type': rtt.get_tissue(),
																				  'cart_item': rtt, },
										  context_instance=RequestContext(request))

# this should be no more necessary, if we find some place, where this is being used, we should replace it be sendfile view
#def experimental_plan_view(request, plan):
#	# create the response
#	response = HttpResponse(mimetype='application/force-download')
#	response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(plan)
#	response['X-Sendfile'] = smart_str(settings.MEDIA_ROOT + 'media/experimental_plans/' + plan)
#
#	# serve the file if the user is a committee member or Uberuser
#	if request.user.groups.filter(name='Committee').count() != 0 or\
#	   request.user.groups.filter(name='Uberuser').count() != 0:
#		return response
#
#	# check that the plan belongs to the user
#	if Request.objects.filter(user=request.user, req_experimental_plan='experimental_plans/' + plan).count() > 0:
#		return response
#
#	#otherwise return a 404 error
#	raise Http404('This page does not exist.')


def tissue_shop_landing_view(request, coh_id):
	context = dict()
	assay = Cohort.objects.get(coh_cohort_name__iexact="Assay Development")
	cohort = Cohort.objects.get(coh_cohort_id=coh_id)
	context['cohort'] = cohort
	if cohort != assay:
		context['assay'] = assay
	categories = list(TissueCategory.objects.order_by('cat_name').all())
	if TissueCategory.objects.filter(cat_name='Custom'):
		custom = TissueCategory.objects.get(cat_name='Custom')
		categories.remove(custom)
		categories.append(custom)

	context['categories'] = categories
	context['cohort'] = cohort
	if cohort != assay:
		context['assay'] = assay
	return render_to_response('matrr/tissue_shopping_landing.html', context, context_instance=RequestContext(request))


def tissue_list(request, tissue_category=None, coh_id=None):
	cohort = None
	if coh_id is not None:
		cohort = Cohort.objects.get(coh_cohort_id=coh_id)
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
													 'cohort': cohort,
													 'plot_gallery': True, },
							  context_instance=RequestContext(request))


def remove_values_from_list(base_list, removal_list):
	return [value for value in base_list if value not in removal_list]


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
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
		status = RequestStatus.Accepted
		email_template = 'matrr/review/request_accepted_email.txt'
	elif accepted and partial:
		status = RequestStatus.Partially
		email_template = 'matrr/review/request_partially_accepted_email.txt'
	else:
		status = RequestStatus.Rejected
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
				req_request.req_status = status
				req_request.save()
				messages.success(request, "The tissue request has been processed.")
				if settings.PRODUCTION:
					emails.send_processed_request_email(form.cleaned_data, req_request)
					messages.info(request, str(req_request.user.username) + " was sent an email informing him/her that the request was processed.")
				return redirect(reverse('review-overview-list'))
			else:
				return render_to_response('matrr/review/process.html',
						{'form': form,
						 'req_request': req_request,
						 'Availability': Availability,
						 'Acceptance': Acceptance},
										  context_instance=RequestContext(request))
		else:
			messages.info(request, "The tissue request has not been processed.  No email was sent.")
			return redirect(reverse('review-overview-list'))
	else:
		# get the subject
		subject = render_to_string('matrr/review/request_email_subject.txt',
				{'status': status, 'cohort': req_request.cohort})
		# Email subject *must not* contain newlines
		subject = ''.join(subject.splitlines())
		request_url = reverse('order-detail', args=[req_request.req_request_id])
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
				emails.send_contact_us_email(form.cleaned_data, request.user)
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
	form = FulltextSearchForm()
	num_results = 0
	monkey_auth = False

	terms = ''
	results = dict()
	if request.method == 'POST':
		form = FulltextSearchForm(request.POST)
		if form.is_valid():
			terms = form.cleaned_data['terms']

			from django.db.models.loading import get_model
			from settings import PRIVATE_SEARCH_INDEXES, PUBLIC_SEARCH_INDEXES

			SEARCH_INDEXES = PUBLIC_SEARCH_INDEXES

			for key, value in PRIVATE_SEARCH_INDEXES.items():
				if 'monkey_auth' in key and request.user.has_perm('matrr.monkey_view_confidential'):
					monkey_auth = True
					SEARCH_INDEXES['monkey'] = value
				#					results['monkeys'] = search_index(terms, SEARCH_INDEXES[key], Monkey)

			for key, value in SEARCH_INDEXES.items():
				results[key] = search_index(terms, value[0], get_model('matrr', value[1]))

			num_results = 0
			for key in results:
				num_results += len(results[key])

	return render_to_response('matrr/search.html',
			{'terms': terms,
			 'results': results,
			 'num_results': num_results,
			 'monkey_auth': monkey_auth,
			 'form': form},
							  context_instance=RequestContext(request))


def advanced_search(request):
	monkey_auth = request.user.has_perm('matrr.monkey_view_confidential')
	select_form = AdvancedSearchSelectForm(prefix='select')
	filter_form = AdvancedSearchFilterForm(prefix='filter')

#	results = Monkey.objects.all().order_by('cohort__coh_cohort_name', 'pk')
#	mpns = MonkeyProtein.objects.filter(monkey__in=results).exclude(mpn_stdev__lt=1)
#	for mky in results:
#		mky.mpns =  mpns.filter(monkey=mky).values_list('protein__pro_abbrev', flat=True).distinct()

	return render_to_response('matrr/advanced_search.html',
			{'monkeys': Monkey.objects.all(),
			 'monkey_auth': monkey_auth,
			 'select_form': select_form,
			 'filter_form': filter_form,
			 'cohorts': Cohort.objects.nicotine_filter(request.user)},
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipping_history(request):
#	Shipped Requests
	shipped_requests = Request.objects.shipped().order_by('-shipments__shp_shipment_date').distinct()
	recently_shipped = shipped_requests[0:5]
	users_with_shipments = shipped_requests.values_list('user', flat=True)
	user_list = User.objects.filter(pk__in=users_with_shipments).order_by('username')
	user_list = ((user, shipped_requests.filter(user=user).count()) for user in user_list)
	return render_to_response('matrr/shipping/shipping_history.html', {'recently_shipped': recently_shipped, 'user_list': user_list}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipping_history_user(request, user_id):
	user = get_object_or_404(User, pk=user_id)
	shipped_requests = Request.objects.shipped().filter(user=user).order_by('-shipments__shp_shipment_date').distinct()
	return render_to_response('matrr/shipping/shipping_history_user.html', {'user': user, 'shipped_requests': shipped_requests}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment') or u.has_perm('matrr.ship_genetics'), login_url='/denied/')
def shipping_overview(request):
	#Requests Pending Shipment
	accepted_requests = Request.objects.none()
	for req_request in Request.objects.accepted_and_partially():
		if req_request.is_missing_shipments():
			if request.user.has_perm('matrr.change_shipment') or (req_request.contains_genetics() and request.user.has_perm('matrr.ship_genetics')):
				accepted_requests |= Request.objects.filter(pk=req_request.pk)
	# Pending Shipments
	pending_shipments = Shipment.objects.none()
	if request.user.has_perm('matrr.change_shipment'):
		pending_shipments |= Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Unshipped)
	if request.user.has_perm('matrr.ship_genetics'):
		pending_shipments |= Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Genetics)
	# Shipped Shipments
	shipped_shipments = Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Shipped).exclude(req_request__req_status=RequestStatus.Shipped)

	return render_to_response('matrr/shipping/shipping_overview.html',
			{'accepted_requests': accepted_requests,
			 'pending_shipments': pending_shipments,
			 'shipped_shipments': shipped_shipments, },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipment_creator(request, req_request_id):
	req_request = get_object_or_404(Request, pk=req_request_id)
	acc_rtt_wo_shipment = req_request.tissue_request_set.filter(shipment=None).exclude(accepted_monkeys=None)

	if request.method == 'POST':
		tissue_shipment_form = TissueShipmentForm(acc_rtt_wo_shipment, data=request.POST)
		if tissue_shipment_form.is_valid():
			# Sanity check
			# Do not allow the user to create a shipment with both tissues and genetics
			contains_genetics = False
			contains_tissues = False
			for rtt in tissue_shipment_form.cleaned_data['tissue_requests']:
				_genetics = rtt.contains_genetics()
				contains_genetics = contains_genetics or _genetics
				contains_tissues = contains_tissues or not _genetics
				if contains_genetics and contains_tissues:
					messages.error(request, "You cannot send tissues and genetics in the same shipment.  DNA/RNA tissue shipments must be built and shipped separately.")
					return render_to_response('matrr/shipping/shipment_creator.html',
						{'req_request': req_request, 'tissue_shipment_form': tissue_shipment_form},
						context_instance=RequestContext(request))

			shipment = Shipment()
			shipment.user = request.user
			shipment.req_request = req_request
			shipment.save()
			for rtt in tissue_shipment_form.cleaned_data['tissue_requests']:
				rtt.shipment = shipment
				rtt.save()
			return redirect(reverse('shipment-detail', args=[shipment.pk]))
		else:
			messages.error(request, "There was an error processing this form.  If this continues to occur please notify a MATRR admin.")

	tissue_shipment_form = TissueShipmentForm(acc_rtt_wo_shipment)
	return render_to_response('matrr/shipping/shipment_creator.html',
		{'req_request': req_request, 'tissue_shipment_form': tissue_shipment_form},
		context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipment_detail(request, shipment_id):
	confirm_ship = False
	confirm_delete_shipment = False

	shipment = get_object_or_404(Shipment, pk=shipment_id)
	req_request = shipment.req_request

	if req_request.req_status != RequestStatus.Shipped or shipment.shp_shipment_date is None:
		edit = True
	else:
		edit = False

	tracking_number = shipment.shp_tracking
	tracking_form = TrackingNumberForm(instance=shipment)
	if request.method == 'POST':
		if 'tracking' in request.POST:
			tracking_form = TrackingNumberForm(instance=shipment, data=request.POST)
			if tracking_form.is_valid():
				tracking_form.save()
				messages.success(request, "Tracking number has been saved.")

		if 'ship' in request.POST:
			if not req_request.can_be_shipped(): # do a sanity check
				messages.warning(request,
								 "A request can only be shipped if all of the following are true:\
													  1) the request has been accepted and not yet shipped, \
													  2) user has submitted a Purchase Order number, \
													  3) User has submitted a valid MTA, \
								 					  4) User has no pending research update requests.")
			else:
				confirm_ship = True
				messages.info(request, "This request is ready to ship.  If this shipment has been shipped, click the ship button again to confirm. \
				An email notifying %s, billing, and MATRR admins of this shipment will be sent." % req_request.user.username)
		if 'confirm_ship' in request.POST:
			if not req_request.can_be_shipped(): # do a sanity check
				messages.warning(request,
								 "A request can only be shipped if all of the following are true:\
													  1) the request has been accepted and not yet shipped, \
													  2) user has submitted a Purchase Order number, \
													  3) User has submitted a valid MTA.\
								 					  4) User has no pending research update requests.")
			else:
				try:
					shipment_status = shipment.ship(request.user)
				except PermissionDenied as pd:
					messages.error(request, str(pd))
				else:
					if shipment_status == ShipmentStatus.Shipped:
						messages.success(request, "Shipment #%d has been shipped." % shipment.pk)
						if settings.PRODUCTION:
							emails.send_po_manifest_upon_shipment(shipment)
							emails.notify_user_upon_shipment(shipment)
					if shipment_status == ShipmentStatus.Genetics:
						messages.success(request, "Shipment #%d has been sent to the DNA processing facility." % shipment.pk)
					req_request.ship_request()
					return redirect(reverse('shipping-overview'))

		if 'delete_shipment' in request.POST:
			if shipment.shp_shipment_status == ShipmentStatus.Genetics:
				messages.warning(request, "You cannot delete a shipment once it has been sent for genetics processing.")
			else:
				messages.warning(request, "Are you sure you want to delete this shipment?  You will have to recreate it before shipping the tissue.")
				confirm_delete_shipment = True
				messages.info(request, "If you are certain you want to delete this shipment, click the delete button again to confirm.")
		if 'confirm_delete_shipment' in request.POST:
			messages.success(request, "Shipment %d deleted." % shipment.pk)
			shipment.delete() # super important that TissueRequest.shipment FK is set to on_delete=SET_NULL
			return redirect(reverse('shipping-overview'))

	return render_to_response('matrr/shipping/shipment_details.html', {'req_request': req_request,
																	   'shipment': shipment,
																	   'tracking_form': tracking_form,
																	   'confirm_ship': confirm_ship,
																	   'confirm_delete_shipment': confirm_delete_shipment,
																	   'edit': edit,
																	   'tracking_number': tracking_number}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipment_manifest_export(request, shipment_id):
	shipment = get_object_or_404(Shipment, pk=shipment_id)
	req_request = shipment.req_request
	response = HttpResponse(mimetype='application/pdf')
	response['Content-Disposition'] = 'attachment; filename=shipment_manifest-' +\
									  str(req_request.user) + '-' +\
									  str(req_request.pk) + '.pdf'

	context = {'shipment': shipment, 'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
	return helper.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=response)


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_delete(request, req_request_id):
	req_request = Request.objects.get(req_request_id=req_request_id)
	#	if req_request.user != request.user:
	#		# tissue requests can only be deleted by the
	#		# user who made the tissue request.
	#		raise Http404('This page does not exist.')

	if req_request.is_evaluated():
		messages.error(request, "You cannot delete an order which has been accepted/rejected.")
		return redirect(reverse('order-list'))
	if req_request.can_be_edited():
		edit = True
	else:
		edit = False

	if request.POST:
		if request.POST['submit'] == 'yes':
			req_request.delete()
			messages.success(request, 'The order was deleted.')
		else:
			messages.info(request, 'The order was not deleted.')
		return redirect(reverse('order-list'))
	else:
		return render_to_response('matrr/order/order_delete.html',
				{'order': req_request,
				 'Acceptance': Acceptance,
				 'edit': edit},
								  context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_checkout(request, req_request_id):
	# get the context (because it loads the cart as well)
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_edited():
		raise Http404('This page does not exist.')

	if request.method != 'POST':
		checkout_form = CartCheckoutForm(instance=req)

		return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form, 'edit': True, 'cart_exists': True, 'cart_num_items': 1},
								  context_instance=RequestContext(request))
	else:
		data = request.POST.copy()
		data['user'] = req.user.id
		data['req_status'] = req.req_status
		data['cohort'] = req.cohort.coh_cohort_id
		checkout_form = CartCheckoutForm(request.POST, request.FILES, instance=req)

		if checkout_form.is_valid() and request.POST['submit'] == 'checkout':
			req.req_experimental_plan = checkout_form.cleaned_data['req_experimental_plan']
			req.req_notes = checkout_form.cleaned_data['req_notes']
			req.submit_request()
			req.req_request_date = datetime.now()
			req.save()
			messages.success(request, 'Tissue Request Submitted.')
			return redirect('order-list')
		else:
			return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form, 'edit': True, 'cart_exists': True, 'cart_num_items': 1},
									  context_instance=RequestContext(request))


def tissue_verification(request):
	request_ids = TissueInventoryVerification.objects.values_list('tissue_request__req_request')
	#	print request_ids
	requests = Request.objects.filter(req_request_id__in=request_ids).order_by('req_request_date')
	#	print requests
	requestless_count = TissueInventoryVerification.objects.filter(tissue_request=None).count()
	return render_to_response('matrr/verification/verification_request_list.html',
			{
			'requests': requests,
			'requestless_count': requestless_count,
			},
							  context_instance=RequestContext(request))


def tissue_verification_export(request, req_request_id):
	if req_request_id:
		tiv_list = TissueInventoryVerification.objects.filter(tissue_request__req_request__req_request_id=req_request_id).order_by('inventory').order_by("monkey")
	else:
		tiv_list = TissueInventoryVerification.objects.filter(tissue_request=None).order_by('inventory').order_by("monkey")

	#Create the HttpResponse object with the appropriate PDF headers.
	response = HttpResponse(mimetype='application/pdf')
	response['Content-Disposition'] = 'attachment; filename=TissueVerificationForm.pdf'
	context = {'tiv_list': tiv_list, 'user': request.user, 'date': datetime.today()}
	return helper.export_template_to_pdf('pdf_templates/tissue_verification.html', context, outfile=response)


def tissue_verification_list(request, req_request_id):
	if int(req_request_id) is 0:
		return tissue_verification_post_shipment(request)

	TissueVerificationFormSet = formset_factory(TissueInventoryVerificationForm, extra=0)
	if request.method == "POST":
		formset = TissueVerificationFormSet(request.POST)
		if formset.is_valid():
			for tivform in formset:
				data = tivform.cleaned_data
				tiv = TissueInventoryVerification.objects.get(pk=data['primarykey'])
				if data['inventory'] != tiv.tiv_inventory:
					tiv.tiv_inventory = data['inventory']
					tiv.save()
			messages.success(request, message="This page of tissues has been successfully updated.")
		else:
			messages.error(request, formset.errors)
	# if request method != post and/or formset isNOT valid
	# build a new formset
	initial = []

	tiv_list = TissueInventoryVerification.objects.filter(tissue_request__req_request__req_request_id=req_request_id).order_by('monkey', 'tissue_type__tst_tissue_name')

	paginator = Paginator(tiv_list, 30)

	page = request.GET.get('page')
	try:
		p_tiv_list = paginator.page(page)
	except EmptyPage:
	# If page is out of range (e.g. 9999), deliver last page of results.
		p_tiv_list = paginator.page(paginator.num_pages)
	except:
	# If page is not an integer, deliver first page.
		p_tiv_list = paginator.page(1)

	for tiv in p_tiv_list.object_list:
		try:
			amount = tiv.tissue_request.get_amount()
			req_request = tiv.tissue_request.req_request\
			if tiv.tissue_request.req_request.get_acc_req_collisions_for_tissuetype_monkey(tiv.tissue_type, tiv.monkey)\
			else False
		except AttributeError: # tissue_request == None
			req_request = False
			amount = "None"
		tss = tiv.tissue_sample
		quantity = -1 if tiv.tissue_request is None else tss.tss_sample_quantity
		tiv_initial = {'primarykey': tiv.tiv_id,
					   'inventory': tiv.tiv_inventory,
					   'monkey': tiv.monkey,
					   'tissue': tiv.tissue_type,
					   'notes': tiv.tiv_notes,
					   'amount': amount,
					   'quantity': quantity,
					   'req_request': req_request, }
		initial.append(tiv_initial)

	formset = TissueVerificationFormSet(initial=initial)
	return render_to_response('matrr/verification/verification_list.html', {"formset": formset, "req_id": req_request_id, "paginator": p_tiv_list}, context_instance=RequestContext(request))


def tissue_verification_post_shipment(request):
	TissueVerificationShippedFormSet = formset_factory(TissueInventoryVerificationShippedForm, extra=0)
	if request.method == "POST":
		formset = TissueVerificationShippedFormSet(request.POST)
		if formset.is_valid():
			for tivform in formset:
				data = tivform.cleaned_data
				tiv = TissueInventoryVerification.objects.get(pk=data['primarykey'])
				tss = tiv.tissue_sample
				if data['units'] != tss.tss_units:
					tss.tss_units = data['units']
					tss.save()
					tiv.tiv_inventory = 'Updated'
				if data['quantity'] >= 0:
					tss.tss_sample_quantity = data['quantity']
					tss.save()
					tiv.tiv_inventory = 'Updated'
				else:
					tiv.tiv_inventory = 'Unverified'
				tiv.save()
			messages.success(request, message="This page of tissues has been successfully updated.")
		else:
			messages.error(request, formset.errors)

	# if request method != post and/or formset isNOT valid
	# build a new formset
	tiv_list = TissueInventoryVerification.objects.filter(tissue_request=None).order_by('monkey', 'tissue_type__tst_tissue_name')

	paginator = Paginator(tiv_list, 30)

	page = request.GET.get('page')
	try:
		p_tiv_list = paginator.page(page)
	except EmptyPage:
	# If page is out of range (e.g. 9999), deliver last page of results.
		p_tiv_list = paginator.page(paginator.num_pages)
	except:
	# If page is not an integer, deliver first page.
		p_tiv_list = paginator.page(1)

	initial = []
	for tiv in p_tiv_list.object_list:
		tss = tiv.tissue_sample
		tiv_initial = {'primarykey': tiv.tiv_id,
					   'monkey': tiv.monkey,
					   'tissue': tiv.tissue_type,
					   'notes': tiv.tiv_notes,
					   'quantity': -1,
					   'units': tss.tss_units,
					   }
		initial.append(tiv_initial)

	formset = TissueVerificationShippedFormSet(initial=initial)
	return render_to_response('matrr/verification/verification_shipped_list.html', {"formset": formset, "req_id": 0, "paginator": p_tiv_list}, context_instance=RequestContext(request))


def tissue_verification_detail(request, req_request_id, tiv_id):
	tiv = TissueInventoryVerification.objects.get(pk=tiv_id)
	if request.method == "POST":
		tivform = TissueInventoryVerificationDetailForm(data=request.POST)
		if tivform.is_valid():
			data = tivform.cleaned_data
			tiv = TissueInventoryVerification.objects.get(pk=tiv_id)
			tss = tiv.tissue_sample
			tss.tss_location = data['location']
			tss.tss_freezer = data['freezer']
			tss.tss_details = data['details']
			tss.user = request.user # who last modified the tissue sample
			if data['quantity']:
				tss.tss_sample_quantity = data['quantity']
			if data['units']:
				tss.tss_units = data['units']
			if data['inventory']:
				tiv.tiv_inventory = data['inventory']
			tiv.save()
			if not 'Do not edit' in tiv.tiv_notes: # see TissueInventoryVerification.save() for details
				tss.save()

			return redirect('/verification/%s' % req_request_id)
		else:
			messages.error(request, tivform.errors)

	# if request method != post and/or formset isNOT valid
	# build a new formset
	try:
		amount = tiv.tissue_request.get_amount()
		req_request = tiv.tissue_request.req_request\
		if tiv.tissue_request.req_request.get_acc_req_collisions_for_tissuetype_monkey(tiv.tissue_type, tiv.monkey)\
		else False
	except AttributeError: # tissue_request == None
		req_request = False
		amount = "None"
	tss = tiv.tissue_sample
	tiv_initial = {'primarykey': tiv.tiv_id,
				   'freezer': tss.tss_freezer,
				   'location': tss.tss_location,
				   'quantity': tss.tss_sample_quantity,
				   'inventory': tiv.tiv_inventory,
				   'units': tss.tss_units,
				   'details': tss.tss_details,
				   'monkey': tiv.monkey,
				   'tissue': tiv.tissue_type,
				   'notes': tiv.tiv_notes,
				   'amount': amount,
				   'req_request': req_request, }
	tivform = TissueInventoryVerificationDetailForm(initial=tiv_initial)
	return render_to_response('matrr/verification/verification_detail.html', {"tivform": tivform, "req_id": req_request_id}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.browse_inventory'), login_url='/denied/')
def inventory_cohort(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	tsts = TissueType.objects.all().order_by('category__cat_name', 'tst_tissue_name')
	monkeys = cohort.monkey_set.all()
	availability_matrix = list()
	#	y tst, x monkey

	if cohort.coh_upcoming:
		messages.warning(request, "This cohort is upcoming, green color indicates future possible availability, however this tissues are NOT is stock.")
		for tst in tsts:
			tst_row = dict()
			tst_row['row'] = list()
			tst_row['title'] = tst.tst_tissue_name
			for mky in monkeys:
				tst_row['row'].append(tst.get_monkey_from_coh_upcoming_availability(mky))
			availability_matrix.append(tst_row)
	else:
		for tst in tsts:
			tst_row = dict()
			tst_row['row'] = list()
			tst_row['title'] = tst.tst_tissue_name
			in_stock_mky_ids = tst.get_directly_in_stock_available_monkey_ids()
			for mky in monkeys:
				if mky.mky_id in in_stock_mky_ids:
					tst_row['row'].append(Availability.In_Stock)
				else:
					tst_row['row'].append(Availability.Unavailable)
			availability_matrix.append(tst_row)
	return render_to_response('matrr/inventory/inventory_cohort.html', {"cohort": cohort, "monkeys": monkeys, "matrix": availability_matrix}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.change_tissuesample'), login_url='/denied/')
def inventory_brain_cohort(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	brains = MonkeyImage.objects.filter(method='__brain_image', monkey__cohort=cohort).distinct()

	cohort.brains = brains.order_by('monkey')
	return render_to_response('matrr/inventory/inventory_brain_cohort.html', {"cohort": cohort}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.change_tissuesample'), login_url='/denied/')
def inventory_brain_monkey(request, mky_id):
	monkey = get_object_or_404(Monkey, pk=mky_id)

	if request.method == 'POST':
		brain_form = InventoryBrainForm(data=request.POST)
		if brain_form.is_valid():
			data = brain_form.cleaned_data
			mbb = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_block_name=data['block'], mbb_hemisphere='L')
			mbb.assign_tissues(data['left_tissues'])
			mbb = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_block_name=data['block'], mbb_hemisphere='R')
			mbb.assign_tissues(data['right_tissues'])
		else:
			messages.error(request, "Invalid form submission")
	else:
		brain_form = InventoryBrainForm()

	blocks = MonkeyBrainBlock.objects.all().values_list('mbb_block_name', flat=True).distinct().count()
	matrix = list()
	show_grid = request.GET.get('show_grid', '0') == '1'
	if show_grid:
		blocks = ['%02d'%i for i in range(1, blocks+1, 1)]
		# Current Matrix:
		for tst in TissueType.objects.filter(category__cat_name__icontains='brain').order_by('tst_tissue_name'):
			tst_row = dict()
			tst_row['row'] = list()
			tst_row['title'] = tst.tst_tissue_name
			for block in blocks:
				brain = list()
				left_hemi = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_hemisphere='L', mbb_block_name__contains=block)
				right_hemi = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_hemisphere='R', mbb_block_name__contains=block)
				brain.append(1 if tst in left_hemi.tissue_types.all() else 0)
				brain.append(1 if tst in right_hemi.tissue_types.all() else 0)
				tst_row['row'].append(brain)
			matrix.append(tst_row)

	image = MonkeyImage.objects.get(monkey=monkey, method='__brain_image') # There can be only 1
	context = {"plot_gallery": True, "monkey": monkey, 'brain_form': brain_form, 'image': image, 'matrix': matrix, 'blocks': blocks, 'show_grid':show_grid}
	return render_to_response('matrr/inventory/inventory_brain_monkey.html', context, context_instance=RequestContext(request))

def rud_update(request):
	if request.method == 'POST':
		form = RudUpdateForm(user=request.user, data=request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			if cd['progress'] == 'CP':
				request.session['rud_form'] = form
				return redirect(reverse('rud-complete'))
			elif cd['progress'] == 'IP':
				request.session['rud_form'] = form
				return redirect(reverse('rud-in-progress'))
			else:
				for req in cd['req_request']:
					rud = ResearchUpdate()
					rud.req_request = req
					rud.rud_progress = cd['progress']
					rud.save()
				messages.info(request, "You will be emailed again in 45 days to provide another research update.")
				return redirect(reverse('account-view'))
	else:
		form = RudUpdateForm(user=request.user)
	return render_to_response('matrr/rud_reports/rud_update.html', {'form': form, }, context_instance=RequestContext(request))

def rud_progress(request):
	progress_form = ''
	update_form = request.session.get('rud_form', '')
	if not update_form:
		messages.error(request, "There was an issue loading the first part of your research update, please start over.  If this continues to happen, please contact a MATRR administrator.")
		return redirect(reverse('rud-upload'))

	update_cd = update_form.cleaned_data
	progress = update_cd['progress']
	if request.method == 'POST':
		post = request.POST.copy()
		post.update({'progress': progress})
		progress_form = RudProgressForm(post, request.FILES)
		if progress_form.is_valid():
			progress_form.clean()
			if not progress_form.errors:
				update_cd = update_form.cleaned_data
				progress_cd = progress_form.cleaned_data
				for req in update_cd['req_request']:
					rud = ResearchUpdate()
					rud.req_request = req
					rud.rud_progress = update_cd['progress']
					rud.rud_pmid = progress_cd['pmid']
					rud.rud_file = File(progress_cd['update_file'])
					rud.rud_comments = progress_cd['comments']
					rud.rud_data_available = progress_cd['data_available']
					rud.rud_grant = progress_cd['grants']
					rud.save()
				messages.success(request, "Your research update was successfully submitted.  Thank you.")
				messages.info(request, "You will be emailed again in 90 days to provide another research update.")
				return redirect(reverse('account-view'))

	form = progress_form if progress_form else RudProgressForm(initial={'progress':update_cd['progress']})
	if progress == ResearchProgress.InProgress:
		template = 'matrr/rud_reports/rud_in_progress.html'
	elif progress == ResearchProgress.Complete:
		template = 'matrr/rud_reports/rud_complete.html'
	else:
		messages.error(request, "There was an issue determining the progress of your research update, please start over.  If this continues to happen, please contact a MATRR administrator.")
		return redirect(reverse('rud-upload'))
	return render_to_response(template, {'form': form, }, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_rud_detail'), login_url='/denied/')
def rud_detail(request, rud_id):
	rud = get_object_or_404(ResearchUpdate, pk=rud_id)
	return render_to_response('matrr/rud_reports/rud_detail.html', {'rud': rud}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_rud_detail'), login_url='/denied/')
def research_update_list(request):
	pending_ruds = ResearchUpdate.objects.all().order_by('req_request', 'rud_date')
	paginator = Paginator(pending_ruds, 20)

	if request.GET and 'page' in request.GET:
		page = request.GET.get('page')
	else:
		page = 1
	try:
		rud_list = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		rud_list = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		rud_list = paginator.page(paginator.num_pages)
	return render_to_response('matrr/rud_reports/rud_list.html', {'rud_list': rud_list}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_rud_detail'), login_url='/denied/')
def research_update_overdue(request):
	pending_ruds = Request.objects.shipped().filter(rud_set=None).order_by('-req_report_asked_count', 'req_request_date')
	paginator = Paginator(pending_ruds, 20)

	if request.GET and 'page' in request.GET:
		page = request.GET.get('page')
	else:
		page = 1
	try:
		req_list = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		req_list = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		req_list = paginator.page(paginator.num_pages)
	return render_to_response('matrr/rud_reports/req_list.html', {'req_list': req_list}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff, login_url='/denied/')
def rna_landing(request):
	if request.method == "POST":
		cohort_form = RNALandingForm(data=request.POST)
		if cohort_form.is_valid():
			cohort = cohort_form.cleaned_data['subject']
			yields = cohort_form.cleaned_data['yields']
			if yields == 'submit':
				return redirect('rna-submit', cohort.pk)
			else:
				return redirect('rna-display', cohort.pk)
		else:
			messages.error(request, "Form submission was invalid.  Please try again.")
	else:
		cohort_form = RNALandingForm()
	return render_to_response('matrr/rna/landing.html', {'cohort_form': cohort_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.rna_submit'), login_url='/denied/')
def rna_submit(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	if request.method == "POST":
		rna_form = RNASubmitForm(cohort, data=request.POST)
		rna = rna_form.instance
		if rna_form.is_valid():
			rna.cohort = cohort
			rna.user = request.user
			rna.full_clean()
			rna.save()
			messages.success(request, "RNA yield data saved.")
		else:
			messages.error(request, "Form submission was invalid.  Please try again.")
	else:
		rna_form = RNASubmitForm(cohort)
	return render_to_response('matrr/rna/submit.html', {'rna_form': rna_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.rna_display'), login_url='/denied/')
def rna_display(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	rna_records = RNARecord.objects.filter(cohort=cohort)
	## Paginator stuff
	if rna_records.count() > 0:
		paginator = Paginator(rna_records, 25)
		# Make sure page request is an int. If not, deliver first page.
		try:
			page = int(request.GET.get('page', '1'))
		except ValueError:
			page = 1
		# If page request (9999) is out of range, deliver last page of results.
		try:
			rna_list = paginator.page(page)
		except (EmptyPage, InvalidPage):
			rna_list = paginator.page(paginator.num_pages)
	else:
		rna_list = rna_records
	return render_to_response('matrr/rna/display.html', {'rna_list': rna_list, 'cohort': cohort}, context_instance=RequestContext(request))

### Tools
def __gather_cohort_protein_images(cohort, proteins):
	images = []
	for protein in proteins:
		pcimage, isnew = CohortProteinImage.objects.get_or_create(protein=protein, cohort=cohort)
		if isnew:
			pcimage.save()
		images.append(pcimage)
	return images

def tools_landing(request):
	cohort_methods = plotting.COHORT_TOOLS_PLOTS.keys()
	monkey_methods = plotting.MONKEY_TOOLS_PLOTS.keys()

	if request.method == 'POST':
		_method = request.POST.get('cohort_method', '')
		if _method:
			if _method in plotting.COHORT_BEC_TOOLS_PLOTS.keys():
				return redirect('tools-cohort-bec-graphs', _method)
			elif _method in plotting.COHORT_ETOH_TOOLS_PLOTS.keys():
				return redirect('tools-cohort-etoh-graphs', _method)
			else:
				raise Http404("There is no '%s' method in the MATRR BEC or ETOH toolboxs." % _method)
		_method = request.POST.get('monkey_method', '')
		if _method:
			if _method in plotting.MONKEY_BEC_TOOLS_PLOTS.keys():
				return redirect('tools-monkey-bec', _method)
			elif _method in plotting.MONKEY_ETOH_TOOLS_PLOTS.keys():
				return redirect('tools-monkey-etoh', _method)
			else:
				raise Http404("There is no '%s' method in the MATRR BEC or ETOH toolboxs." % _method)


	coh_images = list()
	for method in cohort_methods:
		try:
			coh_images.append(CohortImage.objects.filter(canonical=True, method=method)[0])
		except:
			pass
	mky_images = list()
	for method in monkey_methods:
		try:
			mky_images.append(MonkeyImage.objects.filter(canonical=True, method=method)[0])
		except IndexError:
			# no images to show.  ignore.
			pass
	return render_to_response('matrr/tools/landing.html', {'mky_images': mky_images, 'coh_images': coh_images}, context_instance=RequestContext(request))

def __tools_landing(request): # deprecated
	if request.method == "POST":
		dataset = request.POST.get('dataset')
		if dataset == 'etoh':
			return redirect('tools-etoh')
		elif dataset == 'protein':
			return redirect('tools-protein')
		elif dataset == 'bec':
			return redirect('tools-bec')
		else:
			messages.error(request, "Form submission was invalid.  Please try again.")
	return render_to_response('matrr/tools/landing.html', {}, context_instance=RequestContext(request))

def tools_protein(request): # pick a cohort
	if request.method == 'POST':
		cohort_form = CohortSelectForm(data=request.POST)
		if cohort_form.is_valid():
			cohort = cohort_form.cleaned_data['subject']
			return redirect('tools-cohort-protein', cohort.pk)
	else:
		cohorts_with_protein_data = MonkeyProtein.objects.all().values_list('monkey__cohort', flat=True).distinct() # for some reason this only returns the pk int
		cohorts_with_protein_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_protein_data) # so get the queryset of cohorts
		cohort_form = CohortSelectForm(subject_queryset=cohorts_with_protein_data)
	return render_to_response('matrr/tools/protein.html', {'subject_select_form': cohort_form}, context_instance=RequestContext(request))

def tools_cohort_protein(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	monkey_keys = MonkeyProtein.objects.filter(monkey__cohort=cohort).values_list('monkey', flat=True).distinct()
	monkey_queryset = Monkey.objects.filter(pk__in=monkey_keys)

	if request.method == 'POST':
		subject_select_form = ProteinGraphSubjectSelectForm(monkey_queryset, data=request.POST)
		if subject_select_form.is_valid():
			subject = subject_select_form.cleaned_data['subject']
			if subject == 'monkey':
				monkeys = subject_select_form.cleaned_data['monkeys']
				get_m = list()
				for m in monkeys:
					get_m.append(`m.mky_id`)
				get_m = "-".join(get_m)
				if not monkeys:
					messages.error(request, "You have to select at least one monkey.")
					return render_to_response('matrr/tools/protein.html', {'subject_select_form': subject_select_form}, context_instance=RequestContext(request))

				return redirect_with_get('tools-monkey-protein', coh_id, monkeys=get_m)
			elif subject == 'cohort':
				return redirect('tools-cohort-protein-graphs', coh_id)
			else: # assumes subject == 'download'
				account = request.user.account
				if account.has_mta():
					monkey_proteins = MonkeyProtein.objects.filter(monkey__in=cohort.monkey_set.all())

					datafile, isnew = DataFile.objects.get_or_create(account=account, dat_title="%s Protein data" % str(cohort))
					if isnew:
						from utils.database import dump_monkey_protein_data

						f = dump_monkey_protein_data(monkey_proteins, '/tmp/%s.csv' % str(datafile))

						datafile.dat_data_file = File(open('/tmp/%s.csv' % str(datafile), 'r'))
						datafile.save()
						messages.info(request, "Your data file has been saved and is available for download on your account page.")
					else:
						messages.warning(request, "This data file has already been created for you.  It is available to download on your account page.")
				else:
					messages.warning(request, "You must have a valid MTA on record to download data.  MTA information can be updated on your account page.")
	return render_to_response('matrr/tools/protein.html', {'subject_select_form': ProteinGraphSubjectSelectForm(monkey_queryset)}, context_instance=RequestContext(request))

def _verify_monkeys(text_monkeys):
	monkey_keys = text_monkeys.split('-')
	query_keys = list()
	if len(monkey_keys) > 0:
		for mk in monkey_keys:
			query_keys.append(int(mk))
		return Monkey.objects.filter(mky_id__in=query_keys)
	else:
		return list()

def tools_cohort_protein_graphs(request, coh_id):
	proteins = None
	old_post = request.session.get('_old_post')
	cohort = Cohort.objects.get(pk=coh_id)
	context = {'cohort': cohort}
	if request.method == "POST" or old_post:
		post = request.POST if request.POST else old_post
		protein_form = ProteinSelectForm(data=post)
		subject_select_form = CohortSelectForm(data=post)
		if protein_form.is_valid() and subject_select_form.is_valid():
			if int(coh_id) != subject_select_form.cleaned_data['subject'].pk:
				request.session['_old_post'] = request.POST
				return redirect(tools_cohort_protein_graphs, subject_select_form.cleaned_data['subject'].pk)
			proteins = protein_form.cleaned_data['proteins']
			graphs = __gather_cohort_protein_images(cohort, proteins)
			context['graphs'] = graphs

	cohorts_with_protein_data = MonkeyProtein.objects.all().values_list('monkey__cohort', flat=True).distinct() # for some reason this only returns the pk int
	cohorts_with_protein_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_protein_data) # so get the queryset of cohorts

	context['subject_select_form'] = CohortSelectForm(subject_queryset=cohorts_with_protein_data, horizontal=True, initial={'subject': coh_id})
	context['protein_form'] = ProteinSelectForm(initial={'proteins': proteins})
	return render_to_response('matrr/tools/protein_cohort.html', context, context_instance=RequestContext(request))

def tools_monkey_protein_graphs(request, coh_id, mky_id=None):
	proteins = None
	#	old_post = request.session.get('_old_post')
	#	monkey = Monkey.objects.get(pk=mky_id) if mky_id else None
	cohort = get_object_or_404(Cohort, pk=coh_id)

	context = {'cohort': cohort}

	if request.method == 'GET' and 'monkeys' in request.GET and request.method != 'POST':
		try:
			monkeys = _verify_monkeys(request.GET['monkeys'])
		except ValueError:
			monkeys = _verify_monkeys(mky_id)
		get_m = list()
		if monkeys:
			for m in monkeys.values_list('mky_id', flat=True):
				get_m.append(`m`)

			text_monkeys = "-".join(get_m)
		else:
			text_monkeys = ""
		context['graph_form'] = MonkeyProteinGraphAppearanceForm(text_monkeys)
		context['protein_form'] = ProteinSelectForm()

	elif request.method == 'POST':
	#		post = request.POST if request.POST else old_post
		protein_form = ProteinSelectForm(data=request.POST)
		graph_form = MonkeyProteinGraphAppearanceForm(data=request.POST)

		if protein_form.is_valid() and graph_form.is_valid():
			try:
				monkeys = _verify_monkeys(graph_form.cleaned_data['monkeys'])
			except ValueError:
				monkeys = _verify_monkeys(mky_id)
			yaxis = graph_form.cleaned_data['yaxis_units']
			data_filter = graph_form.cleaned_data['data_filter']
			proteins = protein_form.cleaned_data['proteins']
			graphs = list()
			if data_filter == "morning":
				afternoon_reading = False
			elif data_filter == 'afternoon':
				afternoon_reading = True
			else:
				afternoon_reading = None
			mpi = ''
			if yaxis != 'monkey_protein_value':
				for mon in monkeys:
					mpis = MonkeyProteinImage.objects.filter(monkey=mon,
															 method=yaxis,
															 #						 proteins = proteins,
															 parameters=`{'afternoon_reading': afternoon_reading}`)
					mpis = mpis.annotate(count=Count("proteins")).filter(count=len(proteins))
					for protein in proteins:
						mpis = mpis.filter(proteins=protein)

					if len(mpis) == 0:
						mpi = MonkeyProteinImage(monkey=mon,
												 method=yaxis,
												 parameters=str({'afternoon_reading': afternoon_reading})
						)
						mpi.save()
						mpi.proteins.add(*proteins)
						mpi.save()
					if len(mpis) > 0:
						mpi = mpis[0]
					graphs.append(mpi)
			else:
				for protein in proteins:
					for mon in monkeys:
						mpis = MonkeyProteinImage.objects.filter(monkey=mon,
																 method=yaxis,
																 proteins__in=[protein, ],
																 parameters=`{'afternoon_reading': afternoon_reading}`)
						if mpis.count() == 0:
							mpi = MonkeyProteinImage(monkey=mon,
													 method=yaxis,
													 parameters=`{'afternoon_reading': afternoon_reading}`)
							mpi.save()
							mpi.proteins.add(protein)
							mpi.save()
						if mpis.count() > 0:
							mpi = mpis[0]

						graphs.append(mpi)
			context['graphs'] = graphs
		else:
			if 'proteins' not in protein_form.data:
				messages.error(request, "You have to select at least one protein.")

			if len(graph_form.errors) + len(protein_form.errors) > 1:
				raise Http404()
			monkeys = protein_form.data['monkeys']

		context['monkeys'] = monkeys
		context['graph_form'] = graph_form
		context['protein_form'] = protein_form

	else:
		# function lands here when directed to protein tools from monkey detail page
		get_m = list()
		if mky_id:
			get_m.append(`mky_id`)
			text_monkeys = "-".join(get_m)
		else:
			text_monkeys = ""
		context['graph_form'] = MonkeyProteinGraphAppearanceForm(text_monkeys)
		context['protein_form'] = ProteinSelectForm()

	return render_to_response('matrr/tools/protein_monkey.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_etoh_mtd(request, mtd_id):
	mtd_image = ''
	if MonkeyToDrinkingExperiment.objects.filter(pk=mtd_id).count():
		mtd = MonkeyToDrinkingExperiment.objects.get(pk=mtd_id)
		mtd_image, is_new = MTDImage.objects.get_or_create(
			monkey_to_drinking_experiment=mtd,
			method='monkey_etoh_bouts_drinks_intraday',
			title="Drinks on %s for monkey %s" % (str(mtd.drinking_experiment.dex_date), str(mtd.monkey))
		)
	return render_to_response('matrr/tools/graph_generic.html', {'matrr_image': mtd_image}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_cohort_etoh_graphs(request, cohort_method):
	context = dict()
	subject_initial = dict()
	range_initial = dict()
	if request.method == "POST":
		subject_select_form = CohortSelectForm(data=request.POST)
		experiment_range_form = ExperimentRangeForm(data=request.POST)
		if subject_select_form.is_valid() and experiment_range_form.is_valid():
			subject_initial = subject_select_form.cleaned_data
			range_initial = experiment_range_form.cleaned_data
			cohort = subject_select_form.cleaned_data['subject']

			from_date = ''
			to_date = ''
			experiment_range = experiment_range_form.cleaned_data['range']
			if experiment_range == 'custom':
				from_date = str(experiment_range_form.cleaned_data['from_date'])
				to_date = str(experiment_range_form.cleaned_data['to_date'])
				experiment_range = None

			params = str({'dex_type': experiment_range, 'from_date': from_date, 'to_date': to_date})
			cohort_image, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=cohort_method, title=plotting.COHORT_PLOTS[cohort_method][1], parameters=params)

			if is_new and not cohort_image.pk:
				messages.error(request, 'Image file not created.  This is usually caused by requesting insufficient or non-existant data.')
			else:
				context['graph'] = cohort_image
		else:
			messages.error(request, subject_select_form.errors.as_text())
			messages.error(request, experiment_range_form.errors.as_text())
	cohorts_with_ethanol_data = MonkeyToDrinkingExperiment.objects.all().values_list('monkey__cohort', flat=True).distinct() # this only returns the pk int
	cohorts_with_ethanol_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_ethanol_data) # so get the queryset of cohorts

	context['cohorts'] = cohorts_with_ethanol_data
	context['subject_select_form'] = CohortSelectForm(subject_queryset=cohorts_with_ethanol_data, horizontal=True, initial=subject_initial)
	context['experiment_range_form'] = ExperimentRangeForm(initial=range_initial)
	return render_to_response('matrr/tools/ethanol_cohort.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_monkey_etoh(request, monkey_method): # pick a cohort
	if request.method == 'POST':
		cohort_form = CohortSelectForm(data=request.POST)
		if cohort_form.is_valid():
			cohort = cohort_form.cleaned_data['subject']
			return redirect('tools-monkey-etoh-graphs', monkey_method, cohort.pk)
	else:
		cohorts_with_etoh_data = MonkeyToDrinkingExperiment.objects.all().values_list('monkey__cohort', flat=True).distinct() # this only returns the pk int
		cohorts_with_etoh_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_etoh_data) # so get the queryset of cohorts
		cohort_form = CohortSelectForm(subject_queryset=cohorts_with_etoh_data)
	return render_to_response('matrr/tools/ethanol.html', {'subject_select_form': cohort_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_monkey_etoh_graphs(request, monkey_method, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	drinking_monkeys = cohort.monkey_set.filter(mky_drinking=True)
	context = {'cohort': cohort}

	if request.method == 'POST':
		monkey_select_form = GraphToolsMonkeySelectForm(drinking_monkeys, data=request.POST)
		experiment_range_form = ExperimentRangeForm(data=request.POST)
		if experiment_range_form.is_valid() and monkey_select_form.is_valid():
			from_date = to_date = ''
			experiment_range = experiment_range_form.cleaned_data['range']
			if experiment_range == 'custom':
				from_date = str(experiment_range_form.cleaned_data['from_date'])
				to_date = str(experiment_range_form.cleaned_data['to_date'])
				experiment_range = None

			monkeys = monkey_select_form.cleaned_data['monkeys']
			title = plotting.MONKEY_PLOTS[monkey_method][1]
			params = {'from_date': str(from_date), 'to_date': str(to_date), 'dex_type': experiment_range}
			graphs = list()
			for monkey in monkeys:
				mig, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, title=title, method=monkey_method, parameters=str(params))
				if mig.pk:
					graphs.append(mig)
			if not graphs:
				messages.info(request, "No graphs could be made with these settings.")
			else:
				context['graphs'] = graphs

		context['monkey_select_form'] = monkey_select_form
		context['experiment_range_form'] = experiment_range_form
	else:
		context['monkey_select_form'] = GraphToolsMonkeySelectForm(drinking_monkeys)
		context['experiment_range_form'] = ExperimentRangeForm()

	return render_to_response('matrr/tools/ethanol_monkey.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_bec_data'), login_url='/denied/')
def tools_cohort_bec_graphs(request, cohort_method):
	context = dict()
	subject_initial = dict()
	range_initial = dict()
	if request.method == "POST":
		subject_select_form = CohortSelectForm(data=request.POST)
		experiment_range_form = BECRangeForm(data=request.POST)
		if subject_select_form.is_valid() and experiment_range_form.is_valid():
			subject_initial = subject_select_form.cleaned_data
			range_initial = experiment_range_form.cleaned_data
			cohort = subject_select_form.cleaned_data['subject']

			from_date = ''
			to_date = ''
			experiment_range = experiment_range_form.cleaned_data['range']
			if experiment_range == 'custom':
				from_date = str(experiment_range_form.cleaned_data['from_date'])
				to_date = str(experiment_range_form.cleaned_data['to_date'])
				experiment_range = None

			sample_before = ''
			sample_after = ''
			sample_range = experiment_range_form.cleaned_data['sample_range']
			if sample_range == 'morning':
				sample_before = '14:00'
			if sample_range == 'afternoon':
				sample_after = '14:00'

			params = str({'dex_type': experiment_range, 'from_date': from_date, 'to_date': to_date, 'sample_before': sample_before, 'sample_after': sample_after})
			cohort_image, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=cohort_method, title=plotting.COHORT_PLOTS[cohort_method][1], parameters=params)
			if is_new and not cohort_image.pk:
				messages.error(request, 'Image file not created.  This is usually caused by requesting insufficient or non-existant data.')
			else:
				context['graph'] = cohort_image
		else:
			messages.error(request, subject_select_form.errors.as_text())
			messages.error(request, experiment_range_form.errors.as_text())
	cohorts_with_bec_data = MonkeyBEC.objects.all().values_list('monkey__cohort', flat=True).distinct() # this only returns the pk int
	cohorts_with_bec_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_bec_data) # so get the queryset of cohorts

	context['cohorts'] = cohorts_with_bec_data
	context['subject_select_form'] = CohortSelectForm(subject_queryset=cohorts_with_bec_data, horizontal=True, initial=subject_initial)
	context['experiment_range_form'] = BECRangeForm(initial=range_initial)
	return render_to_response('matrr/tools/bec_cohort.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_bec_data'), login_url='/denied/')
def tools_monkey_bec(request, monkey_method): # pick a cohort
	if request.method == 'POST':
		cohort_form = CohortSelectForm(data=request.POST)
		if cohort_form.is_valid():
			cohort = cohort_form.cleaned_data['subject']
			return redirect('tools-monkey-bec-graphs', monkey_method, cohort.pk)
	else:
		cohorts_with_bec_data = MonkeyBEC.objects.all().values_list('monkey__cohort', flat=True).distinct() # this only returns the pk int
		cohorts_with_bec_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_bec_data) # so get the queryset of cohorts
		cohort_form = CohortSelectForm(subject_queryset=cohorts_with_bec_data)
	return render_to_response('matrr/tools/bec.html', {'subject_select_form': cohort_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_bec_data'), login_url='/denied/')
def tools_monkey_bec_graphs(request, monkey_method, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	drinking_monkeys = cohort.monkey_set.filter(mky_drinking=True)
	context = {'cohort': cohort}

	if request.method == 'POST':
		monkey_select_form = GraphToolsMonkeySelectForm(drinking_monkeys, data=request.POST)
		experiment_range_form = BECRangeForm(data=request.POST)
		if experiment_range_form.is_valid() and monkey_select_form.is_valid():
			from_date = to_date = ''
			experiment_range = experiment_range_form.cleaned_data['range']
			if experiment_range == 'custom':
				from_date = str(experiment_range_form.cleaned_data['from_date'])
				to_date = str(experiment_range_form.cleaned_data['to_date'])
				experiment_range = None

			sample_before = sample_after = ''
			sample_range = experiment_range_form.cleaned_data['sample_range']
			if sample_range == 'morning':
				sample_before = '14:00'
			if sample_range == 'afternoon':
				sample_after = '14:00'

			monkeys = monkey_select_form.cleaned_data['monkeys']
			title = plotting.MONKEY_PLOTS[monkey_method][1]
			params = {'from_date': str(from_date), 'to_date': str(to_date), 'dex_type': experiment_range}
			graphs = list()
			for monkey in monkeys:
				mig, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, title=title, method=monkey_method, parameters=str(params))
				if mig.pk:
					graphs.append(mig)
			if not graphs:
				messages.info(request, "No graphs could be made with these settings.")
			else:
				context['graphs'] = graphs

		context['monkey_select_form'] = monkey_select_form
		context['experiment_range_form'] = experiment_range_form
	else:
		context['monkey_select_form'] = GraphToolsMonkeySelectForm(drinking_monkeys)
		context['experiment_range_form'] = BECRangeForm()

	return render_to_response('matrr/tools/bec_monkey.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.genealogy_tools'), login_url='/denied/')
def tools_genealogy(request):
	if request.method == 'POST':
		cohort_form = CohortSelectForm(data=request.POST)
		if cohort_form.is_valid():
			return HttpResponseRedirect(reverse('tools-cohort-genealogy', args=[cohort_form.cleaned_data['subject'].pk]))
		else:
			messages.error(request, "Invalid form submission")
	return render_to_response('matrr/tools/genealogy/subject_select.html', {'subject_select_form': CohortSelectForm()}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.access_genealogy_tools'), login_url='/denied/')
def tools_cohort_genealogy(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	cohort_monkeys = cohort.monkey_set.all()

	if request.method == 'POST':
		genealogy_form = GenealogyParentsForm(subject_queryset=cohort_monkeys, data=request.POST)
		if genealogy_form.is_valid():
			me = FamilyNode.objects.get(monkey=genealogy_form.cleaned_data['subject'])
			dad = FamilyNode.objects.get(monkey=genealogy_form.cleaned_data['father'])
			mom = FamilyNode.objects.get(monkey=genealogy_form.cleaned_data['mother'])

			me.sire = dad
			me.dam = mom
			me.save()

			messages.success(request, "Parentage for monkey %d saved." % me.monkey.pk)
			return redirect(reverse('tools-cohort-genealogy', args=[coh_id]))
		else:
			messages.error(request, "Invalid form submission")

	context = dict()
	context['genealogy_form'] = GenealogyParentsForm(subject_queryset=cohort_monkeys)
	return render_to_response('matrr/tools/genealogy/parent_select.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff, login_url='/denied/')
def tools_sandbox(request):
	append = request.GET.get('append', "christa")
	base = settings.STATIC_ROOT + '/images/%s/' % append
	_files = os.listdir(base)
	files = list()
	for f in _files:
		if not os.path.isdir(base+f):
			files.append(f)
	files = sorted(files)
	return render_to_response('matrr/tools/sandbox.html', {'files':files, 'append':append}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser, login_url='/denied/')
def tools_supersandbox(request):
	plot = request.GET.get('plot', '')
	if plot == 'adjacency':
		return _tools_supersandbox_adjacency(request)
	elif plot == 'chord':
		return _tools_supersandbox_chord(request)
	else:
		return render_to_response('matrr/tools/supersandbox.html', {}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser, login_url='/denied/')
def _tools_supersandbox_chord(request):
#	https://github.com/mbostock/d3/wiki/Gallery
	min_conf = request.GET.get('min_conf', 0)
	try:
		min_conf = float(min_conf)
	except ValueError:
		messages.error(request, "ValueError you big dummy.  Enter a number, 1 > x > 0.")
		min_conf = 0
	if not 1 > min_conf >= 0:
		messages.error(request, "Enter a number, 1 > x > 0, nerd.")
		min_conf = 0

	def reformat_apriori_output_1to1(cohort=None):
		cohorts = [cohort] if cohort else [5,6,9,10]
		drinkers = Monkey.objects.Drinkers().filter(cohort__in=cohorts)
		drinkers = drinkers.values_list('pk', flat=True)
		matrix = numpy.zeros((drinkers.count(), drinkers.count()))

		indices = dict()
		for index, monkey_pk in enumerate(drinkers):
			indices[monkey_pk] = index

		for cohort_pk in cohorts:
			orig = apriori.get_confederate_groups(cohort_pk, minutes=15, min_confidence=min_conf)
			for support, occurrences in orig.iteritems():
				for cause, effect, confidence in occurrences:
					if len(cause) > 1 or len(effect) > 1:
						continue
					cause = tuple(cause)[0]
					effect = tuple(effect)[0]
					matrix[indices[cause], indices[effect]] = float(support)*float(confidence)
		list_matrix = list()
		for row in matrix:
			list_matrix.append(list(row))
		return list_matrix, drinkers

	def reformat_apriori_output_NtoN(cohort=None):
		cohorts = [cohort] if cohort else [5,6,9,10]
		drinkers = Monkey.objects.Drinkers().filter(cohort__in=cohorts)
		drinkers = drinkers.values_list('pk', flat=True)
		matrix = numpy.zeros((drinkers.count(), drinkers.count()))

		indices = dict()
		for index, monkey_pk in enumerate(drinkers):
			indices[monkey_pk] = index

		for cohort_pk in cohorts:
			orig = apriori.get_confederate_groups(cohort_pk, minutes=15, min_confidence=min_conf)
			for support, occurrences in orig.iteritems():
				for cause_monkeys, effect_monkeys, confidence in occurrences:
					cause_value = float(support) * float(confidence) / len(cause_monkeys) / len(effect_monkeys)
					for _cause in cause_monkeys:
						for _effect in effect_monkeys:
							matrix[indices[_cause], indices[_effect]] += cause_value
		list_matrix = list()
		for row in matrix:
			list_matrix.append(list(row))
		return list_matrix, drinkers

	NtoN = request.GET.get('NtoN', False)
	reformat_method = reformat_apriori_output_NtoN if NtoN else reformat_apriori_output_1to1

	chord_data = list()
	from matplotlib.colors import rgb2hex
	for coh in [5,6,9,10]:
		matrix, labels = reformat_method(coh)
		labels_colors = list()
		cmap = plotting.get_cmap('jet')
		for idx, key in enumerate(labels):
			lc = {'name': key, 'color': rgb2hex(cmap(idx / (len(labels)-1.)))}
			labels_colors.append(lc)
		dataset = mark_safe(json.dumps(matrix))
		labels_colors = mark_safe(json.dumps(labels_colors))
		cohort = Cohort.objects.get(pk=coh)
		data = {'dataset': dataset, 'labels_colors': labels_colors, 'cohort': cohort}
		chord_data.append(data)
	return render_to_response('matrr/tools/supersandbox.html', {'chord_data': chord_data}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser, login_url='/denied/')
def _tools_supersandbox_adjacency(request):
	""" http://bost.ocks.org/mike/miserables/ """
	cohort = Cohort.objects.get(pk=10)
	dataset = []
	network_data = {'cohort': cohort, 'dataset': dataset}

	return render_to_response('matrr/tools/supersandbox.html', {'network_data': network_data}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser, login_url='/denied/')
def tools_sandbox_familytree(request):
	from matrr.helper import FamilyTree, ExampleFamilyTree
	def male_female_shape(node):
		shape = 'circle' if node[1]['shape_input'] == 'F' else 'square'
		return shape

	me = FamilyNode.objects.exclude(sire=None, dam=None)[0]
	tree = ExampleFamilyTree(me)

	tree.visual_style.discrete_node_shapes(shape_method=male_female_shape)
	tree.visual_style.continuous_node_colors('color_input', min_value='blue', max_value='orange')
	tree.visual_style.passthru_node_borderColors('borderColor_color')
	tree.visual_style.discrete_node_borderWidth()

	tree.visual_style.passthru_edge_colors()
	tree.visual_style.passthru_edge_width()

	draw_options = dict()
	draw_options['network'] = tree.dump_graphml()
	draw_options['visualStyle'] = tree.visual_style.get_visual_style()
	draw_options = mark_safe(str(draw_options))
	return render_to_response('matrr/tools/sandbox_familytree.html', {'monkey': me.monkey, 'draw_options': draw_options}, context_instance=RequestContext(request))

### End tools

# Permission-restricted media file hosting
from settings import MEDIA_ROOT
import os
import mimetypes
def sendfile(request, id):
	files = list()

	#	append all possible files
	r = Request.objects.filter(req_experimental_plan=id)
	files.append((r, 'req_experimental_plan'))
	r = Mta.objects.filter(mta_file=id)
	files.append((r, 'mta_file'))
	r = ResearchUpdate.objects.filter(rud_file=id)
	files.append((r, 'rud_file'))
	r = CohortData.objects.filter(cod_file=id)
	files.append((r, 'cod_file'))
	r = MonkeyImage.objects.filter(thumbnail=id)
	files.append((r, 'thumbnail'))
	r = MonkeyImage.objects.filter(svg_image=id)
#	files.append((r, 'svg_image'))
	r = MonkeyImage.objects.filter(image=id)
	files.append((r, 'image'))
	r = MonkeyImage.objects.filter(html_fragment=id)
	files.append((r, 'html_fragment'))
	r = CohortImage.objects.filter(thumbnail=id)
	files.append((r, 'thumbnail'))
	r = CohortImage.objects.filter(image=id)
	files.append((r, 'image'))
	r = CohortImage.objects.filter(html_fragment=id)
	files.append((r, 'html_fragment'))
	r = CohortImage.objects.filter(svg_image=id)
#	files.append((r, 'svg_image'))
	r = MTDImage.objects.filter(thumbnail=id)
	files.append((r, 'thumbnail'))
	r = MTDImage.objects.filter(image=id)
	files.append((r, 'image'))
	r = MTDImage.objects.filter(html_fragment=id)
	files.append((r, 'html_fragment'))
	r = MTDImage.objects.filter(svg_image=id)
#	files.append((r, 'svg_image'))
	r = DataFile.objects.filter(dat_data_file=id)
	files.append((r, 'dat_data_file'))
	r = CohortProteinImage.objects.filter(image=id)
	files.append((r, 'image'))
	r = CohortProteinImage.objects.filter(thumbnail=id)
	files.append((r, 'thumbnail'))
	r = CohortProteinImage.objects.filter(svg_image=id)
#	files.append((r, 'svg_image'))
	r = MonkeyProteinImage.objects.filter(image=id)
	files.append((r, 'image'))
	r = MonkeyProteinImage.objects.filter(thumbnail=id)
	files.append((r, 'thumbnail'))
	r = MonkeyProteinImage.objects.filter(svg_image=id)
#	files.append((r, 'svg_image'))

	#	this will work for all listed files
	file = None
	for r, f in files:
		if len(r) > 0:
			if r[0].verify_user_access_to_file(request.user):
				file = getattr(r[0], f)
			break
	if not file:
		raise Http404()

	if file.url.count('/media') > 0:
		file_url = file.url.replace('/media/', '')
	else:
		file_url = file.url.replace('/', '', 1)

	response = HttpResponse()
	response['X-Sendfile'] = os.path.join(MEDIA_ROOT, file_url)

	content_type, encoding = mimetypes.guess_type(file_url)
	if not content_type:
		content_type = 'application/octet-stream'
	response['Content-Type'] = content_type
	response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_url)
	return response

@user_passes_test(lambda u: u.has_perm('auth.upload_raw_data'), login_url='/denied/')
def raw_data_upload(request):
	if request.method == 'POST':
		form = RawDataUploadForm(request.POST, request.FILES)
		if form.is_valid():
			f = request.FILES['data']
			name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "." + f.name
			upload_path = os.path.join(settings.UPLOAD_DIR, name)
			destination = open(upload_path, 'wb+')
			for chunk in f.chunks():
				destination.write(chunk)
			destination.close()
			return render_to_response('upload_forms/raw_data_upload.html', {'form': RawDataUploadForm(), 'success': True}, context_instance=RequestContext(request))
	else:
		form = RawDataUploadForm()
	return render_to_response('upload_forms/raw_data_upload.html', {'form': form}, context_instance=RequestContext(request))

import cStringIO as StringIO
import ho.pisa as pisa
def create_pdf_fragment(request):
	if request.method == 'GET':
		fragment_filename = request.GET['html']
		htmlfile = os.path.join('matrr_images/fragments/',fragment_filename)

#		this is ugly, but we do not have to repeat code
#		if user does not have permissions, send file will raise Http404()
#		so this is all just about permission check
		sendfile(request, htmlfile)


		htmlfile = os.path.join(settings.MEDIA_ROOT,htmlfile)
		try:
			with open(htmlfile, 'r') as f:
				html = f.read()
		except:
			raise Http404()
		result = StringIO.StringIO()

		pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=result, link_callback=_fetch_resources,
							 )
		if not pdf.err:

			resp =  HttpResponse(result.getvalue(), mimetype='application/pdf')
			resp['Content-Disposition'] = 'attachment; filename=%s' % fragment_filename.replace("html", "pdf")
			return resp
		raise Http404()
	else:
		raise Http404()

def _fetch_resources(uri, rel):

	if uri.startswith(settings.MEDIA_URL):
		path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
	elif uri.startswith(settings.STATIC_URL):
		path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))

	return path

import matrr.models as mmodels
def create_svg_fragment(request, klass, imageID):
	im = get_object_or_404(getattr(mmodels, klass), pk=imageID)
	if not isinstance(im, MATRRImage):
		raise Http404()
	if not im.verify_user_access_to_file(request.user):
		raise Http404()
	image_data = open(os.path.join(settings.MEDIA_ROOT, im.svg_image.name), "rb").read()
	resp = HttpResponse(image_data, mimetype="image/svg+xml")
	resp['Content-Disposition'] = 'attachment; filename=%s' % (str(im) + '.svg')
	return resp

import simplejson
@user_passes_test(lambda u: u.is_authenticated(), login_url='/denied/')
def ajax_advanced_search(request):
	show_ids = ['blank']
	hide_ids = ['blank']
	if request.POST:
		select_form = AdvancedSearchSelectForm(data=request.POST, prefix='select')
		if select_form.is_valid():
			select_query = Q()
			selects = select_form.cleaned_data
			if selects['sex']:
				select_query = select_query & Q(mky_gender__in=selects['sex'])
			if selects['species']:
				select_query = select_query & Q(mky_species__in=selects['species'])

			filter_form = AdvancedSearchFilterForm(data=request.POST, prefix='filter')
			if filter_form.is_valid():
				filters = filter_form.cleaned_data
				if filters['control']:
					select_query = select_query & (Q(mky_drinking=False) | Q(mky_housing_control=True))
				if filters['proteins']:
					select_query = select_query & Q(protein_set__mpn_stdev__gte=1, protein_set__protein__in=filters['proteins'])
				if filters['cohorts']:
					select_query = select_query & Q(cohort__in=filters['cohorts'])

			if select_query:
				show_ids = Monkey.objects.filter(select_query).values_list('mky_id', flat=True).distinct()
			else:
				show_ids = Monkey.objects.none()
			hide_ids = Monkey.objects.exclude(pk__in=show_ids).values_list('mky_id', flat=True).distinct()
			hide_ids = list(hide_ids)
			show_ids = list(show_ids)

		return HttpResponse(simplejson.dumps({'show_ids': show_ids, 'hide_ids': hide_ids}), mimetype='application/json')
	else:
		raise Http404

