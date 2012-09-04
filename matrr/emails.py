from django.contrib.auth.models import Permission
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from matrr.views import _export_template_to_pdf
import settings
from datetime import datetime
from django.core.mail import send_mail
from matrr.models import Request, User, Shipment


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
		subject = 'Request is ready to ship'
		body =  'Click here to see the shipping overview page.\n'
		body += 'http://gleek.ecs.baylor.edu%s\n' % reverse('shipping-overview')
		body += 'Please, do not respond. This is an automated message.\n'

		if settings.PRODUCTION:
			ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Shipment info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

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
	_export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=outfile)

	outfile.close()
	email.attach_file(outfile.name)
	email.send()

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
	_export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=outfile)

	outfile.close()
	email.attach_file(outfile.name)
	email.send()

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

