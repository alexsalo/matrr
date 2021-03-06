from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.http import HttpResponse
from matrr import forms, models
from matrr.models import Cohort, MonkeyBrainBlock, TissueType, MonkeyImage, Availability, DataIntegrationTracking

inventory_landing = user_passes_test(lambda u: u.has_perm('matrr.browse_inventory'), login_url='/denied/')(
    ListView.as_view(model=Cohort, template_name="matrr/inventory/inventory.html")
)

@user_passes_test(lambda u: u.has_perm('matrr.browse_inventory'), login_url='/denied/')
def inventory_cohort(request, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    tsts = TissueType.objects.all().order_by('category__cat_name', 'tst_tissue_name')
    monkeys = cohort.monkey_set.all()
    availability_matrix = list()
    #	y tst, x monkey

    if cohort.coh_upcoming:
        messages.warning(request,
                         "This cohort is upcoming, green color indicates future possible availability, however this tissues are NOT is stock.")
        for tst in tsts:
            tst_row = dict()
            tst_row['row'] = list()
            tst_row['title'] = tst.tst_tissue_name
            for mky in monkeys:
                tst_row['row'].append(tst.get_monkey_from_coh_upcoming_availability(mky))
            availability_matrix.append(tst_row)
    else:
        for tst in tsts:
            tst_row = dict()
            tst_row['row'] = list()
            tst_row['title'] = tst.tst_tissue_name
            in_stock_mky_ids = tst.get_directly_in_stock_available_monkey_ids()
            for mky in monkeys:
                if mky.mky_id in in_stock_mky_ids:
                    tst_row['row'].append(Availability.In_Stock)
                else:
                    tst_row['row'].append(Availability.Unavailable)
            availability_matrix.append(tst_row)
    return render_to_response('matrr/inventory/inventory_cohort.html',
                              {"cohort": cohort, "monkeys": monkeys, "matrix": availability_matrix}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_tissuesample'), login_url='/denied/')
def inventory_brain_cohort(request, coh_id):
    cohort = get_object_or_404(Cohort, pk=coh_id)
    brains = MonkeyImage.objects.filter(method='__brain_image', monkey__cohort=cohort)

    cohort.brains = brains.order_by('monkey')
    return render_to_response('matrr/inventory/inventory_brain_cohort.html', {"cohort": cohort}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_tissuesample'), login_url='/denied/')
def inventory_brain_monkey(request, mig_id):
    mig = get_object_or_404(MonkeyImage, pk=mig_id)
    monkey = mig.monkey

    if request.method == 'POST':
        brain_form = forms.InventoryBrainForm(data=request.POST)
        if brain_form.is_valid():
            data = brain_form.cleaned_data
            mbb = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_block_name=data['block'], mbb_hemisphere='L')
            mbb.assign_tissues(data['left_tissues'])
            mbb = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_block_name=data['block'], mbb_hemisphere='R')
            mbb.assign_tissues(data['right_tissues'])
        else:
            messages.error(request, "Invalid form submission")
    else:
        brain_form = forms.InventoryBrainForm()

    blocks = MonkeyBrainBlock.objects.all().values_list('mbb_block_name', flat=True).distinct().count()
    matrix = list()
    show_grid = request.GET.get('show_grid', '0') == '1'
    if show_grid:
        blocks = ['%02d' % i for i in range(1, blocks + 1, 1)]
        # Current Matrix:
        for tst in TissueType.objects.filter(category__cat_name__icontains='brain').order_by('tst_tissue_name'):
            tst_row = dict()
            tst_row['row'] = list()
            tst_row['title'] = tst.tst_tissue_name
            for block in blocks:
                brain = list()
                left_hemi = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_hemisphere='L', mbb_block_name__contains=block)
                right_hemi = MonkeyBrainBlock.objects.get(monkey=monkey, mbb_hemisphere='R', mbb_block_name__contains=block)
                brain.append(1 if tst in left_hemi.tissue_types.all() else 0)
                brain.append(1 if tst in right_hemi.tissue_types.all() else 0)
                tst_row['row'].append(brain)
            matrix.append(tst_row)

    context = {"plot_gallery": True, "monkey": monkey, 'brain_form': brain_form, 'image': mig, 'matrix': matrix,'blocks': blocks, 'show_grid': show_grid}
    return render_to_response('matrr/inventory/inventory_brain_monkey.html', context, context_instance=RequestContext(request))


class DataIntegrationTrackingView(View):
    def permission_decorator(self):
        return user_passes_test(lambda u: u.has_perm('matrr.view_dit_data'), login_url='/denied/')

#    @method_decorator(permission_decorator)
    def get(self, request, *args, **kwargs):
        dit_form = forms.DataIntegrationTrackingForm()
        dit_results = DataIntegrationTracking.objects.all().order_by('cohort__coh_cohort_name')
        fields = list(dit_results[0]._meta.fields)
        fields.pop(0)
        headers = [f.verbose_name for f in fields]
        field_names = [f.name for f in fields]
        field_names[0] = 'cohort__coh_cohort_name'
        dit_results = dit_results.values_list(*field_names)
        return render_to_response('matrr/inventory/data_integration_tracking.html', {'headers': headers, 'dit_results': dit_results, 'dit_form': dit_form}, context_instance=RequestContext(request))

#    @method_decorator(permission_decorator)
    def post(self, request, *args, **kwargs):
        dit_form = forms.DataIntegrationTrackingForm(data=request.POST)
        if dit_form.is_valid():
            dit, is_new = DataIntegrationTracking.objects.get_or_create(cohort=dit_form.cleaned_data['cohort'])
            dit_form = forms.DataIntegrationTrackingForm(data=request.POST, instance=dit)
            dit_form.save()
            messages.success(request, "Data has been saved.")
            return redirect(reverse('data-integration-tracking'))
        return render_to_response('matrr/inventory/data_integration_tracking.html', {'dit_form': dit_form}, context_instance=RequestContext(request))
