from django.contrib.auth.models import Permission
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from matrr import helper
import settings, re
from datetime import datetime, timedelta, date
from django.core.mail import send_mail
from matrr.models import Request, User, Shipment, Account, RequestStatus, Acceptance, Group, Review

# regular_tasks
def send_colliding_requests_info():

	time_now = datetime.now()
	time_yesterday = time_now - timedelta(days=1)
	requests = Request.objects.submitted().filter(req_modified_date__gte=time_yesterday, req_modified_date__lte=time_now).exclude(user__username='matrr_admin')

	collisions = list()

	for request in requests:
		acc_coll =  request.get_acc_req_collisions()
		sub_coll =  request.get_sub_req_collisions()
		if acc_coll or sub_coll:
			collisions.append((request, sub_coll, acc_coll))


	if len(collisions) > 0:
		users = Account.objects.users_with_perm('can_receive_colliding_requests_info')
		collision_text = ""
		for req, sub, acc in collisions:

			sub_text = ""
			if sub:
				sub_text = "	has collision with following submitted requests:\n"
				for s in sub:
					sub_text = sub_text + ("		%s\n" % s)
			acc_text = ""
			if acc:
				acc_text = "	has collision with following accepted requests:\n"
				for a in acc:
					acc_text = acc_text + ("		%s\n" % a)

			collision_text = collision_text + ("Request: %s\n" % req) + sub_text + acc_text
		subject = 'Submitted requests with collisions'
		body = 'Information from matrr.com\nSome requests submitted during last 24 hours collide with other requests.\n' + \
				collision_text + \
				'Please, do not respond. This is an automated message.\n'

		from_email = Account.objects.get(user__username='matrr_admin').email
		for user in users:
			email = user.email
			recipients = list()
			recipients.append(email)


			ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Colliding requests info sent for user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# regular_tasks
def send_verify_tissues_info():

	users = Account.objects.users_with_perm('can_verify_tissues')
	time_now = datetime.now()
	time_yesterday = time_now - timedelta(days=1)
	requests = Request.objects.submitted().filter(req_modified_date__gte=time_yesterday, req_modified_date__lte=time_now)
	requests = requests.exclude(user__username='matrr_admin')
	requests = requests.exclude(cohort__coh_cohort_name__icontains='assay')

	# Send emails to all tissue verifiers for all non-assay requests
	if len(requests) > 0:
		from_email = Account.objects.get(user__username='matrr_admin').email
		for user in users:
			email = user.email
			recipients = list()
			recipients.append(email)
			subject = 'Tissues to be verified'
			body = 'Information from matrr.com\n During last 24 hours new request(s) has (have) been submitted. Your account %s can verify tissues. Please, find some time to do so.\n' % user.username + \
				'Please, do not respond. This is an automated message.\n'

			ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Verify tissues info sent for user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)


	# Send emails only to jim and april for assay requests.  Because assay requests are special....
	assay_requests = Request.objects.submitted().filter(req_modified_date__gte=time_yesterday, req_modified_date__lte=time_now)
	assay_requests = assay_requests.exclude(user__username='matrr_admin')
	assay_requests = assay_requests.filter(cohort__coh_cohort_name__icontains='assay')

	if len(assay_requests) > 0:
		from_email = Account.objects.get(user__username='matrr_admin').email
		for user in [Account.objects.get(user__username='jdaunais'), Account.objects.get(user__username='adaven')]:
			email = user.email
			recipients = list()
			recipients.append(email)
			subject = 'Assay Tissues to be verified'
			body = 'Information from matrr.com\n During last 24 hours new request(s) has (have) been submitted. Your account %s can verify tissues. Please, find some time to do so.\n' % user.username + \
				'Please, do not respond. This is an automated message.\n'

			ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Verify tissues info sent for user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# regular_tasks
def urge_po_mta():
#	accepted = Q(req_status__in=[RequestStatus.Partially, RequestStatus.Accepted]) # Requests that have been accepted
	#incomplete = Q(req_purchase_order="") | Q(req_purchase_order=None) # | Q(user__account__act_mta_is_valid=False) <-- not a real field

	accepted = Request.objects.accepted_and_partially()


	for req in accepted:
		if req.req_purchase_order and req.user.account.has_mta():
			continue

		from_email = Account.objects.get(user__username='matrr_admin').email
		to_email = req.user.email

		recipients = list()
		recipients.append(to_email)

		if req.req_status == RequestStatus.Accepted:
			email_template = 'matrr/review/request_accepted_email.txt'
		elif req.req_status == RequestStatus.Partially:
			email_template = 'matrr/review/request_partially_accepted_email.txt'
		else:
			print "How did you get here?!"
			raise Exception('How did you get here?!')

		request_url = reverse('order-detail', args=[req.req_request_id])
		body = render_to_string(email_template, {'request_url': request_url, 'req_request': req, 'Acceptance': Acceptance})
		body = re.sub('(\r?\n){2,}', '\n\n', body)
		subject = "MATRR needs more information before request %s can be shipped." % str(req.pk)

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s Report urged for request: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), `req`)

