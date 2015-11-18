import sys, os
sys.path.append('~/pycharm/ve1/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.models import Monkey
import dateutil
from matrr.plotting import monkey_plots as mkplot
import matplotlib
matplotlib.rcParams['savefig.directory'] = '~/win-share/matrr_sync/'
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


def normalize_float_cols(_df):
    def normalize(__df):
        return (__df - __df.mean()) / (__df.std())
    float_columns = [column for column in _df.columns if _df[column].dtype == 'float64']
    _df[float_columns] = normalize(_df[float_columns])
    return _df

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


# from pylab import *
# def print_available_backends():
#     import time
#
#     import matplotlib.backends
#     import matplotlib.pyplot as p
#     import os.path
#
#
#     def is_backend_module(fname):
#         """Identifies if a filename is a matplotlib backend module"""
#         return fname.startswith('backend_') and fname.endswith('.py')
#
#     def backend_fname_formatter(fname):
#         """Removes the extension of the given filename, then takes away the leading 'backend_'."""
#         return os.path.splitext(fname)[0][8:]
#
#     # get the directory where the backends live
#     backends_dir = os.path.dirname(matplotlib.backends.__file__)
#
#     # filter all files in that directory to identify all files which provide a backend
#     backend_fnames = filter(is_backend_module, os.listdir(backends_dir))
#
#     backends = [backend_fname_formatter(fname) for fname in backend_fnames]
#
#     print "supported backends: \t" + str(backends)
#
#     # validate backends
#     backends_valid = []
#     for b in backends:
#         try:
#             p.switch_backend(b)
#             backends_valid += [b]
#         except:
#             continue
#
#     print "valid backends: \t" + str(backends_valid)
#
# print_available_backends()


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
# df = pd.DataFrame(list(bds.values_list('monkey__mky_id', 'monkey__cohort', 'monkey__mky_drinking_category', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd')), columns=['mky_id', 'coh', 'dc', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd'])
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

#print BoneDensity.objects.all().values_list('monkey__cohort__coh_cohort_id', flat=True).distinct()
# CohortImage.objects.filter(method__contains='densities').delete()
# from plotting import plot_tools
# plot_tools.create_bone_densities_plots()

# def prefix_f(W):
#     fail =  len(W)*[0]
#     fail[0] = -1
#
#     pos = 2
#     cnd = 0
#     while pos < len(W):
#         if W[pos - 1] == W[cnd]:
#             cnd += 1
#             fail[pos] = cnd
#             pos += 1
#         else:
#             if cnd > 0:
#                 cnd = fail[cnd]
#             else:
#                 fail[pos] = 0
#                 pos +=1
#     return fail
#
#
# print prefix_f('bbcbbcbbce')
# print prefix_f('ababcb')

### 2 July 2015
# c2 = Cohort.objects.get(coh_cohort_name='INIA Cyno 2')
# r5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')
# r6a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6a')
# r6b = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6b')
# r10 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 10')
# c2 = Cohort.objects.get(coh_cohort_name='INIA Cyno 2')
# r7b = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')

from plotting import plot_tools
from plotting import monkey_plots
from plotting import cohort_plots
# plot_tools.create_bec_tools_canonicals(c2, True)

# for monkey in Monkey.objects.filter(cohort=r6a):
#     bec_records = monkey.bec_records.all()
#     for bec_rec in bec_records:
#         #f bec_rec.mtd.drinking_experiment.dex_type is None:
#         if bec_rec.mtd is None:
#             print monkey, bec_rec

#alice = Monkey.objects.get(mky_id=10078)
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=alice).order_by('drinking_experiment__dex_date')
# for date in mtds.values_list('drinking_experiment__dex_date', flat=True):
#     print date
#r10.cbc.populate_fields()
#monkey_plots.monkey_etoh_bouts_vol(alice)
#plot_tools.create_mtd_tools_canonicals(r10, True)

# print NecropsySummary.objects.filter(monkey=Monkey.objects.filter(cohort=r10)[1])
#
# cohort_plots.cohort_etoh_induction_cumsum(r6a, 0)
# cohort_plots.cohort_etoh_induction_cumsum(r6a, 1)
# cohort_plots.cohort_etoh_induction_cumsum(r6a, 2)
# cohort_plots.cohort_etoh_induction_cumsum(r6a, 3)
#cohort_plots.cohort_etoh_max_bout_cumsum_horibar_ltgkg(r6a)
#plot_tools.create_necropsy_plots(r10, True)
#plot_tools.create_daily_cumsum_graphs()

### 3 July 2015

# timeline = pd.DataFrame(list(CohortEvent.objects.filter(cohort=c2).values_list('event__evt_id', 'event__evt_name', 'cev_date')), columns=['id', 'name', 'date'])
# print timeline

