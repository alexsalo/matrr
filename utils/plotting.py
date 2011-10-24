import os
import matplotlib as mpl
from matplotlib import pyplot
import Image
from matplotlib.patches import Circle
import numpy as np
from pylab import *
from settings import MATRR_STATIC_STRING
from os import path, makedirs
from datetime import datetime
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
COLORS = {'monkey' : "#FF6600", 'cohort' : 'black'}

def cohort_boxplot_m2de(cohort, days=10):
	# Gather drinking monkeys from the cohort
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)
	if cohort_drinking_experiments.count() > 0:
		dates = cohort_drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('-drinking_experiment__dex_date')

		# For each experiment date, gather the drinking data
		etoh_data = {}
		pellet_data = {}
		veh_data = {}
		weight_data = {}
		for date in dates[:days]:
			etoh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')
			pellet_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')
			veh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')
			weight_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')
		all_data = {"etoh" : ("Ethanol Intake (in ml)", etoh_data), "pellet" : ("Total Pellets", pellet_data), "veh" : ("Veh Intake", veh_data), "weight" : ("Weight (in kg)", weight_data)}


		for data_type, data in all_data.items():
			dir = MATRR_STATIC_STRING + '/images/' + data_type + "/"
			if not os.path.exists(dir):
				os.makedirs(dir)
			filename = dir + cohort.coh_cohort_name
			print filename

			sorted_keys = [item[0] for item in sorted(data[1].items())]
			sorted_values = [item[1] for item in sorted(data[1].items())]

			fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
			ax1 = fig.add_subplot(111)
			ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
			ax1.set_axisbelow(True)
			ax1.set_title('MATRR Boxplot')
			ax1.set_xlabel("Date of Experiment")
			ax1.set_ylabel(data[0])

			bp = pyplot.boxplot(sorted_values)
			pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
			pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
			pyplot.setp(bp['fliers'], color='red', marker='+')
			xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
			pyplot.setp(xtickNames, rotation=45)
	else:
		print "No drinking experiments for this cohort."

def cohort_boxplot_m2de_month(cohort, from_date=None, to_date=None):
	# Gather drinking monkeys from the cohort
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)
	if from_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__gte=from_date)
	if to_date:
		cohort_drinking_experiments = cohort_drinking_experiments.filter(drinking_experiment__dex_date__lte=to_date)

	if cohort_drinking_experiments.count() > 0:
		dates = cohort_drinking_experiments.dates('drinking_experiment__dex_date', 'month').order_by('-drinking_experiment__dex_date')

		# For each experiment date, gather the drinking data
		etoh_data = {}
		pellet_data = {}
		veh_data = {}
		weight_data = {}
		for date in dates:
			cde_of_month = cohort_drinking_experiments.filter(drinking_experiment__dex_date__month=date.month, drinking_experiment__dex_date__year=date.year)
			etoh_data[date] = cde_of_month.exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')
			pellet_data[date] = cde_of_month.exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')
			veh_data[date] = cde_of_month.exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')
			weight_data[date] = cde_of_month.exclude(mtd_weight=None).values_list('mtd_weight')
		all_data = {"etoh" : ("Ethanol Intake (in ml)", etoh_data), "pellet" : ("Total Pellets", pellet_data), "veh" : ("Veh Intake", veh_data), "weight" : ("Weight (in kg)", weight_data)}


		DEFAULT_FIG_SIZE = (10,10)
		thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
		for data_type, data in all_data.iteritems():
			dir = MATRR_STATIC_STRING + '/images/' + data_type + "/"
			if not os.path.exists(dir):
				os.makedirs(dir)
			filename = dir + cohort.coh_cohort_name
			print filename

			sorted_keys = [item[0].strftime("%b %Y") for item in sorted(data[1].items())]
			sorted_values = [item[1] for item in sorted(data[1].items())]

			fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
			ax1 = fig.add_subplot(111)
			ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
			ax1.set_axisbelow(True)
			ax1.set_title('MATRR Boxplot')
			ax1.set_xlabel("Date of Experiment")
			ax1.set_ylabel(data[0])

			bp = pyplot.boxplot(sorted_values)
			pyplot.setp(bp['boxes'], linewidth=3, color=COLORS['cohort'])
			pyplot.setp(bp['whiskers'], linewidth=3, color=COLORS['cohort'])
			pyplot.setp(bp['fliers'], color='red', marker='+')
			xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
			pyplot.setp(xtickNames, rotation=45)
			fig.savefig(filename + ".png", dpi=DEFAULT_DPI)

			img = Image.open(filename + ".png")
			img.thumbnail(thumb_size, Image.ANTIALIAS)
			img.save(filename + "-thumb.jpg")
	else:
		print "No drinking experiments for this cohort."

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
				if mtd.monkey.mky_real_id not in monkeys:
					monkeys[mtd.monkey.mky_real_id] = dict()
				monkeys[mtd.monkey.mky_real_id][dex_date] = event.eev_occurred - min_occurred # elapsed time since the beginning of the experiment

	for dex_date in dates:
		for event_dates in monkeys.itervalues():
			if dex_date not in event_dates:
				event_dates[dex_date] = None
	formatted_monkeys = dict()
	for monkey, event_dates in monkeys.iteritems():
		formatted_monkeys[monkey] = [ convert_timedelta(event_dates[key]) for key in sorted(event_dates.keys()) ]	
	return formatted_monkeys

