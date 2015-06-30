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
    'VHD' : 'r',
    'None' : 'k',
    None : 'k'
}
dc_colors_o = {
    'LD' : 'go',
    'BD' : 'bo',
    'HD' : 'yo',
    'VHD' : 'ro',
    None : 'ko'
}

coh_colors = {
    5 : 'g',
    6 : 'b',
    7 : 'r',
    8 : 'k',
    9 : 'y',
    10 : 'm',
    19 : 'c'
}

from matrr.plotting import plot_tools
from matplotlib import pyplot, cm, gridspec, colors
from numpy import polyfit, polyval
from matplotlib.ticker import NullLocator, MaxNLocator
DEFAULT_CIRCLE_MAX = 200
DEFAULT_CIRCLE_MIN = 60
DEFAULT_FIG_SIZE = (10,10)
HISTOGRAM_FIG_SIZE = (15,10)
THIRDS_FIG_SIZE = (20,8)
DEFAULT_DPI = 80

import django
django.setup()

def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

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
# print Monkey.objects.get(mky_id=10092)
# print Monkey.objects.get(mky_id=10054)
# def pct_days_over(mtds, gkg_treshold = 3):
#     over_days = len([mtd.mtd_etoh_g_kg for mtd in mtds if mtd.mtd_etoh_g_kg > gkg_treshold])
#     total_days = mtds.count()
#     return 1.0 * over_days / total_days
#
# MIDS = [10083, 10084, 10090, 10089, 10085, 10087, 10086, 10060, 10082, 10064, 10065, 10088, 10097,
#         10067, 10091, 10098, 10066, 10063, 10061, 10062, 10208, 10209, 10210, 10211, 10212, 10213, 10214, 10215,
#         10092, 10054]
# LMD = [10083, 10084, 10090, 10089, 10085, 10087, 10086, 10060, 10208, 10209, 10210, 10211, 10212, 10213,
#        10092, 10054]
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

# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey = Monkey.objects.filter(mky_id=10083))
# print [mtd.mtd_etoh_g_kg for mtd in mtds if mtd.mtd_etoh_g_kg > 3]

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
# # m = Monkey.objects.filter(mky_id=10208)
# # mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date')
# # print mtds.values_list('drinking_experiment__dex_type')
# # print Cohort.objects.get(coh_cohort_name='INIA Rhesus 10')
# coh10_file = '/home/alex/Dropbox/Baylor/Matrr/coh10/38.coh10_22hr_tentative_to_20140925_matrr.csv'
# from matrr.utils.database import load
# load.load_mtd(coh10_file, 'Open Access', 'INIA Rhesus 10')

# cohorts = Cohort.objects.all()
# for c in cohorts:
#     if c.coh_cohort_name == 'Assay Development':
#             print 'Assay Dev'
#     else:
#         print c.coh_cohort_name[5:]
# print cohorts[1].coh_cohort_name[5:]

###3-26-2015
# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# m = Monkey.objects.filter(cohort=c)[1]
# # print m
# #
# # df = pd.DataFrame(list(CohortEvent.objects.filter(cohort=c).values_list('event__evt_id', 'event__evt_name', 'cev_date')))
# # print df
#
# # print MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date').filter(drinking_experiment__dex_date__lte=dingus.get_datetime_from_steve('08/05/2013')).\
# # filter(drinking_experiment__dex_date__gte=dingus.get_datetime_from_steve('08/04/2013'))
#
# # print CohortEvent.objects.filter(cohort=c)
# # for eve in CohortEvent.objects.filter(cohort=c):
# #     eve.delete()
# # EventType.objects.filter(evt_id=79).delete()
# # print pd.DataFrame(list(EventType.objects.all().values_list('evt_id', 'evt_name')), columns=['id','name']).sort('id')
#
# # cohort_name_ish = "inia %s %s" % ('rhesus', '10')
# # print cohort_name_ish
# # cohort = Cohort.objects.filter(coh_cohort_name__iexact=cohort_name_ish)
# # print cohort
#
# #print EventType.objects.get(evt_name='Individual Housing End')
#
# # timelines_all = '/home/alex/Dropbox/Baylor/Matrr/coh10/timelines_all.csv'
# # from matrr.utils.database import load
# # load.load_cohort_timelines(timelines_all, True)
#
# # print CohortEvent.objects.filter(cohort=c)
# # badev = EventType.objects.filter(evt_name__contains='201')
# # print badev
# # for ev in badev:
# #     ev.delete()
# # badev = EventType.objects.filter(evt_name__contains='201')
# # print badev
# # print EventType.objects.all()
#
# print CohortEvent.objects.filter(cohort=c)

