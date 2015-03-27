__author__ = 'alex'
from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)

x = feat_chosen.drop('mky_drinking_category', axis = 1)
y = feat_chosen['mky_drinking_category']
x = x.drop('mky_gender', axis=1)
x = x[['mtd_veh_bout_d', 'mky_age_at_intox', 'mtd_max_bout_length_d1','mtd_etoh_mean_drink_vol_d2']]
print x.columns

def showCM(cm, plot=True):
    print(cm)

    #Accuracy
    trues = sum(cm[i][i] for i in xrange(0, len(cm)))
    accuracy = trues / (cm.sum() * 1.0)
    print ('Accuracy: %s' % accuracy)

    #Balanced Error Rate
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

def showScores(scores):
    print 'Accuracy scores for each split: ', scores
    print "Accuracy: %0.2f (+/- %0.2f)" % (np.mean(scores), np.std(scores))

###My Cross Val
def executeCrossVal(x, y, clf):
    N = len(x.index)
    print ('Total number of elements: %s' % N)
    base_rate_accuracy = y.value_counts()/len(y.index)
    #print y.value_counts()
    print 'Base rate accuracy:'
    print base_rate_accuracy

    cm = np.zeros(shape=(4,4), dtype=int)
    scores = []
    ss = cross_validation.ShuffleSplit(N, n_iter=8, test_size=3,random_state=0)
    misclassified = []
    for train_index, test_index in ss:
        #train set
        train_x = x.loc[list(x.index[train_index])]
        train_y = y.loc[list(x.index[train_index])]

        #test set
        test_x = x.loc[list(x.index[test_index])]
        test_y = y.loc[list(x.index[test_index])]

        #fit and pred
        fit = clf.fit(train_x,train_y)
        #print clf.feature_importances_
        y_pred = clf.predict(test_x)

        #LD-VHD MIX
        tmp = test_y[y_pred == 'VHD']
        print tmp[tmp=='LD']
        tmp = test_y[y_pred == 'LD']
        print tmp[tmp=='VHD']

        #accuracy score and confusion matrix
        scores.append(accuracy_score(y_pred, test_y))
        cm_cur = confusion_matrix(y_pred, test_y, labels = ['LD', 'BD', 'HD', 'VHD'])
        skipped = 0
        if len(cm_cur) == 4:
            cm += cm_cur
        else:
            skipped += 1

    print ('Skipped for confusion matrix: %s' % skipped)
    return scores, cm

clf = RandomForestClassifier()
#clf = GradientBoostingClassifier(n_estimators=200, max_features='sqrt',max_depth=5)
bagging =  BaggingClassifier(clf, n_estimators=20, max_samples=0.8, max_features=0.4, bootstrap=True, n_jobs=2) #

scores, cm = executeCrossVal(x, y, clf)
showScores(scores)
showCM(cm, True)

#x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)

#print clf.feature_importances_
#features = [0, 10, (0, 10)]
#plot_partial_dependence(clf, x, features, label='LD')

scores = cross_validation.cross_val_score(clf, x, y, cv=14)
print scores
print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std())

# scores = cross_validation.cross_val_score(bagging, x, y, cv=14)
# print scores
# print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std())

# y_pred = clf.predict(x_test)
# cm = confusion_matrix(y_pred, y_test)
# print cm


# model = RandomForestClassifier()
# fit = model.fit(x,y)
# print fit
# y_pred = model.predict(x)
# cm = confusion_matrix(y, y_pred)
# print cm

# scores = cross_validation.cross_val_score(clf, x, y, cv=3)
# print scores
# print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2)