# def dump_MATRR_current_data_grid():
#     cohorts = Cohort.objects.all().exclude(coh_cohort_name__icontains='devel').order_by('pk')
#     data_types = ["Necropsy", "Drinking Summary", "Bouts", "Drinks",
#                   #"Raw Drinking data",
#                   "Exceptions", "BEC",
#                   "Metabolite", "Protein",
#                   'Cohort Plots', 'Monkey Plots', 'Cohort Protein Plots', 'Tissue Requests', 'Tissue Samples',
#                   "Hormone",
#                   '    Cortisol', '    ACTH', '    Testosterone', '    Deoxycorticosterone', '    Aldosterone', '    DHEAS', # 6 types of hormones
#                    'Bone Density',
#                   '    Area', '    Bone Mineral Content', '    Bone Mineral Density',
#                   'CRH Challenge',
#                   '    ACTH', '    Cortisol', '    17beta-estradiol', '    Deoxycorticosterone', '    Aldosterone', '    DHEA-S',
#                   'ElectroPhys',
#                   "    Frequency (hz)", "    In-Event Interval","    Amplitude","    Rise (ms)","    Decay (ms)", "    Area","    Baseline","    Noise", "    10-90 Rise (ms)","    10-90 Slope","    Half Width","    50 Rise (ms)","    Rel Time",
#                   ]
#     data_classes = [NecropsySummary, MonkeyToDrinkingExperiment, ExperimentBout, ExperimentDrink,
#                     #ExperimentEvent,
#                     MonkeyException, MonkeyBEC,
#                     MonkeyMetabolite, MonkeyProtein,
#                     CohortImage, MonkeyImage, CohortProteinImage, TissueRequest, TissueSample,
#                     MonkeyHormone,
#                     MonkeyHormone,MonkeyHormone,MonkeyHormone,MonkeyHormone,MonkeyHormone,MonkeyHormone, # 6 types of hormones
#                     BoneDensity,
#                     BoneDensity,BoneDensity,BoneDensity,
#                     CRHChallenge,
#                     CRHChallenge,CRHChallenge,CRHChallenge,CRHChallenge,CRHChallenge,CRHChallenge,
#                     MonkeyEphys,
#                     MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,MonkeyEphys,
#                     ]
#     cohort_fields = ['monkey__cohort', 'monkey__cohort', 'mtd__monkey__cohort', 'ebt__mtd__monkey__cohort',
#                      #'monkey__cohort',
#                      'monkey__cohort', 'monkey__cohort',
#                      'monkey__cohort', 'monkey__cohort',
#                      'cohort', 'monkey__cohort', 'cohort', 'req_request__cohort','monkey__cohort',
#                      'monkey__cohort',
#                      'monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort', # 6 types of hormones
#                      'monkey__cohort',
#                      'monkey__cohort','monkey__cohort','monkey__cohort',
#                      'monkey__cohort',
#                      'monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort',
#                      'monkey__cohort',
#                      'monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort','monkey__cohort',
#                      ]
#     exclude_none_fields = [
#                     '','','','',
#                     #'',
#                     '','',
#                     '','',
#                     '','','','','',
#                     '',
#                     'mhm_cort', 'mhm_acth', 'mhm_t', 'mhm_doc', 'mhm_ald', 'mhm_dheas',
#                     '',
#                     'bdy_area','bdy_bmc','bdy_bmd',
#                     '',
#                     'crc_acth', 'crc_cort', 'crc_e', 'crc_doc', 'crc_ald', 'crc_dheas',
#                     '',
#                     'mep_freq','mep_iei','mep_amp','mep_rise','mep_decay','mep_area','mep_baseline','mep_noise','mep_10_90_rise','mep_10_90_slope','mep_half_width','mep_50_rise','mep_rel_time',
#
#                     ]
#     assert len(data_types) == len(data_classes) == len(cohort_fields) == len(exclude_none_fields), \
#                                                                     "data_types, data_classes, and cohort_fields " \
#                                                                        "aren't all the same length.  You probably " \
#                                                                        "forgot to add a value to one of them."
#     headers = ['Data Type']
#     headers.extend(cohorts.values_list('coh_cohort_name', flat=True))
#     data_rows = list()
#     for _type, _field, _class, _exclude in zip(data_types, cohort_fields, data_classes, exclude_none_fields):
#         print _type, _field, _class, _exclude
#         _row = [_type, ]
#         for _cohort in cohorts:
#             ### 14 Jul 2015:
#             ### Count for cohort excluding Nones for specific attributes
#             if _exclude == '':
#                 row_count = _class.objects.filter(**{_field: _cohort}).count()
#             else:
#                 row_count = _class.objects.filter(**{_field: _cohort}).exclude(**{_exclude: None}).exclude(**{_exclude: 0.0}).count()
#             _row.append(row_count)
#         data_rows.append(_row)
#
#     outcsv = open('data_grid.csv', 'w')
#     writer = csv.writer(outcsv)
#     writer.writerow(headers)
#     writer.writerows(data_rows)
#     outcsv.close()
#
#     context = {'headers': headers, 'data_rows': data_rows, 'last_updated': datetime.now().strftime('%Y-%m-%d') }
#     outjson = open('current_data_grid.json', 'w')
#     json_string = json.dumps(context)
#     outjson.write(json_string)
#     outjson.close()

#dump_MATRR_current_data_grid()

### Don't bother, depreciated method for proteins
# for cohort in Cohort.objects.all():
#     for protein in Protein.objects.all():
#         cnt = MonkeyProtein.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort)).count()
#         if cnt > 0:
#             print cohort, protein, cnt
#
# for cohort in Cohort.objects.all():
#     cohortHormones = MonkeyHormone.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort))
#     if cohortHormones.count() > 0:
#         df = pd.DataFrame(list(cohortHormones.values_list('mhm_date', 'mhm_cort',
#                                                       'mhm_acth', 'mhm_t', 'mhm_doc', 'mhm_ald', 'mhm_dheas')),
#                       columns = ['mhm_date', 'mhm_cort', 'mhm_acth', 'mhm_t', 'mhm_doc', 'mhm_ald', 'mhm_dheas'])
#
#         print cohort
#         print df


### 13 July 2015
#print NecropsySummary.objects.all().values_list('monkey__cohort__coh_cohort_name', flat=True).distinct()

# def human_format(num):
#     magnitude = 0
#     while abs(num) >= 1000:
#         magnitude += 1
#         num /= 1000.0
#     # add more suffixes if you need them
#     return '%.0f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
#
# print('the answer is %s' % human_format(7436313))
#
# json_file = open('current_data_grid.json', 'r')
# context = json.loads(json_file.read())
# for item in context['data_rows']:
#     for i, num in enumerate(item):
#         if i > 0:
#             item[i] = human_format(num)
#     print item

# cohortHormones = MonkeyHormone.objects.filter(monkey__in=Monkey.objects.filter(cohort=Cohort.objects.get(coh_cohort_name='INIA Cyno 2')))
# print 'all: ', cohortHormones.count()
# print cohortHormones.values_list('mhm_t', flat=True)
# cort = cohortHormones.exclude(mhm_t=None)
# print 'mhm_t: ', cort.count()


### 15 July 2015
# for cohort in Cohort.objects.all():
#     monkeys = Monkey.objects.filter(cohort=cohort)
#     cohortEphys = MonkeyEphys.objects.filter(monkey__in=monkeys)
#     if cohortEphys.count() > 0:
#         for m in monkeys:
#             mEphys = cohortEphys.filter(monkey=m)
#             if mEphys.count() > 0:
#                 print m
#                 df = pd.DataFrame(list(mEphys.values()))
#                 print cohort
#                 print df

