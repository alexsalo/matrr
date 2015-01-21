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

@transaction.commit_on_success
# Creates ALL tissue samples in the database, for every monkey:tissuetype combination.
def create_TissueSamples(tissue_type=None):
    units = Units[2][0]
    for monkey in Monkey.objects.all():
        quantity = 0
        if not tissue_type:
            tissuetypes = TissueType.objects.all()
            # Only create the "be specific" tissue samples for upcoming cohorts
            if monkey.cohort.coh_upcoming:
                quantity = 1
            else:
                tissuetypes = tissuetypes.exclude(tst_tissue_name__icontains="Be specific")
        else:
            tissuetypes = [tissue_type]

        for tt in tissuetypes:
            sample, is_new = TissueSample.objects.get_or_create(monkey=monkey, tissue_type=tt)
            if is_new:
                sample.tss_freezer = "<new record, no data>"
                sample.tss_location = "<new record, no data>"
                sample.save()
                # Can be incredibly spammy
                print "New tissue sample: " + sample.__unicode__()

@transaction.commit_on_success
# Creates ALL tissue samples in the database, for every monkey:tissuetype combination.
#m_tissue_type and m_cohort_id are integer ids
def create_TissueSamples_forCohort(m_tissue_type, m_cohort_id):
    units = Units[2][0]
    tt = TissueType.objects.get(tst_type_id = m_tissue_type)
    for monkey in Monkey.objects.all().filter(cohort_id = m_cohort_id):
        quantity = 0
        sample, is_new = TissueSample.objects.get_or_create(monkey=monkey, tissue_type=tt)
        if is_new:
            sample.tss_freezer = "<new record, no data>"
            sample.tss_location = "<new record, no data>"
            sample.save()
            # Can be incredibly spammy
            print "New tissue sample: " + sample.__unicode__()

@transaction.commit_on_success
def create_Assay_Development_tree():
    institution = Institution.objects.all()[0]
    cohort = Cohort.objects.get_or_create(coh_cohort_name="Assay Development", coh_upcoming=False,
                                          institution=institution)
    monkey = Monkey.objects.get_or_create(mky_real_id=0, mky_drinking=False, cohort=cohort[0])
    for tt in TissueType.objects.exclude(category__cat_name__icontains="Internal"):
        tissue_sample = TissueSample.objects.get_or_create(tissue_type=tt, monkey=monkey[0])
        tissue_sample[0].tss_sample_quantity = 999 # Force quantity
        tissue_sample[0].tss_freezer = "Assay Tissue"
        tissue_sample[0].tss_location = "Assay Tissue"
        tissue_sample[0].tss_details = "MATRR does not track assay inventory."

def create_7b_control_monkeys():
    import datetime

    cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')
    monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
                    mky_real_id=24818,
                    mky_birthdate=datetime.date(2005, 3, 13),
                    mky_necropsy_start_date=datetime.date(2012, 7, 23),
                    mky_age_at_necropsy='7 yrs 4 mos 10 days',
    )
    monkey.save()
    monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
                    mky_real_id=25207,
                    mky_birthdate=datetime.date(2005, 6, 1),
                    mky_necropsy_start_date=datetime.date(2012, 7, 27),
                    mky_age_at_necropsy='7 yrs 1 mos 26 days',
    )
    monkey.save()
    monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
                    mky_real_id=25407,
                    mky_birthdate=datetime.date(2005, 4, 1),
                    mky_necropsy_start_date=datetime.date(2012, 7, 26),
                    mky_age_at_necropsy='7 yrs 3 mos 25 days',
    )
    monkey.save()
    monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
                    mky_real_id=25526,
                    mky_birthdate=datetime.date(2005, 2, 1),
                    mky_necropsy_start_date=datetime.date(2012, 7, 24),
                    mky_age_at_necropsy='7 yrs 5 mos 23 days',
    )
    monkey.save()

