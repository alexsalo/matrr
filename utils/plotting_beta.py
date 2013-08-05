import copy
from django.db.models import Sum
import itertools
import numpy
from matplotlib import pyplot, gridspec, ticker, cm, patches
from scipy import cluster, stats
import operator
from numpy.linalg import LinAlgError
from matrr.models import *
from utils import plotting, apriori
from collections import defaultdict
import networkx as nx


def create_convex_hull_polygon(subplot, xvalues, yvalues, color):
    from matrr.helper import convex_hull
    from matplotlib.path import Path

    try:
        hull = convex_hull(numpy.array(zip(xvalues, yvalues)).transpose())
    except AssertionError: # usually means < 5 datapoints
        return
    path = Path(hull)
    x, y = zip(*path.vertices)
    x = list(x)
    x.append(x[0])
    y = list(y)
    y.append(y[0])
    line = subplot.plot(x, y, c=color, linewidth=3, alpha=.3)
    return line


_1_hour = 60 * 60
_2_hour = 2 * _1_hour
_6_hour = 6 * _1_hour # time before lights out
_12_hour = 12 * _1_hour # duration of lights out
_22_hour = 22 * _1_hour # duration of drinking day
_24_hour = 24 * _1_hour # full day

session_start = 0
session_end = session_start + _22_hour
lights_out = session_start + _6_hour
lights_on = lights_out + _12_hour
diff = session_end - lights_on


def cohorts_daytime_bouts_histogram():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

    main_plot = None
    for cohort in cohorts:
        fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        main_gs = gridspec.GridSpec(3, 40)
        main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
        main_plot = fig.add_subplot(main_gs[:, :], sharey=main_plot)
        main_plot.set_title(cohort.coh_cohort_name + " Open Access Only")
        main_plot.set_xlabel("Seconds of day, binned by hour")
        main_plot.set_ylabel("Total bout count during hour")
        x_axis = list()
        y_axes = list()
        labels = list()
        index = 0
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
            bout_starts = bouts.values_list('ebt_start_time', flat=True)
            bout_starts = numpy.array(bout_starts)
            y_axes.append(bout_starts)
            x_axis.append(index)
            labels.append(str(monkey.pk))
            index += 1
        bin_edges = range(0, _22_hour, _1_hour)
        n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
        main_plot.axvspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
        main_plot.legend(ncol=5, loc=9)
        main_plot.set_ylim(ymax=1600)


def cohorts_daytime_volbouts_bargraph():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

    width = 1
    main_plot = None
    for cohort in cohorts:
        index = 0
        night_time = list()
        labels = set()
        fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        main_gs = gridspec.GridSpec(3, 40)
        main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
        main_plot = fig.add_subplot(main_gs[:, 1:], sharey=main_plot)
        main_plot.set_title(cohort.coh_cohort_name + " Open Access Only")
        main_plot.set_xlabel("Hour of day")
        main_plot.set_ylabel("Total vol etoh consumed during hour")

        monkeys = cohort.monkey_set.exclude(mky_drinking=False)
        mky_count = float(monkeys.count())
        cmap = cm.get_cmap('jet')
        mky_color = list()
        for idx, key in enumerate(monkeys):
            mky_color.append(cmap(idx / (mky_count - 1)))
        for start_time in range(0, _22_hour, _1_hour):
            x_axis = list()
            y_axis = list()
            if start_time >= lights_out and start_time <= lights_on:
                night_time.append(index)
            for monkey in monkeys:
                bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time,
                                                           ebt_start_time__lt=start_time + _1_hour)
                bout_vols = bouts.values_list('ebt_volume', flat=True)
                bouts_sum = numpy.array(bout_vols).sum()
                #			bout_starts = bout_starts - diff
                y_axis.append(bouts_sum)
                x_axis.append(index)
                index += 1
                labels.add(str(monkey.pk))
            rects1 = main_plot.bar(x_axis, y_axis, width, color=mky_color, alpha=.7)
            index += 2
        main_plot.legend(rects1, labels, ncol=5, loc=9)
        main_plot.axvspan(min(night_time), max(night_time), color='black', alpha=.2, zorder=-100)
        x_labels = ['hr %d' % i for i in range(1, 23)]
        main_plot.set_xlim(xmax=index - 2)
        main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
        xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
        pyplot.setp(xtickNames, rotation=45)
        main_plot.set_ylim(ymax=100000)


def cohorts_daytime_bouts_boxplot():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])

    x_axis = list()
    y_axes = list()
    labels = list()
    index = 0
    for cohort in cohorts:
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
            bout_starts = bouts.values_list('ebt_start_time', flat=True)
            bout_starts = numpy.array(bout_starts)
            y_axes.append(bout_starts)
            x_axis.append(index)
            labels.append(str(monkey.pk))
            index += 1
        index += 3

    bp = main_plot.boxplot(y_axes, positions=x_axis, whis=2, sym='.')
    main_plot.axvspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)

    xtickNames = pyplot.setp(main_plot, xticklabels=labels)
    pyplot.setp(xtickNames, rotation=45)
    return fig, False


def cohorts_daytime_bouts_boxplot_remix():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    #	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    #	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])

    x_axis = list()
    y_axes = list()
    labels = list()
    index = 0
    for cohort in cohorts:
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
            night_bouts = bouts.filter(ebt_start_time__gte=lights_out).filter(ebt_start_time__lt=lights_on).values_list(
                'ebt_start_time', flat=True)
            day_bouts = bouts.filter(ebt_start_time__gte=lights_on) | bouts.filter(ebt_start_time__lt=lights_out)
            day_bouts = day_bouts.values_list('ebt_start_time', flat=True)
            new_bouts = list(night_bouts)
            for v in day_bouts:
                if v >= lights_on:
                    new_v = v - _24_hour
                    new_bouts.append(new_v)
                else:
                    new_bouts.append(v)
                #			new_bouts.extend(new_bouts)
            y_axes.append(new_bouts)
            x_axis.append(index)
            labels.append(str(monkey.pk))
            index += 1
        index += 3

    bp = main_plot.boxplot(y_axes, positions=x_axis, whis=1.5, sym='.')
    main_plot.axhspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)

    xtickNames = pyplot.setp(main_plot, xticklabels=labels)
    pyplot.setp(xtickNames, rotation=45)
    return fig, False


def cohorts_daytime_bouts_boxplot_doubleremix():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    #	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    #	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])

    x_axis = list()
    before_end = list()
    after_start = list()
    night_y = list()
    labels = list()
    index = 0
    for cohort in cohorts:
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
            night_bouts = bouts.filter(ebt_start_time__gte=lights_out).filter(ebt_start_time__lt=lights_on).values_list(
                'ebt_start_time', flat=True)
            day_bouts = bouts.filter(ebt_start_time__gte=lights_on) | bouts.filter(ebt_start_time__lt=lights_out)
            day_bouts = day_bouts.values_list('ebt_start_time', flat=True)

            b4_end = list()
            _after_start = list()
            for v in day_bouts:
                if v >= lights_on:
                    new_v = v - _24_hour
                    b4_end.append(new_v)
                else:
                    _after_start.append(v)

            night_y.append(night_bouts)
            before_end.append(b4_end)
            after_start.append(_after_start)
            x_axis.append(index)
            labels.append(str(monkey.pk))
            index += 1
        index += 3

    bp = main_plot.boxplot(before_end, positions=x_axis, whis=1.5, sym='.')
    bp = main_plot.boxplot(after_start, positions=x_axis, whis=1.5, sym='.')
    bp = main_plot.boxplot(night_y, positions=x_axis, whis=1.5, sym='.')

    main_plot.axhspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
    main_plot.axhspan(session_start, session_start - _2_hour, color='red', alpha=.2, zorder=-100)

    xtickNames = pyplot.setp(main_plot, xticklabels=labels)
    pyplot.setp(xtickNames, rotation=45)
    return fig, False


def cohorts_daytime_bouts_boxplot_hattrick():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])

    x_axis = list()
    before_end = list()
    after_start = list()
    night_y = list()
    labels = list()
    index = 0
    for cohort in cohorts:
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
            night_bouts = bouts.filter(ebt_start_time__gte=lights_out).filter(ebt_start_time__lt=lights_on).values_list(
                'ebt_start_time', flat=True)
            day_bouts = bouts.filter(ebt_start_time__gte=lights_on) | bouts.filter(ebt_start_time__lt=lights_out)
            day_bouts = day_bouts.values_list('ebt_start_time', flat=True)

            b4_end = list()
            _after_start = list()
            for v in day_bouts:
                if v >= lights_on:
                    new_v = v - _24_hour
                    b4_end.append(new_v)
                else:
                    _after_start.append(v)

            _after_start.extend(night_bouts)
            before_end.append(b4_end)
            after_start.append(_after_start)

            x_axis.append(index)
            labels.append(str(monkey.pk))
            index += 1
        index += 3

    bp = main_plot.boxplot(before_end, positions=x_axis, whis=1.5, sym='.')
    bp = main_plot.boxplot(after_start, positions=x_axis, whis=1.5, sym='.')

    main_plot.axhspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
    main_plot.axhspan(session_start, session_start - _2_hour, color='red', alpha=.2, zorder=-100)

    xtickNames = pyplot.setp(main_plot, xticklabels=labels)
    pyplot.setp(xtickNames, rotation=45)
    return fig, False


def cohorts_scatterbox():
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults
    colors = ['green', 'blue', 'red']

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, 1:])
    main_plot.set_title("Ethanol Intake Distribution during Open Access ")
    main_plot.set_xlabel("Hour of day")
    main_plot.set_ylabel("Total vol etoh consumed during hour")

    width = 1
    day_hours = range(0, _22_hour, _1_hour)
    cohort_hours = list()
    for cohort in cohorts:
        monkeys = cohort.monkey_set.exclude(mky_drinking=False)
        monkey_hours = list()
        for start_time in day_hours:
            mky_sums = list()
            for monkey in monkeys:
                bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time,
                                                           ebt_start_time__lt=start_time + _1_hour)
                bout_vols = bouts.values_list('ebt_volume', flat=True)
                mky_sum = numpy.array(bout_vols).sum()
                mky_sums.append(mky_sum)
            monkey_hours.append(mky_sums)
        cohort_hours.append(monkey_hours)

    x_position = numpy.array([i * (2 + len(cohorts)) for i in range(len(day_hours))])
    wrecktangles = list()
    for cohort, ch, color in zip(cohorts, cohort_hours, colors):
        bp = main_plot.boxplot(ch, positions=x_position, sym='.')
        x_position += 1

        wrect = patches.Rectangle((0, 0), 1, 1, fc=color, label=str(cohort))
        wrecktangles.append(wrect)
        for key in bp.keys():
            if key != 'medians':
                pyplot.setp(bp[key], color=color)

    main_plot.legend(wrecktangles, (wrect.get_label() for wrect in wrecktangles), loc=0)

    main_plot.set_xlim(xmin=-1) # i don't understand why i need this
    main_plot.axvspan(7 * (2 + len(cohorts)) - 1, 19 * (2 + len(cohorts)) - 1, color='black', alpha=.2, zorder=-100)

    x_labels = ['hr %d' % i for i in range(1, 23)]
    main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
    xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
    pyplot.setp(xtickNames, rotation=45)


def cohorts_bec_stage_scatter(stage):
    cohorts = list()
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
    cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
    colors = ["orange", 'blue', 'green']
    scatter_markers = ['+', 'x', '4']
    centroid_markers = ['s', 'D', 'v']

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title("Induction Stage %d" % (stage + 1))
    main_plot.set_xlabel("BEC")
    main_plot.set_ylabel("Hours since last etoh intake")

    starts = [0, .9, 1.4]
    ends = [.6, 1.1, 1.6]
    stage_start = starts[stage]
    stage_end = ends[stage]
    sample_time = [30 * 60., 60 * 60., 90 * 60.]
    for index, cohort in enumerate(cohorts):
        x_axis = list()
        y_axis = list()
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            becs = MonkeyBEC.objects.Ind().filter(monkey=monkey).order_by('pk')
            becs = becs.filter(mtd__mtd_etoh_g_kg__gte=stage_start).filter(mtd__mtd_etoh_g_kg__lte=stage_end)
            seconds = becs.values_list('mtd__mtd_seconds_to_stageone', flat=True)
            try:
                y_axis.extend([(s - sample_time[stage]) / (60 * 60) for s in
                               seconds]) # time between end of drinking and sample taken
            except:
                print "skipping monkey %d" % monkey.pk
                continue
            x_axis.extend(becs.values_list('bec_mg_pct', flat=True))

        scatter = main_plot.scatter(x_axis, y_axis, color=colors[index], marker=scatter_markers[index], alpha=1, s=150,
                                    label=str(cohort))
        res, idx = cluster.vq.kmeans2(numpy.array(zip(x_axis, y_axis)), 1)
        scatter = main_plot.scatter(res[:, 0][0], res[:, 1][0], color=colors[index], marker=centroid_markers[index],
                                    alpha=1, s=250, label=str(cohort) + " Centroid")

    main_plot.axhspan(0, 0, color='black', alpha=.4, zorder=-100)
    main_plot.text(0, 0, "Blood Sample Taken")

    leg = main_plot.legend(loc=9, ncol=3, scatterpoints=1)
    ltext = leg.get_texts()
    pyplot.setp(ltext, fontsize=12)
    main_plot.set_xlim(xmin=0)
    main_plot.set_ylim(ymin=-1.7)
    yticks = [-1, ]
    yticks.extend(range(0, 13, 2))
    main_plot.set_yticks(yticks)


