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
#print Monkey.objects.all().filter(mky_drinking_category = "HD")
#m = Monkey.objects.get(mky_id=10006)
#ms = Monkey.objects.all()[3:6]
#print ms



#mkplot.monkey_necropsy_avg_22hr_g_per_kg(m)
#necropsy image do force render
#mkplot.monkey_necropsy_etoh_4pct(m)
#pylab.show()
from matrr.utils.database import dump
dump.dump_data_req_request_425_thru_431()

#CohortProteinImage.objects.all().delete()
#CohortImage.objects.all().get(pk=2699).save(force_render = True)
#http://127.0.0.1:8080/media/matrr_images/INIA_Cyno_1.Total_Ethanol_Intake_ml.2699-thumb_fd1XXi2.jpg

#print MonkeyImage.objects.filter(method__contains = "necropsy").count()
#for image in MonkeyImage.objects.filter(method__contains = "necropsy"):
#    image.save(force_render = True)