def create_cohort_bouts(cohort, gap_seconds, overwrite=False):
    def _create_cohort_bouts(cohort, overwrite, gap_definition_seconds=0):
        if not isinstance(cohort, Cohort):
            try:
                cohort = Cohort.objects.get(pk=cohort)
            except Cohort.DoesNotExist:
                raise Exception("That's not a valid cohort")

        def _create_cbts(drinks, date, cohort, gap_definition_seconds=0, overwrite=False):
            """
            This recursive function will iterate thru the drinks' start and end times to create a CohortBout.
            When it finds a drink start time that is over gap_definition_seconds from this function's CohortBout it will call itself again to create a new CohortBout with the remaining drink times.
            """
            def _get_or_create_cbt(date, cohort, cbt_number, overwrite, gap_definition_seconds):
                cbt, is_new = CohortBout.objects.get_or_create(cohort=cohort, dex_date=date, cbt_number=cbt_number, cbt_gap_definition=gap_definition_seconds)
                needs_times = is_new or overwrite
                return cbt, needs_times

            cbt_index = 0
            if len(drinks):
                cbt, needs_times = _get_or_create_cbt(date, cohort, cbt_number=cbt_index, overwrite=overwrite, gap_definition_seconds=gap_definition_seconds)
                for index, drink in enumerate(drinks):
                    if needs_times:
                        cbt.cbt_start_time = drink['edr_start_time']
                        cbt.cbt_end_time = drink['edr_end_time']
                        needs_times = False
                    drink_gap = drink['edr_start_time'] - cbt.cbt_end_time
                    if drink_gap >= gap_definition_seconds:
                        cbt.save() # first, save this CBT
                        cbt_index += 1
                        cbt, needs_times = _get_or_create_cbt(date=date, cohort=cohort, cbt_number=cbt_index, overwrite=overwrite, gap_definition_seconds=gap_definition_seconds)
                        if needs_times:
                            cbt.cbt_start_time = drink['edr_start_time']
                            cbt.cbt_end_time = drink['edr_end_time']
                            cbt.save()
                            needs_times = False
                    else:
                        cbt.cbt_end_time = max(cbt.cbt_end_time, drink['edr_end_time'])

        all_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)
        # Get all the dates for this cohort
        all_dates = all_mtds.dates('drinking_experiment__dex_date', 'day', 'ASC').order_by('drinking_experiment__dex_date')
        for date in all_dates:
            # Get all the drink start times from each date
            drinks = ExperimentDrink.objects.filter(ebt__mtd__monkey__cohort=cohort, ebt__mtd__drinking_experiment__dex_date=date).order_by('edr_start_time')
            drink_values = drinks.values('edr_start_time', 'edr_end_time')

            # And send the times into a recursion loop
            _create_cbts(drink_values, date, cohort, overwrite=overwrite, gap_definition_seconds=gap_definition_seconds)
            # After we've created all the cohort bouts, we need to update the drinks' cbt foreign key association
            cbts = CohortBout.objects.filter(cohort=cohort, dex_date=date, cbt_gap_definition=gap_definition_seconds)
            for cbt in cbts:
                # I didn't assign the cbt fk in the recursion because this update should be faster
                cbt.populate_edr_set()

    for seconds in gap_seconds:
        _create_cohort_bouts(cohort, overwrite, seconds)

def create_data_tissue_tree():
    """
        This function will create (if needed) TissueCategory, TissueTypes, and TissueSamples for all data types available in MATRR
    """
    data_category, cat_is_new = TissueCategory.objects.get_or_create(cat_name='Data')
    data_names = ["Blood Ethanol Concentration", "Hormone", "Daily Ethanol Summary", "Ethanol Events", "Necropsy Summary", "Electrophysiology", "Metabolite", "Protein"]
    data_models = [MonkeyBEC, MonkeyHormone, MonkeyToDrinkingExperiment, ExperimentEvent, NecropsySummary, MonkeyEphys, MonkeyMetabolite, MonkeyProtein]
    for _name, _model in zip(data_names, data_models):
        _tst, tst_is_new = TissueType.objects.get_or_create(tst_tissue_name=_name, category=data_category)
        new_tss_count = 0
        for _mky in _model.objects.order_by().values_list('monkey', flat=True).distinct():
            _mky = Monkey.objects.get(pk=_mky)
            _tss, tss_is_new = TissueSample.objects.get_or_create(monkey=_mky, tissue_type=_tst, tss_sample_quantity=1, tss_units='whole')
            if tss_is_new:
                new_tss_count += 1
        print "%s Data Type %s:  %d new data samples created" % ("New" if tst_is_new else "Old", _name, new_tss_count)


    # "Ethanol Drinks",
    # ExperimentBout, ExperimentDrink,

    ### Experiment Bouts don't have an ebt.monkey field....
    _tst, tst_is_new = TissueType.objects.get_or_create(tst_tissue_name="Ethanol Bouts", category=data_category)
    new_tss_count = 0
    for _mky in ExperimentBout.objects.order_by().values_list('mtd__monkey', flat=True).distinct():
        _mky = Monkey.objects.get(pk=_mky)
        _tss, tss_is_new = TissueSample.objects.get_or_create(monkey=_mky, tissue_type=_tst, tss_sample_quantity=1, tss_units='whole')
        if tss_is_new:
            new_tss_count += 1
    print "%s Data Type %s:  %d new data samples created" % ("New" if tst_is_new else "Old", "Ethanol Bouts", new_tss_count)

    ### Experiment Drinks don't have an edr.monkey field....
    _tst, tst_is_new = TissueType.objects.get_or_create(tst_tissue_name="Ethanol Drinks", category=data_category)
    new_tss_count = 0
    for _mky in ExperimentDrink.objects.order_by().values_list('ebt__mtd__monkey', flat=True).distinct():
        _mky = Monkey.objects.get(pk=_mky)
        _tss, tss_is_new = TissueSample.objects.get_or_create(monkey=_mky, tissue_type=_tst, tss_sample_quantity=1, tss_units='whole')
        if tss_is_new:
            new_tss_count += 1
    print "%s Data Type %s:  %d new data samples created" % ("New" if tst_is_new else "Old", "Ethanol Drinks", new_tss_count)

    print "Success."


