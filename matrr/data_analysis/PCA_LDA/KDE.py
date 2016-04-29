from fetch_data import *
import math
import seaborn as sns


def plot_mhc_kde(df, challenge, save=True):
    hormones = df.columns[:-1]
    df = normalize_float_columns(df)
    nrows = int(math.ceil(len(hormones) / 2.0))

    fig, axes = plt.subplots(nrows=nrows, ncols=2, figsize=DEFAULT_FIG_SIZE_ALEX)
    axes = axes.ravel()

    for h, ax in zip(hormones, axes):
        groups = df.groupby('dc')[h]
        groups = sorted(groups, cmp=dc_comparator, key=lambda x: x[0])
        for dc, group in groups:
            sample_size = len(df[df.dc == dc])
            group.plot(kind='kde', alpha=0.5, ax=ax,
                       label='%.3s (n=%s)' % (dc, sample_size),
                       c=DC_COL[dc], lw=3)
        ax.set_title(MonkeyHormoneChoice.get_verbose(h))
        ax.legend()

    cohorts = set(Monkey.objects.filter(mky_id__in=df.index).values_list('cohort__coh_cohort_name', flat=True))
    plt.suptitle('KDE (normalized) for challenge: %s\nCohorts: %s; Samples used: %s' %
                 (challenge, ', '.join(cohorts), len(df)))
    plt.tight_layout()
    fig.subplots_adjust(top=0.94)

    if save:
        path = '/home/alex/win-share/matrr_sync/PCA_LDA_KDE/KDE/MonkeyHormoneChallenge/' + challenge + '/'
        if not os.path.exists(path):
            print 'Creating new dir %s' % path
            os.makedirs(path)
        fig.savefig(path + challenge + '-' + '_'.join(hormones), dpi=DEFAULT_ALEX_DPI)



# SUFFICIENT_NUMBER_HORMONES = 100
# challenge = 'Saline'
# hormones = ['cort', 'doc', 'ald', 'acth', 'estra', 'dheas']
# df = fetch_hormone_challenge(hormone_challenge=challenge)[list(hormones) + ['dc']].\
#                         dropna(axis=0, how='any')
#
# plot_mhc_kde(df, challenge, save=False)
# plt.show()