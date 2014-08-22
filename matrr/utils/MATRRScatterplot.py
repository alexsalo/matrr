import hashlib
import warnings
import numpy
from matplotlib import pyplot, gridspec
from matrr import models, plotting

cached_data_path = "matrr/utils/DATA/MATRRScatterplot/"

class MATRRScatterplot(object):
    figure = None
    subplot = None

    def __init__(self):
        self.prepare_plot()
        
    def __str__(self):
        return "MATRRScatterplot"

    def prepare_plot(self):
        self.figure = pyplot.figure(figsize=(14, 9), dpi=plotting.DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.05, right=0.99, top=.97, bottom=.1)
        self.subplot = self.figure.add_subplot(gs[:, :])

    def savefig(self, dpi=120):
        m = hashlib.sha224()
        m.update(str(self))
        hash_name = m.hexdigest()
        file_name = str(self) + hash_name + '.png'
        self.figure.savefig(file_name, dpi=dpi)

    def draw_scatterplot(self, data_object):
        self.subplot.scatter(data_object.gather_xaxis_data(),
                             data_object.gather_yaxis_data(),
                             s=data_object.gather_scale_data(),
                             c=data_object.gather_color_data(),
                             marker=data_object.gather_marker_data(),
                             alpha=data_object.gather_alpha_data(),
                             label=data_object.get_label(),
        )

    def style_subplot(self, style_object):
        self.subplot.set_title(style_object.title())
        self.subplot.set_xlabel(style_object.xlabel())
        self.subplot.set_ylabel(style_object.ylabel())
        self.subplot.set_xlim(style_object.xlim())
        self.subplot.set_ylim(style_object.ylim())
        self.subplot.legend(ncol=style_object.legend_columns(),)


class ScatterplotData(object):
    def gather_xaxis_data(self):
        raise NotImplementedError()

    def gather_yaxis_data(self):
        raise NotImplementedError()

    def gather_scale_data(self):
        warnings.warn("Scale data not implemented!")
        return 20

    def gather_color_data(self):
        warnings.warn("Color data not implemented!")
        return 'black'

    def gather_marker_data(self):
        warnings.warn("Marker data not implemented!")
        return 'o'

    def gather_alpha_data(self):
        warnings.warn("Alpha data not implemented!")
        return None

    def get_label(self): return ""


class ScatterplotStyle(object):
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


class MonkeyBingeScatterplotData(ScatterplotData):
    """
    xaxis = days since binge day
    yaxis = gkg intake on binge day
    """
    raw_data = ()
    x_values = ()
    y_values = ()

    def __init__(self, monkey_pk, binge_definition=3, alpha=1):
        self.monkey_pk = monkey_pk
        self.binge_definition = binge_definition
        self.alpha = alpha

    def _gather_raw_data(self):
        mtds = models.MonkeyToDrinkingExperiment.objects.OA().filter(monkey=self.monkey_pk)
        mtds = mtds.order_by('drinking_experiment__dex_date')
        self.raw_data = numpy.array(mtds.values_list('mtd_etoh_g_kg', flat=True))

    def _gather_xy_data(self):
        self._gather_raw_data()

        x_values = list()
        y_values = list()
        days_since_binge = 0
        for gkg_value in self.raw_data:
            if gkg_value > self.binge_definition:  # Today was a binge day
                x_values.append(days_since_binge)
                days_since_binge = 0
                y_values.append(gkg_value)
            else: # not a binge day
                days_since_binge += 1
        self.x_values = numpy.array(x_values)
        self.y_values = numpy.array(y_values)

    def gather_xaxis_data(self):
        if not len(self.x_values):
            self._gather_xy_data()
        return self.x_values

    def gather_yaxis_data(self):
        if not len(self.y_values):
            self._gather_xy_data()
        return self.y_values

    def gather_scale_data(self):
        return 100

    def gather_color_data(self):
        monkey = models.Monkey.objects.get(pk=self.monkey_pk)
        color = plotting.RHESUS_COLORS[monkey.mky_drinking_category]
        return color

    def gather_marker_data(self):
        monkey = models.Monkey.objects.get(pk=self.monkey_pk)
        marker = plotting.DRINKING_CATEGORY_MARKER[monkey.mky_drinking_category]
        return marker

    def gather_alpha_data(self):
        return self.alpha

    def get_label(self): return str(self.monkey_pk)


class MonkeyBingeScatterplotStyle(ScatterplotStyle):
    def __init__(self, binge_definition, xmax, ymax):
        self.binge_definition = binge_definition
        self.xmin = 0
        self.xmax = xmax
        self.ymin = self.binge_definition
        self.ymax = ymax

    def title(self): return "Binge Scatterplot"

    def xlabel(self): return "Days Since gkg > %d" % self.binge_definition

    def ylabel(self): return "Intake on Binge Day (g/kg)"

    def xlim(self): return self.xmin, self.xmax

    def ylim(self): return self.ymin, self.ymax

    def legend_columns(self): return 3
