from pfd_get_data import *
from pfd_plots import *
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier
from sklearn import cross_validation, metrics

RF = RandomForestClassifier(n_estimators=100)
BAGGING = BaggingClassifier(RF, n_estimators=10, bootstrap=True, n_jobs=2)
STEPS = {'Heavy vs. Not Heavy': 0.52,
         'LD vs. BD': 0.615,
         'HD vs. VHD': 0.625}


def select_features_for(step):
    df = WHICH_DF[step]
    return df[WHICH_FEATURES[step]], df['Drinking Category']


def select_features(step, clf, runs=10, regenerate=False):
    df = WHICH_DF[step]
    y = df['Drinking Category']
    x = df.drop(['Drinking Category', 'Cohort'], axis=1)
    n = len(x.columns)
    top5_features, test_best_scores = [], np.empty([runs, n])
    for i in range(runs):
        all_features = list(x.columns)
        chosen_features, best_scores = [], []
        while len(chosen_features) < n:
            best_score = 0
            for feature in all_features:
                candidate_features = chosen_features + [feature]
                scores = cross_validation.cross_val_score(clf, x[candidate_features], y, cv=10)
                score = scores.mean()
                if score > best_score:
                    best_score, best_feature = score, feature
            print best_feature, best_score
            best_scores.append(best_score)
            chosen_features.append(best_feature)
            all_features.remove(best_feature)
        print chosen_features
        test_best_scores[i] = best_scores
        top5_features += chosen_features[:5]

    print 'Results: \n -------------------------------------'
    import collections
    print top5_features
    print collections.Counter(top5_features)

    if regenerate:
        np.save('best_scores_' + step.lower().replace('.', '').replace(' ', '_'), test_best_scores)
# select_features(step='Heavy vs. Not Heavy', clf=RF, runs=20, regenerate=True)
# select_features(step='LD vs. BD', clf=RF, runs=20, regenerate=True)
# select_features(step='HD vs. VHD', clf=RF, runs=20, regenerate=True)


def plot_feature_selection(test_best_scores, step, label, ax=None, trim_at=None, save_path=None):
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=FIG_SIZE, dpi=PNG_DPI)

    if trim_at is not None:
        test_best_scores = test_best_scores[:, :trim_at]

    n = test_best_scores.shape[1]
    tbs_means = np.mean(test_best_scores, axis=0)
    tbs_sds = np.std(test_best_scores, axis=0)
    print tbs_means
    best_n, best_score = tbs_means.argmax() + 1, max(tbs_means)

    ylim = (0.5, 1)
    ax.plot(range(1, n + 1), tbs_means, linewidth=2, label="Average accuracy")
    lower = [mean - sds for mean, sds in zip(tbs_means, tbs_sds)]
    upper = [mean + sds for mean, sds in zip(tbs_means, tbs_sds)]
    ax.fill_between(range(1, n + 1), lower, upper, facecolor='yellow', alpha=0.5, label='Standard Deviation')
    # dummy plot to create legend since fill_between is not supported
    ax.plot([], [], color='yellow', linewidth=10, label='Std. Deviation')
    ax.axhline(STEPS[step], color='g', ls='--', lw=3, label="Naive (Base) accuracy")
    matplotlib.rcParams['legend.numpoints'] = 1
    ax.plot([best_n], [best_score], 'ro', markersize=15, label='Optimal number of features')
    ax.plot([1, best_n, best_n], [best_score, best_score, ylim[0]], 'k--', lw=1.5)

    # ax.set_xlabel('Number of features')
    ax.set_ylabel('Accuracy: ' + step)
    ax.set_ylim(ylim)
    ax.set_xlim(1, n)
    # ax.legend(loc='upper right')
    # ax.set_title('Feature Selection: %s' % step)
    ax.grid()
    # ax.tight_layout()
    ax.text(0.015, 0.87, label, transform=ax.transAxes, fontsize=22, family='monospace',
            bbox=dict(boxstyle='round', facecolor='mintcream', alpha=0.3))

    if save_path is not None:
        fig.savefig(save_path + step.lower().replace(' ', '_').replace('.', '') + '.png', dpi=PNG_DPI, format='png')
        fig.savefig(save_path + step.lower().replace(' ', '_').replace('.', '') + '.pdf', dpi=PDF_DPI, format='pdf')


