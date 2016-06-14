import matplotlib
import math
import pandas as pd
from matplotlib import pyplot as plt
from pfd_get_data import get_fold_subdivide_features, get_features, \
    UNSEX, BEHAVIOR_ATTRIBUTES, ANIMAL_ATTRIBUTES, LIGHT, HEAVY
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble.partial_dependence import plot_partial_dependence

FIG_SIZE = (16, 10)
TALL_FIG_SIZE = (12, 10)
PDP_FIG_SIZE = (12, 14)
PDF_DPI, PNG_DPI = 600, 100
DELTA, DELTA1, DELTA2, DELTAT = '$\Delta$', '$\Delta_1$', '$\Delta_2$', '$\Delta_t$'
DELTA_E1, DELTA_E2, DELTA_ET = '$\Delta_{p3e1}$', '$\Delta_{p3e2}$', '$\Delta_{p3et}$'
D_DELTA = {'_d1': DELTA1, '_d2': DELTA2, '_dt': DELTAT, '_e1': DELTA_E1, '_e2': DELTA_E2, '_et': DELTA_ET}
WD = '/home/alex/Dropbox/matrr_predicting_drinkers/'

# FEATURES_LIGHT_HEAVY = ['Age of EtOH\ninduction (days)', 'Sex', 'etoh_bout_d2', 'max_bout_d2', 'latency_1st_drink_dt']
#
# FEATURES_LD_BD = ['etoh_mean_drink_length_d2', 'latency_1st_drink_d2', 'etoh_drink_bout_d2']
# FEATURES_HD_VHD = ['pct_max_bout_vol_total_etoh_d2', 'max_bout_length_d1', 'etoh_median_idi_dt', 'drinks_1st_bout_d1']


FEATURES_LIGHT_HEAVY = ['Age of EtOH\ninduction (days)', 'Sex', 'etoh_median_idi_d2', 'max_bout_e1', 'latency_1st_drink_e2']
FEATURES_LD_BD = ['etoh_mean_drink_length_d2', 'latency_1st_drink_d2', 'etoh_bout_dt', 'etoh_mean_drink_length_dt']
FEATURES_HD_VHD = ['etoh_bout_e1', 'etoh_bout_et', 'etoh_drink_bout_et', 'etoh_mean_drink_vol_d1', 'etoh_mean_drink_length_d1']

WHICH_FEATURES = {'Heavy vs. Not Heavy': FEATURES_LIGHT_HEAVY,
                  'LD vs. BD': FEATURES_LD_BD,
                  'HD vs. VHD': FEATURES_HD_VHD}

matplotlib.rcParams.update({'font.size': 16})
matplotlib.rcParams['savefig.directory'] = '/home/alex/Dropbox/matrr_predicting_drinkers/dev_images'

data_low_heavy, data_ld_bd, data_hd_vhd = get_fold_subdivide_features(regenerate=False)
data = get_features()

WHICH_DF = {'Heavy vs. Not Heavy': data_low_heavy,
            'LD vs. BD': data_ld_bd,
            'HD vs. VHD': data_hd_vhd}
HIGHLIGHT_IMPORTANT = {DELTA1: (-0.45, 0.45),
                       DELTA2: (0.55, 1.45),
                       DELTAT: (1.55, 2.45),
                       DELTA_E1: (2.55, 3.45),
                       DELTA_E2: (3.55, 4.45),
                       DELTA_ET: (4.55, 5.45)}


