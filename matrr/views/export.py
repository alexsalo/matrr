__author__ = 'alex'
import csv
from django.http import HttpResponse
from matrr.models import *

def export_cohort_data(request, **kwargs):
    coh_cohort_id = kwargs['coh_id']
    cohort = Cohort.objects.get(coh_cohort_id = coh_cohort_id)
    monkeys = cohort.monkey_set.all()
    filename = lower(str(cohort.coh_cohort_name)) + "_data.csv"
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+filename
    #coh_cohort_id = 3
    writer = csv.writer(response)
    writer.writerow([
        'sum_etoh_1st_6mo_gkg',
        'days',
        'sum_etoh_2nd_6mo_gkg',
        'days',
        'sum_etoh_total_gkg',
        'days',
        'sum_veh_1st_6mo_ml',
        'sum_veh_2nd_6mo_ml',
        'sum_veh_total_ml',
        'avg_BEC_1st_6mo_ml',
        'days',
        'avg_BEC_2nd_6mo_ml',
        'days',
        'avg_BEC_total_ml',
        'days'
    ])

    for monkey in monkeys:
        etoh1_a, etoh1_b = monkey.sum_etoh_1st_6mo_gkg() #value, days
        etoh2_a, etoh2_b = monkey.sum_etoh_2nd_6mo_gkg()
        etoht_a, etoht_b = monkey.sum_etoh_total_gkg()

        bec1_a, bec1_b = monkey.avg_BEC_1st_6mo_ml()
        bec2_a, bec2_b = monkey.avg_BEC_2nd_6mo_ml()
        bect_a, bect_b = monkey.avg_BEC_total_ml()
        writer.writerow([
            etoh1_a,
            etoh1_b,
            etoh2_a,
            etoh2_b,
            etoht_a,
            etoht_b,
            monkey.sum_veh_1st_6mo_ml(),
            monkey.sum_veh_2nd_6mo_ml(),
            monkey.sum_veh_total_ml(),
            bec1_a,
            bec1_b,
            bec2_a,
            bec2_b,
            bect_a,
            bect_b
        ])
    # writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    # writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response