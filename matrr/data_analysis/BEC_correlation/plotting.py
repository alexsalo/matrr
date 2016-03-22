__author__ = 'alex'
from common import *
from statsmodels.formula.api import ols
from data_generation import get_bec_df_for_all_animals

def _plot_regression_line_and_corr_text(ax, x, y, linecol='red', group_label='', text_y_adj=0):
    fit = np.polyfit(x, y, deg=1)
    ax.plot(x, fit[0] * x + fit[1], color=linecol)

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    text = group_label + ' Corr: %s' % np.round(x.corr(y), 4)
    ax.text(0.05, 0.95 + text_y_adj, text, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)


def _plot_ancova_regression_pvalue(ax, df_group1, df_group_2, which_etoh):
    df = df_group1.copy(deep=True)
    df['over'] = False
    df = df.append(df_group_2)
    df.fillna(True, inplace=True)

    fit = ols('bec ~ ' + which_etoh + ' * C(over)', df).fit()
    pvalue = fit.pvalues[which_etoh + ':C(over)[T.True]']

    props = dict(boxstyle='round', facecolor='mintcream', alpha=0.3)
    ax.text(0.70, 0.95, 'H0: Equal slopes\nP-value: %.4f' % pvalue, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)



def plot_bec_correlation(bec_df):
    fig, axs = plt.subplots(1, 3, figsize=(15, 8), facecolor='w', edgecolor='k')
    bec_df.plot(kind='scatter', x='etoh_previos_day', y='bec', ax=axs[0])
    bec_df.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', ax=axs[1])
    bec_df.plot(kind='scatter', x='etoh_next_day', y='bec', ax=axs[2])
    plt.tight_layout()

    _plot_regression_line_and_corr_text(axs[0], bec_df.etoh_previos_day, bec_df.bec)
    _plot_regression_line_and_corr_text(axs[1], bec_df.etoh_at_bec_sample_time, bec_df.bec)
    _plot_regression_line_and_corr_text(axs[2], bec_df.etoh_next_day, bec_df.bec)


def plot_bec_correlation_by_dc(bec_df, font_size=12):
    fig, axs = plt.subplots(4, 3, figsize=(20, 10), facecolor='w', edgecolor='k')
    axs = axs.ravel()
    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        df_dc = bec_df[bec_df.dc == dc]

        df_dc.plot(kind='scatter', x='etoh_previos_day', y='bec', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 0])
        df_dc.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 1])
        df_dc.plot(kind='scatter', x='etoh_next_day', y='bec', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 2])

        _plot_regression_line_and_corr_text(axs[i*3 + 0], df_dc.etoh_previos_day, df_dc.bec)
        _plot_regression_line_and_corr_text(axs[i*3 + 1], df_dc.etoh_at_bec_sample_time, df_dc.bec)
        _plot_regression_line_and_corr_text(axs[i*3 + 2], df_dc.etoh_next_day, df_dc.bec)

    # fine tune plot look'n'feel
    plt.tight_layout()

    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
    plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)

    plt.setp([axs[i].get_xticklabels() for i in [9, 10, 11]], visible=True)
    plt.setp([axs[i].get_yticklabels() for i in [0, 3, 6, 9]], visible=True)

    [ax.set_ylabel('') for ax in axs]
    axs[0].set_ylabel('LD', fontsize=font_size)
    axs[3].set_ylabel('BD', fontsize=font_size)
    axs[6].set_ylabel('HD', fontsize=font_size)
    axs[9].set_ylabel('VHD', fontsize=font_size)

    fig.text(0.5, 0.94, 'BEC correlation: EtOH the day before, day of and day after', ha='center', fontsize=font_size+4)
    fig.text(0.005, 0.5, 'BEC', va='center', rotation='vertical', fontsize=font_size+4)
    fig.subplots_adjust(top=0.93)
    return fig
