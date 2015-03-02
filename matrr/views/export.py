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
        row = list(monkey.sum_etoh_gkg_by_period())
        row += list(monkey.sum_veh_ml_by_period())
        row += list(monkey.avg_BEC_pct_by_period())
        writer.writerow(row)
    # writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    # writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response