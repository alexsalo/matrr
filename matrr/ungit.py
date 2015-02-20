import sys, os
sys.path.append('~/pycharm/ve1/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.models import Monkey
from matrr.plotting import monkey_plots as mkplot
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import pylab
from datetime import datetime as dt
import string
import csv
import re
from django.db.transaction import commit_on_success
from django.db import transaction
from matrr.utils.database import dingus, create

import django
django.setup()

#print Monkey.objects.all().count()
#print Monkey.objects.filter(mky_study_complete = True).count()
#print Monkey.objects.all().filter(mky_drinking_category = "HD").count()
#m = Monkey.objects.get(mky_id=10006)
# m = Monkey.objects.get(mky_real_id=1059)
# from matrr.utils.plotting_beta import monkey_plots as mkplt
# mkplt.monkey_etoh_bouts_vol(m)
# pylab.show()
# print m.mky_id
# import mlma
# print mlma.oa_drinking_lwr(m)
#ms = Monkey.objects.all()[3:6]
#print ms



#mkplot.monkey_necropsy_avg_22hr_g_per_kg(m)
#necropsy image do force render
#mkplot.monkey_necropsy_etoh_4pct(m)
#mkplot.monkey_necropsy_sum_g_per_kg(m)
#pylab.show()
#from matrr.utils.database import dump
#dump.dump_data_req_request_425_thru_431()

#CohortProteinImage.objects.all().delete()
#CohortHormoneImage.objects.all().delete()
#CohortImage.objects.all().get(pk=2699).save(force_render = True)
#http://127.0.0.1:8080/media/matrr_images/INIA_Cyno_1.Total_Ethanol_Intake_ml.2699-thumb_fd1XXi2.jpg

#print MonkeyImage.objects.filter(method__contains = "necropsy").count()
# print MonkeyImage.objects.count()
# cnt = 0
# for image in MonkeyImage.objects.all():#.filter(method__contains = "necropsy"):
#     cnt += 1
#     print image, cnt
#     image.save(force_render = True)

#from matrr.utils.parallel_plot import *
#hdmonekeys = Monkey.objects.all().filter(mky_drinking_category = "HD")
#print hdmonekeys.count()
#print hdmonekeys[1]
#mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=hdmonekeys[1].)
#print percentage_of_days_over_2_gkg(m[1])


###Drinking Days Total
#print m.DrinkingDaysTotal()


###LOAD daily_22h_etoh###
# from matrr.utils.database import dingus
#
# def read_daily_22hr_etoh(file, cohort, parsenames=False):
#     with open(file, 'r') as f:
#         #1. Parse header to get monkeys
#         monkeys = []
#         names = []
#         header = f.readline()
#         header_split = header.split(',')
#         for s in header_split:
#             s_split = s.split(' ')
#             for s2 in s_split:
#                 if s2.isdigit():
#                     m = Monkey.objects.get(mky_real_id = s2)
#                     monkeys.append(m)
#                 else:
#                     names.append(s2)
#         if parsenames:
#             for i in xrange(len(monkeys)):
#                 m = monkeys[i]
#                 m.mky_name = names[i+2]
#                 m.save()
#         #2. Parse Data
#         read_data = f.readlines()
#         cnt = 0
#         for line_number, line in enumerate(read_data):
#             #print line_number
#             #print line
#             cnt += 1
#             print cnt
#             # if cnt > 2:
#             #        break
#             data = line.split(',')
#
#             #2.1 Create Drinking Experiments
#             dex_date = dingus.get_datetime_from_steve(data[1])
#             des = DrinkingExperiment.objects.filter(dex_type="Open Access", dex_date = dex_date,
#                                                     cohort = cohort)
#             if des.count() == 0:
#                 de = DrinkingExperiment(dex_type="Open Access", dex_date = dex_date,
#                                                     cohort = cohort)
#             elif des.count() == 1:
#                 de = des[0]
#             elif des.count() > 1:
#                 print "too many drinking experiments!"
#             #save notes if any
#             notepos = len(monkeys)+2
#             if len(data[notepos]) > 2:
#                 de.dex_notes = data[notepos]
#             de.save()
#
#             #2.2 Create MonkeyToDrinkingExperiment
#             pos = 2
#             for monkey in monkeys:
#                 mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment = de, monkey = monkey)
#                 if mtds.count() != 0:
#                     mtd = mtds[0]
#                 else:
#                     mtd = MonkeyToDrinkingExperiment()
#                     mtd.monkey = monkey
#                     mtd.drinking_experiment = de
#                     mtd.mtd_total_pellets = 0
#
#                 #print mtd
#                 if data[pos]:
#                     mtd.mtd_etoh_g_kg = data[pos]
#                 else:
#                     mtd.mtd_etoh_g_kg = None
#                     mtd.mtd_total_pellets = 0
#                 #print mtd
#
#                 mtd.save()
#                 pos +=1
#
# #file_name = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet1_daily_22h_etoh.csv'
# file_name = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet2_daily_22h_etoh.csv'
# #cohort_vervet_1 = Cohort.objects.get(coh_cohort_name="INIA Vervet 1")
# cohort_vervet_2 = Cohort.objects.get(coh_cohort_name="INIA Vervet 2")
#
# read_daily_22hr_etoh(file_name, cohort_vervet_2, True)

###LOAD BEC###
# m = Monkey.objects.get(mky_real_id = 1190)
# # print m
# bec = MonkeyBEC.objects.filter(monkey=m)
# print bec.count()
#
# from matrr.utils.database import load_unusual_formats
# # #bec_vervet1_file = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet1_BEC.csv'
# # bec_vervet2_file = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet2_BEC.csv'
# bec_vervet2_induction_file = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet1_BEC_induction.csv'
# load_unusual_formats.load_bec_data_vervet(bec_vervet2_induction_file, True, True)

from django.db.models import Sum, Avg
from dateutil.relativedelta import relativedelta

m = Monkey.objects.get(mky_id = 10022)
# mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey = m).order_by('drinking_experiment__dex_date')
# start_date = mtds[1].drinking_experiment.dex_date # + relativedelta( months = +6 )
# end_date = start_date + relativedelta( months = +6 )
# mtds = mtds.filter(drinking_experiment__dex_date__gte=start_date).filter(drinking_experiment__dex_date__lte=end_date)
# print mtds.values('drinking_experiment__dex_date').distinct().count()
# print mtds.aggregate(Sum('mtd_etoh_intake')).values()[0]
# print m.Total_etoh_during_first_6mo()
# print m.Total_etoh_during_second_6mo()
# print m.Total_etoh()
# print m.Total_veh_during_first_6mo()
# print m.Total_veh_during_second_6mo()
# print m.Total_veh()

# mbecs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey = m).order_by('bec_collect_date')
# start_date = mbecs[1].bec_collect_date
# end_date = start_date + relativedelta( months = +6 )
# mbecs = mbecs.filter(bec_collect_date__gte=start_date).filter(bec_collect_date__lte=end_date)
# #days = (mbecs.reverse()[1] - mbecs[1].bec_collect_date)
# print mbecs.values('bec_collect_date').distinct().count()
# print mbecs.aggregate(Avg('bec_vol_etoh')).values()[0]

#mbecs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey = m)
#print round(mbecs.aggregate(Avg('bec_vol_etoh')).values()[0], 2)
# print m.cohort.coh_cohort_id
# cohort = Cohort.objects.get(coh_cohort_id = m.cohort.coh_cohort_id)
# print cohort.monkey_set.all().count()
# m
# print [m.avg_BEC_1st_6mo(), m.avg_BEC_all()]

# from matrr.utils.database import load
# filename = '/home/alex/Dropbox/Baylor/Matrr/6a/31.6a_bec_20150218_re_check.csv'
# load.load_bec_data(filename, True, True)

# a, b = m.sum_etoh_1st_6mo_gkg()
# print a
# print b
from matrr.utils.database import dump
dump.dump_standard_cohort_data(m.cohort.coh_cohort_id)