from datetime import datetime
from django.forms.models import formset_factory
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages
from matrr import gizmo
from matrr.forms import TissueInventoryVerificationForm, TissueInventoryVerificationShippedForm, TissueInventoryVerificationDetailForm
from matrr.models import TissueInventoryVerification, Request


def tissue_verification(request):
    request_ids = TissueInventoryVerification.objects.values_list('tissue_request__req_request')
    requests = Request.objects.filter(req_request_id__in=request_ids).order_by('req_request_date')
    requestless_count = TissueInventoryVerification.objects.filter(tissue_request=None).count()
    return render_to_response('matrr/verification/verification_request_list.html',
                              {
                              'requests': requests,
                              'requestless_count': requestless_count,
                              },
                              context_instance=RequestContext(request))


def tissue_verification_export(request, req_request_id):
    if req_request_id:
        tiv_list = TissueInventoryVerification.objects.filter(
            tissue_request__req_request__req_request_id=req_request_id).order_by('inventory').order_by("monkey")
    else:
        tiv_list = TissueInventoryVerification.objects.filter(tissue_request=None).order_by('inventory').order_by(
            "monkey")

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=TissueVerificationForm.pdf'
    context = {'tiv_list': tiv_list, 'user': request.user, 'date': datetime.today()}
    return gizmo.export_template_to_pdf('pdf_templates/tissue_verification.html', context, outfile=response)


def tissue_verification_list(request, req_request_id):
    if int(req_request_id) is 0:
        return tissue_verification_post_shipment(request)

    TissueVerificationFormSet = formset_factory(TissueInventoryVerificationForm, extra=0)
    if request.method == "POST":
        formset = TissueVerificationFormSet(request.POST)
        if formset.is_valid():
            for tivform in formset:
                data = tivform.cleaned_data
                tiv = TissueInventoryVerification.objects.get(pk=data['primarykey'])
                if data['inventory'] != tiv.tiv_inventory:
                    tiv.tiv_inventory = data['inventory']
                    tiv.save()
            messages.success(request, message="This page of tissues has been successfully updated.")
        else:
            messages.error(request, formset.errors)
    # if request method != post and/or formset isNOT valid
    # build a new formset
    initial = []

    tiv_list = TissueInventoryVerification.objects.filter(
        tissue_request__req_request__req_request_id=req_request_id).order_by('monkey', 'tissue_type__tst_tissue_name')

    p_tiv_list = gizmo.create_paginator_instance(request, tiv_list, 30)
    for tiv in p_tiv_list.object_list:
        try:
            amount = tiv.tissue_request.get_amount()
            req_request = tiv.tissue_request.req_request \
                if tiv.tissue_request.req_request.get_acc_req_collisions_for_tissuetype_monkey(tiv.tissue_type,
                                                                                               tiv.monkey) \
                else False
        except AttributeError: # tissue_request == None
            req_request = False
            amount = "None"
        tss = tiv.tissue_sample
        quantity = -1 if tiv.tissue_request is None else tss.tss_sample_quantity
        tiv_initial = {'primarykey': tiv.tiv_id,
                       'inventory': tiv.tiv_inventory,
                       'monkey': tiv.monkey,
                       'tissue': tiv.tissue_type,
                       'notes': tiv.tiv_notes,
                       'amount': amount,
                       'quantity': quantity,
                       'req_request': req_request, }
        initial.append(tiv_initial)

    formset = TissueVerificationFormSet(initial=initial)
    return render_to_response('matrr/verification/verification_list.html',
                              {"formset": formset, "req_id": req_request_id, "paginator": p_tiv_list},
                              context_instance=RequestContext(request))


