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



"""
29 Dec 2015
Drinking Pattern
"""

# def get_mky_oa_drinks_cumsum(mky, end_time=SESSION_END):
#     def get_mtd_drinks(mtd):
#         try:
#             # Select Drinks
#             bouts = ExperimentBout.objects.filter(mtd=mtd)
#             edrs = ExperimentDrink.objects.filter(ebt__in=bouts).order_by('edr_start_time')
#
#             if end_time != SESSION_END:
#                 edrs = edrs.filter(edr_start_time__lte=end_time)
#
#             drinks = pd.DataFrame(list(edrs.values_list('edr_start_time', 'edr_volume')),
#                                   columns=['start_time', 'volume'])
#             drinks.set_index('start_time', inplace=True)
#
#             # Convert vols to gkg and cumsum
#             gkg_ratio = 0.04 * mtd.mtd_weight
#             drinks['gkg'] = drinks.volume * gkg_ratio
#
#             # Join on standardized index_df
#             index_df = pd.DataFrame(index=np.arange(0, end_time, 1))
#             index_df = index_df.join(drinks)  # join fits into index df
#
#             return index_df
#         except Exception as e:
#             pass
#             print e
#
#     mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).order_by('drinking_experiment__dex_date')
#     drinks_cumsum = get_mtd_drinks(mtds[0])
#     mtds_used = 1
#     for mtd in mtds[10:20]:
#         drinks_cumsum = drinks_cumsum.append(get_mtd_drinks(mtd))
#         mtds_used += 1
#
#     drinks_cumsum.sort_index(inplace=True)
#     drinks_cumsum = drinks_cumsum.fillna(0)
#     drinks_cumsum.gkg = drinks_cumsum.gkg.cumsum()
#
#     return drinks_cumsum.gkg, mtds_used
#
#
# def plot_cohort_oa_cumsum_drinking_pattern(cohort, end_time=SESSION_END):
#     fig = plt.figure(figsize=(14, 10))
#     ax = fig.add_subplot(111)
#
#     monkeys_id = list()
#     cumsum_dfs = list()
#     mtds_mky_used = list()
#     for mky in cohort.monkey_set.filter(mky_drinking=True).order_by('mky_drinking_category'):
#         mky_drink_cumsum, mtds_used = get_mky_oa_drinks_cumsum(mky, end_time)
#         monkeys_id.append(mky.mky_id)
#         cumsum_dfs.append(mky_drink_cumsum)
#         mtds_mky_used.append(mtds_used)
#     cohort_cumsum_df = pd.concat(cumsum_dfs, axis=1)
#     cohort_cumsum_df.columns = monkeys_id
#     print cohort_cumsum_df
#
#     # Normalize (average) values
#     for id, mused in zip(monkeys_id, mtds_mky_used):
#         cohort_cumsum_df[id] = cohort_cumsum_df[id] / mused
#     cohort_cumsum_df.index = cohort_cumsum_df.index / (60*60*1.0)
#
#     # Plot
#     cohort_cumsum_df.plot(ax=ax)
#
#     # # Remove trend (by mky)
#     # fit = np.polyfit(mky_drink_cumsum.index, mky_drink_cumsum.gkg, deg=1)
#     # mky_drink_cumsum.gkg = mky_drink_cumsum.gkg - (fit[0] * mky_drink_cumsum.index + fit[1])
#
#     # # Plot
#     # mky_drink_cumsum.gkg.plot(color=DRINKING_CATEGORIES_COLORS[mky.mky_drinking_category], ax=ax,
#     #                           label="%3s" % mky.mky_drinking_category + ' ' + str(mky.mky_id))
#
#
#     # # Tune plot
#     # plt.xticks(np.arange(SESSION_START/ONE_HOUR, (end_time/ONE_HOUR + 1), 1))
#     # if end_time == SESSION_END:
#     #     plt.axvspan(LIGHTS_OUT/ONE_HOUR, LIGHTS_ON/ONE_HOUR, color='black', alpha=.2, zorder=-100)
#     # plt.legend(loc=4)
#     # plt.xlabel('Time (session hour)')
#     # plt.ylabel('Average cumulative EtOH (gkg)')
#     # plt.title("Cumulative Drinking Pattern for Cohort %s\n 22hr Session Schedule" % cohort)
#     # plt.tight_layout()
#
# matplotlib.rc('font', family='monospace')
# matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/Matrr/drinking_pattern_study/'
# plot_cohort_oa_cumsum_drinking_pattern(r10, LIGHTS_OUT)



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
    for mtd in mtds[imtd: ]: #imtd + 15]:
        drinks_cumsum = drinks_cumsum.append(get_mtd_drinks(mtd))
        mtds_used += 1

    drinks_cumsum.sort_index(inplace=True)
    return drinks_cumsum, mtds_used


def plot_cohort_oa_cumsum_drinking_pattern(cohorts, schedule='Day Light', remove_trend=False):
    DURATION = SESSION_END if schedule == '22hr' else 10 * ONE_HOUR
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
            mky_drink_cumsum.new_index[mky_drink_cumsum.new_index > 18 * ONE_HOUR] -= TWENTYTWO_HOUR
            mky_drink_cumsum.new_index += 4 * ONE_HOUR
            mky_drink_cumsum = mky_drink_cumsum.set_index('new_index').sort_index()
            mky_drink_cumsum = mky_drink_cumsum[mky_drink_cumsum.index < 10*ONE_HOUR]  # Drop unseen

        # Normalize (average) values, remove trend and plot
        mky_drink_cumsum.gkg = mky_drink_cumsum.gkg.cumsum() / mtds_used
        mky_drink_cumsum.index = mky_drink_cumsum.index / (60*60*1.0)

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

    # Plot pellets for entire cohort
    pellets_eevs = ExperimentEvent.objects.filter(monkey__in=monkeys).filter(eev_event_type=ExperimentEventType.Pellet)
    pellets = pd.DataFrame(list(pellets_eevs.values_list('eev_session_time', flat=True)))
    pellets = pellets / (60*60*1.0)
    if schedule == 'Day Light':
        pellets += 4
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
        ax.set_xlim(0, 10 * ONE_HOUR / (60*60*1.0))

    ax.set_xlabel('Time (session hour)')
    ax.set_ylabel('Average ' + remove_trend_title[remove_trend] + 'cumulative EtOH (gkg)')
    cohort_short_names = [x.coh_cohort_name.encode('utf-8') for x in cohorts] # .split(' ')[2]
    plt.title("Cumulative Drinking Pattern for Cohort %s\n%s Session Schedule" % (cohort_short_names, schedule))
    if len(cohorts) == 1:  # annotate target start time if only one cohort
        target_start_time = cohorts[0].coh_target_start_time
        if target_start_time is not None:
            fig.text(0.065, 0.02, 'Target start time: %s' % target_start_time.strftime("%H:%M %p"), ha='left')
    plt.tight_layout()

matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/Matrr/drinking_pattern_study/'
# plot_cohort_oa_cumsum_drinking_pattern(RHESUS_FEMALES, schedule='Day Light', remove_trend=False)
# plot_cohort_oa_cumsum_drinking_pattern(RHESUS_MALES, schedule='Day Light', remove_trend=False)
#
# plt.show()




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
