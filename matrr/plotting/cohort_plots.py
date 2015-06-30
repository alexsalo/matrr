__author__ = 'farro'
import matplotlib
import numpy as np
from matplotlib import pyplot, cm, gridspec
from matplotlib import pyplot as plt
from django.db.models import Sum, Min, Max, Q
from matplotlib.cm import get_cmap
from matplotlib.ticker import MaxNLocator
import numpy, operator
from scipy.linalg import LinAlgError
from scipy.cluster import vq
from matrr.models import *
from matrr.utils.gadgets import Treemap
from matrr.plotting import specific_callables, plot_tools, DEFAULT_FIG_SIZE, DEFAULT_DPI, HISTOGRAM_FIG_SIZE, RHESUS_COLORS
import matplotlib.patches as mpatches

import matplotlib.patches as mpatches

def cohort_bone_densities(cohort):
    """
    This method will create a cohort graph for bone densities
    """
    if BoneDensity.objects.filter(monkey__cohort=cohort).count():
        return _cohort_bone_densities(cohort)
    else:
        return False, False

def _cohort_bone_densities(cohort):
    """
    Makes a plot of bone densities for cohort
    :param cohort:
    :return: figure
    """
    ld_patch = mpatches.Patch(color='g', label='LD')
    bd_patch = mpatches.Patch(color='b', label='BD')
    hd_patch = mpatches.Patch(color='y', label='HD')
    vhd_patch = mpatches.Patch(color='r', label='VHD')
    control_patch = mpatches.Patch(color='k', label='Control')
    dc_colors = {
        'LD' : 'g',
        'BD' : 'b',
        'HD' : 'y',
        'VHD' : 'r',
        'None' : 'k',
        None : 'k'
    }

    tool_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = tool_figure.add_subplot(111)
    bds = BoneDensity.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort))
    df = pd.DataFrame(list(bds.values_list('monkey__mky_id', 'monkey__mky_drinking_category', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd')), columns=['mky_id', 'dc', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd'])
    df.color = df.dc.apply(lambda x: dc_colors[x])
    ax1.scatter(df.bdy_area, df.bdy_bmc, c=df.color, s=80, alpha=0)
    for label, x, y, col in zip(df.mky_id, df.bdy_area, df.bdy_bmc, df.color):
        ax1.annotate(
            label,
            xy = (x, y), xytext = (20, -7),
            textcoords = 'offset points', ha = 'right', va = 'bottom',
            bbox = dict(boxstyle = 'round,pad=0.5', fc = col, alpha = 0.5))
    ax1.grid()
    ax1.set_xlabel(r'Bone Area $(cm^2)$')
    ax1.set_ylabel('Bone Mineral Content $(g)$')
    ax1.set_title('BMA and BMC for NHP cohort ' + cohort.coh_cohort_name)
    matplotlib.rcParams.update({'font.size': 16})
    for dc in ['LD', 'BD','HD','VHD', 'None']:
        if dc == 'None':
            df2 = df[~df.dc.isin(['LD', 'BD','HD','VHD'])]
        else:
            df2 = df[df.dc == dc]
        if len(df2) > 1:
            fit = np.polyfit(df2.bdy_area, df2.bdy_bmc, 1)
            fit_fn = np.poly1d(fit)
            ax1.plot(df2.bdy_area, fit_fn(df2.bdy_area), dc_colors[dc], lw=2)
    ax1.legend(handles=[ld_patch, bd_patch, hd_patch, vhd_patch, control_patch], loc=4)
    return tool_figure, 'build HTML fragment'

def _cohort_summary_general(specific_callable, x_label, graph_title, legend_labels, cohort):
    """
    This generalized method will create the necropsy summary graph using the parameters passed it.  These parameters
    are used to collect the graph's data and customize the labels/appearance to match that data.

    Args:
    specific_callable: a callable method expected to return a tuple of 3 lists, coh_data_1, coh_data_2, cohort_labels
                       coh_data_N values are used as Y values for horizontal bar graphs in the plot.  The cohort_labels
                       are assumed to be ordered the same as the coh_data_N values.
    x_label: label of the x axis.  As this is a horizontal bar graph, the x axis represents the dependent variable, the
             data value of interest.  The Y axis is treated as the independent variable (monkey name/label)
    graph_title:  Title of the graph
    legend_labels: specific_callable will return 2 datasets.  legend_labels will be the label (in the legend) for these
                   datasets.
    cohort: the subject cohort for which this graph is being made.
    """
    ##  Verify argument is actually a cohort
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.  Using monkey's cohort")
            return False, False

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = fig.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
    ax1.set_axisbelow(True)
    font_dict = {'size': 16}
    ax1.set_title(graph_title, fontdict=font_dict)
    ax1.set_ylabel("Monkey ID", fontdict=font_dict)
    ax1.set_xlabel(x_label, fontdict=font_dict)

    cohort_colors =  ['navy', 'slateblue']

    coh_data_1, coh_data_2, cohort_labels = specific_callable(Monkey.objects.Drinkers().filter(cohort=cohort))

    if not coh_data_1:
        logging.warning("Cohort pk=%d doesn't have any necropsy summary data for this callable" % cohort.pk)
        return False, False

    def autolabel(rects, text_color=None):
        import locale
        locale.setlocale(locale.LC_ALL, '')
        for rect in rects:
            width = rect.get_width()
            xloc = width * .98
            clr = text_color if text_color else "black"
            align = 'right'
            yloc = rect.get_y()+rect.get_height()/2.0

            text_width = locale.format("%.1f", width, grouping=True)
            if width > 0:
                ax1.text(xloc, yloc, text_width, horizontalalignment=align, verticalalignment='center', color=clr, weight='bold')

    idx = numpy.arange(len(coh_data_1))
    width = 0.4

    cohort_bar1 = ax1.barh(idx, coh_data_1, width, color=cohort_colors[0])
    autolabel(cohort_bar1, 'white')
    if all(coh_data_2):
        cohort_bar2 = ax1.barh(idx+width, coh_data_2, width, color=cohort_colors[1])
        autolabel(cohort_bar2, 'white')
        ax1.legend( (cohort_bar2[0], cohort_bar1[0]), legend_labels, loc=2)
    else:
        ax1.legend( (cohort_bar1[0], ), legend_labels, loc=2)

    ax1.set_yticks(idx+width)
    ax1.set_yticklabels(cohort_labels)
    return fig, 'map'

def cohort_necropsy_avg_22hr_g_per_kg(cohort):
    """
    This method will create a cohort graph (horizontal bar graph) showing each monkey's average open access etoh intake
    in g/kg.
    """
    if NecropsySummary.objects.filter(monkey__cohort=cohort).count():
        graph_title = 'Average Daily EtOH Intake (22hr open access)'
        x_label = "Average Daily Ethanol Intake (g/kg)"
        legend_labels = ('6 Month Average', '12 Month Average')
        return _cohort_summary_general(specific_callables.necropsy_summary_avg_22hr_g_per_kg, x_label, graph_title, legend_labels, cohort)
    else:
        return False, False

def cohort_necropsy_etoh_4pct(cohort):
    """
    This method will create a cohort graph (horizontal bar graph) showing each monkey's open access and lifetime ethanol
     intake, in ml.
    """
    if NecropsySummary.objects.filter(monkey__cohort=cohort).count():
        graph_title = "Total EtOH Intake (mL)"
        x_label = "Ethanol intake (4% w/v)"
        legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)')
        return _cohort_summary_general(specific_callables.necropsy_summary_etoh_4pct, x_label, graph_title, legend_labels, cohort)
    else:
        return False, False

