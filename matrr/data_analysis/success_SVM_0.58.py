__author__ = 'alex'
__author__ = 'alex'
from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)

print feat_chosen.columns

x = feat_chosen.drop('mky_drinking_category', axis = 1)
y = feat_chosen['mky_drinking_category']

###play
# clf = svm.SVC(kernel='rbf', gamma=1, C=5, class_weight=dc_weights)
# fit = clf.fit(x,y)
# print fit
# print clf.n_support_
#
# y_pred = clf.predict(x)
# cm = confusion_matrix(y, y_pred)


###validation
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.1, random_state=0)
#clf = svm.SVC(kernel='rbf', gamma=1, C=5, class_weight=dc_weights)
clf = svm.SVC(kernel='linear', C=3, class_weight=dc_weights)
fit = clf.fit(x,y)

scores = cross_validation.cross_val_score(clf, x, y, cv=5)
print scores
print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2)

print fit
print clf.support_
#print clf.support_vectors_
print clf.n_support_

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