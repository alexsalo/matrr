from matrr.models import *
from matplotlib import pyplot
import Image

def cohort_boxplot_m2de(cohort):
	# Gather drinking monkeys from the cohort
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return

	cohort_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)
	if cohort_drinking_experiments.count() > 0:
		dates = cohort_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

		# For each experiment date, gather the drinking data
		etoh_data = {}
		pellet_data = {}
		veh_data = {}
		weight_data = {}
		for date in dates:
			etoh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')
			pellet_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')
			veh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')
			weight_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')
		all_data = {"etoh" : ("Ethanol Intake (in ml)", etoh_data), "pellet" : ("Total Pellets", pellet_data), "veh" : ("Veh Intake", veh_data), "weight" : ("Weight (in kg)", weight_data)}


		fig_size = (10,10)
		thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
		for data_type, data in all_data.items():
			filename = 'static/images/' + data_type + "/" + cohort.coh_cohort_name
			print filename

			# *_data.values()/keys() is sorted ascending by date (oldest last) (as much as a dictionary can be at least)
			# this reverses the lists, which will display the oldest dates on the left of the boxplot
			rev_values = data[1].values()
			rev_keys = data[1].keys()
			rev_keys.reverse()
			rev_values.reverse()

			fig = pyplot.figure(figsize=fig_size)
			ax1 = fig.add_subplot(111)
			ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
			ax1.set_axisbelow(True)
			ax1.set_title('MATRR Boxplot')
			ax1.set_xlabel("Date of Experiment")
			ax1.set_ylabel(data[0])
			bp = pyplot.boxplot(rev_values)
			xtickNames = pyplot.setp(ax1, xticklabels=rev_keys)
			pyplot.setp(xtickNames, rotation=45)
			fig.savefig(filename + ".png")

			img = Image.open(filename + ".png")
			img.thumbnail(thumb_size, Image.ANTIALIAS)
			img.save(filename + "-thumb.jpg")


