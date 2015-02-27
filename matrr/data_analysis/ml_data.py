__author__ = 'alex'
import sys, os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *

import matplotlib
import pylab
matplotlib.use('TkAgg')

import numpy as np
import lwr

import django
django.setup()

anomalies_mtds_ids = [10069,10070,10078,10079,10080,10081]
dc_colors_o = {
    'LD' : 'go',
    'BD' : 'bo',
    'HD' : 'yo',
    'VHD' : 'ro'
}
dc_colors_ol = {
    'LD' : 'g-o',
    'BD' : 'b-o',
    'HD' : 'y-o',
    'VHD' : 'r-o'
}
def remove_none(nparray):
    return [x for x in nparray if x != None]
def remove_outliers(nparray, m=1.5):
    return nparray[abs(nparray - np.mean(nparray)) < m * np.std(nparray)]

features_names_perstage = [
    'mtd_seconds_to_stageone', #Seconds it took for monkey to reach day's ethanol allotment
    'mtd_latency_1st_drink', #Time from session start to first etOH consumption
    'mtd_etoh_bout', #Total etOH bouts (less than 300 seconds between consumption of etOH)
    'mtd_etoh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of etOH) per etOH bout
    'mtd_veh_bout', #Total H20 bouts (less than 300 seconds between consumption of H20)
    'mtd_veh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of H20) per H20 bout
    'mtd_etoh_mean_drink_length', #Mean length for ethanol drinks (less than 5 seconds between consumption of etOH is a continuous drink
    'mtd_etoh_median_idi', #Median time between drinks (always at least 5 seconds because 5 seconds between consumption defines a new drink
    'mtd_etoh_mean_drink_vol', #Mean volume of etOH drinks
    'mtd_etoh_mean_bout_length'
    'mtd_etoh_media_ibi', #Median inter-bout interval (always at least 300 seconds, because 300 seconds between consumption defines a new bout)
    'mtd_pct_etoh_in_1st_bout', #Percentage of the days total etOH consumed in the first bout
    'mtd_drinks_1st_bout', #Number of drinks in the first bout
    'mtd_max_bout', #Number of the bout with maximum ethanol consumption
    'mtd_max_bout_length', #Length of maximum bout (bout with largest ethanol consumption)
    'mtd_pct_max_bout_vol_total_etoh', #Maximum bout volume as a percentage of total ethanol consumed that day
    #derive somethin by perhour drinks - mornin drinking?
    #maybe get medians and register related change? so instead of 3 features we have 2: delta_1, delta_2?
    ]


pylab.show()