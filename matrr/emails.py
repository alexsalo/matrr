import re
from datetime import datetime, timedelta, date

from django.contrib.auth.models import Permission
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.models import Group

from matrr import gizmo
from matrr import settings
from matrr.models import Request, User, Shipment, Account, RequestStatus, Acceptance, Review, DataSymposium


# regular_tasks
def send_colliding_requests_info():
    """
    If there are colliding requests (tissue requests for the same monkey:tissue) in the last day,
    this cron task will email users with permission 'can_receive_colliding_requests_email'
    which requests are colliding
    """
    time_now = datetime.now()
    time_yesterday = time_now - timedelta(days=1)
    requests = Request.objects.submitted().filter(req_request_date__gte=time_yesterday,
                                                  req_request_date__lte=time_now).exclude(user__username='matrr_admin')

    collisions = list()
    for request in requests:
        acc_coll = request.get_acc_req_collisions()
        sub_coll = request.get_sub_req_collisions()
        if acc_coll or sub_coll:
            collisions.append((request, sub_coll, acc_coll))

    if len(collisions) > 0:
        users = Account.objects.users_with_perm('can_receive_colliding_requests_email')
        collision_text = ""
        for req, sub, acc in collisions:

            sub_text = ""
            if sub:
                sub_text = "	has collision with following submitted requests:\n"
                for s in sub:
                    sub_text += ("		%s\n" % s)
            acc_text = ""
            if acc:
                acc_text = "	has collision with following accepted requests:\n"
                for a in acc:
                    acc_text += ("		%s\n" % a)

            collision_text = collision_text + ("Request: %s\n" % req) + sub_text + acc_text
        subject = 'Submitted requests with collisions'
        body = 'Information from matrr.com\nSome requests were submitted during the last 24 hours which collide with other requests.\n' + \
               collision_text + \
               'Please, do not respond. This is an automated message.\n'

        from_email = Account.objects.get(user__username='matrr_admin').email
        for user in users:
            email = user.email
            recipients = list()
            recipients.append(email)

            if settings.PRODUCTION and settings.ENABLE_EMAILS:
                ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
                if ret > 0:
                    print "%s Colliding requests info sent for user: %s" % (
                    datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# regular_tasks
def send_verify_tissues_info():
    """
    If there are submitted requests which need tissue verification, this cron task will email users who have permission to verify tissue that they need to do so.
    """
    users = Account.objects.users_with_perm('receive_verify_tissues_email')
    time_now = datetime.now()
    time_yesterday = time_now - timedelta(days=1)
    requests = Request.objects.submitted().filter(req_request_date__gte=time_yesterday, req_request_date__lte=time_now)
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
            body = 'Information from matrr.com\n During the last 24 hours new request(s) has (have) been submitted. Your account %s can verify tissues. Please, find some time to do so.\n' % user.username + \
                   'Please, do not respond. This is an automated message.\n'

            if settings.PRODUCTION and settings.ENABLE_EMAILS:
                ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
                if ret > 0:
                    print "%s Verify tissues info sent for user: %s" % (
                    datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

    # Send emails only to jim and april for assay requests.  Because assay requests are special....
    assay_requests = Request.objects.submitted().filter(req_modified_date__gte=time_yesterday,
                                                        req_modified_date__lte=time_now)
    assay_requests = assay_requests.exclude(user__username='matrr_admin')
    assay_requests = assay_requests.filter(cohort__coh_cohort_name__icontains='assay')

    if len(assay_requests) > 0:
        from_email = Account.objects.get(user__username='matrr_admin').email
        for user in [Account.objects.get(user__username='jdaunais'), Account.objects.get(user__username='adaven')]:
            email = user.email
            recipients = list()
            recipients.append(email)
            subject = 'Assay Tissues to be verified'
            body = 'Information from matrr.com\n'
            body += 'During the last 24 hours new request(s) has (have) been submitted. Your account %s can verify tissues. Please, find some time to do so.\n' % user.username
            body += 'Please, do not respond. This is an automated message.\n'

            if settings.PRODUCTION and settings.ENABLE_EMAILS:
                ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
                if ret > 0:
                    print "%s Verify tissues info sent for user: %s" % (
                    datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# regular_tasks
def urge_po_mta():
    """
    If a user has submitted a requests, but have not submitted a Purchase Order, or have not agreed to an MTA, the user will be emailed, informing them that they must do these things before
    the tissue can ship
    """
    from_email = Account.objects.get(user__username='matrr_admin').email
    accepted = Request.objects.accepted_and_partially()
    for req in accepted:
        if req.req_purchase_order and req.user.account.has_mta():
            continue

        to_email = req.user.email
        recipients = list()
        recipients.append(to_email)

        if req.req_status == RequestStatus.Accepted:
            email_template = 'matrr/review/request_accepted_email.txt'
        elif req.req_status == RequestStatus.Partially:
            email_template = 'matrr/review/request_partially_accepted_email.txt'
        else:
            print "How did you get here?! urge_po_mta trap"
            raise Exception('How did you get here?! urge_po_mta trap')

        request_url = reverse('order-detail', args=[req.req_request_id])
        body = render_to_string(email_template,
                                {'request_url': request_url, 'req_request': req, 'Acceptance': Acceptance})
        body = re.sub('(\r?\n){2,}', '\n\n', body)

        if not req.req_purchase_order and not req.user.account.has_mta():
            matrr_needs = "your MTA and Purchase Order Number"
        else:
            if not req.req_purchase_order:
                matrr_needs = "your Purchase Order Number"
            else: # because of the continue at the top of the loop the only remaining option is it's missing a PO number
                matrr_needs = "your MTA"

        subject = "MATRR needs %s before request %s can be shipped." % (matrr_needs, str(req.pk))

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
            if ret > 0:
                print "%s PO/MTA urged for request: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), `req`)

# regular_tasks
def urge_progress_reports():
    """
    When users request tissue, they agree to submit progress reports on science done with the tissues.  Ninety days after the tissue has shipped, this progress report is due and they begin
    receiving these emails, notifying them that the reports are overdue.

    Additionally, if there are users whose reports are way overdue (>= 2 weeks overdue), the MATRR Uberusers are notified that we have research updates which are way overdue.
    """
    way_overdue = False
    shipped_requests = Request.objects.shipped()
    for req in shipped_requests:
        if not req.is_rud_overdue() or not req.user.is_active:
            continue
        else:
            way_overdue = way_overdue or req.get_rud_weeks_overdue() >= 2
        from_email = Account.objects.get(user__username='matrr_admin').email
        recipients = [req.user.email, ]

        shipment_date = req.shipments.order_by('-shp_shipment_date')[0].shp_shipment_date
        subject = 'Progress Report'
        body = 'Hello, \n'
        body += 'the tissue(s) you requested were shipped on %s. ' % str(shipment_date)
        body += 'Please, submit a progress report concerning this request using this link: http://gleek.ecs.baylor.edu%s\n' % reverse('rud-upload')
        body += "\n"
        body += "Request overview:\n\n%s\n" % req.print_self_in_detail()
        body += "\n"
        body += "Yours sincerely,\n"
        body += "MATRR team"
        body += "\n\n"
        body += "This is an automated message."

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
            if ret > 0:
                print "%s Report urged for request: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), `req`)

    if way_overdue and date.today().isocalendar()[1] % 2 == 0: # there exist overdue updates, and today is an even week of the year
        from_email = Account.objects.get(user__username='matrr_admin').email
        recipients = [user.email for user in Group.objects.get(name='Uberuser').user_set.all()]
        subject = 'Overdue Progress Report'
        body = "We have some users who haven't given us a research update.  Click the link below to see who's slacking off.\n\n"
        body += 'http://gleek.ecs.baylor.edu' + reverse('rud-overdue')

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
            if ret > 0:
                print "%s Overdue research update notification sent" % datetime.now().strftime("%Y-%m-%d,%H:%M:%S")

# regular_tasks
def send_pending_reviews_info():
    """
    Send an email, once a week, to reviewers who have pending reviews
    """
    users = Account.objects.users_with_perm('can_receive_pending_reviews_info')
    from_email = Account.objects.get(user__username='matrr_admin').email
    for user in users:
        reviews = Review.objects.filter(user=user.id).filter(req_request__req_status=RequestStatus.Submitted).exclude(
            req_request__user__username='matrr_admin')
        unfinished_reviews = [review for review in reviews if not review.is_finished()]
        if len(unfinished_reviews) > 0:

            email = user.email
            recipients = list()
            recipients.append(email)
            subject = 'Pending requests'
            body = 'Information from matrr.com\n You have pending request(s) to be reviewed on your account: %s \n' % user.username + \
                   'Please, do not respond. This is an automated message.\n'

            if settings.PRODUCTION and settings.ENABLE_EMAILS:
                ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
                if ret > 0:
                    print "%s Pending info sent for user: %s" % (
                    datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# used in matrr and utils.regular_tasks
def send_shipment_ready_notification(assay_ready=False):
    """
    Send an email to all users with matrr.change_shipment that there is a request ready to be shipped
    """
    if assay_ready:
        users = [User.objects.get(username='jdaunais'), User.objects.get(username='adaven')]
    else:
        users = Account.objects.users_with_perm('handle_shipments_email')
    from_email = User.objects.get(username='matrr_admin').email
    for user in users:
        email = user.email
        recipients = list()
        recipients.append(email)
        subject = '%sequest is ready to ship' % ('Assay r' if assay_ready else 'R')
        body = 'Click here to see the shipping overview page.\n'
        body += 'http://gleek.ecs.baylor.edu%s\n' % reverse('shipping-overview')
        body += 'Please, do not respond. This is an automated message.\n'

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
            if ret > 0:
                print "%s Shipment info sent to user: %s" % (
                datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# matrr
def send_po_manifest_upon_shipment(shp_shipment):
    """
    Send an email to 'po_manifest_email' users when a shipment is shipped.  This email will contain the shipping manifest (with Purchase Order number).
    """
    if not isinstance(shp_shipment, Shipment):
        shp_shipment = Shipment.objects.get(pk=shp_shipment)

    req_request = shp_shipment.req_request
    perm = Permission.objects.get(codename='po_manifest_email')
    to_list = User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct().values_list(
        'email', flat=True)

    subject = "Shipping Manifest for MATRR request %s." % str(req_request.pk)
    body = "A MATRR shipment has been shipped.  Attached is the shipping manifest for this request, with the customer's Purchase Order number.  Please contact a MATRR admin if there are any issues or missing information."
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, to_list)

    filename = 'manifest_user-%s_shipment-%s.pdf' % (str(req_request.user), str(shp_shipment.pk))
    outfile = open('/tmp/%s' % filename, 'wb')
    context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
    gizmo.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=outfile)

    outfile.close()
    email.attach_file(outfile.name)
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        email.send()

# matrr
def notify_user_upon_shipment(shp_shipment):
    """
    Notify a user, via email, that their tissue request has shipped.
    """
    if not isinstance(shp_shipment, Shipment):
        shp_shipment = Shipment.objects.get(pk=shp_shipment)
    req_request = shp_shipment.req_request
    to_list = [req_request.user.email]

    subject = "MATRR has shipped tissue to %s." % str(req_request.user.username)
    body = "A MATRR shipment has been shipped.  Attached is the shipping manifest for this request.\n"
    body += "\nFedEx Tracking Number:  %s\n" % str(shp_shipment.shp_tracking)
    body += 'Please, do not respond. This is an automated message.\n'

    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, to_list)
    filename = 'manifest_user-%s_shipment-%s.pdf' % (str(req_request.user), str(shp_shipment.pk))
    outfile = open('/tmp/%s' % filename, 'wb')
    context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
    gizmo.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=outfile)

    outfile.close()
    email.attach_file(outfile.name)
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        email.send()

# matrr
def send_jim_hippocampus_notification(req_request):
    """
    Send an email to jim when someone requests a hippocampus
    """
    if not isinstance(req_request, Request):
        req_request = Request.objects.get(pk=req_request)
    jim = User.objects.get(username='jdaunais')
    matrr = User.objects.get(username='matrr_admin')

    subject = 'Yo dude, user %s requested a HIPPOCAMPUS' % req_request.user
    body = 'Hey Jim,\n'
    body += "This is just a frendly remainder that sumone rekwested a hippocampus, which in some way requires your attenshun.\n\n"
    body += 'http://gleek.ecs.baylor.edu%s\n' % reverse('review-overview', args=[req_request.pk])
    body += 'This message is very, extremely automated.  Have a nice day!\n\n'
    body += 'Sincerely,\n'
    body += 'MATRR'

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        ret = send_mail(subject, body, matrr.email, recipient_list=[jim.email, ], fail_silently=False)
        if ret > 0:
            print "%s Hippocampus notification sent to %s." % (
            datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), jim.username)

