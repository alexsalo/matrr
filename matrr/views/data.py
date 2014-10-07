import os
from django.contrib import messages
from django.core.exceptions import FieldError
from django.core.files import File
from django.core.urlresolvers import reverse
from django.http import Http404
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.core import paginator
from matrr import models, forms


@user_passes_test(lambda u: u.has_perm('matrr.can_download_data'), login_url='/denied/')
def data_landing(request):
    if request.method == 'POST':
        data_form = forms.DataSelectForm(data=request.POST)
        if data_form.is_valid():
            return redirect(reverse('data-cohort', args=[data_form.cleaned_data.get('data_type', "")]))
        else:
            messages.error(request, "You submitted an invalid for, please try again.  If this continues to happen, please contact a MATRR administrator.")
    else:
        data_form = forms.DataSelectForm()
    return render_to_response('matrr/data/landing.html', {'data_form': data_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.can_download_data'), login_url='/denied/')
def data_cohort(request, data_type=""): # pick a cohort
    if not data_type in [field[0] for field in forms.DataSelectForm.DATA_CHOICES]: # basically, if someone hand-wrote the url incorrectly
        raise Http404("That is not a valid data type option.")

    if request.method == 'POST':
        cohort_form = forms.CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            return redirect('data-cohort-submit', data_type, cohort.pk)
        else:
            messages.error(request, "You submitted an invalid for, please try again.  If this continues to happen, please contact a MATRR administrator.")

    try:
        DataType = eval(data_type)
    except NameError:
        # The only reason this ought to happen is if you've added data types to DataSelectForm.DATA_CHOICES but you're not importing the object in this file.
        raise Http404("I have never heard of that data type.  Please contact a MATRR admin.")
    cohorts_with_data_type = DataType.objects.all().values_list('monkey__cohort') # find cohorts which have the type of data requested
    cohorts_with_data_type = models.Cohort.objects.nicotine_filter(request.user).filter( pk__in=cohorts_with_data_type) # the Form needs a queryset of cohorts
    subject_select_form = forms.CohortSelectForm(subject_queryset=cohorts_with_data_type)
    return render_to_response('matrr/data/data_type.html', {'subject_select_form': subject_select_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.can_download_data'), login_url='/denied/')
def data_cohort_dates(request, data_type='', coh_id=0):
    if not data_type in [field[0] for field in forms.DataSelectForm.DATA_CHOICES]:
        raise Http404("That is not a valid data type option.") # basically, if someone manually wrote the url incorrectly
    DataModel = eval(data_type)
    cohort = get_object_or_404(models.Cohort, pk=coh_id)
    monkey_queryset = models.Monkey.objects.Drinkers().filter(cohort=cohort)

    if request.method == 'POST':
        experiment_range_form = forms.ExperimentRangeForm(data=request.POST)
        monkey_select_form = forms.GraphToolsMonkeySelectForm(monkey_queryset, data=request.POST)
        if experiment_range_form.is_valid() and monkey_select_form.is_valid():
            experiment_range = experiment_range_form.cleaned_data['range']
            dex_type = experiment_range if experiment_range != 'custom' else ''
            from_date = experiment_range_form.cleaned_data['from_date']
            to_date = experiment_range_form.cleaned_data['to_date']

            monkeys = monkey_select_form.cleaned_data['monkeys']
            account = request.user.account
            if account.has_mta():
                unfiltered_data = DataModel.objects.filter(monkey__in=monkeys)
                datafile, isnew = models.DataFile.objects.get_or_create(account=account, dat_title="%s - %s - %s" % (str(cohort), data_type,  experiment_range))
                if not isnew:
                    # delete the existing DataFile
                    datafile.delete() # we don't want to store an assload of datafiles when they can generate them whenever they want
                    # and then create the data file again.
                    datafile, isnew = models.DataFile.objects.get_or_create(account=account, dat_title="%s - %s - %s" % (str(cohort), data_type,  experiment_range))

                from matrr.gizmo import dump_queryset_to_csv
                temp_path = '/tmp/%s.csv' % str(datafile)
                # dump method will filter dates and dex_types appropriately by model.
                success = True
                try:
                    dump_queryset_to_csv(unfiltered_data, temp_path, dex_type=dex_type, from_date=from_date, to_date=to_date)
                except FieldError:
                    success = False
                f = open(temp_path, 'r')
                datafile.dat_data_file = File(f)
                datafile.save()
                os.remove(temp_path)
                if success:
                    messages.info(request, "Your data file has been saved and is available for download on your account page.")
                else:
                    messages.warning(request, "Your data file was NOT saved.  This is usually avoided by choosing 'Custom Dates' and leaving the date fields blank.")
            else:
                messages.warning(request, "You must have a valid MTA on record to download data.  MTA information can be updated on your account page.")
    monkey_select_form = forms.GraphToolsMonkeySelectForm(monkey_queryset)
    experiment_range_form = forms.ExperimentRangeForm()
    context = {'monkey_select_form': monkey_select_form, 'cohort': cohort, 'experiment_range_form': experiment_range_form}
    return render_to_response('matrr/data/data_type_cohort.html', context, context_instance=RequestContext(request))

def view_dto_data(request):
    if request.user.has_perm('matrr.view_dto_data'):
        dto_set = models.DataOwnership.objects.all().order_by('-dto_date')
    else:
        dto_set = models.DataOwnership.objects.filter(account=request.user.account)
    ## Paginator stuff
    dto_paginator = paginator.Paginator(dto_set, 5)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    # If page request is out of range, deliver last page of results.
    try:
        dto_page = dto_paginator.page(page)
    except (paginator.EmptyPage, paginator.InvalidPage):
        dto_page = dto_paginator.page(dto_paginator.num_pages)
    if not len(dto_page.object_list):
        messages.info(request, "You must upload data before viewing anything here.")
    return render_to_response('matrr/data/view_dto_data.html', {'dto_page': dto_page}, context_instance=RequestContext(request))
