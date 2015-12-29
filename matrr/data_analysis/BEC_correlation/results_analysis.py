__author__ = 'alex'
from common import *
from data_generation import get_bec_df_for_all_animals


def compile_bec_correlation_table(schedule, split_by, label_group1, label_group2):
    bec_df_all, bec_df_group_1, bec_df_group_2 = get_bec_df_for_all_animals(schedule, split_by, regenerate=False)

    colnames = ['before_' + label_group1, 'before_' + label_group2, 'before_all',
                'day_of_' + label_group1, 'day_of_' + label_group2, 'day_of_all',
                'next_' + label_group1, 'next_' + label_group2, 'next_all']
    corrs_df = pd.DataFrame(index=colnames)

    drinking_categories = ['LD', 'BD', 'HD', 'VHD']
    for i, dc in enumerate(drinking_categories):
        bec_dc_all = bec_df_all[bec_df_all.dc == dc]
        bec_dc_group_1 = bec_df_group_1[bec_df_group_1.dc == dc]
        bec_dc_group_2 = bec_df_group_2[bec_df_group_2.dc == dc]

        corrs_df[dc] = [
            np.round(bec_dc_group_1.etoh_previos_day.corr(bec_dc_group_1.bec), 4),
            np.round(bec_dc_group_2.etoh_previos_day.corr(bec_dc_group_2.bec), 4),
            np.round(bec_dc_all.etoh_previos_day.corr(bec_dc_all.bec), 4),

            np.round(bec_dc_group_1.etoh_at_bec_sample_time.corr(bec_dc_group_1.bec), 4),
            np.round(bec_dc_group_2.etoh_at_bec_sample_time.corr(bec_dc_group_2.bec), 4),
            np.round(bec_dc_all.etoh_at_bec_sample_time.corr(bec_dc_all.bec), 4),

            np.round(bec_dc_group_1.etoh_next_day.corr(bec_dc_group_1.bec), 4),
            np.round(bec_dc_group_2.etoh_next_day.corr(bec_dc_group_2.bec), 4),
            np.round(bec_dc_all.etoh_next_day.corr(bec_dc_all.bec), 4),
        ]
    print '\n' + schedule
    print corrs_df
def compile_all_bec_corr_tables():
    for schedule in ['22hr', 'daylight']:
        for split_by, less, over in zip(['bec_mgpct', 'bec_over2stdev'],
                                        ['<80', '<2std'], ['>=80', '>std']):
            compile_bec_correlation_table(schedule, split_by, less, over)
compile_all_bec_corr_tables()