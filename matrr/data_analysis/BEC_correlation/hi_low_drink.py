from common import *
from matrr.models import Cohort, MonkeyToDrinkingExperiment

r6a = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6a")
r6b = Cohort.objects.get(coh_cohort_name="INIA Rhesus 6b")
r5 = Cohort.objects.get(coh_cohort_name="INIA Rhesus 5")
r7a = Cohort.objects.get(coh_cohort_name="INIA Rhesus 7a")
r7b = Cohort.objects.get(coh_cohort_name="INIA Rhesus 7b")

RHESUS_FEMALES = [r6a, r6b]
RHESUS_MALES = [r5, r7a, r7b]

TRESHOLD = 2
USED_STD = []
POPULATION = RHESUS_FEMALES + RHESUS_MALES
RETAIN_WASTED = True
REGENERATE = True


def mky_hi_low(mky, treshold):
    df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).
                           order_by('drinking_experiment__dex_date').
                           values_list('monkey__mky_gender', 'mtd_etoh_g_kg', 'monkey__mky_drinking_category')),
                      columns=['Sex', 'EtOH Today', 'Drinking Category'])
    df['EtOH Today'] = (df['EtOH Today'] - df['EtOH Today'].mean()) / df['EtOH Today'].std()
    df['EtOH Next Day'] = list(df['EtOH Today'][1:]) + [0]  # shifted - next day etoh
    df['wasted'] = df['EtOH Today'] > treshold

    print len(df[df.wasted]) * 1.0 / len(df)
    USED_STD.append(len(df[df.wasted]) * 1.0 / len(df))
    return df[:-1]  # truncate last entry since we don't know tmr's value
#mky_hi_low(Monkey.objects.filter(cohort__in=RHESUS_MALES).filter(mky_drinking_category__isnull=False)[0], TRESHOLD)

def collect_hi_low_dfs(monkeys, treshold):
    df = mky_hi_low(monkeys[0], treshold)
    for mky in monkeys[1:]:
        df = df.append(mky_hi_low(mky, treshold))
    # if POPULATION == RHESUS_FEMALES:
    #     df['Drinking Category'] = df['Drinking Category'].astype('category').cat.set_categories(['LD', 'HD', 'VHD'])
    # else:
    #     df['Drinking Category'] = df['Drinking Category'].astype('category').cat.set_categories(['LD', 'BD', 'HD', 'VHD'])
    return df


monkeys = Monkey.objects.filter(cohort__in=POPULATION).filter(mky_drinking_category__isnull=False)
if REGENERATE:
    df = collect_hi_low_dfs(monkeys, TRESHOLD)
    df.save('fm_all_hanogver_drinking_%s.plk' % TRESHOLD)
else:
    df = pd.read_pickle('fm_all_hanogver_drinking_%s.plk' % TRESHOLD)

if RETAIN_WASTED:
    df = df[df.wasted]
    long_df = pd.melt(df, id_vars=['Drinking Category'], value_vars=['EtOH Today', 'EtOH Next Day'],
                  value_name='EtOH (normed per animal)', var_name='Day')

pct_used = np.mean(USED_STD)
print 'avg pct used: %s, std: %.4f' % (pct_used, np.std(USED_STD))
print df[['wasted', 'Drinking Category']].groupby('Drinking Category').count()
dcN = list(df[['wasted', 'Drinking Category']].groupby('Drinking Category').count()['wasted'])
print dcN



#df[['etoh', 'next', 'dc']].groupby('dc').boxplot()
#plt.tight_layout()

import seaborn as sns



