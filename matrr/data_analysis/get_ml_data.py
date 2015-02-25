__author__ = 'alex'
import sys, os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.models import Monkey
from matrr.plotting import monkey_plots as mkplot
import matplotlib
matplotlib.use('TkAgg')
import pylab
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from patsy import dmatrices
from sklearn.linear_model import LogisticRegression, RandomizedLogisticRegression
from sklearn.cross_validation import train_test_split
from sklearn import metrics
from sklearn.cross_validation import cross_val_score
import lwr

import django
django.setup()

anomalies_mtds_ids = [10069,10070,10078,10079,10080,10081]

mycolors = {
    'LD' : 'go',
    'BD' : 'bo',
    'HD' : 'yo',
    'VHD' : 'ro'
}
mycolors2 = {
    'LD' : 'g-o',
    'BD' : 'b-o',
    'HD' : 'y-o',
    'VHD' : 'r-o'
}

###Machine Learning###

##Define Cohorts and Monkeys##
def define_monkeys():
    cohort_names = ["INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 6a", "INIA Rhesus 7b",
        "INIA Rhesus 6b", "INIA Rhesus 7a"]
    ml_cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
    ml_monkeys = Monkey.objects.filter(cohort__in = ml_cohorts).exclude(mky_drinking_category = None)
    return ml_monkeys

##Prepare Feature Data (Induction)##
def median_drinking_latency_for_monkeys(monkeys, mtds_all):
    meds = pd.DataFrame(columns=["mky_id", "med"])
    cnt = 0
    for m in monkeys:
        mtds = mtds_all.filter(monkey = m)
        count = mtds.count()
        if count > 100:
            print m.mky_id, count
        med = mtds.values_list('mtd_latency_1st_drink', flat=True).order_by('mtd_latency_1st_drink')[int(round(count/2))]
        meds.loc[cnt] = [m.mky_id, med]
        cnt += 1
    return meds

def median_value_per_stage_for_monkeys(monkeys, mtds_all, index, value_name='mtd_seconds_to_stageone', GKG_DELTA_EPSILON=0.4):
    medians = pd.DataFrame(columns=[value_name+"_1", value_name+"_2", value_name+"_3", value_name+"_total"], index=index)
    cnt = 0
    for m in monkeys:
        mtds = mtds_all.filter(monkey = m).order_by('drinking_experiment__dex_date')
        values_df = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', value_name)))
        values_df.columns = ['etoh', 'value']

        # split on 3 parts by etoh_gkg
        tp0, tp1, tp2 = 1, 1, 1

        if m.mky_id in anomalies_mtds_ids:
            tp0, tp1, tp2 = 55, 84, 115
        else:
            for i in range(20, values_df.etoh.size - 20):
                if values_df.etoh[i] > (values_df.etoh[i-1] + GKG_DELTA_EPSILON):
                    if tp1 == 1:
                        tp1 = i-1
                    else:
                        tp2 = i-1

        if values_df.value[tp0:tp1].median() < 0:
            total_medain = values_df.value.median()
            medians.ix[m.mky_id] = [total_medain, total_medain, total_medain, total_medain]
        else:
            medians.ix[m.mky_id] = [values_df.value[tp0:tp1].median(),
                                values_df.value[tp1:tp2].median(),
                                values_df.value[tp2:].median(),
                                values_df.value[tp0:].median()]
        cnt += 1
    return medians

def reject_outliers(data, m=1.5):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

def avg_drinking_latency_for_monkeys(monkeys, mtds_all, index):
    avgs = pd.DataFrame(columns=["avg"], index=index)
    for m in monkeys:
        mtds = mtds_all.filter(monkey = m)
        avg = reject_outliers(np.array(mtds.values_list('mtd_latency_1st_drink', flat=True))).mean()
        avgs.ix[m.mky_id] = avg
    return avgs


