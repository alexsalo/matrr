from collections import defaultdict
import json
import numpy
from matplotlib import pyplot, gridspec
import os
from scipy import stats
from matrr.plotting import *
from matrr.utils import apriori, gadgets
from matrr.models import Monkey, Cohort, MonkeyToDrinkingExperiment, CohortBout, ExperimentBout, Min, TWENTYFOUR_HOUR, DrinkingExperiment

#plot
from matrr.utils.confederates import confederates


def confederate_boxplots(confederates, bout_column):
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

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 40)
    main_gs.update(left=0.12, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])

    cohort_data = list()
    confed_data = list()
    monkey_data = list()
    minutes = numpy.array([0, 1, 5, 10, 15, 20])
    min_oa_date = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
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

    main_plot.boxplot(monkey_data, positions=monkey_pos)

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

#analyze datas
def analyze_MBA(pk, minutes):
    confeds = apriori.get_nighttime_confederate_groups(pk, minutes)
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
def rhesus_confederate_boxplots(minutes):
    figs = list()
    for i in [5, 6, 9, 10]:
        scores = analyze_MBA(i, minutes)
        confeds = list()
        mean = numpy.array(scores.values()).mean()
        for key in scores.keys():
            if scores[key] > mean:
                confeds.append(key)
        for _column in ['ebt_length', 'ebt_volume']:
            fig = confederate_boxplots(confeds, _column)
            figs.append((fig, i, _column))
    return figs


#---# Confederate graphs
def _confederate_bout_start_difference_subplots(monkey_one, monkey_two, scatter_subplot, axHistx=None, axHisty=None, collect_xy_data=None):
    def _bout_startdiff_volsum(subplot, monkey_one, monkey_two):
        try:
            fx = open('matrr/utils/DATA/json/_bout_startdiff_volsum-%d-%d-xvalues.json' % (monkey_one.pk, monkey_two.pk), 'r')
            fy = open('matrr/utils/DATA/json/_bout_startdiff_volsum-%d-%d-yvalues.json' % (monkey_one.pk, monkey_two.pk), 'r')
        except:
            one_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_one).order_by('drinking_experiment__dex_date')
            one_dates = one_mtds.values_list('drinking_experiment__dex_date', flat=True).distinct()
            x_data = [TWENTYFOUR_HOUR,]
            y_data = [1000,]
            for date in one_dates:
                one_values = ExperimentBout.objects.filter(mtd__monkey=monkey_one, mtd__drinking_experiment__dex_date=date).values_list('ebt_start_time', 'ebt_volume')
                two_values = ExperimentBout.objects.filter(mtd__monkey=monkey_two, mtd__drinking_experiment__dex_date=date).values_list('ebt_start_time', 'ebt_volume')
                if not one_values or not two_values:
                    continue
                two_starts = numpy.array(two_values)[:,0]
                for one_start_time, one_volume in one_values:
                    two_closest_start = min(two_starts, key=lambda x:abs(x-one_start_time))
                    two_closest_bout = two_values.get(ebt_start_time=two_closest_start)
                    x_value = float(numpy.abs(one_start_time - two_closest_bout[0]))
                    y_value = float(one_volume + two_closest_bout[1])
                    x_data.append(x_value)
                    y_data.append(y_value)
            subplot.set_ylabel("Summed volume of adjacent bouts")
            subplot.set_xlabel("Bout start time difference")

            folder_name = 'matrr/utils/DATA/json/'
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            fx = open(folder_name+'_bout_startdiff_volsum-%d-%d-xvalues.json' % (monkey_one.pk, monkey_two.pk), 'w')
            fy = open(folder_name+'_bout_startdiff_volsum-%d-%d-yvalues.json' % (monkey_one.pk, monkey_two.pk), 'w')
            fx.write(json.dumps(x_data))
            fy.write(json.dumps(y_data))
            fx.close()
            fy.close()
            return subplot, x_data, y_data
        else:
            x = json.loads(fx.readline())
            y = json.loads(fy.readline())
            fx.close()
            fy.close()
            subplot.set_ylabel("Summed volume of adjacent bouts")
            subplot.set_xlabel("Bout start time difference")
            return subplot, x, y

    collect_xy_data = collect_xy_data if collect_xy_data else _bout_startdiff_volsum

    scatter_subplot, _x, _y = collect_xy_data(scatter_subplot, monkey_one, monkey_two)
    _x = numpy.array(_x)
    _y = numpy.array(_y)

    #### chop off outliers > 2stdev from the mean
    x_mean = _x.mean()
    x_std = _x.std()
    y_mean = _y.mean()
    y_std = _y.std()
    x_data = list()
    y_data = list()
    for xval, yval in zip(_x, _y):
        if (x_mean - 2*x_std) < xval < (x_mean + 2*x_std):
            if (y_mean - 2*y_std) < yval < (y_mean + 2*y_std):
                x_data.append(xval)
                y_data.append(yval)
    ###--