def cohort_necropsy_sum_g_per_kg(cohort):
    """
    This method will create a cohort graph (horizontal bar graph) showing each monkey's total etoh intake during lifetime
    and open access, in g/kg.
    """
    if NecropsySummary.objects.filter(monkey__cohort=cohort).count():
        graph_title = 'Total EtOH Intake (g/kg)'
        x_label = "Ethanol Intake (g/kg)"
        legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)')
        return _cohort_summary_general(specific_callables.necropsy_summary_sum_g_per_kg, x_label, graph_title, legend_labels, cohort)
    else:
        return False, False

def cohort_summary_avg_bec_mgpct(cohort):
    """
    This method will create a cohort graph (horizontal bar graph) showing each monkey's average open access bec values
    """
    if MonkeyBEC.objects.filter(monkey__cohort=cohort).count():
        graph_title = 'Average Blood Ethanol Concentration (22hr open access)'
        x_label = "Average BEC (mg percent)"
        legend_labels = ('12 Month Average', '6 Month Average')
        return _cohort_summary_general(specific_callables.summary_avg_bec_mgpct, x_label, graph_title, legend_labels, cohort)
    else:
        return False, False

def _cohort_tools_boxplot(data, title, x_label, y_label, scale_x=(), scale_y=()):
    tool_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = tool_figure.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    ax1.set_axisbelow(True)
    ax1.set_title(title)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)

    if scale_x:
        ax1.set_xlim(scale_x)
    if scale_y:
        ax1.set_ylim(scale_y)

    sorted_keys = [item[0] for item in sorted(data.items())]
    sorted_values = [item[1] for item in sorted(data.items())]
    scatter_y = []
    scatter_x = []
    for index, dataset in enumerate(sorted_values):
        for data in dataset:
            scatter_x.append(index+1)
            scatter_y.append(data)

    ax1.scatter(scatter_x, scatter_y, marker='+', color='purple', s=80)
    bp = ax1.boxplot(sorted_values)
    pyplot.setp(bp['boxes'], linewidth=3, color='black')
    pyplot.setp(bp['whiskers'], linewidth=3, color='black')
    pyplot.setp(bp['fliers'], color='red', marker='o', markersize=10)
    xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
    pyplot.setp(xtickNames, rotation=45)
    return tool_figure