# matrr
def send_verify_new_account_email(account):
    """
    When a new user signs up for a MATRR account, there is a 2-stage verification process.

    The first stage is handled by django_auth, which verifies the user's email address.
    The second stage is handled here.  All users must be verified by matrr_admin as a real human researcher.  This will send an email to him holding information about the user and two links.

    One link will verify the user's account, granting access to all public-facing facets of the website.  There are several parts of the site which are further permission-restricted, but
    now the user can submit tissue requests.
    The second link will delete the user's (presumably fake) account.

    There is (presently) no other interface for this process, except direct DB access.
    """

    body = "New account was created.\n" + \
           "\t username: %s\n" % account.user.username + \
           "\t first name: %s\n" % account.user.first_name + \
           "\t last name: %s\n" % account.user.last_name + \
           "\t e-mail: %s\n" % account.user.email + \
           "\t phone number: %s\n" % account.phone_number + \
           "\t institution: %s\n" % account.institution + \
           "\t first name: %s\n" % account.user.first_name + \
           "\t address 1: %s\n" % account.act_real_address1 + \
           "\t address 2: %s\n" % account.act_real_address2 + \
           "\t city: %s\n" % account.act_real_city + \
           "\t ZIP code: %s\n" % account.act_real_zip + \
           "\t state: %s\n" % account.act_real_state + \
           "\nTo view account in admin, go to:\n" + \
           "\t http://gleek.ecs.baylor.edu/admin/matrr/account/%d/\n" % account.user.id + \
           "To verify account follow this link:\n" + \
           "\t http://gleek.ecs.baylor.edu%s\n" % reverse('account-verify', args=[account.user.id, ]) + \
           "To delete account follow this link and confirm deletion of all objects (Yes, I'm sure):\n" + \
           "\t http://gleek.ecs.baylor.edu/admin/auth/user/%d/delete/\n" % account.user.id + \
           "All the links might require a proper log-in."
    subject = "New account on www.matrr.com"
    from_e = User.objects.get(username='matrr_admin').email
    to_e = [from_e, ]
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        send_mail(subject, body, from_e, to_e, fail_silently=True)

