__author__ = 'farro'
import numpy
import dateutil
import gc
import logging
import traceback
import sys
from datetime import datetime, date
from matplotlib import colors
from numpy.ma import concatenate
from scipy.interpolate import spline

import matplotlib
from matplotlib.cm import get_cmap
from matplotlib.ticker import MaxNLocator

from matrr.models import Monkey, MonkeyToDrinkingExperiment, MonkeyBEC, MonkeyImage, Cohort, CohortImage, ExperimentEvent, NecropsySummary, Q
#from matrr.plotting import cohort_plots, monkey_plots

def validate_dates(from_date=False, to_date=False):
    if from_date and not isinstance(from_date, (datetime, date)):
        try:
            #maybe its a str(datetime)
            from_date = dateutil.parser.parse(from_date)
        except:
            #otherwise give up
            logging.warning("Invalid parameter, from_date")
            logging.warning('>>> traceback <<<')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('-- ' + line for line in lines)
            logging.warning(log_output)
            logging.warning('>>> end of traceback <<<')
            from_date = None
    if to_date and not isinstance(to_date, (datetime, date)):
        try:
            #maybe its a str(datetime)
            to_date = dateutil.parser.parse(to_date)
        except:
            #otherwise give up
            logging.warning("Invalid parameter, to_date")
            logging.warning('>>> traceback <<<')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('-- ' + line for line in lines)
            logging.warning(log_output)
            logging.warning('>>> end of traceback <<<')
            to_date = None
    return from_date, to_date

def cmap_discretize(cmap, N):
    """Return a discrete colormap from the continuous colormap cmap.

        cmap: colormap instance, eg. cm.jet.
        N: number of colors.

    Example
        x = resize(arange(100), (5,100))
        djet = cmap_discretize(cm.jet, 5)
        imshow(x, cmap=djet)
    """

    if type(cmap) == str:
        name = cmap
        cmap = get_cmap(cmap)
        cmap.name = name
    colors_i = concatenate((numpy.linspace(0, 1., N), (0.,0.,0.,0.)))
    colors_rgba = cmap(colors_i)
    indices = numpy.linspace(0, 1., N+1)
    cdict = {}
    for ki,key in enumerate(('red','green','blue')):
        cdict[key] = [ (indices[i], colors_rgba[i-1,ki], colors_rgba[i,ki]) for i in xrange(N+1) ]
    # Return colormap object.
    return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)

def create_convex_hull_polygon(subplot, xvalues, yvalues, color):
    """
    This method will draw several lines around the provided x-y values, onto 'subplot', colored by 'color'.
    """
    from matrr.utils.gadgets import convex_hull
    from matplotlib.path import Path

    try:
        hull = convex_hull(numpy.array(zip(xvalues, yvalues)).transpose())
        # hull == numpy array of exterior points
    except AssertionError: # usually means < 5 datapoints
        return
    path = Path(hull) # I think Path() just sorts the points such that it goes around the perimeter

    # path.verticies is the a 2d array of points.  But this array doesn't complete the perimeter.
    # so you need to append the first point to the end of the array to close the polygon
    x = list(path.vertices[:,0])
    y = list(path.vertices[:,1])
    x.append(x[0])
    y.append(y[0])
    line = subplot.plot(x, y, c=color, linewidth=3, alpha=.3)
    return line


def _lifetime_cumsum_etoh(eevs, subplot, color_monkey=True):
    """
    This is used by monkey_etoh_lifetime_cumsum.  It will extract the ethanol events from the eevs arg
    and create a cumulative summation plot of the ethanol intake.
    """
    colors = ['navy', 'goldenrod']
    volumes = numpy.array(eevs.values_list('eev_etoh_volume', flat=True))
    yaxis = numpy.cumsum(volumes)
    xaxis = numpy.array(eevs.values_list('eev_occurred', flat=True))
    color = colors[1] if color_monkey else colors[0]
    subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=color)
    return subplot

