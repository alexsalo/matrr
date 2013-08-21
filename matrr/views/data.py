from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404

__author__ = 'developer'
from datetime import datetime
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from matrr.forms import ExperimentRangeForm, DataSelectForm, CohortSelectForm
from matrr.models import MonkeyToDrinkingExperiment, MonkeyBEC, MonkeyHormone, MonkeyProtein, Cohort


def data_landing(request):
    if request.method == 'POST':
        data_form = DataSelectForm(data=request.POST)
        if data_form.is_valid():
            return redirect(reverse('data-cohort', args=[data_form.cleaned_data.get('data_type', "")]))
        else:
            messages.error("You submitted an invalid for, please try again.  If this continues to happen, please contact a MATRR administrator.")
    else:
        data_form = DataSelectForm()
    return render_to_response('matrr/data/landing.html', {'data_form': data_form}, context_instance=RequestContext(request))


def data_cohort(request, data_type=""): # pick a cohort
    if not data_type in [field[0] for field in DataSelectForm.DATA_CHOICES]: # basically, if someone hand-wrote the url incorrectly
        raise Http404("That is not a valid data type option.")

    if request.method == 'POST':
        cohort_form = CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            return redirect('data-cohort-submit', data_type, cohort.pk)
        else:
            messages.error("You submitted an invalid for, please try again.  If this continues to happen, please contact a MATRR administrator.")

    try:
        DataType = eval(data_type)
    except NameError:
        # The only reason this ought to happen is if you've added data types to DataSelectForm.DATA_CHOICES but you're not importing the object in this file.
        raise Http404("I have never heard of that data type.  Please contact a MATRR admin.")
    cohorts_with_data_type = DataType.objects.all().values_list('monkey__cohort') # find cohorts which have the type of data requested
    cohorts_with_data_type = Cohort.objects.nicotine_filter(request.user).filter( pk__in=cohorts_with_data_type) # the Form needs a queryset of cohorts
    subject_select_form = CohortSelectForm(subject_queryset=cohorts_with_data_type)
    return render_to_response('matrr/data/data_type.html', {'subject_select_form': subject_select_form}, context_instance=RequestContext(request))

# GraphToolsMonkeySelectForm
def data_cohort_dates(request, data_type='', coh_id=0):
    if not data_type in [field[1] for field in DataSelectForm.DATA_CHOICES]: # basically, if someone hand-wrote the url incorrectly
        raise Http404("That is not a valid data type option.")
    cohort = get_object_or_404(Cohort, pk=coh_id)

    monkey_keys = MonkeyProtein.objects.filter(monkey__cohort=cohort).values_list('monkey', flat=True).distinct()
    monkey_queryset = Monkey.objects.filter(pk__in=monkey_keys)

    if request.method == 'POST':
        subject_select_form = GraphSubjectSelectForm(monkey_queryset, download_option=True, data=request.POST)
        if subject_select_form.is_valid():
            subject = subject_select_form.cleaned_data['subject']
            if subject == 'monkey':
                monkeys = subject_select_form.cleaned_data['monkeys']
                get_m = list()
                for m in monkeys:
                    get_m.append(`m.mky_id`)
                get_m = "-".join(get_m)
                if not monkeys:
                    messages.error(request, "You have to select at least one monkey.")

                return gizmo.redirect_with_get('tools-monkey-protein', coh_id, monkeys=get_m)
            elif subject == 'cohort':
                return redirect('tools-cohort-protein-graphs', coh_id)
            else: # assumes subject == 'download'
                account = request.user.account
                if account.has_mta():
                    monkey_proteins = MonkeyProtein.objects.filter(monkey__in=cohort.monkey_set.all())

                    datafile, isnew = DataFile.objects.get_or_create(account=account,
                                                                     dat_title="%s Protein data" % str(cohort))
                    if isnew:
                        from utils.database import dump_monkey_protein_data
                        dump_monkey_protein_data(monkey_proteins, '/tmp/%s.csv' % str(datafile))
                        datafile.dat_data_file = File(open('/tmp/%s.csv' % str(datafile), 'r'))
                        datafile.save()
                        messages.info(request,
                                      "Your data file has been saved and is available for download on your account page.")
                    else:
                        messages.warning(request,
                                         "This data file has already been created for you.  It is available to download on your account page.")
                else:
                    messages.warning(request,
                                     "You must have a valid MTA on record to download data.  MTA information can be updated on your account page.")
    subject_select_form = GraphSubjectSelectForm(monkey_queryset, download_option=True)
    return render_to_response('matrr/tools/protein/protein.html', {'subject_select_form': subject_select_form},
                              context_instance=RequestContext(request))


def _verify_monkeys(text_monkeys):
    monkey_keys = text_monkeys.split('-')
    if len(monkey_keys) > 0:
        query_keys = list()
        for mk in monkey_keys:
            query_keys.append(int(mk))
        return Monkey.objects.filter(mky_id__in=query_keys)
    else:
        return Monkey.objects.none()


