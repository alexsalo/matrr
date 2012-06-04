from matplotlib import pyplot, cm
from django.db.models.aggregates import Sum, Max, Avg
from matplotlib.patches import Circle, Rectangle
from matplotlib.ticker import NullLocator, FixedLocator
import numpy, dateutil, gc, operator, matplotlib
#from pylab import *
from numpy import polyfit, polyval
from matrr.models import *

###############  matplotlibrc settings
matplotlib.rcParams['figure.subplot.left'] 	= 0.1	# the left side of the subplots of the figure
matplotlib.rcParams['figure.subplot.right'] 	= 0.98	# the right side of the subplots of the figure
matplotlib.rcParams['figure.subplot.bottom'] 	= 0.12	# the bottom of the subplots of the figure
matplotlib.rcParams['figure.subplot.top'] 	= 0.96	# the top of the subplots of the figure
matplotlib.rcParams['figure.subplot.wspace'] 	= 0.05	# the amount of width reserved for blank space between subplots
matplotlib.rcParams['figure.subplot.hspace'] 	= 0.05	# the amount of height reserved for white space between subplots
############### end

DEFAULT_CIRCLE_MAX = 280
DEFAULT_CIRCLE_MIN = 20
DEFAULT_FIG_SIZE = (10,10)
DEFAULT_DPI = 80
COLORS = {'monkey' : "#01852F", 'cohort' : 'black'}

def validate_dates(from_date=False, to_date=False):
	from datetime import datetime, date
	if from_date and not isinstance(from_date, (datetime, date)):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print "Invalid parameter, from_date"
			from_date = None
	if to_date and not isinstance(to_date, (datetime, date)):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print "Invalid parameter, to_date"
			to_date = None
	return from_date, to_date


def Treemap(ax, node_tree, color_tree, size_method, color_method, x_labels=None):
	def addnode(ax, node, color, lower=[0,0], upper=[1,1], axis=0):
		axis %= 2
		draw_rectangle(ax, lower, upper, node, color)
		width = upper[axis] - lower[axis]
		try:
			for child, color in  zip(node, color):
				upper[axis] = lower[axis] + (width * float(size_method(child))) / size_method(node)
				addnode(ax, child, color, list(lower), list(upper), axis + 1)
				lower[axis] = upper[axis]
		except TypeError:
			pass
	def draw_rectangle(ax, lower, upper, node, color):
		c = color_method(color)
		r = Rectangle( lower, upper[0]-lower[0], upper[1] - lower[1],
					   edgecolor='k',
					   facecolor=c)
		ax.add_patch(r)
	def assign_x_labels(ax, labels):
		def sort_patches_by_xcoords(patches):
			sorted_patches = []
			# This method returns a list of patches sorted by each patch's X coordinate
			xcoords = sorted([patch.get_x() for patch in patches])
			for x in xcoords:
				for patch in patches:
					if patch.get_x() == x:
						sorted_patches.append(patch)
			return sorted_patches
		patches = ax.patches
		# A primary_patch is a Rectangle which takes up the full height of the treemap.  In the cohort treemap implementation, a primary patch is a monkey
		primary_patches = [patch for patch in patches if patch.get_height() == 1 and patch.get_width() != 1]
		sorted_patches = sort_patches_by_xcoords(primary_patches)

		label_locations = []
		patch_edge = 0
		for patch in sorted_patches:
			width = patch.get_width()
			_location = patch_edge + (width / 2.)
			label_locations.append(_location)
			patch_edge += width

		Axis_Locator = FixedLocator(label_locations)
		ax.xaxis.set_major_locator(Axis_Locator)
		ax.set_xticklabels(labels, rotation=45)


	addnode(ax, node_tree, color_tree)
	if x_labels:
		assign_x_labels(ax, x_labels)
	else:
		ax.set_xticks([])


### Specific Callables ###
def etoh_intake(queryset):
	return queryset.exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')

def total_pellets(queryset):
	return queryset.exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')

def veh_intake(queryset):
	return queryset.exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')

def mtd_weight(queryset):
	return queryset.exclude(mtd_weight=None).values_list('mtd_weight')

def necropsy_summary_avg_22hr_g_per_kg(queryset):
	summaries = []
	raw_labels = []
	for mky in queryset.order_by("necropsy_summary__ncm_22hr_12mo_avg_g_per_kg", "necropsy_summary__ncm_22hr_6mo_avg_g_per_kg"):
		try:
			summaries.append(mky.necropsy_summary)
			raw_labels.append(str(mky.pk))
		except: # really only catching mky.necropsy_summary == None
			continue
	return [summary.ncm_22hr_6mo_avg_g_per_kg for summary in summaries], [summary.ncm_22hr_12mo_avg_g_per_kg for summary in summaries], raw_labels

def necropsy_summary_etoh_4pct(queryset):
	summaries = []
	raw_labels = []
	for mky in queryset.order_by("necropsy_summary__ncm_etoh_4pct_lifetime", "necropsy_summary__ncm_etoh_4pct_22hr"):
		try:
			summaries.append(mky.necropsy_summary)
			raw_labels.append(str(mky.pk))
		except: # really only catching mky.necropsy_summary == None
			continue
	return [summary.ncm_etoh_4pct_22hr for summary in summaries], [summary.ncm_etoh_4pct_lifetime for summary in summaries], raw_labels

def necropsy_summary_sum_g_per_kg(queryset):
	summaries = []
	raw_labels = []
	for mky in queryset.order_by("necropsy_summary__ncm_sum_g_per_kg_22hr", "necropsy_summary__ncm_sum_g_per_kg_lifetime"):
		try:
			summaries.append(mky.necropsy_summary)
			raw_labels.append(str(mky.pk))
		except: # really only catching mky.necropsy_summary == None
			continue
	return [summary.ncm_sum_g_per_kg_22hr for summary in summaries], [summary.ncm_sum_g_per_kg_lifetime for summary in summaries], raw_labels
### End Specific Callables ###


def cohort_necropsy_avg_22hr_g_per_kg(cohort):
	nec_sums = []
	for monkey in cohort.monkey_set.all():
		try:
			nec_sums.append(monkey.necropsy_summary)
		except NecropsySummary.DoesNotExist:
			continue
	if nec_sums:
		graph_title = 'Average Ethanol Intake for cohort %s during 22 Hour Free Access Phase' % str(cohort)
		x_label = "Ethanol Intake (in g/kg)"
		legend_labels = ('12 Month Average', '6 Month Average')
		return cohort_necropsy_summary_general(necropsy_summary_avg_22hr_g_per_kg, x_label, graph_title, legend_labels, cohort)
	else:
		return False, 'NO MAP'

def cohort_necropsy_etoh_4pct(cohort):
	nec_sums = []
	for monkey in cohort.monkey_set.all():
		try:
			nec_sums.append(monkey.necropsy_summary)
		except NecropsySummary.DoesNotExist:
			continue
	if nec_sums:
		graph_title = 'Total Ethanol Intake for Cohort %s' % str(cohort)
		x_label = "Ethanol Intake (in 4% ml)"
		legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)')
		return cohort_necropsy_summary_general(necropsy_summary_etoh_4pct, x_label, graph_title, legend_labels, cohort)
	else:
		return False, 'NO MAP'

def cohort_necropsy_sum_g_per_kg(cohort):
	nec_sums = []
	for monkey in cohort.monkey_set.all():
		try:
			nec_sums.append(monkey.necropsy_summary)
		except NecropsySummary.DoesNotExist:
			continue
	if nec_sums:
		graph_title = 'Total Ethanol Intake for Cohort %s' % str(cohort)
		x_label = "Ethanol Intake (in g/kg)"
		legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)')
		return cohort_necropsy_summary_general(necropsy_summary_sum_g_per_kg, x_label, graph_title, legend_labels, cohort)
	else:
		return False, 'NO MAP'