###3-27-2015
# m = Monkey.objects.get(mky_id=10187)
# df_m_weight = pd.DataFrame(list(Monkey.objects.all().values_list('cohort__coh_cohort_name','mky_id','mky_weight')), columns=['cohort','mky_id','weight'])
# mid_no_weight = df_m_weight[np.isnan(df_m_weight.weight)].mky_id
# for mid in mid_no_weight:
#     weight = np.mean(MonkeyToDrinkingExperiment.objects.filter(monkey=Monkey.objects.get(mky_id=mid)).values_list('mtd_weight', flat=True))
#     print mid, weight
# # print m.mky_weight
# # mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date')
# # print mtds.values_list('mtd_weight', flat=True)
# # df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date','mtd_weight')), columns=['date', 'weights'])
# # print df.weights
# # plt.plot(df.date, df.weights)

###3-28-2015
# import numpy as np
# vector1 = np.array([1, 2, 3])
# vector2 = np.array([4, 5, 6])
# print vector1 + vector2
# print (vector1 + vector2)/2.0

# a = [1,1,1,1,2,2,2,2,3,3,4,5,5]
# from itertools import groupby
# print [(key, len(list(group))) for key, group in groupby(a)]

# def showCM(cm, plot=True):
#     print(cm)
#
#     #Accuracy
#     trues = sum(cm[i][i] for i in xrange(0, len(cm)))
#     accuracy = trues / (cm.sum() * 1.0)
#     print ('Accuracy: %s' % accuracy)
#
#     #Balanced Error Rate
#     k = len(cm)
#     error_rate = 0
#     for i in xrange(0, k):
#         sumrow = 0
#         for j in xrange(0, k):
#             sumrow += cm[i][j]
#         error_rate += 1.0 * cm[i][i] / sumrow
#     balanced_error_rate = 1 - error_rate / k
#     print ('Balanced Error Rate: %s' % balanced_error_rate)
#     print '--> where BER = 1 - 1/k * sum_i (m[i][i] / sum_j (m[i][j]))'
#
#     if plot:
#         fig = plt.figure()
#         ax = fig.add_subplot(111)
#         ms = ax.matshow(cm)
#         ax.set_title('Confusion matrix')
#         plt.colorbar(ms)
#         ax.set_ylabel('True label')
#         ax.set_xlabel('Predicted label')
#         ax.set_xticklabels(['', 'LD', 'BD', 'HD', 'VHD'])
#         ax.set_yticklabels(['', 'LD', 'BD', 'HD', 'VHD'])
#         plt.tight_layout()
#         pylab.show()
#
# cm = np.zeros(shape=(4,4))#, dtype=int)
# cm[0][0] = 6
# cm[0][1]=1
# cm[0][2]=0
# cm[0][3]=1
#
# cm[1][0]=1
# cm[1][1]=1
# cm[1][2]=3
# cm[1][3]=0
#
# cm[2][0]=0
# cm[2][1]=0
# cm[2][2]=3
# cm[2][3]=0
#
# cm[3][0]=1
# cm[3][1]=0
# cm[3][2]=1
# cm[3][3]=6
#
# showCM(cm, True)
#
# k = 4
# sums = np.sum(cm)
# for i in xrange(0, k):
#     for j in xrange(0, k):
#         cm[i][j] = 1.0 * cm[i][j] /  sums
#
# print cm
# fig = plt.figure()
# ax = fig.add_subplot(111)
# ms = ax.matshow(cm)
# ax.set_title('Confusion matrix')
# plt.colorbar(ms)
# ax.set_ylabel('True label')
# ax.set_xlabel('Predicted label')
# ax.set_xticklabels(['', 'LD', 'BD', 'HD', 'VHD'])
# ax.set_yticklabels(['', 'LD', 'BD', 'HD', 'VHD'])
# plt.tight_layout()
# pylab.show()
#
#
# cm[0][0] = 33
# cm[1][0] = 17
# cm[2][0] = 19
# cm[3][0] = 31
#
# print cm
# #Balanced Error Rate
# k = len(cm)
# error_rate = 0
# for i in xrange(0, k):
#     sumrow = 0
#     for j in xrange(0, k):
#         sumrow += cm[i][j]
#     error_rate += 1.0 * cm[i][i] / sumrow
# balanced_error_rate = 1 - error_rate / k
# print ('Balanced Error Rate: %s' % balanced_error_rate)
# print '--> where BER = 1 - 1/k * sum_i (m[i][i] / sum_j (m[i][j]))'


