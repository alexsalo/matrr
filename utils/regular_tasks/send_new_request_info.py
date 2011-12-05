#import sys, os
#project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#sys.path.append(project)
#from django.core.management import setup_environ
#import settings
#setup_environ(settings)
from datetime import datetime

from django.core.mail import send_mail
from matrr.models import Account, Request


def send_new_request_info(req_request):
	if not settings.PRODUCTION:
		print "%s - New request email not sent, settings.PRODUCTION = %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), settings.PRODUCTION)
		return
	req_request = Request.objects.get(pk=req_request.req_request_id)
	users = Account.objects.users_with_perm('can_receive_pending_reviews_info')
	for user in users:
		email = user.email
		recipients = list()
		recipients.append(email)
		subject = 'User %s submitted a request for %s tissues from %s.' % (req_request.user, req_request.get_requested_tissue_count(), req_request.cohort)
		body = 'More information about this request is available at matrr.com\n'\
			'Please, do not respond. This is an automated message.\n'

		ret = send_mail(subject, body, email, recipient_list=recipients, fail_silently=False)
		if ret > 0:
			print "%s New request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)