def cohort_necropsy_summary_general(specific_callable, x_label, graph_title, legend_labels, cohort):
	from matrr.models import Cohort
	##  Verify argument is actually a cohort
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.  Using monkey's cohort")
		return False, 'NO MAP'

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
	ax1.set_axisbelow(True)
#	ax1.set_title('Average Ethanol Intake for Monkey %s during 22 Hour Free Access Phase' % str(monkey.pk))
	ax1.set_title(graph_title)
	ax1.set_ylabel("Monkey")
	ax1.set_xlabel(x_label)

	cohort_colors =  ['navy', 'slateblue']

	coh_data_1, coh_data_2, cohort_labels = specific_callable(cohort.monkey_set.all())

	if not coh_data_1:
		print("Cohort doesn't have any necropsy summary data for this callable")
		return False, 'NO MAP'

	idx = numpy.arange(len(coh_data_1))
	width = 0.4

	cohort_bar1 = ax1.barh(idx, coh_data_1, width, color=cohort_colors[0])
	cohort_bar2 = ax1.barh(idx+width, coh_data_2, width, color=cohort_colors[1])

	def autolabel(rects, text_color=None):
		import locale
		locale.setlocale(locale.LC_ALL, '')
		for rect in rects:
			width = rect.get_width()
			xloc = width * .98
			clr = text_color if text_color else "black"
			align = 'right'
			yloc = rect.get_y()+rect.get_height()/2.0

			text_width = locale.format("%.1f", width, grouping=True)
			if width > 0:
				ax1.text(xloc, yloc, text_width, horizontalalignment=align, verticalalignment='center', color=clr, weight='bold')

	autolabel(cohort_bar1, 'white')
	autolabel(cohort_bar2, 'white')

	ax1.legend( (cohort_bar2[0], cohort_bar1[0]), legend_labels, loc=4)

	ax1.set_yticks(idx+width)
	ax1.set_yticklabels(cohort_labels)
	return fig, 'map'


def cohort_boxplot_m2de_etoh_intake(cohort, days=10):
	return cohort_boxplot_m2de_general(etoh_intake, "Ethanol Intake (in ml)",cohort, days)

def cohort_boxplot_m2de_veh_intake(cohort, days=10):
	return cohort_boxplot_m2de_general(veh_intake , "Veh Intake",cohort, days)

def cohort_boxplot_m2de_total_pellets(cohort, days=10):
	return cohort_boxplot_m2de_general(total_pellets,"Total Pellets",cohort, days )

def cohort_boxplot_m2de_mtd_weight(cohort, days=10):
	return cohort_boxplot_m2de_general(mtd_weight, "Weight (in kg)", cohort, days )

def cohort_boxplot_m2de_general(specific_callable, y_label, cohort, days=10,):
	from matrr.models import Cohort, MonkeyToDrinkingExperiment
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, 'NO MAP'
	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)
	if cohort_drinking_experiments.count() > 0:
		dates = cohort_drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('-drinking_experiment__dex_date')

		# For each experiment date, gather the drinking data
		data = dict()
		for date in dates[:days]:
			data[str(date.date())] = specific_callable(cohort_drinking_experiments.filter(drinking_experiment__dex_date=date))

		sorted_keys = [item[0] for item in sorted(data.items())]
		sorted_values = [item[1] for item in sorted(data.items())]

		fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
		ax1 = fig.add_subplot(111)
		ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
		ax1.set_axisbelow(True)
		ax1.set_title('MATRR Boxplot')
		ax1.set_xlabel("Date of Experiment")
		ax1.set_ylabel(y_label)

		bp = pyplot.boxplot(sorted_values)
		pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['fliers'], color='red', marker='+')
		xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
		pyplot.setp(xtickNames, rotation=45)
		return fig, 'NO MAP'

	else:
		print "No drinking experiments for this cohort."
		return False, 'NO MAP'


def cohort_boxplot_m2de_month_etoh_intake(cohort, from_date=None, to_date=None, dex_type=''):
	return cohort_boxplot_m2de_month_general(etoh_intake, "Ethanol Intake (in ml)", cohort, from_date, to_date, dex_type)

def cohort_boxplot_m2de_month_veh_intake(cohort, from_date=None, to_date=None, dex_type=''):
	return cohort_boxplot_m2de_month_general(veh_intake , "Veh Intake", cohort, from_date, to_date, dex_type)
	
def cohort_boxplot_m2de_month_total_pellets(cohort, from_date=None, to_date=None, dex_type=''):
	return cohort_boxplot_m2de_month_general(total_pellets,"Total Pellets" , cohort, from_date, to_date, dex_type)
	
def cohort_boxplot_m2de_month_mtd_weight(cohort, from_date=None, to_date=None, dex_type=''):
	return cohort_boxplot_m2de_month_general(mtd_weight, "Weight (in kg)", cohort, from_date, to_date, dex_type)

def cohort_boxplot_m2de_month_general(specific_callable, y_label, cohort, from_date=None, to_date=None, dex_type=''):
	# Gather drinking monkeys from the cohort
	from matrr.models import Cohort, MonkeyToDrinkingExperiment
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, 'NO MAP'

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)

	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_type=dex_type)

	if cohort_drinking_experiments.count() > 0:
		dates = cohort_drinking_experiments.dates('drinking_experiment__dex_date', 'month').order_by('-drinking_experiment__dex_date')

		all_data = dict()
		for date in dates:
			cde_of_month = cohort_drinking_experiments.filter(drinking_experiment__dex_date__month=date.month, drinking_experiment__dex_date__year=date.year)
			all_data[date] = specific_callable(cde_of_month)

		
		sorted_keys = [item[0].strftime("%b %Y") for item in sorted(all_data.items())]
		sorted_values = [item[1] for item in sorted(all_data.items())]

		fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
		ax1 = fig.add_subplot(111)
		ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
		ax1.set_axisbelow(True)
		ax1.set_title('MATRR Boxplot')
		ax1.set_xlabel("Date of Experiment")
		ax1.set_ylabel(y_label)
		pyplot.ylim(ymin=0)

		bp = pyplot.boxplot(sorted_values)
		pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['fliers'], color='red', marker='+')
		xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
		pyplot.setp(xtickNames, rotation=45)
		return fig, "cohort map"
	else:
		print "No drinking experiments for this cohort."
		return False, 'NO MAP'

def convert_timedelta(t):
	if t:
		return t.seconds
	else:
		return None

def cohort_drinking_speed(cohort, dex_type, from_date=None, to_date=None):
	from matrr.models import Cohort, MonkeyToDrinkingExperiment, ExperimentEventType
	from django.db.models import Min

	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return

	mtds = MonkeyToDrinkingExperiment.objects.all()
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		mtds = mtds.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		mtds = mtds.filter(drinking_experiment__dex_date__lte=to_date)
	mtds = mtds.exclude(mtd_etoh_intake=-1)
	if mtds.count() > 0:
		dates = mtds.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
	else:
		return

	monkeys = dict()
	for dex_date in dates:
		mtds_by_day = mtds.filter(drinking_experiment__dex_date=dex_date)

		min_etoh_intake = mtds_by_day.aggregate(Min('mtd_etoh_intake'))['mtd_etoh_intake__min']
		for mtd in mtds_by_day:
			events = mtd.events_set.filter(eev_event_type=ExperimentEventType.Drink, eev_etoh_total__gte=min_etoh_intake).order_by('eev_etoh_total')
			min_occurred = mtd.events_set.filter(eev_event_type=ExperimentEventType.Time).aggregate(Min('eev_occurred'))['eev_occurred__min']
			if events.count() > 0:
				event = events[0]
				if mtd.monkey.mky_id not in monkeys:
					monkeys[mtd.monkey.mky_id] = dict()
				monkeys[mtd.monkey.mky_id][dex_date] = event.eev_occurred - min_occurred # elapsed time since the beginning of the experiment

	for dex_date in dates:
		for event_dates in monkeys.itervalues():
			if dex_date not in event_dates:
				event_dates[dex_date] = None
	formatted_monkeys = dict()
	for monkey, event_dates in monkeys.iteritems():
		formatted_monkeys[monkey] = [ convert_timedelta(event_dates[key]) for key in sorted(event_dates.keys()) ]
	return formatted_monkeys

