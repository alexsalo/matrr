import os
from datetime import datetime
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from settings import UPLOAD_DIR, PRODUCTION
from matrr import emails
from matrr.forms import MtaForm, CodForm, RawDataUploadForm
from matrr.models import Mta, Cohort


def mta_upload(request):
    # make blank mta instance
    mta_object = Mta(user=request.user)
    # make a MTA upload form if one does not exist
    if request.method == 'POST':
        if 'request_form' in request.POST:
            if PRODUCTION:
                account = request.user.account
                emails.send_mta_uploaded_email(account)
            else:
                print "%s - New request email not sent, PRODUCTION = %s" % (
                datetime.now().strftime("%Y-%m-%d,%H:%M:%S"), PRODUCTION)
            messages.success(request,
                             'A MATRR administrator has been notified of your MTA request and will contact you with more information.')
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
        cohort = Cohort.objects.get(pk=coh_id)
        form = CodForm(cohort=cohort, user=request.user)
    return render_to_response('matrr/upload_forms/cod_upload_form.html', {'form': form, },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('auth.upload_raw_data'), login_url='/denied/')
def raw_data_upload(request):
    if request.method == 'POST':
        form = RawDataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['data']
            name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "." + f.name
            upload_path = os.path.join(UPLOAD_DIR, name)
            destination = open(upload_path, 'wb+')
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()
            return render_to_response('matrr/upload_forms/raw_data_upload.html',
                                      {'form': RawDataUploadForm(), 'success': True},
                                      context_instance=RequestContext(request))
    else:
        form = RawDataUploadForm()
    return render_to_response('matrr/upload_forms/raw_data_upload.html', {'form': form},
                              context_instance=RequestContext(request))