def cohort_etoh_gkg_histogram(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(cohort.coh_cohort_name + " Open Access Only")
    main_plot.set_xlabel("# of days with ethanol intake")
    main_plot.set_ylabel("Ethanol Intake, g/kg")
    y_axes = list()
    labels = list()
    for monkey in cohort.monkey_set.exclude(mky_drinking=False):
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
        gkg_values = mtds.values_list('mtd_etoh_g_kg', flat=True)
        gkg_values = numpy.array(gkg_values)
        y_axes.append(gkg_values)
        labels.append(str(monkey.pk))
    bin_edges = range(9)
    n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
    main_plot.legend(ncol=2, loc=0)


def cohort_etoh_quadbar(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle(str(cohort), size=18)
    main_gs = gridspec.GridSpec(2, 2)
    main_gs.update(left=0.08, right=.98, top=.92, bottom=.06, wspace=.02, hspace=.23)

    cohort_colors = ['navy', 'slateblue']
    main_plot = None
    subplots = [(i, j) for i in range(2) for j in range(2)]
    for gkg, _sub in enumerate(subplots, 1):
        main_plot = fig.add_subplot(main_gs[_sub], sharey=main_plot)
        main_plot.set_title("Open Access, greater than %d g per kg Etoh" % gkg)

        monkeys = cohort.monkey_set.filter(mky_drinking=True).values_list('pk', flat=True)
        width = .9

        data = list()
        colors = list()
        for i, mky in enumerate(monkeys):
            mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=mky,
                                                                                       mtd_etoh_g_kg__gte=gkg).count()
            mtds = mtds if mtds else .001
            data.append((mky, mtds))
            colors.append(cohort_colors[i % 2]) # we don't want the colors sorted.  It breaks if you try anyway.
        sorted_data = sorted(data, key=lambda t: t[1])
        sorted_data = numpy.array(sorted_data)
        labels = sorted_data[:, 0]
        yaxis = sorted_data[:, 1]
        bar = main_plot.bar(range(len(monkeys)), yaxis, width, color=colors)

        if gkg % 2:
            main_plot.set_ylabel("Day count")
        else:
            main_plot.get_yaxis().set_visible(False)

        x_labels = ['%d' % i for i in labels]
        main_plot.set_xticks(range(len(monkeys)))
        xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
        pyplot.setp(xtickNames, rotation=45)
    return fig, True


def cohort_bec_day_distribution(cohort, stage):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    colors = ["orange", 'blue', 'green']

    sample_time = [60 * 30., 60 * 60., 60 * 90.]
    starts = [0, .9, 1.4]
    ends = [.6, 1.1, 1.6]
    stage_start = starts[stage]
    stage_end = ends[stage]

    becs = MonkeyBEC.objects.Ind().filter(monkey__cohort=cohort)# cohort and induction filter
    becs = becs.filter(mtd__mtd_etoh_g_kg__gte=stage_start).filter(mtd__mtd_etoh_g_kg__lte=stage_end).order_by(
        'bec_collect_date') # stage filter and ordering
    dates = becs.dates('bec_collect_date', 'day').distinct()

    columns = 2
    rows = int(numpy.ceil(dates.count() / columns))

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(rows, columns)
    main_gs.update(left=0.08, right=.98, wspace=.15, hspace=.15)
    main_plot = None

    subplots = [(i, j) for i in range(rows) for j in range(columns)]
    for date, _sub in zip(dates, subplots):
        main_plot = fig.add_subplot(main_gs[_sub])
        x_axis = list()
        y_axis = list()
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            try:
                bec = becs.get(bec_collect_date=date, monkey=monkey)
            except:
                continue

            eevs = ExperimentEvent.objects.filter(monkey=monkey, eev_occurred__year=date.year,
                                                  eev_occurred__month=date.month, eev_occurred__day=date.day)
            eevs = eevs.exclude(eev_etoh_volume=None).exclude(eev_etoh_volume=0)
            seconds = eevs.values_list('eev_session_time', flat=True)
            try:
                y_vals = [(s - sample_time[stage]) / (60 * 60) for s in
                          seconds] # time between end of drinking and sample taken
            except:
                print "skipping monkey %d" % monkey.pk
                continue

            x_axis.append(bec.bec_mg_pct)
            y_axis.append(y_vals)
        main_plot.boxplot(y_axis, positions=x_axis, widths=5)
        main_plot.axhspan(0, 0, color='black', alpha=.3)

    return fig, True


def cohorts_daytime_volbouts_bargraph_split(phase):
    assert type(phase) == int and 0 <= phase <= 2
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    _phase = 'mtd__drinking_experiment__dex_date__gt' if phase == 2 else 'mtd__drinking_experiment__dex_date__lte'

    title_append = " Phase %d Open Access" % phase if phase else " All Open Access"
    width = 1
    figures = list()
    main_plot = None
    for cohort in cohorts:
        index = 0
        night_time = list()
        labels = set()
        fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        main_gs = gridspec.GridSpec(3, 40)
        main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
        main_plot = fig.add_subplot(main_gs[:, 1:], sharey=main_plot)
        main_plot.set_title(cohort.coh_cohort_name + title_append)
        main_plot.set_xlabel("Hour of day")
        main_plot.set_ylabel("Total vol etoh consumed during hour")

        monkeys = cohort.monkey_set.exclude(mky_drinking=False)
        mky_count = float(monkeys.count())
        cmap = cm.get_cmap('jet')
        mky_color = list()
        for idx, key in enumerate(monkeys):
            mky_color.append(cmap(idx / (mky_count - 1)))
        for start_time in range(0, _22_hour, _1_hour):
            x_axis = list()
            y_axis = list()
            if start_time >= lights_out and start_time <= lights_on:
                night_time.append(index)
            for monkey in monkeys:
                bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time,
                                                           ebt_start_time__lt=start_time + _1_hour)
                if phase:
                    bouts = bouts.filter(**{_phase: rhesus_1st_oa_end[cohort.pk]})
                bout_vols = bouts.values_list('ebt_volume', flat=True)
                bouts_sum = numpy.array(bout_vols).sum()
                #			bout_starts = bout_starts - diff
                y_axis.append(bouts_sum)
                x_axis.append(index)
                index += 1
                labels.add(str(monkey.pk))
            rects1 = main_plot.bar(x_axis, y_axis, width, color=mky_color, alpha=.7)
            index += 2
        main_plot.legend(rects1, labels, ncol=5, loc=9)
        main_plot.axvspan(min(night_time), max(night_time), color='black', alpha=.2, zorder=-100)
        x_labels = ['hr %d' % i for i in range(1, 23)]
        main_plot.set_xlim(xmax=index - 2)
        main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
        xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
        pyplot.setp(xtickNames, rotation=45)
        main_plot.set_ylim(ymax=100000)
        figures.append((fig, cohort))
    return figures


def cohorts_daytime_bouts_histogram_split(phase):
    assert type(phase) == int and 0 <= phase <= 2
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    _phase = 'mtd__drinking_experiment__dex_date__gt' if phase == 2 else 'mtd__drinking_experiment__dex_date__lte'

    title_append = " Phase %d Open Access" % phase if phase else " All Open Access"
    figures = list()
    main_plot = None
    for cohort in cohorts:
        fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        main_gs = gridspec.GridSpec(3, 40)
        main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
        main_plot = fig.add_subplot(main_gs[:, :], sharey=main_plot)

        main_plot.set_title(cohort.coh_cohort_name + title_append)
        main_plot.set_xlabel("Hour of Session")
        main_plot.set_ylabel("Total bout count during hour")
        x_axis = list()
        y_axes = list()
        labels = list()
        index = 0
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
            if phase:
                bouts = bouts.filter(**{_phase: rhesus_1st_oa_end[cohort.pk]})
            bout_starts = bouts.values_list('ebt_start_time', flat=True)
            bout_starts = numpy.array(bout_starts)
            y_axes.append(bout_starts)
            x_axis.append(index)
            labels.append(str(monkey.pk))
            index += 1
        bin_edges = range(0, _22_hour + 1, _1_hour)
        n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
        main_plot.axvspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
        main_plot.legend(ncol=5, loc=9)
        main_plot.set_ylim(ymax=1600)

        x_labels = ['hr %d' % i for i in range(1, 23)]
        new_xticks = range(0, _22_hour, _1_hour)
        new_xticks = [_x + (_1_hour / 2.) for _x in new_xticks]
        main_plot.set_xticks(new_xticks)
        xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
        pyplot.setp(xtickNames, rotation=45)
        figures.append((fig, cohort))
    return figures


def cohorts_maxbouts_histogram(phase):
    assert type(phase) == int and 0 <= phase <= 2
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    _phase = 'drinking_experiment__dex_date__gt' if phase == 2 else 'drinking_experiment__dex_date__lte'

    title_append = " Phase %d Open Access" % phase if phase else " All Open Access"
    figures = list()
    main_plot = None
    for cohort in cohorts:
        fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        main_gs = gridspec.GridSpec(3, 40)
        main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
        main_plot = fig.add_subplot(main_gs[:, :], sharey=main_plot)

        main_plot.set_title(cohort.coh_cohort_name + title_append)
        main_plot.set_xlabel("Maximum Bout Volume")
        main_plot.set_ylabel("Bout Count")
        y_axes = list()
        labels = list()
        max_bout = 0
        for monkey in cohort.monkey_set.exclude(mky_drinking=False):
            mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment__dex_type='Open Access', monkey=monkey)
            if phase:
                mtds = mtds.filter(**{_phase: rhesus_1st_oa_end[cohort.pk]})
            mtd_maxes = mtds.values_list('mtd_max_bout_vol', flat=True)
            mtd_maxes = numpy.array(mtd_maxes)
            try:
                max_bout = max_bout if max_bout > mtd_maxes.max() else mtd_maxes.max()
            except:
                continue
            y_axes.append(mtd_maxes)
            labels.append(str(monkey.pk))
        bin_max = 900
        bin_edges = range(0, bin_max, 100)
        n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
        main_plot.legend(ncol=5, loc=9)
        figures.append((fig, cohort))
    return figures


def cohorts_scatterbox_split(phase):
    assert type(phase) == int and 0 < phase < 3
    colors = ['green', 'blue', 'red']
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    _phase = 'mtd__drinking_experiment__dex_date__gt' if phase == 2 else 'mtd__drinking_experiment__dex_date__lte'

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, 1:])
    main_plot.set_title("Ethanol Intake Distribution during Phase %d Open Access" % phase)
    main_plot.set_xlabel("Hour of day")
    main_plot.set_ylabel("Total vol etoh consumed during hour")

    width = 1
    day_hours = range(0, _22_hour, _1_hour)
    cohort_hours = list()
    for cohort in cohorts:
        monkeys = cohort.monkey_set.exclude(mky_drinking=False)
        monkey_hours = list()
        for start_time in day_hours:
            mky_sums = list()
            for monkey in monkeys:
                bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time,
                                                           ebt_start_time__lt=start_time + _1_hour)
                bouts = bouts.filter(**{_phase: rhesus_1st_oa_end[cohort.pk]})
                bout_vols = bouts.values_list('ebt_volume', flat=True)
                mky_sum = numpy.array(bout_vols).sum()
                mky_sums.append(mky_sum)
            monkey_hours.append(mky_sums)
        cohort_hours.append(monkey_hours)

    x_position = numpy.array([i * (2 + len(cohorts)) for i in range(len(day_hours))])
    wrecktangles = list()
    for cohort, ch, color in zip(cohorts, cohort_hours, colors):
        bp = main_plot.boxplot(ch, positions=x_position, sym='.')
        x_position += 1

        wrect = patches.Rectangle((0, 0), 1, 1, fc=color, label=str(cohort))
        wrecktangles.append(wrect)
        for key in bp.keys():
            if key != 'medians':
                pyplot.setp(bp[key], color=color)

    main_plot.legend(wrecktangles, (wrect.get_label() for wrect in wrecktangles), loc=0)

    main_plot.set_xlim(xmin=-1) # i don't understand why i need this
    main_plot.axvspan(7 * (2 + len(cohorts)) - 1, 19 * (2 + len(cohorts)) - 1, color='black', alpha=.2, zorder=-100)

    x_labels = ['hr %d' % i for i in range(1, 23)]
    main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
    xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
    pyplot.setp(xtickNames, rotation=45)


def cohort_age_sessiontime(stage):
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    colors = ["orange", 'blue', 'green']
    scatter_markers = ['s', 'D', 'v']

    starts = [0, .9, 1.4]
    ends = [.6, 1.1, 1.6]
    stage_start = starts[stage]
    stage_end = ends[stage]

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title("Induction Stage %d" % (stage + 1))
    main_plot.set_xlabel("age at first intox")
    main_plot.set_ylabel("average session1 time")

    for index, cohort in enumerate(cohorts):
        x = list()
        y = list()
        for monkey in cohort.monkey_set.exclude(mky_age_at_intox=None).exclude(mky_age_at_intox=0):
            age = monkey.mky_age_at_intox / 365.25
            mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=monkey)
            mtds = mtds.filter(mtd_etoh_g_kg__gte=stage_start).filter(mtd_etoh_g_kg__lte=stage_end)
            avg = mtds.aggregate(Avg('mtd_seconds_to_stageone'))['mtd_seconds_to_stageone__avg']
            avg /= 3600
            x.append(age)
            y.append(avg)
        main_plot.scatter(x, y, label=str(cohort), color=colors[index], marker=scatter_markers[index], s=150)
    main_plot.legend(loc=0, scatterpoints=1)
    #	ltext = leg.get_texts()
    #	pyplot.setp(ltext, fontsize=12)
    #	main_plot.set_xlim(xmin=0)
    main_plot.set_ylim(ymin=0)
    return fig


def cohort_age_vol_hour(phase, hours): # phase = 0-2
    assert 0 <= phase <= 2
    assert 0 < hours < 3
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    oa_phases = ['', 'eev_occurred__lte', 'eev_occurred__gt']
    colors = ["orange", 'blue', 'green']
    scatter_markers = ['s', 'D', 'v']
    titles = ["Open Access, 12 months", "Open Access, 1st Six Months", "Open Access, 2nd Six Months"]
    titles = [t + ", first %d hours" % hours for t in titles]

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(titles[phase])
    main_plot.set_xlabel("Age at first intox")
    main_plot.set_ylabel("Daily Average Etoh Volume in First %d Hour%s" % (hours, '' if hours == 1 else 's'))

    for index, cohort in enumerate(cohorts):
        x = list()
        y = list()
        for monkey in cohort.monkey_set.exclude(mky_age_at_intox=None).exclude(mky_age_at_intox=0):
            age = monkey.mky_age_at_intox / 365.25
            x.append(age)

            eevs = ExperimentEvent.objects.filter(dex_type='Open Access', monkey=monkey).exclude(
                eev_etoh_volume=None).exclude(eev_etoh_volume=0)
            if phase:
                eevs = eevs.filter(**{oa_phases[phase]: rhesus_1st_oa_end[cohort.pk]})
            eevs = eevs.filter(eev_session_time__lt=hours * 60 * 60)
            eev_count = eevs.dates('eev_occurred', 'day').count() * 1.
            eev_vol = eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
            value = eev_vol / eev_count
            y.append(value)
        main_plot.scatter(x, y, label=str(cohort), color=colors[index], marker=scatter_markers[index], s=150)
    main_plot.legend(loc=0, scatterpoints=1)
    return fig


def _cohort_etoh_cumsum_nofood(cohort, subplot, minutes_excluded=5):
    mkys = cohort.monkey_set.filter(mky_drinking=True)
    mky_count = mkys.count()

    subplot.set_title("Induction Cumulative EtOH Intake for %s, excluding drinks less than %d minutes after food" % (
    str(cohort), minutes_excluded))
    subplot.set_ylabel("Volume EtOH / Monkey Weight, ml/kg")

    cmap = plotting.get_cmap('jet')
    mky_colors = dict()
    mky_ymax = dict()
    for idx, m in enumerate(mkys):
        eevs = ExperimentEvent.objects.Ind().filter(monkey=m).exclude(eev_etoh_volume=None).order_by('eev_occurred')
        eevs = eevs.exclude(eev_pellet_time__gte=minutes_excluded * 60)
        if not eevs.count():
            continue
        mky_colors[m] = cmap(idx / (mky_count - 1.))
        volumes = numpy.array(eevs.values_list('eev_etoh_volume', flat=True))
        yaxis = numpy.cumsum(volumes)
        mky_ymax[m] = yaxis[-1]
        xaxis = numpy.array(eevs.values_list('eev_occurred', flat=True))
        subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=mky_colors[m], label=str(m.pk))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    subplot.legend(loc=2)
    if not len(mky_ymax.values()):
        raise Exception("no eevs found")
    return subplot, mky_ymax, mky_colors


