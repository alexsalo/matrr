from pfd_common import *

FIRST_N_MINUTES = 10
TEMP_FEATURES = 'temp_features.plk'
SEX = {'F': 0, 'M': 1}
HEAVY = 'heavy'
LIGHT = 'light'
BEHAVIOR_ATTRIBUTES = [
    'mtd_seconds_to_stageone',     # Seconds it took for monkey to reach day's ethanol allotment
    'mtd_latency_1st_drink',       # Time from session start to first etOH consumption
    'mtd_etoh_bout',               # Total etOH bouts (less than 300 seconds between consumption of etOH)
    'mtd_etoh_drink_bout',         # Average number of drinks (less than 5 seconds between consumption of etOH)
                                   # per etOH bout
    # 'mtd_veh_bout', #Total H20 bouts (less than 300 seconds between consumption of H20)
    # 'mtd_veh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of H20) per H20 bout
    'mtd_etoh_mean_drink_length',  # Mean length for ethanol drinks (less than 5 seconds between consumption
                                   # of etOH is a continuous drink
    'mtd_etoh_median_idi',         # Median time between drinks (always at least 5 seconds because 5 seconds
                                   # between consumption defines a new drink
    'mtd_etoh_mean_drink_vol',     # Mean volume of etOH drinks
    'mtd_etoh_mean_bout_length',
    'mtd_pct_etoh_in_1st_bout',    # Percentage of the days total etOH consumed in the first bout
    'mtd_drinks_1st_bout',         # Number of drinks in the first bout
    'mtd_max_bout',                # Number of the bout with maximum ethanol consumption
    'mtd_max_bout_length',         # Length of maximum bout (bout with largest ethanol consumption)
    'mtd_pct_max_bout_vol_total_etoh',  # Maximum bout volume as a percentage of total ethanol consumed that day
    ]
ANIMAL_ATTRIBUTES = {'mky_id': 'mky_id',
                     'cohort__coh_cohort_id': 'coh',
                     'mky_gender': 'sex',
                     'mky_age_at_intox': 'intox',
                     'mky_drinking_category': 'dc',
                     'mky_days_at_necropsy': 'age_at_necropsy'
                     }
COHORT_NAMES = map(lambda x: 'INIA Rhesus ' + x, ['10', '4', '5', '6a', '6b', '7a', '7b'])


def generate_data():
    ml_monkeys = Monkey.objects.filter(cohort__in=Cohort.objects.filter(coh_cohort_name__in=COHORT_NAMES))\
                               .exclude(mky_drinking_category=None)
    animals_df = pd.DataFrame(list(ml_monkeys.values_list(*ANIMAL_ATTRIBUTES.keys())),
                              columns=ANIMAL_ATTRIBUTES.values()).set_index('mky_id')
    animals_df.sex = map(lambda x: SEX[x], animals_df.sex)
    behavior_df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().
                                    filter(monkey__in=ml_monkeys).
                                    order_by('monkey__mky_id', 'drinking_experiment__dex_date').
                                    values_list(*(['monkey__mky_id', 'mtd_etoh_g_kg'] + BEHAVIOR_ATTRIBUTES))),
                               columns=['mky_id', 'etoh_g_kg'] + [name[4:] for name in BEHAVIOR_ATTRIBUTES])

    # Get medians for each of the three stages (doses)
    behavior_df['etoh_g_kg'] = behavior_df['etoh_g_kg'].round(1)
    median1 = behavior_df[behavior_df['etoh_g_kg'] == 0.50].groupby('mky_id').median().drop('etoh_g_kg', axis=1)
    median2 = behavior_df[behavior_df['etoh_g_kg'] == 1].groupby('mky_id').median().drop('etoh_g_kg', axis=1)
    median3 = behavior_df[behavior_df['etoh_g_kg'] == 1.50].groupby('mky_id').median().drop('etoh_g_kg', axis=1)

    # Calculate log of deltas and update column names
    delta1 = np.log(median2 / median1)
    delta2 = np.log(median3 / median2)
    delta1.columns = map(lambda x: x + '_d1', delta1.columns)
    delta2.columns = map(lambda x: x + '_d2', delta2.columns)

    # Concat all together and save
    result = pd.concat([animals_df, delta1, delta2], axis=1, verify_integrity=True)
    result.save(TEMP_FEATURES)
    return result


def get_features(regenerate):
    if regenerate:
        df = generate_data()
    else:
        try:
            df = pd.read_pickle(TEMP_FEATURES)
        except IOError:
            print 'Temp file is not found, regenerating..'
            df = generate_data()
    return df


def get_fold_subdivide_features(regenerate):
    df = get_features(regenerate=regenerate)

    ld_bd = df.loc[df['dc'].isin(['LD', 'BD'])]
    hd_vhd = df.loc[df['dc'].isin(['HD', 'VHD'])]

    df.ix[df['dc'].isin(['LD', 'BD']), 'dc'] = HEAVY
    df.ix[df['dc'].isin(['HD', 'VHD']), 'dc'] = LIGHT

    return df, ld_bd, hd_vhd


# data_low_heavy, data_ld_bd, data_hd_vhd = get_fold_subdivide_features(regenerate=False)
# print map(lambda x: len(x), [data_low_heavy, data_ld_bd, data_hd_vhd])
# print len(data_low_heavy[data_low_heavy.sex == 1])