COHORT_PLOTS = ((cohort_boxplot_m2de, "cohort_boxplot_m2de"),
		 (cohort_boxplot_m2de_month, "cohort_boxplot_m2de_month"),
)


def monkey_bouts_drinks(monkey, from_date=None, to_date=None, circle_max=DEFAULT_CIRCLE_MAX, circle_min=DEFAULT_CIRCLE_MIN):
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
			monkey = Monkey.objects.get(mky_real_id=monkey)
		except Monkey.DoesNotExist:
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				print("That's not a valid monkey.")
				return

	if not isinstance(from_date, datetime):
		try:
			#maybe its a str(datetime)
			from_date = dateutil.parser.parse(from_date)
		except:
			#otherwise give up
			print("Invalid paremeter, from_date")
			return
	if not isinstance(to_date, datetime):
		try:
			#maybe its a str(datetime)
			to_date = dateutil.parser.parse(to_date)
		except:
			#otherwise give up
			print("Invalid paremeter, from_date")
			return

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
		return
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

	fig = pyplot.figure(dpi=DEFAULT_DPI)

#    main graph
	ax1 = fig.add_subplot(111)

	s= ax1.scatter(xaxis, total_drinks, c=bouts, s=rescaled_bouts, alpha=0.4)

	ax1.set_ylabel("Total number of drinks =  bouts * drinks per bout")
	ax1.set_xlabel("Days")

	ax1.set_title('Monkey %d: from %s to %s' % (monkey.mky_real_id, (dates[0]).strftime("%d/%m/%y"), (dates[dates.count()-1]).strftime("%d/%m/%y")))
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

def monkey_boxplot_etoh(monkey=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment
	
	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_real_id=monkey)
		except Monkey.DoesNotExist:
			print("That's not a real monkey.")
			return
	##  Because this is ethanol data, only bother with drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return

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

	return fig, 'NO MAP'

def monkey_boxplot_pellet(monkey=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_real_id=monkey)
		except Monkey.DoesNotExist:
			print("That's not a real monkey.")
			return

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return

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

	return fig, 'NO MAP'

def monkey_boxplot_veh(monkey=None, monkey_image=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_real_id=monkey)
		except Monkey.DoesNotExist:
			print("That's not a real monkey.")
			return

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return

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

	return fig, 'NO MAP'

def monkey_boxplot_weight(monkey=None, monkey_image=None):
	from matrr.models import Monkey
	from matrr.models import MonkeyToDrinkingExperiment

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mky_real_id=monkey)
		except Monkey.DoesNotExist:
			print("That's not a real monkey.")
			return

	##  No data for non-drinking monkeys
	if monkey.mky_drinking is False:
		print "This monkey isn't drinking:  " + str(monkey)
		return

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

	return fig, 'NO MAP'

MONKEY_PLOTS = {'monkey_bouts_drinks': monkey_bouts_drinks,
				 'monkey_boxplot_etoh': monkey_boxplot_etoh,
				 'monkey_boxplot_pellet': monkey_boxplot_pellet,
				 'monkey_boxplot_veh': monkey_boxplot_veh,
				 'monkey_boxplot_weight': monkey_boxplot_weight,
}