###9 Apr 2015
# cohort_names = ["INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 7b", "INIA Rhesus 7a"]
# cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
# print cohorts
# monkeys  = Monkey.objects.filter(cohort__in=cohorts)
# mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey__in=monkeys)
# becs = MonkeyBEC.objects.OA().filter(monkey__in=monkeys)
#
# table = []
# for i, m in enumerate(monkeys):
#     #End Date
#     end_date = CohortEvent.objects.filter(cohort=m.cohort).filter(event=42)[0].cev_date
#
#     #EtOH
#     mtds_m = mtds.filter(monkey = m).filter(drinking_experiment__dex_date__lte=end_date).order_by('-drinking_experiment__dex_date')[:30]
#     mean_etoh = mtds_m.aggregate(models.Avg('mtd_etoh_g_kg')).values()[0]
#
#     #BEC
#     becs_m = becs.filter(monkey = m).filter(bec_collect_date__lte=end_date).order_by('-bec_collect_date')[:3]
#     mean_bec = becs_m.aggregate(models.Avg('bec_mg_pct')).values()[0]
#
#     if mean_etoh != None and mean_bec != None:
#         table.append([m.mky_id, mean_etoh, mean_bec])
#
# print table
# df = pd.DataFrame(table, columns=['mky_id', 'mean_etoh_gkg', 'mean_bec'])
# print df
#
# print pd.DataFrame(list(CohortEvent.objects.filter(cohort=cohorts[0]).values_list('cev_date', 'event__evt_id', 'event__evt_name')), columns=['date','id','name'])
#
# # becs_m = MonkeyBEC.objects.filter(monkey = Monkey.objects.get(mky_id=10054)).order_by('bec_collect_date').values_list('bec_mg_pct', flat=True)
# # plt.plot(becs_m)

###16 Apr 2015
# import datetime
# cohort_names = ["INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 7b", "INIA Rhesus 7a"]
# cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
# for cohort in cohorts:
#     monkeys  = Monkey.objects.filter(cohort=cohort)
#     mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey__in=monkeys)
#     becs = MonkeyBEC.objects.OA().filter(monkey=monkeys)
#
#     #Start - End Date
#     end_date = CohortEvent.objects.filter(cohort=cohort).filter(event=42)[0].cev_date
#     start_date = end_date - datetime.timedelta(days=29)
#
#     table = []
#     for i, m in enumerate(monkeys):
#         #EtOH
#         mtds_m = mtds.filter(monkey = m).filter(drinking_experiment__dex_date__gte=start_date).\
#             filter(drinking_experiment__dex_date__lte=end_date).order_by('drinking_experiment__dex_date')
#         if i == 0:
#             table.append(['Date: '] + [d.strftime("%Y-%m-%d") for d in mtds_m.values_list('drinking_experiment__dex_date', flat=True)])
#             table.append(['Etohs: '] + ['-' for i in xrange(len(table[0])-1)])
#         etohs = mtds_m.values_list('mtd_etoh_g_kg', flat=True)
#         if len(etohs) > 5 :
#             table.append([m.mky_id] + list(etohs))
#
#     table.append(['BECs: '] + ['-' for i in xrange(len(table[0])-1)])
#     for i, m in enumerate(monkeys):
#         #BEC
#         bec_values = becs.filter(monkey = m).filter(bec_collect_date__gte=start_date).\
#             filter(bec_collect_date__lte=end_date).order_by('bec_collect_date').values_list('bec_collect_date','bec_mg_pct')
#         if len(bec_values) > 0:
#             becs_row = [0 for i in xrange(len(table[0])-1)]
#             for bec in bec_values:
#                 becs_row[table[0].index(bec[0].strftime("%Y-%m-%d"))] = bec[1]
#             table.append([m.mky_id] + becs_row)
#
#     #print table
#     df = pd.DataFrame(table)
#     df = df.set_index([0])
#     df.to_csv('/home/alex/Dropbox/Baylor/Matrr/_etoh_per_cohort/' + cohort.coh_cohort_name + '.csv')
#     #print df
#


