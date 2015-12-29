__author__ = 'alex'
from header import *

features_names_perstage = [
        'mtd_seconds_to_stageone', #Seconds it took for monkey to reach day's ethanol allotment
        'mtd_latency_1st_drink', #Time from session start to first etOH consumption
        'mtd_etoh_bout', #Total etOH bouts (less than 300 seconds between consumption of etOH)
        'mtd_etoh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of etOH) per etOH bout
        #'mtd_veh_bout', #Total H20 bouts (less than 300 seconds between consumption of H20)
        #'mtd_veh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of H20) per H20 bout
        'mtd_etoh_mean_drink_length', #Mean length for ethanol drinks (less than 5 seconds between consumption of etOH is a continuous drink
        'mtd_etoh_median_idi', #Median time between drinks (always at least 5 seconds because 5 seconds between consumption defines a new drink
        'mtd_etoh_mean_drink_vol', #Mean volume of etOH drinks
        'mtd_etoh_mean_bout_length',
        'mtd_pct_etoh_in_1st_bout', #Percentage of the days total etOH consumed in the first bout
        'mtd_drinks_1st_bout', #Number of drinks in the first bout
        'mtd_max_bout', #Number of the bout with maximum ethanol consumption
        'mtd_max_bout_length', #Length of maximum bout (bout with largest ethanol consumption)
        'mtd_pct_max_bout_vol_total_etoh', #Maximum bout volume as a percentage of total ethanol consumed that day
        'etoh_during_ind'
        ]
cohort_names = ["INIA Rhesus 10", "INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 6a", "INIA Rhesus 7b",
            "INIA Rhesus 6b", "INIA Rhesus 7a"]

GENERATE_DATA = False
FOLD_INTO_TWO_DC = True
SUBDIVIDE = True

FIG_SIZE = (16, 10)
DPI = 100
matplotlib.rcParams.update({'font.size': 16})

RF = RandomForestClassifier(n_estimators=100)
BAGGING = BaggingClassifier(RF, n_estimators=10, bootstrap=True, n_jobs=2)
SVM_CLF = svm.SVC(kernel='linear', C=1, class_weight=dc_weights)

if not GENERATE_DATA:
    data = pd.read_pickle('dec_data_all.plk')
    data.sex = (data.sex == 'M').astype(int)

else:
    data = generate_data()

def generate_data():
    features_monkey = ["mky_id", 'cohort__coh_cohort_id', "mky_gender", "mky_age_at_intox", "mky_drinking_category", 'mky_days_at_necropsy']
    features_monkey_names = ["mky_id", 'coh', "sex", "intox", "DC", 'necropsy']
    FIRST_N_MINUTES = 10
    DELTA_DAYS = 10

    ml_cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
    ml_monkeys = Monkey.objects.filter(cohort__in = ml_cohorts).exclude(mky_drinking_category = None)

    data = pd.DataFrame(list(ml_monkeys.values_list(*features_monkey)), columns=features_monkey_names).set_index('mky_id')

    mky_medians = pd.DataFrame(index=[m.mky_id for m in ml_monkeys], columns = features_names_perstage + [s + "_1" for s in features_names_perstage] + [s + "_2" for s in features_names_perstage])
    mtds_all= MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey__in=ml_monkeys)
    for m in ml_monkeys:
        mtds = mtds_all.filter(monkey=m).order_by('drinking_experiment__dex_date')
        if m.mky_id in anomalies_mtds_ids:
            mtds = mtds[55:]
        for feature in features_names_perstage:
            if feature == 'etoh_during_ind':
                df = m.etoh_during_ind(FIRST_N_MINUTES)
            else:
                df = pd.DataFrame(list(mtds.values_list(feature, flat=True)))
            try:
                N = len(df)
                median_start = df.iloc[:DELTA_DAYS].median()[0]
                median_middle = df.iloc[N/2-DELTA_DAYS/2:N/2+DELTA_DAYS/2].median()[0]
                median_end= df.iloc[-DELTA_DAYS:].median()[0]

                feature_value = median_end / median_start
                feature_value_1 = median_middle / median_start
                feature_value_2 = median_end / median_middle
            except Exception as e:
                feature_value = 1 # NA - pretend has not changed
                feature_value_1 = 1 # NA - pretend has not changed
                feature_value_2 = 1 # NA - pretend has not changed

            mky_medians.at[m.mky_id, feature] = feature_value
            mky_medians.at[m.mky_id, feature+'_1'] = feature_value_1
            mky_medians.at[m.mky_id, feature+'_2'] = feature_value_2

    data = data.join(mky_medians)
    data = data.fillna(0)
    print_full(data)
    data.save('dec_data_all.plk')
    data.sex = (data.sex == 'M').astype(int)
    return data

