import numpy
import os
import collections
import datetime
import json
from matrr import models, plotting
from matrr.plotting import plot_tools
from matrr.utils import gadgets
from matplotlib import pyplot, gridspec
# todo: write in the exclude_bec_days bit
def oa_eev_volume_summation_by_minutes_from_pellet(drinking_category=None, minutes=20, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False, damn_config_object=None):
    """
    This method will return a tuple.

    Tuple[0] will be a dictionary of the summed volume of ethanol consumed by monkeys in drinking_category
    Each key will be the number of minutes since the last pellet was taken, and the value at that key will be the volume consumed during that minute.

    Tuple[1] will be the count of monkeys in drinking_category, typically used for averages.
    """
    if damn_config_object:
        minutes = damn_config_object.minutes
        DAYTIME = damn_config_object.DAYTIME
        NIGHTTIME = damn_config_object.NIGHTTIME
        exclude_bec_days = damn_config_object.exclude_bec_days
        drinking_category = None
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    _subject = drinking_category if drinking_category else damn_config_object.monkey
    file_name = "oa_eev_volume_summation_by_minutesFromPellet-%s-%s-%s.json" % (_subject, str(minutes), filename_concatenation)
    file_path = os.path.join(folder_name, file_name)

    if plotting.RDD_56890.has_key(drinking_category):
        monkey_set = plotting.RDD_56890[drinking_category]
    elif damn_config_object:
        monkey_set = [damn_config_object.monkey,]
    else:
        raise Exception("I need either a drinking_category or a damn_config_object")

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

# todo: write in the exclude_bec_days bit
def oa_eev_volume_summation_high_vs_low(category_half='high', minutes=20,  DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False):
    assert category_half in ('high', 'low')
    if category_half == 'high':
        monkey_set = plotting.RDD_56890['VHD']
        monkey_set.extend(plotting.RDD_56890['HD'])
    else:
        monkey_set = plotting.RDD_56890['BD']
        monkey_set.extend(plotting.RDD_56890['LD'])

    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    filename_concatenation = "ALLDAY" if DAYTIME and NIGHTTIME else filename_concatenation
    file_name = "oa_eev_volume_summation_high_vs_low-%s-%s-%s.json" % (category_half, str(minutes), filename_concatenation)
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