### 27 April 2015
# # Load Cohort 10
# # coh10_file = '/home/alex/Dropbox/Baylor/Matrr/coh10/41.coh10_ind_sum_corrected_20150427.csv'
# from matrr.utils.database import load
# # load.load_mtd(coh10_file, 'Induction', 'INIA Rhesus 10')
#
# coh10_file_22hr = '/home/alex/Dropbox/Baylor/Matrr/coh10/Coh10_22hr_Sum_20150423matrr.csv'
# from matrr.utils.database import load
# load.load_mtd(coh10_file_22hr, 'Open Access', 'INIA Rhesus 10', update_duplicates=True)
#
# # coh10_exception_file = '/home/alex/Dropbox/Baylor/Matrr/coh10/Coh10_exception_days.csv'
# # load.load_monkey_exceptions(coh10_exception_file, overwrite=False, header=True)
# #
# m = Monkey.objects.get(mky_id=10208)
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date')
# df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date', 'mtd_etoh_g_kg')), columns=['date', 'etoh'])
# pylab.plot(df.date, df.etoh, 'bo')
# # #print m.mky_age_at_intox
#
# # print m.mky_real_id
# # print MonkeyException.objects.filter(monkey=m)


###4-29-2015
## Upload timeline for cohort 13
# c = Cohort.objects.get(coh_cohort_name = 'INIA Cyno 13')
# df = pd.DataFrame(list(CohortEvent.objects.filter(cohort=c).values_list('event__evt_id', 'event__evt_name', 'cev_date')))
# print df
#
# timelines_all = '/home/alex/Dropbox/Baylor/Matrr/coh13/coh13_timeline.csv'
# from matrr.utils.database import load
# load.load_cohort_timelines(timelines_all, True)


###4-30-2015
## Upload BECs for Cohort 10
# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c)
# print MonkeyBEC.objects.filter(monkey__in=monkeys)
#
# filename = '/home/alex/Dropbox/Baylor/Matrr/coh10/42.coh10_bec_1year_20150429.csv'
# from matrr.utils.database import load
# load.load_bec_data(filename, True, True)
#
# print MonkeyBEC.objects.filter(monkey__in=monkeys)

# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c)
# print MonkeyBEC.objects.OA().filter(monkey__in=monkeys)
# for bec in MonkeyBEC.objects.filter(monkey__in=monkeys):
#     bec.populate_fields(True)
#     bec.save()
# print MonkeyBEC.objects.OA().filter(monkey__in=monkeys)
#
###5-1-2015
## Populate Drinking Category
# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c)
# for m in monkeys:
#     m.mky_study_complete = True
#     m.populate_age_at_intox()
#     m.populate_drinking_category()
#     m.save()
#     print m.mky_drinking_category, m.mky_age_at_intox


### 5-2-2015
# # m = Monkey.objects.get(mky_id=10208)
# # mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date')
# # plt.plot(mtds.values_list('mtd_etoh_g_kg', flat=True))
#
#
# ind_boutDrinks_coh10 = '/home/alex/MATRR/Coh10_data/Coh10_IndBoutsDrinks/'
# ind_data_coh10 = '/home/alex/MATRR/Coh10_data/Coh10_Ind_data_20150424/'
#
# OA_boutDrinks_coh10 = '/home/alex/MATRR/Coh10_data/Coh10_22hrBoutsDrinks1yr/'
# OA_data_coh10 = '/home/alex/MATRR/Coh10_data/Coh10_22hr_data_1yr_20150424/'
#
# from matrr.utils.database import load
# #load.load_eevs(ind_data_coh10, 'Induction')
# #load.load_eevs(OA_data_coh10, 'Open Access')
#
# load.load_edrs_and_ebts('INIA Rhesus 10', 'Induction', ind_boutDrinks_coh10)
# #load.load_edrs_and_ebts('INIA Rhesus 10', 'Open Access', OA_boutDrinks_coh10)


