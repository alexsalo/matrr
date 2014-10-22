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
from scipy import stats
from matplotlib import pyplot, gridspec, cm, colors
from matrr import plotting
from matrr.models import MonkeyToDrinkingExperiment, Monkey
from matrr.plotting import DRINKING_CATEGORIES, DEFAULT_DPI, RHESUS_COLORS, RHESUS_MONKEY_COLORS, \
    RHESUS_MONKEY_MARKERS, ALL_RHESUS_DRINKERS, DRINKING_CATEGORY_MARKER, RHESUS_DRINKERS_DISTINCT, \
    RHESUS_MONKEY_CATEGORY, plot_tools, DEFAULT_FIG_SIZE


class MATRRStandardErrorScatterplot():
    monkeys = None
    gkg_cutoff = 0
    reversed = False

    interval_intake = []
    interval_stderr = []
    daycount = []
    daycount_stderr = []

    figure = None
    title = "Blank Title"

    def __init__(self, gkg_cutoff=3.0, monkeys=(10087, 10088, 10089, 10091)):
        self.gkg_cutoff = gkg_cutoff
        self.monkeys = Monkey.objects.filter(pk__in=monkeys)
        self.title = "%.2f g/kg ethanol cutoff" % self.gkg_cutoff


    def draw_figure(self):
        fig = pyplot.figure(figsize=(23, 6), dpi=DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.03, right=0.98, top=.95, bottom=.045, hspace=.25)
        subplot = fig.add_subplot(gs[:, :])

        if not len(self.interval_intake) == len(self.monkeys):
            self.gather_data()
        mky_colors = [RHESUS_COLORS[mky.mky_drinking_category] for mky in self.monkeys]
        subplot.scatter(x=self.daycount, y=self.interval_intake, c=mky_colors, s=200, alpha=.5)
        subplot.set_title(self.title)
        subplot.set_xlim(xmin=0,)
        self.figure = fig
        return fig

    def gather_data(self):
        folder_name = path + "/DATA/json/"
        m = hashlib.sha224()
        m.update(str(self))
        hash_name = m.hexdigest()
        file_name = 'MATRRStandarErrorScatterplot.' + hash_name + '.rawData.json'
        file_path = os.path.join(folder_name, file_name)
        try:
            fx = open(file_path, 'r')
            docstring = fx.readline()
            json_string = fx.readline()
            data_lists = json.loads(json_string)
        except Exception as e:
            mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions()
            __reversed = '-' if self.reversed else ''
            order_by = '%sdrinking_experiment__dex_date' % __reversed
            mtds = mtds.filter(monkey__in=self.monkeys).order_by(order_by)
            data_lists = [list(), list(), list(), list()]
            for _mky in self.monkeys:
                mky_mtds = mtds.filter(monkey=_mky)
                mky_data = self.collect_data_from_mtds(mtds=mky_mtds)
                for value, storage_container in zip(mky_data, data_lists):
                    storage_container.append(value)
            fx = open(file_path, 'w')
            json_data = json.dumps(data_lists)
            fx.write(str(self) + "\n")
            fx.write(json_data)
            fx.close()
        self.interval_intake = data_lists.pop(0)
        self.interval_stderr = data_lists.pop(0)
        self.daycount = data_lists.pop(0)
        self.daycount_stderr = data_lists.pop(0)

    def collect_data_from_mtds(self, mtds=None):
        if not mtds:
            return numpy.nan, numpy.nan, numpy.nan, numpy.nan
        interval_intakes_averages = list()
        interval_intakes = list()
        daycounts = list()
        for mtd in mtds:
            if mtd.mtd_etoh_g_kg is None:
                continue
            if mtd.mtd_etoh_g_kg >= self.gkg_cutoff:
                # Don't AND these together
                # I need the else triggered regardless of the length of interval_intakes
                if len(interval_intakes) > 0:
                    interval_intakes_averages.append(numpy.mean(interval_intakes))
                    daycounts.append(len(interval_intakes))
                    interval_intakes = list()
            else:
                interval_intakes.append(mtd.mtd_etoh_g_kg)
        if len(interval_intakes) > 0:
            interval_intakes_averages.append(numpy.mean(interval_intakes))
            daycounts.append(len(interval_intakes))
        aaa = numpy.mean(interval_intakes_averages)
        aab = stats.sem(interval_intakes_averages)
        aac = numpy.mean(daycounts)
        aad = stats.sem(daycounts)
        return (numpy.mean(interval_intakes_averages),
                stats.sem(interval_intakes_averages),
                numpy.mean(daycounts),
                stats.sem(daycounts),
        )

    def __str__(self):
        df = "-".join([str(m) for m in self.monkeys])
        return "MATRRStandardErrorScatterplot.%s.%.2f.%s" % (df, self.gkg_cutoff, "reversed" if self.reversed else "")


def render_stackplot():
    """
    """
    return 0

def main():
    import optparse
    p = optparse.OptionParser()
    p.add_option('--category', '-c', default="VHD")
    p.add_option('--smooth_method', '-s', default="polyfit")
    p.add_option('--smooth_period', '-p', default="3")
    p.add_option('--baseline', '-b', default="sym")
    options, arguments = p.parse_args()
    render_stackplot()

if __name__ == '__main__':
           main()