def tissue_verification_post_shipment(request):
    TissueVerificationShippedFormSet = formset_factory(TissueInventoryVerificationShippedForm, extra=0)
    if request.method == "POST":
        formset = TissueVerificationShippedFormSet(request.POST)
        if formset.is_valid():
            for tivform in formset:
                data = tivform.cleaned_data
                tiv = TissueInventoryVerification.objects.get(pk=data['primarykey'])
                tss = tiv.tissue_sample
                if data['units'] != tss.tss_units:
                    tss.tss_units = data['units']
                    tss.save()
                    tiv.tiv_inventory = 'Updated'
                if data['quantity'] >= 0:
                    tss.tss_sample_quantity = data['quantity']
                    tss.save()
                    tiv.tiv_inventory = 'Updated'
                else:
                    tiv.tiv_inventory = 'Unverified'
                tiv.save()
            messages.success(request, message="This page of tissues has been successfully updated.")
        else:
            messages.error(request, formset.errors)

    # if request method != post and/or formset isNOT valid
    # build a new formset
    tiv_list = TissueInventoryVerification.objects.filter(tissue_request=None).order_by('monkey',
                                                                                        'tissue_type__tst_tissue_name')
    p_tiv_list = gizmo.create_paginator_instance(request, tiv_list, 30)
    initial = []
    for tiv in p_tiv_list.object_list:
        tss = tiv.tissue_sample
        tiv_initial = {'primarykey': tiv.tiv_id,
                       'monkey': tiv.monkey,
                       'tissue': tiv.tissue_type,
                       'notes': tiv.tiv_notes,
                       'quantity': -1,
                       'units': tss.tss_units,
        }
        initial.append(tiv_initial)

    formset = TissueVerificationShippedFormSet(initial=initial)
    return render_to_response('matrr/verification/verification_shipped_list.html',
                              {"formset": formset, "req_id": 0, "paginator": p_tiv_list},
                              context_instance=RequestContext(request))


def tissue_verification_detail(request, req_request_id, tiv_id):
    tiv = TissueInventoryVerification.objects.get(pk=tiv_id)
    if request.method == "POST":
        tivform = TissueInventoryVerificationDetailForm(data=request.POST)
        if tivform.is_valid():
            data = tivform.cleaned_data
            tiv = TissueInventoryVerification.objects.get(pk=tiv_id)
            tss = tiv.tissue_sample
            tss.tss_location = data['location']
            tss.tss_freezer = data['freezer']
            tss.tss_details = data['details']
            tss.user = request.user # who last modified the tissue sample
            if data['quantity']:
                tss.tss_sample_quantity = data['quantity']
            if data['units']:
                tss.tss_units = data['units']
            if data['inventory']:
                tiv.tiv_inventory = data['inventory']
            tiv.save()
            if not 'Do not edit' in tiv.tiv_notes: # see TissueInventoryVerification.save() for details
                tss.save()

            return redirect('/verification/%s' % req_request_id)
        else:
            messages.error(request, tivform.errors)

    # if request method != post and/or formset isNOT valid
    # build a new formset
    try:
        amount = tiv.tissue_request.get_amount()
        if tiv.tissue_request.req_request.get_acc_req_collisions_for_tissuetype_monkey(tiv.tissue_type, tiv.monkey):
            req_request = tiv.tissue_request.req_request
        else:
            req_request = False
    except AttributeError: # tissue_request == None
        req_request = False
        amount = "None"
    tss = tiv.tissue_sample
    tiv_initial = {'primarykey': tiv.tiv_id,
                   'freezer': tss.tss_freezer,
                   'location': tss.tss_location,
                   'quantity': tss.tss_sample_quantity,
                   'inventory': tiv.tiv_inventory,
                   'units': tss.tss_units,
                   'details': tss.tss_details,
                   'monkey': tiv.monkey,
                   'tissue': tiv.tissue_type,
                   'notes': tiv.tiv_notes,
                   'amount': amount,
                   'req_request': req_request, }
    tivform = TissueInventoryVerificationDetailForm(initial=tiv_initial)
    return render_to_response('matrr/verification/verification_detail.html',
                              {"tivform": tivform, "req_id": req_request_id}, context_instance=RequestContext(request))