def _days_cumsum_etoh(eevs, subplot):
    """
    This fn is used by cohort_etoh_induction_cumsum and monky_etoh_induction_cumsum.  It will extract the ethanol event data
    from the eevs argand plot the cumulative summation line for each day's intake, resetting the line to 0 each new day.
    """
    colors = ['navy', 'goldenrod']
    dates = eevs.dates('eev_occurred', 'day')
    offset = 0
    for index, date in enumerate(dates):
        date_eevs = eevs.filter(eev_occurred__year=date.year, eev_occurred__month=date.month, eev_occurred__day=date.day)
        times = numpy.array(date_eevs.values_list('eev_session_time', flat=True))
        volumes = numpy.array(date_eevs.values_list('eev_etoh_volume', flat=True))
        pace = 0
        x_index = 0
        xaxis = list()
        yaxis = list()
        for t, v in zip(times, volumes):
            if not pace:
                pace = t
                yaxis.append(v)
                xaxis.append(x_index)
                x_index += 1
                continue
            _v = yaxis[len(yaxis)-1]
            if t != pace+1:
                for i in range(t-pace-1):
                    yaxis.append(_v)
                    xaxis.append(x_index)
                    x_index += 1
            yaxis.append(_v+v)
            xaxis.append(x_index)
            x_index += 1
            pace = t

        xaxis = numpy.array(xaxis) + offset
        offset = xaxis.max()
        subplot.plot(xaxis, yaxis, alpha=1, linewidth=0, color=colors[index%2])
        subplot.fill_between(xaxis, 0, yaxis, color=colors[index%2])

    if len(eevs.order_by().values_list('eev_dose', flat=True).distinct()) > 1:
        stage_2_eevs = eevs.filter(eev_dose=1)
        stage_2_xaxis = numpy.array(stage_2_eevs.values_list('eev_occurred', flat=True))
        subplot.axvspan(stage_2_xaxis.min(), stage_2_xaxis.max(), color='black', alpha=.2, zorder=-100)

# histograms
def _general_histogram(monkey, monkey_values, cohort_values, high_values, low_values, label, axis, hide_xticks, show_legend):
    """
    A generalized histogram function, used to add context to complex graphs by plotting the histogram distribution of
    values being displayed in the graph.  This will draw 4 lines onto the axis arg, lines for monkey, cohort, high_drinking_monkey,
    and low_drinking_monkey. Each line shows the distribution of values for that subject, providing quick comparison of
    the subject monkey to its peers and high/low drinking monkeys.
    """
    data_arrays = [monkey_values, cohort_values, high_values, low_values]
    maxes = list()
    for d in data_arrays:
        maxes.append(d.mean()+ 2*d.std()) # "max" == 3 standard deviations from the mean
    linspace = numpy.linspace(0, max(maxes), 15) # defines number of bins in histogram

    # Monkey histogram spline
    n, bins, patches = axis.hist(monkey_values, bins=linspace, normed=True, alpha=0, color='gold')
    bincenters = 0.5*(bins[1:]+bins[:-1])
    newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
    newy = spline(bincenters, n, newx) # smooth out the y axis
    axis.plot(newx, newy, color='gold', linewidth=5, label="%d" % monkey.pk) # smoothed line

    # Cohort histogram spline
    n, bins, patches = axis.hist(cohort_values, bins=linspace, normed=True, alpha=0, color='purple')
    bincenters = 0.5*(bins[1:]+bins[:-1])
    newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
    newy = spline(bincenters, n, newx) # smooth out the y axis
    axis.plot(newx, newy, color='purple', linewidth=2, label=str(monkey.cohort)) # smoothed line

    # high-drinker histogram spline
    n, bins, patches = axis.hist(high_values, bins=linspace, normed=True, alpha=0, color='red')
    bincenters = 0.5*(bins[1:]+bins[:-1])
    newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
    newy = spline(bincenters, n, newx) # smooth out the y axis
    axis.plot(newx, newy, color='red', ls='--', linewidth=2, label="HD") # smoothed line

    # low-drinker histogram spline
    n, bins, patches = axis.hist(low_values, bins=linspace, normed=True, alpha=0, color='blue')
    bincenters = 0.5*(bins[1:]+bins[:-1])
    newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
    newy = spline(bincenters, n, newx) # smooth out the y axis
    axis.plot(newx, newy, color='blue', ls='--', linewidth=2, label="LD") # smoothed line

    if show_legend:
        axis.legend(loc="upper left", frameon=False)
    axis.set_title(label)
    axis.set_yticks([])
    if hide_xticks:
        axis.set_xticks([])
    else:
        axis.xaxis.set_major_locator(MaxNLocator(4))
    return axis