# matrr
def send_new_request_info(req_request):
    """
    This email is sent upon user submission of a request.  It notifies reviewers of the new request.
    """
    if not settings.PRODUCTION and req_request.user.username != 'matrr_admin':
        print "%s - New request email not sent, settings.PRODUCTION = %s" % (
        datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), str(settings.PRODUCTION))
        return
    req_request = Request.objects.get(pk=req_request.req_request_id)
    users = Account.objects.users_with_perm('can_receive_pending_reviews_info')
    from_email = Account.objects.get(user__username='matrr_admin').email
    for user in users:
        email = user.email
        recipients = list()
        recipients.append(email)
        subject = 'User %s submitted a request for %s tissues from %s.' % (
        req_request.user, req_request.get_requested_tissue_count(), req_request.cohort)
        body = 'More information about this request is available at matrr.com\n' \
               'Please, do not respond. This is an automated message.\n'

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
            if ret > 0:
                print "%s New request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# matrr
def send_verification_complete_notification(req_request):
    """
    This email will notify Erich (matrr_admin) that all tissues for the request have been verified
    """
    from_email = Account.objects.get(user__username='matrr_admin').email
    recipients = [from_email]
    subject = 'Inventory Verified for request %s' % str(req_request.pk)
    body = "Information from matrr.com\n The inventory for %s's request from cohort %s has all been verified.\n" % (
    req_request.user.username, req_request.cohort.coh_cohort_name) + \
           "Please check https://gleek.ecs.baylor.edu%s to see if this request is ready for processing.\n" % reverse(
               'review-overview', args=[req_request.pk, ]) + \
           "Please, do not respond. This is an automated message.\n"

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)

