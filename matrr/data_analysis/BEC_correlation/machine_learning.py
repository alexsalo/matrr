from common import *
from data_generation import get_bec_df_for_all_animals

def compile_all_dfs():
    all_more2stdev, g1_more2stdev, g2_more2stdev = get_bec_df_for_all_animals('22hr', 'bec_more2stdev', regenerate=False)
    g1_more2stdev['more2stdev'] = False
    g2_more2stdev['more2stdev'] = True
    g1_more2stdev = g1_more2stdev.append(g2_more2stdev)

    g1_more2stdev['more80pct'] = False
    g1_more2stdev.more80pct[g1_more2stdev.bec > 80] = True

    return g1_more2stdev


df = compile_all_dfs()
print df.columns

from sklearn import cross_validation
from sklearn.ensemble import RandomForestRegressor

clf = RandomForestRegressor()
#x = df[['bec', 'more2stdev', 'more80pct']]
x = df[['bec', 'more2stdev']]
y = df['etoh_next_day']
clf.fit(x, y)


scores = cross_validation.cross_val_score(clf, x, y, cv=4)
print scores
print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std())

