# Create your views here.
from django.core.mail.message import EmailMessage
from django.forms.models import modelformset_factory
from django.forms.models import formset_factory
from django.template import RequestContext
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import  render_to_response, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.encoding import smart_str
import settings
from matrr.forms import *
from matrr.models import *
import math
from datetime import date, timedelta
from django.db import DatabaseError
from djangosphinx.models import SphinxQuerySet
from process_latex import process_latex
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from utils import plotting
from matrr.decorators import user_owner_test
from utils.plotting import monkey_protein

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
def cohorts_view_available(request):
	cohorts = Cohort.objects.filter(coh_upcoming=False).order_by('coh_cohort_name')
	template_name = 'matrr/available_cohorts.html'
	return __cohorts_view(request, cohorts, template_name)


def cohorts_view_upcoming(request):
	cohorts = Cohort.objects.filter(coh_upcoming=True).order_by('coh_cohort_name')
	template_name = 'matrr/upcoming_cohorts.html'
	return __cohorts_view(request, cohorts, template_name)


def cohorts_view_all(request):
	cohorts = Cohort.objects.order_by('coh_cohort_name')
	template_name = 'matrr/cohorts.html'
	return __cohorts_view(request, cohorts, template_name)


def cohorts_view_assay(request):
	return redirect(reverse('tissue-shop-landing', args=[Cohort.objects.get(coh_cohort_name__iexact="Assay Development").pk, ]))


def matrr_handler500(request):
	from django.core.context_processors import static

	return render_to_response('500.html', static(request), context_instance=RequestContext(request)
	)


def __set_images(cohort, user):
	cohort.images = cohort.image_set.vip_filter(user)
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
		images = CohortImage.objects.filter(cohort=cohort).vip_filter(request.user)
	else:
		return redirect(reverse('cohorts'))
	return render_to_response('matrr/cohort.html', {'cohort': cohort, 'images': images, 'coh_data': coh_data, 'plot_gallery': True}, context_instance=RequestContext(request))


def monkey_cohort_detail_view(request, cohort_id, monkey_id):
	try:
		monkey = Monkey.objects.get(mky_id=monkey_id)
	except:
		raise Http404((u"No %(verbose_name)s found matching the query") %
					  {'verbose_name': Monkey._meta.verbose_name})

	if str(monkey.cohort.coh_cohort_id) != cohort_id:
		raise Http404((u"No %(verbose_name)s found matching the query") %
					  {'verbose_name': Monkey._meta.verbose_name})

	images = MonkeyImage.objects.filter(monkey=monkey).vip_filter(request.user)
	return render_to_response('matrr/monkey.html', {'monkey': monkey, 'images': images, 'plot_gallery': True},
							  context_instance=RequestContext(request))


def monkey_detail_view(request, monkey_id):
	try:
		monkey = Monkey.objects.get(mky_id=monkey_id)
	except:
		raise Http404((u"No %(verbose_name)s found matching the query") %
					  {'verbose_name': Monkey._meta.verbose_name})

	images = MonkeyImage.objects.filter(monkey=monkey).vip_filter(request.user)
	return render_to_response('matrr/monkey.html', {'monkey': monkey, 'images': images, 'plot_gallery': True},
							  context_instance=RequestContext(request))


def get_or_create_cart(request, cohort):
	"""
	 This function will get the cart for the cohort if it exists.
	 If it does not exist, it will create a new cart for the cohort.
	 In the case that the user has a cart open for a different cohort,
	 this function will return None.  (unless the cart was empty, in which
	 case it will be deleted.)
	 """

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
	instance = TissueRequest(tissue_type=current_tissue, req_request=cart_request)

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
			url = reverse('tissue-shop-landing', args=[cart_request.cohort.coh_cohort_id, ])
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


def mta_upload(request):
	# make blank mta instance
	mta_object = Mta(user=request.user)
	# make a MTA upload form if one does not exist
	if request.method == 'POST':
		if 'request_form' in request.POST:
			if not settings.PRODUCTION:
				print "%s - New request email not sent, settings.PRODUCTION = %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), settings.PRODUCTION)
			else:
