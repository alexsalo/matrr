from matrr.models import *
from matplotlib import pyplot
import Image

def boxplot_m2de(cohort):
	# Gather drinking monkeys from the cohort
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			return
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(mtd_etoh_intake=None)

	if monkey_drinking_experiments.count() > 0:
		dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

		# For each experiment date, gather the drinking data
		etoh_data = {}
		pellet_data = {}
		veh_data = {}
		weight_data = {}
		for date in dates:
			etoh_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).values_list('mtd_etoh_intake')
			pellet_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).values_list('mtd_total_pellets')
			veh_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).values_list('mtd_veh_intake')
			weight_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).values_list('mtd_weight')
		all_data = {"etoh" : ("Ethanol Intake (in mL)", etoh_data), "pellet" : ("Total Pellets", pellet_data), "veh" : ("Veh Intake", veh_data), "weight" : ("Weight", weight_data)}


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