def monkey_boxplot_etoh(monkey):
	fig_size = (10,10)
	thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
	coh_etoh_data = {}
	mky_etoh_data = {}
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
	filename = 'static/images/' + 'etoh' + "/" + str(monkey)

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mki_real_id=monkey)
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
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

	##  For all dates this monkey drank, collect the ethanol data
	for date in dates:
		coh_etoh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')
		mky_etoh_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')

	##  Reverse the order of the dates
	rev_keys = coh_etoh_data.keys()
	rev_keys.reverse()

	##  Plot the monkey drinking line.
	rev_values = []
	for i in mky_etoh_data.values():  # This sillyness turns a list[ of tuples( holding lists[])] into a list[] of daily ethanol intakes, which pyplot.plot() can use
		for j in i:
			rev_values[len(rev_values):] = [j[0]]
	rev_values.reverse() # Reverses the intakes to match the dates.

	pos = range(1,len(rev_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, rev_values, colors['monkey'], linewidth=5)

	rev_values = coh_etoh_data.values() # list[tuple(list[])] doesn't seem to bother the pyplot.boxplot()
	rev_values.reverse() # Important to remember
	bp = pyplot.boxplot(rev_values, positions=pos)


	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Ethanol Intake (in ml)')
	xtickNames = pyplot.setp(ax1, xticklabels=rev_keys)
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
			monkey = Monkey.objects.get(mki_real_id=monkey)
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
	for date in dates:
		coh_pellet_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')
		mky_pellet_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')

	##  Reverse the order of the dates
	rev_keys = coh_pellet_data.keys()
	rev_keys.reverse()

	##  Plot the monkey line.
	rev_values = []
	for i in mky_pellet_data.values():  # This sillyness turns a list[ of tuples( holding lists[])] into a list[] of daily pellet (intakes?), which pyplot.plot() can use
		for j in i:
			rev_values[len(rev_values):] = [j[0]]
	rev_values.reverse() # Reverses to match the dates.

	pos = range(1,len(rev_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, rev_values, colors['monkey'], linewidth=5)

	rev_values = coh_pellet_data.values() # list[tuple(list[])] doesn't seem to bother the pyplot.boxplot()
	rev_values.reverse() # Important to remember
	bp = pyplot.boxplot(rev_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Total Pellets')
	xtickNames = pyplot.setp(ax1, xticklabels=rev_keys)
	pyplot.setp(xtickNames, rotation=45)

	## Save image and create thumbnail
	fig.savefig(filename + ".png")
	img = Image.open(filename + ".png")
	img.thumbnail(thumb_size, Image.ANTIALIAS)
	img.save(filename + "-thumb.jpg")


def monkey_boxplot_veh(monkey):
	fig_size = (10,10)
	thumb_size = (240, 240) # Image.thumbnail() will preserve aspect ratio
	coh_veh_data = {}
	mky_veh_data = {}
	colors = {'monkey' : "#FF6600", 'cohort' : 'black'}
	filename = 'static/images/' + 'veh' + "/" + str(monkey)

	##  Verify argument is actually a monkey
	if not isinstance(monkey, Monkey):
		try:
			monkey = Monkey.objects.get(mki_real_id=monkey)
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
	for date in dates:
		coh_veh_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')
		mky_veh_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')

	##  Reverse the order of the dates
	rev_keys = coh_veh_data.keys()
	rev_keys.reverse()

	##  Plot the monkey line.
	rev_values = []
	for i in mky_veh_data.values():  # This sillyness turns a list[ of tuples( holding lists[])] into a list[] of daily ethanol intakes, which pyplot.plot() can use
		for j in i:
			rev_values[len(rev_values):] = [j[0]]
	rev_values.reverse() # Reverses the intakes to match the dates.

	pos = range(1,len(rev_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, rev_values, colors['monkey'], linewidth=5)

	rev_values = coh_veh_data.values() # list[tuple(list[])] doesn't seem to bother the pyplot.boxplot()
	rev_values.reverse() # Important to remember
	bp = pyplot.boxplot(rev_values, positions=pos)


	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Veh Intake')
	xtickNames = pyplot.setp(ax1, xticklabels=rev_keys)
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
			monkey = Monkey.objects.get(mki_real_id=monkey)
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
	for date in dates:
		coh_weight_data[str(date.date())] = cohort_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')
		mky_weight_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).exclude(mtd_weight=None).values_list('mtd_weight')

	##  Reverse the order of the dates
	rev_keys = coh_weight_data.keys()
	rev_keys.reverse()

	##  Plot the monkey line.
	rev_values = []
	for i in mky_weight_data.values():  # This sillyness turns a list[ of tuples( holding lists[])] into a list[] of daily ethanol intakes, which pyplot.plot() can use
		for j in i:
			rev_values[len(rev_values):] = [j[0]]
	rev_values.reverse() # Reverses the intakes to match the dates.

	pos = range(1,len(rev_values)+1)  # This is what aligns the boxplot and line graphs
	fig = pyplot.figure(figsize=fig_size)
	ax1 = fig.add_subplot(111)
	plt = pyplot.plot(pos, rev_values, colors['monkey'], linewidth=5)

	rev_values = coh_weight_data.values() # list[tuple(list[])] doesn't seem to bother the pyplot.boxplot()
	rev_values.reverse() # Important to remember
	bp = pyplot.boxplot(rev_values, positions=pos)

	## Pretty colors and fancy letters
	pyplot.setp(bp['boxes'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['whiskers'], linewidth=3, color=colors['cohort'])
	pyplot.setp(bp['fliers'], color='red', marker='+')
	ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax1.set_axisbelow(True)
	ax1.set_title('MATRR Boxplot')
	ax1.set_xlabel("Date of Experiment")
	ax1.set_ylabel('Weight (in kg)')
	xtickNames = pyplot.setp(ax1, xticklabels=rev_keys)
	pyplot.setp(xtickNames, rotation=45)

	## Save image and create thumbnail
	fig.savefig(filename + ".png")
	img = Image.open(filename + ".png")
	img.thumbnail(thumb_size, Image.ANTIALIAS)
	img.save(filename + "-thumb.jpg")