def cohort_protein_boxplot(cohort=None, protein=None):
#	from matrr.models import Cohort, Protein, MonkeyProtein
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    if not isinstance(protein, Protein):
        try:
            protein = Protein.objects.get(pk=protein)
        except Protein.DoesNotExist:
            print("That's not a valid protein.")
            return False, False

    monkey_proteins = MonkeyProtein.objects.filter(monkey__in=cohort.monkey_set.all(), protein=protein).order_by('mpn_date')
    if monkey_proteins.count() > 0:
        title = '%s : %s' % (str(cohort), str(protein))
        x_label = "Date of sample"
        y_label = "Sample Value, in %s" % str(protein.pro_units)
        dates = monkey_proteins.values_list('mpn_date', flat=True)
        data = dict()
        for date in dates:
            data[str(date.date())] = monkey_proteins.filter(mpn_date=date).values_list('mpn_value')
        fig = _cohort_tools_boxplot(data, title, x_label, y_label)
        return fig, False

    else:
        msg = "No MonkeyProteins for cohort %s, pk=%d." % (str(cohort), cohort.pk)
        logging.warning(msg)
        return False, False

def cohort_hormone_boxplot(cohort=None, hormone="", scaled=False):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            msg = "That's not a valid cohort: %s" % str(cohort)
            logging.warning(msg)
            return False, False
    hormone_field_names = [f.name for f in MonkeyHormone._meta.fields]
    if not hormone in hormone_field_names:
        msg = "That's not a MonkeyHormone field name: %s." % hormone
        logging.warning(msg)
        return False, False

    cohort_hormones = MonkeyHormone.objects.filter(monkey__in=cohort.monkey_set.all()).order_by('mhm_date')
    cohort_hormones = cohort_hormones.exclude(Q(**{hormone: None}))
    if cohort_hormones.count() > 0:
        title = '%s : %s' % (str(cohort), hormone)
        x_label = "Date of sample"
        y_label = "Hormone Value, %s" % MonkeyHormone.UNITS[hormone]
        dates = cohort_hormones.values_list('mhm_date', flat=True)
        data = dict()
        for date in dates:
            data[str(date.date())] = cohort_hormones.filter(mhm_date=date).values_list(hormone)

        scale_y = ()
        if scaled:
            min_field = "cbc_%s_min" % hormone
            max_field = "cbc_%s_max" % hormone
            cbcs = CohortMetaData.objects.exclude(Q(**{min_field: None})).exclude(Q(**{max_field: None}))
            cbc_scales = cbcs.aggregate(Min(min_field), Max(max_field))
            scale_y = (cbc_scales[min_field+"__min"], cbc_scales[max_field+'__max'])
        fig = _cohort_tools_boxplot(data, title, x_label, y_label, scale_y=scale_y)
        return fig, False

    else:
        msg = "No MonkeyHormones for cohort %s, pk=%d." % (str(cohort), cohort.pk)
        logging.warning(msg)
        return False, False