# duration = 10 * 60
# mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=Monkey.objects.get(mky_id=10208)).exclude_exceptions().order_by('drinking_experiment__dex_date')
# volumes = []
# for mtd in mtds:
#     bouts = mtd.bouts_set.filter(ebt_start_time__lt=duration)
#     drinks_in_bout = ExperimentDrink.objects.Ind().filter(ebt__in=bouts).filter(edr_start_time__lt=duration)
#     vols = numpy.array(drinks_in_bout.values_list('edr_volume'))
#     volumes.append(vols.sum() / mtd.mtd_etoh_intake)
# print pd.DataFrame(list(volumes))

### 5-3-2015
# from matrr.plotting import monkey_plots
# m = Monkey.objects.get(mky_id=10062)
# fig = monkey_plots.monkey_etoh_bouts_vol(m,circle_min=150, circle_max=200)
# matplotlib.rcParams.update({'font.size': 18})

# matplotlib.rcParams.update({'font.size': 12})
# m = Monkey.objects.get(mky_id=10062)
# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c).filter(mky_drinking=True)
# print monkeys
# print [m.mky_real_id for m in monkeys]
#
# # Populate fields
# # for m in monkeys:
# #     print m
# #     mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m)
# #     for mtd in mtds:
# #         mtd.populate_fields()
#
# duration = 20 * 60
# mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=Monkey.objects.get(mky_real_id=27682)).exclude_exceptions().order_by('drinking_experiment__dex_date')
# mtd_bad = mtds[15]
# mtd_bad.mex_excluded = True
# mtd_bad.save()
# mtds = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=Monkey.objects.get(mky_real_id=27682)).exclude_exceptions().order_by('drinking_experiment__dex_date')
# print mtds.values_list('mtd_etoh_g_kg', flat=True)
# volumes = mtds.values_list('mtd_etoh_intake', flat=True)
# print volumes
# print volumes[15]
# # mtd = mtds[45]
# # print mtd
# # print mtd.mtd_etoh_intake
# # bouts = ExperimentBout.objects.filter(mtd=mtd).filter(ebt_start_time__lt=duration)
# # print bouts
# # drinks_in_bout = ExperimentDrink.objects.Ind().filter(ebt__in=bouts).filter(edr_start_time__lt=duration)
# # print drinks_in_bout
# # vols = numpy.array(drinks_in_bout.values_list('edr_volume'))
# # print vols
#
# volumes = []
# for i, mtd in enumerate(mtds):
#     bouts = mtd.bouts_set.filter(ebt_start_time__lt=duration)
#     drinks_in_bout = ExperimentDrink.objects.Ind().filter(ebt__in=bouts).filter(edr_start_time__lt=duration)
#     vols = numpy.array(drinks_in_bout.values_list('edr_volume'))
#     if i == 15:
#         print 15
#     print i, vols.sum() / mtd.mtd_etoh_intake
#     volumes.append(vols.sum() / mtd.mtd_etoh_intake)
# plt.plot(pd.DataFrame(list(volumes)))

# fig, axs = plt.subplots(monkeys.count(),1, figsize=(10,16))
# for i, m in enumerate(monkeys):
#     axs[i].plot(m.etoh_during_ind(10), 'r-o')
#     title = str(m.mky_id) + ', ' + str(m.mky_drinking_category) + ', ' + str(m.mky_age_at_intox)
#     #axs[i].set_title(title)
#     axs[i].text(.5,.9,title,
#         horizontalalignment='center',
#         transform=axs[i].transAxes)
# fig.subplots_adjust(hspace=0)
# fig.subplots_adjust(wspace=0)
# plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
# plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)
# plt.tight_layout()

### May 7 2015
# c = Cohort.objects.get(coh_cohort_name = "INIA Cyno 2")
# df = pd.DataFrame(list(CohortEvent.objects.filter(cohort=c).values_list('event__evt_id', 'event__evt_name', 'cev_date')))
# print df

