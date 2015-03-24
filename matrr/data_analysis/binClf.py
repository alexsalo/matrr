__author__ = 'alex'
from header import *

from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)

x = feat_chosen.drop('mky_drinking_category', axis = 1)
y = feat_chosen['mky_drinking_category']
x = x.drop('mky_gender', axis=1)
print x.columns

#try to delete 'bad' monkeys

#binarize output
# y[y=='BD']='LD'
# y[y=='HD']='VHD'
# print y

clf = RandomForestClassifier()
fit = clf.fit(x,y)
df = pd.DataFrame(list(x.columns))
df['imp'] = clf.feature_importances_
print df
print df.imp.sum()
bagging =  BaggingClassifier(clf, n_estimators=20, max_samples=0.8, max_features=0.4, bootstrap=True, n_jobs=2) #

scores = cross_validation.cross_val_score(clf, x, y, cv=14)
print "Accuracy Random Forest Classifier: %0.3f (sd %0.3f)" % (scores.mean(), scores.std())
scores = cross_validation.cross_val_score(bagging, x, y, cv=14)
print "Accuracy Random Forest Classifier with Bagging: %0.3f (sd %0.3f)" % (scores.mean(), scores.std())

clf = GradientBoostingClassifier(n_estimators=200, max_features='sqrt',max_depth=5)
bagging =  BaggingClassifier(clf, n_estimators=20, max_samples=0.8, max_features=0.4, bootstrap=True, n_jobs=2) #

scores = cross_validation.cross_val_score(clf, x, y, cv=14)
print "Accuracy Gradient Boosting Classifier: %0.3f (sd %0.3f)" % (scores.mean(), scores.std())
scores = cross_validation.cross_val_score(bagging, x, y, cv=14)
print "Accuracy Gradient Boosting Classifier + Bagging: %0.3f (sd %0.3f)" % (scores.mean(), scores.std())