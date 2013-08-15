from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr.forms import RNALandingForm, RNASubmitForm
from matrr.models import Cohort, RNARecord

@user_passes_test(lambda u: u.is_staff, login_url='/denied/')
def rna_landing(request):
    if request.method == "POST":
        cohort_form = RNALandingForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            yields = cohort_form.cleaned_data['yields']
            if yields == 'submit':
                return redirect('rna-submit', cohort.pk)
            else:
                return redirect('rna-display', cohort.pk)
        else:
            messages.error(request, "Form submission was invalid.  Please try again.")
    else:
        cohort_form = RNALandingForm()
    return render_to_response('matrr/rna/landing.html', {'cohort_form': cohort_form},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.rna_submit'), login_url='/denied/')
def rna_submit(request, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    if request.method == "POST":
        rna_form = RNASubmitForm(cohort, data=request.POST)
        rna = rna_form.instance
        if rna_form.is_valid():
            rna.cohort = cohort
            rna.user = request.user
            rna.full_clean()
            rna.save()
            messages.success(request, "RNA yield data saved.")
        else:
            messages.error(request, "Form submission was invalid.  Please try again.")
    else:
        rna_form = RNASubmitForm(cohort)
    return render_to_response('matrr/rna/submit.html', {'rna_form': rna_form}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.rna_display'), login_url='/denied/')
def rna_display(request, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    rna_records = RNARecord.objects.filter(cohort=cohort)
    ## Paginator stuff
    if rna_records.count() > 0:
        paginator = Paginator(rna_records, 25)
        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        # If page request (9999) is out of range, deliver last page of results.
        try:
            rna_list = paginator.page(page)
        except (EmptyPage, InvalidPage):
            rna_list = paginator.page(paginator.num_pages)
    else:
        rna_list = rna_records
    return render_to_response('matrr/rna/display.html', {'rna_list': rna_list, 'cohort': cohort},
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.rna_display'), login_url='/denied/')
def rna_detail(request, rna_id):
    rna_record = get_object_or_404(RNARecord, pk=rna_id)
    return render_to_response('matrr/rna/detail.html', {'rna_record': rna_record}, context_instance=RequestContext(request))

