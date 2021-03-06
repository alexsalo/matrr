import sys
import os
sys.path.append('/web/www/matrr-prod')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")
import django
django.setup()

from matrr import settings
from matrr.emails import send_shipment_ready_notification

def shipments_ready():
    from django.db.models.query_utils import Q
    from matrr.models import RequestStatus, Request
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