# matrr
def send_processed_request_email(form_data, req_request):
    """
    This email is sent to the user when the request is processed (accepted, partially accepted, or rejected).  If it was not rejected, it will include a PDF of the final invoice.
    """
    subject = form_data['subject']
    body = form_data['body']
    subject = ' '.join(subject.splitlines())
    perm = Permission.objects.get(codename='bcc_request_email')
    bcc_list = User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct().values_list(
        'email', flat=True)
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [req_request.user.email], bcc=bcc_list)
    if req_request.req_status != RequestStatus.Rejected:
        outfile = open('/tmp/MATRR_Invoice-%s.pdf' % str(req_request.pk), 'wb')
        context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
        gizmo.export_template_to_pdf('pdf_templates/invoice.html', context, outfile=outfile)
        outfile.close()
        email.attach_file(outfile.name)
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        email.send()
        if req_request.contains_genetics() and req_request.req_status != RequestStatus.Rejected:
            send_dna_request_details(req_request)

# matrr
def send_contact_us_email(form_data, user):
    """
    This will send an email to matrr_admin based on the form data submitted thru the contact_us page
    """
    subject = ''.join(form_data['email_subject'].splitlines())
    subject += '//'
    try:
        if user.email:
            subject += user.email
    except:
        # Anonymous user does not have email field.
        pass
    email_to = User.objects.get(username='matrr_admin').email
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        send_mail(subject, form_data['email_body'], form_data['email_from'], [email_to])

