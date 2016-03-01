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
        'MID',
        '1st_6mo_sum_etoh_gkg',
        '2nd_6mo_sum_etoh_gkg',
        'total_sum_etoh_gkg',

        '1st_6mo_avg_etoh_gkg',
        '2nd_6mo_avg_etoh_gkg',
        'total_avg_etoh_gkg',

        '1st_6mo_sum_H2O_ml',
        '2dn_6mo_sum_H2O_ml',
        'total_sum_H2O_ml',

        '1st_6mo_avg_H2O_ml',
        '2dn_6mo_avg_H2O_ml',
        'total_avg_H2O_ml',

        '1st_6mo_days',
        '2dn_6mo_days',
        'total_days',

        '1st_6mo_avg_BEC_pct',
        'Ds',
        '2nd_6mo_avg_BEC_pct',
        'Ds',
        'total_avg_BEC_pct',
        'Ds'
    ])

    for monkey in monkeys:
        row = [monkey.mky_id]
        row += list(monkey.sum_etoh_gkg_by_period())
        row += list(monkey.avg_etoh_gkg_by_period())
        row += list(monkey.sum_veh_ml_by_period())
        row += list(monkey.avg_veh_ml_by_period())

        row += list(monkey.avg_BEC_pct_by_period())

        writer.writerow(row)
    # writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    # writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response