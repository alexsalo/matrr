"""
These functions are designed to be called generically to perform a specialized operation on a generalized input.

Alone, these functions are close to useless.  however, with the the general plotting method for which they are designed
they can be quite useful, especially for reducing/eliminating redundant code.

"""
__author__ = 'developer'
from django.db.models import Avg
from matrr.models import NecropsySummary, MonkeyBEC, MonkeyToDrinkingExperiment


def etoh_intake(queryset):
    return queryset.exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')

def total_pellets(queryset):
    return queryset.exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')

def veh_intake(queryset):
    return queryset.exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')

def mtd_weight(queryset):
    return queryset.exclude(mtd_weight=None).values_list('mtd_weight')

def necropsy_summary_avg_with_days_22hr_g_per_kg(queryset):
    """
    This method, used by necropsy graphs, will collect 12 month and 6 month average g/kg etoh intake for the [queryset]

    Args:
    queryset is expected to be a queryset of monkeys

    return:
    tuple, ( list of 6 month averages, list of 12 month averages, number of actual days 6 months, number of actual days
    in 12 months OA, list of monkey pk labels )
    """
    summaries = []
    raw_labels = []
    days = []
    days_2 = []

    for mky in queryset.order_by("necropsy_summary__ncm_22hr_12mo_avg_gkg", "necropsy_summary__ncm_22hr_1st_6mo_avg_gkg"):
        try:
            summaries.append(mky.necropsy_summary)
            days_2.append(MonkeyToDrinkingExperiment.objects.OA().first_six_months_oa().exclude_exceptions().
                          filter(monkey=mky).count())
            days.append(MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=mky).count())
        except NecropsySummary.DoesNotExist:
            continue
        raw_labels.append(str(mky.pk))
    return [summary.ncm_22hr_1st_6mo_avg_gkg for summary in summaries], \
           [summary.ncm_22hr_12mo_avg_gkg for summary in summaries], days_2, days, raw_labels

def necropsy_summary_avg_22hr_g_per_kg(queryset):
    """
    This method, used by necropsy graphs, will collect 12 month and 6 month average g/kg etoh intake for the [queryset]

    Args:
    queryset is expected to be a queryset of monkeys

    return:
    tuple, ( list of 6 month averages, list of 12 month averages, list of monkey pk labels )
    """
    summaries = []
    raw_labels = []
    for mky in queryset.order_by("necropsy_summary__ncm_22hr_12mo_avg_gkg", "necropsy_summary__ncm_22hr_1st_6mo_avg_gkg"):
        try:
            summaries.append(mky.necropsy_summary)
        except NecropsySummary.DoesNotExist:
            continue
        raw_labels.append(str(mky.pk))
    return [summary.ncm_22hr_1st_6mo_avg_gkg for summary in summaries], [summary.ncm_22hr_12mo_avg_gkg for summary in summaries], raw_labels

def necropsy_summary_with_days_etoh_4pct(queryset):
    """
    This method, used by necropsy graphs, will collect 22hr and lifetime etoh intake (in ml) for the [queryset]

    Args:
    queryset is expected to be a queryset of monkeys

    return:
    tuple, ( list of open access total intakes, list of lifetime total intakes, list of monkey pk labels )
    """
    summaries = []
    raw_labels = []
    days = []
    days_2 = []
    for mky in queryset.order_by("necropsy_summary__ncm_etoh_sum_ml_4pct_lifetime", "necropsy_summary__ncm_etoh_sum_ml_4pct_22hr"):
        try:
            summaries.append(mky.necropsy_summary)
            days_2.append(MonkeyToDrinkingExperiment.objects.OA().first_six_months_oa().exclude_exceptions().
                          filter(monkey=mky).count())
            days.append(MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=mky).count())
        except NecropsySummary.DoesNotExist:
            continue
        raw_labels.append(str(mky.pk))
    return [summary.ncm_etoh_sum_ml_4pct_22hr for summary in summaries], [summary.ncm_etoh_sum_ml_4pct_lifetime for summary in summaries],\
           days_2, days, raw_labels

def necropsy_summary_etoh_4pct(queryset):
    """
    This method, used by necropsy graphs, will collect 22hr and lifetime etoh intake (in ml) for the [queryset]

    Args:
    queryset is expected to be a queryset of monkeys

    return:
    tuple, ( list of open access total intakes, list of lifetime total intakes, list of monkey pk labels )
    """
    summaries = []
    raw_labels = []
    for mky in queryset.order_by("necropsy_summary__ncm_etoh_sum_ml_4pct_lifetime", "necropsy_summary__ncm_etoh_sum_ml_4pct_22hr"):
        try:
            summaries.append(mky.necropsy_summary)
        except NecropsySummary.DoesNotExist:
            continue
        raw_labels.append(str(mky.pk))
    return [summary.ncm_etoh_sum_ml_4pct_22hr for summary in summaries], [summary.ncm_etoh_sum_ml_4pct_lifetime for summary in summaries], raw_labels