# matrr
def notify_mta_uploaded(mta):
    """
    Will send an email to 'mta_upload_notification' users that an MTA has been uploaded and awaits verification/processing.
    """
    mta_admins = Account.objects.users_with_perm('mta_upload_notification')
    from_email = Account.objects.get(user__username='matrr_admin').email

    for admin in mta_admins:
        recipients = [admin.email]
        subject = 'User %s has uploaded an MTA form' % mta.user.username
        body = '%s has has uploaded an MTA form.\n' % mta.user.username
        body += 'This MTA can be downloaded here:  http://gleek.ecs.baylor.edu%s.\n' % mta.mta_file.url
        body += 'If necessary you can contact %s with the information below.\n\n' % mta.user.username
        body += "Name: %s %s\nEmail: %s\nPhone: %s \n\n" % (
        mta.user.first_name, mta.user.last_name, mta.user.email, mta.user.account.phone_number)
        body += "If this is a valid MTA click here to update MATRR: http://gleek.ecs.baylor.edu%s" % reverse('mta-list')

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients)
            if ret > 0:
                print "%s MTA verification request sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), admin.username)
    return

# matrr
def send_account_verified_email(account):
    """
    After matrr_admin verifies the new account (with links from the send_verify_new_account_email() email), this email is sent to the user informing them that their account is now active.
    """
    subject = "Account on www.matrr.com has been verified"
    body = "Your account on www.matrr.com has been verified\n" + \
           "\t username: %s\n" % account.user.username + \
           "From now on, you can access pages on www.matrr.com.\n" + \
           "This is an automated message, please, do not respond.\n"

    from_e = account.user.email
    to_e = list()
    to_e.append(from_e)
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        send_mail(subject, body, from_e, to_e, fail_silently=True)