if FOLD_INTO_TWO_DC:
    if SUBDIVIDE:
        data_LDBD = data.loc[data['DC'].isin(['LD','BD'])]
        data_HDVHD= data.loc[data['DC'].isin(['HD','VHD'])]

    data.ix[(data.DC=='BD'), 'DC']='LD'
    data.ix[(data.DC=='HD'), 'DC']='VHD'
    SVM_CLF = svm.SVC(kernel='linear', C=5)


### Testing ###
data_targets = data.DC
data_features = data.drop(['DC', 'coh'], axis = 1)
M_EXAMPLES = len(data_features.index)
print 'M = ' + str(M_EXAMPLES)

# Feature Selection Plot
def featureSelectionPlot(X, y, YLABEL, YNAIVE):
    import RF_feat_sel
    RF_feat_sel.feature_selection(X, y, YLABEL, YNAIVE, RUNS=10, FIG_SIZE=FIG_SIZE, DPI=DPI)

# Select Top Features
def selectFeatures4Classes(X):
    return X[['mtd_etoh_bout_2', 'intox', 'mtd_max_bout_length', 'mtd_etoh_mean_bout_length']]

def selectFeaturesHeavyNonHeavy(X):
    return X[['mtd_etoh_bout_2', 'necropsy', 'mtd_etoh_mean_drink_vol_1', 'mtd_etoh_mean_drink_length_1']]

def selectFeaturesLDBD(X):
    Xnew = X[['mtd_etoh_mean_drink_length_2', 'mtd_latency_1st_drink']]
    return Xnew

def selectFeaturesHDVHD(X):
    Xnew = X[['mtd_etoh_mean_drink_length', 'mtd_etoh_mean_drink_vol', 'mtd_etoh_mean_bout_length', 'mtd_max_bout_length']]
    return Xnew

## Test all features
def testClassifiers(X, y):
    # cv_classfier(X,y,RF,10, 'all features')
    # cv_classfier(X,y,BAGGING,10, 'all features')
    # cv_classfier(normalize(X),y,SVM_CLF,10, 'all features')

    X = selectFeatures(X)

    # Test Top features
    cv_classfier(X,y,RF,10, 'top features')
    cv_classfier(X,y,BAGGING,10, 'top features')
    cv_classfier(normalize(X),y,SVM_CLF,10, 'top features')

## Find best SVM parametr
def testSVMparams(X, y, selectFeatures=True):
    if selectFeatures:
        X = selectFeatures(X)
    X = normalize(X)
    print_full(X)
    print_full(y)

    best_accuracy = 0
    for kernel in ['linear', 'rbf', 'sigmoid']:
        for C in [1,2,3,4,5]:
            if FOLD_INTO_TWO_DC:
                svm_clf = svm.SVC(kernel=kernel, C=C)
            else:
                svm_clf = svm.SVC(kernel=kernel, C=C, class_weight=dc_weights)
            accuracy = cv_classfier(X,y,svm_clf,10, 'top features')
            if accuracy > best_accuracy:
                best_accuracy = accuracy
    return best_accuracy

