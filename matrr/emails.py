from django.core.urlresolvers import reverse
import settings
from datetime import datetime
from django.core.mail import send_mail
from matrr.models import Request, User


def send_shipment_ready_notification(req_request):
	if not settings.PRODUCTION and req_request.user.username != 'matrr_admin':
		print "%s - New request email not sent, settings.PRODUCTION = %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), settings.PRODUCTION)
		return
	if not isinstance(req_request, Request):
		req_request = Request.objects.get(pk=req_request.req_request_id)

	users = User.objects.filter(is_staff=True).exclude(username='garyjmurray')
#	users = User.objects.filter(username='jarquet')
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
