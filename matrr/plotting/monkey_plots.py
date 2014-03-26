__author__ = 'farro'
from matplotlib import pyplot, cm, gridspec, colors
import numpy
import gc
from numpy import polyfit, polyval
from scipy.cluster import vq

from django.db.models.aggregates import Max, Avg
from matplotlib.cm import get_cmap
from matplotlib.ticker import NullLocator, MaxNLocator
import matplotlib

from matrr.models import *
from matrr.plotting import specific_callables, plot_tools
from matrr.plotting import *

def monkey_necropsy_avg_22hr_g_per_kg(monkey):
    try:
        monkey.necropsy_summary
    except NecropsySummary.DoesNotExist:
        return False, False
    else:
        graph_title = 'Average Ethanol Intake for Monkey %s during 22 Hour Free Access Phase' % str(monkey.pk)
        x_label = "Ethanol Intake (in g/kg)"
        legend_labels = ('12 Month Average', '6 Month Average', '%s 12 Month Average' % str(monkey.pk), '%s 6 Month Average' % str(monkey.pk))
        return _monkey_summary_general(specific_callables.necropsy_summary_avg_22hr_g_per_kg, x_label, graph_title, legend_labels, monkey)


def monkey_necropsy_etoh_4pct(monkey):
    try:
        monkey.necropsy_summary
    except NecropsySummary.DoesNotExist:
        return False, False
    else:
        graph_title = 'Total Ethanol Intake for Monkey %s' % str(monkey.pk)
        x_label = "Ethanol Intake (in 4% ml)"
        legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)', '%s Total Intake (Lifetime)' % str(monkey.pk), '%s Total Intake (22hr)' % str(monkey.pk))
        return _monkey_summary_general(specific_callables.necropsy_summary_etoh_4pct, x_label, graph_title, legend_labels, monkey)


def monkey_necropsy_sum_g_per_kg(monkey):
    try:
        monkey.necropsy_summary
    except NecropsySummary.DoesNotExist:
        return False, False
    else:
        graph_title = 'Total Ethanol Intake for Monkey %s' % str(monkey.pk)
        x_label = "Ethanol Intake (in g/kg)"
        legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)', '%s Total Intake (Lifetime)' % str(monkey.pk), '%s Total Intake (22hr)' % str(monkey.pk))
        return _monkey_summary_general(specific_callables.necropsy_summary_sum_g_per_kg, x_label, graph_title, legend_labels, monkey)


def monkey_summary_avg_bec_mgpct(monkey):
    """
    This method will create a monkey graph (horizontal bar graph) showing each monkey's average open access bec values, highlighting monkey's values
    """
    if MonkeyBEC.objects.filter(monkey=monkey).count():
        graph_title = 'Average Blood Ethanol Concentration for Monkey %s (22hr open access)' % str(monkey.pk)
        x_label = "Average BEC (mg percent)"
        legend_labels = ('12 Month Average', '6 Month Average', '%s 12 Month Average' % str(monkey.pk), '%s 6 Month Average' % str(monkey.pk))
        return _monkey_summary_general(specific_callables.summary_avg_bec_mgpct, x_label, graph_title, legend_labels, monkey)
    else:
        return False, False



def _monkey_summary_general(specific_callable, x_label, graph_title, legend_labels, monkey, cohort=None):
    from matrr.models import Monkey, Cohort
    ##  Verify argument is actually a monkey
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False
    if cohort:
        if not isinstance(cohort, Cohort):
            try:
                cohort = Cohort.objects.get(pk=cohort)
            except Cohort.DoesNotExist:
                print("That's not a valid cohort.  Using monkey's cohort")
                cohort = monkey.cohort
    else:
        cohort = monkey.cohort

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = fig.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
    ax1.set_axisbelow(True)
    #	ax1.set_title('Average Ethanol Intake for Monkey %s during 22 Hour Free Access Phase' % str(monkey.pk))
    ax1.set_title(graph_title)
    ax1.set_ylabel("Monkey")
    ax1.set_xlabel(x_label)

    cohort_colors = ['navy', 'slateblue']
    monkey_colors = ['goldenrod', 'gold']

    if not monkey.necropsy_summary:
        print("Monkey doesn't have any necropsy summary rows")
        return False, False

    coh_data_1, coh_data_2, cohort_labels = specific_callable(cohort.monkey_set.exclude(pk=monkey.pk))
    mky_data_1, mky_data_2, monkey_label = specific_callable(cohort.monkey_set.filter(pk=monkey.pk))
    if not mky_data_1[0] or not mky_data_2[0]: # don't draw plots for control monkeys
        return False, False

    idx = numpy.arange(len(coh_data_1))
    width = 0.4

    cohort_bar1 = ax1.barh(idx, coh_data_1, width, color=cohort_colors[0])
    cohort_bar2 = ax1.barh(idx + width, coh_data_2, width, color=cohort_colors[1])
    monkey_bar1 = ax1.barh(max(idx) + 1, mky_data_1, width, color=monkey_colors[0])
    monkey_bar2 = ax1.barh(max(idx) + 1 + width, mky_data_2, width, color=monkey_colors[1])

    def autolabel(rects, text_color=None):
        import locale

        locale.setlocale(locale.LC_ALL, '')
        for rect in rects:
            width = rect.get_width()
            xloc = width * .98
            clr = text_color if text_color else "black"
            align = 'right'
            yloc = rect.get_y() + rect.get_height() / 2.0

            text_width = locale.format("%.1f", width, grouping=True)
            if width > 0:
                ax1.text(xloc, yloc, text_width, horizontalalignment=align, verticalalignment='center', color=clr, weight='bold')

    autolabel(cohort_bar1, 'white')
    autolabel(cohort_bar2, 'white')
    autolabel(monkey_bar1, 'black')
    autolabel(monkey_bar2, 'black')

    ax1.legend((cohort_bar2[0], cohort_bar1[0], monkey_bar2, monkey_bar1), legend_labels, loc=4)

    idx = numpy.arange(len(coh_data_1) + 1)
    cohort_labels.append(str(monkey.pk))
    ax1.set_yticks(idx + width)
    ax1.set_yticklabels(cohort_labels)
    return fig, 'map'


def _monkey_tools_single_line(x_values, y_values, title, x_label, y_label, scale_x=(), scale_y=()):
    """
    x_values = list of datetime.datetime() objects
    y_values = list of y values for each x_value date.
    title = title of the plot
    x_label = x axis label
    y_label = y axis label

    This is used by monkey_protein_value() and monkey_hormone_value() tools plot.  These methods collect the data passed
    to this method.  This method plots that data.
    """
    value_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = value_figure.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
    ax1.set_axisbelow(True)

    ax1.set_title(title)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)

    if scale_x:
        ax1.set_xlim(scale_x)
    if scale_y:
        ax1.set_ylim(scale_y)

    ax1.plot(x_values, y_values, alpha=1, linewidth=4, color='black', marker='o',
             markersize=10) # I removed label="blah" in refactor

    # rotate the xaxis labels
    xticks = [date.date() for date in x_values]
    xtick_labels = [str(date.date()) for date in x_values]
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xtick_labels, rotation=45)

    return value_figure


def _monkey_tools_multiple_lines(list_of_xvalues, list_of_yvalues, list_of_colors, list_of_labels, title, x_label, y_label, scale_x=(), scale_y=()):
    figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = figure.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
    ax1.set_axisbelow(True)

    ax1.set_title(title)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)

    if scale_x:
        ax1.set_xlim(scale_x)
    if scale_y:
        ax1.set_ylim(scale_y)

    dates = list()
    for x_values, y_values, color, label in zip(list_of_xvalues, list_of_yvalues, list_of_colors, list_of_labels):
        dates.extend(x_values)
        ax1.plot(x_values, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=8, markeredgecolor=color,
                 label=label)
    dates = sorted(set(dates))

    oldylims = ax1.get_ylim()
    y_min = min(oldylims[0], -1 * oldylims[1])
    y_max = max(oldylims[1], -1 * oldylims[0])
    ax1.set_ylim(ymin=y_min, ymax=y_max) #  add some spacing, keeps the boxplots from hugging teh axis

    # rotate the xaxis labels
    xticks = [date.date() for date in dates]
    xtick_labels = [str(date.date()) for date in dates]
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xtick_labels, rotation=45)

    # Shink current axis by 20%
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    # Put a legend to the right of the current axis
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    return figure


