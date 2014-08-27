import hashlib
import warnings
import numpy
from matplotlib import pyplot, gridspec
from matrr import models, plotting

cached_data_path = "matrr/utils/DATA/MATRRBarplot/"

class MATRRBarplot(object):
    def __init__(self, subplot):
        self.subplot = subplot

    def __str__(self):
        return "MATRRBarplot"

    def draw_Barplot(self, data_object):
        self.subplot.bar(left=data_object.gather_xaxis_data(),
                         height=data_object.gather_yaxis_data(),
                         width=data_object.gather_width_data(),
                         bottom = data_object.gather_bottom_data(),
                         color=data_object.gather_color_data(),
                         edgecolor=data_object.gather_edgecolor_data(),
                         xerr=data_object.gather_xerr_data(),
#                         yerr=data_object.gather_yerr_data(),
                         label=data_object.get_label(),
        )

    def style_subplot(self, style_object):
        self.subplot.set_title(style_object.title())
        self.subplot.set_xlabel(style_object.xlabel())
        self.subplot.set_ylabel(style_object.ylabel())
        self.subplot.set_xlim(style_object.xlim())
        self.subplot.set_ylim(style_object.ylim())
        self.subplot.legend(ncol=style_object.legend_columns(),)


class BarplotData(object):
    def gather_xaxis_data(self):
        raise NotImplementedError()

    def gather_yaxis_data(self):
        raise NotImplementedError()

    def gather_width_data(self):
        warnings.warn("Width data not implemented!")
        return .8

    def gather_bottom_data(self):
        warnings.warn("Bottom data not implemented!")
        return None

    def gather_color_data(self):
        warnings.warn("Color data not implemented!")
        return 'black'

    def gather_edgecolor_data(self):
        warnings.warn("edgecolor data not implemented!")
        return None

    def gather_xerr_data(self):
        warnings.warn("xerr data not implemented!")
        return None

    def gather_yerr_data(self):
        warnings.warn("yerr data not implemented!")
        return None

    def get_label(self): return "No Label"


class BarplotStyle(object):
    def __init__(self):
        raise NotImplementedError()

    def title(self):
        return "Title"

    def xlabel(self):
        return "X Label"

    def ylabel(self):
        return "Y Label"

    def xlim(self):
        return 0,1

    def ylim(self):
        return 0,1

    def legend_columns(self):
        return 1


class MonkeySetBingeBarplotData(BarplotData):
    """
    xaxis = Interval Index
    yaxis = days until next binge
    """

    def __init__(self, monkey_queryset, binge_definition=2,):
        self.monkeys = monkey_queryset
        self.binge_definition = binge_definition
        self.raw_data = ()
        self.monkeys_intervals = list()
        self.max_interval_index = 0
        self.x_values = ()
        self.y_values = ()
        self.yerr = ()

    def _gather_raw_data(self):
        mtds = models.MonkeyToDrinkingExperiment.objects.OA().filter(monkey__in=self.monkeys)
        mtds = mtds.order_by('drinking_experiment__dex_date')
        self.raw_data = mtds.values_list('monkey', 'mtd_etoh_g_kg')

    def _square_the_matrix(self):
        square_list = list()
        for row in self.monkeys_intervals:
            square_row = numpy.zeros(self.max_interval_index)
            for index, value in enumerate(row):
                square_row[index] = value
            square_list.append((square_row))
        self.monkeys_intervals = numpy.array(square_list)

    def _gather_xy_data(self):
        self._gather_raw_data()
        for mky in self.monkeys:
            mky_mtds = self.raw_data.filter(monkey=mky).values_list('mtd_etoh_g_kg', flat=True)
            mky_interval = list()
            days_since_binge = 0
            for gkg_value in mky_mtds:
                if gkg_value > self.binge_definition:  # Today was a binge day
                    mky_interval.append(days_since_binge)
                    days_since_binge = 0
                else: # not a binge day
                    days_since_binge += 1
            self.monkeys_intervals.append(mky_interval)
            print len(mky_interval)
            self.max_interval_index = max(self.max_interval_index, len(mky_interval))
            print self.max_interval_index
        self._square_the_matrix()
        self.monkeys_intervals = numpy.array(self.monkeys_intervals)
        self.x_values = numpy.arange(self.max_interval_index)
        self.y_values = numpy.average(self.monkeys_intervals, axis=0)

    def gather_xaxis_data(self):
        if not len(self.x_values):
            self._gather_xy_data()
        return self.x_values

    def gather_yaxis_data(self):
        if not len(self.y_values):
            self._gather_xy_data()
        return self.y_values

    def gather_yerr_data(self):
        return numpy.std(self.monkeys_intervals, axis=0)

    def get_label(self): return "\n".join([str(m) for m in self.monkeys])


class MonkeyBingeBarplotStyle(BarplotStyle):
    def __init__(self, binge_definition, xmax, ymax):
        self.binge_definition = binge_definition
        self.xmin = 0
        self.xmax = xmax
        self.ymin = self.binge_definition
        self.ymax = ymax

    def title(self): return "Binge Barplot"

    def xlabel(self): return "Interval Index"

    def ylabel(self): return "Days between %dgkg days" % self.binge_definition

    def xlim(self): return 1.05*self.xmin, 100 # 1.05*self.xmax

    def ylim(self): return 1.05*self.ymin, 1.05*self.ymax

    def legend_columns(self): return 3
