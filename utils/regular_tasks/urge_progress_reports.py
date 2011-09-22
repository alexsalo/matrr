import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.core.mail import send_mail
from matrr.models import Shipment, Request
from datetime import date, timedelta
from django.contrib.auth.models import User

def urge_progress_reports():
    today = date.today()
    days90 = timedelta(days = 90)
    limit_date = today - days90
    ship_to_report_req = Shipment.objects.filter(shp_shipment_date__lte = limit_date,
             req_request__req_report_asked=False).values('req_request','user','shp_shipment_date')
    
    
    for shipment in ship_to_report_req:
        email = User.objects.get(id= shipment['user']).email

        recipients = list()
        recipients.append(email)
        req = Request.objects.get(req_request_id= shipment['req_request'])
        
        subject = 'Progress report'
        body = 'Hello, \nthe tissue(s) you requested were shipped on %s. ' % shipment['shp_shipment_date'] + \
            'Please, submit a 90 day progress report concerning this request.\n' + \
            "\nRequest overview:\n\n%s\n" % req.print_setf_in_detail() + \
            "\nYours sincerely,\n\nMatrr team\n\n" + \
            'This is an automated message.\n'
           
        ret = send_mail(subject, body, email, recipient_list=recipients, fail_silently=False)
        req.req_report_asked = True
        req.save()

urge_progress_reports()