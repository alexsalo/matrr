import sys
import os
import django
import matplotlib
#import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats
from enum import Enum
from matplotlib import pyplot as plt
from datetime import timedelta

sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
django.setup()

from matrr.models import Cohort, ExperimentBout, ExperimentDrink, Monkey, MonkeyToDrinkingExperiment, CohortEvent

# ==========================CONSTANTS=================================

FEMALES = ['INIA Rhesus 6a', 'INIA Rhesus 6b']
MALES = ['INIA Rhesus 5', 'INIA Rhesus 7a', 'INIA Rhesus 7b']
DURATION = {'oa': 'Open Access',
            'oa_f9mo': 'First 9 Months of OA',
            'oa_l3mo': 'Last 3 Months of OA'}

MKY_ATTR = [
        ('monkey__mky_gender', 'Sex'),
        ('monkey__mky_drinking_category', 'DC'),
        ('monkey__cohort__coh_cohort_id', 'cohort'),
    ]
MTDS_ATRR = [
        ('mtd_etoh_bout', 'Total EtOH bouts'),
        ('mtd_etoh_drink_bout', 'Average number of drinks per bout'),
        ('mtd_etoh_mean_drink_length', 'Average length of EtOH drinks'),
        ('mtd_etoh_median_idi', 'Median time between drinks'),
        ('mtd_etoh_mean_bout_length', 'Average length of EtOH bouts'),
        ('mtd_etoh_media_ibi', 'Median time between bouts'),
        ('mtd_max_bout_length', 'Max Bout Length'),
    ]
ATTRIBUTES = MKY_ATTR + MTDS_ATRR

matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/Matrr/baker_salo/habitual_drinking/'

# ==========================DATA GENERATION=================================
def get_monkeys_mtds(coh_names, duration):
    cohorts = Cohort.objects.filter(coh_cohort_name__in=coh_names)

    if duration == 'oa':
        monkeys = Monkey.objects.filter(cohort__in=cohorts, mky_drinking=True)
        mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey__in=monkeys)

    elif duration == 'oa_f9mo':
        mtds = cohorts[0].get_etoh_mtds(9, 'first')
        for cohort in cohorts[1:]:
             mtds = mtds | cohort.get_etoh_mtds(9, 'first')

    elif duration == 'oa_l3mo':
        mtds = cohorts[0].get_etoh_mtds(3, 'last')
        for cohort in cohorts[1:]:
             mtds = mtds | cohort.get_etoh_mtds(3, 'last')

    return mtds
def get_duration_df(duration):
    def get_population_df(coh_names, duration):
        mtds = get_monkeys_mtds(coh_names, duration)
        return pd.DataFrame(list(mtds.values_list(*[x[0] for x in ATTRIBUTES])),
                            columns=[x[1] for x in ATTRIBUTES])

    df = get_population_df(FEMALES, duration)
    df = df.append(get_population_df(MALES, duration))
    df['Average Drink-to-Bout Length Ratio'] = df['Average length of EtOH drinks'] / df['Average length of EtOH bouts']
    return df

# ====================PLOTTING===================================
def all_mean_drink_vs_bout_plot(coh_names, duration):
    xlim = (-1, 60)
    ylim = (-10, 600)

    mtds = get_monkeys_mtds(coh_names)
    drinks_bouts = pd.DataFrame(list(mtds.values_list('mtd_etoh_mean_drink_length', 'mtd_etoh_mean_bout_length')),
                                columns=['mean_drink_len', 'mean_bout_len'])
    ax = drinks_bouts.plot(kind='hexbin', gridsize=30, x='mean_drink_len', y='mean_bout_len', label='mean drink len vs mean bout len')
    ax.set_title(coh_names)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
#all_mean_drink_vs_bout_plot(FEMALES)

