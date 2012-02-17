from django.core.urlresolvers import reverse
import settings

from django.core.mail import send_mail
from matrr.models import Account


def send_verification_complete_notification(req_request):
	from_email = Account.objects.get(user__username='matrr_admin').email
	recipients = [from_email]
	subject = 'Inventory Verified for request %s'% str(req_request)
	body = "Information from matrr.com\n The inventory for %s's request from cohort %s has all been verified.\n" % (req_request.user.username, req_request.cohort.coh_cohort_name) + \
		   "Please check https://gleek.ecs.baylor.edu%s to see if this request is ready for processing.\n" % reverse('review-overview', args=[req_request.pk,]) + \
		   "Please, do not respond. This is an automated message.\n"

	if settings.PRODUCTION:
		send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
