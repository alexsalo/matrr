from django.contrib.auth.models import Permission
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from matrr.process_latex import process_latex
import settings
from datetime import datetime
from django.core.mail import send_mail
from matrr.models import Request, User, Shipment


def send_shipment_ready_notification(req_request):
	if not isinstance(req_request, Request):
		req_request = Request.objects.get(pk=req_request)

	users = User.objects.filter(is_staff=True).exclude(username='garyjmurray')
	from_email = User.objects.get(username='matrr_admin').email
	for user in users:
		email = user.email
		recipients = list()
		recipients.append(email)
		subject = 'Request is ready to ship for user %s' % req_request.user
		body =  'Click here to see request details, download shipping manifest and update MATRR once shipped.\n'
		body += 'http://gleek.ecs.baylor.edu%s\n' % reverse('shipment-creator', args=[req_request.pk])
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
	process_latex('latex/shipment_manifest.tex', {'req_request': req_request,
												  'account': req_request.user.account,
												  'time': datetime.today(),
												  }, outfile=outfile)
	outfile.close()
	email.attach_file(outfile.name)
	email.send()