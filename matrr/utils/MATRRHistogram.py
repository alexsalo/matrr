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

cached_data_path = "matrr/utils/DATA/MATRRHistogram/"

class MATRRHistogram(object):
    figure = None
    subplot = None

    def __init__(self):
        self.prepare_plot()
        
    def __str__(self):
        return "MATRRHistogram"

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

    def draw_histogram(self, data_object):
        x=data_object.gather_xaxis_data()
        bins=data_object.gather_bins_data()
        color=data_object.gather_color_data()
        label=data_object.get_label()

#        self.subplot.hist(x=data_object.gather_xaxis_data(),
#                          bins=data_object.gather_bins_data(),
#                          color=data_object.gather_color_data(),
#                          label=data_object.get_label(),
#        )
        self.subplot.hist(x=x, bins=bins, color=color, label=label, histtype='barstacked')

    def style_subplot(self, style_object):
        self.subplot.set_title(style_object.title())
        self.subplot.set_xlabel(style_object.xlabel())
        self.subplot.set_ylabel(style_object.ylabel())
        self.subplot.set_xlim(style_object.xlim())
        self.subplot.set_ylim(style_object.ylim())
        self.subplot.legend(ncol=style_object.legend_columns(),)


class HistogramData(object):
    def gather_xaxis_data(self):
        raise NotImplementedError()

    def gather_bins_data(self):
        warnings.warn("Bins data not implemented!")
        return 10

    def gather_color_data(self):
        warnings.warn("Color data not implemented!")
        return 'black'

    def get_label(self): return ""


class HistogramStyle(object):
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


class MonkeyBingeHistogramData(HistogramData):
    """
    xaxis = days since binge day
    yaxis = gkg intake on binge day
    """
    def __init__(self, monkey_pk, binge_definition=3):
        self.monkey_pk = monkey_pk
        self.binge_definition = binge_definition

    def gather_xaxis_data(self):
        mtds = models.MonkeyToDrinkingExperiment.objects.OA().filter(monkey=self.monkey_pk)
        mtds = mtds.order_by('drinking_experiment__dex_date')
        gkg_data = numpy.array(mtds.values_list('mtd_etoh_g_kg', flat=True))

        x_values = list()
        days_since_binge = 0
        for gkg_value in gkg_data:
            if gkg_value > self.binge_definition:  # Today was a binge day
                x_values.append(days_since_binge)
                days_since_binge = 0
            else: # not a binge day
                days_since_binge += 1
        return numpy.array(x_values)

    def gather_bins_data(self):
        return 30

    def gather_color_data(self):
        monkey = models.Monkey.objects.get(pk=self.monkey_pk)
        color = plotting.RHESUS_COLORS[monkey.mky_drinking_category]
        return color

    def gather_marker_data(self):
        monkey = models.Monkey.objects.get(pk=self.monkey_pk)
        marker = plotting.DRINKING_CATEGORY_MARKER[monkey.mky_drinking_category]
        return marker

    def get_label(self): return str(self.monkey_pk)

class DrinkingCategoryBingeHistogramData(HistogramData):
    """
    xaxis = days since binge day
    yaxis = gkg intake on binge day
    """
    def __init__(self, monkey_set, binge_definition=3):
        self.monkey_set = monkey_set
        self.binge_definition = binge_definition

    def gather_xaxis_data(self):
        mtds = models.MonkeyToDrinkingExperiment.objects.OA()
        category_data = {key: list() for key in plotting.DRINKING_CATEGORIES}
        for mky in self.monkey_set:
            mky_mtds = mtds.filter(monkey=mky).order_by('drinking_experiment__dex_date')
            gkg_data = numpy.array(mky_mtds.values_list('mtd_etoh_g_kg', flat=True))
            mky_values = list()
            days_since_binge = 0
            for gkg_value in gkg_data:
                if gkg_value > self.binge_definition:  # Today was a binge day
                    mky_values.append(days_since_binge)
                    days_since_binge = 0
                else: # not a binge day
                    days_since_binge += 1
            category_data[mky.mky_drinking_category].extend(mky_values)
        return numpy.array([category_data[category] for category in plotting.DRINKING_CATEGORIES])

    def gather_bins_data(self):
        return 30

    def gather_color_data(self):
        return numpy.array([plotting.RHESUS_COLORS[category] for category in plotting.DRINKING_CATEGORIES])

    def get_label(self): return plotting.DRINKING_CATEGORIES





class MonkeyBingeHistogramStyle(HistogramStyle):
    def __init__(self, binge_definition, xmax, ymax):
        raise NotImplementedError()
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