def _cohort_etoh_max_bout_cumsum(cohort, subplot):
    mkys = Monkey.objects.Drinkers().filter(cohort=cohort).values_list('pk', flat=True)
    mky_count = mkys.count()

    subplot.set_title("Induction St. 3 Cumulative Max Bout EtOH Intake for %s" % str(cohort))
    subplot.set_ylabel("Volume EtOH / Monkey Weight, ml/kg")

    cmap = plotting.get_cmap('jet')
    mky_colors = dict()
    mky_ymax = dict()
    for idx, m in enumerate(mkys):
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m, drinking_experiment__dex_type="Induction").exclude(
            mtd_max_bout_vol=None).order_by('drinking_experiment__dex_date')
        mtds = mtds.filter(mtd_etoh_g_kg__gte=1.4).filter(mtd_etoh_g_kg__lte=1.6)
        if not mtds.count():
            continue
        mky_colors[m] = rhesus_monkey_colors[m]
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
    subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
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
    subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
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
    subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot


def cohort_etoh_max_bout_cumsum_horibar_3gkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_3gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, None


def cohort_etoh_max_bout_cumsum_horibar_4gkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_4gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, None


def cohort_etoh_max_bout_cumsum_horibar_ltgkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_ltgkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, None


def cohort_etoh_ind_cumsum_horibar_34gkg(cohort, minutes_excluded=5):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_cumsum_nofood(cohort, line_subplot,
                                                                        minutes_excluded=minutes_excluded)
    except Exception as e:
        print e.message
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_4gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, None


#--
def cohort_age_mtd_general(phase, mtd_callable_yvalue_generator): # phase = 0-2
    assert 0 <= phase <= 2
    _7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
    _5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
    _4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
    cohorts = [_7a, _5, _4]
    oa_phases = ['', 'drinking_experiment__dex_date__lte', 'drinking_experiment__dex_date__gt']
    colors = ["orange", 'blue', 'green']
    scatter_markers = ['s', 'D', 'v']
    titles = ["Open Access, 12 months", "Open Access, 1st Six Months", "Open Access, 2nd Six Months"]

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(titles[phase])
    main_plot.set_xlabel("Age at first intox")

    label = ''
    for index, cohort in enumerate(cohorts):
        x = list()
        y = list()
        for monkey in cohort.monkey_set.exclude(mky_age_at_intox=None).exclude(mky_age_at_intox=0):
            age = monkey.mky_age_at_intox / 365.25
            mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
            if phase:
                mtds = mtds.filter(**{oa_phases[phase]: rhesus_1st_oa_end[cohort.pk]})
            x.append(age)
            value, label = mtd_callable_yvalue_generator(mtds)
            y.append(value)
        main_plot.scatter(x, y, label=str(cohort), color=colors[index], marker=scatter_markers[index], s=150)
    main_plot.set_ylabel(label)
    main_plot.legend(loc=0, scatterpoints=1)
    return fig


def _mtd_call_gkg_etoh(mtds):
    avg = mtds.aggregate(Avg('mtd_etoh_g_kg'))['mtd_etoh_g_kg__avg']
    return avg, "Average daily ethanol intake, g/kg"


def _mtd_call_bec(mtds):
    avg = mtds.aggregate(Avg('bec_record__bec_mg_pct'))['bec_record__bec_mg_pct__avg']
    return avg, "Average BEC value"


def _mtd_call_over_3gkg(mtds):
    count = mtds.filter(mtd_etoh_g_kg__gte=3).count()
    return count, "Days over 3 g/kg"


def _mtd_call_over_4gkg(mtds):
    count = mtds.filter(mtd_etoh_g_kg__gte=4).count()
    return count, "Days over 4 g/kg"


def _mtd_call_max_bout_vol(mtds):
    avg = mtds.aggregate(Avg('mtd_max_bout_vol'))['mtd_max_bout_vol__avg']
    return avg, "Average Maximum Bout Volume"


def _mtd_call_max_bout_vol_pct(mtds):
    avg = mtds.aggregate(Avg('mtd_pct_max_bout_vol_total_etoh'))['mtd_pct_max_bout_vol_total_etoh__avg']
    return avg, "Average Maximum Bout, as % of total intake"

#--

rhesus_keys = ['VHD', 'HD', 'MD', 'LD']
rhesus_1st_oa_end = {10: "2011-08-01", 9: '2012-01-08', 6: "2009-10-13", 5: "2009-05-24"}

rhesus_drinkers = dict()
rhesus_drinkers['LD'] = [10048, 10052, 10055, 10056, 10058, 10083, 10084, 10085, 10089, 10090,
                         10092] # all drinking monkeys in 5,6,9,10 not listed below
rhesus_drinkers['MD'] = [10082, 10057, 10087, 10088, 10059, 10054, 10086, 10051, 10049, 10063, 10091, 10060, 10064,
                         10098, 10065, 10097, 10066, 10067, 10061, 10062]
rhesus_drinkers['HD'] = [10082, 10049, 10064, 10063, 10097, 10091, 10065, 10066, 10067, 10088, 10098, 10061, 10062]
rhesus_drinkers['VHD'] = [10088, 10091, 10066, 10098, 10063, 10061, 10062]

rhesus_drinkers_distinct = dict()
rhesus_drinkers_distinct['LD'] = [10048, 10052, 10055, 10056, 10058, 10083, 10084, 10085, 10089, 10090, 10092]
rhesus_drinkers_distinct['MD'] = [10057, 10087, 10059, 10054, 10086, 10051, 10060]
rhesus_drinkers_distinct['HD'] = [10082, 10049, 10064, 10097, 10065, 10067]
rhesus_drinkers_distinct['VHD'] = [10088, 10091, 10066, 10098, 10063, 10061, 10062]

all_rhesus_drinkers = [__x for __d in rhesus_drinkers_distinct.itervalues() for __x in __d]

rhesus_markers = {'LD': 'v', 'MD': '<', 'HD': '>', 'VHD': '^'}

rhesus_colors = {'LD': '#0052CC', 'MD': 'green', "HD": "orange", 'VHD': 'red'}
rhesus_colors_hex = {'LD': '#0052CC', 'MD': '#008000', 'HD': '#FF6600', 'VHD': '#FF0000'}
rhesus_monkey_category = dict()
rhesus_monkey_colors = dict()
rhesus_monkey_colors_hex = dict()
rhesus_monkey_markers = dict()
for key in rhesus_keys:
    for monkey_pk in rhesus_drinkers_distinct[key]:
        rhesus_monkey_category[monkey_pk] = key
        rhesus_monkey_colors[monkey_pk] = rhesus_colors[key]
        rhesus_monkey_colors_hex[monkey_pk] = rhesus_colors_hex[key]
        rhesus_monkey_markers[monkey_pk] = rhesus_markers[key]


def rhesus_etoh_gkg_histogram():
    mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__cohort__in=[5, 6, 9, 10])
    daily_gkgs = mtds.values_list('mtd_etoh_g_kg', flat=True)

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])

    _bins = 150
    linspace = numpy.linspace(0, max(daily_gkgs), _bins) # defines number of bins in histogram
    n, bins, patches = subplot.hist(daily_gkgs, bins=linspace, normed=False, alpha=.5, color='slateblue')
    bincenters = 0.5 * (bins[1:] + bins[:-1])
    newx = numpy.linspace(min(bincenters), max(bincenters), _bins / 8) # smooth out the x axis
    newy = plotting.spline(bincenters, n, newx) # smooth out the y axis
    subplot.plot(newx, newy, color='r', linewidth=5) # smoothed line
    subplot.set_ylim(ymin=0)
    subplot.set_title("Rhesus 4/5/7a/7b, g/kg per day")
    subplot.set_ylabel("Day Count")
    subplot.set_xlabel("Day's etoh intake, g/kg")
    return fig


def rhesus_etoh_gkg_bargraph(limit_step=1):
    cohorts = Cohort.objects.filter(pk__in=[5, 6, 9, 10])
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])

    monkeys = Monkey.objects.none()
    for coh in cohorts:
        monkeys |= coh.monkey_set.filter(mky_drinking=True)

    width = 1 / (1. / limit_step)
    limits = numpy.arange(1, 9, limit_step)
    gkg_daycounts = numpy.zeros(len(limits))
    for monkey in monkeys:
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
    subplot.bar(limits, gkg_daycounts, width=width, color='navy')
    xmax = max(gkg_daycounts) * 1.005
    subplot.set_ylim(ymin=0, ymax=xmax)
    subplot.set_title("Rhesus 4/5/7a/7b, distribution of intakes exceeding g/kg minimums")
    subplot.set_ylabel("Summation of each monkey's percentage of days where EtoH intake exceeded x-value")
    subplot.set_xlabel("Etoh intake, g/kg")
    return fig


def rhesus_etoh_gkg_stackedbargraph(limit_step=.1, fig_size=plotting.HISTOGRAM_FIG_SIZE):
    fig = pyplot.figure(figsize=fig_size, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])

    limits = numpy.arange(1, 9, limit_step)
    bottom = numpy.zeros(len(limits))
    color_index = 0
    for key in rhesus_keys:
        width = 1 / (1. / limit_step)
        gkg_daycounts = numpy.zeros(len(limits))
        for monkey in rhesus_drinkers_distinct[key]:
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
        color = rhesus_colors[key]
        color_index += 1
        subplot.bar(limits, gkg_daycounts, bottom=bottom, width=width, color=color, label=key, alpha=1)
        bottom += gkg_daycounts

    subplot.set_xlim(xmin=1, xmax=7)
    tick_size = 20
    title_size = 26
    label_size = 24
    legend_size = 20
    subplot.legend(prop={'size': legend_size})
    subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
    subplot.set_title("Rhesus 4/5/7a/7b, distribution of intakes exceeding g/kg minimums", size=title_size)
    subplot.set_ylabel("Aggregate percent days of EtOH intake exceeding x-value", size=label_size)
    subplot.set_xlabel("Etoh intake, g/kg", size=label_size)
    return fig


def rhesus_etoh_gkg_forced_monkeybargraphhistogram(fig_size=plotting.HISTOGRAM_FIG_SIZE):
    fig = pyplot.figure(figsize=fig_size, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(1, 6)
    gs.update(left=0.05, right=0.95, top=.95, wspace=.15, hspace=0)

    tick_size = 20
    title_size = 26
    label_size = 24
    #	Histogram, left
    subplot = fig.add_subplot(gs[:, :3])
    subplot = _etoh_gkg_forced_histogram(subplot, tick_size=tick_size, title_size=title_size, label_size=label_size)
    #	Histograms, right
    subplot = None
    cutoffs = {2: .5, 3: .3, 4: .1}
    for limit in range(2, 5, 1): # loop thru the remaining 3 divisions of the gridspec
        gs_index = limit + 1
        subplot = fig.add_subplot(gs[:, gs_index:gs_index + 1], sharex=subplot, sharey=subplot)
        subplot = _etoh_gkg_monkeybargraph(subplot, limit, cutoff=cutoffs[limit])
        subplot.yaxis.tick_right()
        subplot.tick_params(axis='both', which='major', labelsize=tick_size)
        subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
        if limit == 3: # middle subplot
            subplot.set_xlabel('Monkey', size=label_size)

    subplot.yaxis.set_label_position('right')
    subplot.set_ylabel('Percent', size=label_size)
    return fig


def _etoh_gkg_forced_histogram(subplot, tick_size=16, title_size=22, label_size=20):
    monkeys = Monkey.objects.Drinkers().filter(cohort__in=[5, 6, 9, 10]).values_list('pk', flat=True).distinct()

    increment = .1
    limits = numpy.arange(0, 8, increment)
    gkg_daycounts = numpy.zeros(len(limits))
    for monkey in monkeys:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
        if not mtds.count():
            continue
        max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
        min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
        days = float((max_date - min_date).days)
        for index, limit in enumerate(limits):
            if not limit:
                continue
            _count = mtds.filter(mtd_etoh_g_kg__gt=limits[index - 1]).filter(mtd_etoh_g_kg__lte=limits[index]).count()
            gkg_daycounts[index] += _count / days

    gkg_daycounts = list(gkg_daycounts)
    for index, xy in enumerate(zip(limits, gkg_daycounts)):
        x, y = xy
        color = 'gold' if index % 2 else 'orange'
        subplot.bar(x, y, width=increment, color=color, edgecolor=None)

    newx = numpy.linspace(min(limits), max(limits), 40) # smooth out the x axis
    newy = plotting.spline(limits, gkg_daycounts, newx) # smooth out the y axis
    subplot.plot(newx, newy, color='r', linewidth=3) # smoothed line

    xmax = 7 # monkeys are cut off at 7 gkg
    ymax = max(gkg_daycounts) * 1.005
    subplot.set_ylim(ymin=0, ymax=ymax)
    subplot.set_xlim(xmin=0, xmax=xmax)
    subplot.set_title("Rhesus 4/5/7a/7b, distribution of intakes", size=title_size)
    subplot.set_ylabel("Aggregate percent days of EtOH consumption", size=label_size)
    subplot.set_xlabel("Etoh intake, g/kg", size=label_size)
    subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
    return subplot


def _etoh_gkg_monkeybargraph(subplot, limit, cutoff=None):
    monkeys = Monkey.objects.Drinkers().filter(cohort__in=[5, 6, 9, 10]).values_list('pk', flat=True).distinct()
    keys = list()
    values = list()
    for monkey in monkeys:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
        if not mtds.count():
            continue
        max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
        min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
        days = float((max_date - min_date).days)
        _count = mtds.filter(mtd_etoh_g_kg__gt=limit).count()
        values.append(_count / days)
        keys.append(str(monkey))

    sorted_x = sorted(zip(keys, values), key=operator.itemgetter(1))
    keys = list()
    values = list()
    for k, v in sorted_x:
        keys.append(k)
        values.append(v)
    #	subplot.bar(limits, gkg_daycounts, #width=.95, color='navy')
    xaxis = range(len(values))
    for x, y in zip(xaxis, values):
        color = 'navy' if x % 2 else 'slateblue'
        subplot.bar(x, y, width=1, color=color, edgecolor=None)
    if cutoff:
        subplot.axhspan(0, cutoff, color='red', alpha=.4, zorder=-100)
        subplot.text(1, cutoff, "%d%%" % int(cutoff * 100), size=20)

    subplot.set_xlim(xmax=len(monkeys))
    subplot.set_xticks([])
    subplot.set_title("%% days > %d g/kg" % limit, size=20)
    return subplot


def rhesus_etoh_gkg_forced_histogram():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])
    subplot = _etoh_gkg_forced_histogram(subplot)
    return fig


def rhesus_etoh_gkg_monkeybargraph():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.04, right=0.98, wspace=.08, hspace=0)

    limits = range(2, 5, 1)
    for index, limit in enumerate(limits):
        subplot = fig.add_subplot(gs[:, index])
        subplot = _etoh_gkg_monkeybargraph(subplot, limit)
    return fig


