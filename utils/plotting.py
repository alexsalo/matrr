from datetime import timedelta, datetime, date, time
from matplotlib import pyplot, cm, gridspec, colors, cm
from django.db.models.aggregates import Sum, Max, Avg
from matplotlib.cm import get_cmap
from matplotlib.patches import Circle, Rectangle
from matplotlib.ticker import NullLocator, FixedLocator, MaxNLocator
import numpy, dateutil, gc, operator, matplotlib
from numpy import polyfit, polyval
from numpy.ma import concatenate
from scipy.linalg import LinAlgError
from scipy.cluster import vq
from scipy.interpolate import spline
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
HISTOGRAM_FIG_SIZE = (15,10)
THIRDS_FIG_SIZE = (20,8)
DEFAULT_DPI = 80
COLORS = {'monkey' : "#01852F", 'cohort' : 'black'}

def validate_dates(from_date=False, to_date=False):
	import traceback
	if from_date and not isinstance(from_date, (datetime, date)):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print "Invalid parameter, from_date"
			print '>>> traceback <<<'
			traceback.print_exc()
			print '>>> end of traceback <<<'
			from_date = None
	if to_date and not isinstance(to_date, (datetime, date)):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print "Invalid parameter, to_date"
			print '>>> traceback <<<'
			traceback.print_exc()
			print '>>> end of traceback <<<'
			to_date = None
	return from_date, to_date

def cmap_discretize(cmap, N):
	"""Return a discrete colormap from the continuous colormap cmap.

		cmap: colormap instance, eg. cm.jet.
		N: number of colors.

	Example
		x = resize(arange(100), (5,100))
		djet = cmap_discretize(cm.jet, 5)
		imshow(x, cmap=djet)
	"""

	if type(cmap) == str:
		name = cmap
		cmap = get_cmap(cmap)
		cmap.name = name
	colors_i = concatenate((numpy.linspace(0, 1., N), (0.,0.,0.,0.)))
	colors_rgba = cmap(colors_i)
	indices = numpy.linspace(0, 1., N+1)
	cdict = {}
	for ki,key in enumerate(('red','green','blue')):
		cdict[key] = [ (indices[i], colors_rgba[i-1,ki], colors_rgba[i,ki]) for i in xrange(N+1) ]
	# Return colormap object.
	return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)

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

def _lifetime_cumsum_etoh(eevs, subplot, color_monkey=True):
	"""

	"""
	colors = ['navy', 'goldenrod']
	volumes = numpy.array(eevs.values_list('eev_etoh_volume', flat=True))
	yaxis = numpy.cumsum(volumes)
	xaxis = numpy.array(eevs.values_list('eev_occurred', flat=True))
	color = colors[1] if color_monkey else colors[0]
	subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=color)
	return subplot

def _days_cumsum_etoh(eevs, subplot):
	"""
	This fn is used by cohort_etoh_induction_cumsum and monky_etoh_induction_cumsum.  It plots the eev cumsum lines on the gives subplot.
	"""
	colors = ['navy', 'goldenrod']
	dates = eevs.dates('eev_occurred', 'day')
	offset = 0
	for index, date in enumerate(dates):
		date_eevs = eevs.filter(eev_occurred__year=date.year, eev_occurred__month=date.month, eev_occurred__day=date.day)
		times = numpy.array(date_eevs.values_list('eev_session_time', flat=True))
		volumes = numpy.array(date_eevs.values_list('eev_etoh_volume', flat=True))
		pace = 0
		x_index = 0
		xaxis = list()
		yaxis = list()
		for t, v in zip(times, volumes):
			if not pace:
				pace = t
				yaxis.append(v)
				xaxis.append(x_index)
				x_index += 1
				continue
			_v = yaxis[len(yaxis)-1]
			if t != pace+1:
				for i in range(t-pace-1):
					yaxis.append(_v)
					xaxis.append(x_index)
					x_index += 1
			yaxis.append(_v+v)
			xaxis.append(x_index)
			x_index += 1
			pace = t

		xaxis = numpy.array(xaxis) + offset
		offset = xaxis.max()
		subplot.plot(xaxis, yaxis, alpha=1, linewidth=0, color=colors[index%2])
		subplot.fill_between(xaxis, 0, yaxis, color=colors[index%2])

	if len(eevs.order_by().values_list('eev_dose', flat=True).distinct()) > 1:
		stage_2_eevs = eevs.filter(eev_dose=1)
		stage_2_xaxis = numpy.array(stage_2_eevs.values_list('eev_occurred', flat=True))
		subplot.axvspan(stage_2_xaxis.min(), stage_2_xaxis.max(), color='black', alpha=.2, zorder=-100)

# histograms
def _general_histogram(monkey, monkey_values, cohort_values, high_values, low_values, label, axis, hide_xticks, show_legend):
	maxes = [monkey_values.max(), cohort_values.max(), high_values.max(), low_values.max()]
	linspace = numpy.linspace(0, max(maxes), 15) # defines number of bins in histogram

	# Monkey histogram spline
	n, bins, patches = axis.hist(monkey_values, bins=linspace, normed=True, alpha=0, color='gold')
	bincenters = 0.5*(bins[1:]+bins[:-1])
	newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
	newy = spline(bincenters, n, newx) # smooth out the y axis
	axis.plot(newx, newy, color='gold', linewidth=5, label="%d" % monkey.pk) # smoothed line

	# Cohort histogram spline
	n, bins, patches = axis.hist(cohort_values, bins=linspace, normed=True, alpha=0, color='purple')
	bincenters = 0.5*(bins[1:]+bins[:-1])
	newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
	newy = spline(bincenters, n, newx) # smooth out the y axis
	axis.plot(newx, newy, color='purple', linewidth=2, label=str(monkey.cohort)) # smoothed line

	# high-drinker histogram spline
	n, bins, patches = axis.hist(high_values, bins=linspace, normed=True, alpha=0, color='purple')
	bincenters = 0.5*(bins[1:]+bins[:-1])
	newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
	newy = spline(bincenters, n, newx) # smooth out the y axis
	axis.plot(newx, newy, color='red', ls='--', linewidth=2, label="HD") # smoothed line

	# low-drinker histogram spline
	n, bins, patches = axis.hist(low_values, bins=linspace, normed=True, alpha=0, color='purple')
	bincenters = 0.5*(bins[1:]+bins[:-1])
	newx = numpy.linspace(min(bincenters), max(bincenters), 100) # smooth out the x axis
	newy = spline(bincenters, n, newx) # smooth out the y axis
	axis.plot(newx, newy, color='blue', ls='--', linewidth=2, label="LD") # smoothed line

	if show_legend:
		axis.legend(loc="upper left", frameon=False)
	axis.set_title(label)
	axis.set_yticks([])
	if hide_xticks:
		axis.set_xticks([])
	else:
		axis.xaxis.set_major_locator(MaxNLocator(4))
	return axis

def _histogram_legend(monkey, axis):
	from matplotlib.lines import Line2D
	lines = list()
	labels = list()
	l = Line2D((0,1),(0,0), color='gold', linewidth=5)
	axis.add_line(l)
	lines.append(l)
	labels.append(monkey)

	l = Line2D((0,1),(0,0), color='purple', linewidth=2)
	axis.add_line(l)
	lines.append(l)
	labels.append(str(monkey.cohort))

	l = Line2D((0,1),(0,0), color='red', linewidth=2, ls='--')
	axis.add_line(l)
	lines.append(l)
	labels.append("High-drinker")

	l = Line2D((0,1),(0,0), color='blue', linewidth=2, ls='--')
	axis.add_line(l)
	lines.append(l)
	labels.append("Low-drinker")

	axis.legend(lines, labels, loc=10, frameon=False, prop={'size':12})
	axis.set_yticks([])
	axis.set_xticks([])