def eev_gkg_summation_by_minute_general(monkey_set, minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True, summed_field='eev_etoh_volume', exclude_bec_days=False):
    def convert_to_gkg(value, weight, field_name):
        if field_name == 'eev_etoh_volume': # or any other ethanol field, where units are in mL of 4% ethanol
            return value * .04 / weight
        if field_name == 'eev_veh_volume': # or any other water field, where units are in mL
            return value / weight
        raise Exception("Unknown field name.  Please update this method or fix your use of it.")
    
    gkg_by_minute_from_pellet = collections.defaultdict(lambda: 0)
    monkey_set_mtds = models.MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
    monkey_set_eevs = models.ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)

    if exclude_bec_days:
        monkey_set_bec_mtds = monkey_set_mtds.exclude(bec_record=None)
        bec_dates = monkey_set_bec_mtds.values_list('drinking_experiment__dex_date', flat=True)
        for _date in bec_dates:
            monkey_set_eevs = monkey_set_eevs.exclude(eev_occurred__contains=_date)
        monkey_set_mtds = monkey_set_mtds.exclude(drinking_experiment__dex_date__in=bec_dates)

    monkey_set_drink_eevs = monkey_set_eevs.filter(eev_event_type=models.ExperimentEventType.Drink)
    if DAYTIME and not NIGHTTIME:
        monkey_set_drink_eevs = monkey_set_drink_eevs.Day()
    if NIGHTTIME and not DAYTIME:
        monkey_set_drink_eevs = monkey_set_drink_eevs.Night()

    start_time = datetime.datetime.now()
    total_loops = len(monkey_set)
    for _loop_index, _monkey in enumerate(monkey_set, 1):
        print "%s:  Starting monkey loop# %d of %d" % (str(datetime.datetime.now()), _loop_index, total_loops)
        _time_per_loop = (datetime.datetime.now()-start_time).seconds / _loop_index
        print "%s:  Average time per loop:  %.2f minutes" % (str(datetime.datetime.now()), _time_per_loop/60)
        print "%s:  Guestimated total time:  %.2f minutes" % (str(datetime.datetime.now()), (_time_per_loop/60)*total_loops)
        _etc = start_time + datetime.timedelta(seconds=_time_per_loop*total_loops)
        print "%s:  Guestimated ETC:  %s" % (str(datetime.datetime.now()), _etc)
        _monkey_weight = monkey_set_mtds.filter(monkey=_monkey).aggregate(models.Avg('mtd_weight'))['mtd_weight__avg']
        _monkey_eevs = monkey_set_drink_eevs.filter(monkey=_monkey)
        _monkey_eevs_count = _monkey_eevs.count() * 1.
        current_eevs = 0
        for _minutes in range(0, minutes+1, minutes_gap):
            if _minutes % 100*60 == 0:
                print "%s:  Starting minute %d of %d" % (str(datetime.datetime.now()), _minutes, minutes)
            _monkey_minute_eevs = _monkey_eevs.filter(eev_pellet_time__gte=_minutes*60)
            if _minutes != minutes: # if this isn't the last minutes loop, add an upper bound
                _monkey_minute_eevs = _monkey_minute_eevs.filter(eev_pellet_time__lte=(_minutes+minutes_gap)*60)
            summed_value = _monkey_minute_eevs.aggregate(sf=models.Sum(summed_field))['sf']
            if summed_value is None:
                continue
            gkg_conversion = convert_to_gkg(summed_value, _monkey_weight, summed_field)
            gkg_by_minute_from_pellet[_minutes] +=  gkg_conversion
            current_eevs += _monkey_minute_eevs.count()
            if current_eevs == _monkey_eevs_count:
                break
        print "!!--!!"
    return gkg_by_minute_from_pellet


