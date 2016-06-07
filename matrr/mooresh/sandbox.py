import sys, os
sys.path.append('/home/ma/VE/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()

import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt

from matrr.models import *

r4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')
r5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')
r6a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6a')
r6b = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6b')
r10 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 10')
c2 = Cohort.objects.get(coh_cohort_name='INIA Cyno 2')
r7b = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')
r7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')
c13 = Cohort.objects.get(coh_cohort_name='INIA Cyno 13')
c9 = Cohort.objects.get(coh_cohort_name='INIA Cyno 9')
v1 = Cohort.objects.get(coh_cohort_id=14)
v2 = Cohort.objects.get(coh_cohort_id=15)

def populate_drinking_category_oaa(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        drinking_cat = None
    else:
        oa_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=self)
        oa_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=self)

        if oa_mtds.count() and oa_becs.count():
            drinking_cat= identify_drinking_category(oa_mtds, oa_becs)
        print "open access all data", self.mky_id, drinking_cat


def populate_drinking_category_f12(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        drinking_cat = None
    else:
         # oa_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=self)
         #    oa_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=self)
         #
         #    if oa_mtds.count() and oa_becs.count():
         #        self.mky_drinking_category = identify_drinking_category(oa_mtds, oa_becs)

#option 1: first 12 montrhs
        f12mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2013-09-04').\
            filter(drinking_experiment__dex_date__lte='2014-09-07')

        f12mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2013-09-04').\
            filter(bec_collect_date__lte='2014-09-07')
#
        if f12mo_mtds.count() and f12mo_becs.count():
             drinking_cat = identify_drinking_category(f12mo_mtds, f12mo_becs)

        print "first 12", self.mky_id, drinking_cat

def populate_drinking_category_l12(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        drinking_cat = None
    else:
         # oa_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=self)
         #    oa_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=self)
         #
         #    if oa_mtds.count() and oa_becs.count():
         #        self.mky_drinking_category = identify_drinking_category(oa_mtds, oa_becs)

#option 1: first 12 montrhs
        l12mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2014-08-16').\
            filter(drinking_experiment__dex_date__lte='2015-08-16')

        l12mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2014-08-16').\
            filter(bec_collect_date__lte='2015-08-16')
#
        if l12mo_mtds.count() and l12mo_becs.count():
             drinking_cat = identify_drinking_category(l12mo_mtds, l12mo_becs)

        print "last 12",self.mky_id, drinking_cat

def populate_drinking_category_oa2(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        drinking_cat = None
    else:
         # oa_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=self)
         #    oa_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=self)
         #
         #    if oa_mtds.count() and oa_becs.count():
         #        self.mky_drinking_category = identify_drinking_category(oa_mtds, oa_becs)

#option 1: first 12 montrhs
        f6mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2013-09-04').\
            filter(drinking_experiment__dex_date__lte='2014-03-09')
        l6mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2014-03-25').\
            filter(drinking_experiment__dex_date__lte='2014-09-07')
        l12mo_mtds=f6mo_mtds | l6mo_mtds

        f6mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2013-09-04').\
            filter(bec_collect_date__lte='2014-03-09')
        l6mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2014-03-25').\
            filter(bec_collect_date__lte='2014-09-07')
        l12mo_bec=f6mo_becs | l6mo_becs

        if l12mo_mtds.count() and l12mo_bec.count():
             drinking_cat = identify_drinking_category(l12mo_mtds, l12mo_bec)

        print "2 Open Access Periods ",self.mky_id, drinking_cat


#Populate Drinking Category
c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
monkeys = Monkey.objects.filter(cohort=c)
for m in monkeys:
   # populate_drinking_category_f12(m)
    populate_drinking_category_l12(m)
    #populate_drinking_category_oaa(m)
    #populate_drinking_category_oa2(m)
    print("***********************")
# m=Monkey.objects.get(mky_id=10208)
# from matrr.utils.gadgets import identify_drinking_category
# if not m.mky_drinking or not m.mky_study_complete:
#     m.mky_drinking_category = None
#else:
# f12mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).\
#     filter(drinking_experiment__dex_date__gte='2013-09-04').\
#     filter(drinking_experiment__dex_date__lte='2014-09-07')
#
# print f12mo_mtds.count()
#
# f12mo_becs = MonkeyBEC.objects.filter(monkey=m).\
#     filter(bec_collect_date__gte='2013-09-04').\
#     filter(bec_collect_date__lte='2014-09-07')
# print f12mo_becs.count()
#
# if f12mo_mtds.count() and f12mo_becs.count():
#      print identify_drinking_category(f12mo_mtds, f12mo_becs)
#********************************
     #     m.populate_age_at_intox()
     #populate_drinking_category_f12(m)
#     m.save()
     #print m.mky_id, m.mky_drinking_category

# for m in r10.monkey_set.all():
#     m.MonkeyBEC.objects.OA().exclude_exceptions().\
#             filter(drinking_experiment__dex_date__gte='2013-09-04').\
#             filter(drinking_experiment__dex_date__lte='2014-09-07').

# # option 1: first 12 montrhs
# l12mo_mtds = MonkeyToDrinkingExperiment.objects.\
#         filter(drinking_experiment__dex_date__gte='2013-09-04').\
#         filter(drinking_experiment__dex_date__lte='2014-09-07')
#
#
# # option 3: all data
# f12mo_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions()

# for m in r10.monkey_set.all():
#       print m;


#******************************
# m=Monkey.objects.get(mky_id=10208)
#
# print MonkeyToDrinkingExperiment.objects.filter(monkey=m).\
#         filter(drinking_experiment__dex_date__gte='2013-03-05').\
#         filter(drinking_experiment__dex_date__lte='2013-06-02').order_by('drinking_experiment__dex_date').values_list('drinking_experiment__dex_date', 'mex_excluded')



#***********************************
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mid).order_by('drinking_experiment__dex_date')
#     df_etoh = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', 'drinking_experiment__dex_date')),
#                       columns=['etoh', 'date'])
#     df_etoh.set_index('date', inplace=True)

#********************************
#MonkeyBEC.content_print(r6a)
# m = Monkey.objects.get(mky_id=10072)
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date')
# df = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', 'drinking_experiment__dex_date')),
#                   columns=['etoh', 'date'])
# plt.plot(df.date, df.etoh, 'ro')

# df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=r6b).filter(monkey__mky_drinking=True).values_list('monkey__mky_id', 'mtd_etoh_g_kg')),
#                   columns=['mky', 'etoh'])
# print df.groupby('mky').sum().sort('etoh')


#***************************
#m10072=Monkey.objects.get(mky_id=10072)
# bouts = ExperimentBout.objects.filter(mtd__monkey=m10072).order_by('mtd__drinking_experiment__dex_date')
# ml = ExperimentDrink.objects.filter(ebt__in=bouts).values_list('edr_volume', 'edr_volume')
# weight = MonkeyToDrinkingExperiment.objects.filter(monkey=m10072).order_by('drinking_experiment__dex_date').values_list('mtd_weight', flat=True)
# print sum([etoh*0.04/w for etoh,w in zip(ml, weight)])

# df= pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.OA().filter(monkey__cohort=r6b).filter(monkey__mky_drinking=True)
#                       .values_list('mtd_etoh_g_kg', flat=True)))
# print df.sum()
#print r6b.monkey_set.all().values_list('mky_real_id', 'mky_drinking')
#print pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.order_by('drinking_experiment__dex_date').values_list('mtd_weight', flat=True)))
#*******

#mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)\
#         .filter(mtd_weight__isnull=False).order_by('drinking_experiment__dex_date')
#     df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date', 'mtd_weight')),
#                       columns=['Date', 'weight'])

#***********************
#r10monkeys = Monkey.objects.filter(cohort=r10)
# print MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys).count()

#plt.show()
#Input specific Open Access Begin Date
def get_first_6mo_oa(cohort):
    dates = CohortEvent.objects.\
        filter(cohort=cohort).\
        filter(event__evt_name__iexact='First 6 Month Open Access Begin').\
        values_list('cev_date', flat=True)
    if len(dates) == 1:
        return dates[0]
    else:
        raise Exception('Ooops something wrong')

print get_first_6mo_oa(r10)
=======