def tools_cohort_protein_graphs(request, coh_id):
    proteins = None
    old_post = request.session.get('_old_post')
    cohort = Cohort.objects.get(pk=coh_id)
    context = {'cohort': cohort}
    if request.method == "POST" or old_post:
        post = request.POST if request.POST else old_post
        protein_form = ProteinSelectForm(data=post)
        subject_select_form = CohortSelectForm(data=post)
        if protein_form.is_valid() and subject_select_form.is_valid():
            if int(coh_id) != subject_select_form.cleaned_data['subject'].pk:
                request.session['_old_post'] = request.POST
                return redirect(tools_cohort_protein_graphs, subject_select_form.cleaned_data['subject'].pk)
            proteins = protein_form.cleaned_data['proteins'] # overwrite proteins=None
            graphs = []
            for protein in proteins:
                cpi_image, is_new = CohortProteinImage.objects.get_or_create(protein=protein, cohort=cohort)
                if cpi_image.pk:
                    graphs.append(cpi_image)
            context['graphs'] = graphs

    cohorts_with_protein_data = MonkeyProtein.objects.all().values_list('monkey__cohort',
                                                                        flat=True).distinct() # for some reason this only returns the pk int
    cohorts_with_protein_data = Cohort.objects.nicotine_filter(request.user).filter(
        pk__in=cohorts_with_protein_data) # so get the queryset of cohorts

    context['subject_select_form'] = CohortSelectForm(subject_queryset=cohorts_with_protein_data, horizontal=True,
                                                      initial={'subject': coh_id})
    context['protein_form'] = ProteinSelectForm(initial={'proteins': proteins})
    return render_to_response('matrr/tools/protein/protein_cohort.html', context,
                              context_instance=RequestContext(request))


def tools_monkey_protein_graphs(request, coh_id, mky_id=None):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    context = {'cohort': cohort}
    try:
        # The monkeys to graph are passed to this view thru request.GET, from tools_cohort_protein
        monkeys = _verify_monkeys(request.GET['monkeys'])
    except ValueError:
        # the mky_id kwarg is present when directed here from monkey detail pages
        monkeys = _verify_monkeys(mky_id)
    context['monkeys'] = monkeys
    if request.method == 'GET' and 'monkeys' in request.GET and request.method != 'POST':
        # We land here when directed from tools_cohort_protein, where we should have monkey_pks from request.GET.
        # After we've parsed the GET monkeys above, we format the monkeys into a '-'-separated string of pks
        # These are stored in a hidden CharField within MonkeyProteinGraphAppearanceForm() for no reason, pretty much.
        get_m = list()
        if monkeys:
            for m in monkeys.values_list('mky_id', flat=True):
                get_m.append(`m`)

            text_monkeys = "-".join(get_m)
        else:
            text_monkeys = ""
        graph_form = MonkeyProteinGraphAppearanceForm(text_monkeys)
        protein_form = ProteinSelectForm()
    elif request.method == 'POST':
        # We land here after submitting POST data of the form, after selecting which graphs to create and what should be in them.
        # We need to parse out the relevant data from the forms
        # Once collected, we build the graphs and add them to the graphs list()
        protein_form = ProteinSelectForm(data=request.POST)
        graph_form = MonkeyProteinGraphAppearanceForm(data=request.POST)
        if protein_form.is_valid() and graph_form.is_valid():
            yaxis = graph_form.cleaned_data['yaxis_units']
            data_filter = graph_form.cleaned_data['data_filter']
            proteins = protein_form.cleaned_data['proteins']
            graphs = list()
            if data_filter == "morning":
                afternoon_reading = False
            elif data_filter == 'afternoon':
                afternoon_reading = True
            else:
                afternoon_reading = None
            mpi = ''
            if yaxis == 'monkey_protein_value':
                for protein in proteins:
                    for mon in monkeys:
                        mpis = MonkeyProteinImage.objects.filter(monkey=mon,
                                                                 method=yaxis,
                                                                 proteins__in=[protein, ],
                                                                 parameters=`{'afternoon_reading': afternoon_reading}`)
                        if mpis.count() == 0:
                            mpi = MonkeyProteinImage(monkey=mon,
                                                     method=yaxis,
                                                     parameters=`{'afternoon_reading': afternoon_reading}`)
                            mpi.save()
                            mpi.proteins.add(protein)
                            mpi.save()
                        if mpis.count() > 0:
                            mpi = mpis[0]
                        if mpi.pk:
                            graphs.append(mpi)
                if len(graphs) < len(proteins):
                    messages.info(request,
                                  'Some image files could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            else:
                for mon in monkeys:
                    mpis = MonkeyProteinImage.objects.filter(monkey=mon,
                                                             method=yaxis,
                                                             parameters=`{'afternoon_reading': afternoon_reading}`)
                    for protein in proteins:
                        mpis = mpis.filter(proteins=protein)

                    if len(mpis) == 0:
                        mpi = MonkeyProteinImage.objects.create(monkey=mon,
                                                                method=yaxis,
                                                                parameters=str(
                                                                    {'afternoon_reading': afternoon_reading}))
                        mpi.save()
                        mpi.proteins.add(*proteins)
                        mpi.save()
                    elif len(mpis) > 0:
                        mpi = mpis[0]
                    else:
                        raise Exception("How did you get a length less than 0?")
                    if mpi.pk:
                        graphs.append(mpi)
                if len(graphs) < len(monkeys):
                    messages.info(request,
                                  'Some image files could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            context['graphs'] = graphs
        else:
            if 'proteins' not in protein_form.data:
                messages.error(request, "You have to select at least one protein.")

            if len(graph_form.errors) + len(protein_form.errors) > 1:
                messages.error(request,
                               "There was an error processing this form.  If this continues to occur please notify a MATRR admin.")
    else:
        # function lands here when directed to protein tools from monkey detail page
        if mky_id:
            text_monkeys = "-".join([str(mky_id), ])
        else:
            text_monkeys = ""
        graph_form = MonkeyProteinGraphAppearanceForm(text_monkeys)
        protein_form = ProteinSelectForm()
    context['graph_form'] = graph_form
    context['protein_form'] = protein_form
    return render_to_response('matrr/tools/protein/protein_monkey.html', context,
                              context_instance=RequestContext(request))