def _rhesus_minute_volumes(subplot, minutes, monkey_category, volume_summation, vs_kwargs=None):
    from utils import plotting

    assert monkey_category in rhesus_drinkers.keys()
    vs_kwargs = vs_kwargs if vs_kwargs is not None else dict()
    light_data, light_count = volume_summation(monkey_category, minutes, exclude=True, **vs_kwargs)
    heavy_data, heavy_count = volume_summation(monkey_category, minutes, exclude=False, **vs_kwargs)
    assert light_data.keys() == heavy_data.keys()
    for x in light_data.keys():
        # lower, light drinkers
        _ld = light_data[x] / float(light_count)
        subplot.bar(x, _ld, width=.5, color='navy', edgecolor='none')
        # higher, heavy drinkers
        subplot.bar(x + .5, heavy_data[x] / float(heavy_count), width=.5, color='slateblue', edgecolor='none')
    #	patches.append(Rectangle((0,0),1,1, color=value))
    subplot.legend(
        [plotting.Rectangle((0, 0), 1, 1, color='slateblue'), plotting.Rectangle((0, 0), 1, 1, color='navy')],
        [monkey_category, "Not %s" % monkey_category], title="Monkey Category", loc='upper left')
    subplot.set_xlim(xmax=max(light_data.keys()))
    # rotate the xaxis labels
    xticks = [x + .5 for x in light_data.keys() if x % 15 == 0]
    xtick_labels = ["%d" % x for x in light_data.keys() if x % 15 == 0]
    subplot.set_xticks(xticks)
    subplot.set_xticklabels(xtick_labels)
    return subplot


def rhesus_oa_discrete_minute_volumes(minutes, monkey_category, distinct_monkeys=False):
    def _oa_eev_volume_summation(monkey_category, minutes=20, exclude=False, distinct_monkeys=False):
        data = defaultdict(lambda: 0)
        _drinkers = rhesus_drinkers_distinct if distinct_monkeys else rhesus_drinkers
        if exclude:
            monkey_set = [x for x in all_rhesus_drinkers if x not in _drinkers[monkey_category]]
        else:
            monkey_set = _drinkers[monkey_category]
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        for i in range(0, minutes):
            _eevs = eevs.filter(eev_pellet_time__gte=i * 60).filter(eev_pellet_time__lt=(i + 1) * 60)
            data[i] = _eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
        return data, len(monkey_set)

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    subplot = fig.add_subplot(main_gs[:, :])
    subplot = _rhesus_minute_volumes(subplot, minutes, monkey_category, _oa_eev_volume_summation,
                                     vs_kwargs={'distinct_monkeys': distinct_monkeys})
    subplot.set_xlabel("Minutes since last pellet")
    subplot.set_title("Average intake by minute after pellet")
    subplot.set_ylabel("Average volume, ml per monkey")
    return fig


def rhesus_thirds_oa_discrete_minute_volumes(minutes, monkey_category, distinct_monkeys=False):
    def _thirds_oa_eev_volume_summation(monkey_category, minutes=20, exclude=False, offset=0, distinct_monkeys=False):
        cohort_starts = {5: datetime(2008, 10, 20), 6: datetime(2009, 4, 13), 9: datetime(2011, 7, 12),
                         10: datetime(2011, 01, 03)}
        data = defaultdict(lambda: 0)
        _drinkers = rhesus_drinkers_distinct if distinct_monkeys else rhesus_drinkers
        if exclude:
            monkey_set = [x for x in all_rhesus_drinkers if x not in _drinkers[monkey_category]]
        else:
            monkey_set = _drinkers[monkey_category]
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        for coh, start_date in cohort_starts.items():
            _eevs = eevs.filter(monkey__cohort=coh)

            start = start_date + timedelta(days=offset)
            _eevs = _eevs.filter(eev_occurred__gte=start)
            if offset <= 120:
                end = start + timedelta(days=120)
                _eevs = _eevs.filter(eev_occurred__lt=end)
            for i in range(0, minutes):
                eev_data = _eevs.filter(eev_pellet_time__gte=i * 60).filter(eev_pellet_time__lt=(i + 1) * 60)
                sum_vol = eev_data.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
                if sum_vol is None:
                    continue
                data[i] += sum_vol
        return data, len(monkey_set)

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.04, right=0.98, wspace=.08, hspace=0)
    y_label = True
    subplot = None
    for index, offset in enumerate([0, 120, 240]):
        subplot = fig.add_subplot(main_gs[:, index], sharey=subplot, sharex=subplot)
        _rhesus_minute_volumes(subplot, minutes, monkey_category, _thirds_oa_eev_volume_summation,
                               vs_kwargs={'offset': offset, 'distinct_monkeys': distinct_monkeys})
        subplot.set_xlabel("Minutes since last pellet")
        subplot.set_title("Average intake by minute after pellet")
        if y_label:
            subplot.set_ylabel("Average volume, ml per monkey")
            y_label = False
    return fig


def _rhesus_category_scatterplot(subplot, collect_xy_data, xy_kwargs=None):
    xy_kwargs = xy_kwargs if xy_kwargs is not None else dict()
    all_x = list()
    all_y = list()
    for idx, key in enumerate(rhesus_keys):
        color = rhesus_colors[key]
        _x, _y = collect_xy_data(key, **xy_kwargs)
        all_x.extend(_x)
        all_y.extend(_y)
        subplot.scatter(_x, _y, color=color, edgecolor='none', s=100, label=key, marker=rhesus_markers[key], alpha=1)
        create_convex_hull_polygon(subplot, _x, _y, color)

    # regression line
    all_x = numpy.array(all_x)
    all_y = numpy.array(all_y)
    slope, intercept, r_value, p_value, std_err = stats.linregress(all_x, all_y)

    reg_label = "Fit: r=%f, p=%f" % (r_value, p_value)
    subplot.plot(all_x, all_x * slope + intercept, color='black', label=reg_label)

    handles, labels = subplot.get_legend_handles_labels()
    _handles = list()
    _labels = copy.copy(rhesus_keys)
    _labels.append(reg_label)
    for _l in _labels:
        _handles.append(handles[labels.index(_l)])
    return subplot, _handles, _labels


def rhesus_oa_pelletvolume_perday_perkg():
    def _oa_pelletvolume_perday_perkg(monkey_category):
        monkey_set = rhesus_drinkers_distinct[monkey_category]
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
        monkey_set = rhesus_drinkers_distinct[monkey_category]
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

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.06, right=0.98, wspace=.08, hspace=0)

    # main scatterplot, pellet vs etoh
    subplot = fig.add_subplot(main_gs[:])
    subplot, handles, labels = _rhesus_category_scatterplot(subplot, _oa_pelletvolume_perday_perkg)
    subplot.legend(handles, labels, scatterpoints=1, loc='lower left')
    subplot.set_title("EtOH Intake vs pellets")
    subplot.set_ylabel("Average pellet / Average weight, per monkey")
    subplot.set_xlabel("Average volume / Average weight, per monkey")

    # inset scatterplot, pellet vs water
    inset_plot = fig.add_axes([0.6, 0.7, 0.37, 0.23])
    inset_plot, handles, labels = _rhesus_category_scatterplot(inset_plot, _oa_pelletwater_perday_perkg)
    inset_plot.set_title("H20 Intake vs pellets")
    inset_plot.set_ylabel("Pellets/Weight/Monkey")
    inset_plot.set_xlabel("Water/Weight/Monkey")
    ## Because the legend is almost the same as the main subplot's legend, we dont need to show most of the keys
    ## but we do want to show the regression fit, and large enough to read without hiding the scatterplot
    for index, label in enumerate(labels):
        if 'Fit' in label:
            break
    inset_legend = inset_plot.legend([handles[index]], [labels[index]], scatterpoints=1, loc='upper right')
    inset_legend.get_frame().set_alpha(0) # hide the legend's background, so it doesn't hide the scatterplot
    return fig


def rhesus_thirds_oa_pelletvolume_perday_perkg():
    def _thirds_oa_pelletvolume_perday_perkg(monkey_category, offset=0):
        cohort_starts = {5: datetime(2008, 10, 20), 6: datetime(2009, 4, 13), 9: datetime(2011, 7, 12),
                         10: datetime(2011, 01, 03)}
        x_data = list()
        y_data = list()
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions()
        for coh, start_date in cohort_starts.items():
            _mtds = mtds.filter(monkey__cohort=coh)
            start = start_date + timedelta(days=offset)
            _mtds = _mtds.filter(drinking_experiment__dex_date__gte=start)
            if offset <= 120:
                end = start + timedelta(days=120)
                _mtds = _mtds.filter(drinking_experiment__dex_date__lt=end)
            for monkey in rhesus_drinkers_distinct[monkey_category]:
                _data = _mtds.filter(monkey=monkey)
                if not _data:
                    continue
                _data = _data.aggregate(Avg('mtd_etoh_intake'), Avg('mtd_total_pellets'), Avg('mtd_weight'))
                vol_avg = _data['mtd_etoh_intake__avg']
                pel_avg = _data['mtd_total_pellets__avg']
                wgt_avg = _data['mtd_weight__avg']
                x_data.append(vol_avg / wgt_avg)
                y_data.append(pel_avg / wgt_avg)
        return x_data, y_data

    fig = pyplot.figure(figsize=plotting.THIRDS_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.04, right=0.98, wspace=.08, hspace=0)
    y_label = True
    subplot = None
    for index, offset in enumerate([0, 120, 240]):
        subplot = fig.add_subplot(main_gs[:, index], sharey=subplot, sharex=subplot)

        subplot, handles, labels = _rhesus_category_scatterplot(subplot, _thirds_oa_pelletvolume_perday_perkg,
                                                                xy_kwargs={'offset': offset})
        subplot.legend(handles, labels, scatterpoints=1)
        subplot.set_title("Intake vs pellets")
        subplot.set_xlabel("Average volume / Average weight, per monkey")
        if y_label:
            subplot.set_ylabel("Average pellet / Average weight, per monkey")
            y_label = False
    return fig


def rhesus_bout_last_pellet_histogram(exclude_intrapellets=True, exclude_zero=False):
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle("Bouts vs time since pellet")
    gs = gridspec.GridSpec(4, 4)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)

    subplot = None
    for index, key in enumerate(rhesus_drinkers_distinct.iterkeys()):
        subplot = fig.add_subplot(gs[index, :], sharex=subplot, sharey=subplot)
        ebts = ExperimentBout.objects.OA().filter(mtd__monkey__cohort__in=[5, 6, 9, 10])
        if exclude_intrapellets:
            ebts = ebts.exclude(ebt_contains_pellet=True)
        if exclude_zero:
            ebts = ebts.exclude(ebt_pellet_elapsed_time_since_last__lte=3 * 60)
        pellet_times = ebts.filter(mtd__monkey__in=rhesus_drinkers_distinct[key]).values_list(
            'ebt_pellet_elapsed_time_since_last', flat=True)
        bin_count = 250
        linspace = numpy.linspace(0, max(pellet_times), bin_count) # defines number of bins in histogram
        n, bins, patches = subplot.hist(pellet_times, bins=linspace, normed=False, alpha=.5, color='slateblue',
                                        log=True)
        bincenters = 0.5 * (bins[1:] + bins[:-1])
        newx = numpy.linspace(min(bincenters), max(bincenters), bin_count / 10) # smooth out the x axis
        newy = plotting.spline(bincenters, n, newx) # smooth out the y axis
        subplot.plot(newx, newy, color='r', linewidth=2) # smoothed line
        subplot.set_ylim(ymin=1)
        # title
        subplot.legend((), title=key, loc=1, frameon=False, prop={'size': 12})
        subplot.set_ylabel("Bout Count")
    subplot.set_xlabel("Seconds since last pellet")
    return fig


def _rhesus_minute_volumes_compare_categories(subplot, minutes, monkey_cat_one, monkey_cat_two, volume_summation):
    from utils import plotting

    assert monkey_cat_one in rhesus_drinkers.keys()
    assert monkey_cat_two in rhesus_drinkers.keys()
    a_data, a_count = volume_summation(monkey_cat_one, minutes)
    b_data, b_count = volume_summation(monkey_cat_two, minutes)
    assert a_data.keys() == b_data.keys()
    for x in a_data.keys():
        # lower, light drinkers
        _ld = a_data[x] / float(a_count)
        subplot.bar(x, _ld, width=.5, color='slateblue', edgecolor='none')
        # higher, heavy drinkers
        subplot.bar(x + .5, b_data[x] / float(b_count), width=.5, color='navy', edgecolor='none')
    #	patches.append(Rectangle((0,0),1,1, color=value))
    subplot.legend(
        [plotting.Rectangle((0, 0), 1, 1, color='slateblue'), plotting.Rectangle((0, 0), 1, 1, color='navy')],
        [monkey_cat_one, monkey_cat_two], title="Monkey Category", loc='upper left')
    subplot.set_xlim(xmax=max(b_data.keys()))
    # rotate the xaxis labels
    xticks = [x + .5 for x in a_data.keys() if x % 15 == 0]
    xtick_labels = ["%d" % x for x in b_data.keys() if x % 15 == 0]
    subplot.set_xticks(xticks)
    subplot.set_xticklabels(xtick_labels)
    return subplot


def rhesus_oa_discrete_minute_volumes_discrete_monkey_comparisons(monkey_cat_one, monkey_cat_two):
    def _oa_eev_volume_summation(monkey_category, minutes=20):
        data = defaultdict(lambda: 0)
        monkey_set = rhesus_drinkers_distinct[monkey_category]
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        for i in range(0, minutes):
            _eevs = eevs.filter(eev_pellet_time__gte=i * 60).filter(eev_pellet_time__lt=(i + 1) * 60)
            data[i] = _eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
        return data, len(monkey_set)

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    subplot = fig.add_subplot(main_gs[:, :])
    subplot = _rhesus_minute_volumes_compare_categories(subplot, 120, monkey_cat_one, monkey_cat_two,
                                                        _oa_eev_volume_summation)
    subplot.set_xlabel("Minutes since last pellet")
    subplot.set_title("Average intake by minute after pellet")
    subplot.set_ylabel("Average volume, ml per monkey")
    return fig


def rhesus_oa_pellettime_vs_gkg():
    def _oa_pelletvolume_perday_perkg(monkey_category):
        monkey_set = rhesus_drinkers_distinct[monkey_category]
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        x_data = list()
        y_data = list()
        for monkey in monkey_set:
            _mtds = mtds.filter(monkey=monkey).aggregate(Avg('mtd_mean_seconds_between_meals'), Avg('mtd_etoh_g_kg'))
            x_data.append(_mtds['mtd_etoh_g_kg__avg'])
            y_data.append(_mtds['mtd_mean_seconds_between_meals__avg'])
        return x_data, y_data

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.06, right=0.98, wspace=.08, hspace=0)
    subplot = fig.add_subplot(main_gs[:])
    subplot, handles, labels = _rhesus_category_scatterplot(subplot, _oa_pelletvolume_perday_perkg)
    subplot.legend(handles, labels, scatterpoints=1)
    subplot.set_title("Intake vs pellets")
    subplot.set_ylabel("Average duration between pellets (seconds), per day, per monkey")
    subplot.set_xlabel("Average ethanol intake (g/kg, per day, per monkey")
    return fig


