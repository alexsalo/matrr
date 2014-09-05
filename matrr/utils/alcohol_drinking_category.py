from collections import defaultdict
from scipy import stats
from scipy.interpolate import spline
from django.db.models import Max, Min, Avg, Sum
import gc
import matplotlib
from matplotlib.ticker import MaxNLocator, NullLocator
import numpy
from matplotlib import pyplot, gridspec, cm, colors
import operator
from matrr import plotting
from matrr.models import Monkey, MonkeyToDrinkingExperiment, MonkeyBEC
from matrr.plotting import DRINKING_CATEGORIES, DEFAULT_DPI, RHESUS_COLORS, RHESUS_MONKEY_COLORS, \
    RHESUS_MONKEY_MARKERS, ALL_RHESUS_DRINKERS, DRINKING_CATEGORY_MARKER, RHESUS_DRINKERS_DISTINCT, \
    RHESUS_MONKEY_CATEGORY, plot_tools, DEFAULT_FIG_SIZE
from matrr.utils import gadgets


def etoh_gkg_forced_histogram(subplot, tick_size=16, label_size=20):
    monkeys = Monkey.objects.Drinkers().filter(cohort__in=[5,6,9,10]).values_list('pk', flat=True).distinct()

    increment = .25
    limits = numpy.arange(0, 7, increment)
    gkg_daycounts = numpy.zeros(len(limits))
    for monkey in monkeys:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
        if not mtds.count():
            continue
        max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
        min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
        days = float((max_date-min_date).days)
        for index, limit in enumerate(limits):
            if not limit:
                continue
            _count = mtds.filter(mtd_etoh_g_kg__gt=limits[index-1]).filter(mtd_etoh_g_kg__lte=limits[index]).count()
            gkg_daycounts[index] += _count / days

    gkg_daycounts = list(gkg_daycounts)
    for index, xy in enumerate(zip(limits, gkg_daycounts)):
        x, y = xy
        color = 'gold' if index % 2 else 'orange'
        subplot.bar(x, y, width=increment, color=color, edgecolor=None)

    newx = numpy.linspace(min(limits), max(limits), 40) # smooth out the x axis
    newy = spline(limits, gkg_daycounts, newx) # smooth out the y axis
    subplot.plot(newx, newy, color='r', linewidth=3) # smoothed line

    xmax = 7 # monkeys are cut off at 7 gkg
    ymax = max(gkg_daycounts)*1.005
    subplot.set_ylim(ymin=0, ymax=ymax)
    subplot.set_xlim(xmin=0, xmax=xmax)
    subplot.set_ylabel("Summation of Percentage of Days of EtOH Intake", size=label_size)
    subplot.set_xlabel("EtOH Intake (g/kg)",  size=label_size)
    subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
#    subplot.set_yticklabels([])
    return subplot

def etoh_gkg_monkeybargraph(subplot, limit, cutoff=None, tick_size=12, label_size=16):
    monkeys = Monkey.objects.Drinkers().filter(cohort__in=[5,6,9,10]).values_list('pk', flat=True).distinct()
    keys = list()
    values = list()
    for monkey in monkeys:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
        if not mtds.count():
            continue
        max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
        min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
        days = float((max_date-min_date).days)
        _count = mtds.filter(mtd_etoh_g_kg__gt=limit).count()
        values.append(_count / days)
        keys.append(str(monkey))

    sorted_x = sorted(zip(keys, values), key=operator.itemgetter(1))
    keys = list()
    values = list()
    for k, v in sorted_x:
        keys.append(k)
        values.append(v)

    xaxis = range(len(values))
    for x, y in zip(xaxis, values):
        color = 'navy' if x % 2 else 'slateblue'
        subplot.bar(x, y, width=1, color=color, edgecolor=None)
    if cutoff:
        subplot.axhspan(0, cutoff, color='red', alpha=.4, zorder=-100)
        subplot.text(1, cutoff, "%d%%" % int(cutoff*100), size=label_size)

    subplot.set_xlim(xmax=len(monkeys))
    subplot.set_xticks([])
    subplot.set_xlabel("Monkey", size=tick_size)
    stupid_legend = subplot.legend((), title="%% Days > %d g/kg" % limit, loc=9, frameon=False)
    stupid_title = stupid_legend.get_title()
    stupid_title.set_fontsize(int(tick_size*.9))
    ytick_labels = ["%d" % (2*10*x) for x in range(6)]
    subplot.set_yticklabels(ytick_labels, size=tick_size)
    return subplot

def rhesus_category_scatterplot(subplot, collect_xy_data, xy_kwargs=None, include_regression=False):
    xy_kwargs = xy_kwargs if xy_kwargs is not None else dict()
    all_x = list()
    all_y = list()
    for idx, key in enumerate(DRINKING_CATEGORIES):
        color = RHESUS_COLORS[key]
        _x, _y = collect_xy_data(key, **xy_kwargs)
        all_x.extend(_x)
        all_y.extend(_y)
        subplot.scatter(_x, _y, color=color, edgecolor='none', s=100, label=key, marker=DRINKING_CATEGORY_MARKER[key], alpha=1)
        plot_tools.create_convex_hull_polygon(subplot, _x, _y, color)

    # regression line
    if include_regression:
        all_x = numpy.array(all_x)
        all_y = numpy.array(all_y)
        slope, intercept, r_value, p_value, std_err = stats.linregress(all_x, all_y)

        reg_label = "Fit: p=%f" % p_value
        subplot.plot(all_x, all_x * slope + intercept, color='black', label=reg_label)

    handles, labels = subplot.get_legend_handles_labels()
    return subplot, handles, labels

def gkg_count_upperlimit(upper_limit, monkeys):
    from matrr import models
    import operator
    data = dict()
    for _mky in monkeys:
        _mtds = models.MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=_mky)
        data[_mky] = _mtds.filter(mtd_etoh_g_kg__lte=upper_limit).count()

    sorted_data = sorted(data.iteritems(), key=operator.itemgetter(1))
    return numpy.array(sorted_data)




def rhesus_etoh_gkg_forced_monkeybargraphhistogram(fig_size=(25, 15), fig_title="Figure 1"):
    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(1, 1)
    gs.update(left=0.055, right=0.492, top=.95, bottom=.08)

    tick_size = 30
    title_size = 32
    label_size = 34
    panel_label_size = 28

    fig.text(.03, .96, fig_title, fontsize=title_size)
    fig.text(.23, .96, "Panel (A)", fontsize=panel_label_size)
    fig.text(.71, .96, "Panel (B)", fontsize=panel_label_size)

