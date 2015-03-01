__author__ = 'alex'
from header import *

mense_monkeys = Monkey.objects.filter(mky_id__in=mense_monkeys_ids)

def plot_mense_etoh(monkey):
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).order_by('drinking_experiment__dex_date')
    df = pd.DataFrame(list(mtds.values_list('mtd_mense_started', 'drinking_experiment__dex_date', 'mtd_etoh_g_kg')), columns=['mense','date', 'etoh'])
    #print df
    xpred, ypred = lwr.wls(xrange(len(df.mense)), df.etoh, False, tau=0.45)
    fig = plt.figure(1, figsize=(20,10))
    plt.clf() #clear the plot
    plt.plot(df.date, df.etoh, dc_colors_o[monkey.mky_drinking_category], df.date, ypred, 'b-')
    plt.title('mense_etoh for ' + monkey.__unicode__())
    [plt.axvline(date, linewidth=1, color='r', linestyle='solid') for date in list(df.date[df.mense])]
    return fig

def save_plot_feature_meds_by_stage():
    for monkey in mense_monkeys:
        fig = plot_mense_etoh(monkey)
        path = '/home/alex/MATRR/mense_f_monkeys/'
        plotname = 'mense_f_monkeys_' + monkey.__unicode__() + '.png'
        fig.savefig(os.path.join(path, plotname), dpi=100)

save_plot_feature_meds_by_stage()



#pylab.show()