def necropsy_summary_with_days_sum_g_per_kg(queryset):
    summaries = []
    raw_labels = []
    days = []
    days_2 = []
    for mky in queryset.order_by("necropsy_summary__ncm_etoh_sum_gkg_22hr", "necropsy_summary__ncm_etoh_sum_gkg_lifetime"):
        try:
            summaries.append(mky.necropsy_summary)
            days_2.append(MonkeyToDrinkingExperiment.objects.OA().first_six_months_oa().exclude_exceptions().filter(monkey=mky).count())
            days.append(MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=mky).count())
        except NecropsySummary.DoesNotExist:
            continue
        raw_labels.append(str(mky.pk))
    return [summary.ncm_etoh_sum_gkg_22hr for summary in summaries], [summary.ncm_etoh_sum_gkg_lifetime for summary in summaries],\
        days_2, days, raw_labels

def necropsy_summary_sum_g_per_kg(queryset):
    """
    This method, used by necropsy graphs, will collect 22hr and lifetime etoh intake (in g/kg) for the [queryset]

    Args:
    queryset is expected to be a queryset of monkeys

    return:
    tuple, ( list of open access total intakes, list of lifetime total intakes, list of monkey pk labels )
    """
    summaries = []
    raw_labels = []
    for mky in queryset.order_by("necropsy_summary__ncm_etoh_sum_gkg_22hr", "necropsy_summary__ncm_etoh_sum_gkg_lifetime"):
        try:
            summaries.append(mky.necropsy_summary)
        except NecropsySummary.DoesNotExist:
            continue
        raw_labels.append(str(mky.pk))
    return [summary.ncm_etoh_sum_gkg_22hr for summary in summaries], [summary.ncm_etoh_sum_gkg_lifetime for summary in summaries], raw_labels

def summary_avg_bec_mgpct(queryset):
    """
    This method, used by necropsy graphs, will collect 12 month and 6 month average bec of the [queryset]

    Args:
    queryset is expected to be a queryset of monkeys

    return:
    tuple, ( list of 6 month averages, list of 12 month averages, list of monkey pk labels )
    """
    # twelve_mo_avg = list()
    # six_months_avg = list()
    # labels = list()
    # for mky in queryset.order_by("necropsy_summary__ncm_22hr_12mo_avg_gkg", "necropsy_summary__ncm_22hr_1st_6mo_avg_gkg"):
    #     _oa_becs = MonkeyBEC.objects.OA().filter(monkey=mky)
    #     _6mo_becs = _oa_becs.first_six_months_oa()
    #
    #     _12mo_avg_mgpct = _oa_becs.aggregate(avg=Avg('bec_mg_pct'))['avg']
    #     _6mo_avg_mgpct = _6mo_becs.aggregate(avg=Avg('bec_mg_pct'))['avg']
    #
    #     if not (_12mo_avg_mgpct or _6mo_avg_mgpct):
    #         continue
    #     twelve_mo_avg.append(_12mo_avg_mgpct)
    #     six_months_avg.append(_6mo_avg_mgpct)
    #     labels.append(str(mky.pk))
    #
    # # sort the three matched lists by the 12 month average
    # twelve_mo_avg, six_months_avg, labels = zip(*sorted(zip(twelve_mo_avg, six_months_avg, labels)))
    # # python is badass, amirite? Nope! This is ugly! Use dataframes instead

    nc = NecropsySummary.objects.filter(monkey__in=queryset)
    import pandas as pd
    df = pd.DataFrame(list(nc.values_list('monkey__mky_id', 'ncm_22hr_1st_6mo_avg_gkg', 'ncm_22hr_12mo_avg_gkg')),
                      columns=['mky_id', 'ncm_22hr_1st_6mo_avg_gkg', 'ncm_22hr_12mo_avg_gkg'])
    df.sort(['ncm_22hr_1st_6mo_avg_gkg', 'ncm_22hr_12mo_avg_gkg'], inplace=True)
    if df.ncm_22hr_12mo_avg_gkg[0] is None:
        df.ncm_22hr_12mo_avg_gkg = df.ncm_22hr_1st_6mo_avg_gkg
    return list(df.ncm_22hr_1st_6mo_avg_gkg), list(df.ncm_22hr_12mo_avg_gkg), list(df.mky_id)
