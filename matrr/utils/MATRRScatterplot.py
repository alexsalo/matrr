import hashlib
import warnings
import numpy
from matplotlib import pyplot, gridspec
import scipy
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
        gs.update(left=0.06, right=0.98, top=.97, bottom=.08)
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

    def draw_regression_line(self, data_object):
        from scipy import stats
        _x = data_object.gather_xaxis_data()
        _y = data_object.gather_yaxis_data()
        regression_data = stats.linregress(_x, _y) # slope, intercept, r_value, p_value, std_err = regression_data
        slope, intercept, r_value, p_value, std_err = regression_data
        reg_label = "Fit: r=%f, p=%f" % (r_value, p_value)
        self.subplot.plot(_x, _x * slope + intercept, label=reg_label, color='black', linewidth=2, alpha=.7)

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


class CohortEphysHormoneScatterplotData(ScatterplotData):
    """
    xaxis = MonkeyEphys.mep_iei
    yaxis = Cortisol Value

    cort values are from EP events, which are stored as str(int) in the MonkeyHormone.mhm_ep_num field

    Values are mapped:
    7 = A1
    8 = A1.1
    9 = A2
    10 = A2.1
    11 = EP7
    12 = A3
    13 = A3.1

    """

    mep_col = 'mep_iei'
    mhm_col = 'mhm_acth'
    x_values = list()
    y_values = list()

    def __init__(self, cohort_pk, ep_num='11', alpha=1):
        self.cohort = models.Cohort.objects.get(pk=cohort_pk)
        self.monkeys = models.Monkey.objects.Drinkers().filter(cohort=self.cohort).order_by('pk')
        self.ep_num = ep_num
        self.alpha = alpha

    def _gather_xy_data(self):
        x_values = list()
        y_values = list()
        for mky in self.monkeys:
            mep_values = models.MonkeyEphys.objects.filter(monkey=mky).values_list(self.mep_col, flat=True)
            mhm_values = models.MonkeyHormone.objects.filter(monkey=mky, mhm_ep_num=self.ep_num).values_list(self.mhm_col, flat=True)
            if not len(mep_values) or not len(mhm_values):
                continue
            size_dif = len(mep_values) - len(mhm_values)
            if size_dif is 0:
                x_values.extend(mep_values)
                y_values.extend(mhm_values)
            else:
                if size_dif < 0: # more cort values than ephys values
                    avg = numpy.mean(mep_values)
                    _x = list(mep_values)
                    _x.extend([avg for i in xrange(size_dif, 0)])
                    x_values.extend(_x)
                    y_values.extend(mhm_values)
                if size_dif > 0: # more ephys values than cort values
                    avg = numpy.mean(mhm_values)
                    _y = list(mhm_values)
                    _y.extend([avg for i in xrange(0, size_dif)])
                    y_values.extend(_y)
                    x_values.extend(mep_values)
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
        colors = list()
        for monkey in self.monkeys:
            if monkey.mky_drinking_category:
                colors.append(plotting.RHESUS_COLORS[monkey.mky_drinking_category])
            else:
                colors.append('black')
        return colors

    def gather_marker_data(self):
        return 'o'
        markers = list()
        for monkey in self.monkeys:
            markers.append(plotting.DRINKING_CATEGORY_MARKER[monkey.mky_drinking_category])
        return markers

    def gather_alpha_data(self):
        return self.alpha

    def get_label(self): return "%s Ephys vs Hormone" % str(self.cohort)


class CohortEphysHormoneScatterplotStyle(ScatterplotStyle):
    mep_col = 'mep_iei'
    mhm_col = 'mhm_acth'

    def __init__(self, cohort_pk, ep_num='11',):
        self.cohort = models.Cohort.objects.get(pk=cohort_pk)
        self.monkeys = models.Monkey.objects.Drinkers().filter(cohort=self.cohort).order_by('pk')
        self.ep_num = ep_num

    def title(self): return "MATRRScatterplot: Ephys vs Hormone EP %s" % self.ep_num

    def xlabel(self): return models.MonkeyEphys._meta.get_field(self.mep_col).verbose_name

    def ylabel(self): return models.MonkeyHormone._meta.get_field(self.mhm_col).verbose_name

    def xlim(self):
        return None

    def ylim(self):
        return None

    def legend_columns(self): return 1


class CohortEphysNecropsyScatterplotData(ScatterplotData):
    """
    xaxis = NecropsySummary field
    yaxis = MonkeyEphys field
    """
    mep_col = 'mep_iei'
    nec_col = 'ncm_sum_g_per_kg_lifetime'
    x_values = list()
    y_values = list()
    alpha=1

    def __init__(self, cohort_pk):
        self.cohort = models.Cohort.objects.get(pk=cohort_pk)
        self.monkeys = models.Monkey.objects.Drinkers().filter(cohort=self.cohort).order_by('pk')

    def _gather_xy_data(self):
        x_values = list()
        y_values = list()
        for mky in self.monkeys:
            meps = models.MonkeyEphys.objects.filter(monkey=mky)
            mep = meps.aggregate(models.Avg(self.mep_col))[self.mep_col+'__avg']
            nec = getattr(models.NecropsySummary.objects.get(monkey=mky), self.nec_col)
            if not mep or not nec:
                self.monkeys = self.monkeys.exclude(pk=mky.pk)
                continue
            x_values.append(nec)
            y_values.append(mep)
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
        colors = list()
        for monkey in self.monkeys:
            if monkey.mky_drinking_category:
                colors.append(plotting.RHESUS_COLORS[monkey.mky_drinking_category])
            else:
                colors.append('black')
        return colors

    def gather_marker_data(self):
        return 'o'

    def gather_alpha_data(self):
        return self.alpha

    def get_label(self): return "%s Ephys vs Necropsy" % str(self.cohort)


class CohortEphysNecropsyScatterplotStyle(ScatterplotStyle):
    """
    xaxis = NecropsySummary field
    yaxis = MonkeyEphys field
    """
    mep_col = 'mep_iei'
    nec_col = 'ncm_sum_g_per_kg_lifetime'

    def __init__(self, cohort_pk):
        self.cohort = models.Cohort.objects.get(pk=cohort_pk)
        self.monkeys = models.Monkey.objects.Drinkers().filter(cohort=self.cohort).order_by('pk')

    def title(self): return "MATRRScatterplot: Ephys vs Necropsy"

    def xlabel(self): return models.MonkeyEphys._meta.get_field(self.mep_col).verbose_name

    def ylabel(self): return models.NecropsySummary._meta.get_field(self.nec_col).verbose_name

    def xlim(self):
        return None

    def ylim(self):
        return None

    def legend_columns(self): return 1

