__author__ = 'alex'
from matrr.models import CohortEvent, MonkeyToDrinkingExperiment, NecropsySummary, MonkeyBEC
import numpy as np

def populate_necropsy_summary(cohort):
    mtds_cohort = MonkeyToDrinkingExperiment.objects.filter(monkey__in=cohort.monkey_set.all())
    if not mtds_cohort.count():
        return

    print "\nCreating Necropsy Summaries for Cohort %s" % cohort

    # cohort's events
    try:
        evts = CohortEvent.objects.filter(cohort=cohort)

        etoh_ind_start     =evts.filter(event__evt_name__iexact='Ethanol Induction Begin').values_list('cev_date', flat=True)[0]
        etoh_ind_end       =evts.filter(event__evt_name__iexact='Ethanol Induction End').values_list('cev_date', flat=True)[0]

        etoh_1st_6_mo_start=evts.filter(event__evt_name__iexact='First 6 Month Open Access Begin').values_list('cev_date', flat=True)[0]
        etoh_1st_6_mo_end  =evts.filter(event__evt_name__iexact='First 6 Month Open Access End').values_list('cev_date', flat=True)[0]

        etoh_2nd_6_mo_start=evts.filter(event__evt_name__iexact='Second 6 Month Open Access Begin').values_list('cev_date', flat=True)[0]
        etoh_2nd_6_mo_end  =evts.filter(event__evt_name__iexact='Second 6 Month Open Access End').values_list('cev_date', flat=True)[0]
    except:
        print "    This cohort does't have proper cohort's events"
        return

    for monkey in cohort.monkey_set.filter(mky_drinking=True).filter(mky_study_complete=True):
        mtds = mtds_cohort.filter(monkey=monkey).filter(mtd_etoh_intake__isnull=False)
        if mtds.count():
            mtds_ind = mtds.filter(drinking_experiment__dex_type='Induction')
            mtds_oa = mtds.filter(drinking_experiment__dex_type='Open Access')

            ncm, created = NecropsySummary.objects.get_or_create(monkey=monkey)

            ncm.ncm_etoh_onset = etoh_ind_start
            ncm.ncm_onset_etoh_age = monkey.mky_birthdate - etoh_ind_start

            ncm.ncm_etoh_sum_ml_4pct_induction = np.sum(mtds_ind.values_list('mtd_etoh_intake', flat=True))
            ncm.ncm_etoh_sum_ml_4pct_22hr      = np.sum(mtds_oa.values_list('mtd_etoh_intake', flat=True))
            ncm.ncm_etoh_sum_ml_4pct_lifetime  = ncm.ncm_etoh_sum_ml_4pct_induction + ncm.ncm_etoh_sum_ml_4pct_22hr

            mtds_ind = mtds_ind.filter(mtd_etoh_g_kg__isnull=False)
            mtds_oa  = mtds_oa.filter(mtd_etoh_g_kg__isnull=False)
            ncm.ncm_etoh_sum_gkg_induction = np.sum(mtds_ind.values_list('mtd_etoh_g_kg', flat=True))
            ncm.ncm_etoh_sum_gkg_22hr      = np.sum(mtds_oa.values_list('mtd_etoh_g_kg', flat=True))
            ncm.ncm_etoh_sum_gkg_lifetime  = ncm.ncm_etoh_sum_gkg_induction + ncm.ncm_etoh_sum_gkg_22hr

            # cohort's events
            ncm.ncm_etoh_ind_start = etoh_ind_start
            ncm.ncm_etoh_ind_end   = etoh_ind_end

            ncm.ncm_1st_6_mo_start = etoh_1st_6_mo_start
            ncm.ncm_1st_6_mo_end   = etoh_1st_6_mo_end

            ncm.ncm_2nd_6_mo_start = etoh_2nd_6_mo_start
            ncm.ncm_2nd_6_mo_end   = etoh_2nd_6_mo_end

            # averages for first, second 6 months, and 12 months.
            mtds_avg = mtds_oa.exclude_exceptions()
            ncm.ncm_22hr_1st_6mo_avg_gkg = np.mean(mtds_avg.
                                                   filter(drinking_experiment__dex_date__gte=etoh_1st_6_mo_start).
                                                   filter(drinking_experiment__dex_date__lte=etoh_1st_6_mo_end).
                                                   values_list('mtd_etoh_g_kg', flat=True))
            ncm.ncm_22hr_2nd_6mo_avg_gkg = np.mean(mtds_avg.
                                                   filter(drinking_experiment__dex_date__gte=etoh_2nd_6_mo_start).
                                                   filter(drinking_experiment__dex_date__lte=etoh_2nd_6_mo_end).
                                                   values_list('mtd_etoh_g_kg', flat=True))
            ncm.ncm_22hr_12mo_avg_gkg    = np.mean([ncm.ncm_22hr_1st_6mo_avg_gkg, ncm.ncm_22hr_2nd_6mo_avg_gkg])

            # BEC
            becs = MonkeyBEC.objects.exclude_exceptions().filter(monkey=monkey).filter(bec_mg_pct__isnull=False)
            ncm.ncm_22hr_1st_6mo_avg_bec = np.mean(becs.filter(bec_collect_date__gte=etoh_1st_6_mo_start).
                                                   filter(bec_collect_date__lte=etoh_1st_6_mo_end).
                                                   values_list('bec_mg_pct', flat=True))
            ncm.ncm_22hr_2nd_6mo_avg_bec = np.mean(becs.filter(bec_collect_date__gte=etoh_2nd_6_mo_start).
                                                   filter(bec_collect_date__lte=etoh_2nd_6_mo_end).
                                                   values_list('bec_mg_pct', flat=True))
            ncm.ncm_22hr_12mo_avg_bec    = np.mean([ncm.ncm_22hr_1st_6mo_avg_bec, ncm.ncm_22hr_2nd_6mo_avg_bec])

            ncm.save()
            print "    %s" % str(monkey)