def _histogram_legend(monkey, axis):
    """
    Creates a legend subplot for the histograms that are created by _general_histogram().

    Example of use inside a plotting method:
    # create the grid spec for the histograms (and legend)
    hist_gs = gridspec.GridSpec(4, 1)
    hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)

    # create the first subplot
    bec_bub_hist = fig.add_subplot(hist_gs[0, :])
    # and add the this legend to that subplot
    bec_bub_hist = _histogram_legend(monkey, bec_bub_hist)
    # add a new subplot
    bec_bub_hist = fig.add_subplot(hist_gs[1, :])
    # and create the histogram in that subplot
    bec_bub_hist = _bec_histogram(monkey, 'bec_mg_pct', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
    # repeat
    bec_bub_hist = fig.add_subplot(hist_gs[2, :])
    bec_bub_hist = _bec_histogram(monkey, 'bec_pct_intake', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
    bec_bub_hist = fig.add_subplot(hist_gs[3, :])
    bec_bub_hist = _bec_histogram(monkey, 'bec_gkg_etoh', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
    """
    from matplotlib.lines import Line2D
    lines = list()
    labels = list()
    l = Line2D((0,1),(0,0), color='gold', linewidth=5)
    axis.add_line(l)
    lines.append(l)
    labels.append(monkey)

    l = Line2D((0,1),(0,0), color='purple', linewidth=2)
    axis.add_line(l)
    lines.append(l)
    labels.append(str(monkey.cohort))

    l = Line2D((0,1),(0,0), color='red', linewidth=2, ls='--')
    axis.add_line(l)
    lines.append(l)
    labels.append("High-drinker")

    l = Line2D((0,1),(0,0), color='blue', linewidth=2, ls='--')
    axis.add_line(l)
    lines.append(l)
    labels.append("Low-drinker")

    axis.legend(lines, labels, loc=10, frameon=False, prop={'size':12})
    axis.set_yticks([])
    axis.set_xticks([])

