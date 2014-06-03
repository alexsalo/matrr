import sys
import os
path = os.path.dirname(os.path.realpath(__file__))
if 'matrr-prod' in path:
    sys.path.append('/web/www/matrr-prod')
elif 'matrr-dev' in path:
    sys.path.append('/web/www/matrr-dev')
else:
    sys.path.append('/web/www/matrr-local')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from collections import defaultdict
import hashlib
import json
from django.db.models import Avg, StdDev
import matplotlib
import numpy
from matplotlib import pyplot, gridspec, cm, colors
from matrr import plotting
from matrr.models import MonkeyToDrinkingExperiment
from matrr.plotting import DRINKING_CATEGORIES, DEFAULT_DPI, RHESUS_COLORS, RHESUS_MONKEY_COLORS, \
    RHESUS_MONKEY_MARKERS, ALL_RHESUS_DRINKERS, DRINKING_CATEGORY_MARKER, RHESUS_DRINKERS_DISTINCT, \
    RHESUS_MONKEY_CATEGORY, plot_tools, DEFAULT_FIG_SIZE


def beta():
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(1, 1)
    gs.update(left=0.07, right=0.98, top=.95, bottom=.045, hspace=.25)
    subplot = fig.add_subplot(gs[:, :])

    fnx = lambda : numpy.random.randint(5, 50, 10)
    y = numpy.row_stack((fnx(), fnx(), fnx()))
    x = numpy.arange(10)

    y1, y2, y3 = fnx(), fnx(), fnx()
    subplot.stackplot(x, y1,y2,y3, y1, y2, y3)
    return fig

def smooth(x,window_len=11,window='hanning'):
    """ http://stackoverflow.com/questions/5515720/python-smooth-time-series-data """
    if x.ndim != 1:
            raise ValueError, "smooth only accepts 1 dimension arrays."
    if x.size < window_len:
            raise ValueError, "Input vector needs to be bigger than window size."
    if window_len<3:
            return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
    s=numpy.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat': #moving average
            w=numpy.ones(window_len,'d')
    else:
            w=eval('numpy.'+window+'(window_len)')
    y=numpy.convolve(w/w.sum(),s,mode='same')
    return y[window_len:-window_len+1]




class MATRRStackPlot():
    drinking_category = "VHD"
    mtd_data_fields = ['mtd_etoh_g_kg', 'bec_record__bec_mg_pct', 'mhm_record__mhm_cort', 'mhm_record__mhm_acth',
                       'mhm_record__mhm_t', 'mhm_record__mhm_doc', 'mhm_record__mhm_ald', 'mhm_record__mhm_dheas',
                       # water, pellets, add more shit
                       ]
    baseline = 'zero'
    smooth_period = 3

    figure = None
    monkey_count = 0
    max_data_length = 0
    raw_data = defaultdict(lambda: list())
    normalized_data = dict()
    smoothed_data = dict()
    merged_data = dict()
    normalization_avgs = dict()
    normalization_stds = dict()

    smooth_method = 'moving average'

    mtd_data_colors = ['red', 'orange', 'yellow', 'green',
                       'blue', 'indigo', 'purple', 'black',
                       # water, pellets, add more shit
                       ]

    def __init__(self, drinking_category='VHD', baseline='zero', smooth_method='moving average', smooth_period=10):
        self.drinking_category = drinking_category
        self.baseline = baseline
        self.smooth_method = smooth_method
        self.smooth_period = smooth_period

    def draw_figure(self):
        #        fig = matplotlib.figure.Figure(figsize=(20, 8), dpi=DEFAULT_DPI)
        fig = pyplot.figure(figsize=(23, 6), dpi=DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.03, right=0.98, top=.95, bottom=.045, hspace=.25)
        subplot = fig.add_subplot(gs[:, :])

        stackplot_arguments, stackplot_kwargs = self.collect_stackplot_arguments()
        stackplot = subplot.stackplot(*stackplot_arguments, **stackplot_kwargs)
        color_map = cm.get_cmap('hsv')
        for index, area in enumerate(stackplot):
            area.set_alpha(.4)
            color = color_map(float(index)/len(stackplot))
            area.set_facecolor(color)
            area.set_edgecolor(color)
        subplot.set_title(self.drinking_category)
        subplot.set_xlim(xmin=0)
        self.figure = fig
        return fig

    def draw_stackedbargraph(self):
        fig = pyplot.figure(figsize=(23, 6), dpi=DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.03, right=0.98, top=.95, bottom=.045, hspace=.25)
        subplot = fig.add_subplot(gs[:, :])

        stackplot_arguments, stackplot_kwargs = self.collect_stackplot_arguments()

        bottom = numpy.zeros(len(stackplot_arguments[0]))
        for _data, _color in zip(stackplot_arguments[1], self.mtd_data_colors):
            subplot.bar(stackplot_arguments[0], _data, bottom=bottom, width=1, color=_color, alpha=.3, linewidth=0)
            bottom += numpy.array(_data)