def oa_eev_gkg_summation_by_minutes_from_pellet(drinking_category, minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    filename_concatenation = "ALLDAY" if DAYTIME and NIGHTTIME else filename_concatenation
    filename_concatenation = filename_concatenation + '-nobec' if exclude_bec_days else filename_concatenation
    file_name = "oa_eev_gkg_summation_by_minutesFromPellet-%s-%s-%s-%s.json" % (drinking_category, str(minutes), str(minutes_gap), filename_concatenation)
    file_path = os.path.join(folder_name, file_name)

    monkey_set = plotting.RDD_56890[drinking_category]
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        gkg_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        gkg_by_minute_from_pellet = eev_gkg_summation_by_minute_general(monkey_set, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, exclude_bec_days=exclude_bec_days)
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
    ylabel = "Average EtOH intake per monkey (g/kg)"
    title = "Average intake by minute after pellet, %s" % filename_concatenation
    gkg_by_minute_from_pellet.pop('720', None) # There is an artifact in the JSON data that took like 2 weeks to generate
                                      # pretty sure its from a <,>,<=, >= type thing, but the last minute has a comparatively HUGE value.
    return gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def oa_eev_gkg_summation_high_vs_low(category_half='high', minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    assert category_half in ('high', 'low'), "Use 'low' or 'high' for the category_half argument."
    if category_half == 'high':
        monkey_set = plotting.RDD_56890['VHD']
        monkey_set.extend(plotting.RDD_56890['HD'])
    else:
        monkey_set = plotting.RDD_56890['BD']
        monkey_set.extend(plotting.RDD_56890['LD'])

    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    filename_concatenation = "ALLDAY" if DAYTIME and NIGHTTIME else filename_concatenation
    filename_concatenation = filename_concatenation + '-nobec' if exclude_bec_days else filename_concatenation
    file_name = "oa_eev_gkg_summation_high_vs_low-%s-%s-%s-%s.json" % (category_half, str(minutes), str(minutes_gap), filename_concatenation)
    file_path = os.path.join(folder_name, file_name)
    try:
        f = open(file_path, 'r')
        json_string = f.readline()
        highlow_gkg_by_minute_from_pellet = json.loads(json_string)
    except IOError:
        print "%s:  Generating and dumping '%s' to file..." % (str(datetime.datetime.now()), file_path)
        highlow_gkg_by_minute_from_pellet  = eev_gkg_summation_by_minute_general(monkey_set, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, exclude_bec_days=exclude_bec_days)
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
    ylabel = "Average EtOH intake per monkey (gkg)"
    title = "Average EtOH intake by minute after pellet, %s" % filename_concatenation
    highlow_gkg_by_minute_from_pellet.pop('720', None) # There is an artifact in the JSON data that took like 2 weeks to generate
                                      # pretty sure its from a <,>,<=, >= type thing, but the last minute has a comparatively HUGE value.
    return highlow_gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title

# todo: write in the exclude_bec_days bit
def oa_eev_h2o_gkg_summation_by_minutes_from_pellet(drinking_category, minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False):
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
    ylabel = "Average H2O intake per monkey (g/kg)"
    title = "Average H2O intake by minute after pellet, %s" % filename_concatenation
    gkg_by_minute_from_pellet.pop('720', None) # There is an artifact in the JSON data that took like 2 weeks to generate
                                      # pretty sure its from a <,>,<=, >= type thing, but the last minute has a comparatively HUGE value.
    return gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title

# todo: write in the exclude_bec_days bit
def oa_eev_h2o_gkg_summation_high_vs_low(category_half='high', minutes=20, minutes_gap=1, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False):
    assert DAYTIME or NIGHTTIME, "You need to include SOME data, ya big dummy."
    assert category_half in ('high', 'low'), "Use 'low' or 'high' for the category_half argument."
    if category_half == 'high':
        monkey_set = plotting.RDD_56890['VHD']
        monkey_set.extend(plotting.RDD_56890['HD'])
    else:
        monkey_set = plotting.RDD_56890['BD']
        monkey_set.extend(plotting.RDD_56890['LD'])

    folder_name = "matrr/utils/DATA/json/"
    filename_concatenation = "DAYTIME" if DAYTIME else ""
    filename_concatenation += "NIGHTTIME" if NIGHTTIME else ""
    filename_concatenation = "ALLDAY" if DAYTIME and NIGHTTIME else filename_concatenation
    file_name = "oa_eev_h2o_gkg_summation_high_vs_low-%s-%s-%s.json" % (category_half, str(minutes), filename_concatenation)
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
    ylabel = "Average H2O intake per monkey (g/kg)"
    title = "Average H2O intake by minute after pellet, %s" % filename_concatenation
    highlow_gkg_by_minute_from_pellet.pop('720', None) # There is an artifact in the JSON data that took like 2 weeks to generate
                                      # pretty sure its from a <,>,<=, >= type thing, but the last minute has a comparatively HUGE value.
    return highlow_gkg_by_minute_from_pellet, len(monkey_set), xlabel, ylabel, title


def rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=120, minutes_gap=10, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False, collect_data=oa_eev_volume_summation_high_vs_low):
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(2,1)
    main_gs.update(left=0.08, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.05)
    hi_subplot = fig.add_subplot(main_gs[0, :])
    lo_subplot = fig.add_subplot(main_gs[1, :], sharey=hi_subplot)

    hi_data, hi_count, xlabel, ylabel, title = collect_data(category_half='high', minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, exclude_bec_days=exclude_bec_days)
    lo_data, lo_count, xlabel, ylabel, title = collect_data(category_half='low', minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, exclude_bec_days=exclude_bec_days)

    sorted_minutes = sorted([int(x) for x in hi_data.keys()])
    _max = 0
    for x in sorted_minutes:
        unicode_x = unicode(x)
        # lower, light drinkers
        if unicode_x in lo_data.keys():
            _ld = 0 if lo_data[unicode_x] is None else lo_data[unicode_x]
            _ld /= float(lo_count)
        else:
            _ld = 0
        # higher, heavy drinkers
        _hd = 0 if hi_data[unicode_x] is None else hi_data[unicode_x]
        _hd /= float(hi_count)
        hi_subplot.bar(x, _hd, color='gold', edgecolor='none')
        lo_subplot.bar(x, _ld, color='purple', edgecolor='none')
        _max = max(_max, _ld, _hd)
    hi_subplot.legend([], title="VHD+HD", loc='upper right')
    lo_subplot.legend([], title="BD+LD", loc='upper right')

    hi_subplot.xaxis.set_visible(False)
    lo_subplot.set_xlabel(xlabel)
    _max = _max * 1.05
    hi_subplot.set_ylim(0, _max)
    lo_subplot.set_ylim(0, _max)
    fig.text(.01, .5, ylabel, rotation='vertical', verticalalignment='center')
    hi_subplot.set_title(title)
    return fig


def rhesus_oa_volumes_by_timefrompellet_by_category(subplot, drinking_category, minutes=120, minutes_gap=10, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False, collect_data=oa_eev_volume_summation_by_minutes_from_pellet):
    a_data, a_count, xlabel, ylabel, title  = collect_data(drinking_category=drinking_category, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, exclude_bec_days=exclude_bec_days)
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


def rhesus_oa_intake_from_pellet_by_category(minutes=120, minutes_gap=10, DAYTIME=True, NIGHTTIME=True, exclude_bec_days=False, collect_data=oa_eev_volume_summation_by_minutes_from_pellet):
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(4,1)
    main_gs.update(left=0.05, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.02)
    indexes = range(4)
    drinking_categories = list(reversed(plotting.DRINKING_CATEGORIES)) # reversed so that LD is on the bottom, cast to list so .pop() works
    subplot = None
    for yindex in indexes:
        subplot = fig.add_subplot(main_gs[yindex, :], sharex=subplot)
        category = drinking_categories.pop()
        subplot, xlabel, ylabel, title  = rhesus_oa_volumes_by_timefrompellet_by_category(subplot=subplot, drinking_category=category, minutes=minutes, minutes_gap=minutes_gap, DAYTIME=DAYTIME, NIGHTTIME=NIGHTTIME, collect_data=collect_data, exclude_bec_days=exclude_bec_days)
        subplot.yaxis.set_visible(False)
        subplot.xaxis.set_visible(False)
    subplot.xaxis.set_visible(True)
    fig.suptitle(title)
    fontsize = 18
    fig.text(.01, .5, ylabel, rotation='vertical', verticalalignment='center', fontsize=fontsize)
    return fig


def create_pellet_volume_graphs(output_path='', graphs='1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20', output_format='png', dpi=80, minutes_gap=1):
    minutes = 12*60
    _graphs = graphs.split(',')

    ###  Half-day graphs, NightTime vs DayTime
    if '1' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME' % minutes
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, DAYTIME=False, collect_data=oa_eev_volume_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '2' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-DAYTIME' % minutes
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, NIGHTTIME=False, collect_data=oa_eev_volume_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '3' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME' % minutes
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, DAYTIME=False, collect_data=oa_eev_volume_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '4' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-DAYTIME' % minutes
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, NIGHTTIME=False, collect_data=oa_eev_volume_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    if '5' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '6' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-DAYTIME-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '7' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '8' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-DAYTIME-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    if '9' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME-H2O-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_h2o_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '10' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-DAYTIME-H2O-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_h2o_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '11' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME-H2O-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, collect_data=oa_eev_h2o_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '12' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-DAYTIME-H2O-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, NIGHTTIME=False, collect_data=oa_eev_h2o_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    ### Ethanol gkg All Day graphs
    if '13' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-ALLDAY-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, collect_data=oa_eev_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '14' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-ALLDAY-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, collect_data=oa_eev_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    ### h2o gkg All Day graphs
    if '15' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-ALLDAY-H2O-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, collect_data=oa_eev_h2o_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '16' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-ALLDAY-H2O-gkg-minutes_gap_%d' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, collect_data=oa_eev_h2o_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    ### ethanol gkg graphs, excluding days where BEC was taken (or rather, days where we have a BEC record
    if '17' in _graphs:
        name = 'rhesus_oa_discrete_minute_volumes_high_vs_low-%d-NIGHTTIME-gkg-minutes_gap_%d-nobec' % (minutes, minutes_gap)
        fig = rhesus_oa_discrete_minute_volumes_high_vs_low(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, exclude_bec_days=True, collect_data=oa_eev_gkg_summation_high_vs_low)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    if '18' in _graphs:
        name = 'rhesus_oa_intake_from_pellet_by_category-%d-NIGHTTIME-gkg-minutes_gap_%d-nobec' % (minutes, minutes_gap)
        fig = rhesus_oa_intake_from_pellet_by_category(minutes=minutes, minutes_gap=minutes_gap, DAYTIME=False, exclude_bec_days=True, collect_data=oa_eev_gkg_summation_by_minutes_from_pellet)
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    if '19' in _graphs:
        name = 'rhesus_oa_percent_etoh_after_last_pellet'
        fig = rhesus_oa_percent_etoh_after_last_pellet()
        gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)

    if '20' in _graphs:  # individual monkey nighttime etoh volume after pellet graphs
        for _category in plotting.RDD_56890.iterkeys():
            for _mky in plotting.RDD_56890[_category]:
                _cfg = DamnThisConfigObject()
                _cfg.monkey = _mky
                _cfg.monkey_category = _category
                fig = monkey_oa_intake_from_pellet(_cfg)
                name = 'monkey_oa_intake_from_pellet-%d-default' % _mky
                gadgets.dump_figure_to_file(fig, name, output_path, output_format, dpi)
    return



