import re
import sys, os
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.template.loader import render_to_string

project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)
from datetime import datetime
from django.core.mail import send_mail
from matrr.models import RequestStatus, Request, Account, Acceptance


def urge_po_mta():
	accepted = Q(req_status__in=[RequestStatus.Partially, RequestStatus.Accepted]) # Requests that have been accepted
	incomplete = Q(req_purchase_order="") | Q(req_purchase_order=None) | Q(user__account__act_mta_is_valid=False)

	incomplete_accepted = Request.objects.filter(accepted & incomplete)


	for req in incomplete_accepted:
		from_email = Account.objects.get(user__username='matrr_admin').email
		to_email = req.user.email

		recipients = list()
		recipients.append(to_email)

		if req.req_status == RequestStatus.Accepted:
			email_template = 'matrr/review/request_accepted_email.txt'
		elif req.req_status == RequestStatus.Partially:
			email_template = 'matrr/review/request_partially_accepted_email.txt'
		else:
			raise Exception('How did you get here?!')

		request_url = reverse('order-detail', args=[req.req_request_id])
		body = render_to_string(email_template, {'request_url': request_url, 'req_request': req, 'Acceptance': Acceptance})
		body = re.sub('(\r?\n){2,}', '\n\n', body)
		subject = "MATRR needs more information before request %s can be shipped." % str(req.pk)

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s Report urged for request: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), `req`)

#if settings.PRODUCTION:
urge_po_mta()