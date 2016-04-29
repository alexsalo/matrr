#
#
# ### Testing ###
# data_targets = data.DC
# data_features = data.drop(['DC', 'coh'], axis = 1)
# M_EXAMPLES = len(data_features.index)
# print 'M = ' + str(M_EXAMPLES)

RF = RandomForestClassifier(n_estimators=100)
BAGGING = BaggingClassifier(RF, n_estimators=10, bootstrap=True, n_jobs=2)
SVM_CLF = svm.SVC(kernel='linear', C=1, class_weight=dc_weights)


# Feature Selection Plot
def featureSelectionPlot(X, y, YLABEL, YNAIVE):
    import RF_feat_sel
    RF_feat_sel.feature_selection(X, y, YLABEL, YNAIVE, RUNS=10, FIG_SIZE=FIG_SIZE, DPI=DPI)

# Select Top Features
def selectFeatures4Classes(X):
    return X[['mtd_etoh_bout_2', 'intox', 'mtd_max_bout_length', 'mtd_etoh_mean_bout_length']]

def selectFeaturesHeavyNonHeavy(X):
    return X[['mtd_etoh_bout_2', 'age_at_necropsy', 'mtd_etoh_mean_drink_vol_1', 'mtd_etoh_mean_drink_length_1']]

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