def rhesus_oa_percent_etoh_after_last_pellet():
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(4,1)
    main_gs.update(left=0.05, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.02)
    subplot = None
    drinking_categories = plotting.DRINKING_CATEGORIES
    for _index, category in enumerate(drinking_categories):
        subplot = fig.add_subplot(main_gs[_index, :], sharex=subplot)
        subplot = rhesus_oa_percent_etoh_after_last_pellet__category(subplot, category)
        subplot.yaxis.set_visible(False)
        subplot.xaxis.set_visible(False)
    subplot.xaxis.set_visible(True)
    fig.suptitle("Distribution of intra-day EtOH intake relative to pellet distribution, by drinking category")
    subplot.set_xlabel("Percentage of EtOH consumed AFTER daily last pellet")
    fig.text(.01, .5, "Count of days", rotation='vertical', verticalalignment='center')
    return fig


def rhesus_oa_percent_etoh_after_last_pellet__category(subplot, drinking_category):
    monkey_set = plotting.RDD_56890[drinking_category]
    mtds = models.MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkey_set)
    mtds = mtds.exclude(mtd_pct_etoh_post_pellets__lt=0)
    values = mtds.values_list('mtd_pct_etoh_post_pellets', flat=True)
    values = numpy.array(values)
    bin_edges = numpy.arange(0,1,.01)
    subplot.hist(values, bins=bin_edges, normed=False, histtype='bar', alpha=1, color=plotting.RHESUS_COLORS[drinking_category])
    return subplot


