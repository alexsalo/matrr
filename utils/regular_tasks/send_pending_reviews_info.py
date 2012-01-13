import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)
from datetime import datetime

from django.core.mail import send_mail
from matrr.models import RequestStatus, Review, Account


def send_pending_reviews_info():
	users = Account.objects.users_with_perm('can_receive_pending_reviews_info')
	from_email = Account.objects.get(username='matrr_admin').email
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
			
	

if settings.PRODUCTION:
	send_pending_reviews_info()