### 16 Jul 2015
# cohort = Cohort.objects.get(coh_cohort_name = "INIA Rhesus 6a")
# bmcs = BoneDensity.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort)).values_list('bdy_bmc', flat=True)
# print bmcs
# sigma = np.std(bmcs)
# mean = np.mean(bmcs)
# print mean, sigma
# print [bmc for bmc in bmcs if abs(bmc-mean)>sigma]
#
# print BoneDensity.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort)).values()
# # for bd in BoneDensity.objects.all():
# #     bd.populate_fields()
# print BoneDensity.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort)).values_list('monkey__mky_id', "bdy_area_stdev")


# for cohort in Cohort.objects.all():
#     monkeys = Monkey.objects.filter(cohort=cohort)
#     cohortEphys = MonkeyEphys.objects.filter(monkey__in=monkeys)
#     if cohortEphys.count() > 0:
#         print cohort
#         df = pd.DataFrame(list(cohortEphys.values()))
#         print df

### 20 July 2015
# becs = MonkeyBEC.objects.OA().filter(monkey__in=Monkey.objects.filter(cohort=r7b))
# print pd.DataFrame(list(becs.values('monkey__mky_id').annotate(avg_bec=Avg('bec_mg_pct'))))

#plot_tools.create_bec_tools_canonicals(r7b, False)
#cohort_plots.cohort_summary_avg_bec_mgpct(r7b)
from matrr.plotting.cohort_plots import COHORT_PLOTS

# for cohort in Cohort.objects.all():
#     try:
#         CohortImage.objects.get_or_create(cohort=cohort, method='cohort_summary_avg_bec_mgpct',  title=COHORT_PLOTS['cohort_summary_avg_bec_mgpct'][1], canonical=True)
#         print 'done: ', cohort
#     except:
#         print 'fail: ', cohort
#         pass

r5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')
r6a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6a')
r6b = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6b')
r10 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 10')
c2 = Cohort.objects.get(coh_cohort_name='INIA Cyno 2')
r7b = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')
r7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')
c13 = Cohort.objects.get(coh_cohort_name='INIA Cyno 13')
c9 = Cohort.objects.get(coh_cohort_name='INIA Cyno 9')

#CohortImage.objects.filter(cohort=r10).filter(method__contains='bihourly').delete()
#plot_tools.create_bec_summary_plots(True, False)
#plot_tools.create_bec_histograms()
#plot_tools.create_mtd_tools_canonicals(r10, False)

### 22 July 2015
# r10.coh_upcoming = False
# r10.save()

# for field in r10._meta.fields:
#     print field.name
#
# print dir(r10)

# for cohort in Cohort.objects.all():
#     monkeys = Monkey.objects.filter(cohort=cohort)
#     cohortEphys = MonkeyEphys.objects.filter(monkey__in=monkeys)
#     if cohortEphys.count() > 0:
#         print cohort
#         df = pd.DataFrame(list(cohortEphys.values('monkey', 'mep_ephys_type', 'mep_amp')))
#         print df

# from matrr.utils.database import load
# load.load_cohort4_electrophys('/home/alex/Dropbox/Baylor/Matrr/christen/inhibitory_working_file_031914.csv', 'In')


### 23JUL2015e
# print pd.DataFrame(list(MonkeyEphys.objects.filter(mep_ephys_type='In').exclude(monkey__mky_drinking_category__isnull=True).
#                         values_list('monkey__mky_id','monkey__mky_drinking_category', 'mep_res', 'mep_cap', 'mep_freq', 'mep_amp')))


# df = pd.DataFrame(list(MonkeyEphys.objects.filter(mep_ephys_type='In').exclude(monkey__mky_drinking_category__isnull=True)\
#     .values_list('monkey__mky_id')\
#     .annotate(res=Avg('mep_res'))\
#     .annotate(cap=Avg('mep_cap'))\
#     .annotate(freq=Avg('mep_freq'))\
#     .annotate(amp=Avg('mep_amp'))\
#     .values_list('monkey__mky_id','monkey__mky_drinking_category','mep_lifetime_gkg','res', 'cap', 'freq', 'amp')),
#                   columns=['id','dc','lt_gkg', 'res', 'cap', 'freq', 'amp'])
# print df
#
# import scipy.stats as stats
# from patsy import dmatrices
# import numpy as np
# import pandas as pd
# import statsmodels.api as sm
# from statsmodels.formula.api import ols
# lm = ols('lt_gkg ~ res + cap + freq + amp', data=df).fit()
# print sm.stats.anova_lm(lm, typ=2)
# print lm.summary()

### 4 AUG 2015
# cohorts = Cohort.objects.filter(coh_cohort_name__in=['INIA Rhesus 4','INIA Rhesus 5','INIA Rhesus 7a','INIA Rhesus 7b'])
# monkeys = Monkey.objects.filter(cohort__in=cohorts)
# hormones = MonkeyHormone.objects.filter(monkey__in=monkeys)
# df = pd.DataFrame(list(hormones.values_list('monkey__cohort__coh_cohort_name', 'monkey__mky_id','mtd__drinking_experiment__dex_date',
#                                             'mtd__drinking_experiment__dex_type')), columns=['cohort', 'mky_id', 'mtd_date', 'dextype'])
# df = df[df.dextype=='Open Access']
# df.sort(['cohort', 'mky_id', 'mtd_date'], inplace=True)
# df.to_csv('/home/alex/Dropbox/Baylor/Matrr/csv_dumps/457a7b_hormone_dates.csv', index=False)
#
# #print MonkeyHormone.objects.filter(monkey=Monkey.objects.filter(mky_id=10054))

# print 0.48*0.94 + 0.52*0.81

# m = Monkey.objects.get(mky_id = 10032)
# print(m)
# mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=m).order_by("drinking_experiment__dex_date")
# values = list(mtds.values_list('mtd_etoh_g_kg', flat = True))
# df = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', 'drinking_experiment__dex_date')), columns=['gkg', 'date'])
# # i = 1
# # while i < len(df['date']):
# #     d = df['date'][i-1]
# #     d += timedelta(days=1)
# #     d += timedelta(days=1)
# #     if d < df['date'][i]:
# #         print df['date'][i-1], df['date'][i]
# #     i += 1
#
# df['gkg'].to_csv('/home/alex/Dropbox/Baylor/TimeSeries/R/ts_hw/ts_hw/gkg_10032.csv', index=False)

#print df
#plt.plot(values)