#	Histogram, left
    subplot = fig.add_subplot(gs[:,:])
    etoh_gkg_forced_histogram(subplot, tick_size=tick_size, label_size=label_size)

#	Histograms, right
    gs = gridspec.GridSpec(1, 3)
    gs.update(left=0.507, right=0.945, top=.95, bottom=.08, wspace=.1, hspace=0)
    subplot = None
    cutoffs = {2:.55, 3:.2, 4:.1}
    for limit in range(2, 5, 1):
        gs_index = limit - 2
        subplot = fig.add_subplot(gs[:,gs_index:gs_index+1], sharex=subplot, sharey=subplot)
        subplot = etoh_gkg_monkeybargraph(subplot, limit, cutoff=cutoffs[limit], tick_size=tick_size, label_size=label_size)
        subplot.yaxis.tick_right()
        subplot.yaxis.set_visible(False)
        subplot.tick_params(axis='both', which='major', labelsize=tick_size)
        subplot.tick_params(axis='both', which='minor', labelsize=tick_size)

    subplot.yaxis.set_visible(True)
    subplot.yaxis.set_label_position('right')
    subplot.set_yticks([.2, .4, .6, .8, 1])
    subplot.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], size=tick_size)
    return fig

def rhesus_etoh_gkg_stackedbargraph(limit_step=.1, fig_size=(25, 15), fig_title="Figure 2"):
    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.05, right=0.98, top=.95, bottom=.08, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])

    limits = numpy.arange(1, 9, limit_step)
    bottom = numpy.zeros(len(limits))
    color_index = 0
    for key in DRINKING_CATEGORIES:
        width = 1 / (1. / limit_step)
        gkg_daycounts = numpy.zeros(len(limits))
        for monkey in RHESUS_DRINKERS_DISTINCT[key]:
            mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
            if not mtds.count():
                continue
            max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
            min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
            days = float((max_date - min_date).days)
            for index, limit in enumerate(limits):
                _count = mtds.filter(mtd_etoh_g_kg__gt=limit).count()
                gkg_daycounts[index] += _count / days

        gkg_daycounts = list(gkg_daycounts)
        color = RHESUS_COLORS[key]
        color_index += 1
        subplot.bar(limits, gkg_daycounts, bottom=bottom, width=width, color=color, label=key, alpha=1)
        bottom += gkg_daycounts

    subplot.set_xlim(xmin=1, xmax=7)

    tick_size = 30
    title_size = 32
    label_size = 34
    fig.text(.05, .96, fig_title, fontsize=title_size)

    subplot.legend(prop={'size': tick_size})
#    subplot.set_yticklabels([])
    subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
    subplot.set_ylabel("Aggregation of EtOH Intake Days by Category", size=label_size)
    subplot.set_xlabel("Percentage of Days Exceeding EtOH Intake(g/kg)", size=label_size)
    return fig

def rhesus_etoh_bec_scatter(monkey_one=10065, monkey_two=10052, monkey_three=0, fig_size=(25, 15)):
    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(2, 1)
    gs.update(left=0.05, right=0.94, top=.95, bottom=.08, wspace=.0, hspace=.04)
    top_subplot = fig.add_subplot(gs[0])
    bottom_subplot_left = fig.add_subplot(gs[1], sharex=top_subplot)
    bottom_subplot_right = bottom_subplot_left.twinx()

    monkey_ids = [monkey_two, monkey_one]
    if monkey_three:
        monkey_ids.append(monkey_three)

    marker_size = 90

    # this is dumb, i know.
    # matplotlib won't plot dates on the axis of a shared axis.  I think this is a known bug, suggested workarounds have failed
    mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_ids).order_by('drinking_experiment__dex_date')
    all_dates = mtds.dates('drinking_experiment__dex_date', 'day')
    x_dates = dict()
    date_index = 0
    for x in all_dates:
        x_dates[x] = date_index
        date_index += 1

    for monkey in monkey_ids:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).order_by('drinking_experiment__dex_date')
        x_axis_dates = mtds.dates('drinking_experiment__dex_date', 'day')
        x_axis = list()
        for x in x_axis_dates:
            x_axis.append(x_dates[x])
        y_axis = mtds.values_list('mtd_etoh_g_kg', flat=True)
        top_subplot.scatter(x_axis, y_axis, color=RHESUS_MONKEY_COLORS[monkey], marker=RHESUS_MONKEY_MARKERS[monkey], s=marker_size, label=str(monkey))
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).order_by('bec_collect_date')
        x_axis_dates = becs.dates('bec_collect_date', 'day')
        x_axis = list()
        for x in x_axis_dates:
            x_axis.append(x_dates[x])
        y_axis = becs.values_list('bec_mg_pct', flat=True)
        bottom_subplot_left.scatter(x_axis, y_axis, color=RHESUS_MONKEY_COLORS[monkey], marker=RHESUS_MONKEY_MARKERS[monkey], s=marker_size, label=str(monkey))
        if monkey in RHESUS_DRINKERS_DISTINCT['VHD']:
            y_axis = becs.values_list('bec_gkg_etoh', 'bec_daily_gkg_etoh')
            y_axis = [y[0]/y[1] for y in y_axis]
            bottom_subplot_right.plot(x_axis, y_axis, color=RHESUS_MONKEY_COLORS[monkey], lw=3, alpha=.5, label="Percent Daily Intake at Sample, %d" % monkey)

    tick_size=22
    title_size=30
    label_size=26
    legend_size = tick_size
    fig.text(.82, .96, "Supplement 6", fontsize=title_size)

    top_subplot.set_ylim(ymin=0)
    top_subplot.set_xlim(xmin=0, xmax=date_index)
    bottom_subplot_left.set_ylim(ymin=0)
    bottom_subplot_left.set_xlim(xmin=0, xmax=date_index)
    top_subplot.axhspan(3.98, 4.02, color='black', alpha=.4, zorder=-100)
    bottom_subplot_left.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    bottom_subplot_left.text(0, 82, "80 mg pct", size=tick_size)
    line_ticks = numpy.arange(0,1.01,.2)
    bottom_subplot_right.set_yticks(line_ticks)
    bottom_subplot_right.set_yticklabels(["%d%%" % int(tick*100) for tick in line_ticks])
    for subplot in [top_subplot, bottom_subplot_left, bottom_subplot_right]:
        subplot.tick_params(axis='both', which='major', labelsize=tick_size)
        subplot.tick_params(axis='both', which='minor', labelsize=tick_size)

    top_subplot.legend(loc=2, prop={'size': legend_size})
    bottom_subplot_left.legend(loc=2, prop={'size': legend_size})
    bottom_subplot_right.legend(loc=1, prop={'size': legend_size})

    top_subplot.text(.42, .92, "Daily EtOH Intake", size=title_size, transform=top_subplot.transAxes)
    top_subplot.set_ylabel("EtOH (g/kg)", size=label_size)
    top_subplot.set_xlabel("Open Access Days", size=label_size)
    top_subplot.get_xaxis().set_visible(False)

    bottom_subplot_left.text(.45, .92, "Daily BEC", size=title_size, transform=bottom_subplot_left.transAxes)
    bottom_subplot_left.set_ylabel("BEC (mg/dl)", size=label_size)
    bottom_subplot_left.set_xlabel("Days", size=label_size)
    bottom_subplot_right.set_ylabel("% Daily EtOH taken before Blood Sample", size=label_size)
    return fig

