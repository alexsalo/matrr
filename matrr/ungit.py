import sys, os
sys.path.append('~/pycharm/ve1/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.models import Monkey
from matrr.plotting import monkey_plots as mkplot
import matplotlib
matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/Matrr'
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pylab
from datetime import datetime as dt
import string
import csv
import re
from django.db.transaction import commit_on_success
from django.db import transaction
from matrr.utils.database import dingus, create
dc_colors = {
    'LD' : 'g',
    'BD' : 'b',
    'HD' : 'y',
    'VHD' : 'r'
}

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

#m = Monkey.objects.get(mky_id = 10022)
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
# from matrr.utils.database import dump
# dump.dump_standard_cohort_data(m.cohort.coh_cohort_id)

# filename = '/home/alex/Dropbox/Baylor/Matrr/9/34.bec_data_explanation_20150227.csv'
# from matrr.utils.database import load
# load.load_bec_data(filename, True, True)

###2-28-15
# def load_mense_data(file_name):
#     with open(file_name, 'rU') as f:
#         #1. Parse header to get monkeys
#         monkeys = []
#         header = f.readline()
#         for s in header.split(',')[2:]: #get mky_ids
#             m = Monkey.objects.get(mky_id = s)
#             monkeys.append(m)
#         #print monkeys
#
#         read_data = f.readlines()
#         for line_number, line in enumerate(read_data):
#             line_split = line.split(',')
#             dex_date = dingus.get_datetime_from_steve(line_split[0])
#             data = line_split[2:]
#             for i, value in enumerate(data):
#                 if value == 'TRUE' or value == 'TRUE\n':
#                     mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkeys[i]).filter(drinking_experiment__dex_date=dex_date)
#                     if mtds.count() > 0:
#                         mtd = mtds[0]
#                         mtd.mtd_mense_started = True
#                         mtd.save()

# mense_data_file_6a6b = '/home/alex/Dropbox/Baylor/Matrr/mense_data/33.coh6a6bmensestartdata20150226.csv'
# load_mense_data(mense_data_file_6a6b)

###3-1-15
# def load_progesterone_data(file_name):
#     with open(file_name, 'rU') as f:
#         #1. Parse header to get monkeys
#         monkeys = []
#         header = f.readline()
#         for s in header.split(',')[2:]: #get mky_ids
#             m = Monkey.objects.get(mky_id = s)
#             monkeys.append(m)
#         #print monkeys
#
#         read_data = f.readlines()
#         for line_number, line in enumerate(read_data):
#             line_split = line.split(',')
#             dex_date = dingus.get_datetime_from_steve(line_split[0])
#             data = line_split[2:]
#             for i, value in enumerate(data):
#                 try:
#                     float_value = float(value)
#                     mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkeys[i]).filter(drinking_experiment__dex_date=dex_date)
#                     if mtds.count() > 0:
#                         mtd = mtds[0]
#                         mtd.mtd_progesterone = float_value
#                         mtd.save()
#                 except ValueError:
#                     pass
#
# progesterone_data_file_6a6b = '/home/alex/Dropbox/Baylor/Matrr/progesterone/32.coh6a6bprogesteronedata20150226.csv'
# load_progesterone_data(progesterone_data_file_6a6b)

# df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.filter(monkey=Monkey.objects.get(mky_id=10077)).order_by('drinking_experiment__dex_date').values_list('mtd_mense_started', 'mtd_progesterone', 'drinking_experiment__dex_date')), columns=['mense', 'progesterone', 'date'])
# df_prog = df[np.isfinite(df['progesterone'])] #to remove nans
# print df_prog
# plt.plot(df_prog.date, df_prog.progesterone, 'go-')
# [plt.axvline(date, linewidth=1, color='r', linestyle='solid') for date in list(df.date[df.mense])]

###3-2-15
# from django.contrib.auth.models import User, Permission, Group
# g = Group.objects.get(name='Committee')
# user = User.objects.get(username='alex')
# print user, g
# #g.user_set.remove(user)
# user.groups.clear()
# user.save()

# c = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6b")
# print CohortEvent.objects.filter(cohort=c)
# df = pd.DataFrame(list(CohortEvent.objects.filter(cohort=c).values_list('cev_date', 'event')), columns = ['cev_date', 'event'])
# print df
# print CohortEvent.objects.filter(cohort=c).filter(event=37)[0].cev_date

# m = Monkey.objects.get(mky_id = 10005)
# print m.avg_BEC_pct_by_period()

###3-4-15
# from django.contrib.contenttypes.models import ContentType
#
# for ct in ContentType.objects.all():
#     m = ct.model_class()
#     print "%s.%s\t%d" % (m.__module__, m.__name__, m._default_manager.count())
#

###3-5-15
# m = Monkey.objects.get(mky_id = 10074)
# duration = 10 * 60 #15 mins
#
# mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m).exclude_exceptions().order_by('drinking_experiment__dex_date')
# volumes = []
# for mtd in mtds:
#     bouts = mtd.bouts_set.filter(ebt_start_time__lt=duration)
#     drinks_in_bout = ExperimentDrink.objects.Ind().filter(ebt__in=bouts).filter(edr_start_time__lt=duration)
#     volumes.append(drinks_in_bout.aggregate(Sum('edr_volume')))
# vols_df = pd.DataFrame(list(volumes))
# print vols_df
# plt.plot(vols_df)

# volumes = bouts_in_fraction.order_by('ebt_start_time').values_list('ebt_volume', flat=True)
# print volumes



# df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date', 'mtd_pct_max_bout_vol_total_etoh_hour_0', 'mtd_pct_max_bout_vol_total_etoh_hour_1')), columns=['date', 'hr1', 'hr2'])
# plt.plot(df.date, df.hr1, 'b-o', df.date, df.hr2, 'r-o')


###3-16-15
# m = Monkey.objects.get(mky_id = 10074)
# print m.etoh_during_ind(5)

# from matrr.utils.database import load
# coh13 = '/home/alex/Dropbox/Baylor/Matrr/coh13/coh13.csv'
# load.load_cyno_13_monkeys(coh13)

#delete
# mids = [32325,32326,32327,32328,32329,32330,32331,32332,32333,32334,32335,32336]
# mm = Monkey.objects.filter(mky_real_id__in=mids)
# for m in mm:
#     print m
#    m.delete()


###3-17-2015
# m = Monkey.objects.get(mky_id = 10072)
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date').order_by('drinking_experiment__dex_date')
# df = pd.DataFrame(list(mtds.values_list('mtd_mense_started', 'drinking_experiment__dex_date', 'mtd_etoh_g_kg', 'mtd_progesterone')), columns=['mense','date', 'etoh', 'progesterone'])
# df = df.set_index('date')
# print df.head()
#
# dates = list(df.index[df.mense].values)
# print len(dates)
# peaks_progesterone = []
# for i in range(1,len(dates),1):
#     df_period = df[dates[i-1]:dates[i]]
#     peak_pos = df_period.progesterone.argmax()
#     if not pd.isnull(peak_pos):
#         peaks_progesterone.append(peak_pos)
#
# periods_for_avg = sorted(dates + peaks_progesterone)
# print periods_for_avg
#
# etohs = [df[periods_for_avg[i-1]:periods_for_avg[i]].etoh.mean() for i, date in enumerate(periods_for_avg)][1:]
# print etohs
# print len(periods_for_avg)
# print len(etohs)
#
# #plot afv etohs
#
# pre_post_luni_phase = {
#     0 : 'c',
#     1 : 'm'
# }
# plt.plot(df.index, df.etoh, label = 'EtOH intake')
# [plt.plot((periods_for_avg[i], periods_for_avg[i+1]), (etoh, etoh), color=pre_post_luni_phase[i%2],marker = '|', alpha=0.9, linewidth=2,) for i, etoh in enumerate(etohs)]


###3-18-2015
# m = Monkey.objects.get(mky_id = 10089)
# df = m.etoh_during_ind(5)
# print df
# med_start = df[:14].median().values[0]
# med_end = df[-14:].median().values[0]
# print med_start, med_end
# delta_etoh_nmin = med_end - med_start
# print delta_etoh_nmin

# print m.cohort
# mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m).exclude_exceptions()
# df = pd.DataFrame(list(mtds.values('drinking_experiment__dex_date', 'mtd_etoh_intake')))
# print df
# plt.plot(df.drinking_experiment__dex_date, df.mtd_etoh_intake, 'bo')



###3-19-2015
# req = Request.objects.get(req_request_id=342)
# print req
# u_jones = User.objects.get(username='srjones')
# print u_jones
# u_ann = User.objects.get(username='jkonstan')
# print u_ann
# req.user = u_jones
# req.save()
# print req

###3-20-2015
# def plot_min_etoh_showcases():
#     def plot_min_etoh_pct_for_monkey(mid, ax):
#         #get monkey
#         m = Monkey.objects.get(mky_id=mid)
#
#         #get the data
#         df = m.etoh_during_ind(10)
#         df.columns=['vol']
#
#         #fit the trend line
#         z = numpy.polyfit(df.index, df.vol, 2)
#         p = numpy.poly1d(z)
#
#         #plot data and trend
#         ax.plot(df.index, df.vol, 'bo', df.index, p(df.index),'r-')
#         ax.set_ylim(-0.05,1.05)
#         ax.set_xlim(0,100)
#         ax.patch.set_facecolor(dc_colors[m.mky_drinking_category])
#         ax.patch.set_alpha(0.1)
#
#         #title and save
#         #ax.set_title(str(10)+'min etoh pct for: ' + m.__unicode__(), loc='left')
#         ax.text(0.97, 0.95, str(m.mky_drinking_category) + ' ' +str(m.mky_id),
#             horizontalalignment='right',
#             verticalalignment='top',
#             transform=ax.transAxes, fontsize=12)
#
#         return ax
#
#     fig, axs = plt.subplots(4, 3, figsize=(30, 20), facecolor='w', edgecolor='k')
#     axs = axs.ravel()
#
#     #coh5
#     plot_min_etoh_pct_for_monkey(10061, axs[0])
#     plot_min_etoh_pct_for_monkey(10064, axs[3])
#     plot_min_etoh_pct_for_monkey(10060, axs[6])
#     axs[9].set_ylim(-0.05,1.05)
#     axs[0].set_title('Cohort 5')
#
#     #coh7b
#     axs[1].set_ylim(-0.05,1.05)
#     plot_min_etoh_pct_for_monkey(10082, axs[4])
#     plot_min_etoh_pct_for_monkey(10086, axs[7])
#     plot_min_etoh_pct_for_monkey(10085, axs[10])
#     axs[1].set_title('Cohort 7b')
#
#     #coh6b
#     plot_min_etoh_pct_for_monkey(10073, axs[2])
#     plot_min_etoh_pct_for_monkey(10075, axs[5])
#     plot_min_etoh_pct_for_monkey(10072, axs[11])
#     axs[8].set_ylim(-0.05,1.05)
#     axs[9].set_xlim(0,100)
#     axs[2].set_title('Cohort 6b')
#
#     # Fine-tune figure; make subplots close to each other and hide x ticks for all but bottom plot.
#     fig.subplots_adjust(hspace=0)
#     fig.subplots_adjust(wspace=0)
#     plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
#     plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)
#
#     plt.setp(axs[9].get_xticklabels(), visible = True)
#     plt.setp([axs[i].get_yticklabels() for i in [0,3,6,9]], visible = True)
#
#     axs[0].set_ylabel('VHD', size=14)
#     axs[3].set_ylabel('HD', size=14)
#     axs[6].set_ylabel('BD', size=14)
#     axs[9].set_ylabel('LD', size=14)
#
#     fig.suptitle('EtOH consumption during first 10 minutes as percent (%) of daily allotment', fontsize=14)
#     fig.subplots_adjust(top=0.93)
#
# plot_min_etoh_showcases()


###3-23-2015
# def pct_days_over(mtds, gkg_treshold = 3):
#     over_days = len([mtd.mtd_etoh_g_kg for mtd in mtds if mtd.mtd_etoh_g_kg > gkg_treshold])
#     total_days = mtds.count()
#     return 1.0 * over_days / total_days
#
# MIDS = [10083, 10084, 10090, 10089, 10085, 10087, 10086, 10060, 10082, 10064, 10065, 10088, 10097,
#         10067, 10091, 10098, 10066, 10063, 10061, 10062, 10208, 10209, 10210, 10211, 10212, 10213, 10214, 10215]
# LMD = [10083, 10084, 10090, 10089, 10085, 10087, 10086, 10060, 10208, 10209, 10210, 10211, 10212, 10213]
# HD = [10082, 10064, 10065, 10088, 10097, 10067, 10091, 10215, 10098, 10066, 10063, 10061, 10214, 10062]
#
# monkeys = Monkey.objects.filter(mky_id__in=MIDS)
# mtds_all = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkeys)
#
# df = pd.DataFrame(index=MIDS, columns=['pct_days_over'])
# for m in monkeys:
#     mtds = mtds_all.filter(monkey=m)
#     if mtds.count() == 0:
#         print m
#     else:
#         df.pct_days_over[m.mky_id] = pct_days_over(mtds)
#
# print df
# df = df.sort('pct_days_over')
# print df
# colors = ['red' if HD.__contains__(x) else 'blue' for x in df.index]
# df.plot(kind='bar', colors = colors)
# plt.xticks(rotation=70)
#
# # mtds = MonkeyToDrinkingExperiment.objects.filter(monkey = Monkey.objects.filter(mky_id=10083))
# # print [mtd.mtd_etoh_g_kg for mtd in mtds if mtd.mtd_etoh_g_kg > 3]

###3-24-2015
# dc_colors_ol = {
#     'LD' : 'g-o',
#     'BD' : 'b-o',
#     'HD' : 'y-o',
#     'VHD' : 'r-o',
#     None : 'k-o'
# }
# mm = Monkey.objects.filter(mky_id__in=[10088, 10032, 10064])
# # print mm
# # fig, axs = plt.subplots(3, 1, figsize=(10,10))
# # for index, m in enumerate(mm):
# #     mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date')
# #     axs[index].plot(mtds.values_list('drinking_experiment__dex_date'), mtds.values_list('mtd_etoh_g_kg'), dc_colors_ol[m.mky_drinking_category])
# # plt.tight_layout()
#
# mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=mm[1]).order_by('drinking_experiment__dex_date')
# df = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', 'mtd_veh_intake')), columns=['etoh', 'veh'])
# df.plot(kind='hist', stacked=True)

###3-25-2015
# import wikipedia as wk
# page = wk.page('cv joint')
# print page.title
# wk.set_lang('ru')
# page = wk.page('Constant-velocity_joint').url
# print page

##upload coh10
# m = Monkey.objects.filter(mky_id=10208)
# mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date')
# print mtds.values_list('drinking_experiment__dex_type')
# print Cohort.objects.get(coh_cohort_name='INIA Rhesus 10')
coh10_file = '/home/alex/Dropbox/Baylor/Matrr/coh10/38.coh10_22hr_tentative_to_20140925_matrr.csv'
from matrr.utils.database import load
load.load_mtd(coh10_file, 'Open Access', 'INIA Rhesus 10')

# cohorts = Cohort.objects.all()
# for c in cohorts:
#     if c.coh_cohort_name == 'Assay Development':
#             print 'Assay Dev'
#     else:
#         print c.coh_cohort_name[5:]
# print cohorts[1].coh_cohort_name[5:]

pylab.show()