# for event in EventType.objects.all():
#     if (event.evt_name in ['Ethanol Induction Begin', 'Ethanol Induction End']):
#         event.evt_dex_type = 'Induction'
#     if "Open Access" in event.evt_name:
#         if "Endocrine" not in event.evt_name:
#             event.evt_dex_type = 'Open (Alcohol) Access'
#     event.save()
#
#
# df = pd.DataFrame(list(EventType.objects.values_list('evt_id', 'evt_name', 'evt_dex_type')), columns=['id', 'name', 'dex_type'])
# print df

### 8 may 2015
# from django.db.models import Q
# jon_user = User.objects.get(username='jon')
# jon_user2 = User.objects.get(username='jarquet')
# requests = Request.objects.shipped().filter(~Q(user=jon_user)).filter(~Q(user=jon_user2))
# print len(requests)
# shipments = Shipment.objects.filter(req_request__in=requests)
# print len(shipments)
#
# df = pd.DataFrame(list(shipments.values_list('shp_shipment_id', 'req_request_id', 'req_request__user__first_name',
#                                              'req_request__user__last_name', 'req_request__user__username')),
#                        columns=['ship_id', 'request_id', 'first name', 'last name', 'username'])
# df.to_csv('/home/alex/Dropbox/Baylor/Matrr/shipments_without_all_jons.csv')
# print df

### 12 May 2015
import lwr
c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c).filter(mky_drinking=True)
# mtds_all = MonkeyToDrinkingExperiment.objects.filter(monkey__in=monkeys)
# fig, axs = plt.subplots(monkeys.count(),1, figsize=(10,16))
# for i, m in enumerate(monkeys):
#     print str(i+1) + " out of: " + str(len(monkeys))
#     mtds = mtds_all.filter(monkey=m).order_by('drinking_experiment__dex_date')
#     df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date', 'mtd_etoh_g_kg')), columns=['date', 'etoh'])
#     xpred, ypred = lwr.wls(xrange(len(df.index)), df.etoh, False, tau=0.45)
#     axs[i].plot(df.date, df.etoh, dc_colors_o[m.mky_drinking_category], df.date, ypred, 'b-')
#     title = str(m.mky_id) + ', ' + str(m.mky_drinking_category) + ', ' + str(m.mky_age_at_intox)
#     #axs[i].set_title(title)
#     axs[i].text(.5,.9,title,
#         horizontalalignment='center',
#         transform=axs[i].transAxes)
# fig.subplots_adjust(hspace=0)
# fig.subplots_adjust(wspace=0)
# plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
# plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)
# plt.tight_layout()

### 13 May 2015
# from matrr.plotting import plot_tools as pl
# pl.create_max_bout_cumsum_horibar_canonicals(c)
# pl.create_mtd_tools_canonicals(c, True)


### 14 May 2015
# print_full(pd.DataFrame(list(TissueType.objects.all().values_list('tst_tissue_name', flat=True))))
# tst = TissueType.objects.get(tst_tissue_name = 'Nucleus accumbens (Core)')
# print tst
# tissue_requests = TissueRequest.objects.filter(tissue_type=tst)
# requests = [ts.req_request for ts in tissue_requests]
# print len(requests)
# shipments = Shipment.objects.filter(req_request__in=requests)
# print len(shipments)
# df = pd.DataFrame(list(shipments.values_list('shp_shipment_id', 'req_request_id', 'req_request__user__first_name',
#                                              'req_request__user__last_name', 'req_request__user__username')),
#                        columns=['ship_id', 'request_id', 'first name', 'last name', 'username'])
# df.to_csv('/home/alex/Dropbox/Baylor/Matrr/shipments_with_nucleus_accumbes_core.csv')
# print df

