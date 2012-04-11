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


if settings.PRODUCTION:
	send_verify_tissues_info()