def prepare_features(ml_monkeys):
    LAPLACE_BALANCE = 900 #see test_speed
    SPEED_TRESHOLD = 2.4 #see test_speed
    features = ["id", "sex", "age_intox", "DC"]
    data = ml_monkeys.values_list("mky_id", "mky_gender", "mky_age_at_intox", "mky_drinking_category")
    df = pd.DataFrame(list(data), columns=features)
    df = df.set_index("id")
    df['sex'] = (df.sex == 'M').astype(int)
    #print df
    df = df.sort_index()

    mtds_all = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=ml_monkeys)

    #med speed to drink
    median_speed_by_stage = median_value_per_stage_for_monkeys(ml_monkeys, mtds_all, df.index, 'mtd_seconds_to_stageone')
    df['speed_1'] = median_speed_by_stage.mtd_seconds_to_stageone_1
    df['speed_2'] = median_speed_by_stage.mtd_seconds_to_stageone_2
    df['speed_3'] = median_speed_by_stage.mtd_seconds_to_stageone_3
    df['speed_total'] = median_speed_by_stage.mtd_seconds_to_stageone_total
    df['speed_changed'] = ((df.speed_3 + LAPLACE_BALANCE) / (df.speed_1 + LAPLACE_BALANCE) > SPEED_TRESHOLD).astype(int)

    #med latency to drink
    median_latency_by_stage = median_value_per_stage_for_monkeys(ml_monkeys, mtds_all, df.index, 'mtd_latency_1st_drink')
    df['latency_1'] = median_latency_by_stage.mtd_latency_1st_drink_1
    df['latency_2'] = median_latency_by_stage.mtd_latency_1st_drink_2
    df['latency_3'] = median_latency_by_stage.mtd_latency_1st_drink_3
    df['latency_total'] = median_latency_by_stage.mtd_latency_1st_drink_total
    df['latency_increased'] = (df.latency_3 > df.latency_1).astype(int)

    #avg latency to drink - still outliers?
    avg_mtds = avg_drinking_latency_for_monkeys(ml_monkeys, mtds_all, df.index)
    df['avg_latency'] = avg_mtds["avg"]
    def plot_latency_outliers():
        m = Monkey.objects.get(mky_id = 10070)
        data = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date').\
                        values_list('mtd_latency_1st_drink', flat=True)
        data = np.array(data)
        fig, axs = plt.subplots(2,1,facecolor='w', edgecolor='k')
        axs[0].plot(data, 'ro')
        axs[0].set_title(str(m.mky_id) + 'latency to first drink')
        print np.mean(data)
        data = reject_outliers(data)
        axs[1].plot(data, 'go')
        axs[1].set_title(str(m.mky_id) + 'latency to first drink - no outliers, factor=1.5')
        fig.subplots_adjust(hspace=0.2)
        print np.mean(data)

    median_etoh_bouts_by_stage = median_value_per_stage_for_monkeys(ml_monkeys, mtds_all, df.index, 'mtd_etoh_bout')
    print median_etoh_bouts_by_stage

    return df

#####LOOK here def
from matrr.utils import plotting_beta
#plotting_beta.cohorts_daytime_volbouts_bargraph()
#plotting_beta.cohort_etoh_cumsum_nofood(ml_cohorts[1], plt.subplot())

def plot_monkeys_latency(monkeys):
    count = monkeys.count()
    print count
    fig, axs = plt.subplots(count,1, figsize=(10, 30), facecolor='w', edgecolor='k')
    fig.subplots_adjust(hspace = .5, wspace=.001)
    axs = axs.ravel()
    i = 0
    for m in monkeys:
        data = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m).order_by('drinking_experiment__dex_date').\
                    values_list('mtd_latency_1st_drink', 'drinking_experiment__dex_date')
        df = pd.DataFrame(list(data), columns=['latency', 'date'])
        df = df.set_index("date")

        # plt.figure(1)
        # plt.plot(xrange(len(df.index)), df.latency.cumsum(), 'g-', xrange(len(df2.index)), df2.latency.cumsum(), 'r-',)

        x, y, xpred, ypred = lwr.wls(xrange(len(df.index)), df.latency, 'go')
        axs[i].plot(x, y, 'ro', xpred, ypred, 'b-')
        axs[i].axis([0, 90, 0, 50])
        axs[i].set_autoscale_on(False)
        axs[i].set_title(str(m.mky_id))

        i +=1
    # Fine-tune figure; make subplots close to each other and hide x ticks for all but bottom plot.
    fig.subplots_adjust(hspace=0)
    plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)

# m1 = Monkey.objects.get(mky_id = 10086)
# m2 = Monkey.objects.get(mky_id = 10080)
#data = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m1).order_by('drinking_experiment__dex_date').\
#                 values_list('mtd_latency_1st_drink', 'drinking_experiment__dex_date')
# df = pd.DataFrame(list(data), columns=['latency', 'date'])
# df = df.set_index("date")
# plt.plot(df, 'ro')
#plot_monkeys_latency(ml_monkeys.filter(mky_drinking_category='LD')[0:5])

def logistic(features, foldTwo=True, Randomized=False):
    X = features[["sex", "age_intox", 'speed_1', 'speed_2', 'speed_3', 'speed_changed']]
    #X = features[["sex"]]
    #X_norm = (X - X.min()) / (X.max() - X.min())
    y = features['DC']
    model = LogisticRegression()

    if foldTwo:
        y.ix[y == 'HD'] = 'VHD'
        y.ix[y == 'BD'] = 'LD'
        y = (y == 'VHD').astype(int)

    if Randomized:
        if foldTwo != True:
            y.ix[y == 'LD'] = 0
            y.ix[y == 'BD'] = 1
            y.ix[y == 'HD'] = 2
            y.ix[y == 'VHD'] = 3
            y = y.astype(int)
        model = RandomizedLogisticRegression()

    print X
    print y

    model = model.fit(X, y)
    #print model.raw_coef_
    scores = cross_val_score(LogisticRegression(), X, y, scoring='accuracy', cv=12)
    print scores
    print scores.mean()
    if foldTwo:
        print 'base rate: %s ' % round((y[y == 1].size / float(y.size)), 2)
    else:
        print 'base rate:'
        print features.DC.value_counts()/len(features.index)
