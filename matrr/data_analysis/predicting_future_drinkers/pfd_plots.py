import matplotlib
from matplotlib import pyplot as plt
from pfd_get_data import get_fold_subdivide_features, BEHAVIOR_ATTRIBUTES, LIGHT, HEAVY

FIG_SIZE = (16, 10)
PDF_DPI = 600
matplotlib.rcParams.update({'font.size': 16})


def plot_deltas_for_feature(df, feature):
    fig, axs = plt.subplots(1, 2, facecolor='w', edgecolor='k', figsize=FIG_SIZE)
    axs = axs.ravel()

    which_axis = {LIGHT: 0, HEAVY: 1}
    which_color = {LIGHT: 'g-o', HEAVY: 'r-o'}
    all_values = df[[feature + '_d1', feature + '_d2']]
    ylim = (min(all_values.min()) - 0.1, max(all_values.max()) + 0.1)

    for mky_id, mky_row in df.iterrows():
        dc = mky_row.dc
        axs[which_axis[dc]].plot([1, 2], [mky_row[feature + '_d1'], mky_row[feature + '_d2']], which_color[dc])

    for ax in axs:
        ax.set_xlim(0.9, 2.1)
        ax.set_ylim(ylim)
        ax.set_xticklabels(['', r'$\Delta_1$', '', '', '', '', r'$\Delta_2$'])
        ax.set_xlabel('Time (Relative Delta)')
        ax.set_ylabel('Log($\Delta$)')

    [axs[which_axis[x]].set_title(x) for x in which_axis.keys()]
    plt.suptitle('%s relative deltas change during induction' % feature)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    return fig


def generate_plot_deltas_for_feature(df, save_path):
    for feature in BEHAVIOR_ATTRIBUTES:
        fig = plot_deltas_for_feature(df, feature=feature[4:])
        fig.savefig(save_path + 'delta_change_' + feature, dpi=PDF_DPI, format='png')


data_low_heavy, data_ld_bd, data_hd_vhd = get_fold_subdivide_features(regenerate=True)
generate_plot_deltas_for_feature(data_low_heavy, '/home/alex/')

plt.show()
