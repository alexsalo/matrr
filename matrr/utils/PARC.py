from collections import defaultdict
from scipy import stats
from scipy.interpolate import spline
from django.db.models import Max, Min, Avg, Sum
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


def monkey_bec_consumption_FirstSixMonthsOA(monkey=None):
    if not isinstance(monkey, Monkey):
        try:
            monkey = Monkey.objects.get(pk=monkey)
        except Monkey.DoesNotExist:
            try:
                monkey = Monkey.objects.get(mky_real_id=monkey)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return False, False

    drinking_experiments = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).first_six_months_oa()
    bec_records = monkey.bec_records.all().first_six_months_oa()
    drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

    if drinking_experiments.count() > 0 and bec_records.count() > 0:
        dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
    else:
        print "No MTDs or no BECs for monkey %s" % str(monkey)
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

    size_min = plotting.DEFAULT_CIRCLE_MIN
    size_scale = plotting.DEFAULT_CIRCLE_MAX - size_min
    cbc = monkey.cohort.cbc
    size_max = cbc.cbc_mtd_etoh_bout_max
    rescaled_volumes = [(vol / size_max) * size_scale + size_min for vol in
                        scatter_size] # rescaled, so that circles will be in range (size_min, size_scale)
    s = bec_con_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)

    y_max = cbc.cbc_mtd_etoh_g_kg_max
    graph_y_max = y_max + y_max * 0.25
    if len(induction_days) and len(induction_days) != len(xaxis):
        # create the shaded area behind induction days
        bec_con_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2,
                              edgecolor='black', zorder=-100)

    bec_con_main_plot.set_ylabel(scatter_y_label)
    bec_con_main_plot.set_title('Monkey %d: from %s to %s' % (
        monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count() - 1]).strftime("%d/%m/%y")),
                                fontsize=title_size)

    bec_con_main_plot.set_ylim(0, 8)
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
        # shades the induction region, if present
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

def create_PARC_graphs(output_path='', png=True, dpi=200):
    figures = list()
    names = list()
    males = (30359, 30354, 30352)
    females = (25064, 25080, 25084)
    for pair in zip(females, males):
        for mky in pair:
            figures.append(monkey_bec_consumption_FirstSixMonthsOA(monkey=mky))
            names.append('monkey_bec_consumption_FirstSixMonthsOA.%d' % mky)
    if png:
        for FigName in zip(figures, names):
            fig, name = FigName
            if png:
                filename = output_path + '%s.png' % name
                fig.savefig(filename, format='png',dpi=dpi)