### 18 May 2015
# cohort_names = ["INIA Rhesus 10", "INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 6a", "INIA Rhesus 7b",
#             "INIA Rhesus 6b", "INIA Rhesus 7a"]
# ml_cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
# monkeys = Monkey.objects.filter(cohort__in=ml_cohorts).exclude(mky_drinking_category = None)
# # for m in monkeys:
# #     mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m).order_by('drinking_experiment__dex_date')
# #     m.mky_days_at_necropsy = (mtds.last().drinking_experiment.dex_date - m.mky_birthdate).days
# #     m.save()
# df = pd.DataFrame(list(monkeys.values_list('mky_id', 'cohort', 'mky_days_at_necropsy')), columns = ['mky_id', 'cohort_id', 'days_at_necropsy'])
# # print df
# # df = df.sort('cohort_id')
# # colors = [coh_colors[id] for id in df.cohort_id]
# # y = df.days_at_necropsy
# # x = np.arange(len(y))
# # plt.scatter(x, y, c=colors, s = 150)
# fig = plt.figure()
# matplotlib.rcParams.update({'font.size': 18})
# coh_ids = np.unique(df.cohort_id)
# gb = df.groupby('cohort_id')
# for i, coh_id in enumerate(coh_ids):
#     cohort = Cohort.objects.get(coh_cohort_id = coh_id)
#     index = gb.get_group(coh_id).index
#     x = df[df.index.isin(index)]
#     t = [i for num in xrange(len(x))]
#     print t
#     print x
#     plt.scatter(t,x.days_at_necropsy, c=coh_colors[coh_id], s = 500, label=cohort.coh_cohort_name, marker='o', alpha=.5)
# plt.legend(loc=1)
# plt.ylabel('Age at Necropsy (Days)')
# plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)


### 20 May 2015
# cohort_names = ["INIA Rhesus 10", "INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 6a", "INIA Rhesus 7b",
#             "INIA Rhesus 6b", "INIA Rhesus 7a"]
# ml_cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
# ml_monkeys = Monkey.objects.filter(cohort__in=ml_cohorts).exclude(mky_drinking_category = None)
# m = ml_monkeys[15]
#
# for m in ml_monkeys:
#     print m
#     endocrine_profiles = CRHChallenge.objects.filter(monkey=m)
#     print endocrine_profiles

# c = Cohort.objects.get(coh_cohort_name = 'INIA Rhesus 10')
# monkeys = Monkey.objects.filter(cohort=c).filter(mky_drinking=True)
# fig, axs = plt.subplots(monkeys.count(),1, figsize=(10,16))
# for i, m in enumerate(monkeys):
#     mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m).order_by('drinking_experiment__dex_date')
#     df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date', 'mtd_etoh_g_kg')), columns=['date', 'etoh'])
#     axs[i].plot(xrange(len(df.date)), df.etoh, 'b-o', alpha=0.2)
#     title = str(m.mky_id) + ', ' + str(m.mky_drinking_category) + ', ' + str(m.mky_age_at_intox)
#     axs[i].text(.5,.9,title,
#         horizontalalignment='center',
#         transform=axs[i].transAxes)
# fig.subplots_adjust(hspace=0)
# fig.subplots_adjust(wspace=0)
# plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
# plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)
# plt.tight_layout()
#
# def plotMTDSforMonkey(m):
#     mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m).order_by('drinking_experiment__dex_date')
#     df = pd.DataFrame(list(mtds.values_list('drinking_experiment__dex_date', 'mtd_etoh_g_kg')), columns=['date', 'etoh'])
#     plt.plot(xrange(len(df.date)), df.etoh, 'b-o', alpha=0.2)


### 22 MAY 2015
# data = pd.read_pickle('data_analysis/may_data_all.plk')
# base_rate_accuracy = data.DC.value_counts()/len(data.index)
# print  "\n-----------------------\nAll:\n" + str(base_rate_accuracy)
#
# data_LDBD = data.loc[data['DC'].isin(['LD','BD'])]
# base_rate_accuracy = data_LDBD.DC.value_counts()/len(data_LDBD.index)
# print  "\n-----------------------\nLD vs BD:\n" + str(base_rate_accuracy)
#
# data_HDVHD= data.loc[data['DC'].isin(['HD','VHD'])]
# base_rate_accuracy = data_HDVHD.DC.value_counts()/len(data_HDVHD.index)
# print  "\n-----------------------\nHD vs VHD:\n" + str(base_rate_accuracy)
#
# print "\n-----------------------\n Grand Average Accuracy:"
# grand_average_accuracy = 0.52*0.87*0.81 + 0.48*0.87*0.94
# print grand_average_accuracy

# data = pd.read_pickle('data_analysis/may_data_all.plk')
# base_rate_accuracy = data.DC.value_counts()
# print  "\n-----------------------\nAll:\n" + str(base_rate_accuracy)