def _bec_histogram(monkey, column_name, axis, from_date=None, to_date=None, sample_before=None, sample_after=None, dex_type='', verbose_name='', hide_xticks=False, show_legend=False):
    """
    This will collect data about the distribution of BEC values in the [column_name] MonkeyBEC column for the monkey, its
    cohort and the high/low drinking benchmark monkeys.

    Once collected, this data is passed to _general_histogram() to plot the histograms onto [axis].
    """
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return
    high_monkey = Monkey.objects.get(mky_high_drinker=True, mky_species=monkey.mky_species)
    low_monkey = Monkey.objects.get(mky_low_drinker=True, mky_species=monkey.mky_species)

    cohort_bec = MonkeyBEC.objects.filter(monkey__cohort=monkey.cohort)
    high_bec = MonkeyBEC.objects.filter(monkey=high_monkey)
    low_bec = MonkeyBEC.objects.filter(monkey=low_monkey)
    from_date, to_date = validate_dates(from_date, to_date)
    q_filter = Q()
    if from_date:
        q_filter = q_filter & Q(mtd__drinking_experiment__dex_date__gte=from_date)
    if to_date:
        q_filter = q_filter & Q(mtd__drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        q_filter = q_filter & Q(mtd__drinking_experiment__dex_type=dex_type)
    if sample_before:
        q_filter = q_filter & Q(bec_sample__lte=sample_before)
    if sample_after:
        q_filter = q_filter & Q(bec_sample__gte=sample_after)
    q_filter = q_filter & ~Q(**{column_name: None})

    cohort_bec = cohort_bec.filter(q_filter)
    monkey_bec = cohort_bec.filter(monkey=monkey)
    cohort_bec = cohort_bec.exclude(monkey=monkey)
    high_bec = high_bec.filter(q_filter)
    low_bec = low_bec.filter(q_filter)

    label = verbose_name
    if not label:
        label = monkey_bec[0]._meta.get_field(column_name).verbose_name

    monkey_values = numpy.array(monkey_bec.values_list(column_name, flat=True), dtype=float)
    cohort_values = numpy.array(cohort_bec.values_list(column_name, flat=True), dtype=float)
    high_values = numpy.array(high_bec.values_list(column_name, flat=True), dtype=float)
    low_values = numpy.array(low_bec.values_list(column_name, flat=True), dtype=float)
    return _general_histogram(monkey, monkey_values, cohort_values, high_values, low_values, label, axis, hide_xticks, show_legend)

def _mtd_histogram(monkey, column_name, axis, from_date=None, to_date=None, dex_type='', verbose_name='', hide_xticks=False, show_legend=False):
    """
    This will collect data about the distribution of MTD values in the [column_name] MonkeyToDrinkingExperiment column
    for the monkey, its cohort and the high/low drinking benchmark monkeys.

    Once collected, this data is passed to _general_histogram() to plot the histograms onto [axis].
    """
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print "That's not a valid monkey."
                return
    high_monkey = Monkey.objects.get(mky_high_drinker=True)
    low_monkey = Monkey.objects.get(mky_low_drinker=True)

    cohort_dex = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=monkey.cohort)
    high_dex = MonkeyToDrinkingExperiment.objects.filter(monkey=high_monkey)
    low_dex = MonkeyToDrinkingExperiment.objects.filter(monkey=low_monkey)
    from_date, to_date = validate_dates(from_date, to_date)
    q_filter = Q()
    if from_date:
        q_filter = q_filter & Q(drinking_experiment__dex_date__gte=from_date)
    if to_date:
        q_filter = q_filter & Q(drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        q_filter = q_filter & Q(drinking_experiment__dex_type=dex_type)
    q_filter = q_filter & ~Q(**{column_name: None})

    cohort_dex = cohort_dex.filter(q_filter)
    monkey_dex = cohort_dex.filter(monkey=monkey)
    cohort_dex = cohort_dex.exclude(monkey=monkey)
    high_dex = high_dex.filter(q_filter)
    low_dex = low_dex.filter(q_filter)

    label = verbose_name
    if not label:
        label = monkey_dex[0]._meta.get_field(column_name).verbose_name

    monkey_values = numpy.array(monkey_dex.values_list(column_name, flat=True), dtype=float)
    cohort_values = numpy.array(cohort_dex.values_list(column_name, flat=True), dtype=float)
    high_values = numpy.array(high_dex.values_list(column_name, flat=True), dtype=float)
    low_values = numpy.array(low_dex.values_list(column_name, flat=True), dtype=float)
    return _general_histogram(monkey, monkey_values, cohort_values, high_values, low_values, label, axis, hide_xticks, show_legend)




def fetch_plot_choices(subject, user, cohort, tool):
    from matrr.plotting.cohort_plots import COHORT_ETOH_TOOLS_PLOTS, COHORT_BEC_TOOLS_PLOTS
    from matrr.plotting.monkey_plots import MONKEY_ETOH_TOOLS_PLOTS, MONKEY_BEC_TOOLS_PLOTS
    plot_choices = []
    if subject == 'monkey':
        if user.has_perm('matrr.view_etoh_data'):
            if tool == 'etoh' and cohort.monkey_set.exclude(mtd_set=None).count():
                plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in MONKEY_ETOH_TOOLS_PLOTS.items()])
            if tool == 'bec' and cohort.monkey_set.exclude(bec_records=None).count():
                plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in MONKEY_BEC_TOOLS_PLOTS.items()])

    elif subject == 'cohort':
        if user.has_perm('matrr.view_etoh_data'):
            if tool == 'etoh' and cohort.monkey_set.exclude(mtd_set=None).count():
                plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in COHORT_ETOH_TOOLS_PLOTS.items()])
            if tool == 'bec' and cohort.monkey_set.exclude(bec_records=None).count():
                plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in COHORT_BEC_TOOLS_PLOTS.items()])
    else:
        raise Exception("'subject' parameter must be 'monkey' or 'cohort'")
    return plot_choices

