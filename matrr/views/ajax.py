import json
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import user_passes_test
from matrr.forms import AdvancedSearchFilterForm, AdvancedSearchSelectForm
from matrr.models import Monkey

@user_passes_test(lambda u: u.is_authenticated(), login_url='/denied/')
def ajax_advanced_search(request):
    show_ids = ['blank']
    hide_ids = ['blank']
    if request.POST:
        select_form = AdvancedSearchSelectForm(data=request.POST, prefix='select')
        if select_form.is_valid():
            select_query = Q()
            selects = select_form.cleaned_data
            if selects['sex']:
                select_query = select_query & Q(mky_gender__in=selects['sex'])
            if selects['species']:
                select_query = select_query & Q(mky_species__in=selects['species'])

            filter_form = AdvancedSearchFilterForm(data=request.POST, prefix='filter')
            if filter_form.is_valid():
                filters = filter_form.cleaned_data
                if filters['control']:
                    select_query = select_query & (Q(mky_drinking=False) | Q(mky_housing_control=True))

                ### Commented by Alex Salo. I believe that's incorrect and inconsistent way to do it. Filter should AND
                ### not OR stuff. However, I failed to make a correct implementaion. S leave it as it is.

                if filters['proteins']:
                    select_query = select_query & Q(protein_set__mpn_stdev__gte=1,
                                                    protein_set__protein__in=filters['proteins'])
                ### New implementation
                # if filters['proteins']:
                #     for protein in filters['proteins']:
                #         print protein
                #         _query = "protein_set__mpn_stdev__gte"
                #         _query_less = "protein_set__mpn_stdev__lte"
                #         select_query = select_query & (Q(**{_query:1}) | Q(**{_query_less:-1})) & Q(protein_set__protein=protein)

                if filters['cohorts']:
                    select_query = select_query & Q(cohort__in=filters['cohorts'])
                if filters['hormones']:
                    for hormone in filters['hormones']:
                        _query = "hormone_records__%s_stdev__gte" % hormone
                        _query_less = "hormone_records__%s_stdev__lte" % hormone
                        select_query = select_query & (Q(**{_query:1}) | Q(**{_query_less:-1}))

                if filters['drinking_category']: # add in 14 Oct,2104 by Yong Shui
                    select_query = select_query & Q(mky_drinking_category__in=filters['drinking_category'])

                if filters['bone_density']:
                    for bone_value in filters['bone_density']:
                        #print bone_value
                        _query = "bdy_records__%s_stdev__gte" % bone_value
                        _query_less = "bdy_records__%s_stdev__lte" % bone_value
                        select_query = select_query & (Q(**{_query:1}) | Q(**{_query_less:-1}))

            if select_query:
                #print select_query
                show_ids = Monkey.objects.filter(select_query).values_list('mky_id', flat=True).distinct()
            else:
                show_ids = Monkey.objects.none()
            hide_ids = Monkey.objects.exclude(pk__in=show_ids).values_list('mky_id', flat=True).distinct()
            hide_ids = list(hide_ids)
            show_ids = list(show_ids)

        return HttpResponse(json.dumps({'show_ids': show_ids, 'hide_ids': hide_ids}), content_type='application/json')
    else:
        raise Http404