def rhesus_category_parallel_classification_stability_popcount(categories, y_value_callable, y_label, fig_size=(25, 15), tick_size=22, title_size=30,  label_size=26):
    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    fig.text(.92, .96, "Figure 4", fontsize=title_size)
    gs = gridspec.GridSpec(6, 1)
    gs.update(left=0.05, right=0.98, top=.95, bottom=.04, hspace=.25)
    etoh_subplot = fig.add_subplot(gs[0:4,:])
    pop_subplot = fig.add_subplot(gs[4:,:], sharex=etoh_subplot)

    etoh_subplot.set_ylabel(y_label, fontdict={'fontsize': label_size})

    plot_x = range(1,5,1)
    etoh_category_values = defaultdict(lambda: defaultdict(lambda: list()))
    for three_months in plot_x:
        etoh_data = y_value_callable(ALL_RHESUS_DRINKERS, fieldname='mtd_etoh_g_kg',  three_months=three_months)
        for monkey in etoh_data.iterkeys():
            key = RHESUS_MONKEY_CATEGORY[monkey]
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
        etoh_subplot.plot(plot_x, plot_y, c=RHESUS_COLORS[key], linewidth=5)
        etoh_subplot.scatter(plot_x, plot_y, c=RHESUS_COLORS[key], edgecolor=RHESUS_COLORS[key], s=150, marker=DRINKING_CATEGORY_MARKER[key], label=key)
        etoh_subplot.fill_between(plot_x, plot_y-std_error, plot_y+std_error, alpha=alpha, edgecolor=RHESUS_COLORS[key], facecolor=RHESUS_COLORS[key])
    etoh_subplot.legend(loc=1, frameon=True, prop={'size': tick_size})

    ###############
    ordinals = ["First", "Second", "Third", "Fourth"]
    x_base = numpy.array(range(1,5,1))
    twelve_mo_category_pop_count = dict()
    for key in DRINKING_CATEGORIES:
        twelve_mo_category_pop_count[key] = len(RHESUS_DRINKERS_DISTINCT[key])

    for ordinal, x_start in zip(ordinals, x_base - .2):
        x_val = x_start
        quarter_population = list(gadgets.get_category_population_by_quarter(ordinal, monkeys=ALL_RHESUS_DRINKERS))
        for key in DRINKING_CATEGORIES:
            x_values = list()
            y_values = list()
            x_values.append(x_val)
            y_value = quarter_population.count(key) - twelve_mo_category_pop_count[key]
            y_values.append(y_value)
            color = RHESUS_COLORS[key]
            x_val += .1
            pop_subplot.bar(x_values, y_values, width=.05, color=color, edgecolor=color)
    for index, subplot in enumerate([etoh_subplot, pop_subplot]):
        subplot.tick_params(axis='both', which='both', labelsize=tick_size)
        subplot.set_xlim(xmin=.75, xmax=len(plot_x)+.2)
        subplot.yaxis.set_major_locator(MaxNLocator(prune='lower'))
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