def _rhesus_eev_by_hour_boxplot(subplot, x_values, monkey_category, data_collection_method, color, width=1,
                                extra_kwargs=None):
    extra_kwargs = extra_kwargs if extra_kwargs else {}
    data = list()
    for start_time in range(session_start, session_end, _1_hour):
        # Get all events that ever happened within this session hour
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(eev_session_time__gte=start_time).filter(
            eev_pellet_time__lt=start_time + _1_hour)
        # pass these events into the data collection method.
        # The data collection method is expected to produce a subset of boxplot-able data, filtered and normalized as the parent method intends
        #data.append(data_collection_method(eevs, monkey_category, **extra_kwargs))
        data = data_collection_method('',
                                      monkey_category) # when using _load_from_file_Hourly_eev_gkg_summations(), uncomment this line, comment the forloop above
    bp = subplot.boxplot(data, positions=x_values, widths=width)
    for key in bp.keys():
        if key != 'medians':
            pyplot.setp(bp[key], color=color)
    pyplot.setp(bp['boxes'], linewidth=2)
    pyplot.setp(bp['whiskers'], linewidth=2)

    return subplot


def rhesus_hourly_gkg_boxplot_by_category(fig_size=plotting.HISTOGRAM_FIG_SIZE):
    def _hourly_eev_gkg_summation(eevs, monkey_category):
        """
		This method will return a list of each monkey's gkg consumed within the events passed in (eevs), for each monkey in monkey_category
		ex.
		[3.2, 1.4, 5.7, 3.5, 2.9]
		"""
        events_gkg = list()
        for monkey in rhesus_drinkers_distinct[monkey_category]:
            # first, get the subset of events associated with this monkey
            _eevs = eevs.filter(monkey=monkey)
            # Next, get this monkey's average OPEN ACCESS weight
            mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=eevs[0].monkey)
            avg_weight = mtds.aggregate(Avg('mtd_weight'))['mtd_weight__avg']
            # to get g/kg, aggregate the volume consumed, multiply by .04 and divide by weight
            gkg = _eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum'] * .04 / avg_weight
            events_gkg.append(gkg)
        return events_gkg

    def _load_from_file_hourly_eev_gkg_summation(eevs, monkey_category):
        import json

        f = open("utils/DATA/json/%s.json" % monkey_category, 'r')
        json_string = f.readline()
        data = json.loads(json_string)
        return data

    fig = pyplot.figure(figsize=fig_size, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.06, right=0.98, wspace=.08, hspace=0)
    subplot = fig.add_subplot(main_gs[:, :])

    gap_factor = 2
    width = .6 * _1_hour / len(rhesus_keys)
    offset = _1_hour / len(rhesus_keys)
    for index, mky_cat in enumerate(rhesus_keys):
        x_values = numpy.arange(index * offset, _22_hour * gap_factor, _1_hour * gap_factor)
        #		subplot = _rhesus_eev_by_hour_boxplot(subplot, x_values, mky_cat, _hourly_eev_gkg_summation, width=width, color=rhesus_colors[mky_cat])
        subplot = _rhesus_eev_by_hour_boxplot(subplot, x_values, mky_cat, _load_from_file_hourly_eev_gkg_summation,
                                              width=width, color=rhesus_colors[mky_cat])

    # Makes all boxplots fully visible
    subplot.set_xlim(xmin=-.5 * _1_hour, xmax=_22_hour * gap_factor)
    # shades the graph gray for light-out hours
    subplot.axvspan(gap_factor * lights_out - width * gap_factor, gap_factor * lights_on - width * gap_factor,
                    color='black', alpha=.2, zorder=-100)

    # defines X labels
    x_labels = ['hr %d' % i for i in range(1, 23)]
    # centers xticks, so labels are place in the middle of the hour, rotated
    new_xticks = numpy.arange(0, _22_hour * gap_factor, _1_hour * gap_factor)
    subplot.set_xticks(new_xticks)
    xtickNames = pyplot.setp(subplot, xticklabels=x_labels)
    pyplot.setp(xtickNames, rotation=45)

    # Create legend
    handles = list()
    labels = list()
    for key in rhesus_keys:
        color = rhesus_colors[key]
        wrect = patches.Rectangle((0, 0), 1, 1, fc=color)
        handles.append(wrect)
        labels.append(key)

    tick_size = 20
    title_size = 26
    label_size = 24
    legend_size = 20
    subplot.legend(handles, labels, loc='upper right', prop={'size': legend_size})
    subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
    subplot.set_title("Hourly g/kg, by category", size=title_size)
    subplot.set_ylabel("g/kg", size=label_size)
    subplot.set_xlabel("Hour of session", size=label_size)
    return fig


def _rhesus_gkg_age_mtd_general(subplot, phase, gkg_onset, mtd_callable_xvalue_generator): # phase = 0-2
    oa_phases = ['', 'drinking_experiment__dex_date__lte', 'drinking_experiment__dex_date__gt']

    label = ''
    for key in rhesus_keys:
        x = list()
        y = list()
        for monkey_pk in rhesus_drinkers_distinct[key]:
            monkey = Monkey.objects.get(pk=monkey_pk)
            monkey_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            min_gkg_onset_date =
            monkey_mtds.filter(mtd_etoh_g_kg__gte=gkg_onset).aggregate(Min('drinking_experiment__dex_date'))[
                'drinking_experiment__dex_date__min']
            if not min_gkg_onset_date:
                continue
            age_at_gkg_onset = (min_gkg_onset_date - monkey.mky_birthdate).days / 365.25
            if phase:
                monkey_mtds = monkey_mtds.filter(**{oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})
            y.append(age_at_gkg_onset)
            value, label = mtd_callable_xvalue_generator(monkey_mtds)
            x.append(value)
        color = rhesus_colors[key]
        subplot.scatter(x, y, label=key, color=color, s=150)
        create_convex_hull_polygon(subplot, x, y, color)
    return subplot, label


def rhesus_gkg_onset_age_category(phase, gkg_onset):
    assert 0 <= phase <= 2
    titles = ["Open Access, 12 months", "Open Access, 1st Six Months", "Open Access, 2nd Six Months"]
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(titles[phase])
    main_plot.set_ylabel("Age at first %d gkg consumption" % gkg_onset)
    main_plot, label = _rhesus_gkg_age_mtd_general(main_plot, phase, gkg_onset, _mtd_call_gkg_etoh)
    main_plot.set_xlabel(label)
    main_plot.legend(loc=0, scatterpoints=1)
    return fig


def _rhesus_bec_age_mtd_general(subplot, phase, bec_onset, mtd_callable_xvalue_generator): # phase = 0-2
    mtd_oa_phases = ['', 'drinking_experiment__dex_date__lte', 'drinking_experiment__dex_date__gt']
    bec_oa_phases = ['', 'bec_collect_date__lte', 'bec_collect_date__gt']

    label = ''
    for key in rhesus_keys:
        x = list()
        y = list()
        for monkey_pk in rhesus_drinkers_distinct[key]:
            monkey = Monkey.objects.get(pk=monkey_pk)
            monkey_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            monkey_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            if phase:
                monkey_becs = monkey_becs.filter(**{mtd_oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})
                monkey_mtds = monkey_mtds.filter(**{bec_oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})

            min_bec_onset_date = monkey_becs.filter(bec_mg_pct__gte=bec_onset).aggregate(Min('bec_collect_date'))[
                'bec_collect_date__min']
            if not min_bec_onset_date:
                continue
            age_at_bec_onset = (min_bec_onset_date.date() - monkey.mky_birthdate).days / 365.25
            y.append(age_at_bec_onset)

            value, label = mtd_callable_xvalue_generator(monkey_mtds)
            x.append(value)
        color = rhesus_colors[key]
        subplot.scatter(x, y, label=key, color=color, s=150)
        if len(x) > 1:
            create_convex_hull_polygon(subplot, x, y, color)
    return subplot, label


def rhesus_bec_onset_age_category(phase, bec_onset):
    assert 0 <= phase <= 2
    titles = ["Open Access, 12 months", "Open Access, 1st Six Months", "Open Access, 2nd Six Months"]
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(titles[phase])
    main_plot.set_ylabel("Age at first %d bec reading" % bec_onset)
    main_plot, label = _rhesus_bec_age_mtd_general(main_plot, phase, bec_onset, _mtd_call_gkg_etoh)
    main_plot.set_xlabel(label)
    main_plot.legend(loc=0, scatterpoints=1)
    return fig


def _rhesus_bec_age_mtd_regression(phase, bec_onset, mtd_callable_xvalue_generator): # phase = 0-2
    mtd_oa_phases = ['', 'drinking_experiment__dex_date__lte', 'drinking_experiment__dex_date__gt']
    bec_oa_phases = ['', 'bec_collect_date__lte', 'bec_collect_date__gt']

    x = list()
    y = list()
    label = ''
    for key in rhesus_keys:
        for monkey_pk in rhesus_drinkers_distinct[key]:
            monkey = Monkey.objects.get(pk=monkey_pk)
            monkey_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            monkey_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            if phase:
                monkey_becs = monkey_becs.filter(**{mtd_oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})
                monkey_mtds = monkey_mtds.filter(**{bec_oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})

            min_bec_onset_date = monkey_becs.filter(bec_mg_pct__gte=bec_onset).aggregate(Min('bec_collect_date'))[
                'bec_collect_date__min']
            if not min_bec_onset_date:
                continue
            age_at_bec_onset = (min_bec_onset_date.date() - monkey.mky_birthdate).days / 365.25
            y.append(age_at_bec_onset)

            value, label = mtd_callable_xvalue_generator(monkey_mtds)
            x.append(value)
    x = numpy.array(x)
    y = numpy.array(y)
    regression_data = stats.linregress(x, y) # slope, intercept, r_value, p_value, std_err = regression_data
    regression = (x, regression_data)
    return regression, label


def _rhesus_bec_age_mtd_regression_centroids(phase, bec_onset, mtd_callable_xvalue_generator): # phase = 0-2
    mtd_oa_phases = ['', 'drinking_experiment__dex_date__lte', 'drinking_experiment__dex_date__gt']
    bec_oa_phases = ['', 'bec_collect_date__lte', 'bec_collect_date__gt']

    centroid_x = list()
    centroid_y = list()
    label = ''
    for key in rhesus_keys:
        data_x = list()
        data_y = list()
        for monkey_pk in rhesus_drinkers_distinct[key]:
            monkey = Monkey.objects.get(pk=monkey_pk)
            monkey_becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            monkey_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
            if phase:
                monkey_becs = monkey_becs.filter(**{mtd_oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})
                monkey_mtds = monkey_mtds.filter(**{bec_oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})

            min_bec_onset_date = monkey_becs.filter(bec_mg_pct__gte=bec_onset).aggregate(Min('bec_collect_date'))[
                'bec_collect_date__min']
            if not min_bec_onset_date:
                continue
            age_at_bec_onset = (min_bec_onset_date.date() - monkey.mky_birthdate).days / 365.25
            data_y.append(age_at_bec_onset)

            value, label = mtd_callable_xvalue_generator(monkey_mtds)
            data_x.append(value)
        try:
            res, idx = cluster.vq.kmeans2(numpy.array(zip(data_x, data_y)), 1)
        except Exception as e:
            print e
            continue
        centroid_x.append(res[:, 0][0])
        centroid_y.append(res[:, 1][0])
    x = numpy.array(centroid_x)
    y = numpy.array(centroid_y)

    regression_data = stats.linregress(x, y) # slope, intercept, r_value, p_value, std_err = regression_data
    regression = (x, regression_data)
    return regression, label


def rhesus_bec_onset_age_category_regressions(phase):
    assert 0 <= phase <= 2
    titles = ["BEC Regression Comparison, Open Access, 12 months",
              "BEC Regression Comparison, Open Access, 1st Six Months",
              "BEC Regression Comparison, Open Access, 2nd Six Months"]
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(titles[phase])
    main_plot.set_ylabel("Age at first bec reading")

    cmap = plotting.get_cmap('jet')
    bec_values = range(40, 260, 20)
    bec_colors = dict()
    for idx, bec in enumerate(bec_values):
        bec_colors[bec] = cmap(idx / (len(bec_values) - 1.))
    xlabel = ''
    for bec_onset in range(40, 260, 20):
        regression, xlabel = _rhesus_bec_age_mtd_regression(phase, bec_onset, _mtd_call_gkg_etoh)
        x_values, regression_data = regression
        slope, intercept, r_value, p_value, std_err = regression_data
        reg_label = "BEC Onset=%d, Fit: r=%f, p=%f" % (bec_onset, r_value, p_value)
        main_plot.plot(x_values, x_values * slope + intercept, color=bec_colors[bec_onset], label=reg_label,
                       linewidth=5, alpha=.7)

    main_plot.set_xlabel(xlabel)
    main_plot.legend(loc=0, scatterpoints=1)
    return fig


def rhesus_bec_onset_age_category_regressions_centroids(phase):
    assert 0 <= phase <= 2
    titles = ["BEC Centroid Regression Comparison, Open Access, 12 months",
              "BEC Centroid Regression Comparison, Open Access, 1st Six Months",
              "BEC Centroid Regression Comparison, Open Access, 2nd Six Months"]
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(titles[phase])
    main_plot.set_ylabel("Age at first bec reading")

    cmap = plotting.get_cmap('jet')
    bec_values = range(40, 260, 20)
    bec_colors = dict()
    for idx, bec in enumerate(bec_values):
        bec_colors[bec] = cmap(idx / (len(bec_values) - 1.))
    xlabel = ''
    for bec_onset in range(40, 260, 20):
        regression, xlabel = _rhesus_bec_age_mtd_regression_centroids(phase, bec_onset, _mtd_call_gkg_etoh)
        x_values, regression_data = regression
        slope, intercept, r_value, p_value, std_err = regression_data
        reg_label = "BEC Onset=%d, Fit: r=%f, p=%f" % (bec_onset, r_value, p_value)
        main_plot.plot(x_values, x_values * slope + intercept, color=bec_colors[bec_onset], label=reg_label,
                       linewidth=5, alpha=.7)

    main_plot.set_xlabel(xlabel)
    main_plot.legend(loc=0, scatterpoints=1)
    return fig


def rhesus_OA_bec_pellettime_scatter(phase): # phase = 0-2
    oa_phases = ['', 'bec_collect_date__lte', 'bec_collect_date__gt']

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title("BEC vs Time Between Pellets")
    main_plot.set_xlabel("BEC")
    main_plot.set_ylabel("Daily Average Hours Between Pellets")

    for key in rhesus_keys:
        x_axis = list()
        y_axis = list()
        for monkey_pk in rhesus_drinkers_distinct[key]:
            monkey = Monkey.objects.get(pk=monkey_pk)
            becs = MonkeyBEC.objects.OA().filter(monkey=monkey_pk).order_by('pk')
            if phase:
                becs = becs.filter(**{oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})
            seconds = numpy.array(becs.values_list('mtd__mtd_mean_seconds_between_meals', flat=True))
            try:
            #				y_axis.extend([(s-sample_time[stage])/(60*60) for s in seconds]) # time between end of drinking and sample taken
                y_axis.extend(seconds / (60 * 60)) # time between end of drinking and sample taken
            except:
                print "skipping monkey %d" % monkey.pk
                continue
            x_axis.extend(becs.values_list('bec_mg_pct', flat=True))

        color = rhesus_colors[key]
        main_plot.scatter(x_axis, y_axis, label=key, color=color, s=15, alpha=.1)
        create_convex_hull_polygon(main_plot, x_axis, y_axis, color)
        try:
            res, idx = cluster.vq.kmeans2(numpy.array(zip(x_axis, y_axis)), 1)
            main_plot.scatter(res[:, 0][0], res[:, 1][0], color=color, marker=rhesus_markers[key], alpha=1, s=300,
                              label="%s Centroid" % key, zorder=5)
        except LinAlgError as e: # I'm not sure what about kmeans2() causes this, or how to avoid it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass
        except ValueError as e: # "Input has 0 items" has occurred
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass

    main_plot.legend(loc=9, ncol=4, scatterpoints=1)
    main_plot.set_xlim(xmin=0)
    main_plot.set_ylim(ymin=0)
    return fig