def cohort_etoh_bihourly_treemap(cohort, from_date=None, to_date=None, dex_type=''):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    size_cache = {}
    def size(thing):
        """sum size of child nodes"""
        if isinstance(thing, dict):
            thing = thing['volume']
        if isinstance(thing, int) or isinstance(thing, float):
            return thing
        if thing in size_cache:
            return size_cache[thing]
        else:
            size_cache[thing] = reduce(operator.add, [size(x) for x in thing])
            return size_cache[thing]

    max_color = 0
    cmap = cm.Greens
    def color_by_pct_of_max_color(color):
        try:
            pct_of_max = 1. * color / max_color
            return cmap(pct_of_max)
        except TypeError:
            return 'white'

    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    cohort_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=monkeys)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        cohort_mtds = cohort_mtds.filter(drinking_experiment__dex_date__gte=from_date)
    if to_date:
        cohort_mtds = cohort_mtds.filter(drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        cohort_mtds = cohort_mtds.filter(drinking_experiment__dex_type=dex_type)
    cohort_bouts = ExperimentBout.objects.filter(mtd__in=cohort_mtds)

    if not cohort_mtds.count() or not cohort_bouts.count():
        return False, False

    monkey_pks = []
    hour_const = 0
    experiment_len = 22
    block_len = 2
    tree = list()
    color_tree = list()
    for monkey in monkeys:
        monkey_pks.append(str(monkey.pk))
        monkey_mtds = cohort_mtds.filter(monkey=monkey)
        num_days = monkey_mtds.order_by().values_list('drinking_experiment__dex_date').distinct().count()

        monkey_bar = list()
        color_monkey_bar = list()
        for hour_start in range(hour_const,hour_const + experiment_len, block_len ):
            hour_end = hour_start + block_len
            fraction_start = (hour_start-hour_const)*60*60
            fraction_end = (hour_end-hour_const)*60*60

            bouts_in_fraction = cohort_bouts.filter(mtd__in=monkey_mtds, ebt_start_time__gte=fraction_start, ebt_start_time__lte=fraction_end)
            mtds_in_fraction = MonkeyToDrinkingExperiment.objects.filter(mtd_id__in=bouts_in_fraction.values_list('mtd', flat=True).distinct())
            volume_sum = bouts_in_fraction.aggregate(Sum('ebt_volume'))['ebt_volume__sum']

            field_name = 'mtd_pct_max_bout_vol_total_etoh_hour_%d' % (hour_start/2)
            max_bout_pct_total = mtds_in_fraction.exclude(**{field_name:None}).values_list(field_name, flat=True)

            if max_bout_pct_total:
                max_bout_pct_total = numpy.array(max_bout_pct_total)
                avg_max_bout_pct_total = numpy.mean(max_bout_pct_total)
            else:
                avg_max_bout_pct_total = 0

            if not volume_sum:
                volume_sum = 0.1
            if not avg_max_bout_pct_total:
                avg_max_bout_pct_total = 0.01

            if (num_days * block_len) == 0:
                avg_vol_per_hour = 0.01
            else:
                avg_vol_per_hour = volume_sum / float(num_days * block_len)

            monkey_bar.append(avg_vol_per_hour)
            color_monkey_bar.append(avg_max_bout_pct_total)
            max_color = max(max_color, avg_max_bout_pct_total)
        tree.append(tuple(monkey_bar))
        color_tree.append(tuple(color_monkey_bar))
    tree = tuple(tree)
    color_tree = tuple(color_tree)

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    left, width = 0.02, 0.73
    bottom, height = 0.05, .85
    left_h = left+width+0.07
    ax_dims = [left, bottom, width, height]

    ax = fig.add_axes(ax_dims)
    ax.set_aspect('equal')
    ax.set_yticks([])

    Treemap(ax, tree, color_tree, size, color_by_pct_of_max_color, x_labels=monkey_pks)

    graph_title = "Bi-hourly distribution of Ethanol Intake"
    if dex_type:
        graph_title +=  " during %s" % dex_type
    elif from_date and to_date:
        graph_title +=  "\nfrom %s, to %s" % (str(from_date.date()), str(to_date.date()))
    elif from_date:
        graph_title +=  " after %s" % str(from_date)
    elif to_date:
        graph_title +=  " before %s" % str(to_date)
    ax.set_title(graph_title)

    ## Custom Colorbar
    color_ax = fig.add_axes([left_h, bottom, 0.08, height])
    m = numpy.outer(numpy.arange(0,1,0.01),numpy.ones(10))
    color_ax.imshow(m, cmap=cmap, origin="lower")
    color_ax.set_xticks(numpy.arange(0))
    labels = [str(int((max_color*100./4)*i))+'%' for i in range(5)]
    color_ax.set_yticks(numpy.arange(0,101,25), labels)
    color_ax.set_title("Average maximum bout,\nby ethanol intake,\nexpressed as percentage \nof total daily intake\n")

    return fig, 'has_caption'

def cohort_etoh_induction_cumsum(cohort, stage=1):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    stages = dict()
    stages[0] = Q(eev_dose__lte=1.5)
    stages[1] = Q(eev_dose=.5)
    stages[2] = Q(eev_dose=1)
    stages[3] = Q(eev_dose=1.5)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
    main_gs = gridspec.GridSpec(monkeys.count(), 40)
    main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.01*monkeys.count()) # sharing xaxis

    stage_plot = fig.add_subplot(main_gs[0:1,2:41])
    stage_text = "Stage %d" % stage if stage else "Induction"
    stage_plot.set_title("%s Cumulative Intraday EtOH Intake for %s" % (stage_text, str(cohort)))
    for index, monkey in enumerate(monkeys):
        if index:
            stage_plot = fig.add_subplot(main_gs[index:index+1,2:41], sharex=stage_plot, sharey=stage_plot) # sharing xaxis
        eevs = ExperimentEvent.objects.filter(monkey=monkey, dex_type='Induction').exclude(eev_etoh_volume=None).order_by('eev_occurred')
        stage_x = eevs.filter(stages[stage])
        plot_tools._days_cumsum_etoh(stage_x, stage_plot)
        stage_plot.get_xaxis().set_visible(False)
        stage_plot.legend((), title=str(monkey), loc=1, frameon=False, prop={'size':12})