def cohort_protein_boxplot(cohort=None, protein=None):
	from matrr.models import Cohort, Protein, MonkeyProtein
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, 'NO MAP'
	if not isinstance(protein, Protein):
		try:
			protein = Protein.objects.get(pk=protein)
		except Protein.DoesNotExist:
			print("That's not a valid protein.")
			return False, 'NO MAP'

	monkey_proteins = MonkeyProtein.objects.filter(monkey__in=cohort.monkey_set.all(), protein=protein).order_by('mpn_date')
	if monkey_proteins.count() > 0:
		fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
		ax1 = fig.add_subplot(111)
		ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
		ax1.set_axisbelow(True)
		ax1.set_title('%s : %s' % (str(cohort), str(protein)))
		ax1.set_xlabel("Date of sample")
		ax1.set_ylabel("Sample Value, in %s" % str(protein.pro_units))

		dates = monkey_proteins.values_list('mpn_date', flat=True)
		data = dict()
		for date in dates:
			data[str(date.date())] = monkey_proteins.filter(mpn_date=date).values_list('mpn_value')

		sorted_keys = [item[0] for item in sorted(data.items())]
		sorted_values = [item[1] for item in sorted(data.items())]
		scatter_y = []
		scatter_x = []
		for index, dataset in enumerate(sorted_values):
			for data in dataset:
				scatter_x.append(index+1)
				scatter_y.append(data)

		bp = pyplot.boxplot(sorted_values)
		scat = pyplot.scatter(scatter_x, scatter_y, marker='+', color='purple', s=80)
		pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['fliers'], color='red', marker='o', markersize=10)
		xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
		pyplot.setp(xtickNames, rotation=45)
		return fig, 'NO MAP'

	else:
		print "No MonkeyProteins for this cohort."
		return False, 'NO MAP'

def cohort_bihourly_etoh_treemap(cohort, from_date=None, to_date=None, dex_type=''):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, 'NO MAP'
	size_cache = {}
	def size(thing):
		if isinstance(thing, dict):
			thing = thing['volume']
		"""sum size of child nodes"""
		if isinstance(thing, int) or isinstance(thing, float):
			return thing
		if thing in size_cache:
			return size_cache[thing]
		else:
			size_cache[thing] = reduce(operator.add, [size(x) for x in thing])
			print thing
			return size_cache[thing]

	max_color = 0
	cmap = cm.Greens
	def color_by_pct_of_max_color(color):
		try:
			pct_of_max = 1. * color / max_color
			return cmap(pct_of_max)
		except TypeError:
			return 'white'

	tree = list()
	color_tree = list()

	monkeys = cohort.monkey_set.filter(mky_drinking=True)
	mtd_count = MonkeyToDrinkingExperiment.objects.filter(monkey__in=monkeys).count()
	if not mtd_count:
		print 'This cohort has no MTDs'
		return False, 'NO MAP'
	monkey_pks = []
	for monkey in monkeys:
		monkey_pks.append(str(monkey.pk))
		hour_const = 0
		experiment_len = 22
		block_len = 2

		monkey_exp = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)

		from_date, to_date = validate_dates(from_date, to_date)
		if from_date:
			monkey_exp = monkey_exp.filter(drinking_experiment__dex_date__gte=from_date)
		if to_date:
			monkey_exp = monkey_exp.filter(drinking_experiment__dex_date__lte=to_date)
		if dex_type:
			monkey_exp = monkey_exp.filter(drinking_experiment__dex_type=dex_type)

		monkey_bar = list()
		color_monkey_bar = list()
		for hour_start in range(hour_const,hour_const + experiment_len, block_len ):

			hour_end = hour_start + block_len

			fraction_start = (hour_start-hour_const)*60*60
			fraction_end = (hour_end-hour_const)*60*60

			bouts_in_fraction = ExperimentBout.objects.filter(mtd__in=monkey_exp, ebt_start_time__gte=fraction_start, ebt_start_time__lte=fraction_end)
			mtds_in_fraction = MonkeyToDrinkingExperiment.objects.filter(mtd_id__in=bouts_in_fraction.values_list('mtd', flat=True).distinct())
			volume_sum = bouts_in_fraction.aggregate(Sum('ebt_volume'))['ebt_volume__sum']

			field_name = 'mtd_pct_max_bout_vol_total_etoh_hour_%d' % (hour_start/2)
			bout_pct_total = mtds_in_fraction.exclude(**{field_name:None}).values_list(field_name, flat=True)

			if bout_pct_total:
				bout_pct_total = numpy.array(bout_pct_total)
				avg_max_bout_pct_total = numpy.mean(bout_pct_total)
			else:
				avg_max_bout_pct_total = 0

			if not volume_sum:
				volume_sum = 0.1
			if not avg_max_bout_pct_total:
				avg_max_bout_pct_total = 0.01

			num_days = monkey_exp.values_list('drinking_experiment__dex_date').distinct().count()
			if (num_days * block_len) == 0:
				avg_vol_per_hour = 0.01
			else:
				avg_vol_per_hour = volume_sum / float(num_days * block_len)

			monkey_bar.append(avg_vol_per_hour)
			color_monkey_bar.append(avg_max_bout_pct_total)
			if avg_max_bout_pct_total > max_color:
				max_color = avg_max_bout_pct_total
		tree.append(tuple(monkey_bar))
		color_tree.append(tuple(color_monkey_bar))
	tree = tuple(tree)
	color_tree = tuple(color_tree)

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	left, width = 0.02, 0.73
	bottom, height = 0.05, .85
	left_h = left+width+0.07
	ax_dims = [left, bottom, width, height]

	ax = pyplot.axes(ax_dims)
	ax.set_aspect('equal')
	ax.set_yticks([])

	Treemap(ax, tree, color_tree, size, color_by_pct_of_max_color, x_labels=monkey_pks)

	graph_title = "Bi-hourly distribution of Ethanol Intake"
	if dex_type:
		graph_title +=  " during %s" % dex_type
	elif from_date and to_date:
		graph_title +=  "\nfrom %s, to %s" % (str(from_date.date()), str(to_date.date()))
	elif from_date:
		graph_title +=  " after %s" % str(from_date)
	elif to_date:
		graph_title +=  " before %s" % str(to_date)
	ax.set_title(graph_title)

	## Custom Colorbar
	color_ax = pyplot.axes([left_h, bottom, 0.08, height])
	m = numpy.outer(numpy.arange(0,1,0.01),numpy.ones(10))
	color_ax.imshow(m, cmap=cmap, origin="lower")
	pyplot.xticks(numpy.arange(0))
	labels = [str(int((max_color*100./4)*i))+'%' for i in range(5)]
	pyplot.yticks(numpy.arange(0,101,25), labels)
	color_ax.set_title("Average maximum bout,\nby ethanol intake,\nexpressed as percentage \nof total daily intake\n")

	return fig, 'has_caption'