# regular_tasks
def urge_progress_reports():
	today = date.today()
	days90 = timedelta(days = 90)
	limit_date = today - days90
	ship_to_report_req = Shipment.objects.filter(shp_shipment_date__lte = limit_date, req_request__rud_set=None)

	for shipment in ship_to_report_req.values('req_request','user','shp_shipment_date'):
		from_email = Account.objects.get(user__username='matrr_admin').email
		email = User.objects.get(id= shipment['user']).email

		recipients = list()
		recipients.append(email)
		req = Request.objects.get(req_request_id= shipment['req_request'])

		subject = 'Progress Report'
		body = 'Hello, \nthe tissue(s) you requested were shipped on %s. ' % shipment['shp_shipment_date'] + \
			'Please, submit a 90 day progress report concerning this request using this link: http://gleek.ecs.baylor.edu%s\n' % reverse('rud-upload') + \
			"\nRequest overview:\n\n%s\n" % req.print_self_in_detail() + \
			"\nYours sincerely,\nMATRR team\n\n" + \
			'This is an automated message.\n'

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		req.req_report_asked_count += 1
		req.save()
		if ret > 0:
			print "%s Report urged for request: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), `req`)

	way_overdues = ship_to_report_req.filter(req_request__req_report_asked_count__gte=2)
	if way_overdues.count() and today.isocalendar()[1] % 2 == 0: # there exist overdue updates, and today is an even week of the year
		from_email = Account.objects.get(user__username='matrr_admin').email
		recipients = [user.email for user in Group.objects.get(name='Uberuser').user_set.all()]
		subject = 'Overdue Progress Report'
		body = "We have some users who haven't given us a research update.  Click the link below to see who's slacking off.\n\n"
		body += 'http://gleek.ecs.baylor.edu' + reverse('rud-overdue')

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s Overdue research update notification sent" % datetime.now().strftime("%Y-%m-%d,%H:%M:%S")

# regular_tasks
def send_pending_reviews_info():
	users = Account.objects.users_with_perm('can_receive_pending_reviews_info')
	from_email = Account.objects.get(user__username='matrr_admin').email
	for user in users:


		reviews = Review.objects.filter(user=user.id).filter(req_request__req_status=RequestStatus.Submitted).exclude(req_request__user__username='matrr_admin')
		unfinished_reviews = [review for review in reviews if not review.is_finished()]
		if len(unfinished_reviews) > 0:

			email = user.email
			recipients = list()
			recipients.append(email)
			subject = 'Pending requests'
			body = 'Information from matrr.com\n You have pending request(s) to be reviewed on your account: %s \n' % user.username + \
				'Please, do not respond. This is an automated message.\n'

			ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Pending info sent for user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# used in matrr and utils.regular_tasks
def send_shipment_ready_notification(assay_ready=False):
	if assay_ready:
		users = [User.objects.get(username='jdaunais'), User.objects.get(username='adaven')]
	else:
		users = User.objects.filter(is_staff=True).exclude(username='garyjmurray')
	from_email = User.objects.get(username='matrr_admin').email
	for user in users:
		email = user.email
		recipients = list()
		recipients.append(email)
		subject = '%sequest is ready to ship' % ('Assay r' if assay_ready else 'R')
		body =  'Click here to see the shipping overview page.\n'
		body += 'http://gleek.ecs.baylor.edu%s\n' % reverse('shipping-overview')
		body += 'Please, do not respond. This is an automated message.\n'

		if settings.PRODUCTION:
			ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Shipment info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# matrr
def send_po_manifest_upon_shipment(shp_shipment):
	if not isinstance(shp_shipment, Shipment):
		shp_shipment = Shipment.objects.get(pk=shp_shipment)

	req_request = shp_shipment.req_request	
	perm = Permission.objects.get(codename='po_manifest_email')
	to_list = User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct().values_list('email', flat=True)

	subject = "Shipping Manifest for MATRR request %s." % str(req_request.pk)
	body = "A MATRR shipment has been shipped.  Attached is the shipping manifest for this request, with the customer's Purchase Order number.  Please contact a MATRR admin if there are any issues or missing information."
	email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, to_list)

	filename = 'manifest_user-%s_shipment-%s.pdf' % (str(req_request.user), str(shp_shipment.pk))
	outfile = open('/tmp/%s' % filename, 'wb')
	context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
	helper.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=outfile)

	outfile.close()
	email.attach_file(outfile.name)
	email.send()