def combine_feature_selection_plots(trim_at=None, save_path=None):
    matplotlib.rcParams.update({'font.size': 15})
    fig, axs = plt.subplots(3, 1, figsize=TALL_FIG_SIZE, dpi=PNG_DPI)
    axs = axs.ravel()
    ax_scores_step = zip(axs,
                         ['best_scores_heavy_vs_not_heavy.npy', 'best_scores_ld_vs_bd.npy','best_scores_hd_vs_vhd.npy'],
                         ['Heavy vs. Not Heavy', 'LD vs. BD', 'HD vs. VHD'],
                         ['A', 'B ', 'C '])
    for ax, score_name, step, label in ax_scores_step:
        plot_feature_selection(np.load(score_name), step, label, ax, trim_at=trim_at)
    plt.suptitle('Feature selection procedure in two-step classification model')
    plt.xlabel('Number of features')
    axs[0].legend(loc='upper right')
    plt.tight_layout()
    fig.subplots_adjust(hspace=0.1)
    fig.subplots_adjust(top=0.95)
    if save_path is not None:
        fig.savefig(save_path + 'feature_selection_combined.png', dpi=PNG_DPI, format='png')
        fig.savefig(save_path + 'feature_selection_combined.pdf', dpi=PDF_DPI, format='pdf')

# combine_feature_selection_plots(trim_at=40, save_path=WD+'/dev_images/feature_selection/')
# combine_feature_selection_plots(save_path=WD+'/dev_images/feature_selection/epochs_only/')


def test_selected_feature(step, runs=20):
    x, y = select_features_for(step)
    cv = 10
    runs_scores = np.empty([runs, cv])
    for i in range(runs):
        scores = cross_validation.cross_val_score(RF, x, y, cv=cv)
        runs_scores[i] = scores
    print 'Step: %s -- accuracy: %.2f (sd=%.2f)' % (step, runs_scores.mean(), runs_scores.std())

# for s in STEPS.keys():
#     test_selected_feature(s)
# test_selected_feature('Heavy vs. Not Heavy')
# test_selected_feature('LD vs. BD')
# test_selected_feature('HD vs. VHD')

# print 0.74*(0.52*0.91 + 0.48 * 0.90)


# Test By Cohort (Holdouts)
def accuracy_by_cohort(step, exclude_cohs_ids=[]):
    def report_results(clf, expected, predicted):
        print("\nClassification report for classifier %s:\n%s\n" %
              (clf, metrics.classification_report(expected, predicted)))
        print("Confusion matrix:\n%s" % metrics.confusion_matrix(expected, predicted))
        print("\nAccuracy score:\n%s" % metrics.accuracy_score(expected, predicted))
    print '\n--------------By Cohort-------------'
    df = WHICH_DF[step]
    coh_ids = np.unique(df['Cohort'])
    gb = df.groupby('Cohort')
    x, y = select_features_for(step)

    global_expected = []
    global_predicted = []
    for coh_id in coh_ids:
        print coh_id
        if coh_id not in exclude_cohs_ids:
            expected = []
            predicted = []

            print Cohort.objects.get(coh_cohort_id=coh_id)
            index = gb.get_group(coh_id).index

            # Train on all but one cohort
            RF.fit(x[~x.index.isin(index)], y[~x.index.isin(index)])

            # Predict on holdout cohort
            y_pred = RF.predict(x[x.index.isin(index)])

            # Print what you got
            y_test = y[x.index.isin(index)]

            expected += list(y_test); global_expected += list(y_test);
            predicted += list(y_pred); global_predicted += list(y_pred);

            y_pred = pd.DataFrame(list(y_pred), columns=['predicted'], index=y_test.index)
            print pd.concat([y_test, y_pred], axis=1, join='inner')
            report_results(RF, expected, predicted)
            print '-----------------------------------\n'
    report_results(RF, global_expected, global_predicted)

# accuracy_by_cohort('Heavy vs. Not Heavy')
# accuracy_by_cohort('LD vs. BD')#, exclude_cohs_ids=[7])
# accuracy_by_cohort('HD vs. VHD', exclude_cohs_ids=[9, 5])

# print 0.78*(0.5*0.90 + 0.5 * 0.95)
# print 0.5 * (16.0/25)
plt.show()