# Dictionary of ethanol cohort plots VIPs can customize
COHORT_ETOH_TOOLS_PLOTS = {"cohort_boxplot_m2de_month_etoh_intake": 		(cohort_boxplot_m2de_month_etoh_intake,'Monthly Cohort Ethanol Intake boxplot'),
						   "cohort_bihourly_etoh_treemap": 					(cohort_bihourly_etoh_treemap, "Cohort Bihourly Drinking Pattern")}
# Dictionary of protein cohort plots VIPs can customize
COHORT_PROTEIN_TOOLS_PLOTS = {"cohort_protein_boxplot": (cohort_protein_boxplot, "Cohort Protein Boxplot")}

# Dictionary of all cohort plots
COHORT_PLOTS = {}
COHORT_PLOTS.update(COHORT_ETOH_TOOLS_PLOTS)
COHORT_PLOTS.update(COHORT_PROTEIN_TOOLS_PLOTS)
COHORT_PLOTS.update({
				"cohort_necropsy_avg_22hr_g_per_kg": (cohort_necropsy_avg_22hr_g_per_kg, 	'Average Ethanol Intake, 22hr'),
				"cohort_necropsy_etoh_4pct": (cohort_necropsy_etoh_4pct, 					"Total Ethanol Intake, ml"),
				"cohort_necropsy_sum_g_per_kg": (cohort_necropsy_sum_g_per_kg, 				"Total Ethanol Intake, g per kg"),
				"cohort_boxplot_m2de_month_veh_intake": (cohort_boxplot_m2de_month_veh_intake, 			'Cohort Water Intake, by month'),
				"cohort_boxplot_m2de_month_total_pellets": (cohort_boxplot_m2de_month_total_pellets, 	'Cohort Pellets, by month'),
				"cohort_boxplot_m2de_month_mtd_weight": (cohort_boxplot_m2de_month_mtd_weight, 			'Cohort Weight, by month'),
})


