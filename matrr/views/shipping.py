from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr import gizmo, emails
from matrr.forms import TissueShipmentForm, TrackingNumberForm
from matrr.models import Request, User, Shipment, ShipmentStatus, RequestStatus


@user_passes_test(lambda u: u.has_perm('matrr.process_shipments') or u.has_perm('matrr.handle_shipments'), login_url='/denied/')
def shipping_status(request):
    shipments = Shipment.objects.all().order_by('-shp_shipment_date', '-shp_processed', '-shp_processing', '-shp_created_at')
    count_per_page = 25
    if shipments.count() > count_per_page:
        page_obj = gizmo.create_paginator_instance(request=request, queryset=shipments, count=count_per_page)
        shipment_list = page_obj.object_list
    else:
        page_obj = None
        shipment_list = shipments
    return render_to_response('matrr/shipping/shipping_status.html',
                              {'shipments': shipment_list, 'page_obj': page_obj},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.process_shipments') or u.has_perm('matrr.handle_shipments'), login_url='/denied/')
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


@user_passes_test(lambda u: u.has_perm('matrr.process_shipments') or u.has_perm('matrr.handle_shipments'), login_url='/denied/')
def shipping_history_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    shipped_requests = Request.objects.shipped().order_by('pk').filter(user=user)
    return render_to_response('matrr/shipping/shipping_history_user.html',
                              {'user': user, 'shipped_requests': shipped_requests},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.process_shipments') or u.has_perm('matrr.handle_shipments'),login_url='/denied/')
def shipping_overview(request):
    #Requests Pending Shipment
    accepted_requests = Request.objects.none()
    for req_request in Request.objects.accepted_and_partially().order_by('req_request_date'):
        if req_request.is_missing_shipments():
            accepted_requests |= Request.objects.filter(pk=req_request.pk)
    # Pending Shipments
    pending_shipments = processing_shipments = Shipment.objects.none()
    if request.user.has_perm('matrr.process_shipments'):
        processing_shipments = Shipment.objects.filter(shp_shipment_status=ShipmentStatus.Processing)
    if request.user.has_perm('matrr.handle_shipments'):
        pending_shipments = Shipment.objects.filter(shp_shipment_status__in=[ShipmentStatus.Unshipped, ShipmentStatus.Processed])
    return render_to_response('matrr/shipping/shipping_overview.html',
                              {'accepted_requests': accepted_requests,
                               'pending_shipments': pending_shipments,
                               'processing_shipments': processing_shipments, },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.handle_shipments'), login_url='/denied/')
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


@user_passes_test(lambda u: u.has_perm('matrr.handle_shipments'), login_url='/denied/')
def shipment_detail(request, shipment_id):
    confirm_ship = False
    confirm_delete_shipment = False

    shipment = get_object_or_404(Shipment, pk=shipment_id)
    initial_shp_status = shipment.shp_shipment_status
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
            if shipment.can_be_shipped():
                try:
                    shipment.ship_to_user(request.user)
                except Exception as e:
                    messages.error(request, str(e))
            elif shipment.needs_processing():
                try:
                    shipment.send_shipment_for_processing(request.user)
                except Exception as e:
                    messages.error(request, str(e))
            else:
                # I don't want it to be able to hit both, in the (impossible) event that the shipment both can be shipped and also needs processing.
                pass
            shipment_status = shipment.shp_shipment_status
            if initial_shp_status != shipment_status:
                if shipment_status == ShipmentStatus.Shipped:
                    messages.success(request, "Shipment #%d has been shipped." % shipment.pk)
                if shipment_status == ShipmentStatus.Processing:
                    messages.success(request, "The DNA processing facility has been notified that Shipment #%d is in their freezer." % shipment.pk)
                return redirect(reverse('shipping-overview'))

        if 'delete_shipment' in request.POST:
            messages.warning(request, "Are you sure you want to delete this shipment?  You will have to recreate it before shipping the tissue.")
            confirm_delete_shipment = True
            messages.info(request, "If you are certain you want to delete this shipment, click the delete button again to confirm.")
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


@user_passes_test(lambda u: u.has_perm('matrr.process_shipments') or u.has_perm('matrr.handle_shipments'), login_url='/denied/')
def shipment_manifest_export(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    req_request = shipment.req_request
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=shipment_manifest-' + \
                                      str(req_request.user) + '-' + \
                                      str(req_request.pk) + '.pdf'

    context = {'shipment': shipment, 'req_request': req_request, 'account': req_request.user.account,
               'time': datetime.today()}
    return gizmo.export_template_to_pdf('pdf_templates/shipment_manifest.html', context, outfile=response)


@user_passes_test(lambda u: u.has_perm('matrr.process_shipments'), login_url='/denied/')
def shipment_processing(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    req_request = shipment.req_request

    if request.method == 'POST' and 'process' in request.POST:
        shipment.process_shipment(request.user)
        messages.info(request, "Users in the ShipmentProcessors group will be notified these tissues are processed.  Thank you %s :)" % request.user.first_name)
    return render_to_response('matrr/shipping/shipment_processing.html', {'req_request': req_request, 'shipment': shipment,}, context_instance=RequestContext(request))


