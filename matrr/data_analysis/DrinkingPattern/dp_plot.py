__author__ = 'alex'
import sys
import os
import django
import matplotlib
#import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import timedelta

sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
django.setup()

from matrr.models import *
from matrr.utils.database import dingus

DRINKING_CATEGORIES_COLORS = {'LD': '#0052CC', 'BD': '#008000', 'HD': '#FF6600', 'VHD': '#FF0000', 'None': 'k', None: 'k'}
LINESTYLES = ['-', '--', '-.', ':']

FEMALES = ['INIA Rhesus 6a', 'INIA Rhesus 6b']
MALES = ['INIA Rhesus 5', 'INIA Rhesus 7a', 'INIA Rhesus 7b']

c13 = Cohort.objects.get(coh_cohort_name="INIA Cyno 13")

r6a = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6a")
r6b = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6b")
r5 = Cohort.objects.get(coh_cohort_name="INIA Rhesus 5")
r7a = Cohort.objects.get(coh_cohort_name="INIA Rhesus 7a")
r7b = Cohort.objects.get(coh_cohort_name="INIA Rhesus 7b")

RHESUS_FEMALES = [r6a, r6b]
RHESUS_MALES = [r5, r7a, r7b]

# Redefining constants by Kathy's request (which kind of make sense by the look ofthe plot)
LIGHTS_OUT = 7 * ONE_HOUR
LIGHTS_ON = 20 * ONE_HOUR
PREV_DAY_LIGHT = 22 * ONE_HOUR - LIGHTS_ON
DAYLIGHT = PREV_DAY_LIGHT + LIGHTS_OUT



"""
29 Dec 2015
Drinking Pattern
"""
def get_mky_oa_drinks_cumsum(mky):
    def get_mtd_drinks(mtd):
        try:
            bouts = ExperimentBout.objects.filter(mtd=mtd)
            edrs = ExperimentDrink.objects.filter(ebt__in=bouts).order_by('edr_start_time')

            drinks = pd.DataFrame(list(edrs.values_list('edr_start_time', 'edr_volume')),
                                  columns=['start_time', 'volume'])
            drinks.set_index('start_time', inplace=True)
            gkg_ratio = 0.04 / mtd.mtd_weight
            drinks['gkg'] = drinks.volume * gkg_ratio
            return drinks
        except Exception as e:
            print e
            pass

    mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).order_by('drinking_experiment__dex_date')

    drinks_cumsum = get_mtd_drinks(mtds[0])
    imtd = 1
    while drinks_cumsum is None:  # make sure we got the data
        drinks_cumsum = get_mtd_drinks(mtds[imtd])
        imtd += 1
    print imtd, mky

    mtds_used = 1
    for mtd in mtds[imtd: ]: #imtd + 5]:
        drinks_cumsum = drinks_cumsum.append(get_mtd_drinks(mtd))
        mtds_used += 1

    drinks_cumsum.sort_index(inplace=True)
    return drinks_cumsum, mtds_used