def rhesus_oa_bout_intake_rate_vs_TSLPellet():
    fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(4,1)
    main_gs.update(left=0.065, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.06)
    subplot = None
    for index, key in enumerate(plotting.RDD_56890.iterkeys()):
        subplot = fig.add_subplot(main_gs[index,:], sharex=subplot, sharey=subplot)
        _monkeys = plotting.RDD_56890[key]
        category_bouts = models.ExperimentBout.objects.OA().filter(mtd__monkey__in=_monkeys)
        color = plotting.RHESUS_COLORS[key]
        x = category_bouts.values_list("ebt_pellet_elapsed_time_since_last", flat=True)
        y = category_bouts.values_list("ebt_intake_rate", flat=True)
        subplot.scatter(x, y, label=key, color=color, s=15, alpha=.15)
        subplot.xaxis.set_visible(False)
    subplot.xaxis.set_visible(True)
    subplot.set_xlim(xmin=0)
    subplot.set_ylim(ymin=0)
    fig.suptitle("Time since last pellet vs rate of EtOH intake, by drinking category")
    ylabel = "Rate of drinking during bout, gkg/minute"
    fontsize = 12
    fig.text(.01, .5, ylabel, rotation='vertical', verticalalignment='center', fontsize=fontsize)
    subplot.set_xlabel("Seconds since last last pellet")