def get_features(generate=True):
    if generate:
        ml_monkeys = define_monkeys()
        features = prepare_features(ml_monkeys)
        features.save('features.pkl')
    else:
        features = pd.read_pickle('features.pkl')
    return features

features = get_features(True)
print features
#logistic(features, False, False)

def test_latency_change():
    print features[['latency_increased', 'DC']]
    features.ix[(features.DC == 'HD'), 'DC'] = 'VHD'
    features.ix[(features.DC == 'BD'), 'DC'] = 'LD'
    erorr_rate = round(len(features.ix[features.DC=='VHD'].ix[features.latency_increased==1, 'sex']) / float(len(features.ix[features.DC=='VHD', 'sex'])), 2)
    accuracy = round(len(features.ix[features.DC=='LD'].ix[features.latency_increased==1, 'sex']) / float(len(features.ix[features.DC=='LD', 'sex'])), 2)
    err_acc = accuracy - erorr_rate
    print erorr_rate, '    ', accuracy, '    ', err_acc

def test_speed_change():
    features.ix[(features.DC == 'HD'), 'DC'] = 'VHD'
    features.ix[(features.DC == 'BD'), 'DC'] = 'LD'
    print 'balance', 'treshold', 'erorr_rate', 'accuracy', 'err_acc'
    best_err_acc = 0
    best_balance = 0
    best_treshold = 0
    for i in np.arange(1,4, 0.2):
        for LAPLACE_BALANCE in np.arange(100,1000, 100):
            features['speed_changed'] = ((features.speed_3 + LAPLACE_BALANCE) / (features.speed_1 + LAPLACE_BALANCE) > i).astype(int)
            erorr_rate = round(len(features.ix[features.DC=='VHD'].ix[features.speed_changed==1, 'sex']) / float(len(features.ix[features.DC=='VHD', 'sex'])), 2)
            accuracy = round(len(features.ix[features.DC=='LD'].ix[features.speed_changed==1, 'sex']) / float(len(features.ix[features.DC=='LD', 'sex'])), 2)
            err_acc = accuracy-erorr_rate
            print LAPLACE_BALANCE, '     ', i, '    ', erorr_rate, '    ', accuracy, '    ', err_acc
            if err_acc > best_err_acc:
                best_err_acc = err_acc
                best_balance = LAPLACE_BALANCE
                best_treshold = i
    print best_err_acc, best_treshold, best_balance
#test_speed_change()


def plot_mtds_anomalies():
    for id in anomalies_mtds_ids:
        m = Monkey.objects.get(mky_id = id)
        mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=m).exclude_exceptions().order_by('drinking_experiment__dex_date').values_list('mtd_etoh_g_kg', flat = True)
        plt.plot(mtds)
    plt.title('mtds for abnormal experiments with monkeys: ' + str(anomalies_mtds_ids))

def plot_med_alcohol_speed():
    t = features.iloc[:, 3:6]
    dc = features.iloc[:, 2]
    print t
    plt.figure(1)
    plt.xlim(-0.2, 2.2)
    for id in features.index:
        plt.plot(t.ix[id].values, mycolors2[dc.ix[id]])
#plot_med_alcohol_speed()

def plot_med_alcohol_latency():
    t = features.iloc[:, 8:11]
    dc = features.iloc[:, 2]
    print t
    plt.figure(1)
    plt.xlim(-0.2, 2.2)
    for id in features.index:
        plt.plot(t.ix[id].values, mycolors2[dc.ix[id]])
    plt.title('Latency to drink by stage')
#plot_med_alcohol_latency()

def explore_feature():
    fig, axs = plt.subplots(2,1,facecolor='w', edgecolor='k')

    m = Monkey.objects.get(mky_id = 10067)
    data = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date').\
                    values_list('mtd_etoh_bout', flat=True)
    data = np.array(data)
    axs[0].plot(data, 'go')
    axs[0].set_title(str(m.mky_id) + ' mtd_etoh_bout')
    print np.mean(data)

    m = Monkey.objects.get(mky_id = 10090)
    data = reject_outliers(data)
    axs[1].plot(data, 'ro')
    axs[1].set_title(str(m.mky_id) + ' mtd_etoh_bout')
    fig.subplots_adjust(hspace=0.2)
    print np.mean(data)
explore_feature()

def feature_mean(feature):
    for m in define_monkeys():
        data = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date').\
                    values_list(feature, flat=True)
        print m.mky_id, m.mky_drinking_category, np.mean(np.array(data))
feature_mean('mtd_etoh_bout')


pylab.show()