def rhesus_category_parallel_classification_stability_popcount_3moAssignment(categories, y_value_callable, y_label, fig_size=(25, 15), tick_size=22, title_size=30,  label_size=26):
    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    fig.text(.82, .96, "Supplement 4", fontsize=title_size)
    gs = gridspec.GridSpec(6, 1)
    gs.update(left=0.05, right=0.98, top=.95, bottom=.04, hspace=.25)
    etoh_subplot = fig.add_subplot(gs[0:4,:])
    pop_subplot = fig.add_subplot(gs[4:,:], sharex=etoh_subplot)

    etoh_subplot.set_ylabel(y_label, fontdict={'fontsize': label_size})

    # Identify each monkey's category based on the first three months of OA, cuz that's what reviewer 2 thought was a good idea -.-
    three_mo_categories= dict()
    for _mky in ALL_RHESUS_DRINKERS:
        _mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=_mky).first_three_months_oa()
        three_mo_categories[_mky] = gadgets.identify_drinking_category(_mtds)

    # Next, collect each monkey's average gkg intake for each quarter, organized by category (as assigned by the first 3 months OA) and quarter
    plot_x = range(1,5,1)
    etoh_category_values = defaultdict(lambda: defaultdict(lambda: list()))
    for three_months in plot_x:
        etoh_data = y_value_callable(ALL_RHESUS_DRINKERS, fieldname='mtd_etoh_g_kg',  three_months=three_months)
        for monkey in etoh_data.iterkeys():
            _mky_category = three_mo_categories[monkey]
            etoh_category_values[_mky_category][three_months].append(etoh_data[monkey])

    # Now we build the top subplot
    # The top subplot shows the 4 categories average intake by quarter.  categories are assigned in based on the first 3 months of OA.
    # The average of each category is plotted, and the standard error of monkey values in each quarter/category are plotted around the avg
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
        etoh_subplot.plot(plot_x, plot_y, c=RHESUS_COLORS[key], linewidth=5)
        etoh_subplot.scatter(plot_x, plot_y, c=RHESUS_COLORS[key], edgecolor=RHESUS_COLORS[key], s=150, marker=DRINKING_CATEGORY_MARKER[key], label=key)
        etoh_subplot.fill_between(plot_x, plot_y-std_error, plot_y+std_error, alpha=alpha, edgecolor=RHESUS_COLORS[key], facecolor=RHESUS_COLORS[key])
    etoh_subplot.legend(loc=1, frameon=True, prop={'size': tick_size})

    ###############
    ordinals = ["First", "Second", "Third", "Fourth"]

    first_quarter_categories = list(gadgets.get_category_population_by_quarter('first', monkeys=ALL_RHESUS_DRINKERS))
    three_mo_category_pop_count = dict()
    for key in DRINKING_CATEGORIES:
        three_mo_category_pop_count[key] = first_quarter_categories.count(key)

    x_base = numpy.array(range(1,5,1))
    for ordinal, x_start in zip(ordinals, x_base - .2):
        x_val = x_start
        quarter_population = list(gadgets.get_category_population_by_quarter(ordinal, monkeys=ALL_RHESUS_DRINKERS))
        for key in DRINKING_CATEGORIES:
            x_values = list()
            y_values = list()
            x_values.append(x_val)
            y_value = quarter_population.count(key) - three_mo_category_pop_count[key]
            y_values.append(y_value)
            color = RHESUS_COLORS[key]
            x_val += .1
            pop_subplot.bar(x_values, y_values, width=.05, color=color, edgecolor=color)
    for index, subplot in enumerate([etoh_subplot, pop_subplot]):
        subplot.tick_params(axis='both', which='both', labelsize=tick_size)
        subplot.set_xlim(xmin=.75, xmax=len(plot_x)+.2)
        subplot.yaxis.set_major_locator(MaxNLocator(prune='lower'))
    etoh_subplot.grid(True, which='major', axis='both')
    pop_subplot.set_ylabel(r'$\Delta$ Population', fontdict={'fontsize': label_size})
    pop_subplot.grid(True, which='major', axis='y')
    pop_subplot.axhspan(-.1, .1, color='black', alpha=.7, zorder=-100)
    pop_subplot.set_yticks(range(-6,7,2))
    etoh_subplot.get_xaxis().set_visible(False)
    pop_subplot.set_xticks(plot_x)
    x_labels = ["%s 3 months" % x for x in ordinals]
    pop_subplot.set_xticklabels(x_labels, size=tick_size)
    legend = pop_subplot.legend((), title="Population change from Three Month Study", loc=9, frameon=False)
    pyplot.setp(legend.get_title(), fontsize=title_size)
    return fig

def rhesus_oa_pelletvolume_perday_perkg(fig_size=(25, 15), include_regression=False, fig_title="Figure 5"):
    def _oa_pelletvolume_perday_perkg(monkey_category):
        monkey_set = RHESUS_DRINKERS_DISTINCT[monkey_category]
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        x_data = list()
        y_data = list()
        for monkey in monkey_set:
            _mtds = mtds.filter(monkey=monkey).aggregate(Avg('mtd_etoh_intake'), Avg('mtd_total_pellets'),
                                                         Avg('mtd_weight'))
            vol_avg = _mtds['mtd_etoh_intake__avg']
            pel_avg = _mtds['mtd_total_pellets__avg']
            wgt_avg = _mtds['mtd_weight__avg']
            x_data.append(vol_avg / wgt_avg)
            y_data.append(pel_avg / wgt_avg)
        return x_data, y_data

    def _oa_pelletwater_perday_perkg(monkey_category):
        monkey_set = RHESUS_DRINKERS_DISTINCT[monkey_category]
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        x_data = list()
        y_data = list()
        for monkey in monkey_set:
            _mtds = mtds.filter(monkey=monkey).aggregate(Avg('mtd_veh_intake'), Avg('mtd_total_pellets'),
                                                         Avg('mtd_weight'))
            vol_avg = _mtds['mtd_veh_intake__avg']
            pel_avg = _mtds['mtd_total_pellets__avg']
            wgt_avg = _mtds['mtd_weight__avg']
            x_data.append(vol_avg / wgt_avg)
            y_data.append(pel_avg / wgt_avg)
        return x_data, y_data

    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.05, right=0.98, top=.95, bottom=.08, wspace=.08, hspace=0)

    tick_size=22
    title_size=30
    label_size=26
    fig.text(.92, .96, fig_title, fontsize=title_size)

    # main scatterplot, pellet vs etoh
    main_subplot = fig.add_subplot(main_gs[:])
    main_subplot, handles, labels = rhesus_category_scatterplot(main_subplot, _oa_pelletvolume_perday_perkg, include_regression=include_regression)
    main_subplot.legend(handles, labels, scatterpoints=1, loc='lower left')
    main_subplot.set_ylabel("Average pellet (count) / Average weight (kg), per monkey", size=label_size)
    main_subplot.set_xlabel("Average EtOH (mL.) / Average weight (kg), per monkey", size=label_size)
    main_subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    main_subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
    main_subplot.legend(loc=3, frameon=True, prop={'size': tick_size})

    # inset scatterplot, pellet vs water
    inset_plot = fig.add_axes([0.6, 0.69, 0.37, 0.23])
    inset_plot, handles, labels = rhesus_category_scatterplot(inset_plot, _oa_pelletwater_perday_perkg, include_regression=include_regression)
    inset_plot.set_title("H20 Intake vs pellets", size=tick_size)
    inset_plot.set_ylabel("Pellet/Weight/Monkey", size=tick_size)
    inset_plot.set_xlabel("Water (mL.) / Weight(kg) / Monkey", size=tick_size)
    ## Because the legend is almost the same as the main_subplot's legend, we dont need to show most of the keys
    ## but we do want to show the regression fit, and large enough to read without hiding the scatterplot
    if include_regression:
        index = 0
        for index, label in enumerate(labels):
            if 'Fit' in label:
                break
        inset_legend = inset_plot.legend([handles[index]], [labels[index]], scatterpoints=1, loc='upper right')
        inset_legend.get_frame().set_alpha(0) # hide the legend's background, so it doesn't hide the scatterplot
    return fig