#    print '%s, %s' % (str(monkey_one), str(monkey_two))
#    print len(x_data)
#    print len(y_data)
#    print '---'
    scatter_subplot.hexbin(x_data, y_data, gridsize=30)
    scatter_subplot.set_xlim(xmin=0)
    scatter_subplot.set_ylim(ymin=0)

    if axHistx:
        axHistx.hist(x_data, bins=150, alpha=1, log=True)
        pyplot.setp(axHistx.get_xticklabels() + axHistx.get_yticklabels(), visible=False)
    if axHisty:
        axHisty.hist(y_data, bins=150, alpha=1, log=True, orientation='horizontal')
        pyplot.setp(axHisty.get_xticklabels() + axHisty.get_yticklabels(), visible=False)
    return scatter_subplot, axHistx, axHisty

def monkey_confederate_bout_start_difference(monkey_one, monkey_two, collect_xy_data=None):
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
    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    fig.suptitle("Monkey %s - Monkey %s" % (str(monkey_one), str(monkey_two)))
    main_gs = gridspec.GridSpec(10, 10)
    main_gs.update(left=0.06, right=0.98, wspace=.08, hspace=0.08)
    scatter_subplot = fig.add_subplot(main_gs[1:,:9])
    axHistx = fig.add_subplot(main_gs[:1,:9], sharex=scatter_subplot)
    axHisty = fig.add_subplot(main_gs[1:10,9:], sharey=scatter_subplot)
    _confederate_bout_start_difference_subplots(monkey_one, monkey_two, scatter_subplot, axHistx, axHisty, collect_xy_data)
    return fig

def monkey_confederate_bout_start_difference_grid(cohort, collect_xy_data=None):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Monkey.DoesNotExist:
            print("That's not a valid cohort.")
            return

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#    fig.suptitle("Cohort %s" % str(cohort))
    fig.suptitle("Cohort %s - first five hours excluded" % str(cohort))
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort).order_by('pk')
    mky_count = monkeys.count()
    main_gs = gridspec.GridSpec(mky_count, mky_count)

    # The grid will hide duplicate monkey pairs (and the diagonal)
    # The left column and bottom row are duplicates, and won't be rendered
    # So I offset the gridspec to shift the left/bottom to hide this empty space.
    bottom_base = .02
    left_base = .02
    bottom = bottom_base - mky_count/100
    left = left_base - mky_count/100
    main_gs.update(top=.93, left=left, right=0.92, bottom=bottom, wspace=.02, hspace=0.02)

    finished = list()
    scatter_subplot = None
    for x_index, x_monkey in enumerate(monkeys):
        for y_index, y_monkey in enumerate(monkeys):
            if x_monkey == y_monkey: continue
            if sorted([x_monkey.pk, y_monkey.pk]) in finished:
                continue
            else:
                finished.append(sorted([x_monkey.pk, y_monkey.pk]))
            scatter_subplot = fig.add_subplot(main_gs[x_index, y_index], sharex=scatter_subplot, sharey=scatter_subplot)

            if x_index == 0 and y_index:
                scatter_subplot.set_title("%s" % str(y_monkey), size=20, color=RHESUS_MONKEY_COLORS[y_monkey.pk])
            if y_index+1 == mky_count:
                x0, y0, x1, y1 = scatter_subplot.get_position().extents
                fig.text(x1 + .02, (y0+y1)/2, "%s" % str(x_monkey), size=20, color=RHESUS_MONKEY_COLORS[x_monkey.pk], rotation=-90, verticalalignment='center')
            scatter_subplot = fig.add_subplot(main_gs[x_index,y_index], sharex=scatter_subplot, sharey=scatter_subplot)
            subplots = _confederate_bout_start_difference_subplots(x_monkey, y_monkey, scatter_subplot, collect_xy_data=collect_xy_data)
            for subplot in subplots:
                if subplot:
                    subplot.set_ylabel("")
                    subplot.set_xlabel("")
