import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)
from datetime import datetime, timedelta

from django.core.mail import send_mail
from matrr.models import RequestStatus, Account, Request
from django.contrib.auth.models import Group


def send_verify_tissues_info():
	
	users = Account.objects.users_with_perm('can_verify_tissues')
	time_now = datetime.now()
	time_yesterday = time_now - timedelta(days=1)
	reguests = Request.objects.submitted().filter(req_modified_date__gte=time_yesterday, req_modified_date__lte=time_now).exclude(user__username='matrr_admin')
	
	if len(reguests) > 0:
		for user in users:
			email = user.email
			recipients = list()
			recipients.append(email)
			subject = 'Tissues to be verified'
			body = 'Information from matrr.com\n During last 24 hours new request(s) has (have) been submitted. Your account %s can verify tissues. Please, find some time to do so.\n' % user.username + \
				'Please, do not respond. This is an automated message.\n'
		
			ret = send_mail(subject, body, email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Verify tissues info sent for user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)
				
	
if settings.PRODUCTION:
	send_verify_tissues_info()