def factorplots():
    fig = sns.factorplot(x='Drinking Category', y='EtOH (normed per animal)', hue='Day', data=long_df, kind='box',
                         size=18, aspect=1.5, legend_out=False)
    plt.title('Factorplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
              (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)

    text = ''
    for label, N in zip(['LD', 'HD', 'VHD'], dcN):
        text += '%3s (N=%s)\n' % (label, N)
    fig.fig.text(0.04, 0.85, text)
    plt.subplots_adjust(top=0.95, bottom=0.05)
    #fig.axes[0, 0].set_ylim(-2, 4)
#factorplots()

# sns.swarmplot(x='Drinking Category', y="EtOH (normed per animal)", hue="Day", data=long_df, size=5)
# plt.title('Swarmplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
#           (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)

def jointlots():
    sns.jointplot(x='EtOH Today', y='EtOH Next Day', data=df, kind="reg")
#jointlots()


def pairplots():
    pairplt = sns.pairplot(df, x_vars='EtOH Today', y_vars=['EtOH Next Day'],
                 hue='Drinking Category', size=18, aspect=.8, kind="reg")
    ax = pairplt.axes[0, 0]
    ax.set_ylim(-2.5, 3.5)
    plt.title('Pairplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
              (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    labels = ['%3s (N=%s)' %(label, N) for label, N in zip(labels, dcN)]
    ax.legend(handles, labels)
    plt.subplots_adjust(top=0.95, bottom=0.05)
#pairplots()


def pairplots_combined():
    df.ix[(df['Drinking Category'] != 'LD') & (df['Sex'] == 'M'), 'Drinking Category'] = 'HD_M'
    df.ix[(df['Drinking Category'] != 'LD') & (df['Sex'] == 'F'), 'Drinking Category'] = 'HD_F'
    df.ix[(df['Drinking Category'] == 'LD') & (df['Sex'] == 'F'), 'Drinking Category'] = 'LD_F'
    df.ix[(df['Drinking Category'] == 'LD') & (df['Sex'] == 'M'), 'Drinking Category'] = 'LD_M'
    dcN = [len(df[df['Drinking Category'] == x]) for x in ['HD_M','HD_F','LD_F','LD_M']]
    #print df
    pairplt = sns.pairplot(df, x_vars='EtOH Today', y_vars=['EtOH Next Day'],
                 hue='Drinking Category', size=18, aspect=.8, kind="reg", palette="husl")
    ax = pairplt.axes[0, 0]
    ax.set_ylim(-2.5, 3.5)
    plt.title('Pairplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
              (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    labels = ['%3s (N=%s)' %(label, N) for label, N in zip(labels, dcN)]
    ax.legend(handles, labels)
    plt.subplots_adjust(top=0.95, bottom=0.05)
#pairplots_combined()


def pairplot_wasted():
    pairplt = sns.pairplot(df, x_vars='EtOH Today', y_vars=['EtOH Next Day'], hue='Sex', size=18, kind="reg")
    ax = pairplt.axes[0, 0]
    plt.title('Pairplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
              (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    labels = ['%3s (N=%s)' %(label, N) for label, N in zip(labels, [len(df[df.Sex=='M']), len(df[df.Sex=='F'])])]
    ax.legend(handles, labels)
    plt.subplots_adjust(top=0.95, bottom=0.05)
#pairplot_wasted()


def lmplots():
    lmplt = sns.lmplot(x='EtOH Today', y='EtOH Next Day', hue='Sex', data=df, size=10,
           order=2, ci=15, scatter_kws={"s": 80})
    ax = lmplt.axes[0, 0]
    plt.title('%s for drinking the day after intoxication\n Normalized daily average EtOH g/kg over treshold: '
              '%s std. dev. (samples used %.2f $\pm$ %.2f on average)' %
              ('Polynomial regession plot', TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    labels = ['%3s (N=%s)' %(label, N) for label, N in zip(labels, [len(df[df.Sex=='M']), len(df[df.Sex=='F'])])]
    ax.legend(handles, labels)
    plt.subplots_adjust(top=0.95, bottom=0.05)
#lmplots()
path = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/thesis_figures/'


def hangover_effect(df):
    res = pd.DataFrame(columns=['sex', 'dc', 'norm', 'hang', 'total'])
    results = pd.DataFrame(columns=['Sex', 'Drinking Category', 'Relative EtOH reduction after intoxication'])
    for sex in ['M', 'F']:
        df_sex = df[df.Sex == sex]
        for dc in ['LD', 'HD', 'VHD']:
            df_dc = df_sex[df_sex['Drinking Category'] == dc]

            norm = np.mean(df_dc[~df_dc.wasted]['EtOH Next Day'] - df_dc[~df_dc.wasted]['EtOH Today'])
            hang = np.mean(df_dc[df_dc.wasted]['EtOH Next Day'] - df_dc[df_dc.wasted]['EtOH Today'])
            total = np.mean(df_dc['EtOH Next Day'] - df_dc['EtOH Today'])
            res.loc[len(results) + 1] = [sex, dc, norm, hang, total]

            hang = df_dc[df_dc.wasted]['EtOH Next Day'] - df_dc[df_dc.wasted]['EtOH Today']
            hang_df = pd.DataFrame(hang, columns=['Relative EtOH reduction after intoxication'])
            hang_df['Sex'] = sex
            hang_df['Drinking Category'] = dc
            results = results.append(hang_df)
    print res
    return results
hangover = hangover_effect(df)


def brush_up(plotname, ax, violin=False):
    plt.title('%s for drinking the day after intoxication\n Normalized daily average EtOH g/kg over treshold: '
              '%s std. dev. (samples used %.2f $\pm$ %.2f on average)' %
              (plotname, TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    labels = ['%3s (N=%s)' %(label, N) for label, N in
              zip(labels, [len(hangover[hangover.Sex == 'M']), len(hangover[hangover.Sex == 'F'])])]
    if violin:
        #Create custom artists
        simArtist = plt.Line2D((0, 1), (0, 0), color='r', linestyle='--', lw=3, alpha=0.4)
        handles.append(simArtist)
        labels.append('Baseline\n(No intoxication)')
    ax.legend(handles, labels)
    plt.subplots_adjust(top=0.90)


hviolin = sns.factorplot(x="Relative EtOH reduction after intoxication", y="Drinking Category", hue="Sex",
                         data=hangover, orient="h", size=3, aspect=3.5, palette="Set3",
                         kind="violin", split=True, cut=0, bw=.2)
brush_up('Split-violin plot', hviolin.axes[0, 0], violin=True)
hviolin.axes[0, 0].axvline(0, color='r', linestyle='--', lw=3, alpha=0.4)



lineplot = sns.factorplot(x="Drinking Category", y="Relative EtOH reduction after intoxication", hue="Sex",
                          data=hangover, size=3, aspect=3.5)
brush_up('Factor-Line plot', lineplot.axes[0, 0])



plt.show()
