__author__ = 'alex'
from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)

print feat_chosen.columns

x = feat_chosen.drop('mky_drinking_category', axis = 1)
y = feat_chosen['mky_drinking_category']
x = x.drop('mky_gender', axis=1)

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)
clf = GradientBoostingClassifier()
fit = clf.fit(x,y)
print clf.feature_importances_
features = [0, 10, (0, 10)]
plot_partial_dependence(clf, x, features, label='LD')

y_pred = clf.predict(x_test)
cm = confusion_matrix(y_pred, y_test)

for i in xrange(10):
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)
    clf = GradientBoostingClassifier()
    fit = clf.fit(x,y)
    y_pred = clf.predict(x_test)
    cm += confusion_matrix(y_pred, y_test)

# Show confusion matrix in a separate window
print(cm)
plt.matshow(cm)
plt.title('Confusion matrix')
plt.colorbar()
plt.ylabel('True label')
plt.xlabel('Predicted label')
plt.show()
pylab.show()

# model = RandomForestClassifier()
# fit = model.fit(x,y)
# print fit
# y_pred = model.predict(x)
# cm = confusion_matrix(y, y_pred)
# print cm
#
# scores = cross_validation.cross_val_score(model, x, y, cv=5)
# print scores
# print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2)