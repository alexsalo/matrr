import os
import collections
import datetime
import json
from matrr import models, plotting
from matrr.utils import gadgets
from matplotlib import pyplot, gridspec

def oa_eev_volume_summation_by_minutes_from_pellet(drinking_category, minutes=20, DAYTIME=True, NIGHTTIME=True):
    """
    This method will return a tuple.

    Tuple[0] will be a dictionary of the summed volume of ethanol consumed by monkeys in drinking_category
    Each key will be the number of minutes since the last pellet was taken, and the value at that key will be the volume consumed during that minute.

    Tuple[1] will be the count of monkeys in drinking_category, typically used for averages.
    """
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    file_name = "oa_eev_volume_summation_by_minutesFromPellet-%s-%s-%s.json" % (drinking_category, str(minutes), filename_concatenation)
    file_path = os.path.join(folder_name, file_name)

    monkey_set = plotting.RDD_56890[drinking_category]
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        volume_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        volume_by_minute_from_pellet = collections.defaultdict(lambda: 0)
        eevs = models.ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        if DAYTIME and not NIGHTTIME:
            eevs = eevs.Day()
        if NIGHTTIME and not DAYTIME:
            eevs = eevs.Night()

        for i in range(0, minutes):
            _eevs = eevs.filter(eev_pellet_time__gte=i * 60).filter(eev_pellet_time__lt=(i + 1) * 60)
            summed_volume = _eevs.aggregate(models.Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
            volume_by_minute_from_pellet[i] = 0 if summed_volume is None else summed_volume
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
        except IOError:
            pass
        f = open(file_path, 'w')
        json_data = json.dumps(volume_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), file_path)
    xlabel = "Minutes since last pellet"
    ylabel = "Average volume per monkey (mL)"
    title = "Average intake by minute after pellet"
    return volume_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def oa_eev_volume_summation_high_vs_low(category_half='high', minutes=20,  DAYTIME=True, NIGHTTIME=True):
    assert category_half in ('high', 'low')
    if category_half == 'high':
        monkey_set = plotting.RDD_56890['VHD']
        monkey_set.extend(plotting.RDD_56890['HD'])
    else:
        monkey_set = plotting.RDD_56890['BD']
        monkey_set.extend(plotting.RDD_56890['LD'])

    folder_name = "matrr/utils/DATA/json/"
    filename_concatination = "DAYTIME" if DAYTIME else ""
    filename_concatination += "NIGHTTIME" if NIGHTTIME else ""
    file_name = "oa_eev_volume_summation_high_vs_low-%s-%s-%s.json" % (category_half, str(minutes), filename_concatination)
    file_path = os.path.join(folder_name, file_name)
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        highlow_volume_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        highlow_volume_by_minute_from_pellet = collections.defaultdict(lambda: 0)
        eevs = models.ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
        if DAYTIME and not NIGHTTIME:
            eevs = eevs.Day()
        if NIGHTTIME and not DAYTIME:
            eevs = eevs.Night()
        for i in range(0, minutes):
            _eevs = eevs.filter(eev_pellet_time__gte=i * 60).filter(eev_pellet_time__lt=(i + 1) * 60)
            highlow_volume_by_minute_from_pellet[i] = _eevs.aggregate(models.Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
        except IOError:
            pass
        f = open(file_path, 'w')
        json_data = json.dumps(highlow_volume_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), file_path)
    xlabel = "Minutes since last pellet"
    ylabel = "Average volume per monkey (mL)"
    title = "Average intake by minute after pellet"
    return highlow_volume_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def eev_gkg_summation_by_minute_general(monkey_set, minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True, summed_field='eev_etoh_volume'):
    gkg_by_minute_from_pellet = collections.defaultdict(lambda: 0)
    monkey_set_mtds = models.MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
    monkey_set_eevs = models.ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)

    monkey_set_drink_eevs = monkey_set_eevs.filter(eev_event_type=models.ExperimentEventType.Drink)
    if DAYTIME and not NIGHTTIME:
        monkey_set_drink_eevs = monkey_set_drink_eevs.Day()
    if NIGHTTIME and not DAYTIME:
        monkey_set_drink_eevs = monkey_set_drink_eevs.Night()

    start_time = datetime.datetime.now()
    total_loops = len(monkey_set)
    for _loop_index, _monkey in enumerate(monkey_set):
        print "%s:  Starting monkey loop# %d of %d" % (str(datetime.datetime.now()), _loop_index, total_loops)
        _time_per_loop = (datetime.datetime.now()-start_time).seconds / _loop_index
        print "%s:  Average time per loop:  %.2f minutes" % (str(datetime.datetime.now()), _time_per_loop/60)
        print "%s:  Guestimated total time:  %.2f minutes" % (str(datetime.datetime.now()), (_time_per_loop/60)*total_loops)
        _etc = start_time + datetime.timedelta(seconds=_time_per_loop*total_loops)
        print "%s:  Guestimated ETC:  %s" % (str(datetime.datetime.now()), _etc)
        print "--"
        _monkey_weight = monkey_set_mtds.filter(monkey=_monkey).aggregate(models.Avg('mtd_weight'))['mtd_weight__avg']
        _monkey_eevs = monkey_set_drink_eevs.filter(monkey=_monkey)
        _monkey_eevs_count = _monkey_eevs.count() * 1.
        current_eevs = 0
        for _minutes in range(0, minutes+1, minutes_gap):
            if _minutes % 60 == 0:
                print "%s:  Starting minute %d of %d" % (str(datetime.datetime.now()), _minutes, minutes)
            _monkey_minute_eevs = _monkey_eevs.filter(eev_pellet_time__gte=_minutes*60)
            if _minutes != minutes: # if this isn't the last minutes loop, add an upper bound
                _monkey_minute_eevs = _monkey_minute_eevs.filter(eev_pellet_time__lte=(_minutes+minutes_gap)*60)
            summed_value = _monkey_minute_eevs.aggregate(sf=models.Sum(summed_field))['sf']
            if summed_value is None:
                continue
            gkg_conversion = summed_value * .04 / _monkey_weight
            gkg_by_minute_from_pellet[_minutes] +=  gkg_conversion
            current_eevs += _monkey_minute_eevs.count()
            if current_eevs == _monkey_eevs_count:
                break
    return gkg_by_minute_from_pellet


