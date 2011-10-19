import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.core.mail import send_mail
from matrr.models import RequestStatus, Review
from django.contrib.auth.models import Group


def send_pending_request_info():
	g = Group.objects.get(name='Committee')
	users = g.user_set.all()
	for user in users:
	
		submitted = RequestStatus.objects.get(rqs_status_name='Submitted')
		reviews = Review.objects.filter(user=user.id).filter(req_request__request_status=submitted)
		unfinished_reviews = [review for review in reviews if not review.is_finished()]
		if len(unfinished_reviews) > 0:
		
			email = user.email
			recipients = list()
			recipients.append(email)
			subject = 'Pending requests'
			body = 'Information from matrr.com\n You have pending request(s) to be reviewed on your account: %s \n' % user.username + \
				'Please, do not respond. This is an automated message.\n'
		
			ret = send_mail(subject, body, email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "Pending info sent for user: %s" % user.username
			
	

send_pending_request_info()
