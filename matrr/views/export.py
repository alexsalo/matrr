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
        'Total_etoh_during_first_6mo',
        'Total_etoh_during_second_6mo',
        'Total_etoh',
        'avg_BEC_1st_6mo',
        'avg_BEC_all',
        'Total_veh_during_first_6mo',
        'Total_veh_during_second_6mo',
        'Total_veh'
    ])

    for monkey in monkeys:
        writer.writerow([
            monkey.Total_etoh_during_first_6mo(),
            monkey.Total_etoh_during_second_6mo(),
            monkey.Total_etoh(),
            monkey.avg_BEC_1st_6mo(),
            monkey.avg_BEC_all(),
            monkey.Total_veh_during_first_6mo(),
            monkey.Total_veh_during_second_6mo(),
            monkey.Total_veh()
        ])
    # writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    # writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response