def oa_eev_gkg_summation_by_minutesFromPellet(drinking_category, minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    folder_name = "matrr/utils/DATA/json/"
    filename_concatination = "DAYTIME" if DAYTIME else ""
    filename_concatination += "NIGHTTIME" if NIGHTTIME else ""
    file_name = "oa_eev_gkg_summation_by_minutesFromPellet-%s-%s-%s.json" % (drinking_category, str(minutes), filename_concatination)
    file_path = os.path.join(folder_name, file_name)

    monkey_set = plotting.RDD_56890[drinking_category]
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        gkg_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        gkg_by_minute_from_pellet = eev_gkg_summation_by_minute_general(monkey_set, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME)
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
        except IOError:
            pass
        f = open(file_path, 'w')
        json_data = json.dumps(gkg_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), file_path)
    xlabel = "Minutes since last pellet"
    ylabel = "Average EtOH intake per monkey, g/kg"
    title = "Average intake by minute after pellet"
    return gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def oa_eev_gkg_summation_high_vs_low(category_half='high', minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    assert category_half in ('high', 'low'), "Use 'low' or 'high' for the category_half argument."
    if category_half == 'high':
        monkey_set = plotting.RDD_56890['VHD']
        monkey_set.extend(plotting.RDD_56890['HD'])
    else:
        monkey_set = plotting.RDD_56890['BD']
        monkey_set.extend(plotting.RDD_56890['LD'])

    folder_name = "matrr/utils/DATA/json/"
    filename_concatination = "DAYTIME" if DAYTIME else ""
    filename_concatination += "NIGHTTIME" if NIGHTTIME else ""
    file_name = "oa_eev_gkg_summation_high_vs_low-%s-%s-%s.json" % (category_half, str(minutes), filename_concatination)
    file_path = os.path.join(folder_name, file_name)
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        highlow_gkg_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        highlow_gkg_by_minute_from_pellet  = eev_gkg_summation_by_minute_general(monkey_set, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME)
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
        except IOError:
            pass
        f = open(file_path, 'w')
        json_data = json.dumps(highlow_gkg_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), file_path)
    xlabel = "Minutes since last pellet"
    ylabel = "Average volume per monkey (mL)"
    title = "Average intake by minute after pellet"
    return highlow_gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def oa_eev_h2o_gkg_summation_by_minutes_from_pellet(drinking_category, minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    file_name = "oa_eev_h2o_gkg_summation_by_minutes_from_pellet-%s-%s-%s.json" % (drinking_category, str(minutes), filename_concatenation)
    file_path = os.path.join(folder_name, file_name)

    monkey_set = plotting.RDD_56890[drinking_category]
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        gkg_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        gkg_by_minute_from_pellet = eev_gkg_summation_by_minute_general(monkey_set, minutes=minutes, minutes_gap=minutes_gap,
                                                                        DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, summed_field='eev_veh_volume')
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
        except IOError:
            pass
        f = open(file_path, 'w')
        json_data = json.dumps(gkg_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), file_path)
    xlabel = "Minutes since last pellet"
    ylabel = "Average EtOH intake per monkey, g/kg"
    title = "Average intake by minute after pellet"
    return gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def oa_eev_h2o_gkg_summation_high_vs_low(category_half='high', minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    assert category_half in ('high', 'low'), "Use 'low' or 'high' for the category_half argument."
    if category_half == 'high':
        monkey_set = plotting.RDD_56890['VHD']
        monkey_set.extend(plotting.RDD_56890['HD'])
    else:
        monkey_set = plotting.RDD_56890['BD']
        monkey_set.extend(plotting.RDD_56890['LD'])

    folder_name = "matrr/utils/DATA/json/"
    filename_concatination = "DAYTIME" if DAYTIME else ""
    filename_concatination += "NIGHTTIME" if NIGHTTIME else ""
    file_name = "oa_eev_h2o_gkg_summation_high_vs_low-%s-%s-%s.json" % (category_half, str(minutes), filename_concatination)
    file_path = os.path.join(folder_name, file_name)
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        highlow_gkg_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        highlow_gkg_by_minute_from_pellet  = eev_gkg_summation_by_minute_general(monkey_set, minutes=minutes, minutes_gap=minutes_gap,
                                                                                 DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, summed_field='eev_veh_volume')
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
        except IOError:
            pass
        f = open(file_path, 'w')
        json_data = json.dumps(highlow_gkg_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), file_path)
    xlabel = "Minutes since last pellet"
    ylabel = "Average volume per monkey (mL)"
    title = "Average intake by minute after pellet"
    return highlow_gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=120, minutes_gap=10, DAYTIME=True, NIGHTTIME=True, collect_data=oa_eev_volume_summation_high_vs_low):
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(2,1)
    main_gs.update(left=0.08, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.05)
    hi_subplot = fig.add_subplot(main_gs[0, :])
    lo_subplot = fig.add_subplot(main_gs[1, :], sharey=hi_subplot)

    hi_data, hi_count, xlabel, ylabel, title = collect_data(category_half='high', minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME)
    lo_data, lo_count, xlabel, ylabel, title = collect_data(category_half='low', minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME)

    sorted_minutes = sorted([int(x) for x in hi_data.keys()])
    for x in sorted_minutes:
        unicode_x = unicode(x)
        # lower, light drinkers
        if unicode_x in lo_data.keys():
            _a = 0 if lo_data[unicode_x] is None else lo_data[unicode_x]
            _ld = _a / float(hi_count)
        else:
            _ld = 0
        lo_subplot.bar(x, _ld, color='purple', edgecolor='none')
        # higher, heavy drinkers
        _y = 0 if hi_data[unicode_x] is None else hi_data[unicode_x]
        _hd = _y / float(lo_count)
        hi_subplot.bar(x, _hd, color='gold', edgecolor='none')
    hi_subplot.legend([], title="VHD+HD", loc='upper right')
    lo_subplot.legend([], title="BD+LD", loc='upper right')

    hi_subplot.xaxis.set_visible(False)
    lo_subplot.set_xlabel(xlabel)
    fig.text(.01, .5, ylabel, rotation='vertical', verticalalignment='center')
    hi_subplot.set_title(title)
    return fig


