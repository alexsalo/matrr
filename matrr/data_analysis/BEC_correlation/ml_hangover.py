from common import *
from sklearn.ensemble import RandomForestRegressor
from matrr.models import Cohort, MonkeyToDrinkingExperiment

r6a = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6a")
r6b = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6b")
r5 = Cohort.objects.get(coh_cohort_name="INIA Rhesus 5")
r7a = Cohort.objects.get(coh_cohort_name="INIA Rhesus 7a")
r7b = Cohort.objects.get(coh_cohort_name="INIA Rhesus 7b")

RHESUS_FEMALES = [r6a, r6b]
RHESUS_MALES = [r5, r7a, r7b]

# def get_mky_drinking(mtds, mky):
#     mky_mtds = mtds.filter(monkey=mky).order_by('drinking_experiment__dex_date')
#     df = pd.DataFrame(list(mky_mtds.values_list('monkey__mky_gender', 'monkey__mky_drinking_category', 'mtd_etoh_g_kg')),
#                       columns=['sex', 'dc', 'etoh'])
#
#     # Normalize (Not taking into account linear trend of more drinking well into experiment
#     df.etoh = (df.etoh - df.etoh.mean()) / (df.etoh.std())
#
#     # Extra variables
#     df['over2std'] = False
#     df['over1std'] = False
#     df.over1std[df.etoh > 1] = True
#     df.over2std[df.etoh > 2] = True
#
#
#     # append next day
#     next = list(df.etoh[1:])
#     next.append(0)
#     df['next'] = next
#
#     # refactor sex
#     df.sex = [True if sex == 'M' else False for sex in df.sex]
#
#     #print df[:-1]
#     return df[:-1]
#
#
# def combine_mkys_drinking():
#     #monkeys = Monkey.objects.filter(mky_drinking_category__isnull=False)
#     monkeys = Monkey.objects.filter(cohort__in=RHESUS_MALES + RHESUS_FEMALES).filter(mky_drinking_category__isnull=False)
#     print monkeys.count()
#     mtds = MonkeyToDrinkingExperiment.objects.OA().filter(mtd_etoh_g_kg__isnull=False)
#     df = get_mky_drinking(mtds, monkeys[0])
#     for mky in monkeys:
#         df = df.append(get_mky_drinking(mtds, mky))
#
#     # Dummy DC
#     df = pd.concat([df, pd.get_dummies(df.dc)], axis=1)
#
#     print df
#     return df
#
# def regress(df, atrrs):
#     clf = RandomForestRegressor()
#     x = df[atrrs]
#     y = df['next']
#     clf.fit(x, y)
#     print 'Feature importances: %s' % ['%s: %.3f' % (f, fi) for f, fi in zip(x, clf.feature_importances_)]
#     print 'R^2 (coefficient of determination): %.3f' % clf.score(x, y)
#
# df = combine_mkys_drinking()
# regress(df, ['etoh'])
# regress(df, ['etoh', 'over2std', 'over1std'])
# regress(df, ['etoh', 'over2std', 'over1std', 'sex'])
# regress(df, ['etoh', 'over2std', 'over1std', 'sex', 'LD', 'BD', 'HD', 'VHD'])


def get_mky_drinking(mky):
    # 1. Filter work data set
    becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
    mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).exclude(mtd_etoh_g_kg__isnull=True)

    # 2. Retain intersection
    bec_dates = becs.values_list('bec_collect_date', flat=True)
    bec_dates_next = [date + timedelta(days=+1) for date in bec_dates]
    mtds_next = mtds.filter(drinking_experiment__dex_date__in=bec_dates_next)

    bec_dates_to_retain = [date + timedelta(days=-1) for date in mtds_next.values_list('drinking_experiment__dex_date', flat=True)]
    becs = becs.filter(bec_collect_date__in=bec_dates_to_retain)

    # 6. Assert we have the same number of data days
    print 'becs retained: %s' % becs.count()
    print 'etoh on next day retained: %s' % mtds_next.count()
    assert becs.count() == mtds_next.count()

    df = pd.DataFrame(list(becs.values_list('monkey__mky_drinking_category', 'monkey__mky_gender',
                                            'bec_mg_pct', 'bec_gkg_etoh')),
                          columns=['dc', 'sex', 'bec', 'etoh'])
    df['etoh_next'] = list(mtds_next.values_list('mtd_etoh_g_kg', flat=True))

    # refactor sex
    df.sex = [True if sex == 'M' else False for sex in df.sex]

    # Normalize (Not taking into account linear trend of more drinking well into experiment
    df.etoh = (df.etoh - df.etoh.mean()) / (df.etoh.std())
    df.etoh_next = (df.etoh_next - df.etoh_next.mean()) / (df.etoh_next.std())
    df.bec = (df.bec - df.bec.mean()) / (df.bec.std())

    # Extra variables
    df['over2std'] = False
    df['over1std'] = False
    df.over1std[df.bec > 1] = True
    df.over2std[df.bec > 2] = True

    return df
# monkeys = Monkey.objects.filter(cohort__in=RHESUS_MALES + RHESUS_FEMALES).filter(mky_drinking_category__isnull=False)
# print get_mky_drinking(monkeys[0])


def combine_mkys_drinking():
    #monkeys = Monkey.objects.filter(mky_drinking_category__isnull=False)
    monkeys = Monkey.objects.filter(cohort__in=RHESUS_MALES + RHESUS_FEMALES).filter(mky_drinking_category__isnull=False)
    print monkeys.count()
    mtds = MonkeyToDrinkingExperiment.objects.OA().filter(mtd_etoh_g_kg__isnull=False)
    df = get_mky_drinking(monkeys[0])
    for mky in monkeys:
        df = df.append(get_mky_drinking(mky))

    # Dummy DC
    df = pd.concat([df, pd.get_dummies(df.dc)], axis=1)

    return df

def regress(df, atrrs):
    clf = RandomForestRegressor()
    x = df[atrrs]
    y = df['etoh_next']
    clf.fit(x, y)
    print 'Feature importances: %s' % ['%s: %.3f' % (f, fi) for f, fi in zip(x, clf.feature_importances_)]
    print 'R^2 (coefficient of determination): %.3f' % clf.score(x, y)

# df = combine_mkys_drinking()
# df.save('bec_etoh_next.plk')
df = pd.read_pickle('bec_etoh_next.plk')

print df
regress(df, ['etoh'])
regress(df, ['etoh', 'over2std', 'over1std'])
regress(df, ['etoh', 'over2std', 'over1std', 'sex'])
regress(df, ['etoh', 'over2std', 'over1std', 'sex', 'LD', 'BD', 'HD', 'VHD'])

print '\n\n------BEC-------\n'
regress(df, ['bec'])
regress(df, ['bec', 'over2std', 'over1std'])
regress(df, ['bec', 'over2std', 'over1std', 'sex'])
regress(df, ['bec', 'over2std', 'over1std', 'sex', 'LD', 'BD', 'HD', 'VHD'])