# matrr
def notify_user_upon_shipment(shp_shipment):
	if not isinstance(shp_shipment, Shipment):
		shp_shipment = Shipment.objects.get(pk=shp_shipment)

	req_request = shp_shipment.req_request
	to_list = [req_request.user.email]

	subject = "MATRR has shipped tissue to %s." % str(req_request.user.username)
	body = "A MATRR shipment has been shipped.  Attached is the shipping manifest for this request.\n"
	body += "\nFedEx Tracking Number:  %s\n" % str(shp_shipment.shp_tracking)
	body += 'Please, do not respond. This is an automated message.\n'

	email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, to_list)
	filename = 'manifest_user-%s_shipment-%s.pdf' % (str(req_request.user), str(shp_shipment.pk))
	outfile = open('/tmp/%s' % filename, 'wb')
	context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
	helper.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=outfile)

	outfile.close()
	email.attach_file(outfile.name)
	email.send()

# matrr
def send_jim_hippocampus_notification(req_request):
	if not isinstance(req_request, Request):
		req_request = Request.objects.get(pk=req_request)
	jim = User.objects.get(username='jdaunais')
	matrr = User.objects.get(username='matrr_admin')

	subject = 'Yo dude, user %s requested a HIPPOCAMPUS' % req_request.user
	body =  'Hey Jim,\n'
	body += "This is just a frendly remainder that sumone rekwested a hippocampus, which in some way requires your attenshun.\n\n"
	body += 'http://gleek.ecs.baylor.edu%s\n' % reverse('review-overview', args=[req_request.pk])
	body += 'This message is very, extremely automated.  Have a nice day!\n\n'
	body += 'Sincerely,\n'
	body += 'MATRR'

	if settings.PRODUCTION:
		ret = send_mail(subject, body, matrr.email, recipient_list=[jim.email,], fail_silently=False)
		if ret > 0:
			print "%s Hippocampus notification sent to %s." % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), jim.username)

# matrr
def send_verify_new_account_email(account):
	body = "New account was created.\n" +\
		   "\t username: %s\n" % account.user.username +\
		   "\t first name: %s\n" % account.user.first_name +\
		   "\t last name: %s\n" % account.user.last_name +\
		   "\t e-mail: %s\n" % account.user.email +\
		   "\t phone number: %s\n" % account.phone_number +\
		   "\t institution: %s\n" % account.institution +\
		   "\t first name: %s\n" % account.user.first_name +\
		   "\t address 1: %s\n" % account.act_real_address1 +\
		   "\t address 2: %s\n" % account.act_real_address2 +\
		   "\t city: %s\n" % account.act_real_city +\
		   "\t ZIP code: %s\n" % account.act_real_zip +\
		   "\t state: %s\n" % account.act_real_state +\
		   "\nTo view account in admin, go to:\n" +\
		   "\t http://gleek.ecs.baylor.edu/admin/matrr/account/%d/\n" % account.user.id +\
		   "To verify account follow this link:\n" +\
		   "\t http://gleek.ecs.baylor.edu%s\n" % reverse('account-verify', args=[account.user.id, ]) +\
		   "To delete account follow this link and confirm deletion of all objects (Yes, I'm sure):\n" +\
		   "\t http://gleek.ecs.baylor.edu/admin/auth/user/%d/delete/\n" % account.user.id +\
		   "All the links might require a proper log-in."

	subject = "New account on www.matrr.com"
	from_e = "Erich_Baker@baylor.edu"
	to_e = list()
	to_e.append(from_e)
	if settings.PRODUCTION:
		send_mail(subject, body, from_e, to_e, fail_silently=True)

# matrr
def send_new_request_info(req_request):
	if not settings.PRODUCTION and req_request.user.username != 'matrr_admin':
		print "%s - New request email not sent, settings.PRODUCTION = %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), settings.PRODUCTION)
		return
	req_request = Request.objects.get(pk=req_request.req_request_id)
	users = Account.objects.users_with_perm('can_receive_pending_reviews_info')
	from_email = Account.objects.get(user__username='matrr_admin').email
	for user in users:
		email = user.email
		recipients = list()
		recipients.append(email)
		subject = 'User %s submitted a request for %s tissues from %s.' % (req_request.user, req_request.get_requested_tissue_count(), req_request.cohort)
		body = 'More information about this request is available at matrr.com\n'\
			'Please, do not respond. This is an automated message.\n'

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s New request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# matrr
def send_verification_complete_notification(req_request):
	from_email = Account.objects.get(user__username='matrr_admin').email
	recipients = [from_email]
	subject = 'Inventory Verified for request %s'% str(req_request.pk)
	body = "Information from matrr.com\n The inventory for %s's request from cohort %s has all been verified.\n" % (req_request.user.username, req_request.cohort.coh_cohort_name) + \
		   "Please check https://gleek.ecs.baylor.edu%s to see if this request is ready for processing.\n" % reverse('review-overview', args=[req_request.pk,]) + \
		   "Please, do not respond. This is an automated message.\n"

	if settings.PRODUCTION:
		send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)