def plot_bec_correlation_by_dc_24panels(schedule, bec_df_all, bec_df_group_1, bec_df_group_2, group1_label, group2_label, font_size=12):
    fig, axs = plt.subplots(4, 6, figsize=(20, 10), facecolor='w', edgecolor='k')
    axs = axs.ravel()
    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        df_dc_group_1 = bec_df_group_1[bec_df_group_1.dc == dc]
        df_dc_group_2 = bec_df_group_2[bec_df_group_2.dc == dc]

        df_dc_group_1.plot(kind='scatter', x='etoh_previos_day', y='bec', c='g', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*6 + 0])
        df_dc_group_2.plot(kind='scatter', x='etoh_previos_day', y='bec', c='y', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*6 + 1])

        df_dc_group_1.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', c='g', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*6 + 2])
        df_dc_group_2.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', c='y', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*6 + 3])

        df_dc_group_1.plot(kind='scatter', x='etoh_next_day', y='bec', c='g', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*6 + 4])
        df_dc_group_2.plot(kind='scatter', x='etoh_next_day', y='bec', c='y', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*6 + 5])

        _plot_regression_line_and_corr_text(axs[i*6 + 0], df_dc_group_1.etoh_previos_day, df_dc_group_1.bec)
        _plot_regression_line_and_corr_text(axs[i*6 + 1], df_dc_group_2.etoh_previos_day, df_dc_group_2.bec)

        _plot_regression_line_and_corr_text(axs[i*6 + 2], df_dc_group_1.etoh_at_bec_sample_time, df_dc_group_1.bec)
        _plot_regression_line_and_corr_text(axs[i*6 + 3], df_dc_group_2.etoh_at_bec_sample_time, df_dc_group_2.bec)

        _plot_regression_line_and_corr_text(axs[i*6 + 4], df_dc_group_1.etoh_next_day, df_dc_group_1.bec)
        _plot_regression_line_and_corr_text(axs[i*6 + 5], df_dc_group_2.etoh_next_day, df_dc_group_2.bec)

    # fine tune plot look'n'feel
    plt.tight_layout()

    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
    plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)

    plt.setp([axs[i].get_xticklabels() for i in [18, 19, 20, 21, 22, 23]], visible=True)
    plt.setp([axs[i].get_yticklabels() for i in [0, 6, 12, 18]], visible=True)

    [ax.set_ylabel('') for ax in axs]
    axs[0].set_ylabel('LD', fontsize=font_size)
    axs[6].set_ylabel('BD', fontsize=font_size)
    axs[12].set_ylabel('HD', fontsize=font_size)
    axs[18].set_ylabel('VHD', fontsize=font_size)

    axs[0].set_title(group1_label)
    axs[1].set_title(group2_label)

    title = 'BEC correlation: EtOH the day before, day of and day after; ' + schedule + ' schedule'
    fig.text(0.5, 0.94, title, ha='center', fontsize=font_size+4)
    fig.text(0.005, 0.5, 'BEC', va='center', rotation='vertical', fontsize=font_size+4)
    fig.subplots_adjust(top=0.90)
    return fig