### 25 Sept 2015
#monkeys = Monkey.objects.filter(cohort=c13)
#print pd.DataFrame(list(monkeys.values_list('mky_name','mky_id','mky_drinking','mky_housing_control')))
#
# print max(Monkey.objects.all().values_list('mky_id', flat=True))
# mky33 = Monkey.objects.get(mky_id=10233)
# mky30 = Monkey.objects.get(mky_id=10230)
#
# mky33.mky_drinking = False
# mky33.save()
#
# mky30.mky_drinking = True
# mky30.save()
#
# print mky33
# print mky30

# from django.core.cache import cache
# cache.clear()
# cache.close()

# def load_cohort_10_13_inventory(input_file):
#     with open(input_file, 'rU') as f:
#         #1. Parse header to get monkeys
#         header = f.readline()
#         monkeys = Monkey.objects.filter(mky_real_id__in=header.split(';')[1:])
#         print monkeys
#
#         # Load Tissues
#         print "Loading Tissue Samples..."
#         read_data = f.readlines()
#         for line_number, line in enumerate(read_data):
#             split = line.split(';')
#             tissue_name = split[0]
#             data = split[1:]
#             tissue_type = TissueType.objects.filter(tst_tissue_name__iexact=tissue_name)
#             if not tissue_type:
#                 print "Error: Unknown tissue type " + tissue_name
#                 continue
#             elif tissue_type.count() == 1:
#                 tissue_type = tissue_type[0]
#                 for im, mky in enumerate(monkeys):
#                     if data[im] == 'X' or 'X\n':
#                         tss, created = TissueSample.objects.get_or_create(monkey=mky, tissue_type=tissue_type)
#                         tss.tss_freezer = "Ask OHSU"
#                         tss.tss_location = "Ask OHSU"
#                         tss.tss_sample_quantity = 1
#                         tss.save()
#                         #print mky.mky_name, tissue_name, " was loaded successfully; TSS created: ", created
#             else:
#                 print "Error:  Too many TissueType matches." + tissue_name

# coh13_invntory_filename = '/home/alex/MATRR/cyno13/47.cohort13_tissue_inventory1.csv'
# #load_cohort_10_13_inventory(coh13_invntory_filename)
#
# coh10_invntory_filename = '/home/alex/MATRR/rhesus10/46.cohort10_tissue_inventory.csv'
# load_cohort_10_13_inventory(coh10_invntory_filename)

# with open(coh13_invntory_filename, 'rU') as f:
#         #1. Parse header to get monkeys
#         header = f.readline()
#         monkeys = Monkey.objects.filter(mky_real_id__in=header.split(';')[1:])
#         print monkeys

# print TissueType.objects.filter(tst_tissue_name__iexact='Amygdala (Accessory Basal)')
# print TissueType.objects.filter(tst_tissue_name__iexact='Adrenal (lt, rt)')
# print TissueType.objects.filter(tst_tissue_name__iexact='Area 1, 2, 3')
#print_full(pd.DataFrame(list(TissueType.objects.all().values_list('tst_tissue_name', flat=True))))

# tt = TissueType.objects.filter(tst_tissue_name__iexact='Amygdala (Accessory Basal)')
# print TissueSample.objects.filter(monkey=Monkey.objects.get(mky_real_id=32325), tissue_type=tt)

# print_full(pd.DataFrame(list(TissueSample.objects.filter(monkey__in=Monkey.objects.filter(cohort=c13)).
#     values_list('monkey__mky_name', 'tissue_type__tst_tissue_name', 'tss_sample_quantity'))))

# print Monkey.objects.get(mky_real_id=23582)
#print pd.DataFrame(list(MonkeyEphys.objects.filter(monkey__in=Monkey.objects.filter(cohort=r5)).values_list('mep_cap')))

#print MonkeyEphys._meta.get_all_field_names()

### 10-OCT-2015
# monkeys = Monkey.objects.filter(cohort=Cohort.objects.get(coh_cohort_name='INIA Vervet 2'))
# m42 = monkeys.get(mky_id=10142)
# m43 = monkeys.get(mky_id=10143)
# m44 = monkeys.get(mky_id=10144)
#
# m42.mky_name = 'Jimmy'
# m42.save()
#
# m43.mky_name = 'Blahnik'
# m43.save()
#
# m44.mky_name = 'Georgio'
# m44.save()
#
# print Monkey.objects.filter(cohort=Cohort.objects.get(coh_cohort_name='INIA Vervet 2'))


## LOAD COH13 DATA
#c13monkeys = Monkey.objects.filter(cohort=c13)
#print c13.coh_cohort_name

#c13mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=c13monkeys)
#print c13mtds.count()

# print DrinkingExperiment.objects.filter(cohort=c13)
#
# import datetime
# d = 40555
# print datetime.date(1904, 1, 1) + datetime.timedelta(int(d))
#
# dingus.get_datetime_from_steve(int(d))

#print dt.datetime(1899, 12, 30) + dt.timedelta(days=d + 1462 * 1)

#print dingus.minimalist_xldate_as_datetime(d, 1)

# print ExperimentEvent.objects.filter(monkey__in=c13monkeys).\
#     filter(eev_occurred__gte=dateutil.parser.parse('2014-12-20')).\
#     filter(eev_occurred__lte=dateutil.parser.parse('2014-12-21')).\
#           filter(eev_source_row_number=1394)
#           #values_list('eev_source_row_number')[:10]

#print Cohort.objects.get(coh_cohort_name='INIA Cyno 13')

# print NecropsySummary.objects.all().values_list('monkey__cohort__coh_cohort_name').distinct()
#
# # plt.plot(MonkeyToDrinkingExperiment.objects.filter(monkey__in=Monkey.objects.filter(cohort=r6a))
# #          .order_by('drinking_experiment__dex_date').values_list('mtd_etoh_g_kg', flat=True), 'bo')
# plt.plot(c13mtds.exclude_exceptions().filter(monkey=c13monkeys[0]).order_by('drinking_experiment__dex_date').\
#          values_list('mtd_etoh_g_kg', flat=True), 'b-o')

#print_full(pd.DataFrame(list(TissueType.objects.all().values_list('tst_tissue_name', flat=True))))