def rhesus_N_gkg_days(upper_limit, fig_size=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI):
    from matplotlib import pyplot
    from matrr import plotting
    import numpy
    monkeys = plotting.ALL_RHESUS_DRINKERS
    fig = pyplot.figure(figsize=fig_size, dpi=dpi)
    gs = gridspec.GridSpec(1, 1)
    gs.update(left=0.07, right=0.98, top=.95, bottom=.045, hspace=.25)
    ax1 = fig.add_subplot(gs[:, :])
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
    ax1.set_axisbelow(True)
    ax1.set_title("Days below %.02f g/kg" % float(upper_limit))
    ax1.set_ylabel("Count")
    ax1.set_xlabel("Monkey")

    sorted_data = gkg_count_upperlimit(upper_limit=upper_limit, monkeys=monkeys)
    idx = numpy.arange(len(sorted_data))
    width = .9
    for _x, _y, _mky in zip(idx, sorted_data[:,1], sorted_data[:,0]):
        if _y and _y != 0:
            ax1.bar(_x, _y, width, color=plotting.RHESUS_MONKEY_COLORS[int(_mky)])
    ax1.set_xticklabels([])

    supplement_title_size = 16
    supplement_title = "Supplement 2a" if upper_limit < 1 else "Supplement 2b"
    fig.text(.82, .96, supplement_title, fontsize=supplement_title_size)
    return fig

def rhesus_cohort_bargraph_gkg_per_quartile():
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(2, 2)
    gs_gap = .035
    main_gs.update(left=gs_gap, right=(1-gs_gap), top=(1-gs_gap), bottom=gs_gap, wspace=3*gs_gap, hspace=3*gs_gap)

    monkeys = RHESUS_DRINKERS_DISTINCT["LD"]
    monkeys.extend(RHESUS_DRINKERS_DISTINCT["BD"])
    monkeys.extend(RHESUS_DRINKERS_DISTINCT["HD"])
    monkeys.extend(RHESUS_DRINKERS_DISTINCT["VHD"])
    subplot = None
    for _quarter, _phonetic in enumerate(['1st', '2nd', '3rd', '4th']):
        _row = 0 if _quarter < 2 else 1
        _col = _quarter % 2
        subplot = fig.add_subplot(main_gs[_row, _col], sharey=subplot)
        subplot.set_title("%s Qtr" % _phonetic)
        subplot.set_xlabel("Monkey")
        subplot.set_ylabel("Ethanol (g/kg)")
        subplot.set_xticks([])
        subplot.set_yticks([])
        for _mky in monkeys:
            _mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=_mky)
            if _quarter == 0:
                _mtds = _mtds.first_three_months_oa()
            elif _quarter == 1:
                _mtds = _mtds.second_three_months_oa()
            elif _quarter == 2:
                _mtds = _mtds.third_three_months_oa()
            elif _quarter == 3:
                _mtds = _mtds.fourth_three_months_oa()
            else:
                raise Exception("CONGRATULATIONS!  You broke python!")  # unreachable code
            _category = gadgets.identify_drinking_category(_mtds)
            _color = RHESUS_COLORS[_category]
            _gkg_sum = _mtds.aggregate(gkg_sum=Sum('mtd_etoh_g_kg'))['gkg_sum']
            _bar = subplot.bar(monkeys.index(_mky), _gkg_sum, width=.8, color=_color, linewidth=1.2, align='center')[0]
            subplot.text(_bar.get_x()+_bar.get_width()/2., 10, "%d" % _mky, ha='center', va='bottom', rotation='vertical', color='white', size=8)

    supplement_title_size = 16
    fig.text(.82, .973, "Supplement 3a", fontsize=supplement_title_size)
    return fig

def rhesus_cohort_bargraph_gkg_per_year():
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(2, 2)
    gs_gap = .035
    main_gs.update(left=gs_gap, right=(1-gs_gap), top=(1-gs_gap), bottom=gs_gap, wspace=3*gs_gap, hspace=3*gs_gap)

    monkeys = RHESUS_DRINKERS_DISTINCT["LD"]
    monkeys.extend(RHESUS_DRINKERS_DISTINCT["BD"])
    monkeys.extend(RHESUS_DRINKERS_DISTINCT["HD"])
    monkeys.extend(RHESUS_DRINKERS_DISTINCT["VHD"])
    subplot = fig.add_subplot(main_gs[:, :])
    subplot.set_title("Twelve Months")
    subplot.set_xlabel("Monkey")
    subplot.set_ylabel("Ethanol (g/kg)")
    subplot.set_xticks([])
    subplot.set_yticks([])
    for _mky in monkeys:
        _mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=_mky)
        _category = gadgets.identify_drinking_category(_mtds)
        _color = RHESUS_COLORS[_category]
        _gkg_sum = _mtds.aggregate(gkg_sum=Sum('mtd_etoh_g_kg'))['gkg_sum']
        _bar = subplot.bar(monkeys.index(_mky), _gkg_sum, width=.8, color=_color, linewidth=1.2, align='center')[0]
        subplot.text(_bar.get_x()+_bar.get_width()/2., 10, "  %d" % _mky, ha='center', va='bottom', rotation='vertical', color='white', size=16)

    supplement_title_size = 16
    fig.text(.82, .973, "Supplement 3b", fontsize=supplement_title_size)
    return fig

def rhesus_category_bec_boxplot():
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(1, 1)
    gs.update(left=0.07, right=0.98, top=.95, bottom=.045, hspace=.25)
    subplot = fig.add_subplot(gs[:, :])

    for x_location, key in enumerate(DRINKING_CATEGORIES, start=1):
        category_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey__in=RHESUS_DRINKERS_DISTINCT[key])
        bec_values = category_becs.values_list('bec_mg_pct', flat=True)
        boxplot = subplot.boxplot(bec_values, positions=[x_location])
        pyplot.setp(boxplot['boxes'], linewidth=3, color=RHESUS_COLORS[key])
        pyplot.setp(boxplot['whiskers'], linewidth=3, color=RHESUS_COLORS[key])
    subplot.set_xlim(xmin=0, xmax=len(DRINKING_CATEGORIES)+1)

    supplement_title_size = 16
    fig.text(.82, .97, "Supplement 5", fontsize=supplement_title_size)

    subplot.legend()
    subplot.set_ylabel("BEC value, percent mg")
    subplot.set_xlabel("Category")
    subplot.set_xticks([])
    return fig

