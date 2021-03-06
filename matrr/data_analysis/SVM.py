__author__ = 'alex'
from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)

print feat_chosen.columns

x = feat_chosen.drop('mky_drinking_category', axis = 1)
y = feat_chosen['mky_drinking_category']
x = x.drop('mky_gender', axis=1)
x = x[['mtd_veh_bout_d', 'mky_age_at_intox', 'mtd_max_bout_length_d1','mtd_etoh_mean_drink_vol_d2']]
###play
# clf = svm.SVC(kernel='rbf', gamma=1, C=5, class_weight=dc_weights)
# fit = clf.fit(x,y)
# print fit
# print clf.n_support_
#
# y_pred = clf.predict(x)
# cm = confusion_matrix(y, y_pred)


###validation
#x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.1, random_state=0)
#clf = svm.SVC(kernel='rbf', gamma=1, C=5, class_weight=dc_weights)
clf = svm.SVC(kernel='linear', C=3, class_weight=dc_weights)
fit = clf.fit(x,y)

# a_scores = []
# kf = KFold(20, 5)
# for train_index, test_index in kf:
#     print("TRAIN:", train_index, "TEST:", test_index)
#     x_train, x_test = x[train_index], x[test_index]
#     y_train, y_test = y[train_index], y[test_index]
#     fit = clf.fit(x_train,y_train)
#     y_pred = clf.predict(x_test)
#     cm = confusion_matrix(y_test, y_pred)
#     print cm
#     a_score = accuracy_score(y_test, y_pred)
#     a_scores += a_score
# print a_scores

scores = cross_validation.cross_val_score(clf, x, y, cv=14)
print scores
print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std())

# print fit
# print clf.support_
# #print clf.support_vectors_
# print clf.n_support_

# y_pred = clf.predict(x_test)
# cm = confusion_matrix(y_pred, y_test)
#
#
#
# # Show confusion matrix in a separate window
# print(cm)
# plt.matshow(cm)
# plt.title('Confusion matrix')
# plt.colorbar()
# plt.ylabel('True label')
# plt.xlabel('Predicted label')
# plt.show()
# pylab.show()