## DELETE ALL Coh10 DATA
r10monkeys = Monkey.objects.filter(cohort=r10)
# print r10monkeys
# r10ebt = ExperimentBout.objects.filter(mtd__monkey__in=r10monkeys)
# print r10ebt.count()
# print ExperimentDrink.objects.filter(ebt__in=r10ebt).count()
# print DrinkingExperiment.objects.filter(cohort=r10).count()
# print MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys).count()
# print NecropsySummary.objects.filter(monkey__in=r10monkeys).count()

##  DELETION
# ExperimentDrink.objects.filter(ebt__in=r10ebt).delete()
# print 'drinks deleted'
#
# r10ebt.delete()
# print 'bouts deleted'
#
# DrinkingExperiment.objects.filter(cohort=r10).delete()
# print 'dex deleted'
#
# MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys).delete()
# print "MTDS deleted"

## FIX DEX TYPE
# r10mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys)
# des = r10mtds[0].drinking_experiment
# des.dex_type = 'Open Access'
# des.save()
# print r10mtds[0].drinking_experiment.dex_type

# for mtd in r10mtds:
#     des = mtd.drinking_experiment
#     des.dex_type = 'Open Access'
#     des.save()

# for mtd in r10mtds:
#     print mtd.drinking_experiment.dex_type

### 22 - Oct - 2015
## LOAD SUHAS GENE VACCINE
#mky_ids = pd.DataFrame(list(Monkey.objects.all().order_by('mky_real_id').values_list('mky_id', 'mky_real_id')), columns=['Matrr ID', 'Real ID'])
#print_full(mky_ids)
#mky_ids.to_csv('/home/alex/win-share/matrr_monkeys_id.csv', index=False)
#print Monkey.objects.get(mky_real_id=26077)

# def load_vaccineStudy_data(file_name):
#     """
#     Loads data from csv provided by Ilhem's lab people
#     :param file_name: delimeted by ';'
#                       script strips mostright \n symbol
#
#     Added by Alex Salo on 27 oct 2015
#     """
#     with open(file_name, 'rU') as f:
#         # 1. Parse header to get monkeys
#         monkeys = []
#         header = f.readline().rstrip('\n')
#         for s in header.split(';')[1:]: #get mky_ids
#             m = Monkey.objects.get(mky_real_id = s)
#             monkeys.append(m)
#         print monkeys
#         print 'Loading...it may take a couple of minutes..'
#
#         # 2. Parse and load data
#         read_data = f.readlines()
#         for index, line in enumerate(read_data):
#             if (index % (len(read_data) / 20) == 0):
#                 print str(1.0*index / len(read_data)) + "%"
#             try:
#                 data = line.rstrip('\n').split(';')
#                 ensembl_id = data[0]
#                 for mky, readcount in enumerate(data[1:]):
#                     vac, created = VaccineStudy.objects.get_or_create(monkey=monkeys[mky], ENSEMBLID=ensembl_id, vac_readcount=readcount)
#                     #print vac, created
#             except:
#                 print line
#     print 'Success'
#
# vaccineStudyFileName = '/home/alex/MATRR/suhas/52.alcohol_vaccinestudy_males.csv'
# load_vaccineStudy_data(vaccineStudyFileName)
# #VaccineStudy.objects.all().delete()
# print VaccineStudy.objects.all().count()
# #print VaccineStudy.objects.filter(monkey=Monkey.objects.get(mky_id=10089))


### 26 Oct 2015
## Change Area 12 to 46/12L and Area 12
# tst12 = TissueType.objects.get(tst_tissue_name='Area 12')
# print TissueSample.objects.filter(tissue_type=tst12).count()
#
# tst4612L = TissueType.objects.get(tst_tissue_name='46/12L')
# print TissueSample.objects.filter(tissue_type=tst4612L).count()

## from load inventory:
        # for mky, cell in zip(monkeys, row):
        #     tss, is_new = TissueSample.objects.get_or_create(monkey=mky, tissue_type=tst)
        #     tss.tss_sample_quantity = 1 if bool(cell) else 0
        #     tss.tss_units = Units[2][0]
        #     tss.save()

#tissueSamples4612L = TissueSample.objects.filter(tissue_type=tst4612L)
# print pd.DataFrame(list(tissueSamples4612L.values_list('monkey','tss_freezer',
#                 'tss_location', 'tss_details', 'tss_sample_quantity', 'tss_units', 'user')))

# for ts in tissueSamples4612L:
#     newts = TissueSample.objects.create(monkey=ts.monkey, tissue_type=tst12)
#     newts.tss_sample_quantity = ts.tss_sample_quantity
#     newts.tss_units           = ts.tss_units
#     newts.tss_freezer = "Ask OHSU"
#     newts.tss_location = "Ask OHSU"
#     newts.save()

# allTissueTypes = pd.DataFrame(list(TissueType.objects.all().values_list('category__cat_name', 'tst_tissue_name')),
#                         columns=['Category', 'Matrr Tissue Name'])
# # print_full(allTissueTypes)
# allTissueTypes.to_csv('/home/alex/win-share/matrr_tissue_types_all.csv', index=False, sep=';')

### 30 Oct 2015
# c9_becs = MonkeyBEC.objects.filter(monkey__in=Monkey.objects.filter(cohort=c9))
# c9_becs_values = pd.DataFrame(list(c9_becs.values_list('monkey__mky_id', 'bec_collect_date',
#             'bec_weight',
#             'bec_mg_pct',
#             'bec_vol_etoh', 'bec_gkg_etoh',
#             'bec_daily_gkg_etoh',
#             )),
#             columns=['mky_id', 'date','weight',
#                      'BEC_mg_pct',
#                      'etoh_vol_at_sample_time_ml','etoh_gkg_at_sample_time',
#                      'etoh_gkg_day_total'])
# c9_becs_values.to_csv('/home/alex/win-share/cyno9_becs.csv', index=False, sep=";")


### 3 November 2015
## order by in RUDs
# print ResearchUpdate.objects.all().order_by('req_request__user_id')
# print ResearchUpdate.objects.all().order_by('req_request__req_request_id')


## Prepare req=592 BEC for 9 all
# print Account.objects.get(user_id=222)
# from django.core import files
# data_file = open('/web/www/MATRR/prod/media/data_files/cyno9_becs.csv', 'r') # 'rb' might not be the worst idea, but I'm not specifically sure of the difference)
# wrapped_data_file = files.File(data_file)
# data_file_record = DataFile()
# account = Account.objects.get(user_id=222)
# data_file_record.account = account# (in a Django view, use request.user.account)
# data_file_record.dat_title = "Cyno_9_BECs"
# data_file_record.dat_data_file.save(name="Cyno_9_BECs", content=wrapped_data_file)
# data_file_record.save()


