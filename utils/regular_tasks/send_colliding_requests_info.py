import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)
from datetime import datetime, timedelta

from django.core.mail import send_mail
from matrr.models import RequestStatus, Request, Account


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
		
		for user in users:
		
			email = user.email
			recipients = list()
			recipients.append(email)
			
		
			ret = send_mail(subject, body, email, recipient_list=recipients, fail_silently=False)
			if ret > 0:
				print "%s Colliding requests info sent for user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)
			
	
if settings.PRODUCTION:
	send_colliding_requests_info()