#                    pyplot.setp(subplot.get_xticklabels() + subplot.get_yticklabels(), visible=False)
                    subplot.set_xticklabels([])
                    subplot.set_yticklabels([])
                    subplot.set_xticks([])
                    subplot.set_yticks([])
                    gray_color = .6
                    subplot.set_axis_bgcolor((gray_color, gray_color, gray_color))
    return fig

def confederate_bout_difference_grid(cohort, collect_xy_data=None):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Monkey.DoesNotExist:
            print("That's not a valid cohort.")
            return

    def __confederate_bout_difference_subplots(monkey_one, monkey_two, scatter_subplot, axHistx=None, axHisty=None, collect_xy_data=None):
        collect_xy_data = collect_xy_data if collect_xy_data else gadgets.collect_bout_startdiff_ratesum_data

        scatter_subplot, _x, _y = collect_xy_data(scatter_subplot, monkey_one, monkey_two)
        _x = numpy.array(_x)
        _y = numpy.array(_y)

        #### chop off outliers > 2stdev from the mean
        x_mean = _x.mean()
        x_std = _x.std()
        y_mean = _y.mean()
        y_std = _y.std()
        x_data = list()
        y_data = list()
        for xval, yval in zip(_x, _y):
            if (x_mean - 2*x_std) < xval < (x_mean + 2*x_std):
                if (y_mean - 2*y_std) < yval < (y_mean + 2*y_std):
                    x_data.append(xval)
                    y_data.append(yval)
        ###--

        bins = numpy.arange(0, 1, .025)
        if y_data:
            scatter_subplot.hist(y_data, bins=bins)
        scatter_subplot.set_xlim(xmin=0)
        scatter_subplot.set_ylim(ymin=0)

        if axHistx:
            axHistx.hist(x_data, bins=150, alpha=1, log=True)
            pyplot.setp(axHistx.get_xticklabels() + axHistx.get_yticklabels(), visible=False)
        if axHisty:
            axHisty.hist(y_data, bins=150, alpha=1, log=True, orientation='horizontal')
            pyplot.setp(axHisty.get_xticklabels() + axHisty.get_yticklabels(), visible=False)
        return scatter_subplot, axHistx, axHisty


    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)

    fig.suptitle("Cohort %s" % str(cohort))
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort).order_by('pk')
    mky_count = monkeys.count()
    main_gs = gridspec.GridSpec(mky_count, mky_count)

    # The grid will hide duplicate monkey pairs (and the diagonal)
    # The left column and bottom row are duplicates, and won't be rendered
    # So I offset the gridspec to shift the left/bottom to hide this empty space.
    bottom_base = .07
    left_base = .05
    bottom = bottom_base - mky_count/100
    left = left_base - mky_count/100
    main_gs.update(top=.93, left=left, right=0.94, bottom=bottom, wspace=.01, hspace=0.01)

    finished = list()
    scatter_subplot = None
    subplots = []
    for x_index, x_monkey in enumerate(monkeys):
        for y_index, y_monkey in enumerate(monkeys):
            if sorted([x_monkey.pk, y_monkey.pk]) in finished:
                continue
            else:
                finished.append(sorted([x_monkey.pk, y_monkey.pk]))
            scatter_subplot = fig.add_subplot(main_gs[x_index, y_index], sharex=scatter_subplot, sharey=scatter_subplot)

            if x_index == 0 and y_index:
                scatter_subplot.set_title("%s" % str(y_monkey), size=20, color=RHESUS_COLORS[y_monkey.mky_drinking_category])
            if y_index+1 == mky_count:
                x0, y0, x1, y1 = scatter_subplot.get_position().extents
                fig.text(x1 + .02, (y0+y1)/2, "%s" % str(x_monkey), size=20, color=RHESUS_COLORS[x_monkey.mky_drinking_category], rotation=-90, verticalalignment='center')

            subplots.append(scatter_subplot)
            __confederate_bout_difference_subplots(x_monkey, y_monkey, scatter_subplot, collect_xy_data=collect_xy_data)
    for subplot in subplots:
        if subplot:
            subplot.set_ylabel("")
            subplot.set_xlabel("")
            subplot.set_xticklabels([])
            subplot.set_yticklabels([])
            subplot.set_xticks([])
            subplot.set_yticks([])
            gray_color = .6
            subplot.set_axis_bgcolor((gray_color, gray_color, gray_color))
    notes_subplot = fig.add_subplot(main_gs[int(mky_count/2)+1:mky_count, 0:int(mky_count/2)])
    notes_subplot.set_axis_bgcolor([1,1,1])
    notes_subplot.set_title("EXAMPLE SUBPLOT")
    notes_subplot.set_ylabel("Count (bouts)")
    notes_subplot.set_xlabel("grams / kilogram / minute")
    notes_subplot.set_xlim(0, 1)
    notes_subplot.set_xticks(numpy.arange(0,1.1 ,.1))
    pyplot.setp(notes_subplot.get_xticklabels(), rotation=-45)
    return fig