## Absitee req 595
# # populate coh10 fields
# r10mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys)
# # for mtd in r10mtds:
# #     mtd.populate_fields()
#
# r10MTDSdf = pd.DataFrame(list(r10mtds.values_list()))
# print r10MTDSdf



### 9 Nov 2015
## Make new statuses for overdue requests
# rud = Request.objects.get(req_request_id=175).rud_set.order_by('-rud_date')[0]
# # rud.rud_progress = ResearchProgress.Suspended
# # rud.save()
# print Request.objects.get(req_request_id=175).rud_set.order_by('-rud_date')[0].rud_file

## Load DopamineStudy
## Analyze data
#def _cohort_dopamine_study(cohort, tissue_type)

from plotting import cohort_plots
#cohort_plots._plot_dopamine_study_boxplots(c9, 'Nucleus accumbens (Core)')
#plot_dopamine_study_boxplots('caudate')

# gen plots on matrr
# from plotting import plot_tools
# plot_tools.create_dopamine_study_plots()
#
# for img in CohortImage.objects.filter(method__contains="dopamine"):
#     print img


### 11 November 2015
## Analyze BECs

# # 1. Filter work data set
# mky = c2.monkey_set.all()[4]
# print mky
# becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_g_kg__isnull=True)
#
# # 2. Get bec dates and corresponding day before and day after dates lists
# bec_dates = becs.values_list('bec_collect_date', flat=True)
# bec_dates_prev = [date + timedelta(days=-1) for date in bec_dates]
# bec_dates_next = [date + timedelta(days=+1) for date in bec_dates]
#
# # 3. Get corresponding mtds
# mtds_prev = mtds.filter(drinking_experiment__dex_date__in=bec_dates_prev)
# mtds_next = mtds.filter(drinking_experiment__dex_date__in=bec_dates_next)
#
# # 4. Find intersection: we need data for prev day, bec day and next day
# mtds_prev_dates = [date + timedelta(days=+1) for date in mtds_prev.values_list('drinking_experiment__dex_date', flat=True)]
# mtds_next_dates = [date + timedelta(days=-1) for date in mtds_next.values_list('drinking_experiment__dex_date', flat=True)]
# mtds_intersection_dates = set(mtds_prev_dates).intersection(mtds_next_dates)
#
# # 5. Retain becs and mtds within days of intersection
# becs_retained = becs.filter(bec_collect_date__in=mtds_intersection_dates).order_by('bec_collect_date')
# mtds_prev_retained = mtds_prev.filter(drinking_experiment__dex_date__in=[date + timedelta(days=-1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')
# mtds_next_retained = mtds_next.filter(drinking_experiment__dex_date__in=[date + timedelta(days=+1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')
#
# # 6. Assert we have the same number of data daysa
# print 'becs retained: %s' % becs_retained.count()
# print 'etoh on prev day retained: %s' % mtds_prev_retained.count()
# print 'etoh on next day retained: %s' % mtds_next_retained.count()
# assert becs_retained.count() == mtds_prev_retained.count() == mtds_next_retained.count()
#
# # 7. Compile data frame
# bec_df = pd.DataFrame(list(mtds_prev_retained.values_list('mtd_etoh_g_kg')), columns=['etoh_previos_day'])
# bec_df['etoh_at_bec_sample_time'] = list(becs_retained.values_list('bec_gkg_etoh', flat=True))
# bec_df['etoh_next_day'] = list(mtds_next_retained.values_list('mtd_etoh_g_kg', flat=True))
# bec_df['bec'] = list(becs_retained.values_list('bec_mg_pct', flat=True))
# print bec_df
#
# # 8. Scatter plot correlations
# fig, axs = plt.subplots(1, 3, figsize=(20, 10), facecolor='w', edgecolor='k')
# bec_df.plot(kind='scatter', x='etoh_previos_day', y='bec', ax=axs[0])
# bec_df.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', ax=axs[1])
# bec_df.plot(kind='scatter', x='etoh_next_day', y='bec', ax=axs[2])
# plt.tight_layout()
#
#
# # 9. Plot fitted lines and correlation values
# def plot_regression_line_and_corr_text(ax, x, y):
#     fit = np.polyfit(x, y, deg=1)
#     ax.plot(x, fit[0] * x + fit[1], color='red')
#
#     props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
#     text = 'Correlation: %s' % np.round(x.corr(y), 4)
#     ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=14,
#             verticalalignment='top', bbox=props)
#
# plot_regression_line_and_corr_text(axs[0], bec_df.etoh_previos_day, bec_df.bec)
# plot_regression_line_and_corr_text(axs[1], bec_df.etoh_at_bec_sample_time, bec_df.bec)
# plot_regression_line_and_corr_text(axs[2], bec_df.etoh_next_day, bec_df.bec)


