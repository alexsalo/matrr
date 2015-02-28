__author__ = 'alex'
from header import *

mense_monkeys = Monkey.objects.filter(mky_id=mense_monkeys_ids[1])

def plot_mense_etoh(monkey):
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=Monkey.objects.get(mky_id=10073)).order_by('drinking_experiment__dex_date')
    import pandas as pd
    df = pd.DataFrame(list(mtds.values_list('mtd_mense_started', 'drinking_experiment__dex_date', 'mtd_etoh_g_kg')), columns=['mense','date', 'etoh'])
    print df
    import lwr
    xpred, ypred = lwr.wls(xrange(len(df.mense)), df.etoh, False)
    plt.plot(df.date, df.etoh, 'go', df.date, ypred, 'b-')
    [plt.axvline(date, linewidth=1, color='r', linestyle='solid') for date in list(df.date[df.mense])]

plot_mense_etoh(mense_monkeys[0])

pylab.show()