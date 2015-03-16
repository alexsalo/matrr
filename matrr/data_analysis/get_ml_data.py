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

def avg_drinking_feature_for_monkeys(monkeys, mtds_all, index, feature):
    avgs = pd.DataFrame(columns=["avg_"+feature], index=index)
    for m in monkeys:
        mtds = mtds_all.filter(monkey = m)
        avg = reject_outliers(np.array(mtds.values_list(feature, flat=True))).mean()
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
    avg_mtds = avg_drinking_feature_for_monkeys(ml_monkeys, mtds_all, df.index, 'mtd_latency_1st_drink')
    df['avg_latency'] = avg_mtds["avg_mtd_latency_1st_drink"]
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

    #median bouts
    median_etoh_bouts_by_stage = median_value_per_stage_for_monkeys(ml_monkeys, mtds_all, df.index, 'mtd_etoh_bout')
    df['bouts_1'] = median_etoh_bouts_by_stage.mtd_etoh_bout_1
    df['bouts_2'] = median_etoh_bouts_by_stage.mtd_etoh_bout_2
    df['bouts_3'] = median_etoh_bouts_by_stage.mtd_etoh_bout_3
    df['bouts_total'] = median_etoh_bouts_by_stage.mtd_etoh_bout_total
    df['bouts_increased'] = (df.bouts_3 > df.bouts_1).astype(int)

    #avg bouts
    df['avg_bouts'] = avg_drinking_feature_for_monkeys(ml_monkeys, mtds_all, df.index, 'mtd_etoh_bout')['avg_mtd_etoh_bout']
    return df

def fold_feature_dc():
    features.ix[(features.DC == 'HD'), 'DC'] = 'VHD'
    features.ix[(features.DC == 'BD'), 'DC'] = 'LD'

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
    X = features.drop('DC', axis = 1)
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
def svm_do():
    from sklearn import cross_validation
    from sklearn import datasets
    from sklearn import svm
    #fold_feature_dc()
    x = features.drop('DC', axis = 1)
    y = features['DC']

    # X_train, X_test, y_train, y_test = cross_validation.train_test_split(x, y, test_size=0.3, random_state=0)
    # clf = svm.SVC(kernel='linear', C=1).fit(X_train, y_train)
    # print clf
    # print clf.score(X_test, y_test)

    clf = svm.SVC(kernel='linear', C=1)
    scores = cross_validation.cross_val_score(clf, x, y, cv=5)
    print scores
    print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2)
def svm_do2():
    import matplotlib.pyplot as plt
    from sklearn import svm, datasets
    from sklearn.metrics import roc_curve, auc
    from sklearn.cross_validation import train_test_split
    from sklearn.preprocessing import label_binarize
    from sklearn.multiclass import OneVsRestClassifier

    X = features[['speed_total', 'latency_total', 'bouts_total']]
    y = features[['DC']]

    # Binarize the output
    y = label_binarize(y, classes=["LD", "BD", "HD", "VHD"])
    n_classes = y.shape[1]
    print y
    print n_classes

    # shuffle and split training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.3,
                                                    random_state=0)

    # Learn to predict each class against the other
    classifier = OneVsRestClassifier(svm.SVC(kernel='linear', probability=True,
                                     random_state=0))
    y_score = classifier.fit(X_train, y_train).decision_function(X_test)
    print y_score

    # Compute ROC curve and ROC area for each class
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Compute micro-average ROC curve and ROC area
    fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), y_score.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    # Plot ROC curve
    plt.figure()
    plt.plot(fpr["micro"], tpr["micro"],
             label='micro-average ROC curve (area = {0:0.2f})'
                   ''.format(roc_auc["micro"]))
    for i in range(n_classes):
        plt.plot(fpr[i], tpr[i], label='ROC curve of class {0} (area = {1:0.2f})'
                                       ''.format(i, roc_auc[i]))

    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Some extension of Receiver operating characteristic to multi-class')
    plt.legend(loc="lower right")
    plt.show()

#features = get_features(False)
#print features
#logistic(features, False, False)
#svm_do()