def create_necropsy_plots(cohorts=True, monkeys=True):
    if monkeys:
        plots = [
            'monkey_necropsy_etoh_4pct',
            'monkey_necropsy_sum_g_per_kg',
            'monkey_necropsy_avg_22hr_g_per_kg',
            ]

        from matrr.models import MonkeyImage, Monkey
        from matrr.plotting import monkey_plots
        for monkey in NecropsySummary.objects.all().values_list('monkey', flat=True).distinct():
            monkey = Monkey.objects.get(pk=monkey)
            for graph in plots:
                MonkeyImage.objects.get_or_create(monkey=monkey, method=graph, title=monkey_plots.MONKEY_PLOTS[graph][1], canonical=True)
                gc.collect()

    if cohorts:
        plots = [
            'cohort_necropsy_etoh_4pct',
            'cohort_necropsy_sum_g_per_kg',
            'cohort_necropsy_avg_22hr_g_per_kg',
            ]

        from matrr.models import CohortImage, Cohort
        from matrr.plotting import cohort_plots
        for cohort in NecropsySummary.objects.all().values_list('monkey__cohort', flat=True).distinct():
            cohort = Cohort.objects.get(pk=cohort)
            print cohort
            for graph in plots:
                gc.collect()
                CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=cohort_plots.COHORT_PLOTS[graph][1], canonical=True)

def create_bec_summary_plots(cohorts=True, monkeys=True):
    from matrr.models import MonkeyImage, CohortImage, Cohort, MonkeyBEC
    from matrr.plotting import monkey_plots, cohort_plots

    bec_cohorts = set(MonkeyBEC.objects.OA().values_list('monkey__cohort', flat=True))
    approved_cohorts = set([2, 3, 5, 6, 9, 10])  # Cyno 1 & 2, Rhesus 4, 5, 7a, 7b
    actionable_cohorts = bec_cohorts & approved_cohorts

    coh_plots = ['cohort_summary_avg_bec_mgpct', ]
    mky_plots = ['monkey_summary_avg_bec_mgpct',]

    for _cohort in actionable_cohorts:
        cohort = Cohort.objects.get(pk=_cohort)
        if cohorts:
            print cohort
            for graph in coh_plots:
                gc.collect()
                CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=cohort_plots.COHORT_PLOTS[graph][1], canonical=True)
        if monkeys:
            for monkey in cohort.monkey_set.all():
                print monkey
                for graph in mky_plots:
                    MonkeyImage.objects.get_or_create(monkey=monkey, method=graph, title=monkey_plots.MONKEY_PLOTS[graph][1], canonical=True)
                    gc.collect()


def create_mtd_histograms():
    names = [
     'mtd_etoh_intake',
     'mtd_pct_etoh',
     'mtd_etoh_g_kg',
     'mtd_etoh_bout',
     'mtd_etoh_mean_drink_vol',
     'mtd_etoh_mean_bout_vol',
     'mtd_vol_1st_bout',
     'mtd_pct_etoh_in_1st_bout',
     'mtd_latency_1st_drink',
     'mtd_max_bout_length',
     'mtd_max_bout_vol',
     'mtd_pct_max_bout_vol_total_etoh',
    ]
    mtd = MonkeyToDrinkingExperiment
    for monkey in mtd.objects.all().values_list('monkey', flat=True).distinct():
        m = Monkey.objects.get(pk=monkey)
        for field in names:
            params = str({'column_name': field })
            title = mtd._meta.get_field(field).verbose_name
            MonkeyImage.objects.get_or_create(method='monkey_mtd_histogram_general', monkey=m, parameters=params, title=title, canonical=True)

def create_bec_histograms():
    names = [
        'bec_mg_pct',
        'bec_pct_intake'
    ]

    bec = MonkeyBEC
    for monkey in bec.objects.all().values_list('monkey', flat=True).distinct():
        m = Monkey.objects.get(pk=monkey)
        for field in names:
            params = str({'column_name': field })
            title = bec._meta.get_field(field).verbose_name
            MonkeyImage.objects.get_or_create(method='monkey_bec_histogram_general', monkey=m, parameters=params, title=title, canonical=True)

