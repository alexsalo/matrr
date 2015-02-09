import sys, os
sys.path.append('~/pycharm/ve1/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.models import Monkey
from matrr.plotting import monkey_plots as mkplot
import matplotlib
matplotlib.use('TkAgg')
import pylab

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


###LOAD MDE DATA sHEET 1
from matrr.utils.database import dingus
cohort_vervet_1 = Cohort.objects.get(coh_cohort_name="INIA Vervet 1")
print cohort_vervet_1
file_name = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet1_daily_22h_etoh.csv'
with open(file_name, 'r') as f:
    #1. Parse header to get monkeys
    monkeys = []
    header = f.readline()
    header_split = header.split(',')
    for s in header_split:
        s_split = s.split(' ')
        for s2 in s_split:
            if s2.isdigit():
                m = Monkey.objects.get(mky_real_id = s2)
                monkeys.append(m)
    #2. Parse Data
    read_data = f.readlines()
    cnt = 0
    for line_number, line in enumerate(read_data):
        #print line_number
        #print line
        cnt += 1
        print cnt
        # if cnt > 40:
        #       break
        data = line.split(',')

        #2.1 Create Drinking Experiments
        dex_date = dingus.get_datetime_from_steve(data[1])
        des = DrinkingExperiment.objects.filter(dex_type="Open Access", dex_date = dex_date,
                                                cohort = cohort_vervet_1)
        if des.count() == 0:
            de = DrinkingExperiment(dex_type="Open Access", dex_date = dex_date,
                                                cohort = cohort_vervet_1)
        elif des.count() == 1:
            de = des[0]
        elif des.count() > 1:
            print "too many drinking experiments!"
        #save notes if any
        if len(data[7]) > 2:
            de.dex_notes = data[7]
        de.save()

        #2.2 Create MonkeyToDrinkingExperiment
        pos = 2
        for monkey in monkeys:
            mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment = de, monkey = monkey)
            if mtds.count() != 0:
                mtd = mtds[0]
            else:
                mtd = MonkeyToDrinkingExperiment()
                mtd.monkey = monkey
                mtd.drinking_experiment = de
                mtd.mtd_total_pellets = 0

            #print mtd
            if data[pos]:
                mtd.mtd_etoh_g_kg = data[pos]
            else:
                mtd.mtd_etoh_g_kg = None
                mtd.mtd_total_pellets = 0
            #print mtd

            mtd.save()
            pos +=1



#print DrinkingExperiment.objects.all()[1]
    #print read_data
