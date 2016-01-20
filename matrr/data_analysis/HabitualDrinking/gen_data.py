import sys
import os
import django
import matplotlib
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
    N = {'F': len(df[df.Sex == 'F']),
         'M': len(df[df.Sex == 'M'])}
    attr_save_name = attr[0]
    attribute = attr[1]

    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(111)
    df.boxplot(column=attribute, by='Sex', ax=ax)

    # Unpaired t-test assuming unequal variances
    # H0: means are equal
    a = df[df.Sex == 'F'][attribute][df[df.Sex == 'F'][attribute].notnull()]
    b = df[df.Sex == 'M'][attribute][df[df.Sex == 'M'][attribute].notnull()]
    ttest = stats.ttest_ind(a, b, equal_var=False)
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    text = 'Unpaired t-test\n  H0: $\mu_F = \mu_M$\nt-statistic: %.4f\np-value: %.4f' % ttest
    ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)

    xlabels = [x.get_text() for x in ax.get_xticklabels()]
    ax.set_xticklabels(['%s\n(N=%s)' % (x, N[x]) for x in xlabels])
    ax.set_xlabel(DURATION[duration])

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    if save:
        path = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/habitual_drinking/'
        fig.savefig(path + 'boxplot_' + duration + '_' + attr_save_name)
    else:
        plt.show()
        return fig


def create_mtd_attribute_boxplots():
    for duration in DURATION.keys():
        df = get_duration_df(duration)
        MTDS_ATRR.append(('drink_to_bout_ratio', 'Average Drink-to-Bout Length Ratio'))
        for attr in MTDS_ATRR:
            boxplot_mtd_attributes(duration, df, attr, save=True)

create_mtd_attribute_boxplots()

# duration = 'oa_l3mo'
# df = get_duration_df(duration)
# attr = ('mtd_max_bout_length', 'Max Bout Length')
# boxplot_mtd_attributes(duration, df, attr, save=False)

