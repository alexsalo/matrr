from common import *
from data_generation import get_bec_df_for_all_animals

from sklearn.ensemble import RandomForestRegressor

def compile_all_dfs():
    all_more2stdev, g1_more2stdev, g2_more2stdev = get_bec_df_for_all_animals('22hr', 'bec_more2stdev', regenerate=False)
    g1_more2stdev['more2stdev'] = False
    g2_more2stdev['more2stdev'] = True
    g1_more2stdev = g1_more2stdev.append(g2_more2stdev)

    g1_more2stdev['more80pct'] = False
    g1_more2stdev.more80pct[g1_more2stdev.bec > 80] = True

    # Drinking Category
    df = g1_more2stdev
    df = pd.concat([df, pd.get_dummies(df.dc)], axis=1)

    return df

df = compile_all_dfs()
print df.columns
def regress_on(xattr='etoh_at_bec_sample_time'):
    clf = RandomForestRegressor()
    #x = df[['more2stdev', 'more80pct', 'LD', 'BD', 'HD', 'VHD', xattr]]
    #x = df[['more2stdev', 'LD', 'BD', 'HD', 'VHD']]
    x = df[['more2stdev']]
    y = df['etoh_next_day']
    clf.fit(x, y)
    print 'Feature importances: %s' % ['%s: %.3f' % (f, fi) for f, fi in zip(x, clf.feature_importances_)]
    print 'R^2 (coefficient of determination): %.3f' % clf.score(x, y)

regress_on('bec')
regress_on('etoh_at_bec_sample_time')
regress_on('etoh_previos_day')

