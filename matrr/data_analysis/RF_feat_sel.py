__author__ = 'alex'
from header import *

feat_chosen = pd.read_pickle('feat_chosen.plk')
feat_chosen = feat_chosen.drop('cohort__coh_cohort_id', axis = 1)
feat_chosen.mky_gender = (feat_chosen.mky_gender == 'M').astype(int)

x = feat_chosen.drop('mky_drinking_category', axis = 1)
y = feat_chosen['mky_drinking_category']
x = x.drop('mky_gender', axis=1)
print x.columns

# y[y=='BD']='LD'
# y[y=='HD']='VHD'

clf = RandomForestClassifier()
###FEATURE SELECTION
top5_features = []
RUNS=10
test_best_scores = np.empty([RUNS, 13])
for i in xrange(RUNS):
    all_features = list(x.columns)
    N = len(all_features)
    F = []
    best_scores = []
    while len(F) < N:
        best_score = 0
        for feature in all_features:
            tmp_F = []
            for f in F:
                tmp_F.append(f)
            tmp_F.append(feature)
            #evalute
            scores = cross_validation.cross_val_score(clf, x[tmp_F], y, cv=14)
            score = scores.mean()
            if score > best_score:
                best_score = score
                best_feature = feature
        print best_feature, best_score
        best_scores.append(best_score)
        F.append(best_feature)
        all_features.remove(best_feature)
    print F
    #test_best_scores = (test_best_scores + np.array(best_scores)) / 2.0
    test_best_scores[i] = best_scores
    top5_features += F[:4]

#best features stat
print 'Results: \n -------------------------------------'
import collections
print top5_features
print collections.Counter(top5_features)

tbs_means = np.mean(test_best_scores, axis=0)
tbs_sds = np.std(test_best_scores, axis=0)
print tbs_means
plt.plot(xrange(1,14), tbs_means)
plt.xlabel('Number of features')
plt.ylabel('Accuracy')
plt.grid()
plt.xlim(1,13)

lower_bound = substract_lists(tbs_means, tbs_sds, 'sum')
upper_bound = substract_lists(tbs_means, tbs_sds, 'diff')
plt.fill_between(xrange(1,14), lower_bound, upper_bound, facecolor='yellow', alpha=0.5,
                label='+- sigma range')
#dummy plot to creaate legend since fill_between is not supported
plt.plot([], [], color='yellow', linewidth=10, label='+- sigma range')
plt.legend(loc='upper left')

pylab.show()

