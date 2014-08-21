import os
import sys
import hashlib
import warnings
import logging
import json
import itertools
import numpy
import operator
from datetime import timedelta, datetime, date
import networkx as nx
from matplotlib import pyplot, gridspec, ticker, cm, patches, ticker
from scipy import cluster, stats
from django.db.models import Sum, Avg, Min, Max, query
from matrr import models, utils, plotting

cached_data_path = "matrr/utils/DATA/MATRRScatterPlot/"

class MATRRScatterPlot(object):
    cached = False
    figure = None
    figure_title = 'MATRR Scatter Plot'
    xaxis_label = 'X Label'
    yaxis_label = 'Y Label'

    def __init__(self, cached=False,):
        self.cached = cached

    def draw_scatter_plot(self):
        fig = pyplot.figure(figsize=(14, 9), dpi=plotting.DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.05, right=0.99, top=.97, bottom=.1)
        subplot = fig.add_subplot(gs[:, :])

        subplot.scatter(self.gather_xaxis_data(),
                        self.gather_yaxis_data(),
                        s=self.gather_scale_data(),
                        c=self.gather_color_data(),
                        marker=self.gather_marker_data(),
                        alpha=self.gather_alpha_data(),
        )
        subplot.set_title(self.figure_title)
        subplot.set_xlabel(self.xaxis_label)
        subplot.set_ylabel(self.yaxis_label)
        self.adjust_subplot(subplot)
        self.figure = fig
        return fig

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

    def adjust_subplot(self, subplot):
        warnings.warn("Alpha data not implemented!")
        return

    def savefig(self, dpi=200):
        fig = self.draw_scatter_plot()
        m = hashlib.sha224()
        m.update(str(self))
        hash_name = m.hexdigest()
        file_name = str(self) + hash_name + '.png'
        fig.savefig(file_name, dpi=dpi)


    def __str__(self):
        return "MATRRScatterPlot"


class MonkeyBingeScatterPlot(MATRRScatterPlot):
    """
    xaxis = days since binge day
    yaxis = gkg intake on binge day
    """
    _monkey_pk = 0
    _binge_definition = 3 # grams per kilogram

    _raw_data = ()
    _x_values = ()
    _y_values = ()

    def __init__(self, monkey_pk, binge_definition=3, *args, **kwargs):
        super(MonkeyBingeScatterPlot, self).__init__(*args, **kwargs)
        self._monkey_pk = monkey_pk
        self._binge_definition = binge_definition
        self.figure_title = "Monkey %d Binge Scatterplot" % int(monkey_pk)
        self.xaxis_label = "Days Since gkg > %d" % self._binge_definition
        self.yaxis_label = "Intake on Binge Day (g/kg)"

    def _gather_raw_data(self):
        mtds = models.MonkeyToDrinkingExperiment.objects.OA().filter(monkey=self._monkey_pk)
        mtds = mtds.order_by('drinking_experiment__dex_date')
        self._raw_data = numpy.array(mtds.values_list('mtd_etoh_g_kg', flat=True))

    def _gather_xy_data(self):
        self._gather_raw_data()

        x_values = list()
        y_values = list()
        days_since_binge = 0
        for gkg_value in self._raw_data:
            if gkg_value > self._binge_definition:  # Today was a binge day
                x_values.append(days_since_binge)
                days_since_binge = 0
                y_values.append(gkg_value)
            else: # not a binge day
                days_since_binge += 1
        self._x_values = numpy.array(x_values)
        self._y_values = numpy.array(y_values)

    def gather_xaxis_data(self):
        if not len(self._x_values):
            self._gather_xy_data()
        return self._x_values

    def gather_yaxis_data(self):
        if not len(self._y_values):
            self._gather_xy_data()
        return self._y_values

    def gather_scale_data(self):
        return 100

    def gather_color_data(self):
        monkey = models.Monkey.objects.get(pk=self._monkey_pk)
        color = plotting.RHESUS_COLORS[monkey.mky_drinking_category]
        return color

    def gather_marker_data(self):
        monkey = models.Monkey.objects.get(pk=self._monkey_pk)
        marker = plotting.DRINKING_CATEGORY_MARKER[monkey.mky_drinking_category]
        return marker

    def adjust_subplot(self, subplot):
        subplot.set_xlim(xmin=0, xmax=max(300, self._raw_data.max()))
        subplot.set_ylim(ymin=self._binge_definition, ymax=7)
        return

    def __str__(self):
        return "MonkeyBingeScatterPlot.%d" % self._monkey_pk