def _bec_histogram(monkey, column_name, axis, from_date=None, to_date=None, sample_before=None, sample_after=None, dex_type='', verbose_name='', hide_xticks=False, show_legend=False):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return
	high_monkey = Monkey.objects.get(mky_high_drinker=True, mky_species=monkey.mky_species)
	low_monkey = Monkey.objects.get(mky_low_drinker=True, mky_species=monkey.mky_species)

	cohort_bec = MonkeyBEC.objects.filter(monkey__cohort=monkey.cohort)
	high_bec = MonkeyBEC.objects.filter(monkey=high_monkey)
	low_bec = MonkeyBEC.objects.filter(monkey=low_monkey)
	from_date, to_date = validate_dates(from_date, to_date)
	q_filter = Q()
	if from_date:
		q_filter = q_filter & Q(mtd__drinking_experiment__dex_date__gte=from_date)
	if to_date:
		q_filter = q_filter & Q(mtd__drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		q_filter = q_filter & Q(mtd__drinking_experiment__dex_type=dex_type)
	if sample_before:
		q_filter = q_filter & Q(bec_sample__lte=sample_before)
	if sample_after:
		q_filter = q_filter & Q(bec_sample__gte=sample_after)

	cohort_bec = cohort_bec.filter(q_filter)
	monkey_bec = cohort_bec.filter(monkey=monkey)
	cohort_bec = cohort_bec.exclude(monkey=monkey)
	high_bec = high_bec.filter(q_filter)
	low_bec = low_bec.filter(q_filter)

	label = verbose_name
	if not label:
		label = monkey_bec[0]._meta.get_field(column_name).verbose_name

	monkey_values = numpy.array(monkey_bec.values_list(column_name, flat=True))
	cohort_values = numpy.array(cohort_bec.values_list(column_name, flat=True))
	high_values = numpy.array(high_bec.values_list(column_name, flat=True))
	low_values = numpy.array(low_bec.values_list(column_name, flat=True))
	return _general_histogram(monkey, monkey_values, cohort_values, high_values, low_values, label, axis, hide_xticks, show_legend)

def _mtd_histogram(monkey, column_name, axis, from_date=None, to_date=None, dex_type='', verbose_name='', hide_xticks=False, show_legend=False):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print "That's not a valid monkey."
				return
	high_monkey = Monkey.objects.get(mky_high_drinker=True)
	low_monkey = Monkey.objects.get(mky_low_drinker=True)

	cohort_dex = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=monkey.cohort)
	high_dex = MonkeyToDrinkingExperiment.objects.filter(monkey=high_monkey)
	low_dex = MonkeyToDrinkingExperiment.objects.filter(monkey=low_monkey)
	from_date, to_date = validate_dates(from_date, to_date)
	q_filter = Q()
	if from_date:
		q_filter = q_filter & Q(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		q_filter = q_filter & Q(drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		q_filter = q_filter & Q(drinking_experiment__dex_type=dex_type)

	cohort_dex = cohort_dex.filter(q_filter)
	monkey_dex = cohort_dex.filter(monkey=monkey)
	cohort_dex = cohort_dex.exclude(monkey=monkey)
	high_dex = high_dex.filter(q_filter)
	low_dex = low_dex.filter(q_filter)

	label = verbose_name
	if not label:
		label = monkey_dex[0]._meta.get_field(column_name).verbose_name

	monkey_values = numpy.array(monkey_dex.values_list(column_name, flat=True))
	cohort_values = numpy.array(cohort_dex.values_list(column_name, flat=True))
	high_values = numpy.array(high_dex.values_list(column_name, flat=True))
	low_values = numpy.array(low_dex.values_list(column_name, flat=True))
	return _general_histogram(monkey, monkey_values, cohort_values, high_values, low_values, label, axis, hide_xticks, show_legend)

def bec_histogram_general(monkey, column_name, dex_type=''):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False

	bec_records = MonkeyBEC.objects.filter(monkey=monkey)
	if dex_type:
		bec_records = bec_records.filter(drinking_experiment__dex_type=dex_type)

	if not bec_records:
		return False, False

	field = bec_records[0]._meta.get_field(column_name)
	if not isinstance(field, (models.FloatField, models.IntegerField, models.BigIntegerField, models.SmallIntegerField, models.PositiveIntegerField, models.PositiveSmallIntegerField)):
		return False, False

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	main_gs = gridspec.GridSpec(1, 1)
	main_gs.update(left=0.05, right=0.95, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot = _bec_histogram(monkey, column_name, main_plot, dex_type=dex_type, show_legend=True)
	return fig, True

def mtd_histogram_general(monkey, column_name, dex_type=''):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False

	mtd_records = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	if dex_type:
		mtd_records = mtd_records.filter(drinking_experiment__dex_type=dex_type)

	if not mtd_records:
		return False, False

	field = mtd_records[0]._meta.get_field(column_name)
	if not isinstance(field, (models.FloatField, models.IntegerField, models.BigIntegerField, models.SmallIntegerField, models.PositiveIntegerField, models.PositiveSmallIntegerField)):
		return False, False

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	main_gs = gridspec.GridSpec(1, 1)
	main_gs.update(left=0.05, right=0.95, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot = _mtd_histogram(monkey, column_name, main_plot, dex_type=dex_type, show_legend=True)
	return fig, True


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
		graph_title = 'Average Daily Ethanol Intake for cohort %s during 22 Hour Free Access Phase' % str(cohort)
		x_label = "Average Daily Ethanol Intake (in g/kg)"
		legend_labels = ('12 Month Average', '6 Month Average')
		return cohort_necropsy_summary_general(necropsy_summary_avg_22hr_g_per_kg, x_label, graph_title, legend_labels, cohort)
	else:
		return False, False

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
		return False, False

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
		return False, False

def cohort_necropsy_summary_general(specific_callable, x_label, graph_title, legend_labels, cohort):
	from matrr.models import Cohort
	##  Verify argument is actually a cohort
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.  Using monkey's cohort")
		return False, False

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
		return False, False

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
			return False, False
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

		bp = ax1.boxplot(sorted_values)
		pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['fliers'], color='red', marker='+')
		xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
		pyplot.setp(xtickNames, rotation=45)
		return fig, False

	else:
		print "No drinking experiments for this cohort."
		return False, False


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
			return False, False

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
		ax1.ylim(ymin=0)

		bp = ax1.boxplot(sorted_values)
		pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['fliers'], color='red', marker='+')
		xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
		pyplot.setp(xtickNames, rotation=45)
		return fig, "cohort map"
	else:
		print "No drinking experiments for this cohort."
		return False, False


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
			return False, False
	if not isinstance(protein, Protein):
		try:
			protein = Protein.objects.get(pk=protein)
		except Protein.DoesNotExist:
			print("That's not a valid protein.")
			return False, False

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

		bp = ax1.boxplot(sorted_values)
		scat = ax1.scatter(scatter_x, scatter_y, marker='+', color='purple', s=80)
		pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
		pyplot.setp(bp['fliers'], color='red', marker='o', markersize=10)
		xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
		pyplot.setp(xtickNames, rotation=45)
		return fig, False

	else:
		print "No MonkeyProteins for this cohort."
		return False, False

def cohort_etoh_bihourly_treemap(cohort, from_date=None, to_date=None, dex_type=''):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False
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
		return False, False
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

	ax = fig.add_axes(ax_dims)
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
	color_ax = fig.add_axes([left_h, bottom, 0.08, height])
	m = numpy.outer(numpy.arange(0,1,0.01),numpy.ones(10))
	color_ax.imshow(m, cmap=cmap, origin="lower")
	color_ax.set_xticks(numpy.arange(0))
	labels = [str(int((max_color*100./4)*i))+'%' for i in range(5)]
	color_ax.set_yticks(numpy.arange(0,101,25), labels)
	color_ax.set_title("Average maximum bout,\nby ethanol intake,\nexpressed as percentage \nof total daily intake\n")

	return fig, 'has_caption'

def cohort_etoh_induction_cumsum(cohort, stage=1):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False
	monkeys = cohort.monkey_set.filter(mky_drinking=True)

	stages = dict()
	stages[0] = Q(eev_dose__lte=1.5)
	stages[1] = Q(eev_dose=.5)
	stages[2] = Q(eev_dose=1)
	stages[3] = Q(eev_dose=1.5)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
	main_gs = gridspec.GridSpec(monkeys.count(), 40)
	main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.01*monkeys.count()) # sharing xaxis

	stage_plot = fig.add_subplot(main_gs[0:1,2:41])
	stage_text = "Stage %d" % stage if stage else "Induction"
	stage_plot.set_title("%s Cumulative Intraday EtOH Intake for %s" % (stage_text, str(cohort)))
	for index, monkey in enumerate(monkeys):
		if index:
			stage_plot = fig.add_subplot(main_gs[index:index+1,2:41], sharex=stage_plot, sharey=stage_plot) # sharing xaxis
		eevs = ExperimentEvent.objects.filter(monkey=monkey, dex_type='Induction').exclude(eev_etoh_volume=None).order_by('eev_occurred')
		stage_x = eevs.filter(stages[stage])
		_days_cumsum_etoh(stage_x, stage_plot)
		stage_plot.get_xaxis().set_visible(False)
		stage_plot.legend((), title=str(monkey), loc=1, frameon=False, prop={'size':12})

#	ylims = stage_plot.get_ylim()
	stage_plot.set_ylim(ymin=0, )#ymax=ylims[1]*1.05)
	stage_plot.yaxis.set_major_locator(MaxNLocator(3, prune='lower'))
	stage_plot.set_xlim(xmin=0)

	# yxes label
	ylabel = fig.add_subplot(main_gs[:,0:2])
	ylabel.set_axis_off()
	ylabel.set_xlim(0, 1)
	ylabel.set_ylim(0, 1)
	ylabel.text(.05, 0.5, "Cumulative EtOH intake, ml", rotation='vertical', horizontalalignment='center', verticalalignment='center')
	return fig, True

def cohort_etoh_gkg_quadbar(cohort):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False
	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	fig.suptitle(str(cohort), size=18)
	main_gs = gridspec.GridSpec(2, 2)
	main_gs.update(left=0.08, right=.98, top=.92, bottom=.06, wspace=.02, hspace=.23)

	cohort_colors =  ['navy', 'slateblue']
	main_plot = None # this is so the first subplot has a sharey.  all subplots after the first will use the previous loop's subplot
	subplots = [(i, j) for i in range(2) for j in range(2)]
	for gkg, _sub in enumerate(subplots, 1):
		main_plot = fig.add_subplot(main_gs[_sub], sharey=main_plot)
		main_plot.set_title("Greater than %d g per kg Etoh" % gkg)

		monkeys = cohort.monkey_set.filter(mky_drinking=True).values_list('pk', flat=True)
		data = list()
		colors = list()
		for i, mky in enumerate(monkeys):
			colors.append(cohort_colors[i%2]) # we don't want the colors sorted.  It breaks if you try anyway.
			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, mtd_etoh_g_kg__gte=gkg).count()
			mtds = mtds if mtds else .001
			data.append((mky, mtds))

		sorted_data = sorted(data, key=lambda t: t[1]) # sort the data by the 2nd tuple value (mtds).  This is important to keep yvalue-monkey matching
		sorted_data = numpy.array(sorted_data)
		yaxis = sorted_data[:,1] # slice off the yaxis values
		bar = main_plot.bar(range(len(monkeys)), yaxis, width=.9, color=colors)

		labels = sorted_data[:,0] # slice off the labels
		x_labels = ["%d" % l for l in labels] # this ensures that the monkey label is "10023" and not "10023.0" -.-
		main_plot.set_xticks(range(len(monkeys))) # this will force a tick for every monkey.  without this, labels become useless
		xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
		pyplot.setp(xtickNames, rotation=45)

		# this hides the yticklabels and ylabel for the right plots
		if gkg % 2:
			main_plot.set_ylabel("Day count")
		else:
			main_plot.get_yaxis().set_visible(False)
	return fig, True

# useless, deprecated
def cohort_bec_bout_general(cohort, x_axis, x_axis_label, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, cluster_count=3):
	"""
		Scatter plot for monkey
			x axis - arguement
			y axis - BEC
			color - Monkey
	"""
	from scipy.cluster import vq
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
	if to_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
	if sample_before:
		bec_records = bec_records.filter(bec_sample__lte=sample_before)
	if sample_after:
		bec_records = bec_records.filter(bec_sample__gte=sample_after)

	if bec_records.count() <= 0:
		return False, False

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)

	mkys = cohort.monkey_set.filter(mky_drinking=True).values_list('pk', flat=True)
	mky_count = float(mkys.count())

	cmap = get_cmap('jet')
	mky_color = dict()
	for idx, key in enumerate(mkys):
		mky_color[key] = cmap(idx / (mky_count-1))

	def create_convex_hull_polygon(cluster):
		from matrr.helper import convex_hull
		from matplotlib.path import Path
		try:
			hull = convex_hull(numpy.array(cluster).transpose())
		except AssertionError: # usually means < 5 datapoints
			return
		path = Path(hull)
		x, y = zip(*path.vertices)
		x = list(x)
		x.append(x[0])
		y = list(y)
		y.append(y[0])
		line = ax1.plot(x, y, 'black')
		return line
	for mky in mkys:
		xy = list()
		becs = bec_records.filter(monkey=mky)
		mtds = MonkeyToDrinkingExperiment.objects.filter(pk__in=becs.values_list('mtd', flat=True))
		gen_x = numpy.array(mtds.values_list(x_axis, flat=True))
		sample = numpy.array(mtds.values_list('bec_record__bec_vol_etoh', flat=True))
		xaxis = numpy.array([n/d if n and d else 0 for n, d in zip(gen_x, sample)]) # will catch division by 0 issues
		yaxis = mtds.values_list('bec_record__bec_mg_pct', flat=True)
		s = ax1.scatter(xaxis, yaxis, c=mky_color[mky], s=100, alpha=1, edgecolor='none', label=`mky`)
		xy.extend(zip(xaxis, yaxis))

		try:
			res, idx = vq.kmeans2(numpy.array(xy), cluster_count)
			ax1.scatter(res[:,0],res[:,1], marker='o', s = 500, linewidths=2, c='none')
			ax1.scatter(res[:,0],res[:,1], marker='x', s = 500, linewidths=2)
			clusters = dict()
			for i in range(cluster_count):
				clusters[i] = list()
			for index, point in zip(idx, xy):
				cluster = clusters[index]
				cluster.append(point)
				clusters[index] = cluster
			for cluster in clusters.values():
				create_convex_hull_polygon(cluster)

		except Exception as e:
			print e

	ax1.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
	ax1.text(0, 82, "80 mg pct")

	title = 'Cohort %s ' % cohort.coh_cohort_name
	if sample_before:
		title += "before %s " % str(sample_before)
	if sample_after:
		title += "after %s " % str(sample_after)

	ax1.set_title(title)
	ax1.set_xlabel(x_axis_label)
	ax1.set_ylabel("Blood Ethanol Concentration, mg %")
	ax1.legend(loc="upper right")
	ax1.set_xlim(xmin=0)
	ax1.set_ylim(ymin=0)
	return fig, True

# useless, deprecated
def cohort_bec_maxbout(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, cluster_count=3):
	return cohort_bec_bout_general(cohort, 'mtd_pct_max_bout_vol_total_etoh', 'Max Bout / Intake at sample', from_date=from_date, to_date=to_date,
								   dex_type=dex_type, sample_before=sample_before, sample_after=sample_after, cluster_count=cluster_count)