def cohort_confederates_data_collection(cohort):
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)
    drinker_count = monkeys.count()
    dexs = DrinkingExperiment.objects.filter(cohort=cohort, dex_type='Open Access')

    data = defaultdict(lambda: defaultdict(list))
    for dex in dexs:
        # get the MTDs for each today's drinking experiment
        mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment=dex, monkey__in=monkeys)
        if not mtds:
            continue

        # find out how many records are missing/excluded, so that I can pad numbers with the average
        empty_count = 0
        for mtd in mtds:
            # We need to find out how many MTDs are excluded
            if mtd.mex_excluded:
                empty_count += 1
        # We also need to find out how many MTD records are missing (usually due to exceptions)
        empty_count += drinker_count - mtds.count()

        included_mtds = mtds.exclude(mex_excluded=True)
        for monkey in monkeys:
            try:
                data['etoh_data'][monkey].append(included_mtds.filter(monkey=monkey)[0].mtd_etoh_g_kg)
            except IndexError:
                data['etoh_data'][monkey].append(0)
            data['missing_counts'][monkey].append(empty_count)
    data['monkeys'] = monkeys
    return data

def cohort_confederate_daily_intakes(cohort_pk, figsize=HISTOGRAM_FIG_SIZE):
    cohort = Cohort.objects.get(pk=cohort_pk)
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)
    fig = pyplot.figure(figsize=figsize, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.04, bottom=.05, right=0.98, top=.95, wspace=.00, hspace=0)
    subplot = fig.add_subplot(gs[:, :])

    data = cohort_confederates_data_collection(cohort)

    grey_indexes = list()
    day_count = max([len(data['etoh_data'][mky]) for mky in monkeys])
    reformatted_ydata = defaultdict(lambda: numpy.zeros(day_count))
    for monkey in monkeys:
        for index, mc in enumerate(data['missing_counts'][monkey]):
            if mc:
                grey_indexes.append(index)
        y_data = numpy.array(data['etoh_data'][monkey])
        reformatted_ydata[monkey.mky_drinking_category] += y_data

    grey_indexes = set(grey_indexes)
    x_axis = range(day_count)
    bottom = numpy.zeros(day_count)
    max_yvalue = 0
    for key in ['LD', 'BD', 'HD', 'VHD']:
        y_axis = reformatted_ydata[key]
        max_yvalue = max(max_yvalue, max(y_axis))
        colors = list()
        for index, _x in enumerate(x_axis):
            color = 'purple' if index in grey_indexes else RHESUS_COLORS[key]
            colors.append(color)
        subplot.bar(x_axis, y_axis, bottom=bottom, width=1, alpha=1, color=colors, edgecolor=colors)
        bottom += y_axis
    subplot.legend()
    subplot.set_title(str(cohort))
    subplot.set_ylabel("Total EtOH Intake of Cohort (g/kg)")
    subplot.set_xlabel("Day of Open Access")
    subplot.set_xlim(xmax=day_count)
    return fig

