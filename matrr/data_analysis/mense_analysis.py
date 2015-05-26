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

def plot_mense_etoh_progesterone_scaled_two_axis(monkey, Y1MAX=7.5, Y2MAX=16.5, FONT_SIZE=20, TICK_LABEL_SIZE=16, PROGESTERON_LW=1.2, TITLE='', TRUNCATE=False):
    #get data for monkey
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).order_by('drinking_experiment__dex_date')
    if TRUNCATE:
        mtds = mtds.filter(drinking_experiment__dex_date__gte='2012-05-20')
    df = pd.DataFrame(list(mtds.values_list('mtd_mense_started', 'drinking_experiment__dex_date', 'mtd_etoh_g_kg', 'mtd_progesterone')), columns=['mense','date', 'etoh', 'progesterone'])

    #make figure
    fig = plt.figure(figsize=(20,10))
    ax1 = fig.add_subplot(111)
    ax1.set_ylim([-0.1, Y1MAX])

    #plot mense rects
    plotMense(df, ax1)

    #plot etoh and trend etoh
    xpred, ypred = lwr.wls(xrange(len(df.mense)), df.etoh, False, tau=0.45)
    ax1.plot(df.date, df.etoh, dc_colors_o[monkey.mky_drinking_category], label = 'EtOH intake')
    ax1.plot(df.date, ypred, '-', color = '#006400', lw=6, label = 'EtOH intake (trend*)')

    #plot proesterone
    ax2 = ax1.twinx()
    ax2.set_ylim([-0.1, Y2MAX])
    df_prog = df[np.isfinite(df['progesterone'])] #to remove nans
    print_full(df)
    ax2.plot(df_prog.date, df_prog.progesterone, 'b-o', lw=PROGESTERON_LW, label = 'Progesterone')
    #ax2.plot(df_prog.date, df_prog.progesterone, 'k-o', color = 0.7, label = 'Progesterone')

    # ###plot avg pre-post lunal phases
    # df = df.set_index('date')
    #
    # #get peaks
    # dates = list(df.index[df.mense].values)
    # peaks_progesterone = []
    # for i in range(1,len(dates),1):
    #     df_period = df[dates[i-1]:dates[i]]
    #     peak_pos = df_period.progesterone.argmax()
    #     if not pd.isnull(peak_pos):
    #         peaks_progesterone.append(peak_pos)
    #
    # #get all periods and corresponding etohs
    # periods_for_avg = sorted(dates + peaks_progesterone)
    # etohs = [df[periods_for_avg[i-1]:periods_for_avg[i]].etoh.mean() for i, date in enumerate(periods_for_avg)][1:]
    #
    # #plot horizontal lines
    # [ax1.plot((periods_for_avg[i], periods_for_avg[i+1]), (etoh, etoh), color=pre_post_luni_phase[i%2],marker = '|', alpha=0.8, linewidth=2) for i, etoh in enumerate(etohs)]

    #titles and legends
    ax2.set_ylabel('Progesterone, ng/mL', fontsize=FONT_SIZE)
    ax2.legend(loc=1, framealpha=1.0, prop={'size':FONT_SIZE})
    ax2.tick_params(axis='both', which='major', labelsize=TICK_LABEL_SIZE)

    if TITLE == '':
        TITLE = 'EtOH Intake, progesterone and mense data, animal id: ' + str(monkey.mky_id)
    ax1.set_title(TITLE, fontsize=FONT_SIZE, y=1.03)
    ax1.set_xlabel('Date', fontsize=FONT_SIZE)
    ax1.set_ylabel('EtOH Intake, g\kg', fontsize=FONT_SIZE)
    ax1.legend(loc=2, framealpha=1.0, prop={'size':FONT_SIZE})
    ax1.tick_params(axis='both', which='major', labelsize=TICK_LABEL_SIZE)
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
#save_plots_by_monkey(mense_monkeys, plot_mense_etoh_progesterone_scaled_two_axis, 'mense_etoh_progesterone_scaled_two_axis_f_monkeys_conf')

m = Monkey.objects.get(mky_id=10077)
plot_mense_etoh_progesterone_scaled_two_axis(m, Y1MAX = 6, Y2MAX=12, FONT_SIZE=26, TICK_LABEL_SIZE = 22, PROGESTERON_LW=2.2,
                TITLE='Longitudial ethanol intakes and menstrual cycle progesterone and menses, animal id: 10072',
                TRUNCATE=True)


pylab.show()