def monkey_bec_consumption(monkey=None, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, circle_max=plotting.DEFAULT_CIRCLE_MAX, circle_min=plotting.DEFAULT_CIRCLE_MIN):
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    cbc = monkey.cohort.cbc
    if circle_max < circle_min:
        circle_max = plotting.DEFAULT_CIRCLE_MAX
        circle_min = plotting.DEFAULT_CIRCLE_MIN
    else:
        if circle_max < 10:
            circle_max = plotting.DEFAULT_CIRCLE_MAX
        if circle_min < 1:
            circle_min = plotting.DEFAULT_CIRCLE_MIN

    drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
    bec_records = monkey.bec_records.all()
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
        bec_records = bec_records.filter(bec_collect_date__gte=from_date)
    if to_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
        bec_records = bec_records.filter(bec_collect_date__lte=from_date)
    if sample_before:
        bec_records = bec_records.filter(bec_sample__lte=sample_before)
    if sample_after:
        bec_records = bec_records.filter(bec_sample__gte=sample_after)
    if dex_type:
        from django.db.models import Max, Min

        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)
        max_date = drinking_experiments.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
        if max_date:
            bec_records = bec_records.filter(bec_collect_date__lte=max_date)
        min_date = drinking_experiments.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
        if min_date:
            bec_records = bec_records.filter(bec_collect_date__gte=min_date)

    drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

    if drinking_experiments.count() > 0 and bec_records.count() > 0:
        dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
    else:
        return None, False

    bar_y_label = 'BEC (% mg)'
    bar_color_label = 'Ethanol Intake (g/kg)'
    scatter_y_label = 'Ethanol Intake (g/kg)'
    scatter_color_label = 'Sample Vol. / Total Intake'
    scatter_size_label = 'Ethanol Bouts'
    induction_days = list()
    scatter_size = list()
    scatter_y = list() # yaxis
    scatter_color = list()
    bar_xaxis = list()
    bar_yaxis = list()
    bar_color = list()
    for index, date in enumerate(dates, 1):
        bec_rec = bec_records.filter(bec_collect_date=date)
        if bec_rec.count():
            bec_rec = bec_rec[0]
            bar_yaxis.append(bec_rec.bec_mg_pct)
            bar_color.append(bec_rec.bec_daily_gkg_etoh)
#            scatter_size.append(bec_rec.bec_pct_intake)
            scatter_color.append(bec_rec.bec_pct_intake)
            bar_xaxis.append(index)
            if not bar_color_label:
                bar_color_label = bec_rec._meta.get_field('bec_pct_intake').verbose_name
        else:
            scatter_color.append(0)
#            scatter_size.append(.001)

        de = drinking_experiments.get(drinking_experiment__dex_date=date)
        if de.drinking_experiment.dex_type == 'Induction':
            induction_days.append(index)
        scatter_y.append(de.mtd_etoh_g_kg)
#        scatter_color.append(de.mtd_etoh_bout)
        scatter_size.append(de.mtd_etoh_bout)

    xaxis = numpy.array(range(1, len(scatter_size) + 1))
    scatter_size = numpy.array(scatter_size)
    scatter_color = numpy.array(scatter_color)
    bar_color = numpy.array(bar_color)
    induction_days = numpy.array(induction_days)

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    tick_size = 18
    label_size = 22
    title_size = 30
    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.07, right=0.93, top=.95, bottom=.08, hspace=.07, wspace=.05)
    bec_con_main_plot = fig.add_subplot(main_gs[0:2, 0:39])
    bec_con_main_plot.set_xticks([])

    size_min = circle_min
    size_scale = circle_max - size_min
    size_max = cbc.cbc_mtd_etoh_bout_max
    rescaled_volumes = [(vol / size_max) * size_scale + size_min for vol in
                        scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)

    s = bec_con_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)

    y_max = cbc.cbc_mtd_etoh_g_kg_max
    graph_y_max = y_max + y_max * 0.25
    if len(induction_days) and len(induction_days) != len(xaxis):
        bec_con_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                              edgecolor='black', zorder=-100)

    bec_con_main_plot.set_ylabel(scatter_y_label)
    bec_con_main_plot.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")),
                                fontsize=title_size)

    bec_con_main_plot.set_ylim(0, graph_y_max)
    bec_con_main_plot.set_xlim(0, len(xaxis) + 2)

    max_y_int = int(round(y_max * 1.25))
    y_tick_int = max(int(round(max_y_int / 5)), 1)
    bec_con_main_plot.set_yticks(range(0, max_y_int, y_tick_int))
    bec_con_main_plot.yaxis.get_label().set_position((0, 0.6))
    bec_con_main_plot.yaxis.get_label().set_fontsize(label_size)

    bec_con_main_plot.tick_params(axis='both', which='major', labelsize=tick_size)
    bec_con_main_plot.tick_params(axis='both', which='minor', labelsize=tick_size)

    bec_con_main_color_plot = fig.add_subplot(main_gs[0:2, 39:])
    bec_con_main_color_plot.yaxis.get_label().set_fontsize(label_size)
    bec_con_main_color_plot.tick_params(axis='both', which='major', labelsize=tick_size)
    bec_con_main_color_plot.tick_params(axis='both', which='minor', labelsize=tick_size)
    cb = fig.colorbar(s, alpha=1, cax=bec_con_main_color_plot)
    cb.set_clim(cbc.cbc_bec_pct_intake_min, cbc.cbc_bec_pct_intake_max)
