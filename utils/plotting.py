import os
from matrr.models import *
import matplotlib as mpl
from matplotlib import pyplot
import Image

###############  matplotlibrc settings
mpl.rcParams['figure.subplot.left'] 	= 0.1	# the left side of the subplots of the figure
mpl.rcParams['figure.subplot.right'] 	= 0.98	# the right side of the subplots of the figure
mpl.rcParams['figure.subplot.bottom'] 	= 0.12	# the bottom of the subplots of the figure
mpl.rcParams['figure.subplot.top'] 	= 0.96	# the top of the subplots of the figure
mpl.rcParams['figure.subplot.wspace'] 	= 0.05	# the amount of width reserved for blank space between subplots
mpl.rcParams['figure.subplot.hspace'] 	= 0.05	# the amount of height reserved for white space between subplots
############### end


def cohort_boxplot_m2de(cohort, days=10):
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
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


		fig_size = (10,10)
		thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
		for data_type, data in all_data.items():
			dir = 'static/images/' + data_type + "/"
			if not os.path.exists(dir):
				os.makedirs(dir)
			filename = dir + cohort.coh_cohort_name
			print filename

			sorted_keys = [item[0] for item in sorted(data[1].items())]
			sorted_values = [item[1] for item in sorted(data[1].items())]

			fig = pyplot.figure(figsize=fig_size)
			ax1 = fig.add_subplot(111)
			ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
			ax1.set_axisbelow(True)
			ax1.set_title('MATRR Boxplot')
			ax1.set_xlabel("Date of Experiment")
			ax1.set_ylabel(data[0])
			
			bp = pyplot.boxplot(sorted_values)
			pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
			pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
			pyplot.setp(bp['fliers'], color='red', marker='+')
			xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
			pyplot.setp(xtickNames, rotation=45)
			fig.savefig(filename + ".png")

			img = Image.open(filename + ".png")
			img.thumbnail(thumb_size, Image.ANTIALIAS)
			img.save(filename + "-thumb.jpg")
	else:
		print "No drinking experiments for this cohort."


def monkey_boxplot_etoh(monkey):
	fig_size = (10,10)
	thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
	filename = 'static/images/' + 'etoh' + "/" + str(monkey)

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
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, colors['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_etoh_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Ethanol Intake (in ml)')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	## Save image and create thumbnail
	fig.savefig(filename + ".png")
	img = Image.open(filename + ".png")
	img.thumbnail(thumb_size, Image.ANTIALIAS)
	img.save(filename + "-thumb.jpg")


def monkey_boxplot_pellet(monkey):
	fig_size = (10,10)
	thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
	coh_pellet_data = {}
	mky_pellet_data = {}
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
	filename = 'static/images/' + 'pellet' + "/" + str(monkey)

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
	for date in dates[:10]:
		coh_pellet_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')
		mky_pellet_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')

	sorted_keys = [item[0] for item in sorted(coh_pellet_data.items())]
	sorted_values = [item[1][0] for item in sorted(mky_pellet_data.items())]

	pos = range(1,len(sorted_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, colors['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_pellet_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)
	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Total Pellets')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	## Save image and create thumbnail
	fig.savefig(filename + ".png")
	img = Image.open(filename + ".png")
	img.thumbnail(thumb_size, Image.ANTIALIAS)
	img.save(filename + "-thumb.jpg")


def monkey_boxplot_veh(monkey):
	fig_size = (10,10)
	thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
	filename = 'static/images/' + 'veh' + "/" + str(monkey)

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
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, colors['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_veh_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Veh Intake')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	## Save image and create thumbnail
	fig.savefig(filename + ".png")
	img = Image.open(filename + ".png")
	img.thumbnail(thumb_size, Image.ANTIALIAS)
	img.save(filename + "-thumb.jpg")


def monkey_boxplot_weight(monkey):
	fig_size = (10,10)
	thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
	coh_weight_data = {}
	mky_weight_data = {}
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
	filename = 'static/images/' + 'weight' + "/" + str(monkey)

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
	for date in dates[:10]:
		coh_weight_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')
		mky_weight_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')

	sorted_keys = [item[0] for item in sorted(coh_weight_data.items())]
	sorted_values = [item[1][0] for item in sorted(mky_weight_data.items())]

	pos = range(1,len(sorted_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, sorted_values, colors['monkey'], linewidth=5)

	sorted_values = [item[1] for item in sorted(coh_weight_data.items())]
	bp = pyplot.boxplot(sorted_values, positions=pos)
	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Weight (in kg)')
	xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
	pyplot.setp(xtickNames, rotation=45)

	## Save image and create thumbnail
	fig.savefig(filename + ".png")
	img = Image.open(filename + ".png")
	img.thumbnail(thumb_size, Image.ANTIALIAS)
	img.save(filename + "-thumb.jpg")
	
def cohort_boxplot_m2de_month(cohort, from_date=None, to_date=None):
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
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


		fig_size = (10,10)
		thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
		for data_type, data in all_data.iteritems():
			dir = 'static/images/' + data_type + "/"
			if not os.path.exists(dir):
				os.makedirs(dir)
			filename = dir + cohort.coh_cohort_name
			print filename

			sorted_keys = [item[0].strftime("%b %Y") for item in sorted(data[1].items())]
			sorted_values = [item[1] for item in sorted(data[1].items())]

			fig = pyplot.figure(figsize=fig_size)
			ax1 = fig.add_subplot(111)
			ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
			ax1.set_axisbelow(True)
			ax1.set_title('MATRR Boxplot')
			ax1.set_xlabel("Date of Experiment")
			ax1.set_ylabel(data[0])
			
			bp = pyplot.boxplot(sorted_values)
			pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
			pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
			pyplot.setp(bp['fliers'], color='red', marker='+')
			xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
			pyplot.setp(xtickNames, rotation=45)
			fig.savefig(filename + ".png")

			img = Image.open(filename + ".png")
			img.thumbnail(thumb_size, Image.ANTIALIAS)
			img.save(filename + "-thumb.jpg")
	else:
		print "No drinking experiments for this cohort."