def boxplot_mtd_attributes(duration, df, attr, save=False):
    # Combine DC
    df.ix[(df.DC == 'LD') | (df.DC == 'BD'), 'DC'] = 'LD_BD'
    df.ix[(df.DC == 'HD') | (df.DC == 'VHD'), 'DC'] = 'HD_VHD'

    # N = {'F': len(df[df.Sex == 'F']),
    #      'M': len(df[df.Sex == 'M'])}
    N = {'(F, HD_VHD)': len(df[(df.Sex == 'F') & (df.DC == 'HD_VHD')]),
         '(F, LD_BD)': len(df[(df.Sex == 'F') & (df.DC == 'LD_BD')]),
         '(M, HD_VHD)': len(df[(df.Sex == 'M') & (df.DC == 'HD_VHD')]),
         '(M, LD_BD)': len(df[(df.Sex == 'M') & (df.DC == 'LD_BD')]),
         }
    attr_save_name = attr[0]
    attribute = attr[1]

    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(111)
    df.boxplot(column=attribute, by=['Sex', 'DC'], ax=ax)

    # # Unpaired t-test assuming unequal variances
    # # H0: means are equal
    # a = df[df.Sex == 'F'][attribute][df[df.Sex == 'F'][attribute].notnull()]
    # b = df[df.Sex == 'M'][attribute][df[df.Sex == 'M'][attribute].notnull()]
    # ttest = stats.ttest_ind(a, b, equal_var=False)
    # props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    # text = 'Unpaired t-test\n  H0: $\mu_F = \mu_M$\nt-statistic: %.4f\np-value: %.4f' % ttest
    # ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=14,
    #         verticalalignment='top', bbox=props)

    xlabels = [x.get_text() for x in ax.get_xticklabels()]
    ax.set_xticklabels(['%s\n(N=%s)' % (x, N[x]) for x in xlabels])
    ax.set_xlabel(DURATION[duration])

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    if save:
        path = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/habitual_drinking/ldbd_hdvhd/'
        fig.savefig(path + 'boxplot_ldbd_hdvhd_' + duration + '_' + attr_save_name)
    else:
        plt.show()
        return fig
def create_mtd_attribute_boxplots():
    for duration in DURATION.keys():
        df = get_duration_df(duration)
        MTDS_ATRR.append(('drink_to_bout_ratio', 'Average Drink-to-Bout Length Ratio'))
        for attr in MTDS_ATRR:
            boxplot_mtd_attributes(duration, df, attr, save=True)
# create_mtd_attribute_boxplots()
# boxplot_mtd_attributes(duration='oa_l3mo', df=get_duration_df('oa_l3mo'),
#                        attr=('mtd_max_bout_length', 'Max Bout Length'), save=False)

#========BOXPLOT_COMBINED=========================
MTDS_ATRR.append(('drink_to_bout_ratio', 'Average Drink-to-Bout Length Ratio'))

def combine_dfs_by_dc():
    df_all = get_duration_df('oa')
    df_all['Period'] = DURATION['oa']
    df_f9 = get_duration_df('oa_f9mo')
    df_f9['Period'] = DURATION['oa_f9mo']
    df_l3 = get_duration_df('oa_l3mo')
    df_l3['Period'] = DURATION['oa_l3mo']
    df = pd.concat([df_all, df_f9, df_l3])

    # Combine DC
    df.ix[(df.DC == 'LD') | (df.DC == 'BD'), 'DC'] = 'LD_BD'
    df.ix[(df.DC == 'HD') | (df.DC == 'VHD'), 'DC'] = 'HD_VHD'

    return df

def boxplot_mtd_attributes_all_durations(attr, save=False):
    df = combine_dfs_by_dc()

    attr_save_name = attr[0]
    attribute = attr[1]

    for dc in ['HD_VHD', 'LD_BD']:
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111)

        df_dc = df[df['DC'] == dc]
        df_dc.groupby('Sex').boxplot(column=attribute, ax=ax, by='Period')
        #df_dc.boxplot(column=attribute, ax=ax, by=['Sex', 'Period'])

        fig.suptitle('%s\n%s' % (attribute, dc), fontsize=14)
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)

        if save:
            path = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/habitual_drinking/combined_periods/'
            fig.savefig(path + 'boxplot_combined_' + attr_save_name + '_' + dc)
        else:
            plt.show()
def create_all_attributes_combined_boxplots():
    for attr in MTDS_ATRR:
        boxplot_mtd_attributes_all_durations(attr, save=True)
#create_all_attributes_combined_boxplots()
#boxplot_mtd_attributes_all_durations(('mtd_max_bout_length', 'Max Bout Length'), save=False)


