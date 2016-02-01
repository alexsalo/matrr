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


def mky_hi_low(mky, treshold):
    df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).
                           order_by('drinking_experiment__dex_date').
                           values_list('mtd_etoh_g_kg', 'monkey__mky_drinking_category')),
                      columns=['EtOH Today', 'Drinking Category'])
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
    return df

monkeys = Monkey.objects.filter(cohort__in=RHESUS_MALES).filter(mky_drinking_category__isnull=False)
df = collect_hi_low_dfs(monkeys, TRESHOLD)
pct_used = len(df[df.wasted]) * 1.0 / len(df)
print 'avg pct used: %s, std: %.4f' % (pct_used, np.std(USED_STD))

df = df[df.wasted]
#df[['etoh', 'next', 'dc']].groupby('dc').boxplot()
#plt.tight_layout()
import seaborn as sns
long_df = pd.melt(df, id_vars=['Drinking Category'], value_vars=['EtOH Today', 'EtOH Next Day'],
                  value_name='EtOH (normed per animal)', var_name='Day')
long_df['Drinking Category'] = long_df['Drinking Category'].astype('category').cat.set_categories(['LD', 'BD', 'HD', 'VHD'])

fig = sns.factorplot(x='Drinking Category', y='EtOH (normed per animal)', hue='Day', data=long_df, kind='box', size=8, aspect=1.5, legend_out=False)
plt.title('Factorplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
          (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)
fig.axes[0, 0].set_ylim(-2, 4)

# sns.swarmplot(x='Drinking Category', y="EtOH (normed per animal)", hue="Day", data=long_df, size=5)
# plt.title('Swarmplot for hangover drinking\nTreshold: %s (avg pct used %.2f $\pm$ %.2f)' %
#           (TRESHOLD, pct_used, np.std(USED_STD)), fontsize=14)

plt.show()
