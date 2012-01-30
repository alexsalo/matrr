from matplotlib import pyplot
import numpy
from pylab import *
from matrr.models import *
import dateutil

###############  matplotlibrc settings
mpl.rcParams['figure.subplot.left'] 	= 0.1	# the left side of the subplots of the figure
mpl.rcParams['figure.subplot.right'] 	= 0.98	# the right side of the subplots of the figure
mpl.rcParams['figure.subplot.bottom'] 	= 0.12	# the bottom of the subplots of the figure
mpl.rcParams['figure.subplot.top'] 	= 0.96	# the top of the subplots of the figure
mpl.rcParams['figure.subplot.wspace'] 	= 0.05	# the amount of width reserved for blank space between subplots
mpl.rcParams['figure.subplot.hspace'] 	= 0.05	# the amount of height reserved for white space between subplots
############### end

DEFAULT_CIRCLE_MAX = 280
DEFAULT_CIRCLE_MIN = 20
DEFAULT_FIG_SIZE = (10,10)
DEFAULT_DPI = 80
COLORS = {'monkey' : "#01852F", 'cohort' : 'black'}

##UNFINISHED
def validate_dates(**kwargs):
	from_date = to_date = False
	if kwargs.has_key('from_date'):
		from_date = kwargs['from_date']
	if kwargs.has_key('to_date'):
		to_date = kwargs['to_date']
	if from_date and not isinstance(from_date, datetime):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'
	if from_date and not isinstance(to_date, datetime):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'


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


def cohort_boxplot_m2de_month_etoh_intake(cohort, from_date=None, to_date=None):
	return cohort_boxplot_m2de_month_general(etoh_intake, "Ethanol Intake (in ml)",cohort, from_date, to_date)

def cohort_boxplot_m2de_month_veh_intake(cohort, from_date=None, to_date=None):
	return cohort_boxplot_m2de_month_general(veh_intake , "Veh Intake",cohort, from_date, to_date)
	
def cohort_boxplot_m2de_month_total_pellets(cohort,from_date=None, to_date=None):
	return cohort_boxplot_m2de_month_general(total_pellets,"Total Pellets" ,cohort, from_date, to_date)
	
def cohort_boxplot_m2de_month_mtd_weight(cohort, from_date=None, to_date=None):
	return cohort_boxplot_m2de_month_general(mtd_weight, "Weight (in kg)",cohort, from_date, to_date)

def cohort_boxplot_m2de_month_general(specific_callable, y_label, cohort, from_date=None, to_date=None):
	# Gather drinking monkeys from the cohort
	from matrr.models import Cohort, MonkeyToDrinkingExperiment
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, 'NO MAP'

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)

	if from_date and not isinstance(from_date, datetime):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'
	if to_date and not isinstance(to_date, datetime):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'

	if from_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)

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
	from datetime import date

	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return
	if not isinstance(from_date, date):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print("Invalid paremeter, from_date")
			return
	if not isinstance(to_date, date):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print("Invalid paremeter, from_date")
			return
	mtds = MonkeyToDrinkingExperiment.objects.all()
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


COHORT_PLOTS = {
				"cohort_boxplot_m2de_month_etoh_intake": (cohort_boxplot_m2de_month_etoh_intake, 'Cohort Ethanol Intake, by month'),
				"cohort_boxplot_m2de_month_veh_intake": (cohort_boxplot_m2de_month_veh_intake, 'Cohort Water Intake, by month'),
				"cohort_boxplot_m2de_month_total_pellets": (cohort_boxplot_m2de_month_total_pellets, 'Cohort Pellets, by month'),
				"cohort_boxplot_m2de_month_mtd_weight": (cohort_boxplot_m2de_month_mtd_weight, 'Cohort Weight, by month'),
				"cohort_necropsy_avg_22hr_g_per_kg": (cohort_necropsy_avg_22hr_g_per_kg, 'Average Ethanol Intake in grams per kilogram'),
				"cohort_necropsy_etoh_4pct": (cohort_necropsy_etoh_4pct, "Total Ethanol Intake in ml"),
				"cohort_necropsy_sum_g_per_kg": (cohort_necropsy_sum_g_per_kg, "Total Ethanol Intake in grams per kilogram"),
#				 "cohort_boxplot_m2de_etoh_intake": cohort_boxplot_m2de_etoh_intake,
#				 "cohort_boxplot_m2de_veh_intake": cohort_boxplot_m2de_veh_intake,
#				 "cohort_boxplot_m2de_total_pellets":cohort_boxplot_m2de_total_pellets,
#				 "cohort_boxplot_m2de_mtd_weight":cohort_boxplot_m2de_mtd_weight,
}


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