# useless, deprecated
def cohort_bec_firstbout(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, cluster_count=3):
	return cohort_bec_bout_general(cohort, 'mtd_pct_etoh_in_1st_bout', 'First Bout / Intake at sample', from_date=from_date, to_date=to_date,
								   dex_type=dex_type, sample_before=sample_before, sample_after=sample_after, cluster_count=cluster_count)

def cohort_bec_firstbout_monkeycluster(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, cluster_count=1):
	"""
		Scatter plot for monkey
			x axis - first bout / total intake
			y axis - BEC
			color - Monkey
	"""
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
	if to_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
	if sample_before:
		bec_records = bec_records.filter(bec_sample__lte=sample_before)
	if sample_after:
		bec_records = bec_records.filter(bec_sample__gte=sample_after)
	bec_records = bec_records.order_by('bec_collect_date')

	if bec_records.count() > 0:
		dates = list(bec_records.dates('bec_collect_date', 'day').order_by('bec_collect_date'))
	else:
		return False, False

	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	ax1 = fig.add_subplot(111)


	mkys = cohort.monkey_set.exclude(mky_drinking=False).values_list('pk', flat=True) # I'd rather have used bec_records to pull the monkey ids, but .distinct() was returning distinct bec records, not distinct monkeys
	mky_count = float(mkys.count())

	cmap = get_cmap('jet')
	mky_color = dict()
	for idx, key in enumerate(mkys):
		mky_color[key] = cmap(idx / (mky_count -1))

	mky_datas = list()
	centeroids = list()
	for mky in mkys:
		mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, drinking_experiment__dex_date__in=dates).exclude(bec_record=None).order_by('drinking_experiment__dex_date')
		xaxis = mtds.values_list('mtd_pct_etoh_in_1st_bout', flat=True)
		yaxis = mtds.values_list('bec_record__bec_mg_pct', flat=True)
		color = mky_color[mky]

		s = ax1.scatter(xaxis, yaxis, c=color, s=40, alpha=.1, edgecolor=color)
		try:
			res, idx = vq.kmeans2(numpy.array(zip(xaxis, yaxis)), cluster_count)
			ax1.scatter(res[:,0],res[:,1], marker='o', s=100, linewidths=3, c=color, edgecolor=color)
			ax1.scatter(res[:,0],res[:,1], marker='x', s=300, linewidths=3, c=color)
			centeroids.append([res[:,0][0], res[:,1][0]])
		except LinAlgError as e: # I'm not sure what about kmeans2() causes this, or how to avoid it
			# todo: logging.error('blah')
			pass

		mky_datas.append((mky, zip(xaxis, yaxis), color))

	def create_convex_hull_polygon(cluster, color, label):
		from matrr.helper import convex_hull
		from matplotlib.path import Path
		try:
			hull = convex_hull(numpy.array(cluster).transpose())
		except AssertionError: # usually means < 5 datapoints
			return
		path = Path(hull)
		x, y = zip(*path.vertices)
		x = list(x)
		x.append(x[0])
		y = list(y)
		y.append(y[0])
		line = ax1.plot(x, y, c=color, linewidth=3, label=label)
		return line

	for mky, data, color in mky_datas:
		create_convex_hull_polygon(data, color, `mky`)

	title = 'Cohort %s ' % cohort.coh_cohort_name
	if sample_before:
		title += "before %s " % str(sample_before)
	if sample_after:
		title += "after %s " % str(sample_after)

	ax1.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
	ax1.text(0, 82, "80 mg pct")
	ax1.set_title(title)
	ax1.set_xlabel("First bout / total intake")
	ax1.set_ylabel("Blood Ethanol Concentration, mg %")
	ax1.legend(loc="upper left")
	ax1.set_xlim(0)
	ax1.set_ylim(0)

	zipped = numpy.vstack(centeroids)
	coordinates = ax1.transData.transform(zipped)
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(mkys, xcoords, ycoords)
	return fig, datapoint_map

def cohort_bec_monthly_centroid_distance_general(cohort, mtd_x_axis, mtd_y_axis, title, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
	"""
	"""
	def add_1_month(date):
		new_month = date.month + 1
		if new_month > 12:
			return datetime(date.year+1, 1, date.day)
		else:
			return datetime(date.year, new_month, date.day)
	def euclid_dist(point_a, point_b):
		import math
		if not any(point_a) or not any(point_b):
			return 0
		return math.hypot(point_b[0]-point_a[0], point_b[1]-point_a[1])

	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
	if to_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
	if sample_before:
		bec_records = bec_records.filter(bec_sample__lte=sample_before)
	if sample_after:
		bec_records = bec_records.filter(bec_sample__gte=sample_after)
	bec_records = bec_records.order_by('bec_collect_date')

	if bec_records.count() > 0:
		dates = sorted(set(bec_records.dates('bec_collect_date', 'month').distinct()))
		bar_x_labels = [date.strftime('%h %Y') for date in dates]
		bar_x = numpy.arange(0, len(dates)-1)
	else:
		return False, False

	monkeys = cohort.monkey_set.exclude(mky_drinking=False)

	cmap = get_cmap('jet')
	month_count = float(len(dates))
	month_color = dict()
	for idx, key in enumerate(dates):
		month_color[key] = cmap(idx / (month_count-1))

	mky_datas = dict()
	for mky in monkeys:
		bar_y = list()
		colors = list()
		for date in dates:
			min_date = date
			max_date = add_1_month(date)
			color = month_color[date]

			cohort_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort,
																	drinking_experiment__dex_date__gte=min_date,
																	drinking_experiment__dex_date__lt=max_date)
			cohort_mtds = cohort_mtds.exclude(bec_record= None).exclude(bec_record__bec_mg_pct = None).exclude(bec_record__bec_mg_pct = 0)
			month_data = list()
			if cohort_mtds.filter(monkey=mky):
				month_data.append(cohort_mtds.filter(monkey=mky))
				month_data.append(cohort_mtds.exclude(monkey=mky))
			if not month_data:
				# still need values stored for this monkey-month if there is no data
				bar_y.append(0)
				colors.append(color)
			else:
				coh_center = (0,0)
				mky_center = (0,0)
				for index, mtd_set in enumerate(month_data): # mtd_set[0] == monkey, mtd_set[1] == cohort
					_xaxis = numpy.array(mtd_set.values_list(mtd_x_axis, flat=True))
					_yaxis = mtd_set.values_list(mtd_y_axis, flat=True)

					try:
						res, idx = vq.kmeans2(numpy.array(zip(_xaxis, _yaxis)), 1)
					except Exception as e:
						# keep default coh/mky center as (0,0)
						if not index: # if it's a monkey center
							colors.append(color) # stash the color for later
					else:
						if index:
							coh_center = [res[:,0][0], res[:,1][0]]
						else:
							mky_center = [res[:,0][0], res[:,1][0]]
							colors.append(color)
				bar_y.append(euclid_dist(mky_center, coh_center))
		mky_datas[mky] = (bar_y, colors)


	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	main_gs = gridspec.GridSpec(monkeys.count(), 40)
	main_gs.update(left=0.03, right=0.98, wspace=0, hspace=.1) # sharing xaxis

	ax_index = 0
	ax = None
	for mky, data in mky_datas.items():
		ax = fig.add_subplot(main_gs[ax_index:ax_index+1, 3:], sharex=ax, sharey=ax)
		if ax_index == 0:
			ax.set_title(title)
		ax.legend((), title=str(mky.pk), loc=1, frameon=False, prop={'size':12})
		ax_index += 1
		bar_y, colors = data
		for _x, _y, _c in zip(bar_x, bar_y, colors):
			# this forloop, while appearing stupid, works out well when there is missing data between monkeys in the cohort.
			ax.bar(_x, _y, color=_c, edgecolor='none')
			ax.get_xaxis().set_visible(False)


	ax.get_xaxis().set_visible(True)
	ax.set_xticks(bar_x)
	ax.set_xticklabels(bar_x_labels, rotation=45)
	ax.yaxis.set_major_locator(MaxNLocator(2, prune='lower'))

	# yxes label
	ylabel = fig.add_subplot(main_gs[:,0:2])
	ylabel.set_axis_off()
	ylabel.set_xlim(0, 1)
	ylabel.set_ylim(0, 1)
	ylabel.text(.05, 0.5, "Euclidean distance between k-means centroids", rotation='vertical', horizontalalignment='center', verticalalignment='center')

	return fig, True