#    cb.set_clim(cbc.cbc_mtd_etoh_bout_min, cbc.cbc_mtd_etoh_bout_max)
    cb.set_label(scatter_color_label)

    #	regression line
    fit = numpy.polyfit(xaxis, scatter_y, 3)
    xr = numpy.polyval(fit, xaxis)
    bec_con_main_plot.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

    #    size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = size_scale / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = size_max / (len(y) - 1)
    bout_labels = [int(round(i * m)) for i in range(1, len(y))] # labels in the range as number of bouts
    bout_labels.insert(0, "1")
    bout_labels.insert(0, "")
    bout_labels.append("")

    bec_con_size_plot = fig.add_subplot(931)
    bec_con_size_plot.set_position((0.07, .879, .3, .07))
    bec_con_size_plot.scatter(x, y, s=size, alpha=0.4)
    bec_con_size_plot.set_xlabel(scatter_size_label)
    bec_con_size_plot.yaxis.set_major_locator(NullLocator())
    pyplot.setp(bec_con_size_plot, xticklabels=bout_labels)

    size_plot_xaxis_fontsize = 20
    size_plot_tick_fontsize = 16
    bec_con_size_plot.xaxis.get_label().set_fontsize(size_plot_xaxis_fontsize)
    bec_con_size_plot.tick_params(axis='both', which='major', labelsize=size_plot_tick_fontsize)
    bec_con_size_plot.tick_params(axis='both', which='minor', labelsize=size_plot_tick_fontsize)

    #	barplot
    bec_con_bar_plot = fig.add_subplot(main_gs[-1:, 0:39])

    bec_con_bar_plot.set_xlabel("Days", fontdict={'size': label_size})
    bec_con_bar_plot.set_ylabel(bar_y_label, fontdict={'size': label_size})
    bec_con_bar_plot.set_ylim(ymin=0, ymax=250)
    bec_con_bar_plot.tick_params(axis='both', which='major', labelsize=tick_size)
    bec_con_bar_plot.tick_params(axis='both', which='minor', labelsize=tick_size)

    bec_con_bar_plot.set_autoscalex_on(False)

    # normalize colors to use full range of colormap
    norm = colors.normalize(cbc.cbc_bec_daily_gkg_etoh_min, cbc.cbc_bec_daily_gkg_etoh_max)

    facecolors = list()
    for bar, x, color_value in zip(bar_yaxis, bar_xaxis, bar_color):
        color = cm.jet(norm(color_value))
        bec_con_bar_plot.bar(x, bar, width=2, color=color, edgecolor='none')
        facecolors.append(color)
    bec_con_bar_plot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    bec_con_bar_plot.text(0, 82, "80 mg pct", fontsize=size_plot_xaxis_fontsize)

    bec_con_bar_plot.set_xlim(0, len(xaxis) + 2)
    if len(induction_days) and len(induction_days) != len(xaxis):
        bec_con_bar_plot.bar(induction_days.min(), bec_con_bar_plot.get_ylim()[1], width=induction_days.max(), bottom=0,
                             color='black', alpha=.2, edgecolor='black', zorder=-100)

    # create a collection that we will use in colorbox
    col = matplotlib.collections.Collection(facecolors=facecolors, norm=norm, cmap=cm.jet)
    col.set_array(bar_color)

    # colorbar for bar plot
    bec_con_bar_color = fig.add_subplot(main_gs[-1:, 39:])
    v = numpy.linspace(cbc.cbc_bec_gkg_etoh_min, cbc.cbc_bec_gkg_etoh_max, 4, endpoint=True)
    cb = fig.colorbar(col, alpha=1, cax=bec_con_bar_color, ticks=v)
    cb.set_label(bar_color_label, fontsize=label_size)
    _ticks = [1.0,3.0,5.0]
    cb.set_ticks(_ticks)
    cb.set_ticklabels(["%.1f" % t for t in _ticks])
    bec_con_bar_color.tick_params(axis='both', which='major', labelsize=tick_size)
    bec_con_bar_color.tick_params(axis='both', which='minor', labelsize=tick_size)

    return fig

class MATRRBECEthanolIntakeScatterPlot():
    def __init__(self):
        pass

    figure = None
    title = "Supplement 7"
    scatter_x_label = 'Daily Ethanol Intake'
    scatter_y_label = 'BEC'
    scatter_color_label = 'Category'
    scatter_alpha = .7

    tick_size = 18
    label_size = 22
    title_size = 30

    becs = None

    def draw_figure(self):
        fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
        main_gs = gridspec.GridSpec(3, 3)
        main_gs.update(left=0.07, right=0.93, top=.95, bottom=.08, hspace=.07, wspace=.05)
        subplot = fig.add_subplot(main_gs[:,:])
        all_x = list()
        all_y = list()
        for category in plotting.DRINKING_CATEGORIES:
            x_axis = self.get_x_axis(category)
            y_axis = self.get_y_axis(category)
            all_x.extend(x_axis)
            all_y.extend(y_axis)
            subplot.scatter(x_axis,
                            y_axis,
                            c=self.get_color_axis(category),
                            alpha=self.scatter_alpha,
                            label=category,
                            s=60,)

        subplot.set_xlim(xmin=0)
        subplot.set_ylim(ymin=0)
        fig.text(.45, .96, self.title, fontsize=self.title_size)
        subplot.tick_params(axis='both', which='major', labelsize=self.tick_size)
        subplot.tick_params(axis='both', which='minor', labelsize=self.tick_size)
        subplot.set_xlabel(self.scatter_x_label, size=self.label_size)
        subplot.set_ylabel(self.scatter_y_label, size=self.label_size)

        # regression line
        all_x = numpy.array(all_x)
        all_y = numpy.array(all_y)
        slope, intercept, r_value, p_value, std_err = stats.linregress(all_x, all_y)

        reg_label = "Fit: p=%f" % p_value
        subplot.plot(all_x, all_x * slope + intercept, color='black', label=reg_label)
        subplot.legend(loc=2, prop={'size': self.tick_size})
        return fig

    def get_x_axis(self, category):
        x_axis = list()
        for mky in plotting.RHESUS_DRINKERS_DISTINCT[category]:
            becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
            x_axis.extend(becs.values_list('bec_daily_gkg_etoh', flat=True))
        return numpy.array(x_axis)

    def get_y_axis(self, category):
        y_axis = list()
        for mky in plotting.RHESUS_DRINKERS_DISTINCT[category]:
            becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
            y_axis.extend(becs.values_list('bec_mg_pct', flat=True))
        return y_axis

    def get_color_axis(self, category):
        color_axis = list()
        for mky in plotting.RHESUS_DRINKERS_DISTINCT[category]:
            datapoint_count = MonkeyBEC.objects.OA().filter(monkey=mky).count()
            color = [plotting.RHESUS_COLORS[category] for _empty in range(datapoint_count)]
            color_axis.extend(color)
        return color_axis