def monkey_protein_stdev(monkey, proteins, afternoon_reading=None):
    try: # silly hack to enforce ability to forloop
        iter(proteins)
    except TypeError:
        proteins = [proteins]

    protein_abbrevs = []
    for protein in proteins:
        protein_abbrevs.append(protein.pro_abbrev)
    protein_title = ", ".join(protein_abbrevs)
    if len(protein_title) > 30: #  title's too long.  got some work to do
        title_abbrev = protein_title[:40].split(', ') # first, chop it to a good length and split it into a list
        title_abbrev.pop(len(
            title_abbrev) - 1) # now, pop off the last value in the list, since its probably a randomly cut string, like "Washi" instead of "Washington"
        protein_title = ", ".join(title_abbrev) # and join the remainders back together
        protein_title += "..." # and tell people we chopped it
    title = 'Monkey %s: %s' % (str(monkey.pk), protein_title)
    x_label = "Date of sample"
    y_label = "Standard deviation from cohort mean"

    color_map = get_cmap('gist_rainbow')
    x_values = list()
    y_values = list()
    colors = list()
    labels = list()
    for index, protein in enumerate(proteins):
        mpn_dates = MonkeyProtein.objects.filter(monkey=monkey, protein=protein).order_by('mpn_date').values_list('mpn_date',
                                                                                                                  flat=True).distinct()
        y_val = []
        dates = []
        for date in mpn_dates:
            monkey_protein = MonkeyProtein.objects.get(monkey=monkey, protein=protein, mpn_date=date)
            if afternoon_reading is None:
                y_val.append(monkey_protein.mpn_stdev)
                dates.append(date)
            elif afternoon_reading is True and monkey_protein.mpn_date.hour > 12:
                y_val.append(monkey_protein.mpn_stdev)
                dates.append(date)
            elif afternoon_reading is False and monkey_protein.mpn_date.hour <= 12:
                y_val.append(monkey_protein.mpn_stdev)
                dates.append(date)
        x_values.append(dates)
        y_values.append(y_val)
        colors.append(color_map(1. * index / len(proteins)))
        labels.append(str(protein.pro_abbrev))
    if any(x_values):
        fig = _monkey_tools_multiple_lines(x_values, y_values, colors, labels, title, x_label, y_label)
        return fig, False
    return False, False


def monkey_protein_pctdev(monkey, proteins, afternoon_reading=None):
    try: # silly hack to enforce ability to forloop
        iter(proteins)
    except TypeError:
        proteins = [proteins]

    protein_abbrevs = []
    for protein in proteins:
        protein_abbrevs.append(protein.pro_abbrev)
    protein_title = ", ".join(protein_abbrevs)
    if len(protein_title) > 30: #  title's too long.  got some work to do
        title_abbrev = protein_title[:40].split(', ') # first, chop it to a good length and split it into a list
        title_abbrev.pop(len(
            title_abbrev) - 1) # now, pop off the last value in the list, since its probably a randomly cut string, like "Washi" instead of "Washington"
        protein_title = ", ".join(title_abbrev) # and join the remainders back together
        protein_title += "..." # and tell people we chopped it
    title = 'Monkey %s: %s' % (str(monkey.pk), protein_title)
    x_label = "Date of sample"
    y_label = "Percent deviation from cohort mean"

    color_map = get_cmap('gist_rainbow')
    x_values = list()
    y_values = list()
    colors = list()
    labels = list()
    for index, protein in enumerate(proteins):
        mpn_dates = MonkeyProtein.objects.filter(monkey=monkey, protein=protein).order_by('mpn_date').values_list('mpn_date',
                                                                                                                  flat=True).distinct()
        y_val = []
        dates = []
        for date in mpn_dates:
            monkey_protein = MonkeyProtein.objects.get(monkey=monkey, protein=protein, mpn_date=date)
            if afternoon_reading is None:
                y_val.append(monkey_protein.mpn_pctdev)
                dates.append(date)
            elif afternoon_reading is True and monkey_protein.mpn_date.hour > 12:
                y_val.append(monkey_protein.mpn_pctdev)
                dates.append(date)
            elif afternoon_reading is False and monkey_protein.mpn_date.hour <= 12:
                y_val.append(monkey_protein.mpn_pctdev)
                dates.append(date)
        x_values.append(dates)
        y_values.append(y_val)
        colors.append(color_map(1. * index / len(proteins)))
        labels.append(str(protein.pro_abbrev))
    if any(x_values):
        fig = _monkey_tools_multiple_lines(x_values, y_values, colors, labels, title, x_label, y_label)
        return fig, False
    return False, False


def monkey_protein_value(monkey, proteins, afternoon_reading=None):
    # This method CANNOT be called with multiple proteins.  You must create these images individually.
    protein = proteins[0]

    protein_title = protein.pro_name
    if len(protein_title) > 30: #  title's too long.  got some work to do
        protein_title = protein.pro_abbrev

    title = 'Monkey %s: %s' % (str(monkey.pk), protein_title)
    x_label = "Date of sample"
    y_label = "Protein Value (in %s)" % protein.pro_units

    dates = MonkeyProtein.objects.filter(monkey=monkey, protein=protein).order_by('mpn_date').values_list('mpn_date',
                                                                                                          flat=True).distinct()
    y_values = []
    for date in dates:
        monkey_protein = MonkeyProtein.objects.get(monkey=monkey, protein=protein, mpn_date=date)
        if afternoon_reading is None:
            y_values.append(monkey_protein.mpn_value)
        elif afternoon_reading is True and monkey_protein.mpn_date.hour > 12:
            y_values.append(monkey_protein.mpn_value)
        elif afternoon_reading is False and monkey_protein.mpn_date.hour <= 12:
            y_values.append(monkey_protein.mpn_value)
        else:
            dates = dates.exclude(mpn_date=date)

    fig = _monkey_tools_single_line(dates, y_values, title, x_label, y_label)
    return fig, False


def monkey_hormone_stdev(monkey, hormone_fieldnames):
    def _calculate_stdev(monkey_hormone, mhm_fieldname):
        cohort_monkeys = monkey_hormone.monkey.cohort.monkey_set.all().exclude(mky_id=monkey_hormone.monkey.pk)
        cohort_hormones = MonkeyHormone.objects.filter(mhm_date=monkey_hormone.mhm_date, monkey__in=cohort_monkeys)
        cohort_hormones = cohort_hormones.exclude(
            Q(**{mhm_fieldname: None})) # numpy.array().mean() blows up with None values in the array.
        ch_values = numpy.array(cohort_hormones.values_list(mhm_fieldname, flat=True))
        stdev = ch_values.std()
        mean = ch_values.mean()
        value = getattr(monkey_hormone, mhm_fieldname)
        if not mean or not value:
            return None
        diff = value - mean
        return diff / stdev

    fieldname_count = len(hormone_fieldnames)
    color_map = get_cmap('gist_rainbow')
    x_values = list()
    y_values = list()
    colors = list()
    labels = list()
    y_val = list()
    for index, hormone in enumerate(hormone_fieldnames):
        mhm_dates = MonkeyHormone.objects.filter(monkey=monkey).order_by('mhm_date').values_list('mhm_date', flat=True).distinct()
        y_val = []
        dates = []
        for date in mhm_dates:
            monkey_hormone = MonkeyHormone.objects.get(monkey=monkey, mhm_date=date)
            y_val.append(_calculate_stdev(monkey_hormone, hormone))
            dates.append(date)
        if len(y_val) == 0:
            continue
        x_values.append(dates)
        y_values.append(y_val)
        colors.append(color_map(float(index) / fieldname_count))
        verbose_hormone = MonkeyHormone._meta.get_field(hormone).verbose_name
        labels.append(verbose_hormone)

    if len(y_val) == 0:
        return False, False
    x_label = "Date of sample"
    y_label = "Standard deviation from cohort mean"
    hormone_title = ", ".join(labels)
    if len(hormone_title) > 30: #  title's too long.  got some work to do
        title_abbrev = hormone_title[:40].split(', ') # first, chop it to a good length and split it into a list
        title_abbrev.pop(len(
            title_abbrev) - 1) # now, pop off the last value in the list, since its probably a randomly cut string, like "Washi" instead of "Washington"
        hormone_title = ", ".join(title_abbrev) # and join the remainders back together
        hormone_title += "..." # and tell people we chopped it
    title = 'Monkey %s: %s' % (str(monkey.pk), hormone_title)
    if any(x_values):
        fig = _monkey_tools_multiple_lines(x_values, y_values, colors, labels, title, x_label, y_label)
        return fig, False
    return False, False