def find_overlapping_bouts(primary_bouts, secondary_bouts):
    secondary_overlapped = list()
    for p_bout in primary_bouts:
        overlapped_bouts = secondary_bouts.filter(ebt_start_time__gt=p_bout.ebt_start_time).filter(ebt_start_time__lt=p_bout.ebt_end_time)
        overlapped_bouts = overlapped_bouts.values_list('pk', flat=True)
        secondary_overlapped.extend(overlapped_bouts)
    return secondary_overlapped

def generic_collect_overlapping_bout_data(monkey_A, monkey_B, bout_field):
    import inspect
    outfile_name = inspect.stack()[0][3] + ".bout_field"
    try:
        AB_overlapping_file = open('matrr/utils/DATA/json/%s-%d-%d-overlapping.json' % (outfile_name, monkey_A.pk, monkey_B.pk), 'r')
        AB_non_overlapping_file = open('matrr/utils/DATA/json/%s-%d-%d-non_overlapping.json' % (outfile_name, monkey_A.pk, monkey_B.pk), 'r')
        BA_overlapping_file = open('matrr/utils/DATA/json/%s-%d-%d-overlapping.json' % (outfile_name, monkey_B.pk, monkey_A.pk), 'r')
        BA_non_overlapping_file = open('matrr/utils/DATA/json/%s-%d-%d-non_overlapping.json' % (outfile_name, monkey_B.pk, monkey_A.pk), 'r')
    except:
        A_mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_A).order_by('drinking_experiment__dex_date')
        A_dates = A_mtds.values_list('drinking_experiment__dex_date', flat=True).distinct()
        AB_overlapping_rates = []
        AB_non_overlapping_rates = []
        BA_overlapping_rates = []
        BA_non_overlapping_rates = []
        for date in A_dates:
            A_bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey_A, mtd__drinking_experiment__dex_date=date).exclude(**{bout_field: None})
            B_bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey_B, mtd__drinking_experiment__dex_date=date).exclude(**{bout_field: None})
            AB_bouts = A_bouts | B_bouts
            if not AB_bouts:
                continue
            else:
                pass

            A_within_B = find_overlapping_bouts(B_bouts, A_bouts)
            B_within_A = find_overlapping_bouts(A_bouts, B_bouts)
            AB_overlapping_rates.extend(A_within_B)
            BA_overlapping_rates.extend(B_within_A)

            A_without_B = A_bouts.exclude(pk__in=A_within_B).values_list('pk', flat=True)
            B_without_A = B_bouts.exclude(pk__in=B_within_A).values_list('pk', flat=True)
            AB_non_overlapping_rates.extend(A_without_B)
            BA_non_overlapping_rates.extend(B_without_A)

        AB_overlapping_rates = list(ExperimentBout.objects.filter(pk__in=AB_overlapping_rates).values_list(bout_field, flat=True))
        AB_non_overlapping_rates = list(ExperimentBout.objects.filter(pk__in=AB_non_overlapping_rates).values_list(bout_field, flat=True))
        BA_overlapping_rates = list(ExperimentBout.objects.filter(pk__in=BA_overlapping_rates).values_list(bout_field, flat=True))
        BA_non_overlapping_rates = list(ExperimentBout.objects.filter(pk__in=BA_non_overlapping_rates).values_list(bout_field, flat=True))

        folder_name = 'matrr/utils/DATA/json/'
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        overlapping_file = open(folder_name+'%s-%d-%d-overlapping.json' % (outfile_name, monkey_A.pk, monkey_B.pk), 'w')
        non_overlapping_file = open(folder_name+'%s-%d-%d-non_overlapping.json' % (outfile_name, monkey_A.pk, monkey_B.pk), 'w')
        overlapping_file.write(json.dumps(AB_overlapping_rates))
        non_overlapping_file.write(json.dumps(AB_non_overlapping_rates))
        overlapping_file.close()
        non_overlapping_file.close()
        overlapping_file = open(folder_name+'%s-%d-%d-overlapping.json' % (outfile_name, monkey_B.pk, monkey_A.pk), 'w')
        non_overlapping_file = open(folder_name+'%s-%d-%d-non_overlapping.json' % (outfile_name, monkey_B.pk, monkey_A.pk), 'w')
        overlapping_file.write(json.dumps(BA_overlapping_rates))
        non_overlapping_file.write(json.dumps(BA_non_overlapping_rates))
        overlapping_file.close()
        non_overlapping_file.close()
        return AB_overlapping_rates, AB_non_overlapping_rates, BA_overlapping_rates, BA_non_overlapping_rates
    else:
        AB_overlapping_rates = json.loads(AB_overlapping_file.readline())
        AB_non_overlapping_rates = json.loads(AB_non_overlapping_file.readline())
        BA_overlapping_rates = json.loads(BA_overlapping_file.readline())
        BA_non_overlapping_rates = json.loads(BA_non_overlapping_file.readline())
        return AB_overlapping_rates, AB_non_overlapping_rates, BA_overlapping_rates, BA_non_overlapping_rates