#    subplot.set_ylabel()
    return fig


def create_allday_from_daynight():
    folder_name = "matrr/utils/DATA/json/"
    def _combine_daynight_json_to_allday(daytime_Filename, nighttime_filename, output_filename):
        daytime_f = open(daytime_Filename, 'r')
        nighttime_f = open(nighttime_filename, 'r')
        daytime_highlow_gkg_by_minute_from_pellet = json.loads(daytime_f.readline())
        nighttime_highlow_gkg_by_minute_from_pellet = json.loads(nighttime_f.readline())

        print "%s:  Combining day/night and dumping '%s' to file..." % (str(datetime.datetime.now()), output_filename)
        allday_highlow_gkg_by_minute_from_pellet = gadgets.sum_dictionaries_by_key(daytime_highlow_gkg_by_minute_from_pellet, nighttime_highlow_gkg_by_minute_from_pellet)

        f = open(output_filename, 'w')
        json_data = json.dumps(allday_highlow_gkg_by_minute_from_pellet)
        f.write(json_data)
        f.close()
        print "%s:  '%s' successfully dumped." % (str(datetime.datetime.now()), output_filename)
        return
    file_pairs = [
            ['oa_eev_gkg_summation_by_minutesFromPellet-BD-720-1-DAYTIME.json',
             'oa_eev_gkg_summation_by_minutesFromPellet-BD-720-1-NIGHTTIME.json',],
             ['oa_eev_gkg_summation_by_minutesFromPellet-HD-720-1-DAYTIME.json',
             'oa_eev_gkg_summation_by_minutesFromPellet-HD-720-1-NIGHTTIME.json',],
             ['oa_eev_gkg_summation_by_minutesFromPellet-LD-720-1-DAYTIME.json',
             'oa_eev_gkg_summation_by_minutesFromPellet-LD-720-1-NIGHTTIME.json',],
             ['oa_eev_gkg_summation_by_minutesFromPellet-VHD-720-1-DAYTIME.json',
             'oa_eev_gkg_summation_by_minutesFromPellet-VHD-720-1-NIGHTTIME.json',],
             ['oa_eev_gkg_summation_high_vs_low-high-720-1-DAYTIME.json',
             'oa_eev_gkg_summation_high_vs_low-high-720-1-NIGHTTIME.json',],
             ['oa_eev_gkg_summation_high_vs_low-low-720-1-DAYTIME.json',
             'oa_eev_gkg_summation_high_vs_low-low-720-1-NIGHTTIME.json',],

             ['oa_eev_h2o_gkg_summation_by_minutes_from_pellet-BD-720-DAYTIME.json',
              'oa_eev_h2o_gkg_summation_by_minutes_from_pellet-BD-720-NIGHTTIME.json',],
             ['oa_eev_h2o_gkg_summation_by_minutes_from_pellet-HD-720-DAYTIME.json',
              'oa_eev_h2o_gkg_summation_by_minutes_from_pellet-HD-720-NIGHTTIME.json',],
             ['oa_eev_h2o_gkg_summation_by_minutes_from_pellet-LD-720-DAYTIME.json',
              'oa_eev_h2o_gkg_summation_by_minutes_from_pellet-LD-720-NIGHTTIME.json',],
             ['oa_eev_h2o_gkg_summation_by_minutes_from_pellet-VHD-720-DAYTIME.json',
              'oa_eev_h2o_gkg_summation_by_minutes_from_pellet-VHD-720-NIGHTTIME.json',],
             ['oa_eev_h2o_gkg_summation_high_vs_low-high-720-DAYTIME.json',
              'oa_eev_h2o_gkg_summation_high_vs_low-high-720-NIGHTTIME.json',],
             ['oa_eev_h2o_gkg_summation_high_vs_low-low-720-DAYTIME.json',
              'oa_eev_h2o_gkg_summation_high_vs_low-low-720-NIGHTTIME.json',]

    ]
    for _day, _night in file_pairs:
        _day_path = os.path.join(folder_name, _day)
        _night_path = os.path.join(folder_name, _night)
        _output_path = _day_path.replace('DAYTIME', 'ALLDAY')
        _combine_daynight_json_to_allday(daytime_Filename=_day_path, nighttime_filename=_night_path, output_filename=_output_path)