def plot_deltas_for_feature(df, feature):
    fig, axs = plt.subplots(1, 2, facecolor='w', edgecolor='k', figsize=FIG_SIZE)
    axs = axs.ravel()

    which_axis = {LIGHT: 0, HEAVY: 1}
    # which_color = {LIGHT: 'g-o', HEAVY: 'r-o'}
    all_values = df[[feature + '_d1', feature + '_d2']]
    ylim = (min(all_values.min()) - 0.1, max(all_values.max()) + 0.1)
    slope_range = ylim[1] - ylim[0]

    for mky_id, mky_row in df.iterrows():
        dc = mky_row['Drinking Category']
        v1, v2 = mky_row[feature + '_d1'], mky_row[feature + '_d2']
        intensity = 0.5 + (v2 - v1) / (2 * slope_range)
        axs[which_axis[dc]].plot([1, 2], [v1, v2],
                                 ls='-', marker='o', lw=2, color=[intensity, 0.36, 0.36])

    for ax in axs:
        ax.set_xlim(0.9, 2.1)
        ax.set_ylim(ylim)
        ax.set_xticklabels(['', DELTA1, '', '', '', '', DELTA2])
        ax.set_xlabel('Time (Relative Delta)')
        ax.set_ylabel('Log(' + DELTA + ')')

    [axs[which_axis[x]].set_title(x) for x in which_axis.keys()]
    plt.suptitle('%s: relative deltas change during induction' % BEHAVIOR_ATTRIBUTES[feature])
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    return fig


def generate_plot_deltas_for_feature(df, func, save_path):
    for feature in BEHAVIOR_ATTRIBUTES.keys():
        fig = func(df, feature=feature)
        fig.savefig(save_path + 'delta_change_' + feature + '.png', dpi=PNG_DPI, format='png')


# plot_deltas_for_feature(data_low_heavy, 'etoh_bout')
# generate_plot_deltas_for_feature(data_low_heavy, plot_deltas_for_feature,
#          '/home/alex/Dropbox/matrr_predicting_drinkers/dev_images/deltas/')
# generate_plot_deltas_for_feature(data_low_heavy,'/home/alex/Dropbox/matrr_predicting_drinkers/dev_images/deltas_col/')


def violin_deltas(df, feature, save_path=None):
    import seaborn as sns
    sns.set(font_scale=1.5)
    sns.set_style('whitegrid')
    df = df[['Sex', 'Drinking Category', feature + '_d1', feature + '_d2']]
    df.columns = ['Sex', 'Drinking Category', DELTA1, DELTA2]
    # feat_name = BEHAVIOR_ATTRIBUTES[feature]
    # df.columns
    df.Sex = [UNSEX[s] for s in df.Sex]
    df_long = pd.melt(df, id_vars=['Sex', 'Drinking Category'],
                      value_vars=[DELTA1, DELTA2], var_name='Stage', value_name=DELTA)
    #plt.figure(figsize=(10, 10))
    # sns.violinplot(data=df_long, x='Sex', y=DELTA, hue='Stage', palette='Set2', scale='count', bw=.2)

    # sns.violinplot(data=df_long, x='Drinking Category', y=DELTA, hue='Stage', palette='Set2', scale='count', bw=.2)
    g = sns.FacetGrid(df_long, col='Sex', size=10, aspect=.7)
    g.map(sns.violinplot, 'Drinking Category', DELTA, 'Stage', bw=.3, palette='Set2').\
        despine(left=True).add_legend(title='Stage')
    plt.suptitle('Delta change in %s by gender' % BEHAVIOR_ATTRIBUTES[feature])
    plt.subplots_adjust(top=0.92)

    if save_path is not None:
        fname = feature + '_' + '_'.join(df['Drinking Category'].unique())
        g.savefig(save_path + fname + '.png', dpi=PNG_DPI, format='png')
        g.savefig(save_path + fname + '.pdf', dpi=PDF_DPI, format='pdf')
# # For LD vs VHD plot
# data = data[data['Drinking Category'].isin(['LD', 'VHD'])]
# violin_deltas(data, 'etoh_mean_drink_length')

# for feature in BEHAVIOR_ATTRIBUTES.keys():
#     violin_deltas(data, feature, save_path=WD + 'dev_images/deltas_violins_by_gender/ld_vhd/')
#     violin_deltas(data_low_heavy, feature, save_path=WD + 'dev_images/deltas_violins_by_gender/heavy_light/')