# matrr
def send_mta_uploaded_email(account):
    """
    Notify 'receive_mta_request' users that a user has requests an MTA form
    """
    from_email = Account.objects.get(user__username='matrr_admin').email

    users = Account.objects.users_with_perm('receive_mta_request')
    for user in users:
        recipients = [user.email]
        subject = 'User %s has requested an MTA form' % account.user.username
        body = '%s has indicated he/she is not associated with any of the UBMTA signatories and requested an MTA form.\n' \
               'He/she was told instructions would be provided with the MTA form.  ' \
               'If you cannot contact %s with the information provided below, please notify the MATRR admins.\n' % (
               account.user.username, account.user.username)
        body += "\n\nName: %s %s\nEmail: %s\nPhone: %s" % (
        account.first_name, account.last_name, account.email, account.phone_number)
        body += "\n\nIn addition to any other steps, please have %s upload the signed MTA form to MATRR using this link: http://gleek.ecs.baylor.edu%s" % (
        account.user.username, reverse('mta-upload'))

        if settings.PRODUCTION and settings.ENABLE_EMAILS:
            ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
            if ret > 0:
                print "%s MTA request info sent to user: %s" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), user.username)

# matrr
def send_dna_request_details(req_request):
    """
    This will notify 'process_shipments_email' users that a tissue request has been submitted for DNA/RNA tissue.
    Users should expect to receive tissue samples from which to extract this information.

    They are expected to ship it to the user and notify MATRR of the deed
    """
    from_email = Account.objects.get(user__username='matrr_admin').email
    subject = "A user has requested DNA/RNA"
    body = \
        """
        This email is to notify you that a user has requested tissue DNA- or RNA-fixed tissues from cohort %s.  A tech user will ship the tissues needed for the extraction to you.

        The attached invoice should provide any details required for the extraction.  If you have any questions please contact a MATRR administrator.
        """
    recipients = Account.objects.users_with_perm('process_shipments_email').values_list('email', flat=True)
    email = EmailMessage(subject, body, from_email, recipients)

    outfile = open('/tmp/MATRR_Invoice-%s.pdf' % str(req_request.pk), 'wb')
    context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
    gizmo.export_template_to_pdf('pdf_templates/invoice.html', context, outfile=outfile)
    outfile.close()
    email.attach_file(outfile.name)
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        email.send()

# matrr
def send_rud_data_available_email(rud):
    """
    In the unlikely event that we ever receive a research update informing us that they have data to provide us, this email is what we would see.
    """
    admin = Account.objects.get(user__username='matrr_admin')
    from_email = admin.email

    recipients = [admin.email]
    subject = 'User %s has data for MATRR' % rud.req_request.user.username
    body = "That's right %s, you read that subject line correctly.\n" % admin.username
    body += "\n"
    body += "%s has submitted a research update and indicated there is data ready to be submitted to MATRR.\n" % rud.req_request.user.username
    body += "I told them that MATRR admins would contact them shortly for upload instructions.\n"
    body += "\n"
    body += "You should probably give %s a high-five :)\n" % rud.req_request.user.username

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
        if ret > 0:
            print "%s rud data available email sent to user: %s" % (
            datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), admin.username)

# matrr
def send_rud_complete_email(rud_username):
    """
    In the unlikely event that we ever receive a research update informing us that they have data to provide us, this email is what we would see.
    """
    admin = Account.objects.get(user__username='matrr_admin')
    from_email = admin.email

    recipients = Account.objects.users_with_perm('receive_rud_complete_email')
    recipient_list = [a.email for a in recipients]
    subject = 'User %s has completed his/her research.' % rud_username
    body = "Yo yo,\n"
    body += "That's right %s, you read that subject line correctly.\n" % admin.username
    body += "\n"
    body += "%s has submitted a 'Complete' research update.\n" % rud_username
    body += "Now would be a good time to get some data from the user, before they 'lose' their data.\n"
    body += "\n"
    body += "You should probably give %s a high-five :)\n" % rud_username

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        ret = send_mail(subject, body, from_email, recipient_list=recipient_list, fail_silently=False)
        if ret > 0:
            print "%s rud complete email sent to user: %s" % (
            datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), admin.username)