#        for color, area in zip(self.mtd_data_colors, stackplot):
#            area.set_alpha(.4)
#            area.set_facecolor(color)
#            area.set_edgecolor(color)
        subplot.set_title(self.drinking_category)
        subplot.set_xlim(xmin=0)
        self.figure = fig
        return fig

    def draw_sidebyside_bargraph(self):
        fig = pyplot.figure(figsize=(23, 6), dpi=DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.03, right=0.98, top=.95, bottom=.045, hspace=.25)
        subplot = fig.add_subplot(gs[:, :])

        stackplot_arguments, stackplot_kwargs = self.collect_stackplot_arguments()

        bar_width = 1. / len(stackplot_arguments[1])
        x_locations = list(stackplot_arguments[0])
        for _data, _color in zip(stackplot_arguments[1], self.mtd_data_colors):
            print x_locations[0]
            subplot.bar(x_locations, _data, width=bar_width, color=_color, alpha=1, linewidth=0)
            for index, value in enumerate(x_locations):
                x_locations[index] = value + bar_width

        subplot.set_title(self.drinking_category)
        subplot.set_xlim(xmin=0)
        self.figure = fig
        return fig

    def draw_linegraph(self):
        fig = pyplot.figure(figsize=(23, 6), dpi=DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.03, right=0.98, top=.95, bottom=.045, hspace=.25)
        subplot = fig.add_subplot(gs[:, :])

        stackplot_arguments, stackplot_kwargs = self.collect_stackplot_arguments()

        for _data, _color in zip(stackplot_arguments[1], self.mtd_data_colors):
            subplot.plot(stackplot_arguments[0], _data, color=_color, alpha=1, linewidth=3)
        subplot.set_title(self.drinking_category)
        subplot.set_xlim(xmin=0)
        self.figure = fig
        return fig

    def collect_stackplot_arguments(self):
        kwargs = {'baseline': self.baseline }
        args = self.build_stackplot_data()
        return args, kwargs
    
    def build_stackplot_data(self):
        """
            *x* : 1d array of dimension N

            *y* : 2d array of dimension MxN, OR any number 1d arrays each of dimension
                  1xN. The data is assumed to be unstacked. Each of the following
                  calls is legal::

            stackplot(x, y)               # where y is MxN
            stackplot(x, y1, y2, y3, y4)  # where y1, y2, y3, y4, are all 1xNm
        """

        # first we need to gather the data
        if not self.raw_data:
            self.gather_data()
        # then we need to normalize it
        if not self.normalized_data:
            self.normalize_data()
        # then we need to smooth it
        if not self.smoothed_data:
            self.smooth_data()
        # and finally we need to condense them all into 1 timeline
        if not self.merged_data:
            self.merge_data()
        x = range(self.max_data_length)
        y = [self.merged_data[mtd_field] for mtd_field in self.mtd_data_fields]
        return x, y

    def gather_data(self):
        folder_name = path + "/DATA/json/"
        m = hashlib.sha224()
        m.update(str(self))
        hash_name = m.hexdigest()
        file_name = hash_name + '.rawData.json'
        file_path = os.path.join(folder_name, file_name)
        try:
            fx = open(file_path, 'r')
            docstring = fx.readline()
            json_string = fx.readline()
            data = json.loads(json_string)
            self.raw_data = data['raw_data']
            self.monkey_count = data['monkey_count']
            self.max_data_length = data['max_data_length']
        except Exception as e:
            mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__mky_drinking_category=self.drinking_category).order_by('drinking_experiment__dex_date')
            monkeys = mtds.values_list('monkey__pk', flat=True).order_by().distinct()
            for mtd_field in self.mtd_data_fields:
                for _mky in monkeys:
                    mky_mtds = mtds.filter(monkey=_mky)
                    data = mky_mtds.values_list(mtd_field, flat=True)
                    self.max_data_length = max(self.max_data_length, data.count())
                    data = list(data)
                    self.raw_data[mtd_field].append(data)
            self.monkey_count = monkeys.count()
            data = {'raw_data': self.raw_data, 'monkey_count': self.monkey_count, 'max_data_length': self.max_data_length}
            fx = open(file_path, 'w')
            json_data = json.dumps(data)
            fx.write(str(self) + "\n")
            fx.write(json_data)
            fx.close()

    def gather_normalization_parameters(self):
        """
        This hits the database pretty hard, so I cache it to JSON.

        """
        df = "-".join(self.mtd_data_fields)
        s = hashlib.sha224()
        s.update(df)
        file_name = 'MATRRStackPlot.normalizationParameters.%s.json' % s.hexdigest()
        folder_name = path + "/DATA/json/"
        file_path = os.path.join(folder_name, file_name)
        try:
            fx = open(file_path, 'r')
            docstring = fx.readline()
            json_string = fx.readline()
            data = json.loads(json_string)
            self.normalization_avgs = data['normalization_avgs']
            self.normalization_stds = data['normalization_stds']
        except Exception as e:
            all_mtds = MonkeyToDrinkingExperiment.objects.all()
            for mtd_field in self.mtd_data_fields:
                field_mtds = all_mtds.exclude(**{mtd_field: None})
                field_avg = field_mtds.aggregate(avg=Avg(mtd_field))['avg']
                field_std = field_mtds.aggregate(std=StdDev(mtd_field))['std']
                assert field_std > 0, "The standard deviation probably shouldn't ever be 0." # I have to divide by this later on
                self.normalization_avgs[mtd_field] = field_avg
                self.normalization_stds[mtd_field] = field_std
            data = {'normalization_avgs': self.normalization_avgs, 'normalization_stds': self.normalization_stds }
            fx = open(file_path, 'w')
            fx.write(df + "\n")
            json_data = json.dumps(data)
            fx.write(json_data)
            fx.close()

    def normalize_data(self):
        if not self.raw_data:
            self.gather_data()
        self.gather_normalization_parameters()
        for mtd_field in self.mtd_data_fields:
            _normalized_field_data = list()
            for _field_data in self.raw_data[mtd_field]:
                _normalized_monkey_data = list()
                for value in _field_data:
                    if not value is None:
                        norm_value = (value - self.normalization_avgs[mtd_field]) / self.normalization_stds[mtd_field]
                    else:
                        norm_value = value
                    _normalized_monkey_data.append(norm_value)
                _normalized_field_data.append(_normalized_monkey_data)
            self.normalized_data[mtd_field] = _normalized_field_data

    def smooth_data(self):
        if not self.normalized_data:
            self.normalize_data()
        smooth_method = self.get_smooth_method()
        for mtd_field in self.mtd_data_fields:
            _smoothed_field_data = list()
            for _field_data in self.normalized_data[mtd_field]:
                _smoothed_field_data.append(smooth_method(_field_data))
            self.smoothed_data[mtd_field] = _smoothed_field_data

    def merge_data(self, data=None):
        if not self.smoothed_data and not data:
            self.smooth_data()
        data = data if data else self.smoothed_data
        for mtd_field in self.mtd_data_fields:
            for _field_data in data[mtd_field]:
                _new_values = list(numpy.zeros(len(_field_data)))
                for index, value in enumerate(_field_data):
                    averaged = value / self.monkey_count
                    _new_values[index] += averaged # add the monkey value to the summed values
                self.merged_data[mtd_field] = _new_values

    def get_smooth_method(self):
        if self.smooth_method == 'moving average':
            return self.__smooth_by_moving_average
        if self.smooth_method == 'polyfit':
            return self.__smooth_by_polyfit
        raise Exception("I don't know about this smoothing method, %s" % self.smooth_method)

    def __smooth_by_moving_average(self, values_list):
        last_n_values = list()
        smoothed_values = list()
        for value in values_list:
            if len(last_n_values) == self.smooth_period:
                last_n_values.pop(0)
            _value = value if value else 0
            last_n_values.append(_value)
            avg = numpy.mean(last_n_values)
            smoothed_value = 0 if numpy.isnan(avg) else avg
            smoothed_values.append(smoothed_value)
        return smoothed_values

    def __smooth_by_polyfit(self, values_list):
        import scipy
        values_list = self.__smooth_by_moving_average(values_list)
        fit_function = scipy.polyfit(range(len(values_list)), values_list, deg=50)
        smoothed_values = scipy.polyval(fit_function, values_list)
        return smoothed_values

    def __str__(self):
        df = "-".join(self.mtd_data_fields)
        return "MATRRStackPlot.%s.%d.%s" % (self.drinking_category, self.smooth_period, df)