def monkey_hormone_pctdev(monkey, hormone_fieldnames):
    def _populate_pctdev(monkey_hormone, mhm_fieldname):
        cohort_monkeys = monkey_hormone.monkey.cohort.monkey_set.all().exclude(mky_id=monkey_hormone.monkey.pk)
        cohort_hormones = MonkeyHormone.objects.filter(mhm_date=monkey_hormone.mhm_date, monkey__in=cohort_monkeys)
        cohort_hormones = cohort_hormones.exclude(
            Q(**{mhm_fieldname: None})) # numpy.array().mean() blows up with None values in the array.
        ch_values = numpy.array(cohort_hormones.values_list(mhm_fieldname, flat=True))
        mean = ch_values.mean()
        value = getattr(monkey_hormone, mhm_fieldname)
        if not mean or not value:
            return None
        diff = value - mean
        return diff / mean * 100

    fieldname_count = len(hormone_fieldnames)
    color_map = get_cmap('gist_rainbow')
    x_values = list()
    y_values = list()
    colors = list()
    labels = list()
    y_val = list()
    for index, hormone in enumerate(hormone_fieldnames):
        mhm_dates = MonkeyHormone.objects.filter(monkey=monkey).order_by('mhm_date').values_list('mhm_date', flat=True).distinct()
        y_val = []
        dates = []
        for date in mhm_dates:
            monkey_hormone = MonkeyHormone.objects.get(monkey=monkey, mhm_date=date)
            y_val.append(_populate_pctdev(monkey_hormone, hormone))
            dates.append(date)
        if len(y_val) == 0:
            continue
        x_values.append(dates)
        y_values.append(y_val)
        colors.append(color_map(float(index) / fieldname_count))
        verbose_hormone = MonkeyHormone._meta.get_field(hormone).verbose_name
        labels.append(verbose_hormone)

    if len(y_val) == 0:
        return False, False
    x_label = "Date of sample"
    y_label = "Standard deviations from cohort mean"
    hormone_title = ", ".join(labels)
    if len(hormone_title) > 30: #  title's too long.  got some work to do
        title_abbrev = hormone_title[:40].split(', ') # first, chop it to a good length and split it into a list
        title_abbrev.pop(len(
            title_abbrev) - 1) # now, pop off the last value in the list, since its probably a randomly cut string, like "Washi" instead of "Washington"
        hormone_title = ", ".join(title_abbrev) # and join the remainders back together
        hormone_title += "..." # and tell people we chopped it
    title = 'Monkey %s: %s' % (str(monkey.pk), hormone_title)
    if any(x_values):
        fig = _monkey_tools_multiple_lines(x_values, y_values, colors, labels, title, x_label, y_label)
        return fig, False
    return False, False


def monkey_hormone_value(monkey, hormone_fieldnames, scaled=False):
    """
    monkey = Monkey Instance or pk or mky_real_id
    hormones = list of MonkeyHormone fieldnames.  Only the first is used.
    afternoon_reading = boolean indicating the hormones should be filtered to exclude morning/afternoon readings
    """
    hormone = hormone_fieldnames[0]
    verbose_hormone = MonkeyHormone._meta.get_field(hormone).verbose_name
    title = 'Monkey %s: %s' % (str(monkey.pk), verbose_hormone)
    x_label = "Date of sample"
    y_label = "Hormone Value, %s" % MonkeyHormone.UNITS[hormone]

    monkey_hormones = MonkeyHormone.objects.filter(monkey=monkey)
    monkey_hormones = monkey_hormones.exclude(**{hormone: None})
    dates = monkey_hormones.order_by('mhm_date').values_list('mhm_date', flat=True).distinct()
    y_values = []
    for date in dates:
        monkey_hormone = monkey_hormones.get(mhm_date=date)
        y_values.append(getattr(monkey_hormone, hormone))
    if not len(y_values):
        return False, False

    scale_y = ()
    if scaled:
        min_field = "cbc_%s_min" % hormone
        max_field = "cbc_%s_max" % hormone
        cbcs = CohortMetaData.objects.exclude(Q(**{min_field: None})).exclude(Q(**{max_field: None}))
        cbc_scales = cbcs.aggregate(Min(min_field), Max(max_field))
        scale_y = (cbc_scales[min_field + "__min"], cbc_scales[max_field + '__max'])
    fig = _monkey_tools_single_line(dates, y_values, title, x_label, y_label, scale_y=scale_y)
    return fig, False


