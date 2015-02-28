__author__ = 'alex'
from header import *

features_monkey = ["mky_id", "mky_gender", "mky_age_at_intox", "mky_drinking_category"]

features_names_perstage = [
    'mtd_seconds_to_stageone', #Seconds it took for monkey to reach day's ethanol allotment
    'mtd_latency_1st_drink', #Time from session start to first etOH consumption
    'mtd_etoh_bout', #Total etOH bouts (less than 300 seconds between consumption of etOH)
    'mtd_etoh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of etOH) per etOH bout
    'mtd_veh_bout', #Total H20 bouts (less than 300 seconds between consumption of H20)
    'mtd_veh_drink_bout', #Average number of drinks (less than 5 seconds between consumption of H20) per H20 bout
    'mtd_etoh_mean_drink_length', #Mean length for ethanol drinks (less than 5 seconds between consumption of etOH is a continuous drink
    'mtd_etoh_median_idi', #Median time between drinks (always at least 5 seconds because 5 seconds between consumption defines a new drink
    'mtd_etoh_mean_drink_vol', #Mean volume of etOH drinks
    'mtd_etoh_mean_bout_length',
    'mtd_etoh_media_ibi', #Median inter-bout interval (always at least 300 seconds, because 300 seconds between consumption defines a new bout)
    'mtd_pct_etoh_in_1st_bout', #Percentage of the days total etOH consumed in the first bout
    'mtd_drinks_1st_bout', #Number of drinks in the first bout
    'mtd_max_bout', #Number of the bout with maximum ethanol consumption
    'mtd_max_bout_length', #Length of maximum bout (bout with largest ethanol consumption)
    'mtd_pct_max_bout_vol_total_etoh', #Maximum bout volume as a percentage of total ethanol consumed that day
    #derive somethin by perhour drinks - mornin drinking?
    #maybe get medians and register related change? so instead of 3 features we have 2: delta_1, delta_2?
    ]

##Define Cohorts and Monkeys##
def get_monkeys():
    cohort_names = ["INIA Rhesus 4", "INIA Rhesus 5", "INIA Rhesus 6a", "INIA Rhesus 7b",
        "INIA Rhesus 6b", "INIA Rhesus 7a"]
    ml_cohorts = Cohort.objects.filter(coh_cohort_name__in = cohort_names)
    ml_monkeys = Monkey.objects.filter(cohort__in = ml_cohorts).exclude(mky_drinking_category = None)
    return ml_monkeys

def median_value_per_stage_for_monkeys(monkeys, mtds_all, value_name, GKG_DELTA_EPSILON=0.4):
    medians = pd.DataFrame(columns=["mky_id", value_name+"_1", value_name+"_2", value_name+"_3", value_name+"_total"])
    for index, m in enumerate(monkeys):
        mtds = mtds_all.filter(monkey = m).order_by('drinking_experiment__dex_date')
        values_df = pd.DataFrame(list(mtds.values_list('mtd_etoh_g_kg', value_name)))
        values_df.columns = ['etoh', 'value']

        # split on 3 parts by etoh_gkg
        tp0, tp1, tp2 = 1, 1, 1

        if m.mky_id in anomalies_mtds_ids:
            tp0, tp1, tp2 = 55, 84, 115
        else:
            for i in range(20, values_df.etoh.size - 20):
                if values_df.etoh[i] > (values_df.etoh[i-1] + GKG_DELTA_EPSILON):
                    if tp1 == 1:
                        tp1 = i-1
                    else:
                        tp2 = i-1
        #if some problems - use total median
        if values_df.value[tp0:tp1].median() < 0:
            total_medain = values_df.value.median()
            medians.ix[m.mky_id] = [total_medain, total_medain, total_medain, total_medain]
        #if all good - assign valid medians by stage
        else:
            medians.loc[index] = [m.mky_id,
                                values_df.value[tp0:tp1].median(),
                                values_df.value[tp1:tp2].median(),
                                values_df.value[tp2:].median(),
                                values_df.value[tp0:].median()]
    medians.set_index("mky_id", inplace=True)
    return medians

def prepare_features(ml_monkeys):
    data = ml_monkeys.values_list(*features_monkey)
    df = pd.DataFrame(list(data), columns=features_monkey)
    df = df.set_index("mky_id")
    df.mky_gender = (df.mky_gender == 'M').astype(int)
    df = df.sort_index()

    mtds_all = MonkeyToDrinkingExperiment.objects.Ind().exclude_exceptions().filter(monkey=ml_monkeys)

    #get medians
    for feature in features_names_perstage:
        medians = median_value_per_stage_for_monkeys(ml_monkeys, mtds_all, feature)
        df = pd.concat([df, medians], axis=1)

    return df

def get_features(generate=True):
    if generate:
        ml_monkeys = get_monkeys()
        features = prepare_features(ml_monkeys)
        features.save('features_set.pkl')
    else:
        features = pd.read_pickle('features_set.pkl')
    return features

def plot_feature_meds_by_stage(feature):
    fig = plt.figure(1, figsize=(10,10))
    plt.clf() #clear the plot
    plt.xlim(-0.2, 2.2)
    for id in features.index:
        plt.plot(features.loc[id,[feature+"_1", feature+"_2", feature+"_3"]], dc_colors_ol[features.loc[id,["mky_drinking_category"]][0]])
    plt.title(feature+"_medians_by_stage")
    return fig

def save_plot_feature_meds_by_stage():
    for feature in features_names_perstage:
        fig = plot_feature_meds_by_stage(feature)
        path = '/home/alex/MATRR/feature_medians_by_stage/'
        plotname = 'medians_by_stage' + feature + '.png'
        fig.savefig(os.path.join(path, plotname), dpi=100)
#save_plot_feature_meds_by_stage()

features = get_features(False)
print features





#pylab.show()