#	ylims = stage_plot.get_ylim()
    stage_plot.set_ylim(ymin=0, )#ymax=ylims[1]*1.05)
    stage_plot.yaxis.set_major_locator(MaxNLocator(3, prune='lower'))
    stage_plot.set_xlim(xmin=0)

    # yxes label
    ylabel = fig.add_subplot(main_gs[:,0:2])
    ylabel.set_axis_off()
    ylabel.set_xlim(0, 1)
    ylabel.set_ylim(0, 1)
    ylabel.text(.05, 0.5, "Cumulative EtOH intake, ml", rotation='vertical', horizontalalignment='center', verticalalignment='center')
    return fig, True

def cohort_etoh_gkg_quadbar(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    fig.suptitle(str(cohort), size=18)
    main_gs = gridspec.GridSpec(2, 2)
    main_gs.update(left=0.08, right=.98, top=.92, bottom=.06, wspace=.02, hspace=.23)

    cohort_colors =  ['navy', 'slateblue']
    main_plot = None # this is so the first subplot has a sharey.  all subplots after the first will use the previous loop's subplot
    subplots = [(i, j) for i in range(2) for j in range(2)]
    for gkg, _sub in enumerate(subplots, 1):
        main_plot = fig.add_subplot(main_gs[_sub], sharey=main_plot)
        main_plot.set_title("Greater than %d g per kg Etoh" % gkg)

        monkeys = Monkey.objects.Drinkers().filter(cohort=cohort).values_list('pk', flat=True)
        data = list()
        colors = list()
        for i, mky in enumerate(monkeys):
            colors.append(cohort_colors[i%2]) # we don't want the colors sorted.  It breaks if you try anyway.
            mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, mtd_etoh_g_kg__gte=gkg).count()
            mtds = mtds if mtds else .001
            data.append((mky, mtds))

        sorted_data = sorted(data, key=lambda t: t[1]) # sort the data by the 2nd tuple value (mtds).  This is important to keep yvalue-monkey matching
        sorted_data = numpy.array(sorted_data)
        yaxis = sorted_data[:,1] # slice off the yaxis values
        main_plot.bar(range(len(monkeys)), yaxis, width=.9, color=colors)

        labels = sorted_data[:,0] # slice off the labels
        x_labels = ["%d" % l for l in labels] # this ensures that the monkey label is "10023" and not "10023.0" -.-
        main_plot.set_xticks(range(len(monkeys))) # this will force a tick for every monkey.  without this, labels become useless
        xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
        pyplot.setp(xtickNames, rotation=45)

        # this hides the yticklabels and ylabel for the right plots
        if gkg % 2:
            main_plot.set_ylabel("Day count")
        else:
            main_plot.get_yaxis().set_visible(False)
    return fig, True

def cohort_bec_firstbout_monkeycluster(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, cluster_count=1):
    """
        Scatter plot for monkey
            x axis - first bout / total intake
            y axis - BEC
            color - Monkey
    """
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

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
        dates = list(bec_records.dates('bec_collect_date', 'day').order_by('bec_collect_date'))
    else:
        return False, False

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = fig.add_subplot(111)


    mkys = bec_records.order_by().values_list('monkey__pk', flat=True).distinct()
    mky_count = float(mkys.count())

    cmap = get_cmap('jet')
    mky_color = dict()
    for idx, key in enumerate(mkys):
        mky_color[key] = cmap(idx / (mky_count -1))

    mky_datas = list()
    centeroids = list()
    for mky in mkys:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, drinking_experiment__dex_date__in=dates)
        mtds = mtds.exclude(bec_record=None).order_by('drinking_experiment__dex_date')
        xaxis = mtds.values_list('mtd_pct_etoh_in_1st_bout', flat=True)
        yaxis = mtds.values_list('bec_record__bec_mg_pct', flat=True)
        color = mky_color[mky]

        ax1.scatter(xaxis, yaxis, c=color, s=40, alpha=.1, edgecolor=color)
        try:
            res, idx = vq.kmeans2(numpy.array(zip(xaxis, yaxis)), cluster_count)
            ax1.scatter(res[:,0],res[:,1], marker='o', s=100, linewidths=3, c=color, edgecolor=color)
            ax1.scatter(res[:,0],res[:,1], marker='x', s=300, linewidths=3, c=color)
            centeroids.append([res[:,0][0], res[:,1][0]])
        except LinAlgError: # I'm not sure what about kmeans2() causes this, or how to avoid it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass
        except ValueError: # "Input has 0 items" has occurred
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass

        mky_datas.append((mky, zip(xaxis, yaxis), color))

    def create_convex_hull_polygon(cluster, color, label):
        from matrr.utils.gadgets import convex_hull
        from matplotlib.path import Path
        try:
            hull = convex_hull(numpy.array(cluster).transpose())
        except AssertionError: # usually means < 5 datapoints
            return
        path = Path(hull)
        x, y = zip(*path.vertices)
        x = list(x)
        x.append(x[0])
        y = list(y)
        y.append(y[0])
        line = ax1.plot(x, y, c=color, linewidth=3, label=label)
        return line

    for mky, data, color in mky_datas:
        create_convex_hull_polygon(data, color, `mky`)

    title = 'Cohort %s ' % cohort.coh_cohort_name
    if sample_before:
        title += "before %s " % str(sample_before)
    if sample_after:
        title += "after %s " % str(sample_after)

    ax1.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    ax1.text(0, 82, "80 mg pct")
    ax1.set_title(title)
    ax1.set_xlabel("First bout / total intake")
    ax1.set_ylabel("Blood Ethanol Concentration, mg %")
    ax1.legend(loc="upper left")
    ax1.set_xlim(0)
    ax1.set_ylim(0)

    zipped = numpy.vstack(centeroids)
    coordinates = ax1.transData.transform(zipped)
    xcoords, inv_ycoords = zip(*coordinates)
    ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
    datapoint_map = zip(mkys, xcoords, ycoords)
    return fig, datapoint_map

