import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.core.mail import send_mail
from matrr.models import Shipment
from datetime import date, timedelta


def urge_progress_reports():
    today = date.today()
    days90 = timedelta(days = 90)
    limit_date = today - days90
    ship_to_report = Shipment.objects.filter(shp_shipment_date__lte = limit_date)
    
    for shipment in ship_to_report:
        req = shipment.req_request
        if not req.req_report_asked:
            email = shipment.user.email
    
            recipients = list()
            recipients.append(email)
            
            subject = 'Progress report'
            body = 'Hello, \nthe tissue(s) you requested were shipped on %s. ' % shipment.shp_shipment_date + \
                'Please, submit a 90 day progress report concerning this request.\n' + \
                "\nRequest overview:\n\n%s\n" % req.print_setf_in_detail() + \
                "\nYours sincerely,\n\nMatrr team\n\n" + \
                'This is an automated message.\n'
               
            ret = send_mail(subject, body, email, recipient_list=recipients, fail_silently=False)
            print "Urge progress report: reqest_id=%d date=%s success=%d" % (req.req_request_id, today, ret)
            req.req_report_asked = True
            req.save()

urge_progress_reports()