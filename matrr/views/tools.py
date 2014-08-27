import json, numpy, os
import cStringIO as StringIO
import ho.pisa as pisa
from django.core.files import File
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils.safestring import mark_safe
from matrr import gizmo, settings
from matrr.views.basic import sendfile
from matrr.forms import CohortSelectForm, GraphSubjectSelectForm, ProteinSelectForm, MonkeyProteinGraphAppearanceForm, HormoneSelectForm, MonkeyHormoneGraphAppearanceForm
from matrr.forms import ExperimentRangeForm, BECRangeForm, GenealogyParentsForm, GraphToolsMonkeySelectForm
from matrr.models import Cohort, Monkey, CohortImage, MonkeyImage, MonkeyProtein, MonkeyBEC, DataFile, MonkeyProteinImage, MonkeyHormone, MonkeyHormoneImage, FamilyNode, MATRRImage
from matrr.models import MonkeyToDrinkingExperiment, MTDImage, CohortProteinImage, CohortHormoneImage
from matrr.plotting import cohort_plots, monkey_plots, RHESUS_MONKEY_COLORS
from matrr.utils import apriori
from matrr.utils.confederates import confederates


def tools_landing(request):
    cohort_methods = cohort_plots.COHORT_TOOLS_PLOTS.keys()
    monkey_methods = monkey_plots.MONKEY_TOOLS_PLOTS.keys()

    if request.method == 'POST':
        _method = request.POST.get('cohort_method', '')
        if _method:
            if _method in cohort_plots.COHORT_BEC_TOOLS_PLOTS.keys():
                return redirect('tools-cohort-bec-graphs', _method)
            elif _method in cohort_plots.COHORT_ETOH_TOOLS_PLOTS.keys():
                return redirect('tools-cohort-etoh-graphs', _method)
            else:
                raise Http404("There is no '%s' method in the MATRR BEC or ETOH toolboxes." % _method)
        _method = request.POST.get('monkey_method', '')
        if _method:
            if _method in monkey_plots.MONKEY_BEC_TOOLS_PLOTS.keys():
                return redirect('tools-monkey-bec', _method)
            elif _method in monkey_plots.MONKEY_ETOH_TOOLS_PLOTS.keys():
                return redirect('tools-monkey-etoh', _method)
            else:
                raise Http404("There is no '%s' method in the MATRR BEC or ETOH toolboxes." % _method)

    coh_images = list()
    for method in cohort_methods:
        try:
            coh_images.append(CohortImage.objects.filter(canonical=True, method=method)[0])
        except IndexError:
            pass
    mky_images = list()
    for method in monkey_methods:
        try:
            mky_images.append(MonkeyImage.objects.filter(canonical=True, method=method)[0])
        except IndexError:
            # no images to show.  ignore.
            pass
    return render_to_response('matrr/tools/landing.html', {'mky_images': mky_images, 'coh_images': coh_images},
                              context_instance=RequestContext(request))


def tools_protein(request): # pick a cohort
    if request.method == 'POST':
        cohort_form = CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            return redirect('tools-cohort-protein', cohort.pk)
    cohorts_with_protein_data = MonkeyProtein.objects.all().values_list('monkey__cohort', flat=True).distinct() # for some reason this only returns the pk int
    cohorts_with_protein_data = Cohort.objects.nicotine_filter(request.user).filter( pk__in=cohorts_with_protein_data) # so get the queryset of cohorts
    subject_select_form = CohortSelectForm(subject_queryset=cohorts_with_protein_data)
    return render_to_response('matrr/tools/protein/protein.html', {'subject_select_form': subject_select_form},
                              context_instance=RequestContext(request))


def tools_cohort_protein(request, coh_id):
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
                        from matrr.utils.database import dump_monkey_protein_data
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