def rhesus_OA_bec_pelletcount_scatter(phase): # phase = 0-2
    oa_phases = ['', 'bec_collect_date__lte', 'bec_collect_date__gt']

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title("BEC vs Total Pellets")
    main_plot.set_xlabel("BEC")
    main_plot.set_ylabel("Daily Total Pellets")

    for key in rhesus_keys:
        x_axis = list()
        y_axis = list()
        for monkey_pk in rhesus_drinkers_distinct[key]:
            monkey = Monkey.objects.get(pk=monkey_pk)
            becs = MonkeyBEC.objects.OA().filter(monkey=monkey_pk).order_by('pk')
            if phase:
                becs = becs.filter(**{oa_phases[phase]: rhesus_1st_oa_end[monkey.cohort.pk]})
            pellet_count = numpy.array(becs.values_list('mtd__mtd_total_pellets', flat=True))
            try:
                y_axis.extend(pellet_count)
            except:
                print "skipping monkey %d" % monkey.pk
                continue
            x_axis.extend(becs.values_list('bec_mg_pct', flat=True))

        color = rhesus_colors[key]
        main_plot.scatter(x_axis, y_axis, label=key, color=color, s=15, alpha=.1)
        #		create_convex_hull_polygon(main_plot, x_axis, y_axis, color)
        try:
            res, idx = cluster.vq.kmeans2(numpy.array(zip(x_axis, y_axis)), 1)
            main_plot.scatter(res[:, 0][0], res[:, 1][0], color=color, marker=rhesus_markers[key], alpha=1, s=300,
                              label="%s Centroid" % key, zorder=5)
        except LinAlgError as e: # I'm not sure what about kmeans2() causes this, or how to avoid it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass
        except ValueError as e: # "Input has 0 items" has occurred
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass

    main_plot.legend(loc=9, ncol=4, scatterpoints=1)
    main_plot.set_xlim(xmin=0)
    main_plot.set_ylim(ymin=0)
    return fig


def _rhesus_etoh_max_bout_cumsum(subplot):
#	VHD_LD = rhesus_drinkers_distinct['VHD']
#	VHD_LD.extend(rhesus_drinkers_distinct['LD'])
#	mkys = Monkey.objects.filter(pk__in=VHD_LD)
    mkys = Monkey.objects.filter(pk__in=all_rhesus_drinkers)

    subplot.set_title("Induction St. 3 Cumulative Max Bout EtOH Intake for cohorts 4/5/7a/7b")
    subplot.set_ylabel("Volume EtOH / Monkey Weight, ml/kg")

    mky_ymax = dict()
    for idx, m in enumerate(mkys):
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m, drinking_experiment__dex_type="Induction").exclude(
            mtd_max_bout_vol=None).order_by('drinking_experiment__dex_date')
        mtds = mtds.filter(mtd_etoh_g_kg__gte=1.4).filter(mtd_etoh_g_kg__lte=1.6)
        if not mtds.count():
            continue
        volumes = numpy.array(mtds.values_list('mtd_max_bout_vol', flat=True))
        weights = numpy.array(mtds.values_list('mtd_weight', flat=True))
        vw_div = volumes / weights
        yaxis = numpy.cumsum(vw_div)
        mky_ymax[m] = yaxis[-1]
        xaxis = numpy.arange(mtds.values_list('drinking_experiment__dex_date', flat=True).distinct().count())
        subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=rhesus_monkey_colors[m.pk], label=str(m.pk))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    if not len(mky_ymax.values()):
        raise Exception("no MTDs found")
    return subplot, mky_ymax


def _rhesus_etoh_horibar_ltgkg(subplot, mky_ymax):
    subplot.set_title("Lifetime EtOH Intake for cohorts 4/5/7a/7b")
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
        bar_colors.append(rhesus_monkey_colors[mky.pk])
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
    subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot


def _rhesus_etoh_horibar_3gkg(subplot, mky_ymax):
    subplot.set_title("# days over 3 g/kg")

    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_3widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        bar_3widths.append(mtds.filter(mtd_etoh_g_kg__gt=3).count())
        bar_colors.append(rhesus_monkey_colors[mky.pk])
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
    subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot


def _rhesus_etoh_horibar_4gkg(subplot, mky_ymax):
    subplot.set_title("# days over 4 g/kg")
    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))
    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_4widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        bar_4widths.append(mtds.filter(mtd_etoh_g_kg__gt=4).count())
        bar_colors.append(rhesus_monkey_colors[mky.pk])
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
    subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot


def rhesus_etoh_max_bout_cumsum_horibar_3gkg():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax = _rhesus_etoh_max_bout_cumsum(line_subplot)
    except:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _rhesus_etoh_horibar_3gkg(bar_subplot, mky_ymax)
    return fig, None


def rhesus_etoh_max_bout_cumsum_horibar_4gkg():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax = _rhesus_etoh_max_bout_cumsum(line_subplot)
    except:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _rhesus_etoh_horibar_4gkg(bar_subplot, mky_ymax)
    return fig, None


def rhesus_etoh_max_bout_cumsum_horibar_ltgkg():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax = _rhesus_etoh_max_bout_cumsum(line_subplot)
    except:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _rhesus_etoh_horibar_ltgkg(bar_subplot, mky_ymax)
    return fig, None


def rhesus_pellet_time_histogram():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle("Meal Distribution")
    gs = gridspec.GridSpec(2, 2)
    gs.update(left=0.05, right=0.985, wspace=.05, hspace=0.08)

    subplot = fig.add_subplot(gs[:, :])
    eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=all_rhesus_drinkers)
    eevs = eevs.filter(eev_event_type=ExperimentEventType.Pellet)
    #	eevs = eevs.exclude(eev_pellet_time__lte=1.95*60*60)
    data = eevs.values_list('eev_pellet_time', flat=True)

    data = numpy.array(data)
    data = data / 60.
    bin_edges = range(min(data), max(data), 5)
    subplot.hist(data, bins=bin_edges, normed=False, histtype='bar', log=True, color='slateblue')
    subplot.set_xlim(xmin=0)
    subplot.set_ylabel("Meal Count")
    subplot.set_xlabel("Time Since Last Meal")
    return fig


def rhesus_pellet_time_histogram_grid():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle("Meal Distribution")
    gs = gridspec.GridSpec(2, 2)
    gs.update(left=0.05, right=0.985, wspace=.05, hspace=0.08)

    subplot = None
    for grid_index, rhesus_key in enumerate(rhesus_keys):
        subplot = fig.add_subplot(gs[grid_index], sharex=subplot)
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=rhesus_drinkers_distinct[rhesus_key])
        eevs = eevs.filter(eev_event_type=ExperimentEventType.Pellet)
        #		eevs = eevs.exclude(eev_pellet_time__lte=1.95*60*60)
        data = eevs.values_list('eev_pellet_time', flat=True)

        data = numpy.array(data)
        data /= 60.
        bin_edges = range(min(data), max(data), 5)
        subplot.hist(data, bins=bin_edges, normed=False, histtype='bar', log=True, color=rhesus_colors[rhesus_key])
        subplot.legend((), title=rhesus_key, loc=1, frameon=False, prop={'size': 12})
        #		subplot.set_xlim(xmin=1.95*60)
        subplot.set_xlim(xmin=0)
        if grid_index % 2:
            subplot.set_yticklabels([])
        else:
            subplot.set_ylabel("Meal Count")
        if grid_index < 2:
            subplot.set_xticklabels([])
        else:
            subplot.set_xlabel("Time Since Last Meal")
    return fig


def rhesus_etoh_pellettime_bec():
    size_min = plotting.DEFAULT_CIRCLE_MIN
    size_scale = plotting.DEFAULT_CIRCLE_MAX * 2 - size_min

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    scatter_subplot = fig.add_subplot(gs[:, :])

    all_x = list()
    all_y = list()
    all_size = list()
    max_size = 0
    for key in rhesus_keys:
        monkeys = Monkey.objects.filter(pk__in=rhesus_drinkers_distinct[key])
        x_values = list()
        y_values = list()
        size_values = list()
        for mky in monkeys:
            _mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).aggregate(
                Avg('mtd_mean_seconds_between_meals'), Avg('mtd_etoh_g_kg'))
            _becs = MonkeyBEC.objects.OA().filter(monkey=mky).aggregate(Avg('bec_mg_pct'))
            x_values.append(_mtds['mtd_etoh_g_kg__avg'])
            y_values.append(_mtds['mtd_mean_seconds_between_meals__avg'])
            size = _becs['bec_mg_pct__avg']
            size_values.append(size)
            max_size = max(size, max_size)
        all_x.append(x_values)
        all_y.append(y_values)
        all_size.append(size_values)
    for key, x_values, y_values, size_values in zip(rhesus_keys, all_x, all_y, all_size):
        rescaled_sizes = [(b / max_size) * size_scale + size_min for b in
                          size_values] # exaggerated and rescaled, so that circles will be in range (size_min, size_scale)
        scatter_subplot.scatter(x_values, y_values, c=rhesus_colors[key], s=rescaled_sizes, alpha=1, label=key)
        create_convex_hull_polygon(scatter_subplot, x_values, y_values, rhesus_colors[key])

    all_x_values = numpy.hstack(all_x)
    all_y_values = numpy.hstack(all_y)
    slope, intercept, r_value, p_value, std_err = stats.linregress(all_x_values, all_y_values)
    reg_label = "Fit: r=%f, p=%f" % (r_value, p_value)
    scatter_subplot.plot(all_x_values, all_x_values * slope + intercept, color='black', label=reg_label)
    scatter_subplot.legend(loc=0, scatterpoints=1)

    scatter_subplot.set_ylabel("Mean Seconds Between Meals, per day, per monkey")
    scatter_subplot.set_xlabel("Ethanol Intake, in g/kg, per day, per monkey")

    # size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = size_scale / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = max_size / (len(y) - 1)
    size_labels = [int(round(i * m)) for i in range(1, len(y))] # labels in the range as number of bouts
    size_labels.insert(0, "1")
    size_labels.insert(0, "")
    size_labels.append("")

    size_legend_subplot = fig.add_subplot(931)
    size_legend_subplot.set_position((0.06, .90, .3, .06))
    size_legend_subplot.scatter(x, y, s=size, alpha=0.4)
    size_legend_subplot.set_xlabel("Average BEC, mg percent")
    size_legend_subplot.yaxis.set_major_locator(plotting.NullLocator())
    pyplot.setp(size_legend_subplot, xticklabels=size_labels)
    #
    return fig


def rhesus_etoh_pellettime_pctetohmeal():
    size_min = plotting.DEFAULT_CIRCLE_MIN
    size_scale = plotting.DEFAULT_CIRCLE_MAX * 2 - size_min

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    scatter_subplot = fig.add_subplot(gs[:, :])

    all_x = list()
    all_y = list()
    all_size = list()
    max_size = 0
    for key in rhesus_keys:
        monkeys = Monkey.objects.filter(pk__in=rhesus_drinkers_distinct[key])
        x_values = list()
        y_values = list()
        size_values = list()
        for mky in monkeys:
            _mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).aggregate(
                Avg('mtd_mean_seconds_between_meals'), Avg('mtd_etoh_g_kg'))
            _eevs = ExperimentEvent.objects.OA().filter(monkey=mky).exclude(eev_pct_etoh=None).aggregate(
                Avg('eev_pct_etoh'))
            x_values.append(_mtds['mtd_etoh_g_kg__avg'])
            y_values.append(_mtds['mtd_mean_seconds_between_meals__avg'])
            size = _eevs['eev_pct_etoh__avg']
            size_values.append(size)
            max_size = max(size, max_size)
        all_x.append(x_values)
        all_y.append(y_values)
        all_size.append(size_values)
    for key, x_values, y_values, size_values in zip(rhesus_keys, all_x, all_y, all_size):
        rescaled_sizes = [(b / max_size) * size_scale + size_min for b in
                          size_values] # exaggerated and rescaled, so that circles will be in range (size_min, size_scale)
        scatter_subplot.scatter(x_values, y_values, c=rhesus_colors[key], s=rescaled_sizes, alpha=1, label=key)
        create_convex_hull_polygon(scatter_subplot, x_values, y_values, rhesus_colors[key])

    all_x_values = numpy.hstack(all_x)
    all_y_values = numpy.hstack(all_y)
    slope, intercept, r_value, p_value, std_err = stats.linregress(all_x_values, all_y_values)
    reg_label = "Fit: r=%f, p=%f" % (r_value, p_value)
    scatter_subplot.plot(all_x_values, all_x_values * slope + intercept, color='black', label=reg_label)
    scatter_subplot.legend(loc=0, scatterpoints=1)

    scatter_subplot.set_ylabel("Mean Seconds Between Meals, per day, per monkey")
    scatter_subplot.set_xlabel("Ethanol Intake, in g/kg, per day, per monkey")

    # size legend
    x = numpy.array(range(1, 6))
    y = numpy.array([1, 1, 1, 1, 1])

    size_m = size_scale / (len(y) - 1)
    size = [int(round(i * size_m)) + size_min for i in
            range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
    size.insert(0, 1 + size_min)
    size = numpy.array(size)

    m = max_size / (len(y) - 1)
    size_labels = ["%.02f" % (100 * m * i) for i in range(1, len(y))] # labels in the range as number of bouts
    size_labels.insert(0, "0")
    size_labels.insert(0, "")
    size_labels.append("")

    size_legend_subplot = fig.add_subplot(931)
    size_legend_subplot.set_position((0.06, .90, .3, .06))
    size_legend_subplot.scatter(x, y, s=size, alpha=0.4)
    size_legend_subplot.set_xlabel("Average Percent of EtOH at meal pellet")
    size_legend_subplot.yaxis.set_major_locator(plotting.NullLocator())
    pyplot.setp(size_legend_subplot, xticklabels=size_labels)
    #
    return fig


def rhesus_pellet_sessiontime_distribution():
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle("Pellet Distribution")
    gs = gridspec.GridSpec(4, 1)
    gs.update(left=0.05, right=0.985, wspace=.05, hspace=0.02)
    common_subplot = fig.add_subplot(gs[:, :])

    subplot = None
    for grid_index, rhesus_key in enumerate(rhesus_keys):
        subplot = fig.add_subplot(gs[grid_index], sharex=subplot, sharey=subplot)
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=rhesus_drinkers_distinct[rhesus_key])
        eevs = eevs.filter(eev_event_type=ExperimentEventType.Pellet)
        eevs = eevs.filter(eev_session_time__lte=8 * 60 * 60)
        data = eevs.values_list('eev_session_time', flat=True)

        data = numpy.array(data)
        data /= 60.
        bin_edges = range(min(data), max(data), 5)
        subplot.hist(data, bins=bin_edges, normed=False, histtype='bar', log=True, color=rhesus_colors[rhesus_key])
        subplot.legend((), title=rhesus_key, loc=1, frameon=False, prop={'size': 12})
        pyplot.setp(subplot.get_xticklabels(), visible=False)
    pyplot.setp(subplot.get_xticklabels(), visible=True)
    subplot.set_yticks([10 ** i for i in range(6) if i % 2])
    subplot.set_xticks([i for i in range(0, 9 * 60, 60)])
    subplot.set_xticklabels([str(i) for i in range(9)])
    subplot.set_xlim(xmin=0, xmax=8 * 60)

    common_subplot.spines['top'].set_color('none')
    common_subplot.spines['bottom'].set_color('none')
    common_subplot.spines['left'].set_color('none')
    common_subplot.spines['right'].set_color('none')
    common_subplot.patch.set_alpha(0)
    common_subplot.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
    common_subplot.set_ylabel("Pellet Count")
    common_subplot.set_xlabel("Session Time")
    return fig


