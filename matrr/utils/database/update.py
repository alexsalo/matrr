from datetime import datetime as dt
from datetime import time
from matrr import models

def convert_MonkeyProtein_dates_to_correct_datetimes():
    dates = (
    (2002, 4, 15),
    (2003, 3, 5),
    (2003, 4, 28),
    (2003, 4, 30),
    (2003, 12, 19),
    (2004, 8, 2),
    )
    times = (
    (12, 0),
    (17, 30),
    (12, 0),
    (17, 30),
    (7, 0),
    (12, 0),
    )
    for d, t in zip(dates, times):
        old_datetime = dt(*d)
        monkeys = models.MonkeyProtein.objects.filter(mpn_date=old_datetime)
        new_datetime = old_datetime.combine(old_datetime.date(), time(*t))
        monkeys.update(mpn_date=new_datetime)

def assign_cohort_institutions():
    wfu = models.Institution.objects.get(ins_institution_name='Wake Forest University')
    ohsu = models.Institution.objects.get(ins_institution_name='Oregon Health Sciences University, Technology Management')

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Cyno 1')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Cyno 2')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Cyno 3')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Cyno 8')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 1')
    cohort.institution = wfu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 2')
    cohort.institution = wfu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 6a')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 6b')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')
    cohort.institution = ohsu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Vervet 1')
    cohort.institution = wfu
    cohort.save()

    cohort = models.Cohort.objects.get(coh_cohort_name='INIA Vervet 2')
    cohort.institution = wfu
    cohort.save()

def populate_mky_species():
    for coh in models.Cohort.objects.exclude(coh_cohort_name__icontains='assay'):
        coh.monkey_set.all().update(mky_species=coh.coh_species)

def delete_wonky_monkeys():
    monkey_pks = [10043, 10050, 10053]
    models = [models.MonkeyToDrinkingExperiment, models.MonkeyBEC, models.ExperimentEvent, models.MonkeyImage]

    for model in models:
        for mky in monkey_pks:
            print "Deleting mky %d from table %s" % (mky, model.__name__)
            model.objects.filter(monkey=mky).delete()

def update_data_tissue_availability():
    data_category, cat_is_new = models.TissueCategory.objects.get_or_create(cat_name='Data')
    data_names = ["Blood Ethanol Concentration", "Hormone", "Daily Ethanol Summary", "Ethanol Events",
                  "Necropsy Summary", "Electrophysiology", "Metabolite", "Protein"]
    data_models = [models.MonkeyBEC, models.MonkeyHormone, models.MonkeyToDrinkingExperiment, models.ExperimentEvent,
                   models.NecropsySummary, models.MonkeyEphys, models.MonkeyMetabolite, models.MonkeyProtein]
    for _name, _model in zip(data_names, data_models):
        _tst, tst_is_new = models.TissueType.objects.get_or_create(tst_tissue_name=_name, category=data_category)
        mkys = _model.objects.order_by().values_list('monkey', flat=True).distinct()
        models.TissueSample.objects.filter(monkey__in=mkys, tissue_type=_tst).update(tss_sample_quantity=1, tss_units='whole')

    # "Ethanol Drinks",
    # ExperimentBout, ExperimentDrink,
    ### Experiment Bouts don't have an ebt.monkey field....
    _tst, tst_is_new = models.TissueType.objects.get_or_create(tst_tissue_name="Ethanol Bouts", category=data_category)
    for _mky in models.ExperimentBout.objects.order_by().values_list('mtd__monkey', flat=True).distinct():
        _mky = models.Monkey.objects.get(pk=_mky)
        models.TissueSample.objects.filter(monkey=_mky, tissue_type=_tst).update(tss_sample_quantity=1, tss_units='whole')

    ### Experiment Drinks don't have an edr.monkey field....
    _tst, tst_is_new = models.TissueType.objects.get_or_create(tst_tissue_name="Ethanol Drinks", category=data_category)
    for _mky in models.ExperimentDrink.objects.order_by().values_list('ebt__mtd__monkey', flat=True).distinct():
        _mky = models.Monkey.objects.get(pk=_mky)
        models.TissueSample.objects.filter(monkey=_mky, tissue_type=_tst).update(tss_sample_quantity=1, tss_units='whole')
    print "Success."