def violin_deltas_total_only(df, feature, save_path=None):
    import seaborn as sns
    sns.set(font_scale=1.5)
    sns.set_style('whitegrid')
    df = df[['Sex', 'Drinking Category', feature + '_dt']]
    df.columns = ['Sex', 'Drinking Category', DELTAT]
    df.Sex = [UNSEX[s] for s in df.Sex]
    fig = plt.figure(figsize=(10, 10))
    sns.violinplot(data=df, x='Sex', y=DELTAT, hue='Drinking Category', palette='Set2', scale='count', bw=.2)
    plt.suptitle('Delta change in %s by gender' % BEHAVIOR_ATTRIBUTES[feature])
    plt.subplots_adjust(top=0.92)

    if save_path is not None:
        fname = feature + '_' + '_'.join(df['Drinking Category'].unique())
        fig.savefig(save_path + fname + '.png', dpi=PNG_DPI, format='png')
        fig.savefig(save_path + fname + '.pdf', dpi=PDF_DPI, format='pdf')
# # For LD vs VHD plot
# data = data[data['Drinking Category'].isin(['LD', 'VHD'])]
# violin_deltas_total_only(data, 'etoh_mean_drink_length')

# data = data[data['Drinking Category'].isin(['LD', 'VHD'])]
# for feature in BEHAVIOR_ATTRIBUTES.keys():
#     violin_deltas_total_only(data, feature, save_path=WD + 'dev_images/deltas_violins_by_gender_totals_only/ld_vhd/')
#     violin_deltas_total_only(data_low_heavy, feature,
#                              save_path=WD + 'dev_images/deltas_violins_by_gender_totals_only/heavy_light/')


def plot_deltas_boxplots_for_feature(df, feature, ax=None, highlight_which=None):
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=FIG_SIZE, facecolor='w', edgecolor='k')
    import seaborn as sns
    sns.set(font_scale=1.2)
    df['MID'] = df.index
    print df[df.MID==10074]
    f_df = df[['MID', 'Drinking Category', feature + '_d1', feature + '_d2', feature + '_dt', feature + '_e1', feature + '_e2', feature + '_et']]
    f_df.columns = ['MID', 'Drinking Category', DELTA1, DELTA2, DELTAT, DELTA_E1, DELTA_E2, DELTA_ET]
    df_long = pd.melt(f_df, id_vars=['MID', 'Drinking Category'],
                      value_vars=[DELTA1, DELTA2, DELTAT, DELTA_E1, DELTA_E2, DELTA_ET], var_name='Stage', value_name=DELTA)
    # Reorder categorical in pandas
    # df_long['Drinking Category'] = df_long['Drinking Category'].astype('category').cat.set_categories([LIGHT, HEAVY])
    sns.boxplot(data=df_long, x='Stage', y=DELTA, hue='Drinking Category', ax=ax)
    ax.legend(loc='upper left')
    ax.grid()
    ax.set_title(BEHAVIOR_ATTRIBUTES[feature])

    if highlight_which:
        x0, x1 = HIGHLIGHT_IMPORTANT[highlight_which]
        ax.axvspan(x0, x1, color='red', alpha=.15, zorder=-100, transform=ax.transAxes)

    # # deal with heavy vs non heavy max bout sequence number annotation
    # if HEAVY in df['Drinking Category'].unique() and feature == 'max_bout':
    #     dist = 0.07
    #     for x in [0.17, 0.5, 0.83]:
    #         ax.text(x - dist, 0.01, HEAVY, transform=ax.transAxes, horizontalalignment='center')
    #         ax.text(x + dist, 0.01, LIGHT, transform=ax.transAxes, horizontalalignment='center')

    # # T-test
    # dcs = f_df['Drinking Category'].unique()
    # import scipy
    # for x_pos, d in zip([0.18, 0.5, 0.82], [DELTA1, DELTA2, DELTAT]):
    #     a = f_df[f_df['Drinking Category'] == dcs[0]][d]
    #     b = f_df[f_df['Drinking Category'] == dcs[1]][d]
    #     if HEAVY in dcs:
    #         z, p = scipy.stats.mannwhitneyu(a, b)
    #     else:
    #         z, p = scipy.stats.ttest_ind(a, b, equal_var=False)
    #     ax.text(x_pos, 0.02, 'p=%.3f' % p, transform=ax.transAxes,
    #             horizontalalignment='center', fontsize=16)
