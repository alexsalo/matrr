__author__ = 'alex'
import sys, os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *

import matplotlib
import matplotlib.pyplot as plt
import pylab
matplotlib.use('TkAgg')

import numpy as np
import pandas as pd
import lwr

import django
django.setup()

anomalies_mtds_ids = [10069,10070,10078,10079,10080,10081]
mense_monkeys_ids = [10077,10072,10075,10073,10074,10187,10188,10186]
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