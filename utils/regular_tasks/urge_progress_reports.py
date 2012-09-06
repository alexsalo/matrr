import sys, os

project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)
from datetime import datetime
from django.core.mail import send_mail
from matrr.models import Shipment, Request, Account
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse


def report_overdue_shipment():
	from_email = Account.objects.get(user__username='matrr_admin').email
	recipients = [user.email for user in Group.objects.get(name='Uberuser').user_set.all()]
	subject = 'Overdue Progress Report'
	body = "Yo yo,\n\nWe have some users who haven't given us a research update.  Click the link below to see who's slacking off.\n\n"
	body += 'http://gleek.ecs.baylor.edu' + reverse('rud-overdue')

	ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
	if ret > 0:
		print "%s Overdue research update notification sent" % datetime.now().strftime("%Y-%m-%d,%H:%M:%S")

def urge_progress_reports():
	today = date.today()
	days90 = timedelta(days = 90)
	limit_date = today - days90
	ship_to_report_req = Shipment.objects.filter(shp_shipment_date__lte = limit_date, req_request__rud_set=None)

	for shipment in ship_to_report_req.values('req_request','user','shp_shipment_date'):
		from_email = Account.objects.get(user__username='matrr_admin').email
		email = User.objects.get(id= shipment['user']).email

		recipients = list()
		recipients.append(email)
		req = Request.objects.get(req_request_id= shipment['req_request'])

		subject = 'Progress Report'
		body = 'Hello, \nthe tissue(s) you requested were shipped on %s. ' % shipment['shp_shipment_date'] + \
			'Please, submit a 90 day progress report concerning this request on My Account page, section Research Updates.\n' + \
			"\nRequest overview:\n\n%s\n" % req.print_self_in_detail() + \
			"\nYours sincerely,\n\nMatrr team\n\n" + \
			'This is an automated message.\n'

		ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
		req.req_report_asked_count += 1
		req.save()
		if ret > 0:
			print "%s Report urged for request: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), `req`)

	way_overdues = ship_to_report_req.filter(req_request__req_report_asked_count__gte=2)
	if way_overdues.count() and today.isocalendar()[1] % 2 == 0: # there exist overdue updates, and today is an even week of the year
		report_overdue_shipment()


if settings.PRODUCTION:
	urge_progress_reports()