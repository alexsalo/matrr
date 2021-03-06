from pfd_common import *

FIRST_N_MINUTES = 10
TEMP_FEATURES, TEMP_FEATURES_CSV, TEMP_MEDIANS = 'temp_features.plk', 'temp_features.csv', 'temp_medians.csv'
SEX, UNSEX = {'F': 0, 'M': 1}, {0: 'Female', 1: 'Male'}
LIGHT = 'Non-heavy'
HEAVY = 'Heavy'
MTD = 'mtd_'
BEHAVIOR_ATTRIBUTES = {
    'seconds_to_stageone': 'Seconds to finish\nEtOH allotment',
    'latency_1st_drink': 'Latency to\nfirst EtOH drink',
    'etoh_bout': 'Total EtOH bouts',
    'etoh_drink_bout': 'Average number of\nEtOH drinks per bout',
    'etoh_mean_drink_length': 'Mean length\nof EtOH drinks',
    'etoh_median_idi': 'Median time\nbetween EtOH drinks',
    'etoh_mean_drink_vol': 'Mean volume\nof EtOH drinks',
    'etoh_mean_bout_length': 'Mean length\nof EtOH bouts',
    'pct_etoh_in_1st_bout': '% days all EtOH\nconsumed in the first bout',
    'drinks_1st_bout': 'Number of EtOH drinks\nin the first EtOH bout',
    'max_bout': 'Sequence number\nof the max EtOH bout',
    'max_bout_length': 'Length of max EtOH bout',
    'pct_max_bout_vol_total_etoh': 'Max EtOH bout volume\nas % of day total'
}
ANIMAL_ATTRIBUTES = {'mky_id': 'Animal ID',
                     'cohort__coh_cohort_id': 'Cohort',
                     'mky_gender': 'Sex',
                     'mky_drinking_category': 'Drinking Category',
                     'mky_days_at_etoh_induction': 'Age of EtOH\ninduction (days)'
                     }
COHORT_NAMES = map(lambda x: 'INIA Rhesus ' + x, ['10', '4', '5', '6a', '6b', '7a', '7b'])


def generate_data():
    ml_monkeys = Monkey.objects.filter(cohort__in=Cohort.objects.filter(coh_cohort_name__in=COHORT_NAMES))\
                               .exclude(mky_drinking_category=None)
    animals_df = pd.DataFrame(list(ml_monkeys.values_list(*ANIMAL_ATTRIBUTES.keys())),
                              columns=ANIMAL_ATTRIBUTES.values()).set_index('Animal ID')
    animals_df['Sex'] = map(lambda x: SEX[x], animals_df['Sex'])
    behavior_df = pd.DataFrame(
        list(MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().
             filter(monkey__in=ml_monkeys).
             order_by('monkey__mky_id', 'drinking_experiment__dex_date').
             values_list(*(['monkey__mky_id', 'mtd_etoh_g_kg'] + map(lambda x: MTD + x, BEHAVIOR_ATTRIBUTES.keys())))),
        columns=['Animal ID', 'etoh_g_kg'] + BEHAVIOR_ATTRIBUTES.keys())

    behavior_df['etoh_g_kg'] = behavior_df['etoh_g_kg'].round(1)

    # add splitting by epoch
    behavior_df['p3_epoch'] = ''
    for mky_id in behavior_df['Animal ID'].unique():
        p3_epoch_len = len(behavior_df[behavior_df['etoh_g_kg'] == 1.50][behavior_df['Animal ID'] == mky_id]) / 3
        epoch = behavior_df.ix[(behavior_df['Animal ID'] == mky_id) & (behavior_df['etoh_g_kg'] == 1.50), 'p3_epoch']
        epoch[:p3_epoch_len] = 'e1'
        epoch[p3_epoch_len:2*p3_epoch_len] = 'e2'
        epoch[2*p3_epoch_len:] = 'e3'
        behavior_df.ix[(behavior_df['Animal ID'] == mky_id) & (behavior_df['etoh_g_kg'] == 1.50), 'p3_epoch'] = epoch

    # Get medians for each of the three stages (doses); for 3 epochs in P3
    median1 = behavior_df[behavior_df['etoh_g_kg'] == 0.50].groupby('Animal ID').median().drop('etoh_g_kg', axis=1)
    median2 = behavior_df[behavior_df['etoh_g_kg'] == 1].groupby('Animal ID').median().drop('etoh_g_kg', axis=1)
    median3 = behavior_df[behavior_df['etoh_g_kg'] == 1.50].groupby('Animal ID').median().drop('etoh_g_kg', axis=1)

    median_e1 = behavior_df[behavior_df['p3_epoch'] == 'e1'].groupby('Animal ID').median().drop('etoh_g_kg', axis=1)
    median_e2 = behavior_df[behavior_df['p3_epoch'] == 'e2'].groupby('Animal ID').median().drop('etoh_g_kg', axis=1)
    median_e3 = behavior_df[behavior_df['p3_epoch'] == 'e3'].groupby('Animal ID').median().drop('etoh_g_kg', axis=1)

    # # Edit columns, combine and save the medians to csv
    # median1.columns = map(lambda x: x + '_m1', median1.columns)
    # median2.columns = map(lambda x: x + '_m2', median2.columns)
    # median3.columns = map(lambda x: x + '_m3', median3.columns)
    # mediansdf = pd.concat([animals_df, median1, median2, median3], axis=1, verify_integrity=True)
    # mediansdf.to_csv(TEMP_MEDIANS)

    # Calculate log of deltas and update column names
    delta1 = np.log(median2 / median1)
    delta2 = np.log(median3 / median2)
    deltat = np.log(median3 / median1)

    delta1.columns = map(lambda x: x + '_d1', delta1.columns)
    delta2.columns = map(lambda x: x + '_d2', delta2.columns)
    deltat.columns = map(lambda x: x + '_dt', deltat.columns)

    delta_e1 = np.log(median_e2 / median_e1)
    delta_e2 = np.log(median_e3 / median_e2)
    delta_et = np.log(median_e3 / median_e1)

    delta_e1.columns = map(lambda x: x + '_e1', delta_e1.columns)
    delta_e2.columns = map(lambda x: x + '_e2', delta_e2.columns)
    delta_et.columns = map(lambda x: x + '_et', delta_et.columns)

    # Concat all together and save
    result = pd.concat([animals_df, delta1, delta2, deltat, delta_e1, delta_e2, delta_et], axis=1, verify_integrity=True)
    # result = pd.concat([animals_df, delta_e1, delta_e2, delta_et], axis=1, verify_integrity=True)

    result.save(TEMP_FEATURES)
    result.to_csv(TEMP_FEATURES_CSV)
    return result
# generate_data()


def get_features(regenerate=False):
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

    ld_bd = df.loc[df['Drinking Category'].isin(['LD', 'BD'])]
    hd_vhd = df.loc[df['Drinking Category'].isin(['HD', 'VHD'])]

    df.ix[df['Drinking Category'].isin(['LD', 'BD']), 'Drinking Category'] = LIGHT
    df.ix[df['Drinking Category'].isin(['HD', 'VHD']), 'Drinking Category'] = HEAVY

    return df, ld_bd, hd_vhd


# data_low_heavy, data_ld_bd, data_hd_vhd = get_fold_subdivide_features(regenerate=True)
# print data_low_heavy.columns
# print map(lambda x: len(x), [data_low_heavy, data_ld_bd, data_hd_vhd])
# print len(data_low_heavy[data_low_heavy.sex == 1])