def monkey_bouts_drinks(monkey=None, from_date=None, to_date=None, circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
			x axis - dates of monkey experiments in range [from_date, to_date] or all possible
			y axis - total number of drinks (bouts * drinks per bout)
			color - number of bouts
			size - drinks per bout
		Circle sizes scaled to range [cirle_min, circle_max]
		Plot saved to filename or to static/images/monkeys-bouts-drinks as mky_[real_id].png and mky_[real_id]-thumb.png
	"""
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	mpl.rcParams['figure.subplot.top'] 	= 0.92
	mpl.rcParams['figure.subplot.bottom'] 	= 0.08

	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, 'NO MAP'

	if from_date and not isinstance(from_date, datetime):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'
	if from_date and not isinstance(to_date, datetime):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
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
	if from_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)

	drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

	if drinking_experiments.count() > 0:
		dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
	else:
		return None, 'NO MAP'
	dr_per_bout =list()
	bouts = list()

	for date in dates:
		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		bouts.append(de.mtd_etoh_bout)
		dr_per_bout.append(de.mtd_etoh_drink_bout)

	xaxis = np.array(range(1,len(dr_per_bout)+1))
	dr_per_bout       = np.array(dr_per_bout)
	bouts   = np.array(bouts)

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
	pyplot.ylim(0,y_max + y_max*0.25) # + % to show circles under the size legend instead of behind it
	pyplot.xlim(0,len(xaxis) + 1)

	cb = pyplot.colorbar(s)

	cb.set_label("Number of bouts")

#    size legend
	x =np.array(range(1,6))
	y =np.array([1,1,1,1,1])

	size_m = size_scale/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = np.array(size)

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

	zipped = np.vstack(zip(xaxis, total_drinks))
	coordinates = ax1.transData.transform(zipped)
	ids = [de.pk for de in drinking_experiments]
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(ids, xcoords, ycoords)

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

	from_date = to_date = False
	if kwargs.has_key('from_date'):
		from_date = kwargs['from_date']
	if kwargs.has_key('to_date'):
		to_date = kwargs['to_date']
	if from_date and not isinstance(from_date, datetime):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'
	if from_date and not isinstance(to_date, datetime):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print("Invalid parameter, from_date")
			return False, 'NO MAP'
		
	monkey_alpha = .7
	cohort = monkey.cohort

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(monkey=monkey)
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)

	if from_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
		monkey_drinking_experiments = monkey_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
		monkey_drinking_experiments = monkey_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)

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
		errorbar[2][0].set_color(eb20_colors)

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


MONKEY_PLOTS = {
#				'monkey_boxplot_etoh': monkey_boxplot_etoh,
#				'monkey_boxplot_veh': monkey_boxplot_veh,
#				'monkey_boxplot_pellets': monkey_boxplot_pellets,
#				'monkey_boxplot_weight': monkey_boxplot_weight,

				'monkey_errorbox_etoh': (monkey_errorbox_etoh, 'Monkey Ethanol Intake'),
				'monkey_errorbox_veh': (monkey_errorbox_veh, 'Monkey Water Intake'),
				'monkey_errorbox_pellets': (monkey_errorbox_pellets, 'Monkey Pellets'),
				'monkey_errorbox_weight': (monkey_errorbox_weight, 'Monkey Weight'),

				'monkey_bouts_drinks': (monkey_bouts_drinks, 'Detailed Ethanol Intake Pattern'),
				'monkey_bouts_drinks_intraday': (monkey_bouts_drinks_intraday, "Intra-day Ethanol Intake"),
				"monkey_necropsy_avg_22hr_g_per_kg": (monkey_necropsy_avg_22hr_g_per_kg, "Average Monkey Ethanol Intake, 22hr"),
				"monkey_necropsy_etoh_4pct": (monkey_necropsy_etoh_4pct, "Total Monkey Ethanol Intake, in 4percent ml"),
				"monkey_necropsy_sum_g_per_kg": (monkey_necropsy_sum_g_per_kg, "Total Monkey Ethanol Intake, in g per kg"),
}

def create_plots():
	from matrr.models import MonkeyImage, Monkey
	MonkeyImage.objects.all().delete()
	for monkey in Monkey.objects.all():
		for key in MONKEY_PLOTS:
			if 'intraday' in key:
				continue
			graph = key
			monkeyimage, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=graph, title=MONKEY_PLOTS[key][1])
			monkeyimage.save()

	from matrr.models import CohortImage, Cohort
	CohortImage.objects.all().delete()
	for cohort in Cohort.objects.all():
		for key in COHORT_PLOTS:
			graph = key
			cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=COHORT_PLOTS[key][1])
			cohortimage.save()