def collect_overlapping_bout_intake_rate_data(monkey_A, monkey_B):
    return generic_collect_overlapping_bout_data(monkey_A, monkey_B, 'ebt_intake_rate')

def collect_overlapping_bout_volume_data(monkey_A, monkey_B):
    return generic_collect_overlapping_bout_data(monkey_A, monkey_B, 'ebt_volume')

def collect_overlapping_bout_volume_data(monkey_A, monkey_B):
    return generic_collect_overlapping_bout_data(monkey_A, monkey_B, 'ebt_length')

def competitive_bout_grid(cohort, support=.2, collect_data_method=collect_overlapping_bout_intake_rate_data):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Monkey.DoesNotExist:
            print("That's not a valid cohort.")
            return

    def __draw_subplot(monkey_one, monkey_two, subplot):
        if monkey_one == monkey_two:
            return subplot
        subplot.text(.05, .35, "A=%d, B=%d" % (monkey_one.pk, monkey_two.pk), size=10, transform=subplot.transAxes)
        AB, AB_NON, BA, BA_NON = collect_data_method(monkey_one, monkey_two)

        #### chop off outliers > 2stdev from the mean
        def chop_outliers(data, std_outlier_limit=5):
            data = numpy.array(data)
            chopped_data = list()
            data_mean = data.mean()
            data_std = data.std()
            for datapoint in data:
                if (data_mean - std_outlier_limit*data_std) < datapoint < (data_mean + std_outlier_limit*data_std):
                    chopped_data.append(datapoint)
            return chopped_data
        AB = chop_outliers(AB)
        AB_NON = chop_outliers(AB_NON)
        BA = chop_outliers(BA)
        BA_NON = chop_outliers(BA_NON)
        ###--

        t_stat, p_value = stats.ttest_ind(AB, AB_NON)
        subplot.text(.05, .85, "AB vs AB_non: p=%.03f" % p_value, size=10, transform=subplot.transAxes)
        if p_value <= .05:
            subplot.axvspan(0, 2.5, color='lightgreen', alpha=.5)
        t_stat, p_value = stats.ttest_ind(BA, BA_NON)
        subplot.text(.25, .75, "BA vs BA_non: p=%.03f" % p_value, size=10, transform=subplot.transAxes)
        if p_value <= .05:
            subplot.axvspan(2.5, 5, color='lightgreen', alpha=.5)
        subplot.boxplot([AB, AB_NON, BA, BA_NON], positions=range(1,5,1))
        subplot.set_xlim(xmin=0, xmax=5)
        return subplot

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    fig.suptitle("Cohort %s" % str(cohort))
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort).order_by('pk')
    mky_count = monkeys.count()
    main_gs = gridspec.GridSpec(mky_count, mky_count)

    # The grid will hide duplicate monkey pairs (and the diagonal)
    # The left column and bottom row are duplicates, and won't be rendered
    # So I offset the gridspec to shift the left/bottom to hide this empty space.
    bottom_base = .07
    left_base = .05
    bottom = bottom_base - mky_count/100
    left = left_base - mky_count/100
    main_gs.update(top=.93, left=left, right=0.94, bottom=bottom, wspace=.03, hspace=0.03)

    supports = confederates.load_apriori_output(cohort.pk, 20)

    # This shit is dumb, part of why I don't like json, and possibly my fault.
    # the keys in the supports are string-represented floats, eg. u'0.20000000001'.  Super stupid.
    # so I loop thru the keys like a lazy clown and get the support level I want.
    apriori_list = []
    for cool_string_float_key in supports.iterkeys():
        real_key = round(float(cool_string_float_key), 1)
        if real_key == support:
            apriori_list = supports[cool_string_float_key]
            break

    def fetch_apriori_supconf(monkey_a, monkey_b):
        pairs = list()
        for mba_output in apriori_list:
            if monkey_a in mba_output[0] or monkey_a in mba_output[1]:
                if monkey_b in mba_output[0] or monkey_b in mba_output[1]:
                    pairs.append(mba_output[2])
        return pairs

    subplots = []
    finished = []
    for x_index, x_monkey in enumerate(monkeys):
        for y_index, y_monkey in enumerate(monkeys):
            if x_monkey == y_monkey:
                continue
            if sorted([x_monkey, y_monkey]) in finished:
                continue
            else:
                finished.append(sorted([x_monkey, y_monkey]))
            subplot = fig.add_subplot(main_gs[x_index, y_index])

            if x_index == 0 and y_index:
                subplot.set_title("%s" % str(y_monkey), size=20, color=RHESUS_COLORS[y_monkey.mky_drinking_category])
            if y_index+1 == mky_count:
                x0, y0, x1, y1 = subplot.get_position().extents
                fig.text(x1 + .02, (y0+y1)/2, "%s" % str(x_monkey), size=20, color=RHESUS_COLORS[x_monkey.mky_drinking_category], rotation=-90, verticalalignment='center')

            subplots.append(subplot)
            __draw_subplot(x_monkey, y_monkey, subplot)
            pairs = fetch_apriori_supconf(x_monkey.pk, y_monkey.pk)
            if len(pairs):
                subplot.text(.05, .55, "Confidence=%s" % str(['%.2f' % conf for conf in pairs]), size=10, transform=subplot.transAxes)
                subplot.axvspan(0, 5, color='orange', alpha=.15)

    for subplot in subplots:
        if subplot:
            subplot.set_ylabel("")
            subplot.set_xlabel("")
            subplot.set_xticklabels([])
            subplot.set_yticklabels([])
            subplot.set_xticks([])
            subplot.set_yticks([])
    temp = """
    notes_subplot = fig.add_subplot(main_gs[int(mky_count/2)+1:mky_count, 0:int(mky_count/2)])
    notes_subplot.set_axis_bgcolor([1,1,1])
    notes_subplot.set_title("EXAMPLE SUBPLOT")
    notes_subplot.set_ylabel("")
    notes_subplot.set_xlabel("")
    notes_subplot.set_xlim(0, 1)
    notes_subplot.set_xticks(numpy.arange(0,1.1 ,.1))
    pyplot.setp(notes_subplot.get_xticklabels(), rotation=-45)
    """
    return fig


def dump_competitive_bout_rate_grid(cohorts=(5,6,8,9,10), supports=(.05, .1, .15, .2), output_path=''):
    for cohort in cohorts:
        for support in supports:
            fig = competitive_bout_grid(cohort, support)
            filename = output_path + 'competitive_bout_rate_grid-%d-%.2f.png' % (cohort, support)
            fig.savefig(filename, format='png')

def dump_competitive_bout_volume_grid(cohorts=(5,6,8,9,10), supports=(.05, .1, .15, .2), output_path=''):
    for cohort in cohorts:
        for support in supports:
            fig = competitive_bout_grid(cohort, support, collect_data_method=collect_overlapping_bout_volume_data)
            filename = output_path + 'competitive_bout_volume_grid-%d-%.2f.png' % (cohort, support)
            fig.savefig(filename, format='png')

def dump_competitive_bout_length_grid(cohorts=(5,6,8,9,10), supports=(.05, .1, .15, .2), output_path=''):
    for cohort in cohorts:
        for support in supports:
            fig = competitive_bout_grid(cohort, support, collect_data_method=collect_overlapping_bout_volume_data)
            filename = output_path + 'competitive_bout_length_grid-%d-%.2f.png' % (cohort, support)
            fig.savefig(filename, format='png')

