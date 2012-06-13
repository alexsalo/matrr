import re
import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.query_utils import Q
from matrr.models import RequestStatus, Request
from matrr.emails import send_shipment_ready_notification

def shipments_ready():
	assay_ready = False
	send_email = False
	accepted = Q(req_status__in=[RequestStatus.Partially, RequestStatus.Accepted]) # Requests that have been accepted
	accepted = Request.objects.filter(accepted)
	for req in accepted:
		if req.can_be_shipped():
			send_email = True
			if 'assay' in req.cohort.coh_cohort_name.lower():
				assay_ready = True

	return send_email, assay_ready

send_email, assay_ready = shipments_ready()
if settings.PRODUCTION and send_email:
	send_shipment_ready_notification(assay_ready=assay_ready)