def plot_bec_correlation_by_dc_12combinedpanels(schedule, bec_df_all, bec_df_group_1, bec_df_group_2, group1_label, group2_label, font_size=12):
    fig, axs = plt.subplots(4, 3, figsize=(20, 10), facecolor='w', edgecolor='k')
    axs = axs.ravel()
    axs_hist = [ax.twiny() for ax in axs]

    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        df_dc_group_1 = bec_df_group_1[bec_df_group_1.dc == dc]
        df_dc_group_2 = bec_df_group_2[bec_df_group_2.dc == dc]
        df_dc_all = bec_df_all[bec_df_all.dc == dc]

        xlim = (0, 8)
        ylim = (-10, 400)
        alp = 0.3

        df_dc_group_1.plot(kind='scatter', x='etoh_previos_day', y='bec', c='g', xlim=xlim, ylim=ylim, ax=axs[i*3 + 0])
        df_dc_group_2.plot(kind='scatter', x='etoh_previos_day', y='bec', c='orange', xlim=xlim, ylim=ylim, ax=axs[i*3 + 0])
        df_dc_all.bec.hist(color='b', alpha=alp, bins=20, normed=True, orientation='horizontal', ax=axs_hist[i*3 + 0])

        df_dc_group_1.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', c='g', xlim=xlim, ylim=ylim, ax=axs[i*3 + 1])
        df_dc_group_2.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', c='orange', xlim=xlim, ylim=ylim, ax=axs[i*3 + 1])
        df_dc_all.bec.hist(color='b', alpha=alp, bins=20, normed=True, orientation='horizontal', ax=axs_hist[i*3 + 1])

        df_dc_group_1.plot(kind='scatter', x='etoh_next_day', y='bec', c='g', xlim=xlim, ylim=ylim, ax=axs[i*3 + 2])
        df_dc_group_2.plot(kind='scatter', x='etoh_next_day', y='bec', c='orange', xlim=xlim, ylim=ylim, ax=axs[i*3 + 2])
        df_dc_all.bec.hist(color='b', alpha=alp, bins=20, normed=True, orientation='horizontal', ax=axs_hist[i*3 + 2])


        _plot_regression_line_and_corr_text(axs[i*3 + 0], df_dc_group_1.etoh_previos_day, df_dc_group_1.bec, linecol='blue')
        _plot_regression_line_and_corr_text(axs[i*3 + 0], df_dc_group_2.etoh_previos_day, df_dc_group_2.bec, text_y_adj=-0.15)
        _plot_ancova_regression_pvalue(axs[i*3 + 0], df_dc_group_1, df_dc_group_2, 'etoh_previos_day')

        _plot_regression_line_and_corr_text(axs[i*3 + 1], df_dc_group_1.etoh_at_bec_sample_time, df_dc_group_1.bec, linecol='blue')
        _plot_regression_line_and_corr_text(axs[i*3 + 1], df_dc_group_2.etoh_at_bec_sample_time, df_dc_group_2.bec, text_y_adj=-0.15)
        _plot_ancova_regression_pvalue(axs[i*3 + 1], df_dc_group_1, df_dc_group_2, 'etoh_at_bec_sample_time')

        _plot_regression_line_and_corr_text(axs[i*3 + 2], df_dc_group_1.etoh_next_day, df_dc_group_1.bec, linecol='blue')
        _plot_regression_line_and_corr_text(axs[i*3 + 2], df_dc_group_2.etoh_next_day, df_dc_group_2.bec, text_y_adj=-0.15)
        _plot_ancova_regression_pvalue(axs[i*3 + 2], df_dc_group_1, df_dc_group_2, 'etoh_next_day')

    # fine tune plot look'n'feel
    plt.tight_layout()

    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
    plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)

    plt.setp([axs[i].get_xticklabels() for i in [9, 10, 11]], visible=True)
    plt.setp([axs[i].get_yticklabels() for i in [0, 3, 6, 9]], visible=True)

    [ax.set_ylabel('') for ax in axs]
    axs[0].set_ylabel('LD', fontsize=font_size)
    axs[3].set_ylabel('BD', fontsize=font_size)
    axs[6].set_ylabel('HD', fontsize=font_size)
    axs[9].set_ylabel('VHD', fontsize=font_size)

    # # Dummy scatter for legend
    dot_group1 = plt.Line2D((0,1),(0,0), color='g', marker='o', linestyle='', label=group1_label, markersize=8)
    dot_group2 = plt.Line2D((0,1),(0,0), color='orange', marker='o', linestyle='', label=group2_label, markersize=8)
    axs[0].legend(handles=[dot_group1, dot_group2], bbox_to_anchor=[0, 1], loc='lower left', scatterpoints=1)

    title = 'BEC correlation: EtOH the day before, day of and day after; ' + schedule + ' schedule'
    fig.text(0.5, 0.94, title, ha='center', fontsize=font_size+4)
    fig.text(0.005, 0.5, 'BEC', va='center', rotation='vertical', fontsize=font_size+4)
    fig.subplots_adjust(top=0.90)

    fig.text(0.19, 0.01, 'EtOH Day Before', ha='center', fontsize=font_size)
    fig.text(0.5, 0.01, 'EtOH Day of BEC Sample', ha='center', fontsize=font_size)
    fig.text(0.83, 0.01, 'EtOH Day After', ha='center', fontsize=font_size)
    fig.subplots_adjust(bottom=0.05)

    return fig