def monkey_etoh_bouts_drinks(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
    """
        Scatter plot for monkey
                x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
            y axis - total number of drinks (bouts * drinks per bout)
            color - number of bouts
            size - drinks per bout
        Circle sizes scaled to range [cirle_min, circle_max]
    """
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
        temp = circle_max
        circle_max = circle_min
        circle_min = circle_max
    else:
        if circle_max < 10:
            circle_max = DEFAULT_CIRCLE_MAX
        if circle_min < 1:
            circle_min = DEFAULT_CIRCLE_MIN

    drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
    if to_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)
    drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

    if drinking_experiments.count() > 0:
        dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
    else:
        return None, False

    scatter_y_label = ''
    scatter_color_label = ''
    scatter_size_label = ''
    induction_days = list()
    scatter_y = list()
    scatter_size = list()
    scatter_color = list()
    for index, date in enumerate(dates, 1):
        de = drinking_experiments.get(drinking_experiment__dex_date=date)
        if de.drinking_experiment.dex_type == 'Induction':
            induction_days.append(index)
        scatter_y.append(de.mtd_etoh_intake)
        scatter_size.append(de.mtd_etoh_bout)
        scatter_color.append(de.mtd_etoh_mean_bout_vol)
        if not scatter_y_label:
            scatter_y_label = de._meta.get_field('mtd_etoh_intake').verbose_name
        if not scatter_color_label:
            scatter_color_label = de._meta.get_field('mtd_etoh_mean_bout_vol').verbose_name
        if not scatter_size_label:
            scatter_size_label = de._meta.get_field('mtd_etoh_bout').verbose_name

    xaxis = numpy.array(range(1, len(scatter_size) + 1))
    scatter_y = numpy.array(scatter_y)
    scatter_size = numpy.array(scatter_size)
    scatter_color = numpy.array(scatter_color)
    induction_days = numpy.array(induction_days)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
    etoh_b_d_main_plot = fig.add_subplot(main_gs[:, 0:39])

    size_min = circle_min
    size_scale = circle_max - size_min
    size_max = float(cbc.cbc_mtd_etoh_bout_max)
    rescaled_bouts = [(b / size_max) * size_scale + size_min for b in
                      scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)

    s = etoh_b_d_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_bouts, alpha=0.4)

    y_max = cbc.cbc_mtd_etoh_intake_max
    graph_y_max = y_max + y_max * 0.25
    if len(induction_days) and len(induction_days) != len(xaxis):
        etoh_b_d_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                               edgecolor='black', zorder=-100)

    etoh_b_d_main_plot.set_ylabel(scatter_y_label)
    etoh_b_d_main_plot.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")))

    etoh_b_d_main_plot.set_ylim(cbc.cbc_mtd_etoh_intake_max, graph_y_max)
    etoh_b_d_main_plot.set_xlim(0, xaxis.max() + 2)

    max_y_int = int(round(y_max * 1.25))
    y_tick_int = int(round(max_y_int / 5))
    etoh_b_d_main_plot.set_yticks(range(0, max_y_int, y_tick_int))
    etoh_b_d_main_plot.yaxis.get_label().set_position((0, 0.6))

    main_color = fig.add_subplot(main_gs[:, 39:])
    cb = fig.colorbar(s, alpha=1, cax=main_color)
    cb.set_label(scatter_color_label)
    cb.set_clim(cbc.cbc_mtd_etoh_mean_bout_vol_min, cbc.cbc_mtd_etoh_mean_bout_vol_max)

    #	regression line
    fit = polyfit(xaxis, scatter_y, 3)
    xr = polyval(fit, xaxis)
    etoh_b_d_main_plot.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

    #   size legend
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

    etoh_b_d_size_plot = fig.add_subplot(931)
    etoh_b_d_size_plot.set_position((0.05, .89, .3, .07))
    etoh_b_d_size_plot.scatter(x, y, s=size, alpha=0.4)
    etoh_b_d_size_plot.set_xlabel(scatter_size_label)
    etoh_b_d_size_plot.yaxis.set_major_locator(NullLocator())
    pyplot.setp(etoh_b_d_size_plot, xticklabels=bout_labels)

    hist_gs = gridspec.GridSpec(4, 1)
    hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)

    etoh_b_d_hist = fig.add_subplot(hist_gs[0, :])
    plot_tools._histogram_legend(monkey, etoh_b_d_hist)

    etoh_b_d_hist = fig.add_subplot(hist_gs[1, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_intake', etoh_b_d_hist, from_date=from_date, to_date=to_date,
                              dex_type=dex_type)
    etoh_b_d_hist = fig.add_subplot(hist_gs[2, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_bout', etoh_b_d_hist, from_date=from_date, to_date=to_date,
                              dex_type=dex_type, )
    etoh_b_d_hist = fig.add_subplot(hist_gs[3, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_mean_bout_vol', etoh_b_d_hist, from_date=from_date,
                              to_date=to_date, dex_type=dex_type, )

    zipped = numpy.vstack(zip(xaxis, scatter_y))
    coordinates = etoh_b_d_main_plot.transData.transform(zipped)
    ids = [de.pk for de in drinking_experiments]
    xcoords, inv_ycoords = zip(*coordinates)
    ycoords = [fig.get_window_extent().height - point for point in inv_ycoords]
    datapoint_map = zip(ids, xcoords, ycoords)
    return fig, datapoint_map


def monkey_etoh_bouts_drinks_intraday(mtd=None):
    if not isinstance(mtd, MonkeyToDrinkingExperiment):
        try:
            mtd = MonkeyToDrinkingExperiment.objects.get(mtd_id=mtd)
        except MonkeyToDrinkingExperiment.DoesNotExist:
            print("That's not a valid MonkeyToDrinkingExperiment.")
            return False, False

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = fig.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
    ax1.set_axisbelow(True)
    ax1.set_title('Drinks on %s for monkey %s' % (mtd.drinking_experiment.dex_date, str(mtd.monkey.pk)))
    ax1.set_xlabel("Time from Start of Experiment (in seconds)")
    ax1.set_ylabel("Ethanol Amount (in ml)")

    drink_colors = ['red', 'orange']
    bout_colors = ['green', 'blue']
    colorcount = 0

    bouts = mtd.bouts_set.all()
    X = Xend = None
    if bouts:
        for bout in bouts:
            X = bout.ebt_start_time
            Xend = bout.ebt_length
            Y = bout.ebt_volume
            ax1.bar(X, Y, width=Xend, color=bout_colors[colorcount % 2], alpha=.5, zorder=1)
            for drink in bout.drinks_set.all():
                xaxis = drink.edr_start_time
                yaxis = drink.edr_volume
                ax1.scatter(xaxis, yaxis, c=drink_colors[colorcount % 2], s=60, zorder=2)

            colorcount += 1

        ax1.set_xlim(xmin=0)
        ax1.set_ylim(ymin=0)
        if X + Xend > 60 * 60:
            ax1.set_xticks(range(0, X + Xend, 60 * 60))
        else:
            ax1.set_xticks(range(0, 60 * 60 + 1, 60 * 60))
        return fig, "bouts intraday"
    else:
        print("No bouts data available for this monkey drinking experiment.")
        return False, False


def monkey_etoh_bouts_vol(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
    """
        Scatter plot for monkey
            x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
            y axis - g/kg consumed that day
            color - number of bouts
            size - avg volume per bout
        Circle sizes scaled to range [cirle_min, circle_max]
        Plot saved to filename or to static/images/monkeys-bouts-drinks as mky_[real_id].png and mky_[real_id]-thumb.png
    """
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
        circle_max = DEFAULT_CIRCLE_MAX
        circle_min = DEFAULT_CIRCLE_MIN
    else:
        if circle_max < 10:
            circle_max = DEFAULT_CIRCLE_MAX
        if circle_min < 1:
            circle_min = DEFAULT_CIRCLE_MIN

    drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
    if to_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)

    drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

    if drinking_experiments.count() > 0:
        dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
    else:
        return None, False

    scatter_y_label = ''
    scatter_color_label = ''
    scatter_size_label = ''
    induction_days = list()
    scatter_y = list()
    scatter_color = list()
    scatter_size = list()
    for index, date in enumerate(dates, 1):
        de = drinking_experiments.get(drinking_experiment__dex_date=date)
        if de.drinking_experiment.dex_type == 'Induction':
            induction_days.append(index)
        scatter_y.append(de.mtd_etoh_g_kg)
        scatter_color.append(de.mtd_etoh_bout)
        bouts_volume = de.bouts_set.all().aggregate(Avg('ebt_volume'))['ebt_volume__avg']
        scatter_size.append(bouts_volume if bouts_volume else 0)
        if not scatter_y_label:
            scatter_y_label = de._meta.get_field('mtd_etoh_g_kg').verbose_name
        if not scatter_color_label:
            scatter_color_label = de._meta.get_field('mtd_etoh_bout').verbose_name
        if not scatter_size_label:
            scatter_size_label = "Avg bout volume"

    xaxis = numpy.array(range(1, len(scatter_size) + 1))
    scatter_size = numpy.array(scatter_size)
    scatter_color = numpy.array(scatter_color)
    induction_days = numpy.array(induction_days)

    size_min = circle_min
    size_scale = circle_max - size_min
    volume_max = cbc.cbc_ebt_volume_max
    rescaled_volumes = [(vol / volume_max) * size_scale + size_min for vol in
                        scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
    etoh_bout_vol_main = fig.add_subplot(main_gs[:, 0:39])
    s = etoh_bout_vol_main.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)

    etoh_bout_vol_main.set_ylabel("Daily Ethanol Consumption (in g/kg)")
    etoh_bout_vol_main.set_xlabel("Days")
    etoh_bout_vol_main.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")))

    y_max = cbc.cbc_mtd_etoh_g_kg_max
    graph_y_max = y_max + y_max * 0.25
    pyplot.ylim(0, graph_y_max)
    pyplot.xlim(0, len(xaxis) + 1)
    if len(induction_days) and len(induction_days) != len(xaxis):
        etoh_bout_vol_main.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                               edgecolor='black', zorder=-100)

    etoh_bout_vol_color = fig.add_subplot(main_gs[:, 39:])
    cb = fig.colorbar(s, alpha=1, cax=etoh_bout_vol_color)
    cb.set_label(scatter_color_label)
    cb.set_clim(cbc.cbc_mtd_etoh_bout_min, cbc.cbc_mtd_etoh_bout_max)

    #    size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = size_scale / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = volume_max / (len(y) - 1)
    size_labels = [int(round(i * m)) for i in range(1, len(y))] # labels in the range as number of bouts
    size_labels.insert(0, "1")
    size_labels.insert(0, "")
    size_labels.append("")

    etoh_bout_vol_size = fig.add_subplot(721)
    etoh_bout_vol_size.scatter(x, y, s=size, alpha=0.4)
    etoh_bout_vol_size.set_xlabel(scatter_size_label)
    etoh_bout_vol_size.yaxis.set_major_locator(NullLocator())
    pyplot.setp(etoh_bout_vol_size, xticklabels=size_labels)

    #	regression line
    try:
        fit = polyfit(xaxis, scatter_y, 3)
    except TypeError as e: # "unsupported operand type(s) for +: 'NoneType' and 'float'"
        pass
    else:
        xr = polyval(fit, xaxis)
        etoh_bout_vol_main.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

    #	histograms
    hist_gs = gridspec.GridSpec(4, 1)
    hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)

    etoh_bout_vol_hist = fig.add_subplot(hist_gs[0, :])
    plot_tools._histogram_legend(monkey, etoh_bout_vol_hist)

    etoh_bout_vol_hist = fig.add_subplot(hist_gs[1, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_g_kg', etoh_bout_vol_hist, from_date=from_date,
                              to_date=to_date, dex_type=dex_type)
    etoh_bout_vol_hist = fig.add_subplot(hist_gs[2, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_bout', etoh_bout_vol_hist, from_date=from_date,
                              to_date=to_date, dex_type=dex_type)
    etoh_bout_vol_hist = fig.add_subplot(hist_gs[3, :])
    plot_tools._mtd_histogram(monkey, 'bouts_set__ebt_volume', etoh_bout_vol_hist, from_date=from_date,
                              to_date=to_date, dex_type=dex_type, verbose_name='Bout Volume')

    zipped = numpy.vstack(zip(xaxis, scatter_y))
    coordinates = etoh_bout_vol_main.transData.transform(zipped)
    ids = [de.pk for de in drinking_experiments]
    xcoords, inv_ycoords = zip(*coordinates)
    ycoords = [fig.get_window_extent().height - point for point in inv_ycoords]
    datapoint_map = zip(ids, xcoords, ycoords)
    return fig, datapoint_map


def monkey_etoh_first_max_bout(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
    """
        Scatter plot for monkey
            x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
            y axis - total number of drinks (scatter_size * drinks per bout)
            color - number of scatter_size
            size - drinks per bout
        Circle sizes scaled to range [cirle_min, circle_max]
    """
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
        circle_max = DEFAULT_CIRCLE_MAX
        circle_min = DEFAULT_CIRCLE_MIN
    else:
        if circle_max < 10:
            circle_max = DEFAULT_CIRCLE_MAX
        if circle_min < 1:
            circle_min = DEFAULT_CIRCLE_MIN

    drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
    if to_date:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)
    drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

    if drinking_experiments.count() > 0:
        dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
    else:
        return None, False

    bar_y_label = ''
    bar_color_label = ''
    scatter_y_label = ''
    scatter_color_label = ''
    scatter_size_label = ''
    xaxis = list()
    induction_days = list()
    scatter_y = list()
    scatter_size = list()
    scatter_color = list()
    bar_yaxis = list()
    bar_color = list()
    for index, date in enumerate(dates, 1):
        xaxis.append(index)
        de = drinking_experiments.get(drinking_experiment__dex_date=date)
        if de.drinking_experiment.dex_type == 'Induction':
            induction_days.append(index)
        scatter_y.append(de.mtd_max_bout_vol)
        scatter_size.append(de.mtd_max_bout_length)
        scatter_color.append(de.mtd_pct_max_bout_vol_total_etoh)
        bar_yaxis.append(de.mtd_vol_1st_bout)
        bar_color.append(de.mtd_pct_etoh_in_1st_bout)
        if not scatter_y_label:
            scatter_y_label = de._meta.get_field('mtd_max_bout_vol').verbose_name
        if not scatter_color_label:
            scatter_color_label = de._meta.get_field('mtd_pct_max_bout_vol_total_etoh').verbose_name
        if not scatter_size_label:
            scatter_size_label = de._meta.get_field("mtd_max_bout_length").verbose_name
        if not bar_y_label:
            bar_y_label = de._meta.get_field('mtd_vol_1st_bout').verbose_name
        if not bar_color_label:
            bar_color_label = de._meta.get_field('mtd_pct_etoh_in_1st_bout').verbose_name

    xaxis = numpy.array(xaxis)
    induction_days = numpy.array(induction_days)
    scatter_y = numpy.array(scatter_y)
    scatter_size = numpy.array(scatter_size)
    scatter_color = numpy.array(scatter_color)

    size_min = circle_min
    size_scale = circle_max - size_min
    max_bout_length_max = cbc.cbc_mtd_max_bout_length_max
    rescaled_bouts = [(bout / max_bout_length_max) * size_scale + size_min for bout in
                      scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
    etoh_1st_max_main = fig.add_subplot(main_gs[0:2, 0:39])
    s = etoh_1st_max_main.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_bouts, alpha=.6)

    y_max = cbc.cbc_mtd_max_bout_vol_max
    graph_y_max = y_max + y_max * 0.25
    if len(induction_days) and len(induction_days) != len(xaxis):
        etoh_1st_max_main.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                              edgecolor='black', zorder=-100)

    etoh_1st_max_main.set_ylabel(scatter_y_label)
    etoh_1st_max_main.set_xlabel("Days")

    etoh_1st_max_main.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")))

    pyplot.ylim(0, graph_y_max)
    pyplot.xlim(0, len(xaxis) + 2)
    max_y_int = int(round(y_max * 1.25))
    y_tick_int = int(round(max_y_int / 5))
    etoh_1st_max_main.set_yticks(range(0, max_y_int, y_tick_int))
    etoh_1st_max_main.yaxis.get_label().set_position((0, 0.6))

    etoh_1st_max_color = fig.add_subplot(main_gs[0:2, 39:])
    cb = fig.colorbar(s, alpha=1, cax=etoh_1st_max_color)
    cb.set_clim(cbc.cbc_mtd_pct_max_bout_vol_total_etoh_min, cbc.cbc_mtd_pct_max_bout_vol_total_etoh_max)
    cb.set_label(scatter_color_label)

    #	Regression line
    fit = polyfit(xaxis, scatter_y, 2)
    xr = polyval(fit, xaxis)
    etoh_1st_max_main.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

    #    size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = size_scale / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = max_bout_length_max / (len(y) - 1)
    bout_labels = [int(round(i * m)) for i in range(1, len(y))] # labels in the range as number of scatter_size
    bout_labels.insert(0, "1")
    bout_labels.insert(0, "")
    bout_labels.append("")

    etoh_1st_max_size = fig.add_subplot(931)
    etoh_1st_max_size.set_position((0, .89, .3, .07))
    etoh_1st_max_size.scatter(x, y, s=size, alpha=0.4)
    etoh_1st_max_size.set_xlabel(scatter_size_label)
    etoh_1st_max_size.yaxis.set_major_locator(NullLocator())
    pyplot.setp(etoh_1st_max_size, xticklabels=bout_labels)

    #	barplot
    etoh_1st_max_barplot = fig.add_subplot(main_gs[-1:, 0:39])

    etoh_1st_max_barplot.set_xlabel("Days")
    etoh_1st_max_barplot.set_ylabel(bar_y_label)
    etoh_1st_max_barplot.set_autoscalex_on(False)

    # normalize colors to use full range of colormap
    norm = colors.normalize(cbc.cbc_mtd_pct_etoh_in_1st_bout_min, cbc.cbc_mtd_pct_etoh_in_1st_bout_max)

    facecolors = list()
    for bar, x, color_value in zip(bar_yaxis, xaxis, bar_color):
        color = cm.jet(norm(color_value))
        pyplot.bar(x, bar, color=color, edgecolor='none')
        facecolors.append(color)

    etoh_1st_max_barplot.set_xlim(0, len(xaxis) + 2)
    etoh_1st_max_barplot.set_ylim(cbc.cbc_mtd_vol_1st_bout_min, cbc.cbc_mtd_vol_1st_bout_max)

    # create a collection that we will use in colorbox
    col = matplotlib.collections.Collection(facecolors=facecolors, norm=norm, cmap=cm.jet)
    col.set_array(bar_color)

    # colorbor for bar plot
    etoh_1st_max_barcolor = fig.add_subplot(main_gs[-1:, 39:])
    cb = fig.colorbar(col, alpha=1, cax=etoh_1st_max_barcolor)
    cb.set_label(bar_color_label)

    hist_gs = gridspec.GridSpec(6, 1)
    hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)

    etoh_1st_max_hist = fig.add_subplot(hist_gs[0, :])
    plot_tools._histogram_legend(monkey, etoh_1st_max_hist)

    etoh_1st_max_hist = fig.add_subplot(hist_gs[1, :])
    plot_tools._mtd_histogram(monkey, 'mtd_max_bout_vol', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
    etoh_1st_max_hist = fig.add_subplot(hist_gs[2, :])
    plot_tools._mtd_histogram(monkey, 'mtd_max_bout_length', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type, hide_xticks=True)
    etoh_1st_max_hist = fig.add_subplot(hist_gs[3, :])
    plot_tools._mtd_histogram(monkey, 'mtd_pct_max_bout_vol_total_etoh', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
    etoh_1st_max_hist = fig.add_subplot(hist_gs[4, :])
    plot_tools._mtd_histogram(monkey, 'mtd_vol_1st_bout', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
    etoh_1st_max_hist = fig.add_subplot(hist_gs[5, :])
    plot_tools._mtd_histogram(monkey, 'mtd_pct_etoh_in_1st_bout', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)

    zipped = numpy.vstack(zip(xaxis, scatter_y))
    coordinates = etoh_1st_max_main.transData.transform(zipped)
    ids = [de.pk for de in drinking_experiments]
    xcoords, inv_ycoords = zip(*coordinates)
    ycoords = [fig.get_window_extent().height - point for point in inv_ycoords]
    datapoint_map = zip(ids, xcoords, ycoords)
    return fig, datapoint_map


def monkey_etoh_induction_cumsum(monkey):
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    stages = dict()
    stages[1] = Q(eev_dose=.5)
    stages[2] = Q(eev_dose=1)
    stages[3] = Q(eev_dose=1.5)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)

    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.05) # sharing xaxis

    stage_plot = fig.add_subplot(main_gs[0:1, 2:39])
    stage_plot.set_title("Induction Cumulative Intraday EtOH Intake for %s" % str(monkey))
    for stage in stages.keys():
        if stage > 1:
            stage_plot = fig.add_subplot(main_gs[stage - 1:stage, 2:39], sharey=stage_plot, sharex=stage_plot) # sharing xaxis
        eevs = ExperimentEvent.objects.filter(monkey=monkey, dex_type='Induction').exclude(eev_etoh_volume=None).order_by(
            'eev_occurred')
        stage_x = eevs.filter(stages[stage])
        plot_tools._days_cumsum_etoh(stage_x, stage_plot)
        stage_plot.get_xaxis().set_visible(False)
        stage_plot.legend((), title="Stage %d" % stage, loc=1, frameon=False, prop={'size': 12})

    stage_plot.set_ylim(ymin=0)
    stage_plot.yaxis.set_major_locator(MaxNLocator(3))
    stage_plot.set_xlim(xmin=0)

    # yaxis label
    ylabel = fig.add_subplot(main_gs[:, 0:2])
    ylabel.set_axis_off()
    ylabel.set_xlim(0, 1)
    ylabel.set_ylim(0, 1)
    ylabel.text(.05, 0.5, "Cumulative EtOH intake, ml", rotation='vertical', horizontalalignment='center',
                verticalalignment='center')
    return fig, True


def monkey_etoh_lifetime_cumsum(monkey):
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)

    #   main graph
    main_gs = gridspec.GridSpec(1, 40)
    main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.05) # sharing xaxis

    lifetime_plot = fig.add_subplot(main_gs[:, 1:41])
    lifetime_plot.set_title("Lifetime Cumulative EtOH Intake for %s" % str(monkey))

    for m in monkey.cohort.monkey_set.all():
        color_monkey = m.pk == monkey.pk
        eevs = ExperimentEvent.objects.filter(monkey=m).exclude(eev_etoh_volume=None).order_by('eev_occurred')
        plot_tools._lifetime_cumsum_etoh(eevs, lifetime_plot, color_monkey=color_monkey)

    lifetime_plot.get_xaxis().set_visible(False)
    return fig, True


