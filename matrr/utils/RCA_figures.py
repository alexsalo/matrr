import numpy
from scipy import stats
from collections import defaultdict
from matplotlib import pyplot, gridspec, ticker
from matrr import plotting, models
from matrr.utils import gadgets, parallel_plot


def popcount_figure(categories, y_value_callable, y_label, fig_size=(25, 15), tick_size=22, title_size=30,  label_size=26):
    """
    Straight-up copy of matrr.utils.alcohol_drinking_category.rhesus_category_parallel_classification_stability_popcount()

    Needed to remove the "Figure 4" text.
    """
    fig = pyplot.figure(figsize=fig_size, dpi=plotting.DEFAULT_DPI)
    #   only change.  #fig.text(.92, .96, "Figure 4", fontsize=title_size)
    gs = gridspec.GridSpec(6, 1)
    gs.update(left=0.05, right=0.98, top=.95, bottom=.04, hspace=.25)
    etoh_subplot = fig.add_subplot(gs[0:4,:])
    pop_subplot = fig.add_subplot(gs[4:,:], sharex=etoh_subplot)

    etoh_subplot.set_ylabel(y_label, fontdict={'fontsize': label_size})

    plot_x = range(1,5,1)
    etoh_category_values = defaultdict(lambda: defaultdict(lambda: list()))
    for three_months in plot_x:
        etoh_data = y_value_callable(plotting.ALL_RHESUS_DRINKERS, fieldname='mtd_etoh_g_kg',  three_months=three_months)
        for monkey in etoh_data.iterkeys():
            key = plotting.RHESUS_MONKEY_CATEGORY[monkey]
            etoh_category_values[key][three_months].append(etoh_data[monkey])

    base_alpha = .35
    for key in categories:
        category_dict = etoh_category_values[key]
        plot_y = list()
        std_error = list()
        for x in plot_x:
            _yvalues = category_dict[x]
            _avg = numpy.average(_yvalues)
            _err = stats.sem(_yvalues)
            plot_y.append(_avg)
            std_error.append(_err)
        plot_y = numpy.array(plot_y)
        std_error = numpy.array(std_error)

        if key in ['HD', 'BD']:
            alpha = .5 * base_alpha
        else:
            alpha = base_alpha
        etoh_subplot.plot(plot_x, plot_y, c=plotting.RHESUS_COLORS[key], linewidth=5)
        etoh_subplot.scatter(plot_x, plot_y, c=plotting.RHESUS_COLORS[key], edgecolor=plotting.RHESUS_COLORS[key], s=150, marker=plotting.DRINKING_CATEGORY_MARKER[key], label=key)
        etoh_subplot.fill_between(plot_x, plot_y-std_error, plot_y+std_error, alpha=alpha, edgecolor=plotting.RHESUS_COLORS[key], facecolor=plotting.RHESUS_COLORS[key])
    etoh_subplot.legend(loc=1, frameon=True, prop={'size': tick_size})

    ###############
    ordinals = ["First", "Second", "Third", "Fourth"]
    x_base = numpy.array(range(1,5,1))
    twelve_mo_category_pop_count = dict()
    for key in plotting.DRINKING_CATEGORIES:
        twelve_mo_category_pop_count[key] = len(plotting.RHESUS_DRINKERS_DISTINCT[key])

    for ordinal, x_start in zip(ordinals, x_base - .2):
        x_val = x_start
        quarter_population = list(gadgets.get_category_population_by_quarter(ordinal, monkeys=plotting.ALL_RHESUS_DRINKERS))
        for key in plotting.DRINKING_CATEGORIES:
            x_values = list()
            y_values = list()
            x_values.append(x_val)
            y_value = quarter_population.count(key) - twelve_mo_category_pop_count[key]
            y_values.append(y_value)
            color = plotting.RHESUS_COLORS[key]
            x_val += .1
            pop_subplot.bar(x_values, y_values, width=.05, color=color, edgecolor=color)
    for index, subplot in enumerate([etoh_subplot, pop_subplot]):
        subplot.tick_params(axis='both', which='both', labelsize=tick_size)
        subplot.set_xlim(xmin=.75, xmax=len(plot_x)+.2)
        subplot.yaxis.set_major_locator(ticker.MaxNLocator(prune='lower'))
    etoh_subplot.grid(True, which='major', axis='both')
    pop_subplot.set_ylabel(r'$\Delta$ Population', fontdict={'fontsize': label_size})
    pop_subplot.grid(True, which='major', axis='y')
    pop_subplot.axhspan(-.1, .1, color='black', alpha=.7, zorder=-100)
    pop_subplot.set_yticks(range(-6,7,2))
    etoh_subplot.get_xaxis().set_visible(False)
    pop_subplot.set_xticks(plot_x)
    x_labels = ["%s 3 months" % x for x in ordinals]
    pop_subplot.set_xticklabels(x_labels, size=tick_size)
    legend = pop_subplot.legend((), title="Population change from 12 Month Study", loc=9, frameon=False)
    pyplot.setp(legend.get_title(), fontsize=title_size)
    return fig


def create_rca_graphs(output_path='', graphs='figa3,figa4,mdr', format='png', dpi=1000):
    figures = list()
    names = list()

    if 'figa3' in graphs:
#        figures.append(monkey_bec_consumption(monkey=10062))
#        names.append('VHD')

#        figures.append(monkey_bec_consumption(monkey=10060))
#        names.append('HD')

#        figures.append(monkey_bec_consumption(monkey=10056))
#        names.append('BD')

#        figures.append(monkey_bec_consumption(monkey=10052))
#        names.append('LD')
        print 'Figure 3 MUST BE RENDERED SPECIAL!!!!'
        print 'Look thru the code of this script.  Render them individually, save them manually, then stich them together in photoshop, adding labels.'
    if 'figa4' in graphs:
        figures.append(
            popcount_figure(plotting.DRINKING_CATEGORIES,
                            gadgets.gather_three_month_monkey_average_by_fieldname,
                            "Average Daily EtOH Intake by Category (g/kg)",
                            )
        )
        names.append('figa4')
    if 'mdr' in graphs:
        pp = parallel_plot.MATRRParallelPlot(cached=False, monkeys=models.Monkey.objects.Drinkers())
        pp.draw_parallel_plot(lw=3, alpha=.5)
        figures.append(pp.figure)
        names.append('mdr')

    if format:
        for FigName in zip(figures, names):
            fig, name = FigName
            filename = output_path + '%s.%s' % (name, format)
            fig.savefig(filename, format=format ,dpi=dpi)
