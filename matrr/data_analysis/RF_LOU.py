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

# binarize output
y[y=='BD']='LD'
y[y=='HD']='VHD'
print y

clf = RandomForestClassifier()
#clf = GradientBoostingClassifier(n_estimators=200, max_features='sqrt',max_depth=5)
bagging =  BaggingClassifier(clf, n_estimators=20, max_samples=0.8, max_features=0.4, bootstrap=True, n_jobs=2) #

N = len(x.index)
loo = cross_validation.LeaveOneOut(N)
correct = 0
cm = np.zeros(shape=(4,4), dtype=int)
cm_dict = {
    'LD' : 0,
    'BD' : 1,
    'HD' : 2,
    'VHD' : 3,
}

for train_index, test_index in loo:
    x_train, x_test = x.iloc[train_index], x.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]

    #fit and pred
    fit = bagging.fit(x_train,y_train)
    y_pred = bagging.predict(x_test)

    print y_pred
    print y_test.values
    if y_test.values == y_pred:
        correct += 1
        print 'correct'
    else:
        print 'wrong'

    i = cm_dict[y_pred[0]]
    j = cm_dict[y_test.values[0]]
    cm[i][j] += 1

print 'Accuracy:  %0.2f' % (1.0*correct / N)
print cm