#				users = Account.objects.users_with_perm('receive_mta_request')
#				from_email = Account.objects.get(user__username='matrr_admin').email
				users = Account.objects.filter(user__username='jarquet')
				from_email = 'jarquet@gmail.com'
				for user in users:
					account = request.user.account
					email = account.email
					recipients = [email]
					subject = 'User %s has requested an MTA form' % account.user.username
					body = '%s has indicated he/she is not associated with any of the UBMTA signatories and requested an MTA form.\n' \
						   'He/she was told instructions would be provided with the MTA form.  '\
						   'If you cannot contact %s with the information provided below, please notify the MATRR admins.\n' % (account.user.username, account.user.username)
					body += "\n\nName: %s %s\nEmail: %s\nPhone: %s" % (account.first_name, account.last_name, account.email, account.phone_number)
					body += "\n\nIn addition to any other steps, please have %s upload the signed MTA form to MATRR using this link: http://gleek.ecs.baylor.edu%s" % (account.user.username, reverse('mta-upload'))

					ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
					if ret > 0:
						print "%s MTA request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)
			messages.success(request, 'A MATRR administrator has been notified of your MTA request and will contact you with more information.')
			return redirect(reverse('account-view'))
		form = MtaForm(request.POST, request.FILES, instance=mta_object)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
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