# matrr
def shipment_sent_for_processing(shipment):
    from_email = Account.objects.get(user__username='matrr_admin').email

    recipients = Account.objects.users_with_perm('process_shipments_email').values_list('email', flat=True)

    subject = "%s has dropped off tissue for MATRR DNA/RNA processing" % shipment.user.username
    email_template = 'matrr/shipping/shipment_processing_email.txt'
    body = render_to_string(email_template, {'shipment': shipment})
    body = re.sub('(\r?\n){2,}', '\n\n', body)

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
        if ret > 0:
            print "%s: Shipment %d sent for DNA/RNA processing" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), shipment.pk)

# matrr
def shipment_processed(shipment):
    from_email = Account.objects.get(user__username='matrr_admin').email

    recipients = Account.objects.users_with_perm('handle_shipments_email').values_list('email', flat=True)

    subject = "%s has dropped off tissue for MATRR DNA/RNA processing" % shipment.user.username
    email_template = 'matrr/shipping/shipment_processed_email.txt'
    body = render_to_string(email_template, {'shipment': shipment})
    body = re.sub('(\r?\n){2,}', '\n\n', body)

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        ret = send_mail(subject, body, from_email, recipient_list=recipients, fail_silently=False)
        if ret > 0:
            print "%s: Email notified that Shipment %d DNA/RNA has been processed" % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), shipment.pk)

# matrr
def dsm_registration_notification(dsm):
    """
    Notify all permissioned users, via email, that a user has registered for the MATRR Data Symposium.
    """
    if not isinstance(dsm, DataSymposium):
        dsm = DataSymposium.objects.get(pk=dsm)
    recipients = Account.objects.users_with_perm('receive_symposium_roster_email')
    to_list = recipients.values_list('email', flat=True)

    subject = "Someone has registered for the MATRR Data Symposium"
    body = "%s %s %s has registered for the symposium.  Click the link below to see more details.\n" % (dsm.dsm_title, dsm.dsm_first_name, dsm.dsm_last_name)
    body += "\n"
    body += 'https://gleek.ecs.baylor.edu%s\n' % reverse('symposium-roster-detail', args=[dsm.pk,])
    body += "\n"
    body += 'Full roster of attendants:  https://gleek.ecs.baylor.edu%s\n' % reverse('symposium-roster')
    body += "\n"
    body += 'Please, do not respond. This is an automated message.\n'

    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, to_list)
    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        email.send()

#matrr
def send_dto_uploaded_email(dto):
    """
    When anyone uploads data to gleek, send an email to appropriate users.
    """
    admin = Account.objects.get(user__username='matrr_admin')
    from_email = admin.email
    recipients = Account.objects.users_with_perm('receive_dto_uploaded_email')
    to_list = recipients.values_list('email', flat=True)
    subject = 'Data uploaded to the MATRR'
    body = "That's right, you read that subject line correctly!\n"
    body += "\n"
    body += "%s has uploaded '%s' data to the MATRR.\n" % (dto.account.user.username, dto.dto_type)
    body += "View uploaded data here:  http://gleek.ecs.baylor.edu%s\n" % reverse('view-dto-data')
    body += "\n"
    body += "You should probably give %s a high-five :)\n" % dto.account.user.username

    if settings.PRODUCTION and settings.ENABLE_EMAILS:
        ret = send_mail(subject, body, from_email, recipient_list=to_list, fail_silently=False)
        if ret > 0:
            print "%s User %s uploaded data." % (datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), dto.account.username)