def plot_bec_correlation_by_dc_24panels_hexbins(schedule, bec_df_all, bec_df_group_1, bec_df_group_2, group1_label, group2_label, font_size=12):
    fig, axs = plt.subplots(4, 6, figsize=(20, 10), facecolor='w', edgecolor='k')
    axs = axs.ravel()
    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        df_dc_group_1 = bec_df_group_1[bec_df_group_1.dc == dc]
        df_dc_group_2 = bec_df_group_2[bec_df_group_2.dc == dc]

        axs[i*6 + 0].hexbin(x=df_dc_group_1.etoh_previos_day, y=df_dc_group_1.bec, cmap=plt.cm.Greens, gridsize=10)
        axs[i*6 + 1].hexbin(x=df_dc_group_2.etoh_previos_day, y=df_dc_group_2.bec, cmap=plt.cm.Blues, gridsize=10)

        axs[i*6 + 2].hexbin(x=df_dc_group_1.etoh_at_bec_sample_time, y=df_dc_group_1.bec, cmap=plt.cm.Greens, gridsize=10)
        axs[i*6 + 3].hexbin(x=df_dc_group_2.etoh_at_bec_sample_time, y=df_dc_group_2.bec, cmap=plt.cm.Blues, gridsize=10)

        axs[i*6 + 4].hexbin(x=df_dc_group_1.etoh_next_day, y=df_dc_group_1.bec, cmap=plt.cm.Greens, gridsize=10)
        axs[i*6 + 5].hexbin(x=df_dc_group_2.etoh_next_day, y=df_dc_group_2.bec, cmap=plt.cm.Blues, gridsize=10)

        _plot_regression_line_and_corr_text(axs[i*6 + 0], df_dc_group_1.etoh_previos_day, df_dc_group_1.bec)
        _plot_regression_line_and_corr_text(axs[i*6 + 1], df_dc_group_2.etoh_previos_day, df_dc_group_2.bec)

        _plot_regression_line_and_corr_text(axs[i*6 + 2], df_dc_group_1.etoh_at_bec_sample_time, df_dc_group_1.bec)
        _plot_regression_line_and_corr_text(axs[i*6 + 3], df_dc_group_2.etoh_at_bec_sample_time, df_dc_group_2.bec)

        _plot_regression_line_and_corr_text(axs[i*6 + 4], df_dc_group_1.etoh_next_day, df_dc_group_1.bec)
        _plot_regression_line_and_corr_text(axs[i*6 + 5], df_dc_group_2.etoh_next_day, df_dc_group_2.bec)

    # fine tune plot look'n'feel
    plt.tight_layout()

    for ax in axs:  # xlim and ylim
        ax.axis([0, 8, 0, 400])

    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)

    plt.setp([a.get_xticklabels() for a in fig.axes], visible=False)
    plt.setp([a.get_yticklabels() for a in fig.axes], visible=False)

    plt.setp([axs[i].get_xticklabels() for i in [18, 19, 20, 21, 22, 23]], visible=True)
    plt.setp([axs[i].get_yticklabels() for i in [0, 6, 12, 18]], visible=True)

    [ax.set_ylabel('') for ax in axs]
    axs[0].set_ylabel('LD', fontsize=font_size)
    axs[6].set_ylabel('BD', fontsize=font_size)
    axs[12].set_ylabel('HD', fontsize=font_size)
    axs[18].set_ylabel('VHD', fontsize=font_size)

    [axs[2 * i].set_title(group1_label) for i in range(0, 3)]
    [axs[2 * i + 1].set_title(group2_label) for i in range(0, 3)]


    title = 'BEC correlation: EtOH the day before, day of and day after; ' + schedule + ' schedule'
    fig.text(0.5, 0.94, title, ha='center', fontsize=font_size+4)
    fig.text(0.005, 0.5, 'BEC', va='center', rotation='vertical', fontsize=font_size+4)
    fig.subplots_adjust(top=0.90)
    fig.subplots_adjust(left=0.04)

    fig.text(0.19, 0.01, 'EtOH Day Before', ha='center', fontsize=font_size)
    fig.text(0.5, 0.01, 'EtOH Day of BEC Sample', ha='center', fontsize=font_size)
    fig.text(0.83, 0.01, 'EtOH Day After', ha='center', fontsize=font_size)
    fig.subplots_adjust(bottom=0.05)
    return fig