def cohort_bec_monthly_centroid_distance_general(cohort, mtd_x_axis, mtd_y_axis, title, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    """
    """
    def add_1_month(date):
        new_month = date.month + 1
        if new_month > 12:
            return datetime(date.year+1, 1, date.day)
        else:
            return datetime(date.year, new_month, date.day)
    def euclid_dist(point_a, point_b):
        import math
        if not any(point_a) or not any(point_b):
            return 0
        return math.hypot(point_b[0]-point_a[0], point_b[1]-point_a[1])

    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

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
        bar_x_labels = [_date.strftime('%h %Y') for _date in dates]
        bar_x = numpy.arange(0, len(dates)-1)
    else:
        return False, False

    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    cmap = get_cmap('jet')
    month_count = float(len(dates))
    month_color = dict()
    for idx, key in enumerate(dates):
        month_color[key] = cmap(idx / (month_count-1))

    mky_datas = dict()
    for mky in monkeys:
        bar_y = list()
        colors = list()
        for _date in dates:
            min_date = _date
            max_date = add_1_month(_date)
            color = month_color[_date]

            cohort_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort,
                                                                    drinking_experiment__dex_date__gte=min_date,
                                                                    drinking_experiment__dex_date__lt=max_date)
            cohort_mtds = cohort_mtds.exclude(bec_record= None).exclude(bec_record__bec_mg_pct = None).exclude(bec_record__bec_mg_pct = 0)
            month_data = list()
            if cohort_mtds.filter(monkey=mky):
                month_data.append(cohort_mtds.filter(monkey=mky))
                month_data.append(cohort_mtds.exclude(monkey=mky))
            if not month_data:
                # still need values stored for this monkey-month if there is no data
                bar_y.append(0)
                colors.append(color)
            else:
                coh_center = (0,0)
                mky_center = (0,0)
                for index, mtd_set in enumerate(month_data): # mtd_set[0] == monkey, mtd_set[1] == cohort
                    _xaxis = numpy.array(mtd_set.values_list(mtd_x_axis, flat=True))
                    _yaxis = mtd_set.values_list(mtd_y_axis, flat=True)

                    try:
                        res, idx = vq.kmeans2(numpy.array(zip(_xaxis, _yaxis)), 1)
                    except Exception as e:
                        # keep default coh/mky center as (0,0)
                        if not index: # if it's a monkey center
                            colors.append(color) # stash the color for later
                    else:
                        if index:
                            coh_center = [res[:,0][0], res[:,1][0]]
                        else:
                            mky_center = [res[:,0][0], res[:,1][0]]
                            colors.append(color)
                bar_y.append(euclid_dist(mky_center, coh_center))
        mky_datas[mky] = (bar_y, colors)


    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(monkeys.count(), 40)
    main_gs.update(left=0.03, right=0.98, wspace=0, hspace=.1) # sharing xaxis

    ax_index = 0
    ax = None
    for mky, data in mky_datas.items():
        ax = fig.add_subplot(main_gs[ax_index:ax_index+1, 3:], sharex=ax, sharey=ax)
        if ax_index == 0:
            ax.set_title(title)
        ax.legend((), title=str(mky.pk), loc=1, frameon=False, prop={'size':12})
        ax_index += 1
        bar_y, colors = data
        for _x, _y, _c in zip(bar_x, bar_y, colors):
            # this forloop, while appearing stupid, works out well when there is missing data between monkeys in the cohort.
            ax.bar(_x, _y, color=_c, edgecolor='none')
            ax.get_xaxis().set_visible(False)


    ax.get_xaxis().set_visible(True)
    ax.set_xticks(bar_x)
    ax.set_xticklabels(bar_x_labels, rotation=45)
    ax.yaxis.set_major_locator(MaxNLocator(2, prune='lower'))

    # yxes label
    ylabel = fig.add_subplot(main_gs[:,0:2])
    ylabel.set_axis_off()
    ylabel.set_xlim(0, 1)
    ylabel.set_ylim(0, 1)
    ylabel.text(.05, 0.5, "Euclidean distance between k-means centroids", rotation='vertical', horizontalalignment='center', verticalalignment='center')

    return fig, True