def rhesus_oa_volumes_by_timefrompellet_by_category(subplot, drinking_category, minutes=120, minutes_gap=10, DAYTIME=True, NIGHTTIME=True, collect_data=oa_eev_volume_summation_by_minutes_from_pellet):
    a_data, a_count, xlabel, ylabel, title  = collect_data(drinking_category=drinking_category, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME)
    a_count = float(a_count)
    colors = (plotting.RHESUS_COLORS[drinking_category], plotting.RHESUS_COLORS_ACCENT[drinking_category])
    minutes = [int(x) for x in a_data.keys()] # the a_data.keys are dumped to json as strings, which matplotlib doesn't appreciate.
    minutes = sorted(minutes)
    for index, x in enumerate(minutes):
        # lower, light drinkers
        _x = str(x)
        _y = 0 if a_data[_x] is None else a_data[_x]
        _y /= a_count
        subplot.bar(x, _y, width=1, color=colors[index%2], edgecolor='none')
    # rotate the xaxis labels
    subplot.set_xlabel(xlabel)
    subplot.set_ylabel(ylabel)
    subplot.legend((), title=drinking_category, loc=1, frameon=False)
    return subplot, xlabel, ylabel, title


def rhesus_oa_intake_from_pellet_by_category(minutes=120, minutes_gap=10, DAYTIME=True, NIGHTTIME=True, collect_data=oa_eev_volume_summation_by_minutes_from_pellet):
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(4,1)
    main_gs.update(left=0.05, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.02)
    indexes = range(4)
    drinking_categories = list(reversed(plotting.DRINKING_CATEGORIES)) # reversed so that LD is on the bottom, cast to list so .pop() works
    subplot = None
    for yindex in indexes:
        subplot = fig.add_subplot(main_gs[yindex, :], sharex=subplot)
        category = drinking_categories.pop()
        subplot, xlabel, ylabel, title  = rhesus_oa_volumes_by_timefrompellet_by_category(subplot=subplot, drinking_category=category, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, collect_data=collect_data)
        subplot.yaxis.set_visible(False)
        subplot.xaxis.set_visible(False)
    subplot.xaxis.set_visible(True)
    fig.suptitle(title)
    fontsize = 18
    fig.text(.01, .5, ylabel, rotation='vertical', verticalalignment='center', fontsize=fontsize)
    return fig


