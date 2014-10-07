import os
from datetime import datetime
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr.settings import UPLOAD_DIR
from matrr import emails
from matrr.forms import MtaForm, CodForm, RawDataUploadForm
from matrr import models


def mta_upload(request):
    # make blank mta instance
    mta_object = models.Mta(user=request.user)
    # make a MTA upload form if one does not exist
    if request.method == 'POST':
        if 'request_form' in request.POST:
            account = request.user.account
            emails.send_mta_uploaded_email(account)
            messages.success(request, 'A MATRR administrator has been notified of your MTA request and will contact you with more information.')
            return redirect(reverse('account-view'))
        form = MtaForm(request.POST, request.FILES, instance=mta_object)
        if form.is_valid():
            # all the fields in the form are valid, so save the data
            form.save()
            emails.notify_mta_uploaded(form.instance)
            messages.success(request, 'MTA Uploaded Successfully')
            return redirect(reverse('account-view'))
    else:
        # create the form for the MTA upload
        form = MtaForm(instance=mta_object)
    return render_to_response('matrr/upload_forms/mta_upload_form.html',
                              {'form': form,
                               'user': request.user
                              },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.add_cohortdata'), login_url='/denied/')
def cod_upload(request, coh_id=1):
    if request.method == 'POST':
        form = CodForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # all the fields in the form are valid, so save the data
            form.save()
            messages.success(request, 'Upload Successful')
            return redirect(reverse('cohort-details', args=[str(coh_id)]))
    else:
        cohort = models.Cohort.objects.get(pk=coh_id)
        form = CodForm(cohort=cohort, user=request.user)
    return render_to_response('matrr/upload_forms/cod_upload_form.html', {'form': form, },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('auth.upload_raw_data'), login_url='/denied/')
def raw_data_upload(request):
    if request.method == 'POST':
        form = RawDataUploadForm(account=request.user.account, data=request.POST, files=request.FILES)
        if form.is_valid():
            dto = models.DataOwnership()
            dto.account = request.user.account
            dto.dto_type = form.cleaned_data['dto_type']
            dto.save()
            dto.dto_data_notes = request.FILES['dto_data_notes']
            dto.dto_data_file = request.FILES['dto_data_file']
            dto.cohorts.add(*form.cleaned_data['cohorts'])
            dto.save()
            messages.success(request, "Your data has been uploaded successfully.")
            return redirect('view-dto-data')
    else:
        form = RawDataUploadForm(account=request.user.account)
    return render_to_response('matrr/upload_forms/raw_data_upload.html', {'form': form},
                              context_instance=RequestContext(request))