def cohort_bec_mcd_sessionVSbec(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    title = 'Euclidean monkey-cohort k-means centroids distance, etoh volume vs bec, by month'
    if sample_before:
        title += ", before %s" % str(sample_before)
    if sample_after:
        title += ", after %s" % str(sample_after)

    return cohort_bec_monthly_centroid_distance_general(cohort, 'bec_record__bec_vol_etoh', 'bec_record__bec_mg_pct', title,
                                                        from_date, to_date, dex_type, sample_before, sample_after)

def cohort_bec_mcd_beta(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    title = 'Euclidean monkey-cohort k-means centroids distance, median ibi vs bec, by month'
    if sample_before:
        title += ", before %s" % str(sample_before)
    if sample_after:
        title += ", after %s" % str(sample_after)
    return cohort_bec_monthly_centroid_distance_general(cohort, 'mtd_etoh_media_ibi', 'bec_record__bec_mg_pct', title,
                                                        from_date, to_date, dex_type, sample_before, sample_after)


def _cohort_etoh_max_bout_cumsum(cohort, subplot):
    mkys = Monkey.objects.Drinkers().filter(cohort=cohort).values_list('pk', flat=True)

    subplot.set_title("Induction St. 3 Cumulative Max Bout EtOH Intake for %s" % str(cohort))
    subplot.set_ylabel("Volume EtOH / Monkey Weight, mL./kg")

    mky_colors = dict()
    mky_ymax = dict()
    for idx, m in enumerate(mkys):
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m, drinking_experiment__dex_type="Induction").exclude(
            mtd_max_bout_vol=None).order_by('drinking_experiment__dex_date')
        mtds = mtds.filter(mtd_etoh_g_kg__gte=1.4).filter(mtd_etoh_g_kg__lte=1.6)
        if not mtds.count():
            continue
        mky_colors[m] = RHESUS_COLORS[m.mky_drinking_category]
        volumes = numpy.array(mtds.values_list('mtd_max_bout_vol', flat=True))
        weights = numpy.array(mtds.values_list('mtd_weight', flat=True))
        vw_div = volumes / weights
        yaxis = numpy.cumsum(vw_div)
        mky_ymax[m] = yaxis[-1]
        xaxis = numpy.array(mtds.values_list('drinking_experiment__dex_date', flat=True))
        subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=mky_colors[m], label=str(m))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    legend = subplot.legend(loc=2)
    pyplot.setp(legend.legendHandles, lw=15)
    if not len(mky_ymax.values()):
        raise Exception("no MTDs found")
    return subplot, mky_ymax, mky_colors

