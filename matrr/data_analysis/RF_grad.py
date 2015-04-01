__author__ = 'alex'
from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
#print len(feat_chosen[feat_chosen.mky_gender=='M'].index)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)



x = feat_chosen.drop('mky_drinking_category', axis = 1)
print x.columns
y = feat_chosen['mky_drinking_category']
x = x.drop('mky_gender', axis=1)
x = x[['mtd_veh_bout_d', 'mky_age_at_intox', 'mtd_max_bout_length_d1','mtd_etoh_mean_drink_vol_d2']]
print x.columns



###2D
# clf = GradientBoostingClassifier(n_estimators=100, max_depth=4,
#                                 learning_rate=0.1,
#                                 random_state=1)
# fit = clf.fit(x,y)
#
# features = [0, 2, (0, 2)]
# plot_partial_dependence(clf, x, features, label='VHD', feature_names=x.columns)
#
# pylab.show()