def rhesus_pellet_sessiontime_percent_distribution():
    def damnit_this_sucks(eevs):
        list_of_percents = list()
        monkeys = eevs.values_list('monkey', flat=True).distinct()
        dates = eevs.dates('eev_occurred', 'day').distinct()
        for date in dates:
            for monkey in monkeys:
                pellet_count = eevs.filter(eev_occurred__year=date.year, eev_occurred__month=date.month,
                                           eev_occurred__day=date.day, monkey=monkey).count()
                if pellet_count:
                    mtd = MonkeyToDrinkingExperiment.objects.get(monkey=monkey, drinking_experiment__dex_date=date)
                    day_pellet_count = mtd.mtd_total_pellets
                    percent = float(pellet_count) / day_pellet_count
                    list_of_percents.append(percent)
        return list_of_percents

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle("Pellet Distribution")
    gs = gridspec.GridSpec(4, 1)
    gs.update(left=0.05, right=0.985, wspace=.05, hspace=0.02)
    common_subplot = fig.add_subplot(gs[:, :])

    subplot = None
    for grid_index, rhesus_key in enumerate(rhesus_keys):
        subplot = fig.add_subplot(gs[grid_index], sharex=subplot, sharey=subplot)
        eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=rhesus_drinkers_distinct[rhesus_key])
        eevs = eevs.filter(eev_event_type=ExperimentEventType.Pellet)
        eevs = eevs.filter(eev_session_time__lte=8 * 60 * 60)

        bin_edges = range(0, 8 * 60 * 60, 5 * 60)
        all_data = dict()
        for start in bin_edges:
            all_data[start] = damnit_this_sucks(
                eevs.filter(eev_session_time__gte=start).filter(eev_session_time__lt=start + 5 * 60))

        x_data = list()
        y_data = list()
        for edge, percents in all_data.iteritems():
            x_data.append(edge)
            y_data.append(numpy.mean(percents))
        subplot.bar(x_data, y_data, width=5 * 60, color=rhesus_colors[rhesus_key])
        #		subplot.hist(data, bins=bin_edges, normed=False, histtype='bar', log=True, color=rhesus_colors[rhesus_key])
        subplot.legend((), title=rhesus_key, loc=1, frameon=False, prop={'size': 12})
        pyplot.setp(subplot.get_xticklabels(), visible=False)
    pyplot.setp(subplot.get_xticklabels(), visible=True)
    subplot.set_yticks([10 ** i for i in range(6) if i % 2])
    subplot.set_xticks([i for i in range(0, 9 * 60, 60)])
    subplot.set_xticklabels([str(i) for i in range(9)])
    subplot.set_xlim(xmin=0, xmax=8 * 60)

    common_subplot.spines['top'].set_color('none')
    common_subplot.spines['bottom'].set_color('none')
    common_subplot.spines['left'].set_color('none')
    common_subplot.spines['right'].set_color('none')
    common_subplot.patch.set_alpha(0)
    common_subplot.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
    common_subplot.set_ylabel("Average Percent of Pellet Intake")
    common_subplot.set_xlabel("Session Time")
    return fig

#---
#plot
def confederate_boxplots(confederates, bout_column):
    from utils import plotting

    confeds = list()
    mky = None
    for c in confederates:
        if not isinstance(c, Monkey):
            try:
                mky = Monkey.objects.get(pk=c)
            except Monkey.DoesNotExist:
                try:
                    mky = Monkey.objects.get(mky_real_id=c)
                except Monkey.DoesNotExist:
                    print("That's not a valid monkey:  %s" % str(c))
                    return False, False
        else:
            mky = c
        confeds.append(mky)
    if not mky:
        return False, False
    cohort = mky.cohort
    monkeys = cohort.monkey_set.exclude(mky_drinking=False).exclude(pk__in=[c.pk for c in confeds])

    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.12, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])

    cohort_data = list()
    confed_data = list()
    monkey_data = list()
    minutes = numpy.array([0, 1, 5, 10, 15, 20])
    min_oa_date =
    MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().aggregate(Min('drinking_experiment__dex_date'))[
        'drinking_experiment__dex_date__min']
    cbts = CohortBout.objects.filter(cohort=cohort).filter(dex_date__gte=min_oa_date)
    for _min in minutes:
        _cbts = cbts.filter(cbt_pellet_elapsed_time_since_last__gte=_min * 60)
        cohort_bouts = _cbts.values_list('ebt_set', flat=True).distinct()

        confed_bouts = _cbts.filter(ebt_set__mtd__monkey__in=confeds).values_list('ebt_set', flat=True).distinct()
        print "confed_count = %d" % confed_bouts.count()
        monkey_bouts = _cbts.filter(ebt_set__mtd__monkey__in=monkeys).values_list('ebt_set', flat=True).distinct()
        print "monkey_count = %d" % monkey_bouts.count()
        cohort_data.append(ExperimentBout.objects.filter(pk__in=cohort_bouts).values_list(bout_column, flat=True))
        confed_data.append(ExperimentBout.objects.filter(pk__in=confed_bouts).values_list(bout_column, flat=True))
        monkey_data.append(ExperimentBout.objects.filter(pk__in=monkey_bouts).values_list(bout_column, flat=True))

    offset = 4
    cohort_pos = numpy.arange(offset, offset * len(minutes) + offset, offset)
    monkey_pos = cohort_pos + 1
    confed_pos = monkey_pos + 1

    bp = main_plot.boxplot(confed_data, positions=cohort_pos)
    pyplot.setp(bp['boxes'], linewidth=1, color='g')
    pyplot.setp(bp['whiskers'], linewidth=1, color='g')
    pyplot.setp(bp['fliers'], color='g', marker='+')

    bp = main_plot.boxplot(monkey_data, positions=monkey_pos)

    bp = main_plot.boxplot(confed_data, positions=confed_pos)
    pyplot.setp(bp['boxes'], linewidth=1, color='r')
    pyplot.setp(bp['whiskers'], linewidth=1, color='r')
    pyplot.setp(bp['fliers'], color='red', marker='+')

    main_plot.set_yscale('log')
    main_plot.set_xlim(xmin=offset - .5)
    ymin, ymax = main_plot.get_ylim()
    y_values = list()
    for x in numpy.arange(ymax):
        if x * 10 ** x <= ymax:
            y_values.append(x * 10 ** x)
        else:
            break
    y_values.append(ymax)
    y_values = numpy.array(y_values)
    main_plot.set_title("%s, Open Access Bout vs Time since last pellet" % str(cohort))
    main_plot.set_xticks(monkey_pos)
    main_plot.set_xticklabels(minutes * 60)
    main_plot.set_yticklabels(y_values)
    main_plot.set_xlabel("Minimum Seconds Since Pellet")
    _label = "Bout Length" if bout_column == 'ebt_length' else ''
    _label = "Bout Volume" if not _label and bout_column == 'ebt_volume' else ''
    main_plot.set_ylabel("%s, in seconds" % _label)
    return fig

#data
def return_confeds(pk, minutes, nighttime_only=False):
    return apriori.get_confederate_groups(pk, minutes, min_confidence=0, nighttime_only=nighttime_only)

#analyze datas
def analyze_MBA(pk, minutes, nighttime_only=False):
    confeds = return_confeds(pk, minutes, nighttime_only=nighttime_only)
    monkey_scores = dict()
    weight_cause = 1
    weight_effect = weight_cause * 1

    for support in confeds.keys():
        data = confeds[support]
        for cause, effect, confidence in data:
            for mky in cause:
                try:
                    monkey_scores[mky] += weight_cause * float(confidence) * float(support)
                except KeyError:
                    monkey_scores[mky] = weight_cause * float(confidence) * float(support)
            for mky in effect:
                try:
                    monkey_scores[mky] += weight_effect * float(confidence) * float(support)
                except KeyError:
                    monkey_scores[mky] = weight_effect * float(confidence) * float(support)
    return monkey_scores

#build boxplots
def rhesus_confederate_boxplots(minutes, nighttime_only=False):
    figs = list()
    for i in [5, 6, 9, 10]:
        scores = analyze_MBA(i, minutes, nighttime_only=nighttime_only)
        confeds = list()
        mean = numpy.array(scores.values()).mean()
        for key in scores.keys():
            if scores[key] > mean:
                confeds.append(key)
        for _column in ['ebt_length', 'ebt_volume']:
            fig = confederate_boxplots(confeds, _column)
            figs.append((fig, i, _column))
    return figs

#--

#---# Confederate histograms and scatterplots
def monkey_confederate_bout_start_difference(monkey_one, monkey_two, collect_xy_data=None):
    def _bout_startdiff_volumesum(subplot, monkey_one, monkey_two):
        if False:
            f = open('utils/DATA/test%s.json' % 0, 'r')
            x = json.loads(f.readline())
            f.close()
            f = open('utils/DATA/test%s.json' % 1, 'r')
            y = json.loads(f.readline())
            f.close()
            return subplot, x, y

        one_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_one).order_by(
            'drinking_experiment__dex_date')
        one_dates = one_mtds.values_list('drinking_experiment__dex_date', flat=True).distinct()

        x_data = list()
        y_data = list()
        for date in one_dates:
            one_values = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_date=date).values_list(
                'ebt_start_time', 'ebt_volume')
            two_bouts = ExperimentBout.objects.filter(mtd__monkey=monkey_two,
                                                      mtd__drinking_experiment__dex_date=date).values_list(
                'ebt_start_time', 'ebt_volume')
            if not one_values or not two_bouts:
                continue
            two_starts = numpy.array(two_bouts)[:, 0]

            for one_start_time, one_volume in one_values:
                two_closest_start = min(two_starts, key=lambda x: abs(x - one_start_time))
                two_closest_bout = two_bouts.get(ebt_start_time=two_closest_start)
                x_data.append(one_start_time - two_closest_bout[0])
                y_data.append(one_volume + two_closest_bout[1])
        subplot.set_ylabel("Summed volume of adjacent bouts")
        subplot.set_xlabel("Bout start time difference")
        return subplot, x_data, y_data

    if not isinstance(monkey_one, Monkey):
        try:
            monkey_one = Monkey.objects.get(pk=monkey_one)
        except Monkey.DoesNotExist:
            try:
                monkey_one = Monkey.objects.get(mky_real_id=monkey_one)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return
    if not isinstance(monkey_two, Monkey):
        try:
            monkey_two = Monkey.objects.get(pk=monkey_two)
        except Monkey.DoesNotExist:
            try:
                monkey_two = Monkey.objects.get(mky_real_id=monkey_two)
            except Monkey.DoesNotExist:
                print("That's not a valid monkey.")
                return
    assert monkey_one.cohort == monkey_two.cohort
    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    fig.suptitle("Monkey %s - Monkey %s" % (str(monkey_one), str(monkey_two)))
    main_gs = gridspec.GridSpec(10, 10)
    main_gs.update(left=0.06, right=0.98, wspace=.08, hspace=0.08)
    subplot = fig.add_subplot(main_gs[1:, :9])
    axHistx = fig.add_subplot(main_gs[:1, :9], sharex=subplot)
    axHisty = fig.add_subplot(main_gs[1:10, 9:], sharey=subplot)

    collect_xy_data = collect_xy_data if collect_xy_data else _bout_startdiff_volumesum

    colors = ['navy', 'gold', 'green', 'blue', 'orange']
    subplot, _x, _y = collect_xy_data(subplot, monkey_one, monkey_two)
    _x = numpy.array(_x)
    _y = numpy.array(_y)

    subplot.scatter(_x, _y, color=colors.pop(0), edgecolor='none', alpha=.2)

    # make some labels invisible
    pyplot.setp(axHistx.get_xticklabels() + axHistx.get_yticklabels(), visible=False)
    pyplot.setp(axHisty.get_xticklabels() + axHisty.get_yticklabels(), visible=False)

    axHistx.hist(_x, bins=150, alpha=1, log=True)
    axHisty.hist(_y, bins=150, alpha=1, log=True, orientation='horizontal')

    """
	subplot.scatter(_x, _y, color='orange', edgecolor='none', alpha=1)
	# regression line
	slope, intercept, r_value, p_value, std_err = stats.linregress(_x, _y)
	reg_label = "Fit: r=%f, p=%f" % (r_value, p_value)
	subplot.plot(_x, _x*slope+intercept, color='black', label=reg_label)
	"""
    return fig


#---#

class RhesusAdjacencyNetwork():
    network = None
    __monkeys = None

    def __init__(self, cohorts, graph=None):
        self.network = graph if graph else nx.Graph()
        self.__monkeys = Monkey.objects.Drinkers().filter(cohort__in=cohorts)

        self.construct_network()

    def dump_graphml(self):
        return "".join(nx.generate_graphml(self.network))

    def dump_JSON(self):
        from networkx.readwrite import json_graph

        return json_graph.dumps(self.network)

    def construct_network(self):
        self.build_nodes()
        self.build_edges()
        print 'Finished'

    def build_nodes(self):
        for mky in self.__monkeys:
            self.add_node(mky)

    def build_edges(self):
        if not self.network.nodes():
            raise Exception("Build nodes first")
        for source_id in self.network.nodes():
            for target_id in self.network.nodes():
                if target_id == source_id:
                    continue
                self.add_edge(source_id, target_id)

    def _construct_node_data(self, mky, data=None):
        #  IMPORTANT NOTE
        # Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
        data = data if data else dict()
        data['monkey'] = mky.pk
        group = None
        for key in rhesus_drinkers_distinct.iterkeys():
            if mky.pk in rhesus_drinkers_distinct[key]:
                break
        if key == 'VHD':
            group = 4
        if key == 'HD':
            group = 3
        if key == 'MD':
            group = 2
        if key == 'LD':
            group = 1

        data['group'] = group
        return data

    def _construct_edge_data(self, source, target, data=None):
        from matrr.models import CohortBout
        #  IMPORTANT NOTE
        # Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
        data = data if data else dict()
        #		data['source'] = source
        #		data['target'] = target
        cbt_count = CohortBout.objects.filter(ebt_set__mtd__monkey=source).filter(
            ebt_set__mtd__monkey=target).distinct().count()
        data['cbt_count'] = cbt_count
        return data

    def add_node(self, mky):
        self.network.add_node(mky.pk, **self._construct_node_data(mky))

    def add_edge(self, source, target):
        self.network.add_edge(source, target, **self._construct_edge_data(source, target))


