from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from settings import PRODUCTION
from matrr import gizmo, emails
from matrr.forms import TissueShipmentForm, TrackingNumberForm
from matrr.models import Request, User, Shipment, ShipmentStatus, RequestStatus


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipping_history(request):
#	Shipped Requests
    shipped_requests = Request.objects.shipped().order_by('-shipments__shp_shipment_date').distinct()
    recently_shipped = shipped_requests[0:5]
    users_with_shipments = shipped_requests.values_list('user', flat=True)
    user_list = User.objects.filter(pk__in=users_with_shipments).order_by('username')
    user_list = ((user, shipped_requests.filter(user=user).count()) for user in user_list)
    return render_to_response('matrr/shipping/shipping_history.html',
                              {'recently_shipped': recently_shipped, 'user_list': user_list},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipping_history_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    shipped_requests = Request.objects.shipped().filter(user=user).order_by('-shipments__shp_shipment_date').distinct()
    return render_to_response('matrr/shipping/shipping_history_user.html',
                              {'user': user, 'shipped_requests': shipped_requests},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment') or u.has_perm('matrr.ship_genetics'),
                  login_url='/denied/')
def shipping_overview(request):
    #Requests Pending Shipment
    accepted_requests = Request.objects.none()
    for req_request in Request.objects.accepted_and_partially().order_by('req_request_date'):
        if req_request.is_missing_shipments():
            if request.user.has_perm('matrr.change_shipment') or (
                req_request.contains_genetics() and request.user.has_perm('matrr.ship_genetics')):
                accepted_requests |= Request.objects.filter(pk=req_request.pk)
    # Pending Shipments
    pending_shipments = Shipment.objects.none()
    if request.user.has_perm('matrr.change_shipment'):
        pending_shipments |= Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Unshipped)
    if request.user.has_perm('matrr.ship_genetics'):
        pending_shipments |= Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Genetics)
    # Shipped Shipments
    shipped_shipments = Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Shipped).exclude(
        req_request__req_status=RequestStatus.Shipped)

    return render_to_response('matrr/shipping/shipping_overview.html',
                              {'accepted_requests': accepted_requests,
                               'pending_shipments': pending_shipments,
                               'shipped_shipments': shipped_shipments, },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipment_creator(request, req_request_id):
    req_request = get_object_or_404(Request, pk=req_request_id)
    acc_rtt_wo_shipment = req_request.tissue_request_set.filter(shipment=None).exclude(accepted_monkeys=None)

    if request.method == 'POST':
        tissue_shipment_form = TissueShipmentForm(acc_rtt_wo_shipment, data=request.POST)
        if tissue_shipment_form.is_valid():
            # Do sanity checks
            if not req_request.can_be_shipped(): # do a sanity check
                messages.warning(request,
                                 "A request can only be shipped if all of the following are true:\
                                      1) the request has been accepted and not yet shipped, \
                                      2) user has submitted a Purchase Order number, \
                                      3) User has submitted a valid MTA, \
                                      4) User has no pending research update requests.")
                return redirect(reverse('shipment-creator', args=[req_request_id]))
            else:
                # Do not allow the user to create a shipment with both tissues and genetics
                contains_genetics = False
                contains_tissues = False
                for rtt in tissue_shipment_form.cleaned_data['tissue_requests']:
                    _genetics = rtt.contains_genetics()
                    contains_genetics = contains_genetics or _genetics
                    contains_tissues = contains_tissues or not _genetics
                    if contains_genetics and contains_tissues:
                        messages.error(request,
                                       "You cannot send tissues and genetics in the same shipment.  DNA/RNA tissue shipments must be built and shipped separately.")
                        return render_to_response('matrr/shipping/shipment_creator.html',
                                                  {'req_request': req_request,
                                                   'tissue_shipment_form': tissue_shipment_form},
                                                  context_instance=RequestContext(request))

                shipment = Shipment()
                shipment.user = request.user
                shipment.req_request = req_request
                shipment.save()
                for rtt in tissue_shipment_form.cleaned_data['tissue_requests']:
                    rtt.shipment = shipment
                    rtt.save()
            return redirect(reverse('shipment-detail', args=[shipment.pk]))
        else:
            messages.error(request,
                           "There was an error processing this form.  If this continues to occur please notify a MATRR admin.")

    tissue_shipment_form = TissueShipmentForm(acc_rtt_wo_shipment)
    return render_to_response('matrr/shipping/shipment_creator.html',
                              {'req_request': req_request, 'tissue_shipment_form': tissue_shipment_form},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipment_detail(request, shipment_id):
    confirm_ship = False
    confirm_delete_shipment = False

    shipment = get_object_or_404(Shipment, pk=shipment_id)
    req_request = shipment.req_request

    if req_request.req_status != RequestStatus.Shipped or shipment.shp_shipment_date is None:
        edit = True
    else:
        edit = False

    tracking_number = shipment.shp_tracking
    tracking_form = TrackingNumberForm(instance=shipment)
    if request.method == 'POST':
        if 'tracking' in request.POST:
            tracking_form = TrackingNumberForm(instance=shipment, data=request.POST)
            if tracking_form.is_valid():
                tracking_form.save()
                messages.success(request, "Tracking number has been saved.")

        if 'ship' in request.POST:
            confirm_ship = True
            messages.info(request, "This request is ready to ship.  If this shipment has been shipped, click the ship button again to confirm. \
            An email notifying %s, billing, and MATRR admins of this shipment will be sent." % req_request.user.username)
        if 'confirm_ship' in request.POST:
            try:
                shipment_status = shipment.ship_to_user(request.user)
            except PermissionDenied as pd:
                messages.error(request, str(pd))
            else:
                if shipment_status == ShipmentStatus.Shipped:
                    messages.success(request, "Shipment #%d has been shipped." % shipment.pk)
                    if PRODUCTION:
                        emails.send_po_manifest_upon_shipment(shipment)
                        emails.notify_user_upon_shipment(shipment)
                if shipment_status == ShipmentStatus.Genetics:
                    messages.success(request,
                                     "Shipment #%d has been sent to the DNA processing facility." % shipment.pk)
                req_request.ship_request()
                return redirect(reverse('shipping-overview'))

        if 'delete_shipment' in request.POST:
            if shipment.shp_shipment_status == ShipmentStatus.Genetics:
                messages.warning(request, "You cannot delete a shipment once it has been sent for genetics processing.")
            else:
                messages.warning(request,
                                 "Are you sure you want to delete this shipment?  You will have to recreate it before shipping the tissue.")
                confirm_delete_shipment = True
                messages.info(request,
                              "If you are certain you want to delete this shipment, click the delete button again to confirm.")
        if 'confirm_delete_shipment' in request.POST:
            messages.success(request, "Shipment %d deleted." % shipment.pk)
            shipment.delete() # super important that TissueRequest.shipment FK is set to on_delete=SET_NULL
            return redirect(reverse('shipping-overview'))

    return render_to_response('matrr/shipping/shipment_details.html', {'req_request': req_request,
                                                                       'shipment': shipment,
                                                                       'tracking_form': tracking_form,
                                                                       'confirm_ship': confirm_ship,
                                                                       'confirm_delete_shipment': confirm_delete_shipment,
                                                                       'edit': edit,
                                                                       'tracking_number': tracking_number},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_shipment'), login_url='/denied/')
def shipment_manifest_export(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    req_request = shipment.req_request
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=shipment_manifest-' + \
                                      str(req_request.user) + '-' + \
                                      str(req_request.pk) + '.pdf'

    context = {'shipment': shipment, 'req_request': req_request, 'account': req_request.user.account,
               'time': datetime.today()}
    return gizmo.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=response)