def monkey_mtd_histogram_general(monkey, column_name, dex_type=''):
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    mtd_records = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
    if dex_type:
        mtd_records = mtd_records.filter(drinking_experiment__dex_type=dex_type)

    if not mtd_records:
        return False, False

    field = mtd_records[0]._meta.get_field(column_name)
    if not isinstance(field, (
        models.FloatField, models.IntegerField, models.BigIntegerField, models.SmallIntegerField, models.PositiveIntegerField,
        models.PositiveSmallIntegerField)):
        return False, False

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(1, 1)
    main_gs.update(left=0.05, right=0.95, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    plot_tools._mtd_histogram(monkey, column_name, main_plot, dex_type=dex_type, show_legend=True)
    return fig, True


def monkey_bec_histogram_general(monkey, column_name, dex_type=''):
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    bec_records = MonkeyBEC.objects.filter(monkey=monkey)
    if dex_type:
        bec_records = bec_records.filter(drinking_experiment__dex_type=dex_type)

    if not bec_records:
        return False, False

    field = bec_records[0]._meta.get_field(column_name)
    if not isinstance(field, (
        models.FloatField, models.IntegerField, models.BigIntegerField, models.SmallIntegerField, models.PositiveIntegerField,
        models.PositiveSmallIntegerField)):
        return False, False

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(1, 1)
    main_gs.update(left=0.05, right=0.95, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    plot_tools._bec_histogram(monkey, column_name, main_plot, dex_type=dex_type, show_legend=True)
    return fig, True


def monkey_bec_bubble(monkey=None, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
    """
        Scatter plot for monkey
            x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
            y axis - BEC
            color - intake at time of sample, g/kg
            size - % of daily intake consumed at time of sample
        Circle sizes scaled to range [cirle_min, circle_max]
    """
    gc.collect()
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    if circle_max < circle_min:
        circle_max = DEFAULT_CIRCLE_MAX
        circle_min = DEFAULT_CIRCLE_MIN
    else:
        if circle_max < 10:
            circle_max = DEFAULT_CIRCLE_MAX
        if circle_min < 1:
            circle_min = DEFAULT_CIRCLE_MIN

    cbc = monkey.cohort.cbc
    bec_records = monkey.bec_records.all()
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
    if to_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
    if sample_before:
        bec_records = bec_records.filter(bec_sample__lte=sample_before)
    if sample_after:
        bec_records = bec_records.filter(bec_sample__gte=sample_after)

    if bec_records.count() > 0:
        dates = bec_records.dates('bec_collect_date', 'day').order_by('bec_collect_date')
    else:
        return False, False

    scatter_y_label = ''
    scatter_color_label = ''
    scatter_size_label = ''
    induction_days = list()
    scatter_y = list()
    scatter_size = list()
    scatter_color = list()
    for index, date in enumerate(dates, 1):
        bec_rec = bec_records.get(bec_collect_date=date)
        if bec_rec.mtd.drinking_experiment.dex_type == 'Induction':
            induction_days.append(index)
        scatter_y.append(bec_rec.bec_mg_pct)
        scatter_size.append(bec_rec.bec_pct_intake)
        scatter_color.append(bec_rec.bec_gkg_etoh)
        if not scatter_y_label:
            scatter_y_label = bec_rec._meta.get_field('bec_mg_pct').verbose_name
        if not scatter_size_label:
            scatter_size_label = bec_rec._meta.get_field("bec_pct_intake").verbose_name
        if not scatter_color_label:
            scatter_color_label = bec_rec._meta.get_field('bec_gkg_etoh').verbose_name

    xaxis = numpy.array(range(1, len(scatter_color) + 1))
    scatter_color = numpy.array(scatter_color) # color
    scatter_size = numpy.array(scatter_size) # size
    induction_days = numpy.array(induction_days)

    size_min = circle_min
    size_scale = circle_max - size_min

    max_intake = cbc.cbc_bec_pct_intake_max
    rescaled_volumes = [(w / max_intake) * size_scale + size_min for w in
                        scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
    bec_bub_main_plot = fig.add_subplot(main_gs[:, 0:39])
    s = bec_bub_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)
    bec_bub_main_plot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    bec_bub_main_plot.text(0, 82, "80 mg pct")

    bec_bub_main_plot.set_ylabel(scatter_y_label)
    bec_bub_main_plot.set_xlabel("Sample Days")
    bec_bub_main_plot.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")))

    y_max = cbc.cbc_bec_mg_pct_max
    graph_y_max = y_max + y_max * 0.25
    bec_bub_main_plot.set_ylim(0, graph_y_max)
    bec_bub_main_plot.set_xlim(0, len(xaxis) + 1)
    if len(induction_days) and len(induction_days) != len(xaxis):
        bec_bub_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                              edgecolor='black', zorder=-100)

    bec_bub_main_color = fig.add_subplot(main_gs[:, 39:])
    cb = fig.colorbar(s, alpha=1, cax=bec_bub_main_color)
    cb.set_label(scatter_color_label)
    cb.set_clim(cbc.cbc_bec_gkg_etoh_min, cbc.cbc_bec_gkg_etoh_max)

    #    size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = float(size_scale) / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = max_intake / (len(y) - 1)
    size_labels = [round(i * m, 2) for i in range(1, len(y))] # labels in the range as monkey weights
    size_labels.insert(0, round(cbc.cbc_bec_pct_intake_min, 2))
    size_labels.insert(0, "")
    size_labels.append("")

    bec_bub_size_fig = fig.add_subplot(721)
    bec_bub_size_fig.scatter(x, y, s=size, alpha=0.4)
    bec_bub_size_fig.set_xlabel(scatter_size_label)
    bec_bub_size_fig.yaxis.set_major_locator(NullLocator())
    pyplot.setp(bec_bub_size_fig, xticklabels=size_labels)

    hist_gs = gridspec.GridSpec(4, 1)
    hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)

    bec_bub_hist = fig.add_subplot(hist_gs[0, :])
    plot_tools._histogram_legend(monkey, bec_bub_hist)

    bec_bub_hist = fig.add_subplot(hist_gs[1, :])
    plot_tools._bec_histogram(monkey, 'bec_mg_pct', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)

    bec_bub_hist = fig.add_subplot(hist_gs[2, :])
    plot_tools._bec_histogram(monkey, 'bec_pct_intake', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)

    bec_bub_hist = fig.add_subplot(hist_gs[3, :])
    plot_tools._bec_histogram(monkey, 'bec_gkg_etoh', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
    return fig, True


def monkey_bec_consumption(monkey=None, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
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
        circle_max = DEFAULT_CIRCLE_MAX
        circle_min = DEFAULT_CIRCLE_MIN
    else:
        if circle_max < 10:
            circle_max = DEFAULT_CIRCLE_MAX
        if circle_min < 1:
            circle_min = DEFAULT_CIRCLE_MIN

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

    bar_y_label = ''
    bar_color_label = ''
    scatter_y_label = ''
    scatter_color_label = ''
    scatter_size_label = ''
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
            bar_color.append(bec_rec.bec_pct_intake)
            bar_xaxis.append(index)
            if not bar_color_label:
                bar_color_label = bec_rec._meta.get_field('bec_pct_intake').verbose_name
            if not bar_y_label:
                bar_y_label = bec_rec._meta.get_field('bec_mg_pct').verbose_name

        de = drinking_experiments.get(drinking_experiment__dex_date=date)
        if de.drinking_experiment.dex_type == 'Induction':
            induction_days.append(index)
        scatter_y.append(de.mtd_etoh_g_kg) # y-axis
        scatter_color.append(de.mtd_etoh_bout) # color
        bouts_volume = de.bouts_set.all().aggregate(Avg('ebt_volume'))['ebt_volume__avg']
        scatter_size.append(bouts_volume if bouts_volume else 0) # size
        if not scatter_y_label:
            scatter_y_label = de._meta.get_field('mtd_etoh_g_kg').verbose_name
        if not scatter_color_label:
            scatter_color_label = de._meta.get_field('mtd_etoh_bout').verbose_name
        if not scatter_size_label:
            scatter_size_label = "Avg bout volume"

    xaxis = numpy.array(range(1, len(scatter_size) + 1))
    scatter_size = numpy.array(scatter_size)
    scatter_color = numpy.array(scatter_color)
    bar_color = numpy.array(bar_color)
    induction_days = numpy.array(induction_days)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    #   main graph
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
    bec_con_main_plot = fig.add_subplot(main_gs[0:2, 0:39])
    bec_con_main_plot.set_xticks([])

    size_min = circle_min
    size_scale = circle_max - size_min
    volume_max = cbc.cbc_ebt_volume_max
    rescaled_volumes = [(vol / volume_max) * size_scale + size_min for vol in
                        scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)

    s = bec_con_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)

    y_max = cbc.cbc_mtd_etoh_g_kg_max
    graph_y_max = y_max + y_max * 0.25
    if len(induction_days) and len(induction_days) != len(xaxis):
        bec_con_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                              edgecolor='black', zorder=-100)

    bec_con_main_plot.set_ylabel(scatter_y_label)
    bec_con_main_plot.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")))

    bec_con_main_plot.set_ylim(0, graph_y_max)
    bec_con_main_plot.set_xlim(0, len(xaxis) + 2)

    max_y_int = int(round(y_max * 1.25))
    y_tick_int = max(int(round(max_y_int / 5)), 1)
    bec_con_main_plot.set_yticks(range(0, max_y_int, y_tick_int))
    bec_con_main_plot.yaxis.get_label().set_position((0, 0.6))

    bec_con_main_color_plot = fig.add_subplot(main_gs[0:2, 39:])
    cb = fig.colorbar(s, alpha=1, cax=bec_con_main_color_plot)
    cb.set_clim(cbc.cbc_mtd_etoh_bout_min, cbc.cbc_mtd_etoh_bout_max)
    cb.set_label(scatter_color_label)

    #	regression line
    fit = polyfit(xaxis, scatter_y, 3)
    xr = polyval(fit, xaxis)
    bec_con_main_plot.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

    #    size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = size_scale / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = volume_max / (len(y) - 1)
    bout_labels = [int(round(i * m)) for i in range(1, len(y))] # labels in the range as number of bouts
    bout_labels.insert(0, "1")
    bout_labels.insert(0, "")
    bout_labels.append("")

    bec_con_size_plot = fig.add_subplot(931)
    bec_con_size_plot.set_position((0.05, .89, .3, .07))
    bec_con_size_plot.scatter(x, y, s=size, alpha=0.4)
    bec_con_size_plot.set_xlabel(scatter_size_label)
    bec_con_size_plot.yaxis.set_major_locator(NullLocator())
    pyplot.setp(bec_con_size_plot, xticklabels=bout_labels)

    #	barplot
    bec_con_bar_plot = fig.add_subplot(main_gs[-1:, 0:39])

    bec_con_bar_plot.set_xlabel("Days")
    bec_con_bar_plot.set_ylabel(bar_y_label)
    bec_con_bar_plot.set_autoscalex_on(False)

    # normalize colors to use full range of colormap
    norm = colors.normalize(cbc.cbc_bec_pct_intake_min, cbc.cbc_bec_pct_intake_max)

    facecolors = list()
    for bar, x, color_value in zip(bar_yaxis, bar_xaxis, bar_color):
        color = cm.jet(norm(color_value))
        bec_con_bar_plot.bar(x, bar, width=2, color=color, edgecolor='none')
        facecolors.append(color)
    bec_con_bar_plot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    bec_con_bar_plot.text(0, 82, "80 mg pct")

    bec_con_bar_plot.set_xlim(0, len(xaxis) + 2)
    if len(induction_days) and len(induction_days) != len(xaxis):
        bec_con_bar_plot.bar(induction_days.min(), bec_con_bar_plot.get_ylim()[1], width=induction_days.max(), bottom=0,
                             color='black', alpha=.2, edgecolor='black', zorder=-100)

    # create a collection that we will use in colorbox
    col = matplotlib.collections.Collection(facecolors=facecolors, norm=norm, cmap=cm.jet)
    col.set_array(bar_color)

    # colorbar for bar plot
    bec_con_bar_color = fig.add_subplot(main_gs[-1:, 39:])
    cb = fig.colorbar(col, alpha=1, cax=bec_con_bar_color)
    cb.set_label(bar_color_label)

    hist_gs = gridspec.GridSpec(6, 1)
    hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)
    bec_con_hist = fig.add_subplot(hist_gs[0, :])
    plot_tools._histogram_legend(monkey, bec_con_hist)

    bec_con_hist = fig.add_subplot(hist_gs[1, :])
    plot_tools._bec_histogram(monkey, 'bec_mg_pct', bec_con_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)

    bec_con_hist = fig.add_subplot(hist_gs[2, :])
    plot_tools._bec_histogram(monkey, 'bec_pct_intake', bec_con_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)

    bec_con_hist = fig.add_subplot(hist_gs[3, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_g_kg', bec_con_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)

    bec_con_hist = fig.add_subplot(hist_gs[4, :])
    plot_tools._mtd_histogram(monkey, 'mtd_etoh_bout', bec_con_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)

    bec_con_hist = fig.add_subplot(hist_gs[5, :])
    plot_tools._mtd_histogram(monkey, 'bouts_set__ebt_volume', bec_con_hist, from_date=from_date, to_date=to_date, dex_type=dex_type, verbose_name='Bout Volume')
    return fig, True


def monkey_bec_monthly_centroids(monkey, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    """
    """

    def add_1_month(date):
        new_month = date.month + 1
        if new_month > 12:
            return datetime(date.year + 1, 1, date.day)
        else:
            return datetime(date.year, new_month, date.day)

    def euclid_dist(point_a, point_b):
        import math

        return math.hypot(point_b[0] - point_a[0], point_b[1] - point_a[1])

    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False
    cohort = monkey.cohort

    bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
    if to_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
    if sample_before:
        bec_records = bec_records.filter(bec_sample__lte=sample_before)
    if sample_after:
        bec_records = bec_records.filter(bec_sample__gte=sample_after)
    bec_records = bec_records.order_by('bec_collect_date')

    if bec_records.count() > 0:
        dates = sorted(set(bec_records.dates('bec_collect_date', 'month').distinct()))
    else:
        return False, False

    cmap = get_cmap('jet')
    month_count = float(max(len(dates), 2)) # prevents zero division in the forloop below
    month_color = dict()
    for idx, key in enumerate(dates):
        month_color[key] = cmap(idx / (month_count - 1))

    mky_centroids = list()
    coh_centroids = list()
    colors = list()
    bar_x = list()
    for date in dates:
        min_date = date
        max_date = add_1_month(date)

        mtds = list()
        all_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort, drinking_experiment__dex_date__gte=min_date,
                                                             drinking_experiment__dex_date__lt=max_date)
        all_mtds = all_mtds.exclude(bec_record=None).exclude(bec_record__bec_mg_pct=None).exclude(bec_record__bec_mg_pct=0)
        if all_mtds.filter(monkey=monkey):
            mtds.append(all_mtds.filter(monkey=monkey))
            mtds.append(all_mtds.exclude(monkey=monkey))
            bar_x.append(date)
        for index, mtd_set in enumerate(mtds):
            xaxis = numpy.array(mtd_set.values_list('bec_record__bec_vol_etoh', flat=True))
            yaxis = mtd_set.values_list('bec_record__bec_mg_pct', flat=True)
            color = month_color[date]

            try:
                res, idx = vq.kmeans2(numpy.array(zip(xaxis, yaxis)), 1)
            except Exception as e:
                print e
                bar_x.remove(date)
            else:
                if index:
                    coh_centroids.append([res[:, 0][0], res[:, 1][0]])
                    colors.append(color)
                else:
                    mky_centroids.append([res[:, 0][0], res[:, 1][0]])

    gs = gridspec.GridSpec(30, 30)
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    bec_cen_dist_mainplot = fig.add_subplot(gs[0:22, 0:30])

    bar_x_labels = [date.strftime('%h %Y') for date in bar_x]
    bar_x = range(0, len(bar_x))
    bar_y = list()
    for a, b, color in zip(mky_centroids, coh_centroids, colors):
        x = [a[0], b[0]]
        y = [a[1], b[1]]
        bec_cen_dist_mainplot.plot(x, y, c=color, linewidth=3, alpha=.3)
        bar_y.append(euclid_dist(a, b))
    m = numpy.array(mky_centroids)
    c = numpy.array(coh_centroids)
    try:
        bec_cen_dist_mainplot.scatter(m[:, 0], m[:, 1], marker='o', s=100, linewidths=3, c=colors, edgecolor=colors,
                                      label='Monkey')
        bec_cen_dist_mainplot.scatter(c[:, 0], c[:, 1], marker='x', s=100, linewidths=3, c=colors, edgecolor=colors,
                                      label='Cohort')
    except IndexError: # m and c are empty if all_mtds.count() == 0
        return False, False

    bec_cen_dist_mainplot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    bec_cen_dist_mainplot.text(0, 82, "80 mg pct")

    _t = dex_type if dex_type else 'all'
    title = 'Monthly drinking effects for monkey %s, %s data' % (str(monkey.pk), _t)
    if sample_before:
        title += " before %s" % str(sample_before)
    if sample_after:
        title += " after %s" % str(sample_after)

    bec_cen_dist_mainplot.set_title(title)
    bec_cen_dist_mainplot.set_xlabel("Intake at sample")
    bec_cen_dist_mainplot.set_ylabel("Blood Ethanol Concentration, mg %")
    bec_cen_dist_mainplot.legend(loc="lower right", title='Centroids', scatterpoints=1, frameon=False)

    #	barplot
    bec_cen_dist_barplot = fig.add_subplot(gs[24:35, 0:30])

    bec_cen_dist_barplot.set_ylabel("Centroid Distance")
    bec_cen_dist_barplot.set_autoscalex_on(False)

    for _x, _y, color in zip(bar_x, bar_y, colors):
        bec_cen_dist_barplot.bar(_x, _y, color=color, edgecolor='none')

    bec_cen_dist_barplot.set_xlim(0, len(bar_x))
    bec_cen_dist_barplot.set_ylim(0, 400)
    bec_cen_dist_barplot.set_xticks(bar_x)
    bec_cen_dist_barplot.set_xticklabels(bar_x_labels, rotation=45)
    return fig, True


# Dictionary of ethanol monkey plots VIPs can customize
MONKEY_ETOH_TOOLS_PLOTS = {'monkey_etoh_bouts_vol': (monkey_etoh_bouts_vol, 'Ethanol Consumption'),
                           'monkey_etoh_first_max_bout': (monkey_etoh_first_max_bout, 'First Bout and Max Bout Details'),
                           'monkey_etoh_bouts_drinks': (monkey_etoh_bouts_drinks, 'Drinking Pattern'),
                           }
# BEC-related plots
MONKEY_BEC_TOOLS_PLOTS = { 'monkey_bec_bubble': (monkey_bec_bubble, 'BEC Plot'),
                           'monkey_bec_consumption': (monkey_bec_consumption, "BEC Consumption "),
                           'monkey_bec_monthly_centroids': (monkey_bec_monthly_centroids, "BEC Monthly Centroid Distance"),
                           }
# Dictionary of protein monkey plots VIPs can customize
MONKEY_PROTEIN_TOOLS_PLOTS = {'monkey_protein_stdev': (monkey_protein_stdev, "Protein Value (standard deviation)"),
                              'monkey_protein_pctdev': (monkey_protein_pctdev, "Protein Value (percent deviation)"),
                              'monkey_protein_value': (monkey_protein_value, "Protein Value (raw value)"),
                              }
# Dictionary of hormone monkey plots VIPs can customize
MONKEY_HORMONE_TOOLS_PLOTS = {'monkey_hormone_stdev': (monkey_hormone_stdev, "Hormone Value (standard deviation)"),
                              'monkey_hormone_pctdev': (monkey_hormone_pctdev, "Hormone Value (percent deviation)"),
                              'monkey_hormone_value': (monkey_hormone_value, "Hormone Value (raw value)"),
                              }
# Dictionary of Monkey Tools' plots
MONKEY_TOOLS_PLOTS = dict()
MONKEY_TOOLS_PLOTS.update(MONKEY_ETOH_TOOLS_PLOTS)
MONKEY_TOOLS_PLOTS.update(MONKEY_BEC_TOOLS_PLOTS)
MONKEY_TOOLS_PLOTS.update(MONKEY_PROTEIN_TOOLS_PLOTS)
MONKEY_TOOLS_PLOTS.update(MONKEY_HORMONE_TOOLS_PLOTS)

# Dictionary of all cohort plots
MONKEY_PLOTS = {}
MONKEY_PLOTS.update(MONKEY_TOOLS_PLOTS)
MONKEY_PLOTS.update({"monkey_necropsy_avg_22hr_g_per_kg": (monkey_necropsy_avg_22hr_g_per_kg, "Average Monkey Ethanol Intake, 22hr"),
                     "monkey_necropsy_etoh_4pct": (monkey_necropsy_etoh_4pct, "Total Monkey Ethanol Intake, ml"),
                     "monkey_necropsy_sum_g_per_kg": (monkey_necropsy_sum_g_per_kg, "Total Monkey Ethanol Intake, g per kg"),
                     "monkey_summary_avg_bec_mgpct": (monkey_summary_avg_bec_mgpct, "Average BEC, 22hr"),
                     'monkey_etoh_bouts_drinks_intraday': (monkey_etoh_bouts_drinks_intraday, "Intra-day Ethanol Intake"),
                     'mtd_histogram_general': (monkey_mtd_histogram_general, 'Monkey Histogram'),
                     'bec_histogram_general': (monkey_bec_histogram_general, 'Monkey Histogram'),
                     'monkey_etoh_induction_cumsum': (monkey_etoh_induction_cumsum, 'Monkey Induction Daily Ethanol Intake'),
                     })