def dump_RAN_json(cohort_pk=0, cohorts_pks=None):
    cohorts = [cohort_pk] if cohort_pk else cohorts_pks
    ran = RhesusAdjacencyNetwork(cohorts=cohorts)
    json = ran.dump_JSON()
    cohorts = [str(cohort) for cohort in cohorts]
    cohorts = '_'.join(cohorts)
    f = open('static/js/%s.RAN.json' % cohorts, 'w')
    f.write(json)
    f.close()


def _kathy_correlation_bec_max_bout_general(subplot, becs, color='black', subject_title=''):
    title = "Correlation between Max Bout Volume and BEC%s" % subject_title
    x_label = "Max Bout Volume (ml), before BEC sample"
    y_label = "BEC (mg pct)"
    subplot.set_title(title)
    subplot.set_xlabel(x_label)
    subplot.set_ylabel(y_label)

    x80_data = list()
    y80_data = list()
    x0_data = list()
    y0_data = list()
    for bec in becs:
        try:
            session_time_of_bec_sample = (
            datetime.combine(date.today(), bec.bec_sample) - datetime.combine(date.today(),
                                                                              bec.bec_session_start)).seconds
        except TypeError as e:
            continue
        bouts_before_sample = bec.mtd.bouts_set.filter(ebt_start_time__lt=session_time_of_bec_sample,
                                                       ebt_end_time__lt=session_time_of_bec_sample)
        max_before_sample_bout_vol = bouts_before_sample.aggregate(Max('ebt_volume'))['ebt_volume__max']
        if max_before_sample_bout_vol is None:
            continue
        if bec.bec_mg_pct > 80:
            x80_data.append(max_before_sample_bout_vol)
            y80_data.append(bec.bec_mg_pct)
        else:
            x0_data.append(max_before_sample_bout_vol)
            y0_data.append(bec.bec_mg_pct)

    subplot.scatter(x80_data, y80_data, c=color, alpha=.2, s=10, label='')
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x80_data, y80_data)
    except ValueError as e:
        print e
    else:
        reg_label = "Fit >80: r=%f, p=%f" % (r_value, p_value)
        subplot.plot(x80_data, numpy.array(x80_data) * slope + intercept, color=color, label=reg_label, lw=3)

    subplot.scatter(x0_data, y0_data, c=color, alpha=.2, s=10, label='')
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x0_data, y0_data)
    except ValueError as e:
        print e
    else:
        reg_label = "Fit <80: r=%f, p=%f" % (r_value, p_value)
        subplot.plot(x0_data, numpy.array(x0_data) * slope + intercept, color=color, label=reg_label, lw=3,
                     ls='dashdot')

    subplot.axhspan(0, 81, color='black', alpha=.4, zorder=-100)
    subplot.text(0, 82, "80 mg pct")
    subplot.legend(loc=0, scatterpoints=1)
    subplot.set_xlim(xmin=0)
    subplot.set_ylim(ymin=0)
    return subplot


def kathy_correlation_bec_maxbout_pairwise_drinkinggroup():
    figures = list()
    labels = list()
    for key1, key2 in itertools.combinations(rhesus_keys, 2):
        fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        gs = gridspec.GridSpec(3, 3)
        gs.update(left=0.08, right=0.98, wspace=.00, hspace=0)
        subplot = fig.add_subplot(gs[:, :])
        subject_title = " for %s vs %s" % (key1, key2)
        vhd_becs = MonkeyBEC.objects.filter(monkey__in=rhesus_drinkers_distinct[key1]).exclude(mtd=None)
        subplot = _kathy_correlation_bec_max_bout_general(subplot, vhd_becs, rhesus_colors[key1], subject_title)
        ld_becs = MonkeyBEC.objects.filter(monkey__in=rhesus_drinkers_distinct[key2]).exclude(mtd=None)
        subplot = _kathy_correlation_bec_max_bout_general(subplot, ld_becs, rhesus_colors[key2], subject_title)
        figures.append(fig)
        labels.append("%s-%s" % (key1, key2))
    return figures, labels


def kathy_correlation_bec_maxbout_cohort(cohort=5):
    figures = list()
    subject_labels = list()
    cohort_monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.08, right=0.98, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])

    subject_title = " for %s" % cohort_monkeys[0].cohort.coh_cohort_name
    coh_becs = MonkeyBEC.objects.filter(monkey__in=cohort_monkeys).exclude(mtd=None)
    subplot = _kathy_correlation_bec_max_bout_general(subplot, coh_becs, 'black', subject_title)
    figures.append(fig)
    subject_labels.append('cohort')
    for mky in cohort_monkeys:
        fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
        gs = gridspec.GridSpec(3, 3)
        gs.update(left=0.08, right=0.98, wspace=.00, hspace=0)
        subplot = fig.add_subplot(gs[:, :])

        subject_title = " for Monkey %d" % mky.pk
        mky_becs = MonkeyBEC.objects.filter(monkey=mky).exclude(mtd=None)
        subplot = _kathy_correlation_bec_max_bout_general(subplot, mky_becs, rhesus_monkey_colors[mky.pk],
                                                          subject_title)
        figures.append(fig)
        subject_labels.append(mky.pk)
    return figures, subject_labels


#----------------------
def create_age_graphs():
    import settings

    output_path = settings.STATIC_ROOT
    output_path = os.path.join(output_path, "images/christa/")
    cohort_age_mtd_general_sets = \
        [_mtd_call_gkg_etoh, _mtd_call_bec, _mtd_call_over_3gkg, _mtd_call_over_4gkg, _mtd_call_max_bout_vol,
         _mtd_call_max_bout_vol_pct]
    for method in cohort_age_mtd_general_sets:
        for phase in range(3):
            fig = cohort_age_mtd_general(phase, method)
            DPI = fig.get_dpi()
            filename = output_path + '%s.Phase%d.png' % (method.__name__, phase)
            fig.savefig(filename, dpi=DPI)
    for stage in range(3):
        fig = cohort_age_sessiontime(stage)
        DPI = fig.get_dpi()
        filename = output_path + '%s.Stage%d.png' % ("cohort_age_sessiontime", stage)
        fig.savefig(filename, dpi=DPI)
    for phase in range(3):
        for hour in range(1, 3):
            fig = cohort_age_vol_hour(phase, hour)
            DPI = fig.get_dpi()
            filename = output_path + '%s.Phase%d.Hour%d.png' % ("cohort_age_vol_hour", phase, hour)
            fig.savefig(filename, dpi=DPI)
    for phase in range(3):
        for gkg in range(6):
            fig = rhesus_gkg_onset_age_category(phase, gkg)
            DPI = fig.get_dpi()
            filename = output_path + '%s.Phase%d.gkg%d.png' % ("rhesus_gkg_onset_age_category", phase, gkg)
            fig.savefig(filename, dpi=DPI)


def create_christa_graphs():
    import settings

    output_path = settings.STATIC_ROOT
    output_path = os.path.join(output_path, "images/christa/")
    for i in range(3):
        volbout_figs = cohorts_daytime_volbouts_bargraph_split(i)
        bouts_figs = cohorts_daytime_bouts_histogram_split(i)
        maxbout_figs = cohorts_maxbouts_histogram(i)
        for fig, cohort in volbout_figs:
            DPI = fig.get_dpi()
            filename = output_path + '%s.%s.Phase%d.png' % ("cohorts_daytime_volbouts_bargraph_split", str(cohort), i)
            fig.savefig(filename, dpi=DPI)
        for fig, cohort in bouts_figs:
            DPI = fig.get_dpi()
            filename = output_path + '%s.%s.Phase%d.png' % ("cohorts_daytime_bouts_histogram_split", str(cohort), i)
            fig.savefig(filename, dpi=DPI)
        for fig, cohort in maxbout_figs:
            DPI = fig.get_dpi()
            filename = output_path + '%s.%s.Phase%d.png' % ("cohorts_maxbouts_histogram", str(cohort), i)
            fig.savefig(filename, dpi=DPI)
    create_age_graphs()


def create_erich_graphs():
    import settings

    output_path = settings.STATIC_ROOT
    output_path = os.path.join(output_path, "images/erich/")
    minutes = 120

    fig = rhesus_oa_pellettime_vs_gkg()
    DPI = fig.get_dpi()
    filename = output_path + '%s.png' % "rhesus_oa_pellettime_vs_gkg"
    fig.savefig(filename, dpi=DPI)

    fig = rhesus_oa_pelletvolume_perday_perkg()
    DPI = fig.get_dpi()
    filename = output_path + '%s.png' % "rhesus_oa_pelletvolume_perday_perkg"
    fig.savefig(filename, dpi=DPI)

    fig = rhesus_thirds_oa_pelletvolume_perday_perkg()
    DPI = fig.get_dpi()
    filename = output_path + '%s.png' % "rhesus_thirds_oa_pelletvolume_perday_perkg"
    fig.savefig(filename, dpi=DPI)

    already_created = \
        """
	fig = rhesus_etoh_gkg_stackedbargraph()
	DPI = fig.get_dpi()
	filename = output_path + '%s.png' % "rhesus_etoh_gkg_stackedbargraph"
	fig.savefig(filename, dpi=DPI)

	for mky_cat in rhesus_drinkers.keys():
		fig = rhesus_oa_discrete_minute_volumes(minutes, mky_cat)
		DPI = fig.get_dpi()
		filename = output_path + '%s-%d-%s.png' % ("rhesus_oa_discrete_minute_volumes", minutes, mky_cat)
		fig.savefig(filename, dpi=DPI)

	confed_boxplots = rhesus_confederate_boxplots()
	for fig, coh_pk, column in confed_boxplots:
		DPI = fig.get_dpi()
		filename = output_path + '%s-%d-%s.png' % ("rhesus_confederate_boxplots", coh_pk, column)
		fig.savefig(filename, dpi=DPI)

	for xkey in rhesus_drinkers_distinct.iterkeys():
		for ykey in rhesus_drinkers_distinct.iterkeys():
			if xkey == ykey:
				continue
			fig = rhesus_oa_discrete_minute_volumes_discrete_monkey_comparisons(xkey, ykey)
			DPI = fig.get_dpi()
			filename = output_path + '%s-%s-%s.png' % ("rhesus_oa_discrete_minute_volumes_discrete_monkey_comparisons", xkey, ykey)
			fig.savefig(filename, dpi=DPI)

	for mky_cat in rhesus_drinkers.keys():
		fig = rhesus_thirds_oa_discrete_minute_volumes(minutes, mky_cat)
		DPI = fig.get_dpi()
		filename = output_path + '%s-%d-%s.png' % ("rhesus_thirds_oa_discrete_minute_volumes", minutes, mky_cat)
		fig.savefig(filename, dpi=DPI)

	fig = rhesus_hourly_gkg_boxplot_by_category()
	DPI = fig.get_dpi()
	filename = output_path + '%s.png' % "rhesus_hourly_gkg_boxplot_by_category"
	fig.savefig(filename, dpi=DPI)
	"""


def create_kathy_graphs():
    import settings

    output_path = settings.STATIC_ROOT
    output_path = os.path.join(output_path, "images/kathy/")
    for coh in [5, 6, 9, 10]:
        figures, labels = kathy_correlation_bec_maxbout_cohort(coh)
        for fig, label in zip(figures, labels):
            DPI = fig.get_dpi()
            filename = output_path + '%s.%s.%s.png' % (str(coh), 'kathy_correlation_bec_maxbout_cohort', label)
            fig.savefig(filename, dpi=DPI)

    figures, labels = kathy_correlation_bec_maxbout_pairwise_drinkinggroup()
    for fig, label in zip(figures, labels):
        DPI = fig.get_dpi()
        filename = output_path + '%s.%s.png' % ("kathy_correlation_bec_maxbout_pairwise_drinkinggroup", label)
        fig.savefig(filename, dpi=DPI)


def create_manuscript_graphs(save=False, fig_size=(25, 15)):
    def etoh_bec_scatter(HD_monkey=10065, LD_monkey=10052, fig_size=plotting.HISTOGRAM_FIG_SIZE):
        fig = pyplot.figure(figsize=fig_size, dpi=plotting.DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 2)
        gs.update(left=0.06, right=0.98, wspace=.12, hspace=0, top=.92)
        left_subplot = fig.add_subplot(gs[0])
        right_subplot = fig.add_subplot(gs[1])

        monkey_ids = [LD_monkey, HD_monkey]

        marker_size = 90
        xmax_bec = 0
        xmax_mtd = 0
        for monkey in monkey_ids:
            mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).order_by(
                'drinking_experiment__dex_date')
            xaxis_length = mtds.count()
            xmax_mtd = max(xaxis_length, xmax_mtd)
            x_axis = range(xaxis_length)
            y_axis = mtds.values_list('mtd_etoh_g_kg', flat=True)
            left_subplot.scatter(x_axis, y_axis, color=rhesus_monkey_colors[monkey],
                                 marker=rhesus_monkey_markers[monkey], s=marker_size)
            becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).order_by('bec_collect_date')
            xaxis_length = becs.count()
            xmax_bec = max(xaxis_length, xmax_bec)
            x_axis = range(xaxis_length)
            y_axis = becs.values_list('bec_mg_pct', flat=True)
            right_subplot.scatter(x_axis, y_axis, color=rhesus_monkey_colors[monkey],
                                  marker=rhesus_monkey_markers[monkey], s=marker_size)

        left_subplot.set_ylim(ymin=0)
        left_subplot.set_xlim(xmin=0, xmax=xmax_mtd)
        right_subplot.set_ylim(ymin=0)
        right_subplot.set_xlim(xmin=0, xmax=xmax_bec)
        tick_size = 20
        legend_size = 20
        for subplot in [left_subplot, right_subplot]:
            subplot.legend(["Monkey %d" % m for m in monkey_ids], prop={'size': legend_size})
            subplot.tick_params(axis='both', which='major', labelsize=tick_size)
            subplot.tick_params(axis='both', which='minor', labelsize=tick_size)

        suptitle_size = 30
        title_size = 26
        label_size = 24
        fig.suptitle("High Drinker vs Low Drinker", size=suptitle_size)
        left_subplot.set_title("Daily Ethanol Intake", size=title_size)
        left_subplot.set_ylabel("Ethanol (g/kg)", size=label_size)
        left_subplot.set_xlabel("Date", size=label_size)
        right_subplot.set_title("Daily BEC", size=title_size)
        right_subplot.set_ylabel("BEC (mg pct)", size=label_size)
        right_subplot.set_xlabel("Date", size=label_size)
        return fig

    figures = list()
    figures.append(rhesus_etoh_gkg_forced_monkeybargraphhistogram(fig_size=fig_size))
    figures.append(rhesus_etoh_gkg_stackedbargraph(fig_size=fig_size))
    figures.append(rhesus_hourly_gkg_boxplot_by_category(fig_size=fig_size))
    figures.append(etoh_bec_scatter(fig_size=fig_size))
    if save:
        output_path = '/home/developer/Desktop/_graphs/manuscript/'
        for index, fig in enumerate(figures):
            filename = output_path + 'Figure-%d.png' % index
            fig.savefig(filename, dpi=300)