#plot_deltas_boxplots_for_feature(data_low_heavy, 'etoh_bout')
#data_low_heavy.boxplot(column='etoh_bout_d1', by='Drinking Category')
#plt.show()


def plot_deltas_boxplots_multiple_features(step, highlight_important=False, save_path=None):
    def uniq(input):
        output = []
        for x in input:
            if x not in output:
                output.append(x)
        return output

    df, features = WHICH_DF[step], WHICH_FEATURES[step]

    # only behavioral features - animal's attributes don't change
    highlight_which = [D_DELTA[f[-3:]] for f in features if f not in ANIMAL_ATTRIBUTES.values()]
    features = [f[:-3] for f in features if f not in ANIMAL_ATTRIBUTES.values()]
    features = uniq(features)  # to remove duplicates
    fig, axs = plt.subplots(int(math.ceil(len(features) / 2.0)), 2, figsize=FIG_SIZE)
    axs = axs.ravel()
    for i, f in enumerate(features):
        plot_deltas_boxplots_for_feature(df, f, axs[i], highlight_which[i])
    plt.suptitle('Behavioral features that classify\n%s' % step)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    if len(features) % 2 == 1:  # clear the last ax if there is no data
        fig.delaxes(axs[len(features)])
        plt.draw()

    # axs[3].set_ylim((-1.8, 1.1))  # for HD vs VHD

    if save_path is not None:
        fig.savefig(save_path + step.lower().replace(' ', '_').replace('.', '') + '.png', dpi=PNG_DPI, format='png')
        fig.savefig(save_path + step.lower().replace(' ', '_').replace('.', '') + '.pdf', dpi=PDF_DPI, format='pdf')


# plot_deltas_boxplots_multiple_features('Heavy vs. Not Heavy', highlight_important=True,
#                                        save_path=WD+'dev_images/deltas_boxplots/')

# plot_deltas_boxplots_multiple_features('HD vs. VHD', True, save_path=WD+'dev_images/deltas_boxplots/')

# plot_deltas_boxplots_multiple_features('LD vs. BD', save_path=WD+'dev_images/deltas_boxplots/')
# plt.show()

# ================= PARTIAL DEPENDENCIES ================
def create_pdp(df, target, deltas):
    x = df[deltas]
    y = df['Drinking Category']
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                     learning_rate=0.1, random_state=1)
    clf.fit(x, y)

    x.columns = [BEHAVIOR_ATTRIBUTES[f[:-3]] + ' ' + D_DELTA[f[-3:]] for f in deltas]
    fig, ax = plot_partial_dependence(clf, x, range(len(deltas)), label=target, feature_names=x.columns,
                                      figsize=FIG_SIZE)
    plt.suptitle('Partial Dependence on Becoming ' + target)

    plt.tight_layout()
    fig.subplots_adjust(top=0.93)


