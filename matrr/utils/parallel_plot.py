import numpy
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
from django.db.models import query, Avg
from matplotlib import pyplot, gridspec
from matrr import models
from matrr.plotting import DEFAULT_DPI, RHESUS_COLORS, DRINKING_CATEGORY_MARKER


def _percentage_of_days_over_x_gkg(mtds, x_gkg):
    assert len(mtds.order_by().values_list('monkey', flat=True).distinct()) == 1, "Nothing about this function will work with an MTD queryset with multiple/zero monkeys"
    max_date = mtds.aggregate(models.Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
    min_date = mtds.aggregate(models.Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
    total_days = float((max_date-min_date).days)
    mtd_values = mtds.values('mtd_etoh_g_kg')
    days_over_x = mtd_values.filter(mtd_etoh_g_kg__gt=x_gkg).count()
    return days_over_x / total_days

def percentage_of_days_over_2_gkg(mtds=None):
    if mtds is None:
        return u"% Days > 2 gkg"
    return _percentage_of_days_over_x_gkg(mtds, 2)

def percentage_of_days_over_3_gkg(mtds=None):
    if mtds is None:
        return u"% Days > 3 gkg"
    return _percentage_of_days_over_x_gkg(mtds, 3)

def percentage_of_days_over_4_gkg(mtds=None):
    if mtds is None:
        return u"% Days > 4 gkg"
    return _percentage_of_days_over_x_gkg(mtds, 4)

def _average_mtd_field_wrapper(mtds, fieldname):
    assert len(mtds.order_by().values_list('monkey', flat=True).distinct()) == 1, "Nothing about this function will work with an MTD queryset with multiple monkeys"
    avg_value = mtds.aggregate(Avg(fieldname))[fieldname+'__avg']
    return numpy.NaN if avg_value is None else avg_value

def average_oa_etoh_intake_gkg(mtds=None):
    if mtds is None:
        return u"Daily Avg Etoh Intake"
    return _average_mtd_field_wrapper(mtds, 'mtd_etoh_g_kg')

def average_oa_water_intake(mtds=None):
    if mtds is None:
        return u"Daily Avg Water Intake"
    return _average_mtd_field_wrapper(mtds, 'mtd_veh_intake')

def average_oa_pellet_intake(mtds=None):
    if mtds is None:
        return u"Daily Avg Pellet Intake"
    return _average_mtd_field_wrapper(mtds, 'mtd_total_pellets')

def average_oa_BEC(mtds=None):
    if mtds is None:
        return u"Average BEC"
    return _average_mtd_field_wrapper(mtds, 'bec_record__bec_mg_pct')

def average_oa_BEC_pct_intake(mtds=None):
    if mtds is None:
        return u"Average % of daily intake at BEC sample"
    return _average_mtd_field_wrapper(mtds, 'bec_record__bec_pct_intake')

def average_oa_Cortisol(mtds=None):
    if mtds is None:
        return u"Average Cortisol"
    return _average_mtd_field_wrapper(mtds, 'mhm_record__mhm_cort')

def average_oa_ACTH(mtds=None):
    if mtds is None:
        return u"Average ACTH"
    return _average_mtd_field_wrapper(mtds, 'mhm_record__mhm_acth')

def average_oa_Testosterone(mtds=None):
    if mtds is None:
        return u"Average Testosterone"
    return _average_mtd_field_wrapper(mtds, 'mhm_record__mhm_t')

def average_oa_Deoxycorticosterone(mtds=None):
    if mtds is None:
        return u"Average DOC"
    return _average_mtd_field_wrapper(mtds, 'mhm_record__mhm_doc')

def average_oa_Aldosterone(mtds=None):
    if mtds is None:
        return u"Average Ald"
    return _average_mtd_field_wrapper(mtds, 'mhm_record__mhm_ald')

def average_oa_DHEAS(mtds=None):
    if mtds is None:
        return u"Average DHEAS"
    return _average_mtd_field_wrapper(mtds, 'mhm_record__mhm_dheas')

def average_oa_max_bout_pct_total_etoh(mtds=None):
    if mtds is None:
        return u"Average Max Bout % of Total Intake"
    return _average_mtd_field_wrapper(mtds, 'mtd_pct_max_bout_vol_total_etoh')

def average_oa_pct_etoh_post_pellets(mtds=None):
    if mtds is None:
        return u"Average % of intake after last pellet"
    return _average_mtd_field_wrapper(mtds, 'mtd_pct_etoh_post_pellets')

def average_oa_daily_bout(mtds=None):
    if mtds is None:
        return u"Average Bouts per Day"
    return _average_mtd_field_wrapper(mtds, 'mtd_etoh_bout')

def average_oa_bout_volume(mtds=None):
    if mtds is None:
        return u"Bout's Average Volume"
    return _average_mtd_field_wrapper(mtds, 'bouts_set__ebt_volume')

def average_oa_volume_first_bout(mtds=None):
    if mtds is None:
        return u"Average First Bout Volume"
    return _average_mtd_field_wrapper(mtds, 'mtd_vol_1st_bout')

def average_oa_bout_pct_volume(mtds=None):
    if mtds is None:
        return u"Bout's Average % of Total intake"
    return _average_mtd_field_wrapper(mtds, 'bouts_set__ebt_pct_vol_total_etoh')

def average_oa_bout_intake_rate(mtds=None):
    if mtds is None:
        return u"Bout's Average Rate of Intake"
    return _average_mtd_field_wrapper(mtds, 'bouts_set__ebt_intake_rate')

def average_oa_bout_time_since_pellet(mtds=None):
    if mtds is None:
        return u"Bout's Average Seconds Since Last Pellet."
    return _average_mtd_field_wrapper(mtds, 'bouts_set__ebt_pellet_elapsed_time_since_last')

def average_oa_bout_start_time(mtds=None):
    if mtds is None:
        return u"Average Bout Start Time"
    return _average_mtd_field_wrapper(mtds, 'bouts_set__ebt_start_time')

def average_oa_drink_volume(mtds=None):
    if mtds is None:
        return u"Average Drink Volume"
    return _average_mtd_field_wrapper(mtds, 'bouts_set__drinks_set__edr_volume')


class MATRRParallelPlot():
    mtd_gather_functions = [
        percentage_of_days_over_4_gkg,
        percentage_of_days_over_3_gkg,
        percentage_of_days_over_2_gkg,
        average_oa_etoh_intake_gkg,
        average_oa_water_intake,
        average_oa_pellet_intake,
        average_oa_max_bout_pct_total_etoh,
        average_oa_pct_etoh_post_pellets,
        average_oa_daily_bout,
        average_oa_bout_volume,
        average_oa_bout_start_time,
        average_oa_volume_first_bout,
        average_oa_bout_pct_volume,
        average_oa_bout_intake_rate,
        average_oa_bout_time_since_pellet,
        average_oa_drink_volume,
        average_oa_BEC,
        average_oa_BEC_pct_intake,
        average_oa_Cortisol,
        average_oa_ACTH,
        average_oa_Testosterone,
        average_oa_Deoxycorticosterone,
        average_oa_Aldosterone,
        average_oa_DHEAS,
    ]
    cached = False
    monkeys = ()
    figure = None
    figure_title = 'MATRR Data Resources'
    parallel_data = defaultdict(lambda: list()) # key: monkey_pk, value: [<scaled plot values>]
    min_data = defaultdict(lambda: 1*10**10) # key: parallel_label, value: maximum observed value # for rescaling
    max_data = defaultdict(lambda: -1*10**10) # key: parallel_label, value: maximum observed value # for rescaling
    parallel_labels = list()

    def __init__(self, monkeys, cached=False):
        self.cached = cached
        if type(monkeys) == query.QuerySet:
            self.monkeys = [str(m) for m in monkeys.order_by('pk').values_list('pk', flat=True)]
        else:
            self.monkeys = [str(m) for m in sorted(monkeys)]
        self.parallel_labels = [g(mtds=None) for g in self.mtd_gather_functions]

    def draw_parallel_plot(self):
        if not self.parallel_data:
            self.gather_data()
        fig = pyplot.figure(figsize=(23, 6), dpi=DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.02, right=0.99, top=.95, bottom=.25, hspace=.25)
        subplot = fig.add_subplot(gs[:, :])

        x_values = range(1, len(self.parallel_labels)+1)
        for _monkey in self.monkeys:
            y_values = self.parallel_data[_monkey]
            if len(y_values) != len(x_values):  # we don't have enough data to plot this monkey.  It's probably 10107.
                continue
            _category = models.Monkey.objects.get(pk=_monkey).mky_drinking_category
            _color = RHESUS_COLORS[_category] if _category else 'black'
            subplot.plot(x_values, y_values, color=_color, alpha=1)
        subplot.set_title(self.figure_title)
        subplot.set_yticks([.15, .5, .85])
        subplot.set_yticklabels(['Low', 'Med', 'High'])
        subplot.set_xticks(x_values)
        subplot.set_xticklabels(self.parallel_labels, rotation=20, ha='right')
        subplot.set_xlim(xmin=0, xmax=len(self.parallel_labels)+1)
        subplot.set_ylim(ymin=-.1, ymax=1.1)
        subplot.xaxis.grid(True, which='major', linestyle='-', linewidth=2)
        self.figure = fig
        return fig

    def gather_data(self):
        def _gather_data():
            for _mky in self.monkeys:
                self.gather_max_min_data(_mky)
            for _mky in self.monkeys:
                self.gather_monkey_data(_mky)

        if self.cached:
            folder_name = path + "/DATA/json/"
            m = hashlib.sha224()
            m.update(str(self))
            hash_name = m.hexdigest()
            file_name = hash_name + '.MATRRParallelPlot.json'
            file_path = os.path.join(folder_name, file_name)
            try:
                fx = open(file_path, 'r')
                docstring = fx.readline()
                json_string = fx.readline()
                data = json.loads(json_string)
                self.parallel_data = data['parallel_data']
                self.max_data = data['max_data']
                self.monkeys = data['monkeys']
            except Exception as e:
                _gather_data()
                data = {'parallel_data': self.parallel_data, 'monkeys': self.monkeys, 'max_data': self.max_data, 'min_data': self.min_data}
                fx = open(file_path, 'w')
                fx.write(str(self) + "\n")
                json_data = json.dumps(data)
                fx.write(json_data)
                fx.flush()
                fx.close()
        else:
            _gather_data()

    def gather_max_min_data(self, monkey_pk):
        mtds = models.MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk).order_by('drinking_experiment__dex_date')
        if mtds.count() < 1: # we need more data.  We always need more data.
            return
        for gather_function in self.mtd_gather_functions:
            _label = gather_function()
            _value = gather_function(mtds)
            self.min_data[_label] = min(self.min_data[_label], _value)
            self.max_data[_label] = max(self.max_data[_label], _value)

    def gather_monkey_data(self, monkey_pk):
        if not self.min_data and self.max_data:
            raise Exception("where'd my mins and maxs go?")
        mtds = models.MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk).order_by('drinking_experiment__dex_date')
        if mtds.count() < 1: # we need more data.  We always need more data.
            return
        for gather_function in self.mtd_gather_functions:
            _label = gather_function()
            _value = gather_function(mtds)
            _scaled_value = self.rescale_value(_value, self.min_data[_label], self.max_data[_label], limitMin=0.0, limitMax=1.0)
            self.parallel_data[monkey_pk].append(_scaled_value)

    def savefig(self, dpi=200):
        fig = self.draw_parallel_plot()
        m = hashlib.sha224()
        m.update(str(self))
        hash_name = m.hexdigest()
        file_name = str(self) + hash_name + '.png'
        fig.savefig(file_name, dpi=dpi)

    @staticmethod
    def rescale_value(valueIn, baseMin, baseMax, limitMin=0.0, limitMax=1.0):
        return (float(limitMax - limitMin) * float(valueIn - baseMin) / float(baseMax - baseMin)) + limitMin

    def __str__(self):
        from django.template.defaultfilters import slugify
        labels = slugify(self.parallel_labels)
        monkeys = slugify(self.monkeys)
        return "MATRRParallelPlot.%s.%s" % (labels, monkeys)