### 12 November 2015
# BECs for all animals
def mky_bec_corr(mky):
    # 1. Filter work data set
    becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_g_kg__isnull=True)

    # 2. Get bec dates and corresponding day before and day after dates lists
    bec_dates = becs.values_list('bec_collect_date', flat=True)
    bec_dates_prev = [date + timedelta(days=-1) for date in bec_dates]
    bec_dates_next = [date + timedelta(days=+1) for date in bec_dates]

    # 3. Get corresponding mtds
    mtds_prev = mtds.filter(drinking_experiment__dex_date__in=bec_dates_prev)
    mtds_next = mtds.filter(drinking_experiment__dex_date__in=bec_dates_next)

    # 4. Find intersection: we need data for prev day, bec day and next day
    mtds_prev_dates = [date + timedelta(days=+1) for date in mtds_prev.values_list('drinking_experiment__dex_date', flat=True)]
    mtds_next_dates = [date + timedelta(days=-1) for date in mtds_next.values_list('drinking_experiment__dex_date', flat=True)]
    mtds_intersection_dates = set(mtds_prev_dates).intersection(mtds_next_dates)

    # 5. Retain becs and mtds within days of intersection
    becs_retained = becs.filter(bec_collect_date__in=mtds_intersection_dates).order_by('bec_collect_date')
    mtds_prev_retained = mtds_prev.filter(drinking_experiment__dex_date__in=[date + timedelta(days=-1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')
    mtds_next_retained = mtds_next.filter(drinking_experiment__dex_date__in=[date + timedelta(days=+1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')

    # 6. Assert we have the same number of data daysa
    print 'becs retained: %s' % becs_retained.count()
    print 'etoh on prev day retained: %s' % mtds_prev_retained.count()
    print 'etoh on next day retained: %s' % mtds_next_retained.count()
    assert becs_retained.count() == mtds_prev_retained.count() == mtds_next_retained.count()

    # 7. Compile data frame
    if mtds_prev_retained.count() == 0:
        return pd.DataFrame() # empty to be ignored

    bec_df = pd.DataFrame(list(mtds_prev_retained.values_list('mtd_etoh_g_kg')), columns=['etoh_previos_day'])
    bec_df['etoh_at_bec_sample_time'] = list(becs_retained.values_list('bec_gkg_etoh', flat=True))
    bec_df['etoh_next_day'] = list(mtds_next_retained.values_list('mtd_etoh_g_kg', flat=True))
    bec_df['bec'] = list(becs_retained.values_list('bec_mg_pct', flat=True))
    bec_df['dc'] = list(mtds_next_retained.values_list('monkey__mky_drinking_category', flat=True))
    return bec_df


# 9. Plot fitted lines and correlation values
def plot_regression_line_and_corr_text(ax, x, y):
    fit = np.polyfit(x, y, deg=1)
    ax.plot(x, fit[0] * x + fit[1], color='red')

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    text = 'Correlation: %s' % np.round(x.corr(y), 4)
    ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)


def plot_bec_correlation(bec_df):
    fig, axs = plt.subplots(1, 3, figsize=(15, 8), facecolor='w', edgecolor='k')
    bec_df.plot(kind='scatter', x='etoh_previos_day', y='bec', ax=axs[0])
    bec_df.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', ax=axs[1])
    bec_df.plot(kind='scatter', x='etoh_next_day', y='bec', ax=axs[2])
    plt.tight_layout()

    plot_regression_line_and_corr_text(axs[0], bec_df.etoh_previos_day, bec_df.bec)
    plot_regression_line_and_corr_text(axs[1], bec_df.etoh_at_bec_sample_time, bec_df.bec)
    plot_regression_line_and_corr_text(axs[2], bec_df.etoh_next_day, bec_df.bec)


def collect_cohort_monkeys_bec(cohort):
    monkeys = Monkey.objects.filter(mky_id__in=MonkeyBEC.objects.all().values_list('monkey__mky_id', flat=True).distinct())
    monkeys = Monkey.objects.filter(mky_id__in=cohort.monkey_set.filter(mky_id__in=monkeys))
    bec_df = mky_bec_corr(monkeys[0])
    for mky in monkeys[1:]:
        print mky
        new_df = mky_bec_corr(mky)
        if len(new_df) > 0:
            bec_df = bec_df.append(new_df)
    print "Total BECs: %s" % len(bec_df)
    return bec_df

def collect_all_monkeys_bec():
    monkeys = Monkey.objects.filter(mky_id__in=MonkeyBEC.objects.all().values_list('monkey__mky_id', flat=True).distinct())
    bec_df = mky_bec_corr(monkeys[0])
    for mky in monkeys[1:]:
        print mky
        new_df = mky_bec_corr(mky)
        if len(new_df) > 0:
            bec_df = bec_df.append(new_df)
    print "Total BECs: %s" % len(bec_df)
    return bec_df


def plot_bec_correlation_by_dc(bec_df, font_size=12):
    fig, axs = plt.subplots(4, 3, figsize=(20, 10), facecolor='w', edgecolor='k')
    axs = axs.ravel()
    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        df_dc = bec_df[bec_df.dc == dc]

        df_dc.plot(kind='scatter', x='etoh_previos_day', y='bec', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 0])
        df_dc.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 1])
        df_dc.plot(kind='scatter', x='etoh_next_day', y='bec', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 2])

        plot_regression_line_and_corr_text(axs[i*3 + 0], df_dc.etoh_previos_day, df_dc.bec)
        plot_regression_line_and_corr_text(axs[i*3 + 1], df_dc.etoh_at_bec_sample_time, df_dc.bec)
        plot_regression_line_and_corr_text(axs[i*3 + 2], df_dc.etoh_next_day, df_dc.bec)

    # fine tune plot look'n'feel
    plt.tight_layout()

    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
    plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)

    plt.setp([axs[i].get_xticklabels() for i in [9, 10, 11]], visible=True)
    plt.setp([axs[i].get_yticklabels() for i in [0, 3, 6, 9]], visible=True)

    [ax.set_ylabel('') for ax in axs]
    axs[0].set_ylabel('LD', fontsize=font_size)
    axs[3].set_ylabel('BD', fontsize=font_size)
    axs[6].set_ylabel('HD', fontsize=font_size)
    axs[9].set_ylabel('VHD', fontsize=font_size)

    fig.text(0.5, 0.94, 'BEC correlation: EtOH the day before, day of and day after', ha='center', fontsize=font_size+4)
    fig.text(0.005, 0.5, 'BEC', va='center', rotation='vertical', fontsize=font_size+4)
    fig.subplots_adjust(top=0.93)


GEN_BEC_DF = False
if GEN_BEC_DF:
    df_bec_all = collect_all_monkeys_bec()
    df_bec_all.save('bec_df_all.plk')
else:
    df_bec_all = pd.read_pickle('bec_df_all.plk')

# plot_bec_correlation_by_dc(df_bec_all)


# fill the corr table
def compile_bec_correlation_table(bec_df):
    cors = list()
    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        f = bec_df[bec_df.dc == dc]
        row = [np.round(f.etoh_previos_day.corr(f.bec), 4),
               np.round(f.etoh_at_bec_sample_time.corr(f.bec), 4),
               np.round(f.etoh_next_day.corr(f.bec), 4)]
        cors.append(row)
    return cors

# bec_all_correlations = compile_bec_correlation_table(df_bec_all)
# for row in bec_all_correlations:
#     print "%.2f "*len(row) % tuple(row)


