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

import datetime
import scipy.stats as stats
from patsy import dmatrices
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from sklearn import cross_validation, svm, metrics
from sklearn.cross_validation import KFold
from sklearn.ensemble  import RandomForestClassifier, GradientBoostingClassifier, BaggingClassifier
from sklearn.ensemble.partial_dependence import plot_partial_dependence
from sklearn.cross_validation import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
import lwr
import mimic_alpha

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
dc_colors_dash = {
    'LD' : 'g-',
    'BD' : 'b-',
    'HD' : 'y-',
    'VHD' : 'r-',
    None : 'k-o'
}

pre_post_luni_phase = {
    0 : 'c',
    1 : 'm'
}

dc_weights = {
    'LD' : 0.32,
    'BD' : 0.2,
    'HD' : 0.18,
    'VHD' : 0.30
}

feature_names = {
        'mtd_seconds_to_stageone': "Seconds to reach day's EtOH allotment",
        'mtd_latency_1st_drink': 'Latency to first EtOH drink (seconds)',
        'mtd_etoh_bout': 'Number of EtOH bouts',
        'mtd_etoh_drink_bout': 'Average number of EtOH drinks per bout',
        'mtd_veh_bout': 'Number of H2O bouts',
        'mtd_veh_drink_bout': 'Average number of H2O drinks per bout',
        'mtd_etoh_mean_drink_length': 'Average EtOH drink length (seconds)',
        'mtd_etoh_median_idi': 'Median EtOH inter-drink interval (seconds)',
        'mtd_etoh_mean_drink_vol' : 'Average EtOH drink volume (ml)',
        'mtd_etoh_mean_bout_length': 'Average EtOH bout length (seconds)',
        'mtd_pct_etoh_in_1st_bout': '% of days EtOH consumed in first bout',
        'mtd_drinks_1st_bout': 'Number of EtOH drinks in first bout',
        'mtd_max_bout': 'Sequence number of max bout',
        'mtd_max_bout_length': 'Max bout length (seconds)',
        'mtd_pct_max_bout_vol_total_etoh': 'Max bout volume as % of total EtOH that day',
        'etoh_during_ind': 'EtOH during first 10 minutes as a % of the daily allotment',
        'sex': 'Gender',
        'intox' : 'Age of first EtOH intoxication',
        'necropsy': 'Age (Necropsy)',
        }

def remove_none(nparray):
    return [x for x in nparray if x != None]
def remove_outliers(nparray, m=1.5):
    return nparray[abs(nparray - np.mean(nparray)) < m * np.std(nparray)]
def plotMense(df, ax=plt):
    [ax.axvspan(date, date + timedelta(days=4), color='r', alpha=0.3) for date in list(df.date[df.mense])]
def normalize(df):
    return (df- df.mean()) / (df.std())
def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

def substract_lists(a, b, operator='diff'):
    if operator=='diff':
        return [a_i - b_i for a_i, b_i in zip(a, b)]
    if operator=='sum':
        return [a_i + b_i for a_i, b_i in zip(a, b)]

def cv_classfier(X, y, clf, fold_size, start_text):
    scores = cross_validation.cross_val_score(clf, X, y, cv=fold_size)
    print scores
    print start_text + ", Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std())
    print str(clf)
    print '---------------------------------------------\n'
    return scores.mean()

def showCM(cm, plot=True, BER=False):
    print(cm)

    #Accuracy
    trues = sum(cm[i][i] for i in xrange(0, len(cm)))
    accuracy = trues / (cm.sum() * 1.0)
    print ('Accuracy: %s' % accuracy)

    #Balanced Error Rate
    if BER:
        k = len(cm)
        error_rate = 0
        for i in xrange(0, k):
            sumrow = 0
            for j in xrange(0, k):
                sumrow += cm[i][j]
            error_rate += 1.0 * cm[i][i] / sumrow
        balanced_error_rate = 1 - error_rate / k
        print ('Balanced Error Rate: %s' % balanced_error_rate)
        print '--> where BER = 1 - 1/k * sum_i (m[i][i] / sum_j (m[i][j]))'

    if plot:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ms = ax.matshow(cm)
        ax.set_title('Confusion matrix')
        plt.colorbar(ms)
        ax.set_ylabel('True label')
        ax.set_xlabel('Predicted label')
        ax.set_xticklabels(['', 'LD', 'BD', 'HD', 'VHD'])
        ax.set_yticklabels(['', 'LD', 'BD', 'HD', 'VHD'])
        plt.tight_layout()
        pylab.show()