class AveragedMATRRBECEthanolIntakeScatterPlot(MATRRBECEthanolIntakeScatterPlot):
    title = "Supplement 6"
    scatter_x_label = 'Average Daily Ethanol Intake'
    scatter_y_label = 'Average BEC'

    def get_x_axis(self, category):
        x_axis = list()
        for mky in plotting.RHESUS_DRINKERS_DISTINCT[category]:
            becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
            x_axis.append(becs.aggregate(Avg('bec_daily_gkg_etoh'))['bec_daily_gkg_etoh__avg'])
        return numpy.array(x_axis)

    def get_y_axis(self, category):
        y_axis = list()
        for mky in plotting.RHESUS_DRINKERS_DISTINCT[category]:
            becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
            y_axis.append(becs.aggregate(Avg('bec_mg_pct'))['bec_mg_pct__avg'])
        return y_axis

    def get_color_axis(self, category):
        color_axis = list()
        for mky in plotting.RHESUS_DRINKERS_DISTINCT[category]:
            color_axis.append(plotting.RHESUS_COLORS[category])
        return color_axis


class PaneledMATRRBECEthanolIntakeScatterPlot(MATRRBECEthanolIntakeScatterPlot):
    def draw_figure(self):
        fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
        main_gs = gridspec.GridSpec(2, 2)
        main_gs.update(left=0.07, right=0.93, top=.95, bottom=.08, hspace=.01, wspace=.008)
        subplot = None
        for index, category in enumerate(plotting.DRINKING_CATEGORIES):
            if index == 0:
                xindex = 0
                yindex = 0
            elif index == 1:
                xindex = 0
                yindex = 1
            elif index == 2:
                xindex = 1
                yindex = 0
            else:
                xindex = 1
                yindex = 1
            subplot = fig.add_subplot(main_gs[xindex,yindex], sharex=subplot, sharey=subplot)
            x_axis = self.get_x_axis(category)
            y_axis = self.get_y_axis(category)
            subplot.scatter(x_axis,
                            y_axis,
                            c=self.get_color_axis(category),
                            alpha=self.scatter_alpha,
                            label=category,
                            s=60,)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis, y_axis)
            reg_label = "Fit: p=%f" % p_value
            subplot.plot(x_axis, x_axis * slope + intercept, color='black', label=reg_label)
            subplot.legend(loc=2, prop={'size': self.tick_size})
            subplot.set_xlim(xmin=0, xmax=7)
            subplot.set_ylim(ymin=0)
            if not xindex:
                subplot.get_xaxis().set_visible(False)
                subplot.set_xlabel('')
            else:
                subplot.set_xlabel(self.scatter_x_label, size=self.label_size)
            if yindex:
                subplot.get_yaxis().set_visible(False)
                subplot.set_ylabel('')
            else:
                subplot.set_ylabel(self.scatter_y_label, size=self.label_size)
            subplot.xaxis.set_major_locator(MaxNLocator(6, prune='lower'))
            subplot.yaxis.set_major_locator(MaxNLocator(6, prune='lower'))
            subplot.tick_params(axis='both', which='major', labelsize=self.tick_size)
            subplot.tick_params(axis='both', which='minor', labelsize=self.tick_size)

        fig.text(.45, .96, self.title, fontsize=self.title_size)

        return fig


def create_manuscript_graphs(output_path='', graphs='1,2,3,4,5,s2a,s2b,s3a,s3b,s4,s5,s6', png=True, fig_size=(25, 15), dpi=800):
    figures = list()
    names = list()
    all_categories = DRINKING_CATEGORIES

    graphs = graphs.split(',')
    if '1' in graphs:
        figures.append(rhesus_etoh_gkg_forced_monkeybargraphhistogram(fig_size=fig_size))
        names.append('Figure1')
    if '2' in graphs:
        figures.append(rhesus_etoh_gkg_stackedbargraph(fig_size=fig_size))
        names.append('Figure2')
    if '3' in graphs:
        figures.append(monkey_bec_consumption(monkey=10062))
        names.append('VHD')

        figures.append(monkey_bec_consumption(monkey=10060))
        names.append('HD')

        figures.append(monkey_bec_consumption(monkey=10056))
        names.append('BD')

        figures.append(monkey_bec_consumption(monkey=10052))
        names.append('LD')
        print 'Figure 3 MUST BE RENDERED SPECIAL!!!!'
        print 'Look thru the code of this script.  Render them individually, save them manually, then stich them together in photoshop, adding labels.'
    if '4' in graphs:
        figures.append(rhesus_category_parallel_classification_stability_popcount(all_categories, gadgets.gather_three_month_monkey_average_by_fieldname, "Average Daily EtOH Intake by Category (g/kg)"))
        names.append('Figure4')
    if '5' in graphs:
        figures.append(rhesus_oa_pelletvolume_perday_perkg(fig_size=fig_size))
        names.append('Figure5')
    if 's2a' in graphs:
        fig = rhesus_N_gkg_days(.5)
        figures.append(fig)
        names.append('S2a')
    if 's2b' in graphs:
        fig = rhesus_N_gkg_days(2.5)
        figures.append(fig)
        names.append('S2b')
    if 's3a' in graphs:
        fig = rhesus_cohort_bargraph_gkg_per_quartile()
        figures.append(fig)
        names.append('S3a')
    if 's3b' in graphs:
        fig = rhesus_cohort_bargraph_gkg_per_year()
        figures.append(fig)
        names.append('S3b')
    if 's4' in graphs:
        fig = rhesus_category_parallel_classification_stability_popcount_3moAssignment(all_categories, gadgets.gather_three_month_monkey_average_by_fieldname, "Average Daily EtOH Intake by Category (g/kg)")
        figures.append(fig)
        names.append('S4')
    if 's5' in graphs:
        fig = rhesus_category_bec_boxplot()
        figures.append(fig)
        names.append('S5')
    if 's6' in graphs:
        figures.append(rhesus_etoh_bec_scatter(monkey_two=10098, monkey_one=10092, fig_size=fig_size))
        names.append('S6')
    if 's7' in graphs:
        bplot = PaneledMATRRBECEthanolIntakeScatterPlot()
        fig = bplot.draw_figure()
        figures.append(fig)
        names.append('S7')

    if png:
        for FigName in zip(figures, names):
            fig, name = FigName
            if png:
                filename = output_path + '%s.png' % name
                fig.savefig(filename, format='png',dpi=dpi)