def _cohort_etoh_horibar_ltgkg(cohort, subplot, mky_ymax, mky_colors):
    subplot.set_title("Lifetime EtOH Intake for %s" % str(cohort))
    subplot.set_xlabel("EtOH Intake, g/kg")

    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        etoh_sum = mtds.aggregate(Sum('mtd_etoh_g_kg'))['mtd_etoh_g_kg__sum']
        bar_widths.append(etoh_sum)
        bar_colors.append(mky_colors[mky])
        if len(bar_y):
            highest_bar = bar_y[len(bar_y) - 1] + bar_height
        else:
            highest_bar = 0 + bar_height
        if ymax > highest_bar:
            bar_y.append(ymax)
        else:
            bar_y.append(highest_bar)
    subplot.barh(bar_y, bar_widths, height=bar_height, color=bar_colors)
    subplot.set_yticks([])
    subplot.xaxis.set_major_locator(MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot

def _cohort_etoh_horibar_3gkg(cohort, subplot, mky_ymax, mky_colors):
    subplot.set_title("# days over 3 g/kg")

    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_3widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        bar_3widths.append(mtds.filter(mtd_etoh_g_kg__gt=3).count())
        bar_colors.append(mky_colors[mky])
        if len(bar_y):
            highest_bar = bar_y[len(bar_y) - 1] + bar_height
        else:
            highest_bar = 0 + bar_height
        if ymax > highest_bar:
            bar_y.append(ymax)
        else:
            bar_y.append(highest_bar)
    subplot.barh(bar_y, bar_3widths, height=bar_height, color=bar_colors)
    subplot.set_yticks([])
    subplot.xaxis.set_major_locator(MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot

def _cohort_etoh_horibar_4gkg(cohort, subplot, mky_ymax, mky_colors):
    subplot.set_title("# days over 4 g/kg")
    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))
    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_4widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        bar_4widths.append(mtds.filter(mtd_etoh_g_kg__gt=4).count())
        bar_colors.append(mky_colors[mky])
        if len(bar_y):
            highest_bar = bar_y[len(bar_y) - 1] + bar_height
        else:
            highest_bar = 0 + bar_height
        if ymax > highest_bar:
            bar_y.append(ymax)
        else:
            bar_y.append(highest_bar)
    subplot.barh(bar_y, bar_4widths, height=bar_height, color=bar_colors)
    subplot.set_yticks([])
    subplot.xaxis.set_major_locator(MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot

def cohort_etoh_max_bout_cumsum_horibar_3gkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except Exception as e:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_3gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, 'build HTML fragment'

def cohort_etoh_max_bout_cumsum_horibar_4gkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except Exception as e:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_4gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, 'build HTML fragment'

def cohort_etoh_max_bout_cumsum_horibar_ltgkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except Exception as e:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_ltgkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, 'build HTML fragment'

# Dictionary of ethanol cohort plots VIPs can customize
COHORT_ETOH_TOOLS_PLOTS = {"cohort_etoh_bihourly_treemap": (cohort_etoh_bihourly_treemap, "Cohort Bihourly Drinking Pattern"),}
# BEC plots
COHORT_BEC_TOOLS_PLOTS = {'cohort_bec_firstbout_monkeycluster': (cohort_bec_firstbout_monkeycluster, 'Monkey BEC vs First Bout'),}
# Dictionary of protein cohort plots VIPs can customize
COHORT_PROTEIN_TOOLS_PLOTS = {"cohort_protein_boxplot": (cohort_protein_boxplot, "Cohort Protein Boxplot")}
# Dictionary of hormone cohort plots VIPs can customize
COHORT_HORMONE_TOOLS_PLOTS = {"cohort_hormone_boxplot": (cohort_hormone_boxplot, "Cohort Hormone Boxplot")}

# Dictionary of Monkey Tools' plots
COHORT_TOOLS_PLOTS = dict()
COHORT_TOOLS_PLOTS.update(COHORT_ETOH_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_BEC_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_PROTEIN_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_HORMONE_TOOLS_PLOTS)

# Dictionary of all cohort plots
COHORT_PLOTS = {}
COHORT_PLOTS.update(COHORT_TOOLS_PLOTS)
COHORT_PLOTS.update({"cohort_necropsy_avg_22hr_g_per_kg": (cohort_necropsy_avg_22hr_g_per_kg, 'Average Ethanol Intake, 22hr'),
                     "cohort_necropsy_etoh_4pct": (cohort_necropsy_etoh_4pct, "Total Ethanol Intake, ml"),
                     "cohort_necropsy_sum_g_per_kg": (cohort_necropsy_sum_g_per_kg, "Total Ethanol Intake, g per kg"),
                     "cohort_summary_avg_bec_mgpct": (cohort_summary_avg_bec_mgpct, "Average BEC, 22hr"),
                     'cohort_etoh_induction_cumsum': (cohort_etoh_induction_cumsum, 'Cohort Induction Daily Ethanol Intake'),
                     'cohort_etoh_max_bout_cumsum_horibar_ltgkg': (cohort_etoh_max_bout_cumsum_horibar_ltgkg, "Cohort Cumulative Daily Max Bout, Lifetime EtOH Intake"),
                     'cohort_etoh_max_bout_cumsum_horibar_3gkg': (cohort_etoh_max_bout_cumsum_horibar_3gkg, "Cohort Cumulative Daily Max Bout, Day count over 3 g per kg"),
                     'cohort_etoh_max_bout_cumsum_horibar_4gkg': (cohort_etoh_max_bout_cumsum_horibar_4gkg, "Cohort Cumulative Daily Max Bout, Day count over 4 g per kg"),
                     'cohort_etoh_gkg_quadbar': (cohort_etoh_gkg_quadbar, "Cohort Daily Ethanol Intake Counts"),
                     "cohort_bone_densities": (cohort_bone_densities, 'Bone Area and Content Trends by DC '),
})