#todo: this whole thing
def rhesus_hourly_gkg_boxplot_by_category(fig_size=plotting.HISTOGRAM_FIG_SIZE):
    def _hourly_eev_gkg_summation(eevs, monkey_category, start_time):
        """
        This method will return a list of each monkey's gkg consumed within the events passed in (eevs), for each monkey in monkey_category
        ex.
        [3.2, 1.4, 5.7, 3.5, 2.9]
        """
        folder_name = "matrr/utils/DATA/json/"
        file_name = "rhesus_hourly_gkg_boxplot_by_category-%s-%s.json" % (monkey_category, str(start_time))
        file_path = os.path.join(folder_name, file_name)
        try:
            f = open(file_path, 'r')
            json_string = f.readline()
            events_gkg = json.loads(json_string)
        except Exception as e:
            print "%s:  Generating and dumping '%s' to file..." % (str(datetime.now()), file_path)
            events_gkg = list()
            for monkey in RDD_56890[monkey_category]:
                # first, get the subset of events associated with this monkey
                _eevs = eevs.filter(monkey=monkey)
                # Next, get this monkey's average OPEN ACCESS weight
                mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
                avg_weight = mtds.aggregate(Avg('mtd_weight'))['mtd_weight__avg']
                # to get g/kg, aggregate the volume consumed, multiply by .04 and divide by weight
                etoh_volume = _eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
                if etoh_volume and avg_weight:
                    gkg = etoh_volume * .04 / avg_weight
                else:
                    gkg = 0
                events_gkg.append(gkg)
            try:
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
            except IOError:
                pass
            f = open(file_path, 'w')
            json_data = json.dumps(events_gkg)
            f.write(json_data)
            f.close()
            print "%s:  '%s' successfully dumped." % (str(datetime.now()), file_path)
        return events_gkg

    fig = pyplot.figure(figsize=fig_size, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(3, 3)
    main_gs.update(left=0.04, right=0.98, top=.95, bottom=.07)
    subplot = fig.add_subplot(main_gs[:, :])

    gap_factor = 2
    width = .6 * ONE_HOUR / len(DRINKING_CATEGORIES)
    offset = ONE_HOUR / len(DRINKING_CATEGORIES)
    for index, mky_cat in enumerate(DRINKING_CATEGORIES):
        x_values = numpy.arange(index * offset, TWENTYTWO_HOUR * gap_factor, ONE_HOUR * gap_factor)
        subplot = rhesus_eev_by_hour_boxplot(subplot, x_values, mky_cat, _hourly_eev_gkg_summation, width=width, color=RHESUS_COLORS[mky_cat])

    # Makes all boxplots fully visible
    subplot.set_xlim(xmin=-.5 * ONE_HOUR, xmax=TWENTYTWO_HOUR * gap_factor)
    # shades the graph gray for light-out hours
    subplot.axvspan(gap_factor * LIGHTS_OUT - width * gap_factor, gap_factor * LIGHTS_ON - width * gap_factor, color='black', alpha=.2, zorder=-100)

    # defines X labels
    x_labels = ['%d' % i for i in range(1, 23)]
    # centers xticks, so labels are place in the middle of the hour, rotated
    new_xticks = numpy.arange(0, TWENTYTWO_HOUR * gap_factor, ONE_HOUR * gap_factor)
    subplot.set_xticks(new_xticks)
    xtick_labels = numpy.arange(ONE_HOUR, TWENTYTWO_HOUR+ONE_HOUR, ONE_HOUR) / 60 / 60
    subplot.set_xticklabels(xtick_labels)
    subplot.set_yticklabels([])

    # Create legend
    handles = list()
    labels = list()
    for key in DRINKING_CATEGORIES:
        color = RHESUS_COLORS[key]
        wrect = patches.Rectangle((0, 0), 1, 1, fc=color)
        handles.append(wrect)
        labels.append(key)

    tick_size = 24
    title_size = 32
    label_size = 32
    legend_size = 32
    subplot.legend(handles, labels, loc='upper right', prop={'size': legend_size})
    subplot.tick_params(axis='both', which='major', labelsize=tick_size)
    subplot.tick_params(axis='both', which='minor', labelsize=tick_size)
    subplot.set_title("Intake per hour by Drinking Category", size=title_size)
    subplot.set_ylabel("Total EtOH Intake of Category, g/kg", size=label_size)
    subplot.set_xlabel("Hour of session", size=label_size)
    return fig


class DamnThisConfigObject():
    minutes = 12*60
    minutes_gap = 1
    DAYTIME = False
    NIGHTTIME = True
    exclude_bec_days = False
    collect_data = oa_eev_volume_summation_by_minutes_from_pellet
    figure = None
    subplot = None
    monkey = None
    monkey_category = 'LD'
    xlabel = "Minutes since last pellet"
    ylabel = "Average volume per monkey (mL)"
    title = "Average intake by minute after pellet"

    def gimme_that_data(self):
        a_data, a_count, xlabel, ylabel, title  = self.collect_data(damn_config_object=self)
        a_count = float(a_count)
        colors = (plotting.RHESUS_COLORS[self.monkey_category], plotting.RHESUS_COLORS_ACCENT[self.monkey_category])
        minutes = [int(x) for x in a_data.keys()] # the a_data.keys are dumped to json as strings, which matplotlib doesn't appreciate.
        minutes = sorted(minutes)
        for index, x in enumerate(minutes):
            # lower, light drinkers
            _x = str(x)
            _y = 0 if a_data[_x] is None else a_data[_x]
            _y /= a_count
            self.subplot.bar(x, _y, width=1, color=colors[index%2], edgecolor='none')
        # rotate the xaxis labels
        self.subplot.set_xlabel(xlabel)
        self.subplot.set_ylabel(ylabel)
        self.subplot.legend((), title=self.monkey, loc=1, frameon=False)


def monkey_oa_intake_from_pellet(config_object):
    config_object.figure = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    main_gs = gridspec.GridSpec(1,1)
    main_gs.update(left=0.05, right=.98, top=.94, bottom=.05, wspace=.1, hspace=.02)
    config_object.subplot = config_object.figure.add_subplot(main_gs[:,:])
    config_object.gimme_that_data()
    config_object.subplot.yaxis.set_visible(False)
    config_object.subplot.xaxis.set_visible(False)
    config_object.subplot.xaxis.set_visible(True)
    config_object.figure.suptitle(config_object.title)
    fontsize = 18
    config_object.figure.text(.01, .5, config_object.ylabel, rotation='vertical', verticalalignment='center', fontsize=fontsize)
    return config_object.figure


