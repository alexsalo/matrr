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
    plotMense(df)
    return fig

def plot_progesterone_mense(monkey):
    df = pd.DataFrame(list(MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).order_by('drinking_experiment__dex_date').values_list('mtd_mense_started', 'mtd_progesterone', 'drinking_experiment__dex_date')), columns=['mense', 'progesterone', 'date'])
    df_prog = df[np.isfinite(df['progesterone'])] #to remove nans
    fig = plt.figure(1, figsize=(20,10))
    plt.clf() #clear the plot
    plt.plot(df_prog.date, df_prog.progesterone, dc_colors_ol[monkey.mky_drinking_category])
    plotMense(df)
    plt.title('progesterone_mense for ' + monkey.__unicode__())
    return fig

def plot_mense_etoh_progesterone(monkey, Y1MAX=16.5):
    #get data for monkey
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).order_by('drinking_experiment__dex_date').order_by('drinking_experiment__dex_date')
    df = pd.DataFrame(list(mtds.values_list('mtd_mense_started', 'drinking_experiment__dex_date', 'mtd_etoh_g_kg', 'mtd_progesterone')), columns=['mense','date', 'etoh', 'progesterone'])

    #make figure
    fig = plt.figure(1, figsize=(20,10))
    plt.clf() #clear the plot
    plt.ylim([0.0, YMAX])

    #plot etoh and trend etoh
    xpred, ypred = lwr.wls(xrange(len(df.mense)), df.etoh, False, tau=0.45)
    plt.plot(df.date, df.etoh, dc_colors_o[monkey.mky_drinking_category], df.date, ypred, 'b-')

    #plot proesterone
    df_prog = df[np.isfinite(df['progesterone'])] #to remove nans
    df_prog.progesterone[df_prog.progesterone > YMAX] = YMAX #reduce amplified values
    plt.plot(df_prog.date, df_prog.progesterone, 'k-o', color = '0.75')

    #plot mense rects
    plotMense(df)

    #titles and legends
    plt.title('mense_etoh_progesterone for ' + monkey.__unicode__())
    plt.xlabel('Smarts')
    plt.ylabel('Probability')

    return fig

def plot_mense_etoh_progesterone_scaled_two_axis(monkey, Y1MAX=7.5, Y2MAX=16.5):
    #get data for monkey
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).order_by('drinking_experiment__dex_date').order_by('drinking_experiment__dex_date')
    df = pd.DataFrame(list(mtds.values_list('mtd_mense_started', 'drinking_experiment__dex_date', 'mtd_etoh_g_kg', 'mtd_progesterone')), columns=['mense','date', 'etoh', 'progesterone'])

    #make figure
    fig = plt.figure(figsize=(20,10))
    ax1 = fig.add_subplot(111)
    ax1.set_ylim([0.0, Y1MAX])

    #plot mense rects
    plotMense(df, ax1)

    #plot etoh and trend etoh
    xpred, ypred = lwr.wls(xrange(len(df.mense)), df.etoh, False, tau=0.45)
    ax1.plot(df.date, df.etoh, dc_colors_o[monkey.mky_drinking_category], label = 'EtOH intake')
    ax1.plot(df.date, ypred, 'b-', label = 'EtOH intake (trend*)')

    #plot proesterone
    ax2 = ax1.twinx()
    ax2.set_ylim([0.0, Y2MAX])
    df_prog = df[np.isfinite(df['progesterone'])] #to remove nans
    ax2.plot(df_prog.date, df_prog.progesterone, 'k-o', color = '0.75', label = 'Progesterone')

    #titles and legends
    ax2.set_ylabel('Progesterone')
    ax2.legend(loc=1, framealpha=1.0)

    ax1.set_title('EtOH Intake, progesterone and mense data, animal id: ' + str(monkey.mky_id))
    ax1.set_xlabel('Date')
    ax1.set_ylabel('EtOH Intake, g\kg')
    ax1.legend(loc=2, framealpha=1.0)
    ax1.grid()

    plt.tight_layout()

    return fig

def save_plots_by_monkey(monkeys, plot_method, plotfolder_name):
    for monkey in monkeys:
        fig = plot_method(monkey)
        path = '/home/alex/MATRR/' + plotfolder_name + '/'
        plotname = plotfolder_name + '_' + monkey.__unicode__() + '.png'
        fig.savefig(os.path.join(path, plotname), dpi=100)

#save_plots_by_monkey(mense_monkeys, plot_mense_etoh, 'mense_f_monkeys')
#save_plots_by_monkey(mense_monkeys, plot_progesterone_mense, 'progesterone_mense_f_monkeys')
#save_plots_by_monkey(mense_monkeys, plot_mense_etoh_progesterone, 'mense_etoh_progesterone_f_monkeys')
save_plots_by_monkey(mense_monkeys, plot_mense_etoh_progesterone_scaled_two_axis, 'mense_etoh_progesterone_scaled_two_axis_f_monkeys')

#m = Monkey.objects.get(mky_id=10077)
#plot_mense_etoh_progesterone_scaled_two_axis(m)


#pylab.show()