__author__ = 'alex'
from matrr.models import *
from matrr.utils.database import load

# RUN ON GLEEK - this is just for reference!

r10monkeys = Cohort.objects.get(coh_cohort_name="INIA Rhesus 10").monkey_set.all()

# # 0. Load Cohort 13 Exception Days
# # 0.1 Delete existing
# MonkeyException.objects.filter(monkey__in=r10monkeys).delete()
#
# # 0.2 Load new
# load.load_monkey_exceptions('/home/alex/MATRR/coh10_full/Coh10_exception_days.txt',
#                             overwrite=True, header=True, delimiter="\t")
#
# # 0.3 Check how many totally excluded
# print MonkeyException.objects.filter(monkey__in=r10monkeys).count()
# print MonkeyException.objects.filter(monkey__in=r10monkeys).filter(mex_excluded=True).count()
#
# # 0.4 Purge exception dates for MEX if mex.mex_excluded==True
# for mex in MonkeyException.objects.filter(monkey__in=r10monkeys).filter(mex_excluded=True):
#     mex.flag_own_data(flag_mtd=True, flag_bec=True, flag_eev=True, flag_mhm=True, flag_mpn=True)
#
# # 1. Load BEC: cohort 10
# MonkeyBEC.objects.filter(monkey__in=r10monkeys).delete()
# load.load_bec_data('/home/alex/MATRR/coh10_full/update/coh10_BEC_Matrr_20151119.txt', overwrite=True, header=True)
# print MonkeyBEC.objects.filter(monkey__in=r10monkeys).count()
#
# # 2. Load necropsy summary Dataset
# # 2.1 Check what is in there
# ncm_colnames = NecropsySummary._meta.get_all_field_names()
# ncm_colnames.remove(u'monkey_id')
# print ncm_colnames
# print pd.DataFrame(list(NecropsySummary.objects.filter(monkey=r10monkeys[1]).values_list(*ncm_colnames)),
#                    columns=ncm_colnames)
#
# # 2.2
# NecropsySummary.objects.filter(monkey__in=r10monkeys).delete()
# load.load_necropsy_summary('/home/alex/MATRR/coh10_full/update/Coh10_std_Dataset_20151119.txt')
#
# # 3. Populate fields (example with cohort10):
# # 3.1 Bouts and MTDS
# for m in r10monkeys:
#     print m
#     mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m)
#     for mtd in mtds:
#         for bout in ExperimentBout.objects.filter(mtd=mtd):
#             bout.populate_fields()
#         mtd.populate_fields()
#
# # 3.2. Populate BEC
# for bec in MonkeyBEC.objects.filter(monkey__in=r10monkeys):
#     bec.populate_fields()
#
# # 3.3 Experiment Events
# for eev in ExperimentEvent.objects.filter(monkey__in=r10monkeys):
#     eev.populate_fields()
#
# # 3.4 Recalculate DC:
# for m in r10monkeys:
#     print m
#     m.mky_study_complete = True
#     m.populate_drinking_category()
#     m.populate_age_intox()
#     m.populate_weights_at_necropsy()
