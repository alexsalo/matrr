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

#****************************************************************************************************************
#Populate Drinking Category for Everything Marked Open Access
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

#Populate Drinking Category for the First 12 Months of Everything Marked as Open Access
def populate_drinking_category_f12(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        drinking_cat = None
    else:
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

#Populate Withdrawal Drinking Category for the last 3 months
def populate_drinking_category_l3(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        self.mky_withdrawal_drinking_category = None
    else:
        l12mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2015-03-30').\
            filter(drinking_experiment__dex_date__lte='2015-06-28')

        l12mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2015-03-30').\
            filter(bec_collect_date__lte='2015-06-28')
#
        if l12mo_mtds.count() and l12mo_becs.count():
             self.mky_withdrawal_drinking_category = identify_drinking_category(l12mo_mtds, l12mo_becs)
    print "last 3",self.mky_id, self.mky_withdrawal_drinking_category
    m.save()

#Populate Withdrawal Drinking Category for the last 6 months
def populate_drinking_category_l6(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        drinking_cat = None
    else:
        f6mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2014-12-08').\
            filter(drinking_experiment__dex_date__lte='2015-03-01')
        l6mo_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self).\
            filter(drinking_experiment__dex_date__gte='2015-03-30').\
            filter(drinking_experiment__dex_date__lte='2015-06-28')
        l12mo_mtds=f6mo_mtds | l6mo_mtds

        f6mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2014-12-08').\
            filter(bec_collect_date__lte='2015-03-01')
        l6mo_becs = MonkeyBEC.objects.filter(monkey=self).\
            filter(bec_collect_date__gte='2015-03-30').\
            filter(bec_collect_date__lte='2015-06-28')
        l12mo_bec=f6mo_becs | l6mo_becs

        if l12mo_mtds.count() and l12mo_bec.count():
             drinking_cat = identify_drinking_category(l12mo_mtds, l12mo_bec)

    print "last 6",self.mky_id, drinking_cat

#Populate Drinking Category for 2 Open Access Periods
def populate_drinking_category_oa2(self):
    #print self
    from matrr.utils.gadgets import identify_drinking_category
    if not self.mky_drinking or not self.mky_study_complete:
        self.mky_drinking_category = None
    else:
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
            self.mky_drinking_category = identify_drinking_category(l12mo_mtds, l12mo_bec)
    m.save()
    print "2 Open Access Periods ",self.mky_id, self.mky_drinking_category


#Populate Drinking Category
#c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
#monkeys = Monkey.objects.filter(cohort=c)
#for m in monkeys:
    #populate_drinking_category_f12(m)
 #   populate_drinking_category_l3(m)
    #populate_drinking_category_oaa(m)
   # populate_drinking_category_oa2(m)
  #  print("***********************")

#*************************************************************************
#Display Dex Type for Dates (check if dates are properly coded as Open Access)
# for m in r10.monkey_set.all():
#     m.MonkeyBEC.objects.OA().exclude_exceptions().\
#             filter(drinking_experiment__dex_date__gte='2013-09-04').\
#             filter(drinking_experiment__dex_date__lte='2014-09-07').

#*******************************************************
#Basic print and initialization commands
# for m in r10.monkey_set.all():
#       print m;

#m=Monkey.objects.get(mky_id=10208)

#r10monkeys = Monkey.objects.filter(cohort=r10)
# print MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys).count()

#plt.show() ***/here


#**********************************
# PD Example etoh and date
#m = Monkey.objects.get(mky_id=10072)
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date')
#     df_etoh = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', 'drinking_experiment__dex_date')),
#                       columns=['etoh', 'date'])
#     df_etoh.set_index('date', inplace=True)

# plt.plot(df.date, df.etoh, 'ro')

# df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=r6b).filter(monkey__mky_drinking=True).values_list('monkey__mky_id', 'mtd_etoh_g_kg')),
#                   columns=['mky', 'etoh'])
# print df.groupby('mky').sum().sort('etoh')
#***************************************************
#Input specific Open Access Begin Date
# def get_first_6mo_oa(cohort):
#     dates = CohortEvent.objects.\
#         filter(cohort=cohort).\
#         filter(event__evt_name__iexact='First 6 Month Open Access Begin').\
#         values_list('cev_date', flat=True)
#     if len(dates) == 1:
#         return dates[0]
#     else:
#         raise Exception('Ooops something wrong')
#
# #print get_first_6mo_oa(r10)
#
#***************************************************************************
#Change dex_type on Timiline on Matrr website
# for cev in CohortEvent.objects.filter(event__evt_name__iexact='Before With. 2 Start'):
#     cev.event.evt_dex_type = 'Open (Alcohol) Access'
#     cev.event.save()
#     cev.save()
#     print cev.event.evt_dex_type
# #
# for cev in CohortEvent.objects.filter(event__evt_name__iexact='Before With. 2 End'):
#     cev.event.evt_dex_type = 'Open (Alcohol) Access'
#     cev.event.save()
#     cev.save()
#     print cev.event.evt_dex_type
#
#
#
# for cev in CohortEvent.objects.filter(event__evt_name__iexact='Before With. 3 EP Start'):
#     cev.event.evt_dex_type = 'Open (Alcohol) Access'
#     cev.event.save()
#     cev.save()
#     print cev.event.evt_dex_type
#
# for cev in CohortEvent.objects.filter(event__evt_name__iexact='Before With. 3 EP End'):
#     cev.event.evt_dex_type = 'Open (Alcohol) Access'
#     cev.event.save()
#     cev.save()
#     print cev.event.evt_dex_type
# #
# for cev in CohortEvent.objects.filter(event__evt_name__iexact='Before With. 3 Open Access End'):
#     cev.event.evt_dex_type = None
#     cev.event.save()
#     cev.save()
#     print cev.event.evt_dex_type
# #
# for cev in CohortEvent.objects.filter(event__evt_name__iexact='Before With. 3 Open Access Start'):
#     cev.event.evt_dex_type = None
#     cev.event.save()
#     cev.save()
#     print cev.event.evt_dex_type
#**********************************************************

# print MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=r5).\
#
#         filter(drinking_experiment__dex_date__gte='2010-04-15').\
#         filter(drinking_experiment__dex_date__lte='2010-05-10').values_list('drinking_experiment__dex_type', flat=True)
#


#**************************************
#Check to see if there is any data stored on endocrine profiling days
# df= pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=r10).\
#         filter(drinking_experiment__dex_date__gte='2014-03-10').\
#         filter(drinking_experiment__dex_date__lte='2014-03-24').order_by('drinking_experiment__dex_date').\
#         values_list('drinking_experiment__dex_date', 'drinking_experiment__dex_type','mex_excluded', 'mtd_etoh_g_kg')))
# df.to_csv('/home/ma/etoh_excluded.csv')

#***************************************************
#Print correlation between cohort id and cohort name
# print pd.DataFrame(list(Cohort.objects.all().values_list('coh_cohort_id', 'coh_cohort_name')),
#                    columns=['id', 'name'])
#********************************************************
#Calculate change in variance in Etoh consmption between 1st 30 days and last 30 days of open access, separated by males and females

# def analyze_change_of_variance_mvf()
#
#     variance = analyze_cohort_change_of_variance(animal)
#
# def analyze_cohort_change_of_variance(cohort):
#     delta_days = 30
#
#     def get_date_of_coh_event(evt_name):
#         return CohortEvent.objects.filter(cohort=cohort).filter(event__evt_name__iexact=evt_name).\
#                                    values_list('cev_date', flat=True)[0]
#     f30d_start = get_date_of_coh_event('First 6 Month Open Access Begin')
#     f30d_end = f30d_start + timedelta(days=delta_days)
#
#     l30d_end = get_date_of_coh_event('Second 6 Month Open Access End')
#     l30d_start = l30d_end - timedelta(days=delta_days)
#
#     print 'First 30 days of the first OA for cohort %s: %s - %s' % (cohort.coh_cohort_name, f30d_start, f30d_end)
#     print 'Last 30 days of the second OA for cohort %s: %s - %s' % (cohort.coh_cohort_name, l30d_start, l30d_end)
#
#     animals = cohort.monkey_set.filter(mky_drinking_category__isnull=False)
#
#     def get_etohs_for_period(start, end):
#         mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=animals).\
#             filter(drinking_experiment__dex_date__gte=start).\
#             filter(drinking_experiment__dex_date__lte=end)
#         return mtds.values_list('mtd_etoh_g_kg', flat=True)
#
#     f30d_etohs = get_etohs_for_period(f30d_start, f30d_end)
#     l30d_etohs = get_etohs_for_period(l30d_start, l30d_end)
#
#     # P-value testing for means
#     from scipy.stats import ttest_rel, ttest_ind
#     print len(f30d_etohs), len(l30d_etohs)
#
#     #t-test
#     t, pval = ttest_ind(f30d_etohs, l30d_etohs, equal_var=False)
#     print t, pval

# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c)
#c= Cohort.objects.all()
#for coh in c:


#first 30 is [:30]
def get_date_of_coh_event(evt_name,coh):
        return CohortEvent.objects.filter(cohort=coh).filter(event__evt_name__iexact=evt_name).\
                                    values_list('cev_date', flat=True)[0]
c = r6a
#female_cohorts = [r6a,r6b]
#for c in female_cohorts
female_mky_id = []
threshold = 0.001
monkeys = Monkey.objects.filter(cohort=c)
#fix
f30date=get_date_of_coh_event('First 6 Month Open Access Begin',c)
##print f30date
l30date=get_date_of_coh_event('Second 6 Month Open Access End',c)
##print l30date
for m in monkeys:
     #cohort.monkey_set.filter(mky_drinking_category__isnull=False)
    if m.mky_drinking==True:
        female_mky_id.append(m.mky_id)
print female_mky_id

variance_fem_first = []
variance_fem_last = []
for f in female_mky_id:
    f30mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().\
              filter(monkey=Monkey.objects.get(mky_id=f)).\
              filter(mtd_etoh_g_kg__gte=threshold).\
              filter(drinking_experiment__dex_date__gte=f30date).order_by('drinking_experiment__dex_date')[:30]
    f30mtds_etoh= pd.DataFrame(list(f30mtds.values_list('mtd_etoh_g_kg')))
    var_temp = np.var(f30mtds_etoh)
    variance_fem_first.append(var_temp)
    #print pd.DataFrame(list(variance_fem_first))
    #print pd.DataFrame(list(f30mtds.values_list('mtd_etoh_g_kg')))
    l30mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().\
              filter(monkey=Monkey.objects.get(mky_id=f)).\
              filter(mtd_etoh_g_kg__gte=threshold).\
              filter(drinking_experiment__dex_date__lte=l30date).order_by('drinking_experiment__dex_date')
    l30mtds_etoh= pd.DataFrame(list(l30mtds.values_list('mtd_etoh_g_kg')), columns=['etoh_g_kg'])[-30:]
    #print l30mtds_etoh
    var_temp = np.var(l30mtds_etoh)
    variance_fem_last.append(var_temp)
    print pd.DataFrame(variance_fem_last)
    #print pd.DataFrame(list(l30mtds.values_list('mtd_etoh_g_kg'))[-30:])
from scipy.stats import ttest_rel, ttest_ind
t, pval = ttest_ind(variance_fem_first, variance_fem_last, equal_var=False)
print t, pval
plt.plot(variance_fem_first)
plt.show()


"""
Profiling
"""
# # Filter by required date
# mtds_to_be_changed = MonkeyToDrinkingExperiment.objects.filter(monkey__mky_id=10208).order_by('drinking_experiment__dex_date')
# for mtd in mtds_to_be_changed:
#     print mtds_to_be_changed[0].drinking_experiment.dex_type
#     mtd = mtds_to_be_changed[0]
#     mtd.drinking_experiment.dex_type = 'Profiling'
#     mtd.drinking_experiment.save()
#     mtd.save()
#     print mtd.drinking_experiment.dex_type