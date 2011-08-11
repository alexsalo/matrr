from matrr.models import *
from matplotlib import pyplot, pylab
from settings import MEDIA_ROOT

def DrinkingCohortBoxplot(cohort):
	# Gather drinking monkeys from the cohort
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(mtd_etoh_intake=None)
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

	# For each experiment date, gather the drinking data
	daily_data = {}
	for date in dates:
		daily_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).values_list('mtd_etoh_intake')

	# daily_data.values()/keys() is sorted ascending by date (oldest last) (as much as a dictionary can be at least)
	# this reverses the lists, which will display the oldest dates on the left of the boxplot
	rev_values = daily_data.values()
	rev_keys = daily_data.keys()
	rev_keys.reverse()
	rev_values.reverse()

	#draw the boxplots
	pyplot.boxplot(rev_values)
	# label X axis ticks by date
	pylab.xticks(range(1, len(rev_keys)+1), rev_keys)
#	pyplot.setp(rev_keys, rotation=45)
	pyplot.xlabel("Date of Experiment")
	pyplot.ylabel("Ethonol Intake (in mL)")
	pyplot.savefig(MEDIA_ROOT + "/%s.png" % cohort)


def graphthis():
	###### works better
	cohort = 2
	monkey_drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort).exclude(mtd_etoh_intake=None)
	dates = monkey_drinking_experiments.dates('drinking_experiment__dex_date', 'day')

	daily_data = {}
	for date in dates:
		daily_data[str(date.date())] = monkey_drinking_experiments.filter(drinking_experiment__dex_date=date).values_list('mtd_etoh_intake')

	rev_values = daily_data.values()
	rev_keys = daily_data.keys()
	rev_keys.reverse()
	rev_values.reverse()

	pyplot.boxplot(rev_values)
	pylab.xticks(range(1, len(rev_keys)+1), rev_keys)

def graphthat():
###########   works
	testcohort = Cohort.objects.get(pk=2)

	monkeys = {}
	drinkingdata = {}	
	monkeyaverage = {}
	monkeydrinking = {}
	sortedmonkeydrinking = {}
	drinkingmonkeys = testcohort.monkey_set.exclude(mky_drinking=False)

	for monkey in drinkingmonkeys:
		mde = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey).exclude(mtd_etoh_intake=None)
		for e in mde:
			try:
				drinkingdata[e.drinking_experiment.dex_date] += e.mtd_etoh_intake
				monkeydrinking[e.drinking_experiment.dex_date] = e.mtd_etoh_intake
				for key in sorted(monkeydrinking.keys()):
					sortedmonkeydrinking[key] = monkeydrinking[key]
				monkeys[monkey.mky_real_id] = sortedmonkeydrinking
			except KeyError:
				drinkingdata[e.drinking_experiment.dex_date] = e.mtd_etoh_intake
		monkeydrinking = {}
		sortedmonkeydrinking = {}

	## sort each date:value for each monkey in monkeys
	sorted_de = {}
	for monkey in monkeys:
		for key in sorted(monkeys[monkey].iterkeys()):
			sorted_de[key] = monkeys[monkey][key]
		monkeys[monkey] = sorted_de

	for key in drinkingdata:
		monkeyaverage[key] = drinkingdata[key]/len(drinkingmonkeys)

	pyplot.plot(monkeyaverage.keys(), monkeyaverage.values())
	pyplot.plot(monkeydrinking.keys(), monkeydrinking.values())
	pyplot.savefig('sweet.png')