def test_latency_change():
    print features[['latency_increased', 'DC']]
    fold_feature_dc()
    erorr_rate = round(len(features.ix[features.DC=='VHD'].ix[features.latency_increased==1, 'sex']) / float(len(features.ix[features.DC=='VHD', 'sex'])), 2)
    accuracy = round(len(features.ix[features.DC=='LD'].ix[features.latency_increased==1, 'sex']) / float(len(features.ix[features.DC=='LD', 'sex'])), 2)
    err_acc = accuracy - erorr_rate
    print erorr_rate, '    ', accuracy, '    ', err_acc

def test_speed_change():
    fold_feature_dc()
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

def test_bouts_change():
    print features[['bouts_increased', 'DC']]
    fold_feature_dc()
    erorr_rate = round(len(features.ix[features.DC=='VHD'].ix[features.bouts_increased==1, 'sex']) / float(len(features.ix[features.DC=='VHD', 'sex'])), 2)
    accuracy = round(len(features.ix[features.DC=='LD'].ix[features.bouts_increased==1, 'sex']) / float(len(features.ix[features.DC=='LD', 'sex'])), 2)
    err_acc = accuracy - erorr_rate
    print erorr_rate, '    ', accuracy, '    ', err_acc
#test_bouts_change()

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

def plot_med_med_bouts():
    t = features.iloc[:, 14:17]
    dc = features.iloc[:, 2]
    print t
    plt.figure(1)
    plt.xlim(-0.2, 2.2)
    for id in features.index:
        plt.plot(t.ix[id].values, mycolors2[dc.ix[id]])
    plt.title('Bouts number by stage')
#plot_med_med_bouts()

def explore_feature(feature, mids):
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    fig, axs = plt.subplots(len(mids),1,facecolor='w', edgecolor='k', figsize=(13,14))
    for i, id in enumerate(mids):
        m = Monkey.objects.get(mky_id=id)
        data = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date').\
                        values_list(feature, flat=True)
        data = np.array(data)
        data = [x for x in data if x != None]
        #axs[i].plot(data, mycolors[m.mky_drinking_category])
        xpred, ypred = lwr.wls(xrange(len(data)), data, False)
        axs[i].plot(xrange(len(data)), data, mycolors[m.mky_drinking_category], xpred, ypred, 'b-')
        axs[i].set_title(str(m.mky_id) + feature)

        mu = np.mean(data)
        median = np.median(data)
        textstr = '$\mu=%.2f$\n$\mathrm{median}=%.2f$'%(mu, median)
        axs[i].text(0.2, 0.95, textstr, transform=axs[i].transAxes, fontsize=14, verticalalignment='top', bbox=props)
    fig.subplots_adjust(hspace=0.2)
    path = '/home/alex/MATRR/dc_feature_example/'
    plotname = 'dc_feature_example_' + feature + '.png'
    fig.savefig(os.path.join(path, plotname), dpi=100)

#explore_feature('mtd_etoh_bout')
# explore_feature('mtd_etoh_median_idi', [10048, 10051, 10049, 10061])
# for feature in features_names_perstage:
#     explore_feature(feature, [10048, 10051, 10049, 10061])

# m = Monkey.objects.get(mky_id = 10081)
# data = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date').\
#                 values_list('mtd_veh_drink_bout', flat=True)
# data = np.array(data)
# data = [x for x in data if x != None]
# xpred, ypred = lwr.wls(xrange(len(data)), data, False)
# plt.plot(xrange(len(data)), data, mycolors[m.mky_drinking_category], xpred, ypred, 'b-')
# print data
#
# print data
# import scipy.stats.stats as st
# print st.nanmean(data)
# data = np.array(data, dtype=object)
# print data
#print np.ma.masked_values(data, None)



def feature_mean(feature):
    for m in define_monkeys():
        data = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=m).order_by('drinking_experiment__dex_date').\
                    values_list(feature, flat=True)
        print m.mky_id, m.mky_drinking_category, np.mean(np.array(data))
#feature_mean('mtd_etoh_bout')


#pylab.show()