## Test By Cohort (Holdouts)
def testByCoghort(X, y, clf, selectFeaturesFunc, NORMALIZE=False, exclude_cohs_ids=[]):
    print '\n--------------By Cohort-------------'
    coh_ids = np.unique(data.coh)
    gb = data.groupby('coh')
    X = selectFeaturesFunc(X)
    if NORMALIZE:
        X = normalize(X)

    global_expected = []
    global_predicted = []
    for coh_id in coh_ids:
        print coh_id
        if coh_id not in exclude_cohs_ids:
            expected = []
            predicted = []

            print Cohort.objects.get(coh_cohort_id = coh_id)
            index = gb.get_group(coh_id).index

            # Train on all but one cohort
            clf.fit(X[~X.index.isin(index)], y[~X.index.isin(index)])

            # Predict on holdout cohort
            y_pred = clf.predict(X[X.index.isin(index)])

            # Print what you got
            y_test = y[X.index.isin(index)]

            expected += list(y_test); global_expected += list(y_test);
            predicted += list(y_pred); global_predicted += list(y_pred);

            y_pred = pd.DataFrame(list(y_pred), columns=['predicted'], index = y_test.index)
            print pd.concat([y_test, y_pred], axis=1, join='inner')
            reportResults(clf, expected, predicted)
            print '-----------------------------------\n'
    reportResults(clf, global_expected, global_predicted, REPORT=True)

def reportResults(clf, expected, predicted, REPORT=False):
    if REPORT:
        print("\nClassification report for classifier %s:\n%s\n"
          % (clf, metrics.classification_report(expected, predicted)))
    print("Confusion matrix:\n%s" % metrics.confusion_matrix(expected, predicted))
    print("\nAccuracy score:\n%s" % metrics.accuracy_score(expected, predicted))

# Leave One Out or K-Fold
def KFoldMonkeys(X, y, clf, folds, NORMALIZE=False):
    print 'K-fold----------------'
    X = selectFeatures(X)
    if NORMALIZE:
        X = normalize(X)
    expected = []
    predicted = []
    for train_index, test_index in folds:
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        #fit and pred
        fit = clf.fit(X_train,y_train)
        y_pred = clf.predict(X_test)

        expected += list(y_test)
        predicted += list(y_pred)
    reportResults(clf, expected, predicted)
    print '-------------------'

def runTwoThenTwo():
    print '\n-------LD-BD-----------------'
    # X = selectFeaturesLDBD(data_LDBD)
    # print X.columns
    # cv_classfier(X,y,RF,10, 'top features')
    y = data_LDBD.DC

    # X_feat_sel = data_LDBD.drop(['DC', 'coh'], axis = 1)
    # featureSelectionPlot(X_feat_sel, y, "LD vs BD", 0.615)

    print '\n-------HD-VHD-----------------'
    # X = selectFeaturesHDVHD(data_HDVHD)
    # print X.columns
    # cv_classfier(X,y,RF,10, 'top features')
    y = data_HDVHD.DC

    # X_feat_sel = data_HDVHD.drop(['DC', 'coh'], axis = 1)
    # featureSelectionPlot(X_feat_sel, y, "HD vs VHD", 0.625)

def gradients(func_data, selectFeaturesFunc, foldername, target='VHD'):
    X = selectFeaturesFunc(func_data)
    print X.columns
    y = func_data.DC
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                learning_rate=0.1,
                                random_state=1)
    fit = clf.fit(X,y)

    n_features = len(X.columns)
    for i in xrange(n_features):
        for j in xrange(i-1):
            lbl = target
            #get the figure
            fig = plt.figure(figsize=(14,8))
            ax = fig.add_subplot(111)
            plt.clf()

            features = [i, j, (i, j)]
            print 'features: ', features
            plot_partial_dependence(clf, X, features, label=lbl, feature_names=X.columns, ax=ax)
            #title and save
            plotname = lbl + ' ' + str(X.columns[i])+' ' + str(X.columns[j]) + ' ' + 'partial dependency.png'
            plt.title(plotname)
            path = '/home/alex/win-share/matrr_sync/gradients/' + foldername
            plt.savefig(os.path.join(path, plotname), dpi=100, format='png')

def massiveRFTest(X, y):
    #X = selectFeatures(X)
    scores = []
    for i in xrange(20):
        scores.extend(cross_validation.cross_val_score(RF, X, y, cv=10))
    print 'Avg score for 20 runs is: %s, sd = %s ' % (np.mean(scores), np.std(scores))