def build_bec_panel(schedule, split_by, regenerate, group1_label, group2_label, plot_func, save):
    bec_df_all, bec_df_group_1, bec_df_group_2 = get_bec_df_for_all_animals(schedule, split_by, regenerate)
    fig = plot_func(schedule, bec_df_all, bec_df_group_1, bec_df_group_2, group1_label, group2_label)

    if save:
        # path = '/home/alex/win-share/matrr_sync/bec_study/'
        path = '/home/alex/Dropbox/Baylor/Matrr/bec_study/'
        plot_func_name = str(plot_func).split('_')[-1].split(' ')[-3]
        fig.savefig(path + schedule + '/' + schedule + '_' + split_by + '_' + plot_func_name)
def build_all_bec_panels(regenerate_data=False):
    for split_by, group1_label, group2_label in \
            zip(['bec_mgpct', 'bec_over2stdev', 'bec_less2stdev', 'bec_more2stdev'],  # split_by
                ['< 80 mg pct', 'Within 2 Std. Dev.', 'Typical', 'Typical'],    # Normal
                ['>= 80 mg pct', 'Outside of 2 Std. Dev.', '< 2 SD', '> 2 SD']  # Condition
                ):
        for plot_func in [plot_bec_correlation_by_dc_24panels, plot_bec_correlation_by_dc_12combinedpanels,
                          plot_bec_correlation_by_dc_24panels_hexbins]:
            for schedule in ['22hr', 'daylight']:
                build_bec_panel(schedule=schedule, split_by=split_by, regenerate=regenerate_data,
                                group1_label=group1_label, group2_label=group2_label,
                                plot_func=plot_func, save=True)
#build_all_bec_panels(regenerate_data=False)


build_bec_panel(schedule='22hr', split_by='bec_mgpct', regenerate=False,
                group1_label='< 80 mg pct', group2_label='>= 80 mg pct',
                plot_func=plot_bec_correlation_by_dc_12combinedpanels, save=False)
plt.show()

"""
ANCOVA Regressions
"""
# from statsmodels.formula.api import ols
# bec_df_all, bec_df_group_1, bec_df_group_2 = get_bec_df_for_all_animals(schedule='22hr', split_by='bec_over2stdev', regenerate=False)
#
#
# def ols_group_dc(df, dc):
#     return ols('bec ~ etoh_next_day', df[df.dc == dc]).fit().summary()
# # print ols_group_dc(bec_df_group_1, 'BD')
# # print ols_group_dc(bec_df_group_2, 'BD')
#
# DC = 'BD'
#
# bec_df_group_1['over'] = False
# bec_df_group_1 = bec_df_group_1.append(bec_df_group_2)
# bec_df_group_1.fillna(True, inplace=True)
# print bec_df_group_1
# print ols('bec ~ etoh_next_day * C(over)', bec_df_group_1[bec_df_group_1.dc == DC]).fit().summary()
# ##.pvalues['etoh_next_day:C(over)[T.True]']
#
#
# def get_group_dc(df, dc, over):
#     df = df[df.dc == dc]
#     return df[df.over == over]
#
# import matplotlib
# matplotlib.rcParams['savefig.directory'] = '~/github/alexsalo.github.io/images/matrr/'
# fig = plt.figure(figsize=(10, 6))
# ax = fig.add_subplot(111)
#
# within = get_group_dc(bec_df_group_1, DC, over=True)
# within.plot(kind='scatter', x='etoh_next_day', y='bec', label='Within', c='g', ax=ax)
# _plot_regression_line_and_corr_text(ax, within.etoh_next_day, within.bec, linecol='g', group_label='Within,')
#
# over = get_group_dc(bec_df_group_1, DC, over=False)
# over.plot(kind='scatter', x='etoh_next_day', y='bec', label='Over', c='orange', ax=ax)
# _plot_regression_line_and_corr_text(ax, over.etoh_next_day, over.bec, linecol='orange', group_label='Over,', text_y_adj=-0.06)
#
# ax.set_title('Regression BEC ~ EtOH for group: HD')
# plt.xlabel('EtOH')
# plt.ylabel('BEC')
# plt.xlim(0, 6)
# plt.ylim(-10, 300)
# plt.tight_layout()