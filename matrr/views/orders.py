from datetime import datetime
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages
from django.forms import widgets
from matrr import gizmo
from matrr.decorators import user_owner_test
from matrr.forms import PurchaseOrderForm, CohortSelectForm, CartCheckoutForm, TissueRequestForm
from matrr.models import Request, RequestStatus, Acceptance, Cohort, TissueRequest

def orders_list(request):
    # get a list of all requests for the user
    orders = Request.objects.processed().filter(user=request.user).order_by('-req_request_date')
    revised = Request.objects.revised_or_duplicated().filter(user=request.user)
    order_list = gizmo.create_paginator_instance(request, orders, 20)
    return render_to_response('matrr/orders/orders.html', {'order_list': order_list, 'revised': revised,},
                              context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user or u.has_perm('matrr.change_shipment') or  u.has_perm('matrr.ship_genetics'), arg_name='req_request_id', redirect_url='/denied/')
def order_detail(request, req_request_id, edit=False):
    # get the request
    req_request = Request.objects.get(req_request_id=req_request_id)
    shipments = req_request.get_shipments()
    is_eval = req_request.is_evaluated()
    po_form = ''
    if not req_request.req_status == 'SH' and not req_request.req_status == 'RJ':
        if request.user == req_request.user or request.user.has_perm('matrr.provide_po_number'):
            po_form = PurchaseOrderForm(instance=req_request)
        if request.method == 'POST':
            _prev_shippable = req_request.can_be_shipped()
            po_form = PurchaseOrderForm(instance=req_request, data=request.POST)
            if po_form.is_valid():
                po_form.save()
                messages.success(request, "Purchase Order number has been saved.")
                if not _prev_shippable and req_request.can_be_shipped():  # couldn't be shipped, but now can
                    from matrr.emails import send_shipment_ready_notification
                    send_shipment_ready_notification()
            else:
                messages.error(request,
                               "Purchase Order form invalid, please try again.  Please notify a MATRR admin if this message is erroneous.")
    if request.GET.get('export', False):
        #Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=Invoice-%d.pdf' % req_request.pk
        context = {'req_request': req_request, 'account': req_request.user.account, 'time': datetime.today()}
        gizmo.export_template_to_pdf('pdf_templates/invoice.html', context, outfile=response)
        return response

    return render_to_response('matrr/orders/order_detail.html',
                              {'order': req_request,
                               'Acceptance': Acceptance,
                               'RequestStatus': RequestStatus,
                               'shipped': req_request.is_shipped(),
                               'shipments': shipments,
                               'after_submitted': is_eval,
                               'edit': edit,
                               'po_form': po_form,
                              },
                              context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_revise(request, req_request_id):
    req = Request.objects.get(req_request_id=req_request_id)
    if not req.can_be_revised():
        raise Http404('This page does not exist.')
    return render_to_response('matrr/orders/order_revise.html', {'req_id': req_request_id},
                              context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_revise_confirm(request, req_request_id):
    req = Request.objects.get(req_request_id=req_request_id)
    if not req.can_be_revised() or not request.POST or request.POST['submit'] != "duplicate":
        raise Http404('This page does not exist.')
    req.create_revised_duplicate()
    messages.success(request, 'A new editable copy has been created. You can find it under Revised Orders.')
    return redirect(reverse('order-list'))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_duplicate(request, req_request_id):
    req = Request.objects.get(req_request_id=req_request_id)
    if not req.can_be_duplicated():
        raise Http404('This page does not exist.')

    tissues = list() # Tissues to be duplicated,
    for rtt in req.tissue_request_set.all():
        if rtt.accepted_monkeys.all(): # only test tissues with accepted monkeys.  Rejected tissues won't be duplicated anyway
            if rtt.accepted_monkeys.all().count() == req.cohort.monkey_set.all().count():
                tissues.append(rtt.tissue_type)

    queryset = Cohort.objects.nicotine_filter(request.user).exclude(pk=req.cohort.pk).order_by('coh_cohort_name')
    return render_to_response('matrr/orders/order_duplicate.html', {'req_id': req_request_id,
                                                                   'cohort_form': CohortSelectForm(
                                                                       subject_queryset=queryset,
                                                                       subject_widget=widgets.Select)},
                              context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_duplicate_confirm(request, req_request_id):
    req = Request.objects.get(req_request_id=req_request_id)
    if not req.can_be_duplicated() or not request.POST or request.POST['submit'] != "duplicate":
        raise Http404('This page does not exist.')

    cohort_form = CohortSelectForm(data=request.POST)
    if cohort_form.is_valid():
        coh = cohort_form.cleaned_data['subject']
        req.create_duplicate(coh)
        messages.success(request, 'A new editable copy has been created. You can find it under Revised Orders.')
    else:
        messages.error(request, "Invalid form")
        return redirect(reverse('order-duplicate'))
    return redirect(reverse('order-list'))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_edit(request, req_request_id):
    req = Request.objects.get(req_request_id=req_request_id)
    if not req.can_be_edited():
        raise Http404('This page does not exist.')

    return order_detail(request, req_request_id=req_request_id, edit=True)


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_delete(request, req_request_id):
    req_request = Request.objects.get(req_request_id=req_request_id)
    #	if req_request.user != request.user:
    #		# tissue requests can only be deleted by the
    #		# user who made the tissue request.
    #		raise Http404('This page does not exist.')

    if req_request.is_evaluated():
        messages.error(request, "You cannot delete an order which has been accepted/rejected.")
        return redirect(reverse('order-list'))
    if req_request.can_be_edited():
        edit = True
    else:
        edit = False

    if request.POST:
        if request.POST['submit'] == 'yes':
            req_request.delete()
            messages.success(request, 'The order was deleted.')
        else:
            messages.info(request, 'The order was not deleted.')
        return redirect(reverse('order-list'))
    else:
        return render_to_response('matrr/orders/order_delete.html',
                                  {'order': req_request,
                                   'Acceptance': Acceptance,
                                   'edit': edit},
                                  context_instance=RequestContext(request))


@user_owner_test(lambda u, req_id: u == Request.objects.get(req_request_id=req_id).user, arg_name='req_request_id', redirect_url='/denied/')
def order_checkout(request, req_request_id):
    # get the context (because it loads the cart as well)
    req = Request.objects.get(req_request_id=req_request_id)
    if not req.can_be_edited():
        raise Http404('This page does not exist.')

    if request.method != 'POST':
        checkout_form = CartCheckoutForm(instance=req)

        return render_to_response('matrr/cart/cart_checkout.html',
                                  {'form': checkout_form, 'edit': True, 'cart_exists': True, 'cart_num_items': 1},
                                  context_instance=RequestContext(request))
    else:
        data = request.POST.copy()
        data['user'] = req.user.id
        data['req_status'] = req.req_status
        data['cohort'] = req.cohort.coh_cohort_id
        checkout_form = CartCheckoutForm(request.POST, request.FILES, instance=req)

        if checkout_form.is_valid() and request.POST['submit'] == 'checkout':
            req.req_experimental_plan = checkout_form.cleaned_data['req_experimental_plan']
            req.req_notes = checkout_form.cleaned_data['req_notes']
            req.submit_request()
            req.req_request_date = datetime.now()
            req.save()
            messages.success(request, 'Tissue Request Submitted.')
            return redirect('order-list')
        else:
            return render_to_response('matrr/cart/cart_checkout.html',
                                      {'form': checkout_form, 'edit': True, 'cart_exists': True, 'cart_num_items': 1},
                                      context_instance=RequestContext(request))


@user_owner_test(lambda u, rtt_id: u == TissueRequest.objects.get(rtt_tissue_request_id=rtt_id).req_request.user, arg_name='req_rtt_id', redirect_url='/denied/')
def order_delete_tissue(request, req_rtt_id):
    rtt = TissueRequest.objects.get(rtt_tissue_request_id=req_rtt_id)
    if not rtt.req_request.can_be_edited() or not request.POST or request.POST['submit'] != "delete":
        raise Http404('This page does not exist.')
    rtt.delete()
    messages.success(request, 'Tissue request deleted.')
    return redirect(reverse('order-edit', args=[rtt.req_request.req_request_id, ]))


@user_owner_test(lambda u, rtt_id: u == TissueRequest.objects.get(rtt_tissue_request_id=rtt_id).req_request.user, arg_name='req_rtt_id', redirect_url='/denied/')
def order_edit_tissue(request, req_rtt_id):
    rtt = TissueRequest.objects.get(rtt_tissue_request_id=req_rtt_id)
    if not rtt.req_request.can_be_edited():
        raise Http404('This page does not exist.')

    if request.method != 'POST': #or request.POST['submit'] == 'edit':
        # create a form so the item can be edited
        tissue_request_form = TissueRequestForm(instance=rtt,
                                                req_request=rtt.req_request,
                                                tissue=rtt.get_tissue())
        return render_to_response('matrr/orders/orders_tissue_edit.html', {'form': tissue_request_form,
                                                                          'cohort': rtt.req_request.cohort,
                                                                          'tissue': rtt.get_tissue(),
                                                                          'cart_item': rtt, },
                                  context_instance=RequestContext(request))
    else:
        if request.POST['submit'] == 'cancel':
            messages.info(request, 'No changes were made.')
            return redirect(reverse('order-edit', args=[rtt.req_request.req_request_id, ]))
        elif request.POST['submit'] == 'delete':
            return order_delete_tissue(request,
                                       req_rtt_id=req_rtt_id) # order_delete_tissue's decorator looks for this as a kwarg, not an arg.  The URL passes the function a kwarg.
        else:
            # validate the form and update the cart_item
            tissue_request_form = TissueRequestForm(instance=rtt,
                                                    data=request.POST,
                                                    req_request=rtt.req_request,
                                                    tissue=rtt.get_tissue())
            if tissue_request_form.is_valid():
                # the form is valid, so update the tissue request
                tissue_request_form.save()
                messages.success(request, 'Tissue request updated.')
                return redirect(reverse('order-edit', args=[rtt.req_request.req_request_id, ]))
            else:
                return render_to_response('matrr/orders/orders_tissue_edit.html', {'form': tissue_request_form,
                                                                                  'cohort': rtt.req_request.cohort,
                                                                                  'tissue_type': rtt.get_tissue(),
                                                                                  'cart_item': rtt, },
                                          context_instance=RequestContext(request))