def plot_cohort_oa_cumsum_drinking_pattern(cohorts, schedule='Day Light', remove_trend=False, ylim=None):
    DURATION = SESSION_END if schedule == '22hr' else DAYLIGHT
    remove_trend_title = {True: '(De-trended) ', False: ''}
    remove_trend_legend_loc = {True: 3, False: 2}
    matplotlib.rc('font', family='monospace')
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111)

    monkeys = Monkey.objects.filter(cohort__in=cohorts).filter(mky_drinking=True).order_by('mky_drinking_category')

    for mky in monkeys:
        mky_drink_cumsum, mtds_used = get_mky_oa_drinks_cumsum(mky)

        if schedule == 'Day Light':
            mky_drink_cumsum['new_index'] = list(mky_drink_cumsum.index)
            mky_drink_cumsum.new_index[mky_drink_cumsum.new_index > LIGHTS_ON] -= TWENTYTWO_HOUR
            mky_drink_cumsum.new_index += PREV_DAY_LIGHT
            mky_drink_cumsum = mky_drink_cumsum.set_index('new_index').sort_index()
            mky_drink_cumsum = mky_drink_cumsum[mky_drink_cumsum.index < DAYLIGHT]  # Drop unseen

        # Normalize (average) values, remove trend and plot
        mky_drink_cumsum.gkg = mky_drink_cumsum.gkg.cumsum() / mtds_used
        mky_drink_cumsum.index /= ONE_HOUR * 1.0

        if remove_trend:
            fit = np.polyfit(mky_drink_cumsum.index, mky_drink_cumsum.gkg, deg=1)
            mky_drink_cumsum.gkg = mky_drink_cumsum.gkg - (fit[0] * mky_drink_cumsum.index + fit[1])

        #ax.plot(mky_drink_cumsum.index, fit[0] * mky_drink_cumsum.index + fit[1], color='k')
        mky_drink_cumsum.gkg.plot(color=DRINKING_CATEGORIES_COLORS[mky.mky_drinking_category], ax=ax,
                                  label="%3s" % mky.mky_drinking_category + ' ' + str(mky.mky_id))

    plt.legend(loc=remove_trend_legend_loc[remove_trend])
    if len(cohorts) > 1:  # Compress the legend - we have monkeys from multiple cohorts
        handles, labels = ax.get_legend_handles_labels()
        used_cols = []
        unique_handles = []
        unique_labels = []
        for i, handle in enumerate(handles):
            if handle.get_c() not in used_cols:
                used_cols.append(handle.get_c())
                unique_handles.append(handle)
                unique_labels.append(labels[i].split(' 1')[0])

        ax.legend(unique_handles, unique_labels, loc=remove_trend_legend_loc[remove_trend])

    if ylim is not None:
        ax.set_ylim(ylim)

    # Plot pellets for entire cohort
    pellets_eevs = ExperimentEvent.objects.filter(monkey__in=monkeys).filter(eev_event_type=ExperimentEventType.Pellet)
    pellets = pd.DataFrame(list(pellets_eevs.values_list('eev_session_time', flat=True)))
    if schedule == 'Day Light':
        pellets += PREV_DAY_LIGHT
    pellets /= ONE_HOUR * 1.0
    ax_pellet = ax.twinx()
    pellets.hist(bins=10*60, ax=ax_pellet, alpha=.4)
    ax_pellet.set_ylabel('Pellet Consumption Distribution (Cohort)')
    ax_pellet.get_yaxis().set_ticks([])
    ax_pellet.set_xlabel('Time (session hour)')

    # Tune plot
    plt.xticks(np.arange(SESSION_START / ONE_HOUR, (DURATION / ONE_HOUR + 1), 1))
    if schedule == '22hr':
        plt.axvspan(LIGHTS_OUT/ONE_HOUR, LIGHTS_ON/ONE_HOUR, color='black', alpha=.2, zorder=-100)
    else:
        ax.set_xlim(0, DAYLIGHT / ONE_HOUR)

    ax.set_xlabel('Time (session hour)')
    ax.set_ylabel('Average ' + remove_trend_title[remove_trend] + 'cumulative EtOH (gkg)')
    cohort_short_names = [x.coh_cohort_name.encode('utf-8') for x in cohorts] # .split(' ')[2]
    plt.title("Cumulative Drinking Pattern for Cohort %s\n%s Session Schedule" % (cohort_short_names, schedule))
    if len(cohorts) == 1:  # annotate target start time if only one cohort
        target_start_time = cohorts[0].coh_target_start_time
        if target_start_time is not None:
            fig.text(0.065, 0.02, 'Target start time: %s' % target_start_time.strftime("%H:%M %p"), ha='left')
    plt.tight_layout()

matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/Matrr/baker_salo/drinking_pattern/'

def fm_dp(remove_trend=False):
    ylim = (-1, 1) if remove_trend else (0, 4.5)

    plot_cohort_oa_cumsum_drinking_pattern(RHESUS_FEMALES, schedule='Day Light', remove_trend=remove_trend, ylim=ylim)
    plot_cohort_oa_cumsum_drinking_pattern(RHESUS_MALES, schedule='Day Light', remove_trend=remove_trend, ylim=ylim)
#fm_dp(remove_trend=True)

#plot_cohort_oa_cumsum_drinking_pattern([c13], schedule='Day Light', remove_trend=True)
plt.show()




"""
Create Images for Matrr
"""
# print CohortImage.objects.filter(method__contains='drinking_pattern').count()
# CohortImage.objects.filter(method__contains='drinking_pattern').delete()
# print CohortImage.objects.filter(method__contains='drinking_pattern').count()

# from matrr.plotting import plot_tools
# plot_tools.create_drinking_pattern_plots()

# for img in CohortImage.objects.filter(method__contains="drinking_pattern"):
#     try:
#         print img
#         img.save(force_render=True)
#     except Exception as e:
#         print e
#         pass