def monkey_boxplot_etoh(monkey=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_id=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return
	##  Because this is ethanol data, only bother with drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return False, 'NO MAP'

	##  The fun stuff:
	cohort = monkey.cohort
	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(monkey=monkey)
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('-drinking_experiment__dex_date')

	##  For all dates this monkey drank, collect the ethanol data
	coh_etoh_data = {}
	mky_etoh_data = {}
	for date in dates[:10]:
		coh_etoh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')
		mky_etoh_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')

	sorted_keys = [item[0] for item in sorted(coh_etoh_data.items())]
	sorted_values = [item[1][0] for item in sorted(mky_etoh_data.items())]

	pos = range(1,len(sorted_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, COLORS['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_etoh_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Ethanol Intake (in ml)')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	return fig, 'etoh'

def monkey_boxplot_pellets(monkey=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_id=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return False, 'NO MAP'

	##  The fun stuff:
	cohort = monkey.cohort
	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(monkey=monkey)
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

	coh_pellet_data = {}
	mky_pellet_data = {}
	##  For all dates this monkey drank, collect the data
	for date in dates[:10]:
		coh_pellet_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')
		mky_pellet_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')

	sorted_keys = [item[0] for item in sorted(coh_pellet_data.items())]
	sorted_values = [item[1][0] for item in sorted(mky_pellet_data.items())]

	pos = range(1,len(sorted_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, COLORS['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_pellet_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)
	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Total Pellets')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	return fig, 'pellet'

def monkey_boxplot_veh(monkey=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_id=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return False, 'NO MAP'

	##  The fun stuff:
	cohort = monkey.cohort
	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(monkey=monkey)
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

	##  For all dates this monkey drank, collect the data
	coh_veh_data = {}
	mky_veh_data = {}
	for date in dates[:10]:
		coh_veh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')
		mky_veh_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')

	sorted_keys = [item[0] for item in sorted(coh_veh_data.items())]
	sorted_values = [item[1][0] for item in sorted(mky_veh_data.items())]

	pos = range(1,len(sorted_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, COLORS['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_veh_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Veh Intake')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	return fig, 'veh'

def monkey_boxplot_weight(monkey=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_id=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return False, 'NO MAP'

	##  The fun stuff:
	cohort = monkey.cohort
	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(monkey=monkey)
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

	coh_weight_data = {}
	mky_weight_data = {}
	##  For all dates this monkey drank, collect the data
	for date in dates[:10]:
		coh_weight_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')
		mky_weight_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')

	sorted_keys = [item[0] for item in sorted(coh_weight_data.items())]
	sorted_values = [item[1][0] for item in sorted(mky_weight_data.items())]

	pos = range(1,len(sorted_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, COLORS['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_weight_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Weight (in kg)')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	return fig, 'weight'


def monkey_bouts_drinks(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
			x axis - dates of monkey experiments in range [from_date, to_date] or all possible
			y axis - total number of drinks (bouts * drinks per bout)
			color - number of bouts
			size - drinks per bout
		Circle sizes scaled to range [cirle_min, circle_max]
	"""
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	matplotlib.rcParams['figure.subplot.top'] 	= 0.92
	matplotlib.rcParams['figure.subplot.bottom'] 	= 0.08
	matplotlib.rcParams['figure.subplot.right'] 	= 0.8

	import matplotlib.gridspec as gridspec


	gs = gridspec.GridSpec(2, 1,height_ratios=[2,1])


	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, 'NO MAP'

	if circle_max < circle_min:
		circle_max = DEFAULT_CIRCLE_MAX
		circle_min = DEFAULT_CIRCLE_MIN
	else:
		if circle_max < 10:
			circle_max = DEFAULT_CIRCLE_MAX
		if circle_min < 1:
			circle_min = DEFAULT_CIRCLE_MIN

	drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)
	drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

	if drinking_experiments.count() > 0:
		dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
	else:
		return None, 'NO MAP'
	dr_per_bout =list()
	bouts = list()
	bar_size = list() # ??
	bar_color = list() # max_bout_vol / total intake


	for date in dates:
		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		bouts.append(de.mtd_etoh_bout)
		dr_per_bout.append(de.mtd_etoh_drink_bout)
		bar_size.append(de.mtd_pct_max_bout_vol_total_etoh)
		bar_color.append(de.mtd_max_bout_vol/de.mtd_etoh_intake)

	xaxis = numpy.array(range(1,len(dr_per_bout)+1))
	dr_per_bout       = numpy.array(dr_per_bout)
	bouts   = numpy.array(bouts)

	size_min = circle_min
	size_scale = circle_max - size_min

	patches = []
	for x1,b,pb in zip(xaxis, dr_per_bout, bouts):
		circle = Circle((x1,b*pb), b*0.1)
		patches.append(circle)

	bouts_max = float(dr_per_bout.max())
	total_drinks = [ b*pb for b, pb in zip(dr_per_bout, bouts)]
	rescaled_bouts = [ (b/bouts_max)*size_scale+size_min for b in dr_per_bout ] # rescaled, so that circles will be in range (size_min, size_scale)

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)

#    main graph
	ax1 = fig.add_subplot(111)

	s= ax1.scatter(xaxis, total_drinks, c=bouts, s=rescaled_bouts, alpha=0.4)

	ax1.set_ylabel("Total number of drinks =  bouts * drinks per bout")
	ax1.set_xlabel("Days")

	ax1.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))
	y_max = max(total_drinks)
	pyplot.ylim(0-((y_max*1.25)/2),y_max + y_max*0.25) # + % to show circles under the size legend instead of behind it
	pyplot.xlim(0,len(xaxis) + 2)
	max_y_int = int(round(y_max*1.25))
	y_tick_int = int(round(max_y_int/5))
	ax1.set_yticks(range(0, max_y_int, y_tick_int))
	ax1.yaxis.get_label().set_position((0,0.6))

#	ax1.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())

	cax = fig.add_axes((0.88, 0.4, 0.03, 0.5))
	cb = pyplot.colorbar(s, cax=cax)
	cb.set_label("Number of bouts")

#    size legend
	x =numpy.array(range(1,6))
	y =numpy.array([1,1,1,1,1])

	size_m = size_scale/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = numpy.array(size)

	m = bouts_max/(len(y)-1)
	bout_labels = [ int(round(i*m)) for i in range(1, len(y))] # labels in the range as number of bouts
	bout_labels.insert(0,"1")
	bout_labels.insert(0, "")
	bout_labels.append("")

	ax2 = fig.add_subplot(721)
	ax2.scatter(x, y, s=size, alpha=0.4)
	ax2.set_xlabel("Drinks per bout")
	ax2.yaxis.set_major_locator(NullLocator())
	pyplot.setp(ax2, xticklabels=bout_labels)

	zipped = numpy.vstack(zip(xaxis, total_drinks))
	coordinates = ax1.transData.transform(zipped)
	ids = [de.pk for de in drinking_experiments]
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(ids, xcoords, ycoords)

#	barplot
	ax3 = fig.add_subplot(313)
	
	ax3.get_yaxis().tick_right()
	ax3.yaxis.set_label_position('right')
	ax3.set_ylabel("Max Bout Volume as % of Total Etoh")
	ax3.set_autoscalex_on(False)
	
	import matplotlib.colors as colors
	import matplotlib.cm as cm
	
	# normalize colors to use full range of colormap
	norm = colors.normalize(min(bar_color), max(bar_color))
	
	facecolors = list()
	
	for bar, x, color_value in zip(bar_size, xaxis, bar_color):
		pyplot.bar(x, bar, color=cm.jet(norm(color_value)))
		facecolors.append(cm.jet(norm(color_value)))
		
	ax3.set_xlim(0,len(xaxis) + 2)
	
	# create a collection that we will use in colorbox
	col = matplotlib.collections.Collection(facecolors=facecolors, norm = norm, cmap = cm.jet)
	col.set_array(bar_color)
	
	# colorbor for bar plot
	cax = fig.add_axes((0.88, 0.09, 0.03, 0.25))
	cb = pyplot.colorbar(col, cax=cax)
	cb.set_label("Max Bout Vol / Total Intake")
	
	return fig, datapoint_map

def monkey_bouts_drinks_intraday(mtd=None):
	if not isinstance(mtd, MonkeyToDrinkingExperiment):
		try:
			mtd = MonkeyToDrinkingExperiment.objects.get(mtd_id=mtd)
		except MonkeyToDrinkingExperiment.DoesNotExist:
			print("That's not a valid MonkeyToDrinkingExperiment.")
			return False, 'NO MAP'

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
	ax1.set_axisbelow(True)
	ax1.set_title('Drinks on %s for monkey %s' % (mtd.drinking_experiment.dex_date, str(mtd.monkey.pk)))
	ax1.set_xlabel("Time from Start of Experiment (in seconds)")
	ax1.set_ylabel("Ethanol Amount (in ml)")

	drink_colors = ['red', 'orange']
	bout_colors =  ['green', 'blue']
	colorcount = 0

	bouts = mtd.bouts_set.all()
	if bouts:
		for bout in bouts:
			X = bout.ebt_start_time
			Xend = bout.ebt_length
			Y = bout.ebt_volume
			pyplot.bar(X, Y, width=Xend, color=bout_colors[colorcount%2], alpha=.5, zorder=1)
			for drink in bout.drinks_set.all():
				xaxis = drink.edr_start_time
				yaxis = drink.edr_volume
				pyplot.scatter(xaxis, yaxis, c=drink_colors[colorcount%2], s=60, zorder=2)

			colorcount+= 1

		pyplot.xlim(xmin=0)
		pyplot.ylim(ymin=0)
		if X+Xend > 60*60:
			ax1.set_xticks(range(0, X+Xend, 60*60))
		else:
			ax1.set_xticks(range(0, 60*60+1, 60*60))
		return fig, "bouts intraday"
	else:
		print("No bouts data available for this monkey drinking experiment.")
		return False, 'NO MAP'


def monkey_bouts_vol(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
			x axis - dates of monkey experiments in range [from_date, to_date] or all possible
			y axis - g/kg consumed that day
			color - number of bouts
			size - avg volume per bout
		Circle sizes scaled to range [cirle_min, circle_max]
		Plot saved to filename or to static/images/monkeys-bouts-drinks as mky_[real_id].png and mky_[real_id]-thumb.png
	"""
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	matplotlib.rcParams['figure.subplot.top'] 	= 0.92
	matplotlib.rcParams['figure.subplot.bottom'] 	= 0.08

	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, 'NO MAP'

	if circle_max < circle_min:
		circle_max = DEFAULT_CIRCLE_MAX
		circle_min = DEFAULT_CIRCLE_MIN
	else:
		if circle_max < 10:
			circle_max = DEFAULT_CIRCLE_MAX
		if circle_min < 1:
			circle_min = DEFAULT_CIRCLE_MIN

	drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)

	drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

	if drinking_experiments.count() > 0:
		dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
	else:
		return None, 'NO MAP'

	avg_bout_volumes = list()
	g_per_kg_consumed = list()
	bouts = list()
	for date in dates:
		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		g_per_kg_consumed.append(de.mtd_etoh_g_kg) # y-axis
		bouts.append(de.mtd_etoh_bout) # color
		bouts_volume = de.bouts_set.all().aggregate(Avg('ebt_volume'))['ebt_volume__avg']
		avg_bout_volumes.append(bouts_volume if bouts_volume else 0) # size

	xaxis = numpy.array(range(1,len(avg_bout_volumes)+1))
	avg_bout_volumes = numpy.array(avg_bout_volumes)
	bouts   = numpy.array(bouts)

	size_min = circle_min
	size_scale = circle_max - size_min

	patches = []
	for x1,v in zip(xaxis, avg_bout_volumes):
		circle = Circle((x1,v), v*0.1)
		patches.append(circle)

	volume_max = float(avg_bout_volumes.max())
	rescaled_volumes = [ (vol/volume_max)*size_scale+size_min for vol in avg_bout_volumes ] # rescaled, so that circles will be in range (size_min, size_scale)

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)

#    main graph
	ax1 = fig.add_subplot(111)

	s= ax1.scatter(xaxis, g_per_kg_consumed, c=bouts, s=rescaled_volumes, alpha=0.4)

	ax1.set_ylabel("Daily Ethanol Consumption (in g/kg)")
	ax1.set_xlabel("Days")

	ax1.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))
	y_max = max(g_per_kg_consumed)
	pyplot.ylim(0,y_max + y_max*0.25) # + % to show circles under the size legend instead of behind it
	pyplot.xlim(0,len(xaxis) + 1)

	cb = pyplot.colorbar(s)

	cb.set_label("Number of bouts")

#    size legend
	x =numpy.array(range(1,6))
	y =numpy.array([1,1,1,1,1])

	size_m = size_scale/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = numpy.array(size)

	m = volume_max/(len(y)-1)
	bout_labels = [ int(round(i*m)) for i in range(1, len(y))] # labels in the range as number of bouts
	bout_labels.insert(0,"1")
	bout_labels.insert(0, "")
	bout_labels.append("")

	ax2 = fig.add_subplot(721)
	ax2.scatter(x, y, s=size, alpha=0.4)
	ax2.set_xlabel("Average bout volume")
	ax2.yaxis.set_major_locator(NullLocator())
	pyplot.setp(ax2, xticklabels=bout_labels)

#	regression line
#	fit = polyfit(xaxis, g_per_kg_consumed ,3)
#	xr=polyval(fit, xaxis)
#	ax1.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

	zipped = numpy.vstack(zip(xaxis, g_per_kg_consumed))
	coordinates = ax1.transData.transform(zipped)
	ids = [de.pk for de in drinking_experiments]
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(ids, xcoords, ycoords)

	return fig, datapoint_map


def monkey_errorbox_etoh(monkey=None, **kwargs):
	return monkey_errorbox_general(etoh_intake, 'Ethanol Intake (in ml)', monkey, **kwargs)

def monkey_errorbox_veh(monkey=None, **kwargs):
	return monkey_errorbox_general(veh_intake, 'Veh Intake (in ml)', monkey, **kwargs)

def monkey_errorbox_weight(monkey=None, **kwargs):
	return monkey_errorbox_general(mtd_weight, 'Weight (in kg)', monkey, **kwargs)

def monkey_errorbox_pellets(monkey=None, **kwargs):
	return monkey_errorbox_general(total_pellets, 'Total Pellets', monkey, **kwargs)

def monkey_errorbox_general(specific_callable, y_label, monkey, **kwargs):
	from matrr.models import Monkey, MonkeyToDrinkingExperiment
	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_real_id=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, 'NO MAP'

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return False, 'NO MAP'

	monkey_alpha = .7
	cohort = monkey.cohort

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(monkey=monkey)
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)

	from_date = to_date = dex_type = False
	if kwargs.has_key('dex_type'):
		dex_type = kwargs['dex_type']
	if kwargs.has_key('from_date'):
		from_date = kwargs['from_date']
	if kwargs.has_key('to_date'):
		to_date = kwargs['to_date']
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
		monkey_drinking_experiments = monkey_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
		monkey_drinking_experiments = monkey_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_type=dex_type)
		monkey_drinking_experiments = monkey_drinking_experiments.filter(drinking_experiment__dex_type=dex_type)

	if monkey_drinking_experiments.count() > 0:
		dates = cohort_drinking_experiments.dates('drinking_experiment__dex_date', 'month').order_by('-drinking_experiment__dex_date')

		# For each experiment date, gather the drinking data
		cohort_data = {}
		monkey_data = {}
		for date in dates:
			cde_of_month = cohort_drinking_experiments.filter(drinking_experiment__dex_date__month=date.month, drinking_experiment__dex_date__year=date.year)
			mde_of_month = monkey_drinking_experiments.filter(drinking_experiment__dex_date__month=date.month, drinking_experiment__dex_date__year=date.year)
			cohort_data[date] = specific_callable(cde_of_month)
			monkey_data[date] = specific_callable(mde_of_month)

		monkey_avg = {}
		monkey_std = {}
		for key in monkey_data:
			monkey_avg[key] = numpy.mean(monkey_data[key])
			monkey_std[key] = numpy.std(monkey_data[key])

		coh_sorted_keys = [item[0].strftime("%b %Y") for item in sorted(cohort_data.items())]
		coh_sorted_values = [item[1] for item in sorted(cohort_data.items())]
		mky_sorted_means = [item[1] for item in sorted(monkey_avg.items())]
		mky_sorted_stdevs = [item[1] for item in sorted(monkey_std.items())]
		pos = range(1,len(coh_sorted_values)+1)  # This is what aligns the boxplot with other graphs

		fig1 = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
		ax1 = fig1.add_subplot(111)
		ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
		ax1.set_axisbelow(True)
		ax1.set_title('MATRR Plot')
		ax1.set_xlabel("Date of Experiment")
		ax1.set_ylabel(y_label)

		errorbar = pyplot.errorbar(pos, mky_sorted_means, yerr=mky_sorted_stdevs, fmt='o', ms=8, mfc=COLORS['monkey'], mec=COLORS['monkey'], elinewidth=4, alpha=monkey_alpha)
		bp = pyplot.boxplot(coh_sorted_values)
		plt = pyplot.plot(pos, mky_sorted_means, COLORS['monkey'], linewidth=4, alpha=monkey_alpha)

		errorbar[2][0].set_color(COLORS['monkey'])
		# colors are stored in LineCollections differently, as an RBGA array(list())
		eb20_colors = errorbar[2][0].get_colors()[0] # get_colors()[0] gets rid of an unneeded list
		eb20_colors[3] = monkey_alpha
		error[2][0].set_color(eb20_colors)

		pyplot.setp(bp['boxes'], linewidth=3, color='gray')
		pyplot.setp(bp['whiskers'], linewidth=3, color='gray')
		pyplot.setp(bp['fliers'], color='red', marker='+')
		xtickNames = pyplot.setp(ax1, xticklabels=coh_sorted_keys)
		pyplot.setp(xtickNames, rotation=45)

		pyplot.ylim(ymin=-1) #  add some spacing, keeps the boxplots from hugging teh axis
		oldxlims = pyplot.xlim()
		pyplot.xlim(xmin=oldxlims[0]/2, xmax=oldxlims[1]*1.05) #  add some spacing, keeps the boxplots from hugging teh axis

		return fig1, 'errorbox'
	else:
		return False, 'NO MAP'


def monkey_necropsy_avg_22hr_g_per_kg(monkey):
	try:
		nec_sum = monkey.necropsy_summary
		graph_title = 'Average Ethanol Intake for Monkey %s during 22 Hour Free Access Phase' % str(monkey.pk)
		x_label = "Ethanol Intake (in g/kg)"
		legend_labels = ('12 Month Average', '6 Month Average', '%s 12 Month Average' % str(monkey.pk), '%s 6 Month Average' % str(monkey.pk))
		return monkey_necropsy_summary_general(necropsy_summary_avg_22hr_g_per_kg, x_label, graph_title, legend_labels, monkey)
	except NecropsySummary.DoesNotExist:
		return False, "NO MAP"

def monkey_necropsy_etoh_4pct(monkey):
	try:
		nec_sum = monkey.necropsy_summary
		graph_title = 'Total Ethanol Intake for Monkey %s' % str(monkey.pk)
		x_label = "Ethanol Intake (in 4% ml)"
		legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)', '%s Total Intake (Lifetime)' % str(monkey.pk), '%s Total Intake (22hr)' % str(monkey.pk))
		return monkey_necropsy_summary_general(necropsy_summary_etoh_4pct, x_label, graph_title, legend_labels, monkey)
	except NecropsySummary.DoesNotExist:
		return False, "NO MAP"

def monkey_necropsy_sum_g_per_kg(monkey):
	try:
		nec_sum = monkey.necropsy_summary
		graph_title = 'Total Ethanol Intake for Monkey %s' % str(monkey.pk)
		x_label = "Ethanol Intake (in g/kg)"
		legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)', '%s Total Intake (Lifetime)' % str(monkey.pk), '%s Total Intake (22hr)' % str(monkey.pk))
		return monkey_necropsy_summary_general(necropsy_summary_sum_g_per_kg, x_label, graph_title, legend_labels, monkey)
	except NecropsySummary.DoesNotExist:
		return False, "NO MAP"

def monkey_necropsy_summary_general(specific_callable, x_label, graph_title, legend_labels, monkey, cohort=None):
	from matrr.models import Monkey, Cohort
	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, 'NO MAP'
	if cohort:
		if not isinstance(cohort, Cohort):
			try:
				cohort = Cohort.objects.get(pk=cohort)
			except Cohort.DoesNotExist:
				print("That's not a valid cohort.  Using monkey's cohort")
				cohort = monkey.cohort
	else:
		cohort = monkey.cohort

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
	ax1.set_axisbelow(True)
#	ax1.set_title('Average Ethanol Intake for Monkey %s during 22 Hour Free Access Phase' % str(monkey.pk))
	ax1.set_title(graph_title)
	ax1.set_ylabel("Monkey")
	ax1.set_xlabel(x_label)

	cohort_colors =  ['navy', 'slateblue']
	monkey_colors =  ['goldenrod', 'gold']

	if not monkey.necropsy_summary:
		print("Monkey doesn't have any necropsy summary rows")
		return False, 'NO MAP'

	coh_data_1, coh_data_2, cohort_labels = specific_callable(cohort.monkey_set.exclude(pk=monkey.pk))
	mky_data_1, mky_data_2, monkey_label = specific_callable(cohort.monkey_set.filter(pk=monkey.pk))
	if not mky_data_1[0] or not mky_data_2[0]: # don't draw plots for control monkeys
		return False, 'NO MAP'

	idx = numpy.arange(len(coh_data_1))
	width = 0.4

	cohort_bar1 = ax1.barh(idx, coh_data_1, width, color=cohort_colors[0])
	cohort_bar2 = ax1.barh(idx+width, coh_data_2, width, color=cohort_colors[1])
	monkey_bar1 = ax1.barh(max(idx)+1, mky_data_1, width, color=monkey_colors[0])
	monkey_bar2 = ax1.barh(max(idx)+1+width, mky_data_2, width, color=monkey_colors[1])

	def autolabel(rects, text_color=None):
		import locale
		locale.setlocale(locale.LC_ALL, '')
		for rect in rects:
			width = rect.get_width()
			xloc = width * .98
			clr = text_color if text_color else "black"
			align = 'right'
			yloc = rect.get_y()+rect.get_height()/2.0

			text_width = locale.format("%.1f", width, grouping=True)
			if width > 0:
				ax1.text(xloc, yloc, text_width, horizontalalignment=align, verticalalignment='center', color=clr, weight='bold')

	autolabel(cohort_bar1, 'white')
	autolabel(cohort_bar2, 'white')
	autolabel(monkey_bar1, 'black')
	autolabel(monkey_bar2, 'black')

	ax1.legend( (cohort_bar2[0], cohort_bar1[0], monkey_bar2, monkey_bar1), legend_labels, loc=4)

	idx = numpy.arange(len(coh_data_1)+1)
	cohort_labels.append(str(monkey.pk))
	ax1.set_yticks(idx+width)
	ax1.set_yticklabels(cohort_labels)
	return fig, 'map'

def monkey_protein_stdev(monkey, proteins, afternoon_reading=None):
	try: # silly hack to enforce ability to forloop
		iter(proteins)
	except TypeError:
		proteins = [proteins]

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
	ax1.set_axisbelow(True)

	protein_abbrevs = []
	for protein in proteins:
		protein_abbrevs.append(protein.pro_abbrev)
	protein_title = ", ".join(protein_abbrevs)
	if len(protein_title) > 30: #  title's too long.  got some work to do
		title_abbrev = protein_title[:40].split(', ') # first, chop it to a good length and split it into a list
		title_abbrev.pop(len(title_abbrev)-1) # now, pop off the last value in the list, since its probably a randomly cut string, like "Washi" instead of "Washington"
		protein_title = ", ".join(title_abbrev) # and join the remainders back together
		protein_title += "..." # and tell people we chopped it
	ax1.set_title('Monkey %s: %s' % (str(monkey.pk), protein_title))
	ax1.set_xlabel("Date of sample")
	ax1.set_ylabel("Standard deviation from cohort mean")

	dates = MonkeyProtein.objects.all().values_list('mpn_date', flat=True).distinct().order_by('mpn_date')
	lines = []
	line_labels = []
	for index, protein in enumerate(proteins):
		dates = MonkeyProtein.objects.filter(monkey=monkey, protein=protein).order_by('mpn_date').values_list('mpn_date', flat=True).distinct()
		y_values = []
		for date in dates:
			monkey_protein = MonkeyProtein.objects.get(monkey=monkey, protein=protein, mpn_date=date)
			if afternoon_reading is None:
				y_values.append(monkey_protein.mpn_stdev)
			elif afternoon_reading is True and monkey_protein.mpn_date.hour > 12:
				y_values.append(monkey_protein.mpn_stdev)
			elif afternoon_reading is False and monkey_protein.mpn_date.hour <= 12:
				y_values.append(monkey_protein.mpn_stdev)
			else:
				dates = dates.exclude(mpn_date=date)

		color_map = pyplot.get_cmap('gist_rainbow')
		color = color_map(1.*index/len(proteins))
		lines.append(ax1.plot(dates, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=8, markeredgecolor=color))
		line_labels.append(str(protein.pro_abbrev))

	oldylims = pyplot.ylim()
	y_min = min(oldylims[0], -1 * oldylims[1])
	y_max = max(oldylims[1], -1 * oldylims[0])
	pyplot.ylim(ymin=y_min, ymax=y_max) #  add some spacing, keeps the boxplots from hugging teh axis

	# rotate the xaxis labels
	pyplot.xticks(dates, [str(date.date()) for date in dates], rotation=45)

	# Shink current axis by 20%
	box = ax1.get_position()
	ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])

	# Put a legend to the right of the current axis
	ax1.legend(lines, line_labels, loc='center left', bbox_to_anchor=(1, 0.5))

	return fig, 'NO MAP'

def monkey_protein_pctdev(monkey, proteins, afternoon_reading=None):
	try: # silly hack to enforce ability to forloop
		iter(proteins)
	except TypeError:
		proteins = [proteins]

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
	ax1.set_axisbelow(True)

	protein_abbrevs = []
	for protein in proteins:
		protein_abbrevs.append(protein.pro_abbrev)
	protein_title = ", ".join(protein_abbrevs)
	if len(protein_title) > 30: #  title's too long.  got some work to do
		title_abbrev = protein_title[:40].split(', ') # first, chop it to a good length and split it into a list
		title_abbrev.pop(len(title_abbrev)-1) # now, pop off the last value in the list, since its probably a randomly cut string, like "Washi" instead of "Washington"
		protein_title = ", ".join(title_abbrev) # and join the remainders back together
		protein_title += "..." # and tell people we chopped it
	ax1.set_title('Monkey %s: %s' % (str(monkey.pk), protein_title))
	ax1.set_xlabel("Date of sample")
	ax1.set_ylabel("Percent deviation from cohort mean")

	dates = MonkeyProtein.objects.all().values_list('mpn_date', flat=True).distinct().order_by('mpn_date')
	lines = []
	line_labels = []
	for index, protein in enumerate(proteins):
		dates = MonkeyProtein.objects.filter(monkey=monkey, protein=protein).order_by('mpn_date').values_list('mpn_date', flat=True).distinct()
		y_values = []
		for date in dates:
			monkey_protein = MonkeyProtein.objects.get(monkey=monkey, protein=protein, mpn_date=date)
			if afternoon_reading is None:
				y_values.append(monkey_protein.mpn_pctdev)
			elif afternoon_reading is True and monkey_protein.mpn_date.hour > 12:
				y_values.append(monkey_protein.mpn_pctdev)
			elif afternoon_reading is False and monkey_protein.mpn_date.hour <= 12:
				y_values.append(monkey_protein.mpn_pctdev)
			else:
				dates = dates.exclude(mpn_date=date)

		color_map = pyplot.get_cmap('gist_rainbow')
		color = color_map(1.*index/len(proteins))
		lines.append(ax1.plot(dates, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=8, markeredgecolor=color))
		line_labels.append(str(protein.pro_abbrev))

	oldylims = pyplot.ylim()
	y_min = min(oldylims[0], -1 * oldylims[1])
	y_max = max(oldylims[1], -1 * oldylims[0])
	pyplot.ylim(ymin=y_min, ymax=y_max) #  add some spacing, keeps the boxplots from hugging teh axis

	# rotate the xaxis labels
	pyplot.xticks(dates, [str(date.date()) for date in dates], rotation=45)

	# Shink current axis by 20%
	box = ax1.get_position()
	ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])

	# Put a legend to the right of the current axis
	ax1.legend(lines, line_labels, loc='center left', bbox_to_anchor=(1, 0.5))

	return fig, 'NO MAP'

def monkey_protein_value(monkey, proteins, afternoon_reading=None):
#	try: # silly hack to enforce 1 protein
#		iter(protein)
#		raise Exception("This method CANNOT be called with multiple proteins.  You must create these images individually.")
#	except TypeError:
#		pass
	
	protein = proteins[0]
	print "This method CANNOT be called with multiple proteins.  You must create these images individually."
#		raise Exception("This method CANNOT be called with multiple proteins.  You must create these images individually.")
		

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
	ax1.set_axisbelow(True)

	protein_title = protein.pro_name
	if len(protein_title) > 30: #  title's too long.  got some work to do
		protein_title = protein.pro_abbrev

	ax1.set_title('Monkey %s: %s' % (str(monkey.pk), protein_title))
	ax1.set_xlabel("Date of sample")
	ax1.set_ylabel("Protein Value (in %s)" % protein.pro_units)

#	dates = MonkeyProtein.objects.all().values_list('mpn_date', flat=True).distinct().order_by('mpn_date')

	lines = []
	line_labels = []

	dates = MonkeyProtein.objects.filter(monkey=monkey, protein=protein).order_by('mpn_date').values_list('mpn_date', flat=True).distinct()
	y_values = []
	for date in dates:
		monkey_protein = MonkeyProtein.objects.get(monkey=monkey, protein=protein, mpn_date=date)
		if afternoon_reading is None:
			y_values.append(monkey_protein.mpn_value)
		elif afternoon_reading is True and monkey_protein.mpn_date.hour > 12:
			y_values.append(monkey_protein.mpn_value)
		elif afternoon_reading is False and monkey_protein.mpn_date.hour <= 12:
			y_values.append(monkey_protein.mpn_value)
		else:
			dates = dates.exclude(mpn_date=date)

	color = 'black'
	lines.append(ax1.plot(dates, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=10))
	line_labels.append(str(protein.pro_abbrev))

	#oldylims = pyplot.ylim()
	#y_min = min(oldylims[0], -1 * oldylims[1])
	#y_max = max(oldylims[1], -1 * oldylims[0])
	#pyplot.ylim(ymin=y_min, ymax=y_max) #  add some spacing, keeps the boxplots from hugging teh axis

	# rotate the xaxis labels
	pyplot.xticks(dates, [str(date.date()) for date in dates], rotation=45)

	# Shink current axis by width% to fit the legend
	box = ax1.get_position()
	width = 0.8
	ax1.set_position([box.x0, box.y0, box.width * width, box.height])

	# Put a legend to the right of the current axis
	ax1.legend(lines, line_labels, loc='center left', bbox_to_anchor=(1, 0.5))

	return fig, 'NO MAP'



# Dictionary of ethanol monkey plots VIPs can customize
MONKEY_ETOH_TOOLS_PLOTS = { 'monkey_bouts_vol': 			(monkey_bouts_vol, 'Detailed Ethanol Intake Pattern'),
							}
# Dictionary of protein monkey plots VIPs can customize
MONKEY_PROTEIN_TOOLS_PLOTS = {'monkey_protein_stdev': 			(monkey_protein_stdev, "Protein Value (standard deviation)"),
							  'monkey_protein_pctdev': 			(monkey_protein_pctdev, "Protein Value (percent deviation)"),
							  'monkey_protein_value': 			(monkey_protein_value, "Protein Value (raw value)"),
}

# Dictionary of all cohort plots
MONKEY_PLOTS = {}
MONKEY_PLOTS.update(MONKEY_ETOH_TOOLS_PLOTS)
MONKEY_PLOTS.update(MONKEY_PROTEIN_TOOLS_PLOTS)
MONKEY_PLOTS.update({
				"monkey_necropsy_avg_22hr_g_per_kg": (monkey_necropsy_avg_22hr_g_per_kg,	"Average Monkey Ethanol Intake, 22hr"),
				"monkey_necropsy_etoh_4pct": (monkey_necropsy_etoh_4pct, 				 	"Total Monkey Ethanol Intake, ml"),
				"monkey_necropsy_sum_g_per_kg": (monkey_necropsy_sum_g_per_kg, 			 	"Total Monkey Ethanol Intake, g per kg"),
				'monkey_errorbox_veh': (monkey_errorbox_veh, 								'Monkey Water Intake'),
				'monkey_errorbox_pellets': (monkey_errorbox_pellets, 						'Monkey Pellets'),
				'monkey_errorbox_weight': (monkey_errorbox_weight, 							'Monkey Weight'),
				'monkey_bouts_drinks_intraday': (monkey_bouts_drinks_intraday, 				"Intra-day Ethanol Intake"),
				'monkey_errorbox_etoh': (monkey_errorbox_etoh, 								'Monkey Ethanol Intake'),
				'monkey_bouts_drinks': (monkey_bouts_drinks, 								'(Deprecated) Detailed Ethanol Intake Pattern'),
})

def create_plots(cohorts=True, monkeys=True, delete=False):
	if monkeys:
		monkey_plots = ['monkey_errorbox_veh',
						'monkey_errorbox_pellets',
						'monkey_errorbox_etoh',
						'monkey_errorbox_weight',
						'monkey_necropsy_etoh_4pct',
						'monkey_necropsy_sum_g_per_kg',
						'monkey_necropsy_avg_22hr_g_per_kg']

		from matrr.models import MonkeyImage, Monkey
		if delete:
			MonkeyImage.objects.all().delete()
		for monkey in Monkey.objects.all():
			for graph in monkey_plots:
				gc.collect()
				monkeyimage, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=graph, title=MONKEY_PLOTS[graph][1])

	if cohorts:
		cohort_plots = ['cohort_bihourly_etoh_treemap',
						'cohort_boxplot_m2de_month_veh_intake',
						'cohort_boxplot_m2de_month_total_pellets',
						'cohort_boxplot_m2de_month_mtd_weight',
						'cohort_boxplot_m2de_month_etoh_intake',
						'cohort_necropsy_etoh_4pct',
						'cohort_necropsy_sum_g_per_kg',
						'cohort_necropsy_avg_22hr_g_per_kg',
						]

		from matrr.models import CohortImage, Cohort
		if delete:
			CohortImage.objects.all().delete()
		for cohort in Cohort.objects.all():
			print cohort
			for graph in cohort_plots:
				gc.collect()
				cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=COHORT_PLOTS[graph][1])
				if graph == 'cohort_bihourly_etoh_treemap':
					_para = parameters=str({'dex_type': 'Open Access'})
					cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=COHORT_PLOTS[graph][1], parameters=_para)