@user_passes_test(lambda u: u.has_perm('matrr.view_hormone_tools'), login_url='/denied/')
def tools_hormone(request): # pick a cohort
    if request.method == 'POST':
        cohort_form = CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            return redirect('tools-cohort-hormone', cohort.pk)
    cohorts_with_hormone_data = MonkeyHormone.objects.all().values_list('monkey__cohort__pk', flat=True).distinct()
    cohorts_with_hormone_data = Cohort.objects.nicotine_filter(request.user).filter(
        pk__in=cohorts_with_hormone_data) # get the queryset of cohorts
    subject_select_form = CohortSelectForm(subject_queryset=cohorts_with_hormone_data)
    return render_to_response('matrr/tools/hormone/hormone.html', {'subject_select_form': subject_select_form},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_hormone_tools'), login_url='/denied/')
def tools_cohort_hormone(request, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    monkey_pks = MonkeyHormone.objects.filter(monkey__cohort=cohort).values_list('monkey', flat=True).distinct()
    monkey_queryset = Monkey.objects.filter(pk__in=monkey_pks)

    # WARNING
    # If hormone data is for-download, replace the raise Http404() with code from tools_cohort_protein, modified for hormones
    subject_select_form = GraphSubjectSelectForm(monkey_queryset)
    if request.method == 'POST':
        subject_select_form = GraphSubjectSelectForm(monkey_queryset, data=request.POST)
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
                return gizmo.redirect_with_get('tools-monkey-hormone', coh_id, monkeys=get_m)
            elif subject == 'cohort':
                return redirect('tools-cohort-hormone-graphs', coh_id)
            else: # assumes subject == 'download'
                # WARNING
                # If hormone data is for-download, replace the raise Http404() with code from tools_cohort_protein, modified for hormones
                raise Http404("Hormone data is not available for download at the moment.")
    return render_to_response('matrr/tools/hormone/hormone.html', {'subject_select_form': subject_select_form}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_hormone_tools'), login_url='/denied/')
def tools_cohort_hormone_graphs(request, coh_id):
    old_post = request.session.get('_old_post')
    if old_post:
        request.session['_old_post'] = {}
    cohort = Cohort.objects.get(pk=coh_id)
    cohorts_with_hormone_data = MonkeyHormone.objects.all().values_list('monkey__cohort__pk', flat=True).distinct()
    cohorts_with_hormone_data = Cohort.objects.nicotine_filter(request.user).filter(pk__in=cohorts_with_hormone_data) # get the queryset of cohorts
    context = {'cohort': cohort}
    if request.method == "POST" or old_post:
        post = request.POST if request.POST else old_post
        hormone_form = HormoneSelectForm(data=post)
        subject_select_form = CohortSelectForm(subject_queryset=cohorts_with_hormone_data, horizontal=True, initial={'subject': coh_id}, data=post)
        if hormone_form.is_valid() and subject_select_form.is_valid():
            if int(coh_id) != subject_select_form.cleaned_data['subject'].pk:
                new_post = dict(request.POST)
                new_post['subject'] = subject_select_form.cleaned_data['subject'].pk
                request.session['_old_post'] = new_post
                return redirect(tools_cohort_hormone_graphs, subject_select_form.cleaned_data['subject'].pk)
            hormones = hormone_form.cleaned_data['hormones']
            scaled = hormone_form.cleaned_data['scaled']
            params = str({'scaled': scaled})
            graphs = []
            for hormone in hormones:
                chi_image, is_new = CohortHormoneImage.objects.get_or_create(hormone=hormone, cohort=cohort, parameters=params)
                if chi_image.pk:
                    graphs.append(chi_image)
            if len(graphs) < len(hormones):
                messages.info(request, 'Some image files could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            context['graphs'] = graphs
    else:
        subject_select_form = CohortSelectForm(subject_queryset=cohorts_with_hormone_data, horizontal=True,
                                               initial={'subject': coh_id})
        hormone_form = HormoneSelectForm()
    context['subject_select_form'] = subject_select_form
    context['hormone_form'] = hormone_form
    return render_to_response('matrr/tools/hormone/hormone_cohort.html', context,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_hormone_tools'), login_url='/denied/')
def tools_monkey_hormone_graphs(request, coh_id, mky_id=None):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    context = {'cohort': cohort}
    try:
        monkeys = _verify_monkeys(request.GET['monkeys'])
    except ValueError:
        monkeys = _verify_monkeys(mky_id)
    context['monkeys'] = monkeys

    if request.method == 'GET' and 'monkeys' in request.GET and request.method != 'POST':
        get_m = list()
        if monkeys:
            for m in monkeys.values_list('mky_id', flat=True):
                get_m.append(`m`)

            text_monkeys = "-".join(get_m)
        else:
            text_monkeys = ""
        graph_form = MonkeyHormoneGraphAppearanceForm(text_monkeys)
        hormone_form = HormoneSelectForm()
    elif request.method == 'POST':
        graph_form = MonkeyHormoneGraphAppearanceForm(data=request.POST)
        hormone_form = HormoneSelectForm(data=request.POST)

        if hormone_form.is_valid() and graph_form.is_valid():
            yaxis = graph_form.cleaned_data['yaxis_units']
            hormones = hormone_form.cleaned_data['hormones']
            scaled = hormone_form.cleaned_data['scaled']
            params = str({'scaled': scaled}) # only used for monkey_hormone_value.  pctdev/stdev don't scale
            graphs = list()
            if yaxis == 'monkey_hormone_value':
                for hormone in hormones:
                    hormone_json = json.dumps([hormone, ])
                    for mon in monkeys:
                        mpi, is_new = MonkeyHormoneImage.objects.get_or_create(monkey=mon, method=yaxis,
                                                                               hormones=hormone_json, parameters=params)
                        if mpi.pk:
                            graphs.append(mpi)
                if len(graphs) < len(hormones):
                    messages.info(request,
                                  'Some image files could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            else:
                hormone_json = json.dumps(list(hormones))
                for mon in monkeys:
                    mpi, is_new = MonkeyHormoneImage.objects.get_or_create(monkey=mon, method=yaxis,
                                                                           hormones=hormone_json)
                    if mpi.pk:
                        graphs.append(mpi)
                if len(graphs) < len(monkeys):
                    messages.info(request,
                                  'Some image files could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            context['graphs'] = graphs
        else:
            if 'hormones' not in hormone_form.data:
                messages.error(request, "You have to select at least one hormone.")

            if len(graph_form.errors) + len(hormone_form.errors) > 1:
                messages.error(request,
                               "There was an error processing this form.  If this continues to occur please notify a MATRR admin.")
    else:
        # function lands here when directed to hormone tools from monkey detail page
        get_m = list()
        if mky_id:
            get_m.append(`mky_id`)
            text_monkeys = "-".join(get_m)
        else:
            text_monkeys = ""
        graph_form = MonkeyHormoneGraphAppearanceForm(text_monkeys)
        hormone_form = HormoneSelectForm()

    context['graph_form'] = graph_form
    context['hormone_form'] = hormone_form
    return render_to_response('matrr/tools/hormone/hormone_monkey.html', context,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_etoh_mtd(request, mtd_id):
    mtd_image = ''
    if MonkeyToDrinkingExperiment.objects.filter(pk=mtd_id).count():
        mtd = MonkeyToDrinkingExperiment.objects.get(pk=mtd_id)
        mtd_image, is_new = MTDImage.objects.get_or_create(
            monkey_to_drinking_experiment=mtd,
            method='monkey_etoh_bouts_drinks_intraday',
            title="Drinks on %s for monkey %s" % (str(mtd.drinking_experiment.dex_date), str(mtd.monkey))
        )
    return render_to_response('matrr/tools/graph_generic.html', {'matrr_image': mtd_image},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_cohort_etoh_graphs(request, cohort_method):
    context = dict()
    subject_initial = dict()
    range_initial = dict()
    if request.method == "POST":
        subject_select_form = CohortSelectForm(data=request.POST)
        experiment_range_form = ExperimentRangeForm(data=request.POST)
        if subject_select_form.is_valid() and experiment_range_form.is_valid():
            subject_initial = subject_select_form.cleaned_data
            range_initial = experiment_range_form.cleaned_data
            cohort = subject_select_form.cleaned_data['subject']

            from_date = ''
            to_date = ''
            experiment_range = experiment_range_form.cleaned_data['range']
            if experiment_range == 'custom':
                from_date = str(experiment_range_form.cleaned_data['from_date'])
                to_date = str(experiment_range_form.cleaned_data['to_date'])
                experiment_range = None

            params = str({'dex_type': experiment_range, 'from_date': from_date, 'to_date': to_date})
            cohort_image, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=cohort_method,
                                                                     title=cohort_plots.COHORT_PLOTS[cohort_method][1],
                                                                     parameters=params)

            if is_new and not cohort_image.pk:
                messages.error(request,
                               'Image file could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            else:
                context['graph'] = cohort_image
        else:
            messages.error(request, subject_select_form.errors.as_text())
            messages.error(request, experiment_range_form.errors.as_text())
    cohorts_with_ethanol_data = MonkeyToDrinkingExperiment.objects.all().values_list('monkey__cohort',
                                                                                     flat=True).distinct() # this only returns the pk int
    cohorts_with_ethanol_data = Cohort.objects.nicotine_filter(request.user).filter(
        pk__in=cohorts_with_ethanol_data) # so get the queryset of cohorts

    context['cohorts'] = cohorts_with_ethanol_data
    context['subject_select_form'] = CohortSelectForm(subject_queryset=cohorts_with_ethanol_data, horizontal=True,
                                                      initial=subject_initial)
    context['experiment_range_form'] = ExperimentRangeForm(initial=range_initial)
    return render_to_response('matrr/tools/ethanol/ethanol_cohort.html', context,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_monkey_etoh(request, monkey_method): # pick a cohort
    if request.method == 'POST':
        cohort_form = CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            return redirect('tools-monkey-etoh-graphs', monkey_method, cohort.pk)
    else:
        cohorts_with_etoh_data = MonkeyToDrinkingExperiment.objects.all().values_list('monkey__cohort',
                                                                                      flat=True).distinct() # this only returns the pk int
        cohorts_with_etoh_data = Cohort.objects.nicotine_filter(request.user).filter(
            pk__in=cohorts_with_etoh_data) # so get the queryset of cohorts
        cohort_form = CohortSelectForm(subject_queryset=cohorts_with_etoh_data)
    return render_to_response('matrr/tools/ethanol/ethanol.html', {'subject_select_form': cohort_form},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_etoh_data'), login_url='/denied/')
def tools_monkey_etoh_graphs(request, monkey_method, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    drinking_monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)
    context = {'cohort': cohort}

    if request.method == 'POST':
        monkey_select_form = GraphToolsMonkeySelectForm(drinking_monkeys, data=request.POST)
        experiment_range_form = ExperimentRangeForm(data=request.POST)
        if experiment_range_form.is_valid() and monkey_select_form.is_valid():
            from_date = to_date = ''
            experiment_range = experiment_range_form.cleaned_data['range']
            if experiment_range == 'custom':
                from_date = str(experiment_range_form.cleaned_data['from_date'])
                to_date = str(experiment_range_form.cleaned_data['to_date'])
                experiment_range = None

            monkeys = monkey_select_form.cleaned_data['monkeys']
            title = monkey_plots.MONKEY_PLOTS[monkey_method][1]
            params = {'from_date': str(from_date), 'to_date': str(to_date), 'dex_type': experiment_range}
            render_failed = False
            graphs = list()
            for monkey in monkeys:
                mig, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, title=title, method=monkey_method,
                                                                parameters=str(params))
                if mig.pk:
                    graphs.append(mig)
                else:
                    render_failed = True
            if not graphs:
                messages.info(request, "No graphs could be made with these settings.")
                render_failed = False # dont give them two messages
            else:
                context['graphs'] = graphs
            if render_failed:
                messages.info(request, "Some graphs failed to render. This issue will be investigated.")

        context['monkey_select_form'] = monkey_select_form
        context['experiment_range_form'] = experiment_range_form
    else:
        context['monkey_select_form'] = GraphToolsMonkeySelectForm(drinking_monkeys)
        context['experiment_range_form'] = ExperimentRangeForm()

    return render_to_response('matrr/tools/ethanol/ethanol_monkey.html', context, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_bec_data'), login_url='/denied/')
def tools_cohort_bec_graphs(request, cohort_method):
    context = dict()
    subject_initial = dict()
    range_initial = dict()
    if request.method == "POST":
        subject_select_form = CohortSelectForm(data=request.POST)
        experiment_range_form = BECRangeForm(data=request.POST)
        if subject_select_form.is_valid() and experiment_range_form.is_valid():
            subject_initial = subject_select_form.cleaned_data
            range_initial = experiment_range_form.cleaned_data
            cohort = subject_select_form.cleaned_data['subject']

            from_date = ''
            to_date = ''
            experiment_range = experiment_range_form.cleaned_data['range']
            if experiment_range == 'custom':
                from_date = str(experiment_range_form.cleaned_data['from_date'])
                to_date = str(experiment_range_form.cleaned_data['to_date'])
                experiment_range = None

            sample_before = ''
            sample_after = ''
            sample_range = experiment_range_form.cleaned_data['sample_range']
            if sample_range == 'morning':
                sample_before = '14:00'
            if sample_range == 'afternoon':
                sample_after = '14:00'

            params = str({'dex_type': experiment_range, 'from_date': from_date, 'to_date': to_date,
                          'sample_before': sample_before, 'sample_after': sample_after})
            cohort_image, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=cohort_method,
                                                                     title=cohort_plots.COHORT_PLOTS[cohort_method][1],
                                                                     parameters=params)
            if is_new and not cohort_image.pk:
                messages.error(request,
                               'Image file could not be created.  This is usually caused by requesting insufficient or non-existent data.')
            else:
                context['graph'] = cohort_image
        else:
            messages.error(request, subject_select_form.errors.as_text())
            messages.error(request, experiment_range_form.errors.as_text())
    cohorts_with_bec_data = MonkeyBEC.objects.all().values_list('monkey__cohort',
                                                                flat=True).distinct() # this only returns the pk int
    cohorts_with_bec_data = Cohort.objects.nicotine_filter(request.user).filter(
        pk__in=cohorts_with_bec_data) # so get the queryset of cohorts

    context['cohorts'] = cohorts_with_bec_data
    context['subject_select_form'] = CohortSelectForm(subject_queryset=cohorts_with_bec_data, horizontal=True,
                                                      initial=subject_initial)
    context['experiment_range_form'] = BECRangeForm(initial=range_initial)
    return render_to_response('matrr/tools/bec/bec_cohort.html', context, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_bec_data'), login_url='/denied/')
def tools_monkey_bec(request, monkey_method): # pick a cohort
    if request.method == 'POST':
        cohort_form = CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            cohort = cohort_form.cleaned_data['subject']
            return redirect('tools-monkey-bec-graphs', monkey_method, cohort.pk)
    else:
        cohorts_with_bec_data = MonkeyBEC.objects.all().values_list('monkey__cohort', flat=True).distinct() # this only returns the pk int
        cohorts_with_bec_data = Cohort.objects.nicotine_filter(request.user).filter( pk__in=cohorts_with_bec_data) # so get the queryset of cohorts
        cohort_form = CohortSelectForm(subject_queryset=cohorts_with_bec_data)
    return render_to_response('matrr/tools/bec/bec.html', {'subject_select_form': cohort_form}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_bec_data'), login_url='/denied/')
def tools_monkey_bec_graphs(request, monkey_method, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    drinking_monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)
    context = {'cohort': cohort}

    if request.method == 'POST':
        monkey_select_form = GraphToolsMonkeySelectForm(drinking_monkeys, data=request.POST)
        experiment_range_form = ExperimentRangeForm(data=request.POST)
        if experiment_range_form.is_valid() and monkey_select_form.is_valid():
            from_date = to_date = ''
            experiment_range = experiment_range_form.cleaned_data['range']
            if experiment_range == 'custom':
                from_date = str(experiment_range_form.cleaned_data['from_date'])
                to_date = str(experiment_range_form.cleaned_data['to_date'])
                experiment_range = None

            monkeys = monkey_select_form.cleaned_data['monkeys']
            title = monkey_plots.MONKEY_PLOTS[monkey_method][1]
            params = {'from_date': str(from_date), 'to_date': str(to_date), 'dex_type': experiment_range}
            render_failed = False
            graphs = list()
            for monkey in monkeys:
                mig, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, title=title, method=monkey_method,
                                                                parameters=str(params))
                if mig.pk:
                    graphs.append(mig)
                else:
                    render_failed = True
            if not graphs:
                messages.info(request, "No graphs could be made with these settings.")
                render_failed = False # dont give them two messages
            else:
                context['graphs'] = graphs
            if render_failed:
                messages.info(request, "Some graphs failed to render. This issue will be investigated.")

        context['monkey_select_form'] = monkey_select_form
        context['experiment_range_form'] = experiment_range_form
    else:
        context['monkey_select_form'] = GraphToolsMonkeySelectForm(drinking_monkeys)
        context['experiment_range_form'] = ExperimentRangeForm()

    return render_to_response('matrr/tools/bec/bec_monkey.html', context, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_confederates'), login_url='/denied/')
def tools_confederates(request):
    return render_to_response('matrr/tools/confederates/confederates.html', {},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_confederates'), login_url='/denied/')
def tools_confederates_chord_diagram(request):
#	https://github.com/mbostock/d3/wiki/Gallery
    d3_redirect = request.GET.get('d3_redirect', '')
    if d3_redirect == 'chord':
        return redirect(reverse('tools-confederates-chord'))
    if d3_redirect == 'adjacency':
        return redirect(reverse('tools-confederates-adjacency'))
    min_conf = request.GET.get('min_conf', 0)
    try:
        min_conf = float(min_conf)
    except ValueError:
        messages.error(request, "Enter a number, 1 > x > 0.")
        min_conf = 0
    if not 1 > min_conf >= 0:
        messages.error(request, "Enter a number, 1 > x > 0.")
        min_conf = 0

    def reformat_apriori_output_1to1(cohort=None):
        cohorts = [cohort] if cohort else [5, 6, 9, 10]
        drinkers = Monkey.objects.Drinkers().filter(cohort__in=cohorts)
        drinkers = drinkers.values_list('pk', flat=True)
        matrix = numpy.zeros((drinkers.count(), drinkers.count()))

        indices = dict()
        for index, monkey_pk in enumerate(drinkers):
            indices[monkey_pk] = index

        for cohort_pk in cohorts:
            orig = confederates.get_all_confederate_groups(cohort_pk, minutes=15, min_confidence=min_conf)
            for support, occurrences in orig.iteritems():
                for cause, effect, confidence in occurrences:
                    if len(cause) > 1 or len(effect) > 1:
                        continue
                    cause = tuple(cause)[0]
                    effect = tuple(effect)[0]
                    matrix[indices[cause], indices[effect]] = float(support) * float(confidence)
        list_matrix = list()
        for row in matrix:
            list_matrix.append(list(row))
        return list_matrix, drinkers

    def reformat_apriori_output_NtoN(cohort=None):
        cohorts = [cohort] if cohort else [5, 6, 9, 10]
        drinkers = Monkey.objects.Drinkers().filter(cohort__in=cohorts)
        drinkers = drinkers.values_list('pk', flat=True)
        matrix = numpy.zeros((drinkers.count(), drinkers.count()))

        indices = dict()
        for index, monkey_pk in enumerate(drinkers):
            indices[monkey_pk] = index

        for cohort_pk in cohorts:
            orig = confederates.get_all_confederate_groups(cohort_pk, minutes=15, min_confidence=min_conf)
            for support, occurrences in orig.iteritems():
                for cause_monkeys, effect_monkeys, confidence in occurrences:
                    cause_value = float(support) * float(confidence) / len(cause_monkeys) / len(effect_monkeys)
                    for _cause in cause_monkeys:
                        for _effect in effect_monkeys:
                            matrix[indices[_cause], indices[_effect]] += cause_value
        list_matrix = list()
        for row in matrix:
            list_matrix.append(list(row))
        return list_matrix, drinkers

    NtoN = request.GET.get('NtoN', False)
    reformat_method = reformat_apriori_output_NtoN if NtoN else reformat_apriori_output_1to1

    chord_data = list()
    for coh in [5, 6, 9, 10]:
        matrix, labels = reformat_method(coh)
        labels_colors = list()
        for key in labels:
            lc = {'name': key, 'color': RHESUS_MONKEY_COLORS[key]}
            labels_colors.append(lc)
        dataset = mark_safe(json.dumps(matrix))
        labels_colors = mark_safe(json.dumps(labels_colors))
        cohort = Cohort.objects.get(pk=coh)
        data = {'dataset': dataset, 'labels_colors': labels_colors, 'cohort': cohort}
        chord_data.append(data)
    return render_to_response('matrr/tools/confederates/chord_diagram.html', {'chord_data': chord_data},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_confederates'), login_url='/denied/')
def tools_confederates_adjacency_matrix(request):
    """
    Based on: http://bost.ocks.org/mike/miserables/

    Important Note:
    The data to create the adjacency matrix is pre-rendered and stored in the /static/js/ folder, filename="%d.RAN.json" % cohort_pk.

    The data is rendered using the utils/plotting_beta/RhesusAdjacencyNetwork() object.  This class was moved here from the matrr/helper.py file
    to alleviate a circular reference.
    """
    d3_redirect = request.GET.get('d3_redirect', '')
    if d3_redirect == 'chord':
        return redirect(reverse('tools-confederates-chord'))
    if d3_redirect == 'adjacency':
        return redirect(reverse('tools-confederates-adjacency'))
    cohort_pk = request.GET.get('cohort', 0)
    if cohort_pk == 'all':
        cohorts = Cohort.objects.none()
        multiple_cohorts = '5_6_9_10'
    else:
        cohorts = Cohort.objects.filter(pk=cohort_pk)
        multiple_cohorts = ''
    return render_to_response('matrr/tools/confederates/adjacency_matrix.html',
                              {'network_data': True, 'cohorts': cohorts, 'multiple_cohorts': multiple_cohorts},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.genealogy_tools'), login_url='/denied/')
def tools_genealogy(request):
    if request.method == 'POST':
        cohort_form = CohortSelectForm(data=request.POST)
        if cohort_form.is_valid():
            return HttpResponseRedirect(
                reverse('tools-cohort-genealogy', args=[cohort_form.cleaned_data['subject'].pk]))
        else:
            messages.error(request, "Invalid form submission")
    return render_to_response('matrr/tools/genealogy/subject_select.html', {'subject_select_form': CohortSelectForm()},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.access_genealogy_tools'), login_url='/denied/')
def tools_cohort_genealogy(request, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    cohort_monkeys = cohort.monkey_set.all()

    if request.method == 'POST':
        genealogy_form = GenealogyParentsForm(subject_queryset=cohort_monkeys, data=request.POST)
        if genealogy_form.is_valid():
            me = FamilyNode.objects.get(monkey=genealogy_form.cleaned_data['subject'])
            dad = FamilyNode.objects.get(monkey=genealogy_form.cleaned_data['father'])
            mom = FamilyNode.objects.get(monkey=genealogy_form.cleaned_data['mother'])

            me.sire = dad
            me.dam = mom
            me.save()

            messages.success(request, "Parentage for monkey %d saved." % me.monkey.pk)
            return redirect(reverse('tools-cohort-genealogy', args=[coh_id]))
        else:
            messages.error(request, "Invalid form submission")

    context = dict()
    context['genealogy_form'] = GenealogyParentsForm(subject_queryset=cohort_monkeys)
    return render_to_response('matrr/tools/genealogy/parent_select.html', context,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_sandbox'), login_url='/denied/')
def tools_sandbox(request):
    append = request.GET.get('append', "christa")
    base = settings.STATIC_ROOT + '/images/%s/' % append
    _files = os.listdir(base)
    files = list()
    for f in _files:
        if not os.path.isdir(base + f):
            files.append(f)
    files = sorted(files)
    return render_to_response('matrr/tools/sandbox/sandbox.html', {'files': files, 'append': append},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser, login_url='/denied/')
def tools_supersandbox(request):
    return render_to_response('matrr/tools/sandbox/supersandbox.html', {}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser, login_url='/denied/')
def tools_sandbox_familytree(request):
    from matrr.utils.network_tools import CohortKinship

    def male_female_shape(node):
        shape = 'circle' if node[1]['shape_input'] == 'F' else 'square'
        return shape

    cohort = 10
    us = FamilyNode.objects.filter(monkey__cohort=cohort)
    tree = CohortKinship(us)

    tree.visual_style.discrete_node_shapes(shape_method=male_female_shape)
    tree.visual_style.continuous_node_colors('color_input', min_value='blue', max_value='orange')
    tree.visual_style.passthru_node_borderColors('color')
    tree.visual_style.passthru_node_borderColors('borderColor_color')
    tree.visual_style.discrete_node_borderWidth()

    tree.visual_style.passthru_edge_colors()
    tree.visual_style.passthru_edge_width()

    draw_options = dict()
    draw_options['network'] = tree.dump_graphml()
    draw_options['visualStyle'] = tree.visual_style.get_visual_style()
    draw_options = mark_safe(str(draw_options))
    return render_to_response('matrr/tools/sandbox/sandbox_familytree.html',
                              {'cohort': cohort, 'draw_options': draw_options},
                              context_instance=RequestContext(request))


def create_pdf_fragment_v2(request, klass, imageID):
    import matrr.models as mmodels
    im = get_object_or_404(getattr(mmodels, klass), pk=imageID)

    if not isinstance(im, MATRRImage):
        raise Http404()
    if not im.verify_user_access_to_file(request.user):
        raise Http404()

    try:
        with open(im.html_fragment.path, 'r') as f:
            html = f.read()
    except:
        raise Http404()

    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=result, link_callback=gizmo.fetch_resources)
    if not pdf.err:
        resp = HttpResponse(result.getvalue(), mimetype='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename=%s' % (im.get_filename() + '.pdf')
        return resp
    raise Http404()

def create_svg_fragment(request, klass, imageID):
    import matrr.models as mmodels
    im = get_object_or_404(getattr(mmodels, klass), pk=imageID)
    if not isinstance(im, MATRRImage):
        raise Http404()
    if not im.verify_user_access_to_file(request.user):
        raise Http404()
    image_data = open(os.path.join(settings.MEDIA_ROOT, im.svg_image.name), "rb").read()
    resp = HttpResponse(image_data, mimetype="image/svg+xml")
    resp['Content-Disposition'] = 'attachment; filename=%s' % (im.get_filename() + '.svg')
    return resp