def cohort_bec_mcd_sessionVSbec(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
	title = 'Euclidean monkey-cohort k-means centroids distance, etoh volume vs bec, by month'
	if sample_before:
		title += ", before %s" % str(sample_before)
	if sample_after:
		title += ", after %s" % str(sample_after)

	return cohort_bec_monthly_centroid_distance_general(cohort, 'bec_record__bec_vol_etoh', 'bec_record__bec_mg_pct', title,
														from_date, to_date, dex_type, sample_before, sample_after)

def cohort_bec_mcd_beta(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
	title = 'Euclidean monkey-cohort k-means centroids distance, median ibi vs bec, by month'
	if sample_before:
		title += ", before %s" % str(sample_before)
	if sample_after:
		title += ", after %s" % str(sample_after)
	return cohort_bec_monthly_centroid_distance_general(cohort, 'mtd_etoh_media_ibi', 'bec_record__bec_mg_pct', title,
														from_date, to_date, dex_type, sample_before, sample_after)


# Dictionary of ethanol cohort plots VIPs can customize
COHORT_ETOH_TOOLS_PLOTS = {"cohort_etoh_bihourly_treemap": (cohort_etoh_bihourly_treemap, "Cohort Bihourly Drinking Pattern"),}
# BEC plots
COHORT_BEC_TOOLS_PLOTS = {'cohort_bec_firstbout_monkeycluster': (cohort_bec_firstbout_monkeycluster, 'Monkey BEC vs First Bout'),}
# Dictionary of protein cohort plots VIPs can customize
COHORT_PROTEIN_TOOLS_PLOTS = {"cohort_protein_boxplot": (cohort_protein_boxplot, "Cohort Protein Boxplot")}

# Dictionary of Monkey Tools' plots
COHORT_TOOLS_PLOTS = dict()
COHORT_TOOLS_PLOTS.update(COHORT_ETOH_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_BEC_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_PROTEIN_TOOLS_PLOTS)

# Dictionary of all cohort plots
COHORT_PLOTS = {}
COHORT_PLOTS.update(COHORT_ETOH_TOOLS_PLOTS)
COHORT_PLOTS.update(COHORT_BEC_TOOLS_PLOTS)
COHORT_PLOTS.update(COHORT_PROTEIN_TOOLS_PLOTS)
COHORT_PLOTS.update({"cohort_boxplot_m2de_month_etoh_intake": (cohort_boxplot_m2de_month_etoh_intake,'Monthly Cohort Ethanol Intake boxplot'),
					 "cohort_necropsy_avg_22hr_g_per_kg": (cohort_necropsy_avg_22hr_g_per_kg, 'Average Ethanol Intake, 22hr'),
					 "cohort_necropsy_etoh_4pct": (cohort_necropsy_etoh_4pct, "Total Ethanol Intake, ml"),
					 "cohort_necropsy_sum_g_per_kg": (cohort_necropsy_sum_g_per_kg, "Total Ethanol Intake, g per kg"),
					 "cohort_boxplot_m2de_month_veh_intake": (cohort_boxplot_m2de_month_veh_intake, 'Cohort Water Intake, by month'),
					 "cohort_boxplot_m2de_month_total_pellets": (cohort_boxplot_m2de_month_total_pellets, 'Cohort Pellets, by month'),
					 "cohort_boxplot_m2de_month_mtd_weight": (cohort_boxplot_m2de_month_mtd_weight, 'Cohort Weight, by month'),
#					 'cohort_bec_maxbout': (cohort_bec_maxbout, 'BEC vs Max Bout'),
#					 'cohort_bec_firstbout': (cohort_bec_firstbout, 'BEC vs First Bout'),
					 'cohort_etoh_induction_cumsum': (cohort_etoh_induction_cumsum, 'Cohort Induction Daily Ethanol Intake'),
					 'cohort_etoh_gkg_quadbar': (cohort_etoh_gkg_quadbar, "Cohort Daily Ethanol Intake Counts"),
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
		return False, False

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
		return False, False

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
		return False, False

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
		return False, False

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
				return False, False

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return False, False

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
		return False, False


def monkey_necropsy_avg_22hr_g_per_kg(monkey):
	try:
		nec_sum = monkey.necropsy_summary
		graph_title = 'Average Ethanol Intake for Monkey %s during 22 Hour Free Access Phase' % str(monkey.pk)
		x_label = "Ethanol Intake (in g/kg)"
		legend_labels = ('12 Month Average', '6 Month Average', '%s 12 Month Average' % str(monkey.pk), '%s 6 Month Average' % str(monkey.pk))
		return monkey_necropsy_summary_general(necropsy_summary_avg_22hr_g_per_kg, x_label, graph_title, legend_labels, monkey)
	except NecropsySummary.DoesNotExist:
		return False, False

def monkey_necropsy_etoh_4pct(monkey):
	try:
		nec_sum = monkey.necropsy_summary
		graph_title = 'Total Ethanol Intake for Monkey %s' % str(monkey.pk)
		x_label = "Ethanol Intake (in 4% ml)"
		legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)', '%s Total Intake (Lifetime)' % str(monkey.pk), '%s Total Intake (22hr)' % str(monkey.pk))
		return monkey_necropsy_summary_general(necropsy_summary_etoh_4pct, x_label, graph_title, legend_labels, monkey)
	except NecropsySummary.DoesNotExist:
		return False, False

def monkey_necropsy_sum_g_per_kg(monkey):
	try:
		nec_sum = monkey.necropsy_summary
		graph_title = 'Total Ethanol Intake for Monkey %s' % str(monkey.pk)
		x_label = "Ethanol Intake (in g/kg)"
		legend_labels = ('Total Intake (Lifetime)', 'Total Intake (22hr)', '%s Total Intake (Lifetime)' % str(monkey.pk), '%s Total Intake (22hr)' % str(monkey.pk))
		return monkey_necropsy_summary_general(necropsy_summary_sum_g_per_kg, x_label, graph_title, legend_labels, monkey)
	except NecropsySummary.DoesNotExist:
		return False, False

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
				return False, False
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
		return False, False

	coh_data_1, coh_data_2, cohort_labels = specific_callable(cohort.monkey_set.exclude(pk=monkey.pk))
	mky_data_1, mky_data_2, monkey_label = specific_callable(cohort.monkey_set.filter(pk=monkey.pk))
	if not mky_data_1[0] or not mky_data_2[0]: # don't draw plots for control monkeys
		return False, False

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

		color_map = get_cmap('gist_rainbow')
		color = color_map(1.*index/len(proteins))
		ax1.plot(dates, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=8, markeredgecolor=color, label=str(protein.pro_abbrev))

	oldylims = ax1.get_ylim()
	y_min = min(oldylims[0], -1 * oldylims[1])
	y_max = max(oldylims[1], -1 * oldylims[0])
	ax1.set_ylim(ymin=y_min, ymax=y_max) #  add some spacing, keeps the boxplots from hugging teh axis

	# rotate the xaxis labels
	xticks = [date.date() for date in dates]
	xtick_labels = [str(date.date()) for date in dates]
	ax1.set_xticks(xticks)
	ax1.set_xticklabels(xtick_labels, rotation=45)

	# Shink current axis by 20%
	box = ax1.get_position()
	ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])

	# Put a legend to the right of the current axis
	ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
	return fig, False

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

		color_map = get_cmap('gist_rainbow')
		color = color_map(1.*index/len(proteins))
		ax1.plot(dates, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=8, markeredgecolor=color, label=str(protein.pro_abbrev))

	oldylims = ax1.get_ylim()
	y_min = min(oldylims[0], -1 * oldylims[1])
	y_max = max(oldylims[1], -1 * oldylims[0])
	ax1.set_ylim(ymin=y_min, ymax=y_max) #  add some spacing, keeps the boxplots from hugging teh axis

	# rotate the xaxis labels
	xticks = [date.date() for date in dates]
	xtick_labels = [str(date.date()) for date in dates]
	ax1.set_xticks(xticks)
	ax1.set_xticklabels(xtick_labels, rotation=45)

	# Shink current axis by 20%
	box = ax1.get_position()
	ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])

	# Put a legend to the right of the current axis
	ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
	return fig, False

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
	ax1.plot(dates, y_values, alpha=1, linewidth=4, color=color, marker='o', markersize=10, label=str(protein.pro_abbrev))

	# rotate the xaxis labels
	xticks = [date.date() for date in dates]
	xtick_labels = [str(date.date()) for date in dates]
	ax1.set_xticks(xticks)
	ax1.set_xticklabels(xtick_labels, rotation=45)

	# Shink current axis by width% to fit the legend
	box = ax1.get_position()
	width = 0.8
	ax1.set_position([box.x0, box.y0, box.width * width, box.height])

	# Put a legend to the right of the current axis
	ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
	return fig, False


def monkey_etoh_bouts_drinks(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
				x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
			y axis - total number of drinks (bouts * drinks per bout)
			color - number of bouts
			size - drinks per bout
		Circle sizes scaled to range [cirle_min, circle_max]
	"""
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False
	cbc = monkey.cohort.cbc

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
		return None, False

	scatter_y_label = ''
	scatter_color_label = ''
	scatter_size_label = ''
	induction_days = list()
	scatter_y = list()
	scatter_size = list()
	scatter_color = list()
	for index, date in enumerate(dates, 1):
		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		if de.drinking_experiment.dex_type == 'Induction':
			induction_days.append(index)
		scatter_y.append(de.mtd_etoh_intake)
		scatter_size.append(de.mtd_etoh_bout)
		scatter_color.append(de.mtd_etoh_mean_bout_vol)
		if not scatter_y_label:
			scatter_y_label = de._meta.get_field('mtd_etoh_intake').verbose_name
		if not scatter_color_label:
			scatter_color_label = de._meta.get_field('mtd_etoh_mean_bout_vol').verbose_name
		if not scatter_size_label:
			scatter_size_label = de._meta.get_field('mtd_etoh_bout').verbose_name

	xaxis = numpy.array(range(1,len(scatter_size)+1))
	scatter_y = numpy.array(scatter_y)
	scatter_size = numpy.array(scatter_size)
	scatter_color = numpy.array(scatter_color)
	induction_days = numpy.array(induction_days)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
	etoh_b_d_main_plot = fig.add_subplot(main_gs[:,0:39])

	size_min = circle_min
	size_scale = circle_max - size_min
	size_max = float(cbc.cbc_mtd_etoh_bout_max)
	rescaled_bouts = [ (b/size_max)*size_scale+size_min for b in scatter_size ] # rescaled, so that circles will be in range (size_min, size_scale)

	s = etoh_b_d_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_bouts, alpha=0.4)

	y_max = cbc.cbc_mtd_etoh_intake_max
	graph_y_max = y_max + y_max*0.25
	if len(induction_days) and len(induction_days) != len(xaxis):
		etoh_b_d_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2, edgecolor='black', zorder=-100)

	etoh_b_d_main_plot.set_ylabel(scatter_y_label)
	etoh_b_d_main_plot.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))

	etoh_b_d_main_plot.set_ylim(cbc.cbc_mtd_etoh_intake_max, graph_y_max)
	etoh_b_d_main_plot.set_xlim(0, xaxis.max() + 2)

	max_y_int = int(round(y_max*1.25))
	y_tick_int = int(round(max_y_int/5))
	etoh_b_d_main_plot.set_yticks(range(0, max_y_int, y_tick_int))
	etoh_b_d_main_plot.yaxis.get_label().set_position((0,0.6))

	main_color = fig.add_subplot(main_gs[:,39:])
	cb = fig.colorbar(s, alpha=1, cax=main_color)
	cb.set_label(scatter_color_label)
	cb.set_clim(cbc.cbc_mtd_etoh_mean_bout_vol_min, cbc.cbc_mtd_etoh_mean_bout_vol_max)

#	regression line
	fit = polyfit(xaxis, scatter_y, 3)
	xr=polyval(fit, xaxis)
	etoh_b_d_main_plot.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

#   size legend
	x =numpy.array(range(1,6))
	y =numpy.array([1,1,1,1,1])

	size_m = size_scale/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = numpy.array(size)

	m = size_max/(len(y)-1)
	bout_labels = [ int(round(i*m)) for i in range(1, len(y))] # labels in the range as number of bouts
	bout_labels.insert(0,"1")
	bout_labels.insert(0, "")
	bout_labels.append("")

	etoh_b_d_size_plot = fig.add_subplot(931)
	etoh_b_d_size_plot.set_position((0.05, .89, .3, .07))
	etoh_b_d_size_plot.scatter(x, y, s=size, alpha=0.4)
	etoh_b_d_size_plot.set_xlabel(scatter_size_label)
	etoh_b_d_size_plot.yaxis.set_major_locator(NullLocator())
	pyplot.setp(etoh_b_d_size_plot, xticklabels=bout_labels)

	hist_gs = gridspec.GridSpec(4, 1)
	hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)
	etoh_b_d_hist = fig.add_subplot(hist_gs[0, :])
	etoh_b_d_hist = _histogram_legend(monkey, etoh_b_d_hist)
	etoh_b_d_hist = fig.add_subplot(hist_gs[1, :])
	etoh_b_d_hist = _mtd_histogram(monkey, 'mtd_etoh_intake', etoh_b_d_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	etoh_b_d_hist = fig.add_subplot(hist_gs[2, :])
	etoh_b_d_hist = _mtd_histogram(monkey, 'mtd_etoh_bout', etoh_b_d_hist, from_date=from_date, to_date=to_date, dex_type=dex_type,)
	etoh_b_d_hist = fig.add_subplot(hist_gs[3, :])
	etoh_b_d_hist = _mtd_histogram(monkey, 'mtd_etoh_mean_bout_vol', etoh_b_d_hist, from_date=from_date, to_date=to_date, dex_type=dex_type,)

	zipped = numpy.vstack(zip(xaxis, scatter_y))
	coordinates = etoh_b_d_main_plot.transData.transform(zipped)
	ids = [de.pk for de in drinking_experiments]
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(ids, xcoords, ycoords)
	return fig, datapoint_map

def monkey_etoh_bouts_drinks_intraday(mtd=None):
	if not isinstance(mtd, MonkeyToDrinkingExperiment):
		try:
			mtd = MonkeyToDrinkingExperiment.objects.get(mtd_id=mtd)
		except MonkeyToDrinkingExperiment.DoesNotExist:
			print("That's not a valid MonkeyToDrinkingExperiment.")
			return False, False

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
			ax1.bar(X, Y, width=Xend, color=bout_colors[colorcount%2], alpha=.5, zorder=1)
			for drink in bout.drinks_set.all():
				xaxis = drink.edr_start_time
				yaxis = drink.edr_volume
				ax1.scatter(xaxis, yaxis, c=drink_colors[colorcount%2], s=60, zorder=2)

			colorcount+= 1

		ax1.set_xlim(xmin=0)
		ax1.set_ylim(ymin=0)
		if X+Xend > 60*60:
			ax1.set_xticks(range(0, X+Xend, 60*60))
		else:
			ax1.set_xticks(range(0, 60*60+1, 60*60))
		return fig, "bouts intraday"
	else:
		print("No bouts data available for this monkey drinking experiment.")
		return False, False

def monkey_etoh_bouts_vol(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
			x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
			y axis - g/kg consumed that day
			color - number of bouts
			size - avg volume per bout
		Circle sizes scaled to range [cirle_min, circle_max]
		Plot saved to filename or to static/images/monkeys-bouts-drinks as mky_[real_id].png and mky_[real_id]-thumb.png
	"""
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False
	cbc = monkey.cohort.cbc

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
		return None, False

	scatter_y_label = ''
	scatter_color_label = ''
	scatter_size_label = ''
	induction_days = list()
	scatter_y = list()
	scatter_color = list()
	scatter_size = list()
	for index, date in enumerate(dates, 1):
		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		if de.drinking_experiment.dex_type == 'Induction':
			induction_days.append(index)
		scatter_y.append(de.mtd_etoh_g_kg)
		scatter_color.append(de.mtd_etoh_bout)
		bouts_volume = de.bouts_set.all().aggregate(Avg('ebt_volume'))['ebt_volume__avg']
		scatter_size.append(bouts_volume if bouts_volume else 0)
		if not scatter_y_label:
			scatter_y_label = de._meta.get_field('mtd_etoh_g_kg').verbose_name
		if not scatter_color_label:
			scatter_color_label = de._meta.get_field('mtd_etoh_bout').verbose_name
		if not scatter_size_label:
			scatter_size_label = "Avg bout volume"

	xaxis = numpy.array(range(1,len(scatter_size)+1))
	scatter_size = numpy.array(scatter_size)
	scatter_color   = numpy.array(scatter_color)
	induction_days = numpy.array(induction_days)

	size_min = circle_min
	size_scale = circle_max - size_min
	volume_max = cbc.cbc_ebt_volume_max
	rescaled_volumes = [ (vol/volume_max)*size_scale+size_min for vol in scatter_size ] # rescaled, so that circles will be in range (size_min, size_scale)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
	etoh_bout_vol_main = fig.add_subplot(main_gs[:,0:39])
	s = etoh_bout_vol_main.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)

	etoh_bout_vol_main.set_ylabel("Daily Ethanol Consumption (in g/kg)")
	etoh_bout_vol_main.set_xlabel("Days")
	etoh_bout_vol_main.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))

	y_max = cbc.cbc_mtd_etoh_g_kg_max
	graph_y_max = y_max + y_max*0.25
	pyplot.ylim(0, graph_y_max)
	pyplot.xlim(0,len(xaxis) + 1)
	if len(induction_days) and len(induction_days) != len(xaxis):
		etoh_bout_vol_main.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2, edgecolor='black', zorder=-100)

	etoh_bout_vol_color = fig.add_subplot(main_gs[:,39:])
	cb = fig.colorbar(s, alpha=1, cax=etoh_bout_vol_color)
	cb.set_label(scatter_color_label)
	cb.set_clim(cbc.cbc_mtd_etoh_bout_min, cbc.cbc_mtd_etoh_bout_max)