#massiveRFTest(selectFeaturesHDVHD(data), data.DC)


def printByCohortDCdistr():
    ml_cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
    for c in ml_cohorts:
        monkeys = Monkey.objects.filter(cohort=c).exclude(mky_drinking_category = None)
        print '/n--------------------'
        print c
        df = pd.DataFrame(list(monkeys.values_list('mky_drinking_category', flat=True)), columns = ['dc'])
        print df.dc.value_counts()

def findSignif():
    signif_cnt = 0
    for feature in data_features.columns:
        ld = data[data['DC']=='LD'][feature]
        #bd = data[data['DC']=='BD'][feature]
        #hd = data[data['DC']=='HD'][feature]
        vhd = data[data['DC']=='VHD'][feature]
        #f_val, p_val = stats.f_oneway(ld, bd, hd, vhd)
        f_val, p_val = stats.f_oneway(ld, vhd)
        if p_val < 0.05:
            importance = 'SIGNIF!:  '
            signif_cnt += 1
        else: importance = ''
        print importance + feature + " One-way ANOVA P =", p_val
    print '\n Significant vars: ' + str(signif_cnt)

### RUN SCRIPTS
#findSignif()

#base_rate_accuracy = data_targets.value_counts()/len(data_targets.index)
#print base_rate_accuracy
#printByCohortDCdistr()

#featureSelectionPlot(data_features, data_targets, "LD vs BD vs HD vs VHD", 0.32)
#featureSelectionPlot(data_features, data_targets, "LD + BD vs HD + VHD", 0.52)

# best_accuracy = testSVMparams(data_features, data_targets, selectFeatures = False)

#testClassifiers(data_features, data_targets)
#
# testByCoghort(data_features, data_targets, RF, selectFeaturesHeavyNonHeavy, False)
# testByCoghort(data_LDBD.drop(['DC'], axis = 1), data_LDBD.DC, RF, selectFeaturesLDBD, False, exclude_cohs_ids=[7])
# testByCoghort(data_HDVHD.drop(['DC'], axis = 1), data_HDVHD.DC, RF, selectFeaturesHDVHD, False, exclude_cohs_ids=[9, 5])
# testByCoghort(data_features, data_targets, SVM_CLF, True)
#
# KFoldMonkeys(data_features, data_targets, RF, cross_validation.LeaveOneOut(M_EXAMPLES))
# KFoldMonkeys(data_features, data_targets, RF, cross_validation.KFold(M_EXAMPLES, n_folds=10))
#
# KFoldMonkeys(data_features, data_targets, SVM_CLF, cross_validation.LeaveOneOut(M_EXAMPLES), NORMALIZE=True)
# KFoldMonkeys(data_features, data_targets, SVM_CLF, cross_validation.KFold(M_EXAMPLES, n_folds=10), NORMALIZE=True)

#runTwoThenTwo()

#print data.mtd_max_bout_length
#plt.plot(data.mtd_pct_max_bout_vol_total_etoh_2, 'ro')
#data.mtd_max_bout_length[np.abs(data.mtd_max_bout_length-data.mtd_max_bout_length.mean()) < 2 * data.mtd_max_bout_length.std()].hist()
#data.mtd_max_bout_length.hist()
#pylab.show()

#gradients(data, selectFeaturesHeavyNonHeavy, 'heavy_nonheavy')
#gradients(data_LDBD, selectFeaturesLDBD, 'ld_bd', target='LD')
#gradients(data_HDVHD, selectFeaturesHDVHD, 'hd_vhd')

# massiveRFTest(data_features, data_targets)
# print data
# pct_data = data[['mtd_pct_etoh_in_1st_bout_1', 'mtd_pct_etoh_in_1st_bout_2']]
# print pct_data
# print pct_data.loc[10086].values
#
# for index in pct_data.index:
#     if data.loc[index].DC == 'VHD':
#         plt.plot(xrange(2), pct_data.loc[index].values, dc_colors_ol[data.DC.loc[index]])
# plt.ylim([0.2, 1.5])