def create_pellet_volume_graphs(output_path='', graphs='1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16', output_format='png', dpi=80, minutes_gap=1):
    minutes = 12*60
    _graphs = graphs.split(',')

    ###  Half-day graphs, NightTime vs DayTime
    if '1' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, DAYTIME=False, collect_data=oa_eev_volume_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME' % minutes
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '2' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, NIGHTTIME=False, collect_data=oa_eev_volume_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-DAYTIME' % minutes
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '3' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, DAYTIME=False, collect_data=oa_eev_volume_summation_by_minutes_from_pellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME' % minutes
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '4' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, NIGHTTIME=False, collect_data=oa_eev_volume_summation_by_minutes_from_pellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-DAYTIME' % minutes
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    if '5' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_gkg_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '6' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_gkg_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-DAYTIME-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '7' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_gkg_summation_by_minutesFromPellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '8' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_gkg_summation_by_minutesFromPellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-DAYTIME-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    if '9' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_h2o_gkg_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME-h20-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '10' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_h2o_gkg_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-DAYTIME-h20-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '11' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_h2o_gkg_summation_by_minutes_from_pellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME-h20-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '12' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_h2o_gkg_summation_by_minutes_from_pellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-DAYTIME-h20-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    ### All Day graphs
    if '13' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=24*60, minutes_gap=minutes_gap, collect_data=oa_eev_gkg_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-ALLDAY-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '14' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=24*60, minutes_gap=minutes_gap, collect_data=oa_eev_gkg_summation_by_minutes_from_pellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-ALLDAY-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '15' in _graphs:
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=24*60, minutes_gap=minutes_gap, collect_data=oa_eev_h2o_gkg_summation_high_vs_low)
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-ALLDAY-h20-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '16' in _graphs:
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=24*60, minutes_gap=minutes_gap, collect_data=oa_eev_h2o_gkg_summation_by_minutes_from_pellet)
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-ALLDAY-h20-gkg-minutes_gap__%d' % (minutes, minutes_gap)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    return