#    size legend
	x =numpy.array(range(1,6))
	y =numpy.array([1,1,1,1,1])

	size_m = size_scale/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = numpy.array(size)

	m = volume_max/(len(y)-1)
	size_labels = [ int(round(i*m)) for i in range(1, len(y))] # labels in the range as number of bouts
	size_labels.insert(0,"1")
	size_labels.insert(0, "")
	size_labels.append("")

	etoh_bout_vol_size = fig.add_subplot(721)
	etoh_bout_vol_size.scatter(x, y, s=size, alpha=0.4)
	etoh_bout_vol_size.set_xlabel(scatter_size_label)
	etoh_bout_vol_size.yaxis.set_major_locator(NullLocator())
	pyplot.setp(etoh_bout_vol_size, xticklabels=size_labels)

#	regression line
	fit = polyfit(xaxis, scatter_y, 3)
	xr=polyval(fit, xaxis)
	etoh_bout_vol_main.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

	hist_gs = gridspec.GridSpec(4, 1)
	hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)
	etoh_bout_vol_hist = fig.add_subplot(hist_gs[0, :])
	etoh_bout_vol_hist = _histogram_legend(monkey, etoh_bout_vol_hist)
	etoh_bout_vol_hist = fig.add_subplot(hist_gs[1, :])
	etoh_bout_vol_hist = _mtd_histogram(monkey, 'mtd_etoh_g_kg', etoh_bout_vol_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	etoh_bout_vol_hist = fig.add_subplot(hist_gs[2, :])
	etoh_bout_vol_hist = _mtd_histogram(monkey, 'mtd_etoh_bout', etoh_bout_vol_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	etoh_bout_vol_hist = fig.add_subplot(hist_gs[3, :])
	etoh_bout_vol_hist = _mtd_histogram(monkey, 'bouts_set__ebt_volume', etoh_bout_vol_hist, from_date=from_date, to_date=to_date, dex_type=dex_type, verbose_name='Bout Volume')

	zipped = numpy.vstack(zip(xaxis, scatter_y))
	coordinates = etoh_bout_vol_main.transData.transform(zipped)
	ids = [de.pk for de in drinking_experiments]
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(ids, xcoords, ycoords)
	return fig, datapoint_map

def monkey_etoh_first_max_bout(monkey=None, from_date=None, to_date=None, dex_type='', circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
			x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
			y axis - total number of drinks (scatter_size * drinks per bout)
			color - number of scatter_size
			size - drinks per bout
		Circle sizes scaled to range [cirle_min, circle_max]
	"""
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False
	cbc = monkey.cohort.cbc
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
		return None, False

	bar_y_label = ''
	bar_color_label = ''
	scatter_y_label = ''
	scatter_color_label = ''
	scatter_size_label = ''
	xaxis = list()
	induction_days = list()
	scatter_y = list()
	scatter_size = list()
	scatter_color = list()
	bar_yaxis = list()
	bar_color = list()
	for index, date in enumerate(dates, 1):
		xaxis.append(index)
		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		if de.drinking_experiment.dex_type == 'Induction':
			induction_days.append(index)
		scatter_y.append(de.mtd_max_bout_vol)
		scatter_size.append(de.mtd_max_bout_length)
		scatter_color.append(de.mtd_pct_max_bout_vol_total_etoh)
		bar_yaxis.append(de.mtd_vol_1st_bout)
		bar_color.append(de.mtd_pct_etoh_in_1st_bout)
		if not scatter_y_label:
			scatter_y_label = de._meta.get_field('mtd_max_bout_vol').verbose_name
		if not scatter_color_label:
			scatter_color_label = de._meta.get_field('mtd_pct_max_bout_vol_total_etoh').verbose_name
		if not scatter_size_label:
			scatter_size_label = de._meta.get_field("mtd_max_bout_length").verbose_name
		if not bar_y_label:
			bar_y_label = de._meta.get_field('mtd_vol_1st_bout').verbose_name
		if not bar_color_label:
			bar_color_label = de._meta.get_field('mtd_pct_etoh_in_1st_bout').verbose_name

	xaxis = numpy.array(xaxis)
	induction_days = numpy.array(induction_days)
	scatter_y = numpy.array(scatter_y)
	scatter_size = numpy.array(scatter_size)
	scatter_color = numpy.array(scatter_color)

	size_min = circle_min
	size_scale = circle_max - size_min
	max_bout_length_max = cbc.cbc_mtd_max_bout_length_max
	rescaled_bouts = [ (bout/max_bout_length_max)*size_scale+size_min for bout in scatter_size ] # rescaled, so that circles will be in range (size_min, size_scale)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
	etoh_1st_max_main = fig.add_subplot(main_gs[0:2,0:39])
	s = etoh_1st_max_main.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_bouts, alpha=.6)

	y_max = cbc.cbc_mtd_max_bout_vol_max
	graph_y_max = y_max + y_max*0.25
	if len(induction_days) and len(induction_days) != len(xaxis):
		etoh_1st_max_main.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2, edgecolor='black', zorder=-100)

	etoh_1st_max_main.set_ylabel(scatter_y_label)
	etoh_1st_max_main.set_xlabel("Days")

	etoh_1st_max_main.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))

	pyplot.ylim(0, graph_y_max)
	pyplot.xlim(0,len(xaxis) + 2)
	max_y_int = int(round(y_max*1.25))
	y_tick_int = int(round(max_y_int/5))
	etoh_1st_max_main.set_yticks(range(0, max_y_int, y_tick_int))
	etoh_1st_max_main.yaxis.get_label().set_position((0,0.6))

	etoh_1st_max_color = fig.add_subplot(main_gs[0:2,39:])
	cb = fig.colorbar(s, alpha=1, cax=etoh_1st_max_color)
	cb.set_clim(cbc.cbc_mtd_pct_max_bout_vol_total_etoh_min, cbc.cbc_mtd_pct_max_bout_vol_total_etoh_max)
	cb.set_label(scatter_color_label)

	#	Regression line
	fit = polyfit(xaxis, scatter_y ,2)
	xr=polyval(fit, xaxis)
	etoh_1st_max_main.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

#    size legend
	x = numpy.array(range(1,6))
	y = numpy.array([1,1,1,1,1])

	size_m = size_scale/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = numpy.array(size)

	m = max_bout_length_max/(len(y)-1)
	bout_labels = [ int(round(i*m)) for i in range(1, len(y))] # labels in the range as number of scatter_size
	bout_labels.insert(0,"1")
	bout_labels.insert(0, "")
	bout_labels.append("")

	etoh_1st_max_size = fig.add_subplot(931)
	etoh_1st_max_size.set_position((0, .89, .3, .07))
	etoh_1st_max_size.scatter(x, y, s=size, alpha=0.4)
	etoh_1st_max_size.set_xlabel(scatter_size_label)
	etoh_1st_max_size.yaxis.set_major_locator(NullLocator())
	pyplot.setp(etoh_1st_max_size, xticklabels=bout_labels)

#	barplot
	etoh_1st_max_barplot = fig.add_subplot(main_gs[-1:, 0:39])

	etoh_1st_max_barplot.set_xlabel("Days")
	etoh_1st_max_barplot.set_ylabel(bar_y_label)
	etoh_1st_max_barplot.set_autoscalex_on(False)

	# normalize colors to use full range of colormap
	norm = colors.normalize(cbc.cbc_mtd_pct_etoh_in_1st_bout_min, cbc.cbc_mtd_pct_etoh_in_1st_bout_max)

	facecolors = list()
	for bar, x, color_value in zip(bar_yaxis, xaxis, bar_color):
		color = cm.jet(norm(color_value))
		pyplot.bar(x, bar, color=color, edgecolor='none')
		facecolors.append(color)

	etoh_1st_max_barplot.set_xlim(0,len(xaxis) + 2)
	etoh_1st_max_barplot.set_ylim(cbc.cbc_mtd_vol_1st_bout_min, cbc.cbc_mtd_vol_1st_bout_max)

	# create a collection that we will use in colorbox
	col = matplotlib.collections.Collection(facecolors=facecolors, norm = norm, cmap = cm.jet)
	col.set_array(bar_color)

	# colorbor for bar plot
	etoh_1st_max_barcolor = fig.add_subplot(main_gs[-1:,39:])
	cb = fig.colorbar(col, alpha=1, cax=etoh_1st_max_barcolor)
	cb.set_label(bar_color_label)

	hist_gs = gridspec.GridSpec(6, 1)
	hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)
	etoh_1st_max_hist = fig.add_subplot(hist_gs[0, :])
	etoh_1st_max_hist = _histogram_legend(monkey, etoh_1st_max_hist)
	etoh_1st_max_hist = fig.add_subplot(hist_gs[1, :])
	etoh_1st_max_hist = _mtd_histogram(monkey, 'mtd_max_bout_vol', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	etoh_1st_max_hist = fig.add_subplot(hist_gs[2, :])
	etoh_1st_max_hist = _mtd_histogram(monkey, 'mtd_max_bout_length', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type, hide_xticks=True)
	etoh_1st_max_hist = fig.add_subplot(hist_gs[3, :])
	etoh_1st_max_hist = _mtd_histogram(monkey, 'mtd_pct_max_bout_vol_total_etoh', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	etoh_1st_max_hist = fig.add_subplot(hist_gs[4, :])
	etoh_1st_max_hist = _mtd_histogram(monkey, 'mtd_vol_1st_bout', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	etoh_1st_max_hist = fig.add_subplot(hist_gs[5, :])
	etoh_1st_max_hist = _mtd_histogram(monkey, 'mtd_pct_etoh_in_1st_bout', etoh_1st_max_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)

	zipped = numpy.vstack(zip(xaxis, scatter_y))
	coordinates = etoh_1st_max_main.transData.transform(zipped)
	ids = [de.pk for de in drinking_experiments]
	xcoords, inv_ycoords = zip(*coordinates)
	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
	datapoint_map = zip(ids, xcoords, ycoords)
	return fig, datapoint_map

def monkey_etoh_induction_cumsum(monkey):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False

	stages = dict()
	stages[1] = Q(eev_dose=.5)
	stages[2] = Q(eev_dose=1)
	stages[3] = Q(eev_dose=1.5)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)

#   main graph
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.05) # sharing xaxis

	stage_plot = fig.add_subplot(main_gs[0:1,2:39])
	stage_plot.set_title("Induction Cumulative Intraday EtOH Intake for %s" % str(monkey))
	for stage in stages.keys():
		if stage > 1:
			stage_plot = fig.add_subplot(main_gs[stage-1:stage,2:39], sharey=stage_plot, sharex=stage_plot) # sharing xaxis
		eevs = ExperimentEvent.objects.filter(monkey=monkey, dex_type='Induction').exclude(eev_etoh_volume=None).order_by('eev_occurred')
		stage_x = eevs.filter(stages[stage])
		_days_cumsum_etoh(stage_x, stage_plot)
		stage_plot.get_xaxis().set_visible(False)
		stage_plot.legend((), title="Stage %d" % stage, loc=1, frameon=False, prop={'size':12})

#	ylims = stage_plot.get_ylim()
	stage_plot.set_ylim(ymin=0, )#ymax=ylims[1]*1.05)
	stage_plot.yaxis.set_major_locator(MaxNLocator(3))
	stage_plot.set_xlim(xmin=0, )

	# yaxis label
	ylabel = fig.add_subplot(main_gs[:,0:2])
	ylabel.set_axis_off()
	ylabel.set_xlim(0, 1)
	ylabel.set_ylim(0, 1)
	ylabel.text(.05, 0.5, "Cumulative EtOH intake, ml", rotation='vertical', horizontalalignment='center', verticalalignment='center')
	return fig, True

def monkey_etoh_lifetime_cumsum(monkey):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)

#   main graph
	main_gs = gridspec.GridSpec(1, 40)
	main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.05) # sharing xaxis

	lifetime_plot = fig.add_subplot(main_gs[:,1:41])
	lifetime_plot.set_title("Lifetime Cumulative EtOH Intake for %s" % str(monkey))

	for m in monkey.cohort.monkey_set.all():
		color_monkey = m.pk == monkey.pk
		eevs = ExperimentEvent.objects.filter(monkey=m).exclude(eev_etoh_volume=None).order_by('eev_occurred')
		_lifetime_cumsum_etoh(eevs, lifetime_plot, color_monkey=color_monkey)

	lifetime_plot.get_xaxis().set_visible(False)
	return fig, True

def monkey_bec_bubble(monkey=None, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	"""
		Scatter plot for monkey
			x axis - dates of monkey experiments in 1) dex_type, 2)range [from_date, to_date] or 3) all possible, in that priority
			y axis - BEC
			color - intake at time of sample, g/kg
			size - % of daily intake consumed at time of sample
		Circle sizes scaled to range [cirle_min, circle_max]
	"""
	gc.collect()
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False

	if circle_max < circle_min:
		circle_max = DEFAULT_CIRCLE_MAX
		circle_min = DEFAULT_CIRCLE_MIN
	else:
		if circle_max < 10:
			circle_max = DEFAULT_CIRCLE_MAX
		if circle_min < 1:
			circle_min = DEFAULT_CIRCLE_MIN

	cbc = monkey.cohort.cbc
	bec_records = monkey.bec_records.all()
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
	if to_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
	if sample_before:
		bec_records = bec_records.filter(bec_sample__lte=sample_before)
	if sample_after:
		bec_records = bec_records.filter(bec_sample__gte=sample_after)

	if bec_records.count() > 0:
		dates = bec_records.dates('bec_collect_date', 'day').order_by('bec_collect_date')
	else:
		return False, False

	scatter_y_label = ''
	scatter_color_label = ''
	scatter_size_label = ''
	induction_days = list()
	scatter_y = list()
	scatter_size = list()
	scatter_color = list()
	for index, date in enumerate(dates, 1):
		bec_rec = bec_records.get(bec_collect_date=date)
		if bec_rec.mtd.drinking_experiment.dex_type == 'Induction':
			induction_days.append(index)
		scatter_y.append(bec_rec.bec_mg_pct)
		scatter_size.append(bec_rec.bec_pct_intake)
		scatter_color.append(bec_rec.bec_gkg_etoh)
		if not scatter_y_label:
			scatter_y_label = bec_rec._meta.get_field('bec_mg_pct').verbose_name
		if not scatter_size_label:
			scatter_size_label = bec_rec._meta.get_field("bec_pct_intake").verbose_name
		if not scatter_color_label:
			scatter_color_label = bec_rec._meta.get_field('bec_gkg_etoh').verbose_name

	xaxis = numpy.array(range(1,len(scatter_color)+1))
	scatter_color = numpy.array(scatter_color) # color
	scatter_size   = numpy.array(scatter_size) # size
	induction_days = numpy.array(induction_days)

	size_min = circle_min
	size_scale = circle_max - size_min

	max_intake = cbc.cbc_bec_pct_intake_max
	rescaled_volumes = [ (w/max_intake)*size_scale+size_min for w in scatter_size ] # rescaled, so that circles will be in range (size_min, size_scale)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
	bec_bub_main_plot = fig.add_subplot(main_gs[:,0:39])
	s = bec_bub_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)
	bec_bub_main_plot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
	bec_bub_main_plot.text(0, 82, "80 mg pct")

	bec_bub_main_plot.set_ylabel(scatter_y_label)
	bec_bub_main_plot.set_xlabel("Sample Days")
	bec_bub_main_plot.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))

	y_max = cbc.cbc_bec_mg_pct_max
	graph_y_max = y_max + y_max*0.25
	bec_bub_main_plot.set_ylim(0, graph_y_max)
	bec_bub_main_plot.set_xlim(0, len(xaxis) + 1)
	if len(induction_days) and len(induction_days) != len(xaxis):
		bec_bub_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2, edgecolor='black', zorder=-100)

	bec_bub_main_color = fig.add_subplot(main_gs[:,39:])
	cb = fig.colorbar(s, alpha=1, cax=bec_bub_main_color)
	cb.set_label(scatter_color_label)
	cb.set_clim(cbc.cbc_bec_gkg_etoh_min, cbc.cbc_bec_gkg_etoh_max)

#    size legend
	x = numpy.array(range(1,6))
	y = numpy.array([1,1,1,1,1])

	size_m = float(size_scale)/(len(y)-1)
	size = [ int(round(i*size_m))+size_min for i in range(1, len(y))] # rescaled, so that circles will be in range (size_min, size_scale)
	size.insert(0,1+size_min)
	size = numpy.array(size)

	m = max_intake/(len(y)-1)
	size_labels = [ round(i*m, 2) for i in range(1, len(y))] # labels in the range as monkey weights
	size_labels.insert(0,round(cbc.cbc_bec_pct_intake_min, 2))
	size_labels.insert(0, "")
	size_labels.append("")

	bec_bub_size_fig = fig.add_subplot(721)
	bec_bub_size_fig.scatter(x, y, s=size, alpha=0.4)
	bec_bub_size_fig.set_xlabel(scatter_size_label)
	bec_bub_size_fig.yaxis.set_major_locator(NullLocator())
	pyplot.setp(bec_bub_size_fig, xticklabels=size_labels)

	hist_gs = gridspec.GridSpec(4, 1)
	hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)
	bec_bub_hist = fig.add_subplot(hist_gs[0, :])
	bec_bub_hist = _histogram_legend(monkey, bec_bub_hist)
	bec_bub_hist = fig.add_subplot(hist_gs[1, :])
	bec_bub_hist = _bec_histogram(monkey, 'bec_mg_pct', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
	bec_bub_hist = fig.add_subplot(hist_gs[2, :])
	bec_bub_hist = _bec_histogram(monkey, 'bec_pct_intake', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
	bec_bub_hist = fig.add_subplot(hist_gs[3, :])
	bec_bub_hist = _bec_histogram(monkey, 'bec_gkg_etoh', bec_bub_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
	return fig, True

def monkey_bec_consumption(monkey=None, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False

	cbc = monkey.cohort.cbc
	if circle_max < circle_min:
		circle_max = DEFAULT_CIRCLE_MAX
		circle_min = DEFAULT_CIRCLE_MIN
	else:
		if circle_max < 10:
			circle_max = DEFAULT_CIRCLE_MAX
		if circle_min < 1:
			circle_min = DEFAULT_CIRCLE_MIN

	drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
	bec_records = monkey.bec_records.all()
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
		bec_records = bec_records.filter(bec_collect_date__gte=from_date)
	if to_date:
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)
		bec_records = bec_records.filter(bec_collect_date__lte=from_date)
	if sample_before:
		bec_records = bec_records.filter(bec_sample__lte=sample_before)
	if sample_after:
		bec_records = bec_records.filter(bec_sample__gte=sample_after)
	if dex_type:
		from django.db.models import Max, Min
		drinking_experiments = drinking_experiments.filter(drinking_experiment__dex_type=dex_type)
		max_date = drinking_experiments.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
		if max_date:
			bec_records = bec_records.filter(bec_collect_date__lte=max_date)
		min_date = drinking_experiments.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
		if min_date:
			bec_records = bec_records.filter(bec_collect_date__gte=min_date)

	drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

	if drinking_experiments.count() > 0 and bec_records.count() > 0:
		dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
	else:
		return None, False

	bar_y_label = ''
	bar_color_label = ''
	scatter_y_label = ''
	scatter_color_label = ''
	scatter_size_label = ''
	induction_days = list()
	scatter_size = list()
	scatter_y = list() # yaxis
	scatter_color = list()
	bar_xaxis = list()
	bar_yaxis = list()
	bar_color = list()
	for index, date in enumerate(dates, 1):
		bec_rec = bec_records.filter(bec_collect_date=date)
		if bec_rec.count():
			bec_rec = bec_rec[0]
			bar_yaxis.append(bec_rec.bec_mg_pct)
			bar_color.append(bec_rec.bec_pct_intake)
			bar_xaxis.append(index)
			if not bar_color_label:
				bar_color_label = bec_rec._meta.get_field('bec_pct_intake').verbose_name
			if not bar_y_label:
				bar_y_label = bec_rec._meta.get_field('bec_mg_pct').verbose_name

		de = drinking_experiments.get(drinking_experiment__dex_date=date)
		if de.drinking_experiment.dex_type == 'Induction':
			induction_days.append(index)
		scatter_y.append(de.mtd_etoh_g_kg) # y-axis
		scatter_color.append(de.mtd_etoh_bout) # color
		bouts_volume = de.bouts_set.all().aggregate(Avg('ebt_volume'))['ebt_volume__avg']
		scatter_size.append(bouts_volume if bouts_volume else 0) # size
		if not scatter_y_label:
			scatter_y_label = de._meta.get_field('mtd_etoh_g_kg').verbose_name
		if not scatter_color_label:
			scatter_color_label = de._meta.get_field('mtd_etoh_bout').verbose_name
		if not scatter_size_label:
			scatter_size_label = "Avg bout volume"

	xaxis = numpy.array(range(1,len(scatter_size)+1))
	scatter_size = numpy.array(scatter_size)
	scatter_color = numpy.array(scatter_color)
	bar_color = numpy.array(bar_color)
	induction_days = numpy.array(induction_days)

	fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.05, right=0.75, wspace=0, hspace=0)
	bec_con_main_plot = fig.add_subplot(main_gs[0:2,0:39])
	bec_con_main_plot.set_xticks([])

	size_min = circle_min
	size_scale = circle_max - size_min
	volume_max = cbc.cbc_ebt_volume_max
	rescaled_volumes = [ (vol/volume_max)*size_scale+size_min for vol in scatter_size ] # rescaled, so that circles will be in range (size_min, size_scale)

	s = bec_con_main_plot.scatter(xaxis, scatter_y, c=scatter_color, s=rescaled_volumes, alpha=0.4)

	y_max = cbc.cbc_mtd_etoh_g_kg_max
	graph_y_max = y_max + y_max*0.25
	if len(induction_days) and len(induction_days) != len(xaxis):
		bec_con_main_plot.bar(induction_days.min(), graph_y_max, width=induction_days.max(), bottom=0, color='black', alpha=.2, edgecolor='black', zorder=-100)

	bec_con_main_plot.set_ylabel(scatter_y_label)
	bec_con_main_plot.set_title('Monkey %d: from %s to %s' % (monkey.mky_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))

	bec_con_main_plot.set_ylim(0, graph_y_max)
	bec_con_main_plot.set_xlim(0,len(xaxis) + 2)

	max_y_int = int(round(y_max*1.25))
	y_tick_int = max(int(round(max_y_int/5)), 1)
	bec_con_main_plot.set_yticks(range(0, max_y_int, y_tick_int))
	bec_con_main_plot.yaxis.get_label().set_position((0,0.6))

	bec_con_main_color_plot = fig.add_subplot(main_gs[0:2,39:])
	cb = fig.colorbar(s, alpha=1, cax=bec_con_main_color_plot)
	cb.set_clim(cbc.cbc_mtd_etoh_bout_min, cbc.cbc_mtd_etoh_bout_max)
	cb.set_label(scatter_color_label)

#	regression line
	fit = polyfit(xaxis, scatter_y, 3)
	xr=polyval(fit, xaxis)
	bec_con_main_plot.plot(xaxis, xr, '-r', linewidth=3, alpha=.6)

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

	bec_con_size_plot = fig.add_subplot(931)
	bec_con_size_plot.set_position((0.05, .89, .3, .07))
	bec_con_size_plot.scatter(x, y, s=size, alpha=0.4)
	bec_con_size_plot.set_xlabel(scatter_size_label)
	bec_con_size_plot.yaxis.set_major_locator(NullLocator())
	pyplot.setp(bec_con_size_plot, xticklabels=bout_labels)

#	barplot
	bec_con_bar_plot = fig.add_subplot(main_gs[-1:, 0:39])

	bec_con_bar_plot.set_xlabel("Days")
	bec_con_bar_plot.set_ylabel(bar_y_label)
	bec_con_bar_plot.set_autoscalex_on(False)

	# normalize colors to use full range of colormap
	norm = colors.normalize(cbc.cbc_bec_pct_intake_min, cbc.cbc_bec_pct_intake_max)

	facecolors = list()
	for bar, x, color_value in zip(bar_yaxis, bar_xaxis, bar_color):
		color = cm.jet(norm(color_value))
		bec_con_bar_plot.bar(x, bar, width=2, color=color, edgecolor='none')
		facecolors.append(color)
	bec_con_bar_plot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
	bec_con_bar_plot.text(0, 82, "80 mg pct")

	bec_con_bar_plot.set_xlim(0,len(xaxis) + 2)
	if len(induction_days) and len(induction_days) != len(xaxis):
		bec_con_bar_plot.bar(induction_days.min(), bec_con_bar_plot.get_ylim()[1], width=induction_days.max(), bottom=0, color='black', alpha=.2, edgecolor='black', zorder=-100)

	# create a collection that we will use in colorbox
	col = matplotlib.collections.Collection(facecolors=facecolors, norm=norm, cmap=cm.jet)
	col.set_array(bar_color)

	# colorbar for bar plot
	bec_con_bar_color = fig.add_subplot(main_gs[-1:,39:])
	cb = fig.colorbar(col, alpha=1, cax=bec_con_bar_color)
	cb.set_label(bar_color_label)

	hist_gs = gridspec.GridSpec(6, 1)
	hist_gs.update(left=0.8, right=.97, wspace=0, hspace=.5)
	bec_con_hist = fig.add_subplot(hist_gs[0, :])
	bec_con_hist = _histogram_legend(monkey, bec_con_hist)
	bec_con_hist = fig.add_subplot(hist_gs[1, :])
	bec_con_hist = _bec_histogram(monkey, 'bec_mg_pct', bec_con_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
	bec_con_hist = fig.add_subplot(hist_gs[2, :])
	bec_con_hist = _bec_histogram(monkey, 'bec_pct_intake', bec_con_hist, from_date=from_date, to_date=to_date, sample_before=None, sample_after=None, dex_type=dex_type)
	bec_con_hist = fig.add_subplot(hist_gs[3, :])
	bec_con_hist = _mtd_histogram(monkey, 'mtd_etoh_g_kg', bec_con_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	bec_con_hist = fig.add_subplot(hist_gs[4, :])
	bec_con_hist = _mtd_histogram(monkey, 'mtd_etoh_bout', bec_con_hist, from_date=from_date, to_date=to_date, dex_type=dex_type)
	bec_con_hist = fig.add_subplot(hist_gs[5, :])
	bec_con_hist = _mtd_histogram(monkey, 'bouts_set__ebt_volume', bec_con_hist, from_date=from_date, to_date=to_date, dex_type=dex_type, verbose_name='Bout Volume')
	return fig, True

def monkey_bec_monthly_centroids(monkey, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
	"""
	"""
	def add_1_month(date):
		new_month = date.month + 1
		if new_month > 12:
			return datetime(date.year+1, 1, date.day)
		else:
			return datetime(date.year, new_month, date.day)
	def euclid_dist(point_a, point_b):
		import math
		return math.hypot(point_b[0]-point_a[0], point_b[1]-point_a[1])

	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(pk=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return False, False
	cohort = monkey.cohort

	bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
	from_date, to_date = validate_dates(from_date, to_date)
	if from_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
	if to_date:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
	if dex_type:
		bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
	if sample_before:
		bec_records = bec_records.filter(bec_sample__lte=sample_before)
	if sample_after:
		bec_records = bec_records.filter(bec_sample__gte=sample_after)
	bec_records = bec_records.order_by('bec_collect_date')

	if bec_records.count() > 0:
		dates = sorted(set(bec_records.dates('bec_collect_date', 'month').distinct()))
	else:
		return False, False

	cmap = get_cmap('jet')
	month_count = float( max(len(dates), 2)) # prevents zero division in the forloop below
	month_color = dict()
	for idx, key in enumerate(dates):
		month_color[key] = cmap(idx / (month_count-1))

	mky_centroids = list()
	coh_centroids = list()
	colors = list()
	bar_x = list()
	for date in dates:
		min_date = date
		max_date = add_1_month(date)

		mtds = list()
		all_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort, drinking_experiment__dex_date__gte=min_date, drinking_experiment__dex_date__lt=max_date)
		all_mtds = all_mtds.exclude(bec_record=None).exclude(bec_record__bec_mg_pct=None).exclude(bec_record__bec_mg_pct=0)
		if all_mtds.filter(monkey=monkey):
			mtds.append(all_mtds.filter(monkey=monkey))
			mtds.append(all_mtds.exclude(monkey=monkey))
			bar_x.append(date)
		for index, mtd_set in enumerate(mtds):
			xaxis = numpy.array(mtd_set.values_list('bec_record__bec_vol_etoh', flat=True))
			yaxis = mtd_set.values_list('bec_record__bec_mg_pct', flat=True)
			color = month_color[date]

			try:
				res, idx = vq.kmeans2(numpy.array(zip(xaxis, yaxis)), 1)
			except Exception as e:
				print e
				bar_x.remove(date)
			else:
				if index:
					coh_centroids.append([res[:,0][0], res[:,1][0]])
					colors.append(color)
				else:
					mky_centroids.append([res[:,0][0], res[:,1][0]])

	gs = gridspec.GridSpec(30,30)
	fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
	bec_cen_dist_mainplot = fig.add_subplot(gs[0:22,  0:30])

	bar_x_labels = [date.strftime('%h %Y') for date in bar_x]
	bar_x = range(0, len(bar_x))
	bar_y = list()
	for a, b, color in zip(mky_centroids, coh_centroids, colors):
		x = [a[0], b[0]]
		y = [a[1], b[1]]
		bec_cen_dist_mainplot.plot(x, y, c=color, linewidth=3, alpha=.3)
		bar_y.append(euclid_dist(a, b))
	m = numpy.array(mky_centroids)
	c = numpy.array(coh_centroids)
	try:
		bec_cen_dist_mainplot.scatter(m[:,0], m[:,1], marker='o', s=100, linewidths=3, c=colors, edgecolor=colors,  label='Monkey')
		bec_cen_dist_mainplot.scatter(c[:,0], c[:,1], marker='x', s=100, linewidths=3, c=colors, edgecolor=colors,  label='Cohort')
	except IndexError as e: # m and c are empty if all_mtds.count() == 0
		return False, False

	bec_cen_dist_mainplot.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
	bec_cen_dist_mainplot.text(0, 82, "80 mg pct")

	_t = dex_type if dex_type else 'all'
	title = 'Monthly drinking effects for monkey %s, %s data' % (str(monkey.pk), _t)
	if sample_before:
		title += " before %s" % str(sample_before)
	if sample_after:
		title += " after %s" % str(sample_after)

	bec_cen_dist_mainplot.set_title(title)
	bec_cen_dist_mainplot.set_xlabel("Intake at sample")
	bec_cen_dist_mainplot.set_ylabel("Blood Ethanol Concentration, mg %")
	bec_cen_dist_mainplot.legend(loc="lower right", title='Centroids', scatterpoints=1, frameon=False)

#	barplot
	bec_cen_dist_barplot = fig.add_subplot(gs[24:35, 0:30])

	bec_cen_dist_barplot.set_ylabel("Centroid Distance")
	bec_cen_dist_barplot.set_autoscalex_on(False)

	for _x, _y, color in zip(bar_x, bar_y, colors):
		bec_cen_dist_barplot.bar(_x, _y, color=color, edgecolor='none')

	bec_cen_dist_barplot.set_xlim(0, len(bar_x))
	bec_cen_dist_barplot.set_ylim(0, 400)
	bec_cen_dist_barplot.set_xticks(bar_x)
	bec_cen_dist_barplot.set_xticklabels(bar_x_labels, rotation=45)
#	zipped = numpy.vstack(centeroids)
#	coordinates = bec_cen_dist_mainplot.transData.transform(zipped)
#	xcoords, inv_ycoords = zip(*coordinates)
#	ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
#	datapoint_map = zip(range(0,len(xcoords)), xcoords, ycoords)
	return fig, True



# Dictionary of ethanol monkey plots VIPs can customize
MONKEY_ETOH_TOOLS_PLOTS = {'monkey_etoh_bouts_vol': (monkey_etoh_bouts_vol, 'Ethanol Consumption'),
						   'monkey_etoh_first_max_bout': (monkey_etoh_first_max_bout, 'First Bout and Max Bout Details'),
						   'monkey_etoh_bouts_drinks': (monkey_etoh_bouts_drinks, 'Drinking Pattern'),
						   }
# BEC-related plots
MONKEY_BEC_TOOLS_PLOTS = { 'monkey_bec_bubble': (monkey_bec_bubble, 'BEC Plot'),
						   'monkey_bec_consumption': (monkey_bec_consumption, "BEC Consumption "),
						   'monkey_bec_monthly_centroids': (monkey_bec_monthly_centroids, "BEC Monthly Centroid Distance"),
						   }
# Dictionary of protein monkey plots VIPs can customize
MONKEY_PROTEIN_TOOLS_PLOTS = {'monkey_protein_stdev': (monkey_protein_stdev, "Protein Value (standard deviation)"),
							  'monkey_protein_pctdev': (monkey_protein_pctdev, "Protein Value (percent deviation)"),
							  'monkey_protein_value': (monkey_protein_value, "Protein Value (raw value)"),
							  }
# Dictionary of Monkey Tools' plots
MONKEY_TOOLS_PLOTS = dict()
MONKEY_TOOLS_PLOTS.update(MONKEY_ETOH_TOOLS_PLOTS)
MONKEY_TOOLS_PLOTS.update(MONKEY_BEC_TOOLS_PLOTS)
MONKEY_TOOLS_PLOTS.update(MONKEY_PROTEIN_TOOLS_PLOTS)

# Dictionary of all cohort plots
MONKEY_PLOTS = {}
MONKEY_PLOTS.update(MONKEY_ETOH_TOOLS_PLOTS)
MONKEY_PLOTS.update(MONKEY_BEC_TOOLS_PLOTS)
MONKEY_PLOTS.update(MONKEY_PROTEIN_TOOLS_PLOTS)
MONKEY_PLOTS.update({"monkey_necropsy_avg_22hr_g_per_kg": (monkey_necropsy_avg_22hr_g_per_kg, "Average Monkey Ethanol Intake, 22hr"),
					 "monkey_necropsy_etoh_4pct": (monkey_necropsy_etoh_4pct, "Total Monkey Ethanol Intake, ml"),
					 "monkey_necropsy_sum_g_per_kg": (monkey_necropsy_sum_g_per_kg, "Total Monkey Ethanol Intake, g per kg"),
					 'monkey_errorbox_veh': (monkey_errorbox_veh, 'Monkey Water Intake'),
					 'monkey_errorbox_pellets': (monkey_errorbox_pellets, 'Monkey Pellets'),
					 'monkey_errorbox_weight': (monkey_errorbox_weight, 'Monkey Weight'),
					 'monkey_etoh_bouts_drinks_intraday': (monkey_etoh_bouts_drinks_intraday, "Intra-day Ethanol Intake"),
					 'monkey_errorbox_etoh': (monkey_errorbox_etoh, 'Monkey Ethanol Intake'),
					 'mtd_histogram_general': (mtd_histogram_general, 'Monkey Histogram'),
					 'bec_histogram_general': (bec_histogram_general, 'Monkey Histogram'),
					 'monkey_etoh_induction_cumsum': (monkey_etoh_induction_cumsum, 'Monkey Induction Daily Ethanol Intake'),
					 })

def fetch_plot_choices(subject, user, cohort, tool):
	plot_choices = []
	if subject == 'monkey':
		if user.has_perm('matrr.view_etoh_data'):
			if tool == 'etoh' and cohort.monkey_set.exclude(mtd_set=None).count():
				plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in MONKEY_ETOH_TOOLS_PLOTS.items()])
			if tool == 'bec' and cohort.monkey_set.exclude(bec_records=None).count():
				plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in MONKEY_BEC_TOOLS_PLOTS.items()])

	elif subject == 'cohort':
		if user.has_perm('matrr.view_etoh_data'):
			if tool == 'etoh' and cohort.monkey_set.exclude(mtd_set=None).count():
				plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in COHORT_ETOH_TOOLS_PLOTS.items()])
			if tool == 'bec' and cohort.monkey_set.exclude(bec_records=None).count():
				plot_choices.extend([(plot_key, plot_value[1]) for plot_key, plot_value in COHORT_BEC_TOOLS_PLOTS.items()])
	else:
		raise Exception("'subject' parameter must be 'monkey' or 'cohort'")
	return plot_choices

def create_necropsy_plots(cohorts=True, monkeys=True):
	if monkeys:
		monkey_plots = [
						'monkey_necropsy_etoh_4pct',
						'monkey_necropsy_sum_g_per_kg',
						'monkey_necropsy_avg_22hr_g_per_kg']

		from matrr.models import MonkeyImage, Monkey
		for monkey in NecropsySummary.objects.all().values_list('monkey', flat=True).distinct():
			monkey = Monkey.objects.get(pk=monkey)
			for graph in monkey_plots:
				monkeyimage, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=graph, title=MONKEY_PLOTS[graph][1], canonical=True)
				gc.collect()

	if cohorts:
		cohort_plots = [
						'cohort_necropsy_etoh_4pct',
						'cohort_necropsy_sum_g_per_kg',
						'cohort_necropsy_avg_22hr_g_per_kg',
						]

		from matrr.models import CohortImage, Cohort
		for cohort in NecropsySummary.objects.all().values_list('monkey__cohort', flat=True).distinct():
			cohort = Cohort.objects.get(pk=cohort)
			print cohort
			for graph in cohort_plots:
				gc.collect()
				cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=COHORT_PLOTS[graph][1], canonical=True)

def create_mtd_histograms():
	names = [
	 'mtd_etoh_intake',
	 'mtd_pct_etoh',
	 'mtd_etoh_g_kg',
	 'mtd_etoh_bout',
	 'mtd_etoh_mean_drink_vol',
	 'mtd_etoh_mean_bout_vol',
	 'mtd_vol_1st_bout',
	 'mtd_pct_etoh_in_1st_bout',
	 'mtd_latency_1st_drink',
	 'mtd_max_bout_length',
	 'mtd_max_bout_vol',
	 'mtd_pct_max_bout_vol_total_etoh',
	]
	mtd = MonkeyToDrinkingExperiment
	for monkey in mtd.objects.all().values_list('monkey', flat=True).distinct():
		m = Monkey.objects.get(pk=monkey)
		for field in names:
			params = str({'column_name': field })
			title = mtd._meta.get_field(field).verbose_name
			mig, is_new = MonkeyImage.objects.get_or_create(method='mtd_histogram_general', monkey=m, parameters=params, title=title, canonical=True)

def create_bec_histograms():
	names = [
		'bec_mg_pct',
		'bec_pct_intake'
	]

	bec = MonkeyBEC
	for monkey in bec.objects.all().values_list('monkey', flat=True).distinct():
		m = Monkey.objects.get(pk=monkey)
		for field in names:
			params = str({'column_name': field })
			title = bec._meta.get_field(field).verbose_name
			mig, is_new = MonkeyImage.objects.get_or_create(method='bec_histogram_general', monkey=m, parameters=params, title=title, canonical=True)

def create_quadbar_graphs():
	plot_method = 'cohort_etoh_gkg_quadbar'
	for cohort in MonkeyToDrinkingExperiment.objects.all().values_list('monkey__cohort', flat=True).distinct():
		cohort = Cohort.objects.get(pk=cohort)
		print "Creating %s graphs" % str(cohort)
		cohort_image, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=plot_method, title=COHORT_PLOTS[plot_method][1], canonical=True)
		gc.collect()


def create_daily_cumsum_graphs():
	cohorts = ExperimentEvent.objects.all().values_list('monkey__cohort', flat=True).distinct()
	for cohort in cohorts:
		cohort = Cohort.objects.get(pk=cohort)
		print "Creating %s graphs" % str(cohort)
		gc.collect()
		for stage in range(0, 4):
			plot_method = 'cohort_etoh_induction_cumsum'
			params = str({'stage': stage})
			cohort_image, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=plot_method, title=COHORT_PLOTS[plot_method][1], parameters=params, canonical=True)
		for monkey in cohort.monkey_set.filter(mky_drinking=True):
			plot_method = 'monkey_etoh_induction_cumsum'
			monkey_image, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=plot_method, title=MONKEY_PLOTS[plot_method][1], canonical=True)

def create_bec_tools_canonicals(cohort, create_monkey_plots=True):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print "That's not a valid cohort."
			return

	cohort_plots = ['cohort_bec_firstbout_monkeycluster',
					]
	dex_types = ["", "Induction", "Open Access"]

	print "Creating bec cohort plots for %s." % str(cohort)
	for dex_type in dex_types:
		params = str({'dex_type': dex_type})
		for method in cohort_plots:
			cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=method, parameters=params, title=COHORT_PLOTS[method][1], canonical=True)

	if create_monkey_plots:
		monkey_plots = ['monkey_bec_bubble',
						'monkey_bec_consumption',
						'monkey_bec_monthly_centroids',
						]
		dex_types = ["", "Induction", "Open Access"]

		print "Creating bec monkey plots."
		for monkey in cohort.monkey_set.all():
			for dex_type in dex_types:
				params = str({'dex_type': dex_type})
				for method in monkey_plots:
					monkeyimage, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=method, parameters=params, title=MONKEY_PLOTS[method][1], canonical=True)
					gc.collect()

def create_mtd_tools_canonicals(cohort, create_monkey_plots=True):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print "That's not a valid cohort."
			return

	cohort_plots = ['cohort_etoh_bihourly_treemap',
					]
	dex_types = ["", "Induction", "Open Access"]

	print "Creating cohort mtd plots for %s." % str(cohort)
	for dex_type in dex_types:
		params = str({'dex_type': dex_type})
		for method in cohort_plots:
			cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=method, parameters=params, title=COHORT_PLOTS[method][1], canonical=True)

	if create_monkey_plots:
		monkey_plots = ['monkey_etoh_bouts_vol',
						'monkey_etoh_first_max_bout',
						'monkey_etoh_bouts_drinks',
						]
		dex_types = ["", "Induction", "Open Access"]

		print "Creating mtd monkey plots."
		for monkey in cohort.monkey_set.all():
			for dex_type in dex_types:
				params = str({'dex_type': dex_type})
				for method in monkey_plots:
					monkeyimage, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=method, parameters=params, title=MONKEY_PLOTS[method][1], canonical=True)
					gc.collect()




