__author__ = 'alex'
import sys, os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.utils.database import dingus, create

import matplotlib
matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/Matrr'
import matplotlib.pyplot as plt
import pylab
matplotlib.use('TkAgg')

import scipy.stats as stats
from patsy import dmatrices
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from sklearn import cross_validation
from sklearn.cross_validation import KFold
from sklearn import svm
from sklearn.ensemble  import RandomForestClassifier, GradientBoostingClassifier, BaggingClassifier
from sklearn.ensemble.partial_dependence import plot_partial_dependence
from sklearn.cross_validation import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
import lwr

import django
django.setup()

anomalies_mtds_ids = [10069,10070,10078,10079,10080,10081]
mense_monkeys_ids = [10077,10072,10075,10073,10074,10187,10188,10186]
dc_colors = {
    'LD' : 'g',
    'BD' : 'b',
    'HD' : 'y',
    'VHD' : 'r'
}
dc_colors_o = {
    'LD' : 'go',
    'BD' : 'bo',
    'HD' : 'yo',
    'VHD' : 'ro',
    None : 'ko'
}
dc_colors_ol = {
    'LD' : 'g-o',
    'BD' : 'b-o',
    'HD' : 'y-o',
    'VHD' : 'r-o',
    None : 'k-o'
}

pre_post_luni_phase = {
    0 : 'c',
    1 : 'm'
}

dc_weights = {
    'LD' : 0.33,
    'BD' : 0.16,
    'HD' : 0.19,
    'VHD' : 0.31
}

def remove_none(nparray):
    return [x for x in nparray if x != None]
def remove_outliers(nparray, m=1.5):
    return nparray[abs(nparray - np.mean(nparray)) < m * np.std(nparray)]
def plotMense(df, ax=plt):
    [ax.axvspan(date, date + timedelta(days=4), color='r', alpha=0.3) for date in list(df.date[df.mense])]
def normalize(df):
    return (df- df.mean()) / (df.std())