# def test_plot_bec_correlation(bec_df):
#     bec_df.plot(kind='scatter', x='etoh_previos_day', y='bec', subplots=True, layout=(1, 3))
#     bec_df.plot(kind='scatter', x='etoh_at_bec_sample_time', subplots=True, layout=(1, 3))
#     bec_df.plot(kind='scatter', x='etoh_next_day', y='bec', subplots=True, layout=(1, 3))
#     plt.tight_layout()
# df_coh = pd.read_pickle('bec_coh_df.plk')
# test_plot_bec_correlation(df_coh)

# mky = r6a.monkey_set.all()[1]
# print mky
# mky_bec_corr(mky)

# cohort_bec_correlation(r6a)


## ANDREW CURVES
#def plot_andrews_curves():
    GEN_COH_DF = False
    if GEN_COH_DF:
        df_coh = collect_cohort_monkeys_bec(r6b)
        df_coh.save('bec_coh_df.plk')
    else:
        df_coh = pd.read_pickle('bec_coh_df.plk')

    from pandas.tools.plotting import andrews_curves, parallel_coordinates
    plt.figure(figsize=(12, 8), facecolor='w', edgecolor='k')
    andrews_curves(df_coh, 'dc')
    plt.tight_layout()

    # df_coh = normalize_float_cols(df_coh)
    df_coh = df_coh.drop('bec', axis=1)
    plt.figure(figsize=(12, 8), facecolor='w', edgecolor='k')
    parallel_coordinates(df_coh, 'dc')
    plt.tight_layout()
# plot_andrews_curves()

# gen plots on matrr
#from plotting import plot_tools
#plot_tools.create_bec_correlation_plots(True, True)


### 13 November 2015
# load necropsy summary # then reload when with BEC
from utils.database import load
#load.load_necropsy_summary('/home/alex/MATRR/coh10_full/Coh10_std_Dataset_partialNoBEC_20151014.txt')
#print pd.DataFrame(list(NecropsySummary.objects.filter(monkey=r10monkeys[1]).values_list()))

# load.load_necropsy_summary('/home/alex/MATRR/coh13_full/Coh13_std_Dataset_partialNoBEC_20151014.txt')
# print pd.DataFrame(list(NecropsySummary.objects.filter(monkey=c13.monkey_set.all()[1]).values_list()))

# # repopulate BEC
# for bec in MonkeyBEC.objects.filter(monkey__in=r10monkeys):
#     bec.populate_fields()

# recalculate DC in coh10:
# for m in r10monkeys:nano
#     m.populate_drinking_category()
#     print m

# # Populate fields in MTDS
# for m in r10monkeys:
#     print m
#     mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m)
#     for mtd in mtds:
#         mtd.populate_fields()

from utils.database import dump
#dump.dump_standard_cohort_data(r10.coh_cohort_id)


### Get 12 mo DC for Cohort 10:
# def arbitrary_drinking_category(cohort, months=12):
#     from matrr.utils.gadgets import identify_drinking_category
#     start_date = CohortEvent.objects.filter(cohort=cohort).filter(event=37)[0].cev_date
#     end_date = CohortEvent.objects.filter(cohort=cohort).filter(event=42)[0].cev_date
#     print "Start: %s - End: %s" % (start_date, end_date)
#     for mky in cohort.monkey_set.all():
#         oa_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=mky).\
#             filter(drinking_experiment__dex_date__gte=start_date).filter(drinking_experiment__dex_date__lte=end_date).\
#             order_by('drinking_experiment__dex_date')
#         oa_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=mky).\
#             filter(bec_collect_date__gte=start_date).filter(bec_collect_date__lte=end_date).\
#             order_by('bec_collect_date')
#         if oa_mtds.count() and oa_becs.count():
#             mky_drinking_category = identify_drinking_category(oa_mtds, oa_becs)
#         else:
#             mky_drinking_category = 'NA'
#
#         mtds_dates = list(oa_mtds.values_list('drinking_experiment__dex_date', flat=True))
#         becs_dates = list(oa_becs.values_list('bec_collect_date', flat=True))
#         print "Assert dates MTDS: Start: %s - End: %s; Assert dates BECs: Start: %s - End: %s;\n12 month drinking category: %s, Monkey: %s" % \
#               (mtds_dates[0], mtds_dates[-1], becs_dates[0], becs_dates[-1], mky_drinking_category, mky)
#
# arbitrary_drinking_category(r10)
# for bec in MonkeyBEC.objects.filter(monkey__in=r10monkeys):
#     bec.populate_fields()

#print MonkeyBEC.objects.OA().filter(monkey__in=r10monkeys).count()
#print MonkeyBEC.objects.filter(monkey__in=c13.monkey_set.all()).count()


### Prepare data requests
# from_date = dingus.get_datetime_from_steve('03/30/2015')
# to_date = dingus.get_datetime_from_steve('07/12/2015')
# mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=r10monkeys).\
#     filter(drinking_experiment__dex_date__gte=from_date).\
#     filter(drinking_experiment__dex_date__lte=to_date)
# #Date	Monk #	Etoh Intake	Veh intake	Etoh %	Etoh g/kg	Tot Pellet
# # Etoh Bout	Etoh Drink/bout	Veh Bout	Veh Drink/bout	Weight	Etoh Conc.
# # Etoh Mean Drink Length	Etoh Median IDI	Etoh Mean Drink Vol	Etoh Mean
# # Bout Length	Etoh Median IBI	Etoh Mean Bout Vol	Etoh St.1	Etoh St.2	Etoh St.3	Veh St.2	Veh St.3
# # 	Pellets St.1	Pellets St.3	Length St.1	Length St.2	Length St.3	Vol. 1st Bout	% Etoh in First Bout
# #  Drinks 1st Bout	Mean Drink Vol 1st Bout	FI w/o Drinking St.1	% Of FI with Drinking St.1
# # Latency to 1st Drink	Exp. Etoh%	St. 1 IOC Avg	Date	Monk #	Max Bout #	Max Bout Start	Max Bout End
# # Max Bout Length	Max Bout Volume	Max Bout Volume as % of Total Etoh
#
# model_fields = [
#     'monkey__mky_id', 'drinking_experiment__dex_date',
#     'mtd_etoh_intake', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_weight'
# ]

# df = pd.DataFrame(list(mtds.values_list()))
# print df.omit
# print plt.get_backend()
# print matplotlib.rcsetup.all_backends

# plt.plot([1,2,3])


### 18 November 2015
### Shippint Manifest


plt.show()