def create_pdp_grid(step, target, save_path=None):
    matplotlib.rcParams.update({'font.size': 12})
    df = WHICH_DF[step]
    x, y = df[WHICH_FEATURES[step]], df['Drinking Category']

    print x.columns
    if 'etoh_bout_e1' in x.columns:
        x.drop('etoh_bout_e1', axis=1, inplace=True)
    print x.columns

    if 'Sex' in x.columns:
        x = x.drop('Sex', axis=1)
    n = len(x.columns)
    if 'Age of EtOH\ninduction (days)' in x.columns:
        x['Age of EtOH\ninduction (days)'] /= 365
    columns = []
    for i, f in enumerate(x.columns):
        f = f.replace('days', 'years')
        if '_d' in f or '_e' in f:
            columns.append(BEHAVIOR_ATTRIBUTES[f[:-3]] + ' ' + D_DELTA[f[-3:]])
        else:
            columns.append(f)
    x.columns = columns

    clf = GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                     learning_rate=0.1, random_state=1)
    clf.fit(x, y)

    layout = []
    for i in xrange(n):
        for j in xrange(n):
            if i == j:
                layout.append(i)
            else:
                layout.append((j, i))

    fig, axs = plot_partial_dependence(clf, x, layout, label=target, feature_names=x.columns,
                                       figsize=PDP_FIG_SIZE, n_cols=n)

    plt.suptitle('Partial dependence grid: likelihood of becoming ' + target)
    [axs[i].set_ylabel('') for i in range(n*n) if i not in range(0, n*n, n)]   # no ylabel except left column
    axs[0].set_ylabel(columns[0])
    [axs[i].set_xlabel('') for i in range(n*n - n)]                            # no xlabel except last row
    [axs[i].text(0.5, 0.91, 'Partial dependence', transform=axs[i].transAxes,
                 horizontalalignment='center') for i in range(0, n*n, n + 1)]  # diagonal label
    plt.tight_layout()
    fig.subplots_adjust(top=0.955, hspace=0.1, wspace=0.14)

    if save_path is not None:
        fname = '_'.join(x.columns).lower().replace(' ', '_').replace('\\', '').replace('$', '').replace('{', '').replace('}', '').replace('\n', '')
        fig.savefig(save_path + fname + '.png', dpi=PNG_DPI, format='png')
        fig.savefig(save_path + fname + '.pdf', dpi=PDF_DPI, format='pdf')


# create_pdp_grid('Heavy vs. Not Heavy', target=HEAVY, save_path=WD+'dev_images/pdp_grids/light_heavy/')
# create_pdp_grid('LD vs. BD', target='LD', save_path=WD+'dev_images/pdp_grids/ld_bd/')
# create_pdp_grid('HD vs. VHD', target='VHD', save_path=WD+'dev_images/pdp_grids/hd_vhd/')
# print_full(data_hd_vhd)
plt.show()

#heavyf = [f for f in FEATURES_LIGHT_HEAVY if f not in ['Sex']]  # , 'max_bout_d2', 'Age at intoxication (days)']]
# heavy_p1 = heavyf[:3]
# heavy_p2 = heavyf[3:]
#create_pdp_grid(data_low_heavy, target=HEAVY, deltas=heavyf, save_path=WD+'dev_images/pdp_grids/light_heavy/')
# create_pdp_grid(data_low_heavy, target=HEAVY, deltas=heavy_p1, save_path=WD+'dev_images/pdp_grids/light_heavy/')
# create_pdp_grid(data_low_heavy, target=HEAVY, deltas=heavy_p2, save_path=WD+'dev_images/pdp_grids/light_heavy/')


def print_selected_features():
    print '\nHeavy light\n-------------------'
    for f in FEATURES_LIGHT_HEAVY:
        if f[:-3] in BEHAVIOR_ATTRIBUTES:
            print BEHAVIOR_ATTRIBUTES[f[:-3]]
        else:
            print f

    print '\nLD_BD\n-------------------'
    for f in FEATURES_LD_BD:
        if f[:-3] in BEHAVIOR_ATTRIBUTES:
            print BEHAVIOR_ATTRIBUTES[f[:-3]]
        else:
            print f

    print '\nHD VHD\n-------------------'
    for f in FEATURES_HD_VHD:
        if f[:-3] in BEHAVIOR_ATTRIBUTES:
            print BEHAVIOR_ATTRIBUTES[f[:-3]]
        else:
            print f
# print_selected_features()

#plt.show()