def render_stackplot( category='VHD',smooth_method='polyfit', smooth_period=3, baseline='sym', mtd_data_fields=()):
    """
    smooth_method = ('polyfit', 'moving average' )
    smooth_period = 3
    baseline = ('zero', 'sym', 'wiggle', 'weighted_wiggle')
    """
    category = category.upper()
    assert category in ('VHD', 'HD', 'BD', 'LD'), "You made up that category="
    if not mtd_data_fields:
        mtd_data_fields = ['mtd_etoh_g_kg', 'bec_record__bec_mg_pct', 'mhm_record__mhm_cort', 'mhm_record__mhm_acth',
                           'mhm_record__mhm_t', 'mhm_record__mhm_doc', 'mhm_record__mhm_ald', 'mhm_record__mhm_dheas',
                           #'mtd_total_pellets', 'mtd_veh_intake', 'mtd_pct_max_bout_vol_total_etoh', 'mtd_pct_etoh_post_pellets'
                           ]
    else:
        raise Exception("I haven't added anything to handle colors for len(mtd_data_field) > 8.  You should probably do that now.")

    MSP = MATRRStackPlot(drinking_category=category, smooth_period=smooth_period, baseline=baseline, smooth_method=smooth_method)
    MSP.mtd_data_fields = mtd_data_fields
    fig = MSP.draw_figure()
    m = hashlib.sha224()
    m.update(str(MSP))
    hash_name = m.hexdigest()
    file_name = str(MSP) + hash_name + '.png'
    fig.savefig(file_name, dpi=200)
    return 0

def main():
    import optparse
    p = optparse.OptionParser()
    p.add_option('--category', '-c', default="VHD")
    p.add_option('--smooth_method', '-s', default="polyfit")
    p.add_option('--smooth_period', '-p', default="3")
    p.add_option('--baseline', '-b', default="sym")
    options, arguments = p.parse_args()
    render_stackplot(options.category, options.smooth_method, int(options.smooth_period), options.baseline)

if __name__ == '__main__':
           main()