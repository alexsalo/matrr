__author__ = 'alex'
from common import *
from data_generation import get_bec_df_for_all_animals

def _plot_regression_line_and_corr_text(ax, x, y, linecol='red', text_y_adj=0):
    fit = np.polyfit(x, y, deg=1)
    ax.plot(x, fit[0] * x + fit[1], color=linecol)

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    text = 'Correlation: %s' % np.round(x.corr(y), 4)
    ax.text(0.05, 0.95 + text_y_adj, text, transform=ax.transAxes, fontsize=14,
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
def plot_bec_correlation_by_dc_24panels(schedule, bec_df_group_1, bec_df_group_2, group1_label, group2_label, font_size=12):
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
def plot_bec_correlation_by_dc_12combinedpanels(schedule, bec_df_group_1, bec_df_group_2, group1_label, group2_label, font_size=12):
    fig, axs = plt.subplots(4, 3, figsize=(20, 10), facecolor='w', edgecolor='k')
    axs = axs.ravel()
    for i, dc in enumerate(['LD', 'BD', 'HD', 'VHD']):
        df_dc_group_1 = bec_df_group_1[bec_df_group_1.dc == dc]
        df_dc_group_2 = bec_df_group_2[bec_df_group_2.dc == dc]

        df_dc_group_1.plot(kind='scatter', x='etoh_previos_day', y='bec', c='g', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 0])
        df_dc_group_2.plot(kind='scatter', x='etoh_previos_day', y='bec', c='orange', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 0])

        df_dc_group_1.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', c='g', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 1])
        df_dc_group_2.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', c='orange', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 1])

        df_dc_group_1.plot(kind='scatter', x='etoh_next_day', y='bec', c='g', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 2])
        df_dc_group_2.plot(kind='scatter', x='etoh_next_day', y='bec', c='orange', xlim=(0, 8), ylim=(-10, 400), ax=axs[i*3 + 2])

        _plot_regression_line_and_corr_text(axs[i*3 + 0], df_dc_group_1.etoh_previos_day, df_dc_group_1.bec, linecol='blue')
        _plot_regression_line_and_corr_text(axs[i*3 + 0], df_dc_group_2.etoh_previos_day, df_dc_group_2.bec, text_y_adj=-0.15)

        _plot_regression_line_and_corr_text(axs[i*3 + 1], df_dc_group_1.etoh_at_bec_sample_time, df_dc_group_1.bec, linecol='blue')
        _plot_regression_line_and_corr_text(axs[i*3 + 1], df_dc_group_2.etoh_at_bec_sample_time, df_dc_group_2.bec, text_y_adj=-0.15)

        _plot_regression_line_and_corr_text(axs[i*3 + 2], df_dc_group_1.etoh_next_day, df_dc_group_1.bec, linecol='blue')
        _plot_regression_line_and_corr_text(axs[i*3 + 2], df_dc_group_2.etoh_next_day, df_dc_group_2.bec, text_y_adj=-0.15)

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

    import matplotlib.patches as mpatches
    patch_group1 = mpatches.Patch(color='g', label=group1_label)
    patch_group2 = mpatches.Patch(color='orange', label=group2_label)
    axs[4].legend(handles=[patch_group1, patch_group2], loc=1)

    title = 'BEC correlation: EtOH the day before, day of and day after; ' + schedule + ' schedule'
    fig.text(0.5, 0.94, title, ha='center', fontsize=font_size+4)
    fig.text(0.005, 0.5, 'BEC', va='center', rotation='vertical', fontsize=font_size+4)
    fig.subplots_adjust(top=0.92)
    return fig


def build_bec_panel(schedule, split_by, regenerate, group1_label, group2_label, plot_func, save):
    bec_df_all, bec_df_group_1, bec_df_group_2 = get_bec_df_for_all_animals(schedule, split_by, regenerate)
    fig = plot_func(schedule, bec_df_group_1, bec_df_group_2, group1_label, group2_label)

    if save:
        path = '/home/alex/win-share/matrr_sync/bec_study/'
        plot_func_name = str(plot_func).split('_')[-1].split(' ')[-3]
        fig.savefig(path + schedule + '/' + schedule + '_' + split_by + '_' + plot_func_name)
def build_all_bec_panels(regenerate_data=False):
    for split_by, group1_label, group2_label in zip(['bec_mgpct', 'bec_over2stdev'],
                                                    ['< 80 mg pct', 'Within 2 Std. Dev.'],
                                                    ['>= 80 mg pct', 'Outside of 2 Std. Dev.']):
        for plot_func in [plot_bec_correlation_by_dc_24panels, plot_bec_correlation_by_dc_12combinedpanels]:
            for schedule in ['22hr', 'daylight']:
                build_bec_panel(schedule=schedule, split_by=split_by, regenerate=regenerate_data,
                                group1_label=group1_label, group2_label=group1_label,
                                plot_func=plot_func, save=True)
#build_all_bec_panels(regenerate_data=False)


# build_bec_panel(schedule='22hr', split_by='bec_mgpct', regenerate=False,
#                 group1_label='group1_label', group2_label='group2_label',
#                 plot_func=plot_bec_correlation_by_dc_12combinedpanels, save=False)
# plt.show()