def rud_upload(request):
	if request.method == 'POST':
		form = RudForm(request.user, request.POST, request.FILES)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			messages.success(request, 'Research Uploaded Successfully')
			return redirect(reverse('account-view'))
	else:
		# create the form for the MTA upload
		form = RudForm(request.user)
	return render_to_response('matrr/upload_forms/rud_upload_form.html',
			{'form': form,
			 },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.add_cohortdata'), login_url='/denied/')
def cod_upload(request, coh_id=1):
	if request.method == 'POST':
		form = CodForm(request.POST, request.FILES)
		if form.is_valid():
			# all the fields in the form are valid, so save the data
			form.save()
			messages.success(request, 'Upload Successful')
			return redirect(reverse('cohort-details', args=[str(coh_id)]))
	else:
		cohort = Cohort.objects.get(pk=coh_id)
		form = CodForm(cohort=cohort)
	return render_to_response('matrr/upload_forms/cod_upload_form.html', {'form': form, }, context_instance=RequestContext(request))


@staff_member_required
def account_verify(request, user_id):
	account = get_object_or_404(Account, pk=user_id)
	if not account.verified:
		account.verified = True
		account.save()
		#		send email
		subject = "Account on www.matrr.com has been verified"
		body = "Your account on www.matrr.com has been verified\n" +\
			   "\t username: %s\n" % account.user.username +\
			   "From now on, you can access pages on www.matrr.com.\n" +\
			   "This is an automated message, please, do not respond.\n"

		from_e = account.user.email
		to_e = list()
		to_e.append(from_e)
		send_mail(subject, body, from_e, to_e, fail_silently=True)
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
	if request.method == 'POST':
		form = AccountMTAForm(data=request.POST)
		if form.is_valid():
			institution = form.cleaned_data['institution'].ins_institution_name
			account = request.user.account
			account.act_mta = institution
			account.save()

			if institution == "Non-UBMTA Institution":
				return redirect('mta-upload')
#				messages.info(request, "If your institution is not part of the <acronym>, you must download, sign, scan, and upload a Material Transfer Agreement.  ")
			else:
				messages.success(request, 'Account Info Saved')
				return redirect(reverse('account-view'))
	else:
		form = AccountMTAForm()
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

	rud_info = ResearchUpdate.objects.filter(request__user=user_id)

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
	overviewers = Account.objects.users_with_perm('view_review_overview')
	for req_request in req_requests:
		req_request.complete = list()
		for reviewer in overviewers:
			for review in req_request.review_set.all():
				if reviewer == review.user:
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
def review_overview(request, req_request_id):
	# get the request being reviewed
	req_request = Request.objects.get(req_request_id=req_request_id)
	no_monkeys = False

	if req_request.is_evaluated():
		no_monkeys = True
	if  'HTTP_REFERER' in request.META:
		back_url = request.META['HTTP_REFERER']
	else:
		back_url = ""

	TissueRequestFormSet = modelformset_factory(TissueRequest, form=TissueRequestProcessForm, extra=0)
	if request.POST:
		tissue_request_forms = TissueRequestFormSet(request.POST, prefix='tissue_requests')

		if tissue_request_forms.is_valid():
			tissue_request_forms.save()
			return redirect(reverse('review-overview-process', args=[req_request_id]))
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
	revised = Request.objects.revised().filter(user=request.user)
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


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user or u.has_perm('change_shipment'), arg_name='req_request_id', redirect_url='/denied/')
def order_detail(request, req_request_id, edit=False):
	# get the request
	req_request = Request.objects.get(req_request_id=req_request_id)
	# check that the request belongs to this user
	#	if req_request.user != request.user and Group.objects.get(name='Committee') not in request.user.groups.all():
	#		# if the request does not belong to the user, return a 404 error (alternately, we could give a permission denied message)
	#		raise Http404('This page does not exist.')

	eval = req_request.is_evaluated()
	po_form = ''
	if not req_request.req_status == 'SH' and not req_request.req_status == 'RJ':
		po_form = PurchaseOrderForm(instance=req_request)
		if request.method == 'POST':
			po_form = PurchaseOrderForm(instance=req_request, data=request.POST)
			if po_form.is_valid():
				po_form.save()
				messages.info(request, "Purchase Order number has been saved.")
			else:
				messages.error(request, "Purchase Order form invalid, please try again.  Please notify a MATRR admin if this message is erroneous.")

	return render_to_response('matrr/order/order_detail.html',
			{'order': req_request,
			 'Acceptance': Acceptance,
			 'RequestStatus': RequestStatus,
			 'shipped': req_request.is_shipped(),
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
def order_duplicate(request, req_request_id):
	req = Request.objects.get(req_request_id=req_request_id)
	if not req.can_be_revised() or not request.POST or request.POST['submit'] != "duplicate":
		raise Http404('This page does not exist.')
	req.create_revised_duplicate()
	messages.success(request, 'A new editable copy has been created. You can find it under Revised Orders.')
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


def tissue_shop_landing_view(request, cohort_id):
	context = dict()
	assay = Cohort.objects.get(coh_cohort_name__iexact="Assay Development")
	cohort = Cohort.objects.get(coh_cohort_id=cohort_id)
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
				# Email subject *must not* contain newlines
				subject = ''.join(form.cleaned_data['subject'].splitlines())
				if not settings.DEVELOPMENT:
					perm = Permission.objects.get(codename='bcc_request_email')
					bcc_list = User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct().values_list('email', flat=True)
					email = EmailMessage(subject, form.cleaned_data['body'], settings.DEFAULT_FROM_EMAIL, [req_request.user.email], bcc=bcc_list)
					if status != RequestStatus.Rejected:
						outfile = open('/tmp/%s.pdf' % str(req_request.pk), 'wb')
						process_latex('latex/shipping_manifest.tex', {'req_request': req_request,
																	  'account': req_request.user.account,
																	  'time': datetime.today(),
																	  }, outfile=outfile)
						outfile.close()
						email.attach_file(outfile.name)
					email.send()
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


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipping_overview(request):
	# get the tissue requests that have been accepted
	accepted_requests = Request.objects.accepted_and_partially()
	# get the tissue requests that have been shipped
	shipped_requests = Request.objects.shipped()

	shipment_ready = {} # currently unused --jf 1/24/2012
	for req in accepted_requests:
		has_fedex = True if req.user.account.act_fedex else False
		has_po = True if req.req_purchase_order else False
		if has_fedex and has_po:
			shipment_ready[req.pk] = 1
		elif has_fedex or has_po:
			shipment_ready[req.pk] = 0
		else:
			shipment_ready[req.pk] = -1

	return render_to_response('matrr/shipping/shipping_overview.html',
			{'accepted_requests': accepted_requests,
			 'shipped_requests': shipped_requests,
			 'shipment_ready': shipment_ready},
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

			if request.user.has_perm('monkey_view_confidential'):
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


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def build_shipment(request, req_request_id):
	# get the request
	req_request = Request.objects.get(req_request_id=req_request_id)

	if Shipment.objects.filter(req_request=req_request).count():
		shipment = req_request.shipment
		if 'shipped' in request.POST:
			if not req_request.can_be_shipped(): # do a sanity check
				messages.warning(request,
				 	"A request can only be shipped if all of the following are true:\
				 	 1) the request has been accepted and not yet shipped, \
				 	 2) the user has provided a FedEx number, \
				 	 3) user has submitted a Purchase Order number, \
				 	 4) User has submitted a valid MTA.")
			else:
				shipment.shp_shipment_date = datetime.today()
				shipment.user = request.user
				shipment.save()
				req_request.ship_request()
				req_request.save()
	else:
		# create the shipment
		shipment = Shipment(user=req_request.user, req_request=req_request)
		shipment.save()

	return render_to_response('matrr/shipping/build_shipment.html',
			{'req_request': req_request,
			 'shipment': shipment, },
							  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def make_shipping_manifest_latex(request, req_request_id):
	req_request = Request.objects.get(req_request_id=req_request_id)
	response = HttpResponse(mimetype='application/pdf')
	response['Content-Disposition'] = 'attachment; filename=manifest-' +\
									  str(req_request.user) + '-' +\
									  str(req_request.pk) + '.pdf'
	account = req_request.user.account

	return process_latex('latex/shipping_manifest.tex', {'req_request': req_request, 'account': account, 'time': datetime.today()}, outfile=response)


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
			req.req_request_date = datetime.now
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
	return process_latex('latex/tissue_verification.tex',
														{'tiv_list': tiv_list,
														 'user': request.user,
														 'date': datetime.today()},
														 outfile=response)

def tissue_verification_list(request, req_request_id):
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
	if int(req_request_id): # Page is displaying a specific requests' TIVs
		tiv_list = TissueInventoryVerification.objects.filter(tissue_request__req_request__req_request_id=req_request_id).order_by('monkey', 'tissue_type__tst_tissue_name')
	else: # Page is displaying the list of TIVs without tissue_requests
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
					   'req_request': req_request, }
		initial[len(initial):] = [tiv_initial]

	formset = TissueVerificationFormSet(initial=initial)
	return render_to_response('matrr/verification/verification_list.html', {"formset": formset, "req_id": req_request_id, "paginator": p_tiv_list}, context_instance=RequestContext(request))


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
				   'req_request': req_request,}
	tivform = TissueInventoryVerificationDetailForm(initial=tiv_initial)
	return render_to_response('matrr/verification/verification_detail.html', {"tivform": tivform, "req_id": req_request_id}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.browse_inventory'), login_url='/denied/')
def inventory_cohort(request, coh_id):
	cohort = get_object_or_404(Cohort, pk=coh_id)
	tsts = TissueType.objects.all().order_by('tst_tissue_name')
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
	if request.method == "POST":
		dataset = request.POST.get('dataset')
		if dataset == 'etoh':
			if request.user.has_perm('matrr.view_etoh_data'):
				return redirect('tools-etoh')
			else:
				return redirect('/denied/')
		elif dataset == 'protein':
			return redirect('tools-protein')
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
		cohorts_with_protein_data = Cohort.objects.filter(pk__in=cohorts_with_protein_data) # so get the queryset of cohorts
		cohort_form = CohortSelectForm(cohort_queryset=cohorts_with_protein_data)
	return render_to_response('matrr/tools/protein.html', {'subject_select_form': cohort_form}, context_instance=RequestContext(request))


def tools_cohort_protein(request, cohort_id):
	if request.method == 'POST':
		subject_select_form = SubjectSelectForm(data=request.POST)
		if subject_select_form.is_valid():
			subject = subject_select_form.cleaned_data['subject']
			if subject == 'monkey':
				return redirect('tools-monkey-protein', cohort_id)
			elif subject == 'cohort':
				return redirect('tools-cohort-protein-graphs', cohort_id)
			else: # assumes subject == 'download'
				account = request.user.account
				if account.has_mta():
					cohort = Cohort.objects.get(pk=cohort_id)
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
	return render_to_response('matrr/tools/protein.html', {'subject_select_form': SubjectSelectForm()}, context_instance=RequestContext(request))


def tools_cohort_protein_graphs(request, cohort_id):
	proteins = None
	old_post = request.session.get('_old_post')
	cohort = Cohort.objects.get(pk=cohort_id)
	context = {'cohort': cohort}
	if request.method == "POST" or old_post:
		post = request.POST if request.POST else old_post
		protein_form = ProteinSelectForm(data=post)
		subject_select_form = CohortSelectForm(data=post)
		if protein_form.is_valid() and subject_select_form.is_valid():
			if int(cohort_id) != subject_select_form.cleaned_data['subject'].pk:
				request.session['_old_post'] = request.POST
				return redirect(tools_cohort_protein_graphs, subject_select_form.cleaned_data['subject'].pk)
			proteins = protein_form.cleaned_data['proteins']
			graphs = __gather_cohort_protein_images(cohort, proteins)
			context['graphs'] = graphs

	cohorts_with_protein_data = MonkeyProtein.objects.all().values_list('monkey__cohort', flat=True).distinct() # for some reason this only returns the pk int
	cohorts_with_protein_data = Cohort.objects.filter(pk__in=cohorts_with_protein_data) # so get the queryset of cohorts

	context['subject_select_form'] = CohortSelectForm(cohort_queryset=cohorts_with_protein_data, horizontal=True, initial={'subject': cohort_id})
	context['protein_form'] = ProteinSelectForm(initial={'proteins': proteins})
	return render_to_response('matrr/tools/protein_cohort.html', context, context_instance=RequestContext(request))


def tools_monkey_protein_graphs(request, cohort_id, monkey_id=0):
	proteins = None
	old_post = request.session.get('_old_post')
	monkey = Monkey.objects.get(pk=monkey_id) if monkey_id else None
	cohort = Cohort.objects.get(pk=cohort_id)
	context = {'monkey': monkey, 'cohort': cohort}
	if request.method == "POST" or old_post:
		post = request.POST if request.POST else old_post
		protein_form = ProteinSelectForm(data=post)
		subject_select_form = MonkeySelectForm(data=post)
		if protein_form.is_valid() and subject_select_form.is_valid():
			if int(monkey_id) != subject_select_form.cleaned_data['subject'].pk:
				request.session['_old_post'] = request.POST
				return redirect(tools_monkey_protein_graphs, cohort_id, subject_select_form.cleaned_data['subject'].pk)
			elif request.session.has_key('_old_post'):
				request.session.pop('_old_post')
			proteins = protein_form.cleaned_data['proteins']
			graph_url = monkey_protein(monkey, proteins, request.user.username)
			context['graphs'] = [graph_url]
	monkeys_with_protein_data = MonkeyProtein.objects.filter(monkey__cohort=cohort).values_list('monkey__pk', flat=True).distinct() # for some reason this only returns the pk int
	monkeys_with_protein_data = Monkey.objects.filter(pk__in=monkeys_with_protein_data) # so get the queryset of cohorts

	context['subject_select_form'] = MonkeySelectForm(monkey_queryset=monkeys_with_protein_data, horizontal=True, initial={'subject': monkey_id})
	context['protein_form'] = ProteinSelectForm(initial={'proteins': proteins})
	return render_to_response('matrr/tools/protein_monkey.html', context, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_vip_images'), login_url='/denied/')
def tools_etoh(request):
	return 0

#  VIP tools
@user_passes_test(lambda u: u.has_perm('matrr.view_vip_images'), login_url='/denied/')
def vip_tools(request):
	return render_to_response('matrr/tools/VIP/vip_index.html', {}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_vip_images'), login_url='/denied/')
def vip_graphs(request):
	if request.POST:
		for key in plotting.VIP_MONKEY_PLOTS:
			if key in request.POST:
				return redirect(reverse('vip-graph-builder', args=[key]))
		for key in plotting.VIP_COHORT_PLOTS:
			if key in request.POST:
				return redirect(reverse('vip-graph-builder', args=[key]))
		return reverse(vip_graphs) #  this should never be hit.  I dunno how it could be.
	else:
		context = {}
		mky_keys = []
		coh_keys = []
		mky_plots = plotting.VIP_MONKEY_PLOTS
		coh_plots = plotting.VIP_COHORT_PLOTS
		for key in mky_plots:
			migs = MonkeyImage.objects.filter(method=key)
			if migs:
				mky_keys.append((key, migs[0], mky_plots[key][1]))
			#else
		for key in coh_plots:
			cigs = CohortImage.objects.filter(method=key)
			if cigs:
				coh_keys.append((key, cigs[0], coh_plots[key][1]))
		mky_keys.sort()
		coh_keys.sort()
		context['mky_keys'] = mky_keys
		context['coh_keys'] = coh_keys
		return render_to_response('matrr/tools/VIP/vip_graphs.html', context, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_vip_images'), login_url='/denied/')
def vip_mtd_graph(request, mtd_id):
	if MonkeyToDrinkingExperiment.objects.filter(pk=mtd_id).count():
		mtd = MonkeyToDrinkingExperiment.objects.get(pk=mtd_id)
		mtd_image, is_new = MTDImage.objects.get_or_create(
			monkey_to_drinking_experiment=mtd,
			method='monkey_bouts_drinks_intraday',
			title="Drinks on %s for monkey %s" % (str(mtd.drinking_experiment.dex_date), str(mtd.monkey))
		)
		return render_to_response('matrr/tools/VIP/vip_graph_generic.html', {'matrr_image': mtd_image}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_vip_images'), login_url='/denied/')
def vip_graph_builder(request, method_name):
	if 'vip-graphs' in request.POST:
		return redirect(reverse('vip-graphs'))

	date_ranges = {}
	all_max = datetime.min.date() # keep track of the max date range possible for all cohorts
	all_min = datetime.today().date() # keep track of the min date range possible for all cohorts
	if 'monkey' in method_name:
		for monkey in Monkey.objects.filter(mtd_set__gt=0).distinct(): # for any monkey we have drinking data for
			mky_min = min(MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).values_list('drinking_experiment__dex_date'))[0]
			mky_max = max(MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).values_list('drinking_experiment__dex_date'))[0]
			date_ranges[monkey] = (mky_min, mky_max)
			# update all_max and all_min
			if mky_min < all_min:
				all_min = mky_min
			if mky_max > all_max:
				all_max = mky_max
	else:
		for cohort in Cohort.objects.filter(cohort_drinking_experiment_set__gt=0).distinct(): # for any cohort we have drinking data for
			coh_min = min(DrinkingExperiment.objects.filter(cohort=cohort).values_list('dex_date'))[0]
			coh_max = max(DrinkingExperiment.objects.filter(cohort=cohort).values_list('dex_date'))[0]
			date_ranges[cohort] = (coh_min, coh_max)
			# update all_max and all_min
			if coh_min < all_min:
				all_min = coh_min
			if coh_max > all_max:
				all_max = coh_max

	min_date = date_to_padded_int(all_min)
	max_date = date_to_padded_int(all_max)
	date_form = DateRangeForm(min_date=min_date, max_date=max_date, data=request.POST)

	if 'monkey' in method_name:
		if request.POST:
			return monkey_graph_builder(request, method_name, date_ranges, min_date, max_date)
		else:
			subject_form = MonkeySelectForm(monkey_queryset=Monkey.objects.filter(mtd_set__gt=0).distinct().order_by('mky_id'))
	else:
		if request.POST:
			return cohort_graph_builder(request, method_name, date_ranges, min_date, max_date)
		else:
			subject_form = CohortSelectForm(cohort_queryset=Cohort.objects.filter(cohort_drinking_experiment_set__gt=0).distinct().order_by('coh_cohort_name'))
	# only reachable if NOT request.POST
	return render_to_response('matrr/tools/VIP/vip_graph_builder.html', {'date_form': date_form, 'subject_form': subject_form, 'date_ranges': date_ranges},
							  context_instance=RequestContext(request))


def monkey_graph_builder(request, method_name, date_ranges, min_date, max_date):
	date_form = DateRangeForm(min_date=min_date, max_date=max_date, data=request.POST)
	subject_form = MonkeySelectForm(data=request.POST)
	matrr_image = ''

	if date_form.is_valid() and subject_form.is_valid():
		parameters = {}
		subject_data = subject_form.cleaned_data
		subject = subject_data['monkey']
		m2de = MonkeyToDrinkingExperiment.objects.filter(monkey=subject)

		date_data = date_form.cleaned_data
		if date_data:
			_from = date_data['from_date']
			_to = date_data['to_date']
			if _from:
				m2de = m2de.filter(drinking_experiment__dex_date__gte=_from)
				parameters['from_date'] = str(_from)
			if _to:
				m2de = m2de.filter(drinking_experiment__dex_date__lte=_to)
				parameters['to_date'] = str(_to)

		if m2de.count():
			from utils.plotting import MONKEY_PLOTS

			title = "%s for monkey %s" % (MONKEY_PLOTS[method_name][1], subject)
			parameters = str(parameters)
			matrr_image, is_new = MonkeyImage.objects.get_or_create(monkey=subject, method=method_name, title=title, parameters=parameters)
			if is_new:
				matrr_image.save()
		else:
			messages.info(request, "No drinking experiments for the given date range for this monkey")

	context = {'date_form': date_form, 'subject_form': subject_form, 'date_ranges': date_ranges, 'matrr_image': matrr_image}
	return render_to_response('matrr/tools/VIP/vip_graph_builder.html', context, context_instance=RequestContext(request))


def cohort_graph_builder(request, method_name, date_ranges, min_date, max_date):
	date_form = DateRangeForm(min_date=min_date, max_date=max_date, data=request.POST)
	subject_form = VIPGraphForm_cohorts(data=request.POST)

	context = {'date_form': date_form, 'subject_form': subject_form, 'date_ranges': date_ranges}

	if date_form.is_valid() and subject_form.is_valid():
		date_data = date_form.cleaned_data
		subject_data = subject_form.cleaned_data
		_from = date_data['from_date']
		_to = date_data['to_date']
		subject = subject_data['cohort']

		parameters = {}
		m2de = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=subject)
		if _from:
			m2de = m2de.filter(drinking_experiment__dex_date__gte=_from)
			parameters['from_date:'] = str(_from)
		if _to:
			m2de = m2de.filter(drinking_experiment__dex_date__lte=_to)
			parameters['to_date:'] = str(_to)

		if m2de.count():
			from utils.plotting import COHORT_PLOTS

			title = "%s for cohort %s" % (COHORT_PLOTS[method_name][1], subject)
			parameters = str(parameters)
			matrr_image, is_new = CohortImage.objects.get_or_create(cohort=subject, method=method_name, title=title, parameters=parameters)
			if is_new:
				matrr_image.save()

			context['matrr_image'] = matrr_image
		else:
			messages.info(request, "No drinking experiments for the given date range for this cohort")
	return render_to_response('matrr/tools/VIP/vip_graph_builder.html', context, context_instance=RequestContext(request))

#	End VIP
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
	r = MTDImage.objects.filter(thumbnail=id)
	files.append((r, 'thumbnail'))
	r = MTDImage.objects.filter(image=id)
	files.append((r, 'image'))
	r = MTDImage.objects.filter(html_fragment=id)
	files.append((r, 'html_fragment'))
	r = DataFile.objects.filter(dat_data_file=id)
	files.append((r, 'dat_data_file'))

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


def test_view(request):
	monkeys = ''
	#	field_names = ['mky_drinking', 'cohort', 'mky_name', 'mky_id', 'mky_real_id', ]
	#	fields = [Monkey._meta.get_field(field) for field in field_names]
	fields = Monkey._meta.fields
	if request.POST:
		spiffy_form = FilterForm(fields, data=request.POST, number_of_fields=1)


		#this shit is crazytown
		if spiffy_form.is_valid(): # hooray, we have a valid form!
			q_object = spiffy_form.get_q_object()
			monkeys = Monkey.objects.filter(q_object)
	else:
		spiffy_form = FilterForm(fields, number_of_fields=1)
	return render_to_response('test.html', {'spiffy_form': spiffy_form, 'monkeys': monkeys}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('auth.upload_raw_data'), login_url='/denied/')
def raw_data_upload(request):
	if request.method == 'POST':
		form = RawDataUploadForm(request.POST, request.FILES)
		if form.is_valid():
			f = request.FILES['data']
			name = f.name + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
			upload_path = os.path.join(settings.UPLOAD_DIR, name)
			destination = open(upload_path, 'wb+')
			for chunk in f.chunks():
				destination.write(chunk)
			destination.close()
			return render_to_response('upload_forms/raw_data_upload.html', {'form': RawDataUploadForm(), 'success': True}, context_instance=RequestContext(request))
	else:
		form = RawDataUploadForm()
	return render_to_response('upload_forms/raw_data_upload.html', {'form': form}, context_instance=RequestContext(request))