# print 0.52 * 0.87, 0.48 * 0.87
# print 0.52*0.87*0.81, 0.48*0.87*0.94
# print (0.52 *0.81 + 0.48 * 0.94) * 0.87
# print 0.62 * 0.52
# print 0.76 / 0.32

# print [i / 28.0 + 1for i in xrange(341)]

### 29 June 2015
# bds = BoneDensity.objects.all()
# df = pd.DataFrame(list(bds.values_list('monkey__mky_id', 'monkey__mky_drinking_category', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd')), columns=['mky_id', 'dc', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd'])
# print len(df)
# print df
# print df.mky_id.unique()
# print df[df.mky_id == 10069]
# df.color = df.dc.apply(lambda x: dc_colors[x])
# plt.scatter(df.bdy_bmc, df.bdy_area, c=df.color, s=80)
# plt.show()

# c = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6a')
# m10070 = Monkey.objects.get(mky_id=10070)
# m10052 = Monkey.objects.get(mky_id=10052)
# print MonkeyImage.objects.filter(monkey=m10070)
# print MonkeyImage.objects.filter(monkey=m10052)
#
# from plotting.plot_tools import *
# create_max_bout_cumsum_horibar_canonicals(c)#, create_monkey_plots=True)

### 30 June 2015

# #Cohort Bone Density
# import matplotlib.patches as mpatches
# ld_patch = mpatches.Patch(color='g', label='LD')
# bd_patch = mpatches.Patch(color='b', label='BD')
# hd_patch = mpatches.Patch(color='y', label='HD')
# vhd_patch = mpatches.Patch(color='r', label='VHD')
# control_patch = mpatches.Patch(color='k', label='Control')
#
# tool_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
# ax1 = tool_figure.add_subplot(111)
# c = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')
# bds = BoneDensity.objects.filter(monkey__in=Monkey.objects.filter(cohort=c))
# df = pd.DataFrame(list(bds.values_list('monkey__mky_id', 'monkey__mky_drinking_category', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd')), columns=['mky_id', 'dc', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd'])
# df.color = df.dc.apply(lambda x: dc_colors[x])
# ax1.scatter(df.bdy_area, df.bdy_bmc, c=df.color, s=80, alpha=0)
# for label, x, y, col in zip(df.mky_id, df.bdy_area, df.bdy_bmc, df.color):
#     ax1.annotate(
#         label,
#         xy = (x, y), xytext = (20, -7),
#         textcoords = 'offset points', ha = 'right', va = 'bottom',
#         bbox = dict(boxstyle = 'round,pad=0.5', fc = col, alpha = 0.5))
# ax1.grid()
# ax1.set_xlabel(r'Bone Area $(cm^2)$')
# ax1.set_ylabel('Bone Mineral Content $(g)$')
# ax1.set_title('BMA and BMC for NHP cohort ' + c.coh_cohort_name)
# matplotlib.rcParams.update({'font.size': 16})
# for dc in ['LD', 'BD','HD','VHD', 'None']:
#     if dc == 'None':
#         df2 = df[~df.dc.isin(['LD', 'BD','HD','VHD'])]
#     else:
#         df2 = df[df.dc == dc]
#     if len(df2) > 1:
#         fit = np.polyfit(df2.bdy_area, df2.bdy_bmc, 1)
#         fit_fn = np.poly1d(fit)
#         ax1.plot(df2.bdy_area, fit_fn(df2.bdy_area), dc_colors[dc], lw=2)
# ax1.legend(handles=[ld_patch, bd_patch, hd_patch, vhd_patch, control_patch], loc=4)
#
# plt.show()

# CohortImage.objects.all().delete()
# plots = ['cohort_bone_densities',            ]
# from matrr.models import CohortImage, Cohort
# from matrr.plotting import cohort_plots
# import gc
# for cohort in BoneDensity.objects.all().values_list('monkey__cohort', flat=True).distinct():
#     cohort = Cohort.objects.get(pk=cohort)
#     print cohort
#     for graph in plots:
#         gc.collect()
#         CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=cohort_plots.COHORT_PLOTS[graph][1], canonical=True)
#
#

#plt.show()