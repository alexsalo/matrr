from datetime import datetime as dt
from datetime import timedelta, time
import dateutil.parser
import string
import django.template.loader as template_loader
import csv
import re
import gc
import logging

from django.db.models.query import QuerySet
from django.db.transaction import commit_on_success
from django.db import transaction

from matrr.models import *
from matrr.utils import gadgets

# dumps the monkey table to a csv
def dump_monkey_data():
    f = open('MATRR_Monkeys.csv', 'w')
    output = csv.writer(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    columns = [
        'mky_id',
        'cohort', # doesnt work with getattr()
        'mky_real_id',
        'mky_name',
        'mky_gender',
        'mky_birthdate',
        'mky_weight',
        'mky_drinking',
        'mky_housing_control',
        'mky_necropsy_start_date',
        'mky_necropsy_start_date_comments',
        'mky_necropsy_end_date',
        'mky_necropsy_end_date_comments',
        'mky_study_complete',
        'mky_stress_model',
        'mky_age_at_necropsy',
        'mky_notes',
        'mky_species',
        'mky_high_drinker',
        'mky_low_drinker',
        'mky_age_at_intox'
    ]
    output.writerow(columns)
    for mky in Monkey.objects.all().order_by('cohort', 'pk'):
        row = list()
        for col in columns:
            if col == 'cohort':
                row.append(mky.cohort.coh_cohort_name)
            else:
                row.append(getattr(mky, col))
        output.writerow(row)
    f.flush()
    f.close()

## Dumps database rows into a CSV.  I'm sure i'll need this again at some point
## -jf
def dump_all_TissueSample(output_file):
    """
        This function will dump existing tissue samples to CSV
        It writes columns in this order
        0 - Category.cat_internal
        1 - Category.parent_category
        2 - Catagory.cat_name
        3 - Category.cat_description
        --- Empty
        4 - TissueType.tst_tissue_name
        5 - TissueType.tst_description
        6 - TissueType.tst_count_per_monkey
        7 - TissueType.tst_cost
        --- Empty
        8 - TissueSample.tss.monkey
        9 - TissueSample.tss_details
        10- TissueSample.tss_freezer
        11- TissueSample.tss_location
        12- TissueSample.tss_sample_count
        13- TissueSample.tss_distributed_count

    """
    output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    columns = \
        ["Internal Category", "Parent Category", "Category:Name", "Category:Description", "Empty Column",
         "TissueType:Name", "TissueType:Description", "TissueType:count_per_monkey",
         "TissueType:cost", "Empty Column", "TissueSample:Monkey", "TissueSample:Details", "TissueSample:Freezer",
         "TissueSample:Location", "TissueSample:sample_count",
         "TissueSample:distributed_count"]
    output.writerow(columns)

    for TS in TissueSample.objects.all():
        row = []
        row[len(row):] = [str(TS.tissue_type.category.cat_internal)]
        row[len(row):] = [str(TS.tissue_type.category.parent_category)]
        row[len(row):] = [str(TS.tissue_type.category.cat_name)]
        row[len(row):] = [str(TS.tissue_type.category.cat_description)]
        row[len(row):] = [" "]
        row[len(row):] = [str(TS.tissue_type.tst_tissue_name)]
        row[len(row):] = [str(TS.tissue_type.tst_description)]
        row[len(row):] = [" "]
        row[len(row):] = [TS.monkey]
        row[len(row):] = [str(TS.tss_details)]
        row[len(row):] = [str(TS.tss_freezer)]
        row[len(row):] = [str(TS.tss_location)]
        row[len(row):] = [TS.tss_sample_count]
        row[len(row):] = [TS.tss_distributed_count]
        output.writerow(row)
    print "Success"

## Dumps database rows into a CSV.  I'm sure i'll need this again at some point
## -jf
def dump_distinct_TissueType(output_file):
    """
        This function will dump existing tissue catagories and tissuetypes to CSV
        It writes columns in this order
        0 - Catagory.cat_name
        1 - TissueType.tst_tissue_name
    """
    output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    columns = \
        ["Category:Name", "TissueType:Name"]
    output.writerow(columns)

    for TT in TissueType.objects.distinct().order_by("category"):
        row = []
        row[len(row):] = [str(TT.category.cat_name)]
        row[len(row):] = [str(TT.tst_tissue_name)]
        output.writerow(row)
    print "Success."

def dump_monkey_protein_data(queryset, output_file):
    if isinstance(queryset, QuerySet) and isinstance(queryset[0], MonkeyProtein):
        with open(output_file, 'w') as f:
            output = csv.writer(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
            columns = ['monkey', 'protein', 'mpn_date', 'mpn_value']
            output.writerow(columns)
            for mpn in queryset:
                output.writerow([mpn.monkey, "%s" % mpn.protein.pro_name, mpn.mpn_date, mpn.mpn_value])
    else:
        raise Exception("queryset kwarg can only be a QuerySet of MonkeyProteins.")

def dump_MATRR_stats():
    """
    Returns a string

    String contains MATRR stats for each year (ending May 31) since project launch (2010)

    Stats include:
    New user signups
    Submitted+ request count
    Requested tissue count
    Accepted tissue count
    Rejected tissue count
    Shipped shipment count
    Shipped tissue count
    Cohort count
    Monkey count
    Brain tissue inventory count (total)
    Peripheral tissue inventory count (total)
    """
    accepted = ['AC', 'PA', 'SH']
    official = ['SB', 'RJ', 'AC', 'PA', 'SH']
    project_start = 2010
    current_year = dt.now().year if dt.now().month < 6 else dt.now().year + 1
    dates = [("%s-06-01" % `year`, "%s-05-31" % `year + 1`) for year in range(project_start, current_year)]

    requests = Request.objects.filter(req_status__in=official)

    output = ''
    for start_date, end_date in dates:
        output += "For the daterange %s -> %s:\n" % (start_date, end_date)
        yearly_requests = requests.filter(req_request_date__gte=start_date).filter(req_request_date__lte=end_date)
        # User stats
        output += "Users joined: %d\n" % User.objects.filter(date_joined__gte=start_date).filter(
            date_joined__lte=end_date).count()
        # Request stats
        for o in official:
            output += "%s Requests: %d\n" % (o, yearly_requests.filter(req_status=o).count())
        # requested tissue stats
        requested_tissues = yearly_requests.aggregate(Count('tissue_request_set__monkeys'))['tissue_request_set__monkeys__count']
        output += "Requested Tissues: %d\n" % requested_tissues
        # accepted tissue stats
        approved_yearly_requests = yearly_requests.filter(req_status__in=accepted)
        approved_tissues = approved_yearly_requests.aggregate(Count('tissue_request_set__monkeys'))[
            'tissue_request_set__monkeys__count']
        output += "Accepted Tissues: %d\n" % approved_tissues
        # rejected tissue stats
        rejected_yearly_requests = yearly_requests.filter(req_status='RJ')
        rejected_tissues = rejected_yearly_requests.aggregate(Count('tissue_request_set__monkeys'))[
            'tissue_request_set__monkeys__count']
        partially_requested = 0
        partially_accepted = 0
        for part_acc in yearly_requests.filter(req_status="PA"):
            partially_requested += part_acc.tissue_request_set.all().aggregate(Count('monkeys'))['monkeys__count']
            partially_accepted += part_acc.tissue_request_set.all().aggregate(Count('accepted_monkeys'))[
                'accepted_monkeys__count']
        rejected_tissues += (partially_requested - partially_accepted)
        output += "Rejected Tissues: %d\n" % rejected_tissues
        # shipment stats
        yearly_shipments = Shipment.objects.filter(shp_shipment_date__gte=start_date).filter(
            shp_shipment_date__lte=end_date)
        output += "Shipped Shipments: %d\n" % yearly_shipments.count()
        output += "Shipped Tissues: %d\n" % yearly_shipments.aggregate(Count('tissue_request_set__monkeys'))[
            'tissue_request_set__monkeys__count']
        output += '-------\n'
    # Cohort/Monkey stats
    output += "Number of Cohorts:  %d\n" % Cohort.objects.all().count()
    output += "Number of Monkeys:  %d\n" % Monkey.objects.all().count()
    # inventory stats
    available_monkey_count = Monkey.objects.filter(cohort__coh_upcoming=False).count()
    brain_tissue_count = TissueType.objects.filter(category__cat_name='Brain Tissues').count()
    peripheral_tissue_count = TissueType.objects.filter(
        category__cat_name="Peripheral Tissues").count() + 1 # +1 is an internal 'serum' tissue in the "Interal Peripheral Tissue" category
    output += "Brain Tissue Inventory: %d tissues\n" % (brain_tissue_count * available_monkey_count)
    output += "Peripheral Tissue Inventory: %d tissues\n" % (peripheral_tissue_count * available_monkey_count)
    return output

def dump_MATRR_current_data_grid(dump_json=True, dump_csv=False):
    cohorts = Cohort.objects.all().exclude(coh_cohort_name__icontains='devel').order_by('pk')
    data_types = ["Necropsy", "Drinking Summary", "Bouts", "Drinks", "Raw Drinking data", "Exceptions", "BEC", "Hormone", "Metabolite", "Protein", 'ElectroPhys', ]
    data_classes = [NecropsySummary, MonkeyToDrinkingExperiment, ExperimentBout, ExperimentDrink, ExperimentEvent, MonkeyException, MonkeyBEC, MonkeyHormone, MonkeyMetabolite, MonkeyProtein, MonkeyEphys]
    cohort_fields = ['monkey__cohort', 'monkey__cohort', 'mtd__monkey__cohort', 'ebt__mtd__monkey__cohort', 'monkey__cohort', 'monkey__cohort', 'monkey__cohort', 'monkey__cohort', 'monkey__cohort', 'monkey__cohort', 'monkey__cohort', ]

    headers = ['Data Type']
    headers.extend(cohorts.values_list('coh_cohort_name', flat=True))
    data_rows = list()
    for _type, _field, _class in zip(data_types, cohort_fields, data_classes):
        _row = [_type, ]
        for _cohort in cohorts:
            row_count = _class.objects.filter(**{_field: _cohort}).count()
            _row.append(row_count)
        data_rows.append(_row)

    if dump_csv:
        outcsv = open('matrr/utils/DATA/current_data_grid.csv', 'w')
        writer = csv.writer(outcsv)
        writer.writerow(headers)
        writer.writerows(data_rows)
        outcsv.close()
    if dump_json:
        context = {'headers': headers, 'data_rows': data_rows, 'last_updated': datetime.now().strftime('%Y-%m-%d') }
        outjson = open('matrr/utils/DATA/json/current_data_grid.json', 'w')
        json_string = json.dumps(context)
        outjson.write(json_string)
        outjson.close()

def find_outlier_datapoints(cohort, stdev_min):
    search_models = [MonkeyToDrinkingExperiment, MonkeyBEC, ]# ExperimentEvent, ExperimentBout, ExperimentDrink]
    search_field = ['monkey__cohort',
                    'monkey__cohort', ]#'monkey__cohort', 'mtd__monkey__cohort', 'mtd__ebt__monkey__cohort']

    field_types = [models.FloatField, models.IntegerField, models.BigIntegerField, models.PositiveIntegerField,
                   models.PositiveSmallIntegerField, models.SmallIntegerField]

    for model, search in zip(search_models, search_field):
        search_field_names = list()
        for field in model._meta.fields:
            if type(field) in field_types:
                search_field_names.append(field.name)
        for _name in search_field_names:
            all_rows = model.objects.filter(**{search: cohort}).exclude(**{_name: None})
            if all_rows.count():
                all_values = all_rows.values_list(_name, flat=True)
                all_values = numpy.array(all_values)
                mean = all_values.mean()
                std = all_values.std()
                low_std = mean - stdev_min * std
                high_std = mean + stdev_min * std
                low_search_dict = {_name + "__lt": low_std}
                high_search_dict = {_name + "__gt": high_std}
                low_outliers = all_rows.filter(**low_search_dict)
                high_outliers = all_rows.filter(**high_search_dict)

                if low_outliers or high_outliers:
                    output_file = "%d.%s__%s-outliers.csv" % (cohort, model.__name__, _name)
                    output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                    header = ["Outlier Value", "Mean value", "StDev"]
                    all_field_names = [f.name for f in model._meta.fields]
                    header.extend(all_field_names)
                    output.writerow(header)
                    for out in low_outliers | high_outliers:
                        row = list()
                        row.append(getattr(out, _name))
                        row.append(mean)
                        row.append(std)
                        for f in all_field_names:
                            row.append(getattr(out, f))
                        output.writerow(row)
            else:
                print "No data: %s " % _name

    print 'done'

def dump_tissue_inventory_csv(cohort):
    """
        This function will dump the browse inventory page to CSV
        It writes columns == monkey, row == tissue.
        Cells where the tissue exists are given "Exists", non-existent tissues are left blank.
    """
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    filename = str(cohort).replace(' ', '_') + "-Inventory.csv"
    output = csv.writer(open(filename, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    columns = ["Tissue Type \ Monkey"]
    columns.extend(["%s/%s" % (str(m.pk), str(m.mky_real_id)) for m in cohort.monkey_set.all().order_by('pk')])
    output.writerow(columns)

    for tst in TissueType.objects.all().order_by('category__cat_name', 'tst_tissue_name'):
        row = [tst.tst_tissue_name]
        for mky in cohort.monkey_set.all().order_by('pk'):
            availability = tst.get_monkey_availability(mky)
            if availability == Availability.Unavailable:
                row.append("")
            else:
                row.append("Exists")
        output.writerow(row)
    print "Success."

def dump_rhesus_summed_gkg_by_quarter():
    f = open('summed_gkg_by_category.csv', 'w')
    writer = csv.writer(f)
    writer.writerow([
        'cohort', 'monkey',
        '12mo summed gkg', '12mo category',
        'first 3mo summed gkg', 'first 3mo category',
        'second 3mo summed gkg', 'second 3mo category',
        'third 3mo summed gkg', 'third 3mo category',
        'fourth 3mo summed gkg', 'fourth 3mo category'
    ])

    data_rows = list()
    for cohort_name, cohort_pk  in Cohort.objects.filter(pk__in=[5,6,9,10]).order_by('coh_cohort_name').values_list('coh_cohort_name', 'pk'):
        for monkey_pk in Monkey.objects.Drinkers().filter(cohort=cohort_pk).order_by('pk').values_list('pk', flat=True):
            row = list()
            row.extend([cohort_name, monkey_pk])

            oa_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            first_mtds = oa_mtds.first_three_months_oa()
            second_mtds = oa_mtds.second_three_months_oa()
            third_mtds = oa_mtds.third_three_months_oa()
            fourth_mtds = oa_mtds.fourth_three_months_oa()
            mtd_sets = [oa_mtds, first_mtds, second_mtds, third_mtds, fourth_mtds]

            for _mtds in mtd_sets:
                gkg_sum = _mtds.aggregate(Sum('mtd_etoh_g_kg'))['mtd_etoh_g_kg__sum']
                period_category = gadgets.identify_drinking_category(_mtds)
                row.append(gkg_sum)
                row.append(period_category)
            data_rows.append(row)
    writer.writerows(data_rows)
    f.close()
    return

def dump_data_req_request_425_thru_431():
    from matrr.utils.parallel_plot import  percentage_of_days_over_4_gkg, percentage_of_days_over_3_gkg, \
        percentage_of_days_over_2_gkg, average_oa_etoh_intake_gkg, average_oa_bout_start_time, average_oa_daily_bout, \
        average_oa_bout_volume, average_oa_volume_first_bout, average_oa_bout_intake_rate, average_oa_bout_pct_volume, \
        average_oa_max_bout_pct_total_etoh, average_oa_bout_time_since_pellet, average_oa_drink_volume, \
        average_oa_pct_etoh_post_pellets, average_oa_pellet_intake, average_oa_water_intake, average_oa_BEC, \
        average_oa_BEC_pct_intake, average_oa_Cortisol, average_oa_ACTH, average_oa_Testosterone, \
        average_oa_Deoxycorticosterone, average_oa_Aldosterone, average_oa_DHEAS
    from matrr.models import Request, MonkeyToDrinkingExperiment, Monkey
    import csv
    # HOORAY for DRY principles :P

    def gather_monkey_data(monkey_pk):
        # I did have to (mostly) repeat this code though -.-
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk).order_by('drinking_experiment__dex_date')
        if mtds.count() < 1: # we need more data.  We always need more data.
            return [], []
        labels = ['matrr id' ]
        values = [str(monkey_pk), ]
        for gather_function in mtd_gather_functions:
            labels.append(gather_function()) # empty calls return the data's label
            values.append(gather_function(mtds)) # calls with mtd= calculate the described value given the input mtds
        return labels, values

    mtd_gather_functions = [
        percentage_of_days_over_4_gkg, percentage_of_days_over_3_gkg,
        percentage_of_days_over_2_gkg, average_oa_etoh_intake_gkg, average_oa_bout_start_time, average_oa_daily_bout,
        average_oa_bout_volume, average_oa_volume_first_bout, average_oa_bout_intake_rate, average_oa_bout_pct_volume,
        average_oa_max_bout_pct_total_etoh, average_oa_bout_time_since_pellet, average_oa_drink_volume,
        average_oa_pct_etoh_post_pellets, average_oa_pellet_intake, average_oa_water_intake, average_oa_BEC,
        average_oa_BEC_pct_intake, average_oa_Cortisol, average_oa_ACTH, average_oa_Testosterone,
        average_oa_Deoxycorticosterone, average_oa_Aldosterone, average_oa_DHEAS,
    ]
    req_requests = Request.objects.filter(pk__in=range(425, 432))
#    req_requests = Request.objects.filter(pk__in=(202,))
    cohorts = req_requests.values_list('cohort', flat=True)
    monkeys = Monkey.objects.filter(cohort__in=cohorts).order_by('cohort').values_list('pk', 'cohort__coh_cohort_name', 'mky_drinking')
    header = ['monkey', 'cohort', 'control']
    all_data = list()
    for mky in monkeys:
        labels, values = gather_monkey_data(mky[0])
        if not len(values):
            continue
        if len(header) == 3:
            header.extend(labels)
        row = [str(m) for m in mky]
        row[2] = not mky[2] # db stores drinkers, ie NOT control
        row.extend(values)
        all_data.append(row)
    f = open('dump_data_req_request_425_thru_431.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_data)
    f.flush()
    f.close()
    print "all done"
    return