def comb_factor_plot(attr, major, minor, ttest=False, save=False):
    import seaborn as sns
    df = combine_dfs_by_dc()

    attr_save_name = attr[0]
    attribute = attr[1]

    for dc in ['HD_VHD', 'LD_BD']:
        df_dc = df[df['DC'] == dc]

        fig = sns.factorplot(x=major, y=attribute, hue=minor, data=df_dc, kind='box', size=8, aspect=1.5, legend_out=False)
        plt.title('%s\n%s' % (attribute, dc), fontsize=14)
        plt.subplots_adjust(top=0.93)

        if ttest:
            # Unpaired t-test assuming equal variances
            # H0: means are equal for f9mo and l3mo population
            def ttest_MF(f, sex, attribute):
                a = f[(f.Period == DURATION['oa_f9mo']) & (f.Sex == sex)][attribute]
                b = f[(f.Period == DURATION['oa_l3mo']) & (f.Sex == sex)][attribute]

                ttest = stats.ttest_ind(a, b, equal_var=False)
                text = 'Unpaired t-test\n$H_0$: (' + sex + ') $\mu_{f9mo} = \mu_{l3mo}$' \
                       '\n$t-statistic$: %.4f\n$p-value$: %.4f' % ttest
                if sex == 'F':
                    x = 0.02
                else:
                    x = 0.45
                plt.annotate(text, xy=(x, .72), xycoords=plt.gca().transAxes, fontsize=14)

            f = df_dc[df_dc[attribute].notnull()]
            ttest_MF(f, 'M', attribute)
            ttest_MF(f, 'F', attribute)

        if save:
            path = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/habitual_drinking/comb_' + minor.lower() + '_factor/'
            fig.savefig(path + 'acomb_' + minor.lower() + '_factor_' + attr_save_name + '_' + dc, dpi=200)
        else:
            plt.show()
def create_comb_factor_plots(major, minor, ttest):
    for attr in MTDS_ATRR:
        comb_factor_plot(attr, major=major, minor=minor, ttest=ttest, save=True)
#create_comb_factor_plots(major='Period', minor='Sex', ttest=False)
#create_comb_factor_plots(major='Sex', minor='Period', ttest=True)
#comb_factor_plot(('mtd_max_bout_length', 'Max Bout Length'), major='Sex', minor='Period', ttest=True, save=False)


#================FANCY CORR PLOT=================================
import seaborn as sns
sns.set(style="white")

def pretty_pairplot(sex, period, save=False):
    def corrfunc(x, y, **kws):
        r, _ = stats.pearsonr(x, y)
        ax = plt.gca()
        ax.annotate("r = {:.2f}".format(r),
                    xy=(.1, .9), xycoords=ax.transAxes)

    df = combine_dfs_by_dc()

    df = df[df.Sex == sex]
    df = df[df.Period == period]

    #df = df.iloc[:100]
    df = df[['Average length of EtOH bouts', 'Average length of EtOH drinks']]
    df.dropna(axis=0, inplace=True)

    # remove outliers
    df[(np.abs(stats.zscore(df)) < 3).all(axis=1)]

    g = sns.PairGrid(df, palette=["red"], size=6)
    g.map_upper(plt.scatter, s=10)
    g.map_diag(sns.distplot, kde=False)
    g.map_lower(sns.kdeplot, cmap="Blues_d")
    g.map_lower(corrfunc)

    g.fig.suptitle('Sex: %s, Period: %s' % (sex, period), fontsize=14)
    plt.subplots_adjust(top=0.95)

    if save:
        path = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/habitual_drinking/pretty_pairplots/'
        g.savefig(path + '_' + sex + '_' + period, dpi=200)
    else:
        plt.show()

def generate_habit_drink_pairplots():
    for period in ['oa_f9mo', 'oa_l3mo']:
        for sex in ['F', 'M']:
            pretty_pairplot(sex=sex, period=DURATION[period], save=True)

#generate_habit_drink_pairplots()

# pretty_pairplot(sex='F', period=DURATION['oa_f9mo'])
# pretty_pairplot(sex='M', period=DURATION['oa_f9mo'])
