def create_quadbar_graphs():
    from matrr.plotting.cohort_plots import COHORT_PLOTS
    plot_method = 'cohort_etoh_gkg_quadbar'
    for cohort in MonkeyToDrinkingExperiment.objects.all().values_list('monkey__cohort', flat=True).distinct():
        cohort = Cohort.objects.get(pk=cohort)
        print "Creating %s graphs" % str(cohort)
        CohortImage.objects.get_or_create(cohort=cohort, method=plot_method, title=COHORT_PLOTS[plot_method][1], canonical=True)
        gc.collect()


def create_daily_cumsum_graphs():
    from matrr.plotting.cohort_plots import COHORT_PLOTS
    from matrr.plotting.monkey_plots import MONKEY_PLOTS
    cohorts = ExperimentEvent.objects.all().values_list('monkey__cohort', flat=True).distinct()
    for cohort in cohorts:
        cohort = Cohort.objects.get(pk=cohort)
        print "Creating %s graphs" % str(cohort)
        gc.collect()
        for stage in range(0, 4):
            plot_method = 'cohort_etoh_induction_cumsum'
            params = str({'stage': stage})
            CohortImage.objects.get_or_create(cohort=cohort, method=plot_method, title=COHORT_PLOTS[plot_method][1], parameters=params, canonical=True)
        for monkey in Monkey.objects.Drinkers().filter(cohort=cohort):
            plot_method = 'monkey_etoh_induction_cumsum'
            MonkeyImage.objects.get_or_create(monkey=monkey, method=plot_method, title=MONKEY_PLOTS[plot_method][1], canonical=True)

def create_bec_tools_canonicals(cohort, create_monkey_plots=True):
    from matrr.plotting.cohort_plots import COHORT_PLOTS
    from matrr.plotting.monkey_plots import MONKEY_PLOTS
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print "That's not a valid cohort."
            return

    cohort_plot_methods = ['cohort_bec_firstbout_monkeycluster',]
    dex_types = ["", "Induction", "Open Access"]

    print "Creating bec cohort plots for %s." % str(cohort)
    for dex_type in dex_types:
        params = str({'dex_type': dex_type})
        for method in cohort_plot_methods:
            CohortImage.objects.get_or_create(cohort=cohort, method=method, parameters=params, title=COHORT_PLOTS[method][1], canonical=True)

    if create_monkey_plots:
        monkey_plot_methods = ['monkey_bec_bubble', 'monkey_bec_consumption', 'monkey_bec_monthly_centroids', ]
        dex_types = ["", "Induction", "Open Access"]

        print "Creating bec monkey plots."
        for monkey in cohort.monkey_set.all():
            for dex_type in dex_types:
                params = str({'dex_type': dex_type})
                for method in monkey_plot_methods:
                    MonkeyImage.objects.get_or_create(monkey=monkey, method=method, parameters=params, title=MONKEY_PLOTS[method][1], canonical=True)
                    gc.collect()

def create_mtd_tools_canonicals(cohort, create_monkey_plots=True):
    from matrr.plotting.cohort_plots import COHORT_PLOTS
    from matrr.plotting.monkey_plots import MONKEY_PLOTS
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print "That's not a valid cohort."
            return

    plots = ['cohort_etoh_bihourly_treemap',]
    dex_types = ["", "Induction", "Open Access"]

    print "Creating cohort mtd plots for %s." % str(cohort)
    for dex_type in dex_types:
        params = str({'dex_type': dex_type})
        for method in plots:
            CohortImage.objects.get_or_create(cohort=cohort, method=method, parameters=params, title=COHORT_PLOTS[method][1], canonical=True)

    if create_monkey_plots:
        plots = ['monkey_etoh_bouts_vol',
                 'monkey_etoh_first_max_bout',
                 'monkey_etoh_bouts_drinks',
                 ]
        dex_types = ["", "Induction", "Open Access"]

        print "Creating mtd monkey plots."
        for monkey in cohort.monkey_set.all():
            for dex_type in dex_types:
                params = str({'dex_type': dex_type})
                for method in plots:
                    MonkeyImage.objects.get_or_create(monkey=monkey, method=method, parameters=params, title=MONKEY_PLOTS[method][1], canonical=True)
                    gc.collect()