def plot_meds(features):
    matplotlib.rcParams.update({'font.size': 18})
    fig, axs = plt.subplots(2,2,facecolor='w', edgecolor='k', figsize=(14,14))
    axs = axs.ravel()
    dc = data.DC
    print features
    plt.xlim(0, 97)
    for ax in axs:
        ax.set_xlim(44, 97)
        ax.set_ylim(0,  9.3)
        ax.tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom='off',      # ticks along the bottom edge are off
            top='off',         # ticks along the top edge are off
            labelbottom='on') # labels along the bottom edge are off
    for id in features.index:
        if id not in [10091]:
            ax_index = 0
            if dc.ix[id] == "BD":
                ax_index = 1
            if dc.ix[id] == "HD":
                ax_index = 2
            if dc.ix[id] == "VHD":
                ax_index = 3
            axs[ax_index].plot([50, 90],features.ix[id].values, dc_colors_ol[dc.ix[id]], linewidth=1.5)
            yval0 = features.ix[id].values[0]
            axs[ax_index].plot([45,55], [yval0, yval0], dc_colors_dash[dc.ix[id]], linewidth=2.5)
            yval1 = features.ix[id].values[1]
            axs[ax_index].plot([85,95], [yval1, yval1], dc_colors_dash[dc.ix[id]], linewidth=2.5)

    axs[0].text(70, 8.5, 'LD')
    axs[1].text(70, 8.5, 'BD')
    axs[2].text(70, 8.5, 'HD')
    axs[3].text(70, 8.5, 'VHD')


    # plt.title('Medain number of bouts by stage')
    axs[2].set_ylabel('Relative change of the attribute "Number of bouts"')
    axs[2].set_xlabel("Induction phase")

    # Fine-tune figure; make subplots close to each other and hide x ticks for all but bottom plot.
    plt.tight_layout()
    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.setp([axs[i].get_xticklabels() for i in [0,1,3]], visible = False)
    plt.setp([axs[i].get_yticklabels() for i in [1,3]], visible = False)

    labels = [item.get_text() for item in axs[2].get_xticklabels()]
    labels = ['', '1st Half','','','','2nd Half']
    axs[2].set_xticklabels(labels)


#pct_data = data[['mtd_etoh_bout_1', 'mtd_etoh_bout_2', 'DC']]
#plot_meds(pct_data)

"""
27 Dec 2015
Generate Two PDPs
"""


def create_pdp_hd_vhd():
    x = data_HDVHD[['mtd_etoh_mean_drink_length', 'mtd_etoh_mean_drink_vol', 'mtd_etoh_mean_bout_length', 'mtd_max_bout_length']]
    x.columns = ['Mean length for EtOH drinks', 'sfdfgsd', 'dfd', 'Max bout length']
    target = 'VHD'

    y = data_HDVHD.DC
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                     learning_rate=0.1, random_state=1)
    clf.fit(x, y)

    matplotlib.rcParams.update({'font.size': 16})
    fig = plt.figure(figsize=(14, 7))
    ax = fig.add_subplot(111)
    plot_partial_dependence(clf, x, [3, 0, (3, 0)], label=target, feature_names=x.columns, ax=ax)
    plt.suptitle('Partial Dependence on Becoming VHD')
    plt.tight_layout()
    pylab.show()
#create_pdp_hd_vhd()


def create_pdp_heavy_nonheavy():
    x = data[['mtd_etoh_bout_2', 'necropsy', 'intox', 'mtd_etoh_median_idi']]
    x.columns = ['Total number of bouts', 'Age', 'Age of First Intoxication', 'Median EtOH interbout interval']
    target = 'VHD'

    y = data.DC
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                     learning_rate=0.1, random_state=1)
    clf.fit(x, y)

    matplotlib.rcParams.update({'font.size': 16})
    fig = plt.figure(figsize=(14, 7))
    ax = fig.add_subplot(111)
    plot_partial_dependence(clf, x, [2, 0, (2, 0)], label=target, feature_names=x.columns, ax=ax)
    plt.suptitle('Partial Dependence on Becoming VHD')
    plt.tight_layout()
    pylab.show()
    fig.subplots_adjust(top=0.93)
create_pdp_heavy_nonheavy()