# matrr
def send_processed_request_email(form_data, req_request):
	subject = form_data['subject']
	body = form_data['body']
	subject = ' '.join(subject.splitlines())
	perm = Permission.objects.get(codename='bcc_request_email')
	bcc_list = User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct().values_list('email', flat=True)
	email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [req_request.user.email], bcc=bcc_list)
	if req_request.req_status != RequestStatus.Rejected:
		outfile = open('/tmp/MATRR_Invoice-%s.pdf' % str(req_request.pk), 'wb')
		context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
		helper.export_template_to_pdf('pdf_templates/invoice.html', context, outfile=outfile)
		outfile.close()
		email.attach_file(outfile.name)
	email.send()

# matrr
def send_contact_us_email(form_data, user):
	subject = ''.join(form_data['email_subject'].splitlines())
	subject += '//'
	try:
		if user.email:
			subject += user.email
	except:
		# Anonymous user does not have email field.
		pass
	email_to = User.objects.get(username='matrr_admin').email
	send_mail(subject, form_data['email_body'], form_data['email_from'],[email_to])

# matrr
def notify_mta_uploaded(mta):
	mta_admins = Account.objects.users_with_perm('mta_upload_notification')
	from_email = Account.objects.get(user__username='matrr_admin').email

	for admin in mta_admins:
		recipients = [admin.email]
		subject = 'User %s has uploaded an MTA form' % mta.user.username
		body = '%s has has uploaded an MTA form.\n' % mta.user.username
		body += 'This MTA can be downloaded here:  http://gleek.ecs.baylor.edu%s.\n' % mta.mta_file.url
		body += 'If necessary you can contact %s with the information below.\n\n' % mta.user.username
		body += "Name: %s %s\nEmail: %s\nPhone: %s \n\n" % (mta.user.first_name, mta.user.last_name, mta.user.email, mta.user.account.phone_number)
		body += "If this is a valid MTA click here to update MATRR: http://gleek.ecs.baylor.edu%s" % reverse('mta-list')

		ret = send_mail(subject, body, from_email, recipient_list=recipients)
		if ret > 0:
			print "%s MTA verification request sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), admin.username)
	return

# matrr
def send_account_verified_email(account):
	subject = "Account on www.matrr.com has been verified"
	body = "Your account on www.matrr.com has been verified\n" +\
		   "\t username: %s\n" % account.user.username +\
		   "From now on, you can access pages on www.matrr.com.\n" +\
		   "This is an automated message, please, do not respond.\n"

	from_e = account.user.email
	to_e = list()
	to_e.append(from_e)
	send_mail(subject, body, from_e, to_e, fail_silently=True)

# matrr
def send_mta_uploaded_email(account):
	from_email = Account.objects.get(user__username='matrr_admin').email

	users = Account.objects.users_with_perm('receive_mta_request')
	for user in users:
		recipients = [user.email]
		subject = 'User %s has requested an MTA form' % account.user.username
		body = '%s has indicated he/she is not associated with any of the UBMTA signatories and requested an MTA form.\n'\
			   'He/she was told instructions would be provided with the MTA form.  '\
			   'If you cannot contact %s with the information provided below, please notify the MATRR admins.\n' % (account.user.username, account.user.username)
		body += "\n\nName: %s %s\nEmail: %s\nPhone: %s" % (account.first_name, account.last_name, account.email, account.phone_number)
		body += "\n\nIn addition to any other steps, please have %s upload the signed MTA form to MATRR using this link: http://gleek.ecs.baylor.edu%s" % (
		account.user.username, reverse('mta-upload'))

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s MTA request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# matrr
def send_dna_request_details(req_request):
	from_email = Account.objects.get(user__username='matrr_admin').email

	# todo: create permission for this email
	users = Account.objects.users_with_perm('')
	for user in users:
		recipients = [user.email]

		# todo: actually write the email
		subject = ''
		body = ''

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s MTA request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)
