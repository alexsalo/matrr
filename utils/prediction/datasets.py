__author__ = 'developer'
import numpy

class RhesusPCADataset():
	data = numpy.array([])
	target = numpy.array([])

	def __init__(self, MultinomialNB=False, include_hormone=False, include_only_hormone=False, monkey_pk=None):
		from matrr.models import MonkeyToDrinkingExperiment, MonkeyHormone, Avg, StdDev
		from utils import plotting_beta
		data_columns = \
			['induction stage',
			 'mtd_etoh_intake',
			 'mtd_veh_intake',
			 'mtd_total_pellets',
			 'mtd_weight',
			 'mtd_pct_etoh',
			 'mtd_etoh_g_kg',
			 'mtd_etoh_bout',
			 'mtd_etoh_drink_bout',
			 'mtd_etoh_mean_drink_length',
			 'mtd_etoh_median_idi',
			 'mtd_etoh_mean_drink_vol',
			 'mtd_etoh_mean_bout_length',
			 'mtd_etoh_media_ibi',
			 'mtd_etoh_mean_bout_vol',
			 'mtd_etoh_st_1',
			 'mtd_etoh_st_2',
			 'mtd_etoh_st_3',
			 'mtd_veh_st_2',
			 'mtd_veh_st_3',
			 'mtd_pellets_st_1',
			 'mtd_pellets_st_3',
			 'mtd_length_st_1',
			 'mtd_length_st_2',
			 'mtd_length_st_3',
			 'mtd_vol_1st_bout',
			 'mtd_pct_etoh_in_1st_bout',
			 'mtd_drinks_1st_bout',
			 'mtd_mean_drink_vol_1st_bout',
			 'mtd_fi_wo_drinking_st_1',
			 'mtd_pct_fi_with_drinking_st_1',
			 'mtd_latency_1st_drink',
			 'mtd_st_1_ioc_avg',
			 'mtd_max_bout',
			 'mtd_max_bout_start',
			 'mtd_max_bout_end',
			 'mtd_max_bout_length',
			 'mtd_max_bout_vol',
			 'mtd_pct_max_bout_vol_total_etoh',
			 'mtd_seconds_to_stageone',
			 'mtd_mean_seconds_between_meals',
			 'mhm_cort',
			 'mhm_acth',
			 'mhm_t',
			 'mhm_doc',
			 'mhm_ald',
			 'mhm_dheas'
			 ]
		loop_mtd_columns = data_columns[1:41]
		loop_mhm_columns = data_columns[41:]

		monkeys = [monkey_pk,] if monkey_pk else plotting_beta.all_rhesus_drinkers
		mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey__in=monkeys).order_by('monkey', 'mtd_etoh_g_kg')

		outlier_multiple = 5
		exclude_low = dict()
		exclude_high = dict()
		means = dict()
		for col in loop_mtd_columns:
			mean = mtds.aggregate(Avg(col))[col+'__avg']
			stdev = mtds.aggregate(StdDev(col))[col+'__stddev']
			if not mean and not stdev:
				exclude_low[col] = None
				exclude_high[col] = None
				means[col] = None
				continue
			outlier_min = mean - outlier_multiple * stdev
			outlier_max = mean + outlier_multiple * stdev
			exclude_low[col] = outlier_min
			exclude_high[col] = outlier_max
			means[col] = mean

		target = list()
		data = list()
		for mtd in mtds:
			if mtd.mex_excluded:
				continue
			try:
				mhm = MonkeyHormone.objects.filter(monkey=mtd.monkey, mhm_date=mtd.drinking_experiment.dex_date)[0]
			except IndexError as e:
				if include_only_hormone:
					continue
				else:
					mhm = None

			target.append(plotting_beta.rhesus_monkey_category[mtd.monkey.pk])

			row = list()

			if mtd.mtd_etoh_g_kg < .8:
				stage = 1
			elif .8 < mtd.mtd_etoh_g_kg < 1.2:
				stage = 2
			elif mtd.mtd_etoh_g_kg > 1.2:
				stage = 3
			else:
				stage = mtd.mtd_etoh_g_kg
			row.append(stage)

			for col in loop_mtd_columns:
				if MultinomialNB and col == 'mtd_st_1_ioc_avg':
					continue
				value = getattr(mtd, col)
				if value > exclude_high[col] or value < exclude_low[col] or value is None:
					value = means[col]
				row.append(value)

			if include_hormone or include_only_hormone:
				for col in loop_mhm_columns:
					if mhm == None:
						row.append(0)
					else:
						row.append(getattr(mhm, col))
			data.append(row)
		self.target = numpy.array(target)
		self.data = numpy.array(data)

def create_dataset_from_mtds(mtds):
	from matrr.models import MonkeyHormone, Avg
	from utils import plotting_beta
	data_columns = \
		['mtd_etoh_intake',
		 'mtd_veh_intake',
		 'mtd_total_pellets',
		 'mtd_weight',
		 'mtd_pct_etoh',
		 'mtd_etoh_g_kg',
		 'mtd_etoh_bout',
		 'mtd_etoh_drink_bout',
		 'mtd_etoh_mean_drink_length',
		 'mtd_etoh_median_idi',
		 'mtd_etoh_mean_drink_vol',
		 'mtd_etoh_mean_bout_length',
		 'mtd_etoh_media_ibi',
		 'mtd_etoh_mean_bout_vol',
		 'mtd_etoh_st_1',
		 'mtd_etoh_st_2',
		 'mtd_etoh_st_3',
		 'mtd_veh_st_2',
		 'mtd_veh_st_3',
		 'mtd_pellets_st_1',
		 'mtd_pellets_st_3',
		 'mtd_length_st_1',
		 'mtd_length_st_2',
		 'mtd_length_st_3',
		 'mtd_vol_1st_bout',
		 'mtd_pct_etoh_in_1st_bout',
		 'mtd_drinks_1st_bout',
		 'mtd_mean_drink_vol_1st_bout',
		 'mtd_fi_wo_drinking_st_1',
		 'mtd_pct_fi_with_drinking_st_1',
		 'mtd_latency_1st_drink',
		 'mtd_st_1_ioc_avg',
		 'mtd_max_bout',
		 'mtd_max_bout_start',
		 'mtd_max_bout_end',
		 'mtd_max_bout_length',
		 'mtd_max_bout_vol',
		 'mtd_pct_max_bout_vol_total_etoh',
		 'mtd_seconds_to_stageone',
		 'mtd_mean_seconds_between_meals',
		 'mhm_cort',
		 'mhm_acth',
		 'mhm_t',
		 'mhm_doc',
		 'mhm_ald',
		 'mhm_dheas'
		 ]
	loop_mtd_columns = data_columns[:40]
	loop_mhm_columns = data_columns[40:]

	means = dict()
	for col in loop_mtd_columns:
		mean = mtds.aggregate(Avg(col))[col+'__avg']
		if not mean:
			means[col] = mean
		else:
			means[col] = None

	target = list()
	data = list()
	for mtd in mtds:
		if mtd.mex_excluded:
			continue
		try:
			mhm = MonkeyHormone.objects.filter(monkey=mtd.monkey, mhm_date=mtd.drinking_experiment.dex_date)[0]
		except IndexError as e:
			mhm = None

		target.append(plotting_beta.rhesus_monkey_category[mtd.monkey.pk])

		row = list()
		for col in loop_mtd_columns:
			value = getattr(mtd, col)
			if not value:
				value = means[col]
			if value is None:
				value = 0
			row.append(value)

		for col in loop_mhm_columns:
			if mhm == None:
				row.append(0)
			else:
				row.append(getattr(mhm, col))
		data.append(row)
	return data, target


class RhesusMonkeyBeyesDataset():
	monkey_pk = 0
	monkey_mtds = None

	def __init__(self, mtds):
		self.monkey_mtds = mtds
		self.monkey_pk = mtds[0].monkey.pk

	def get_aggregate_dataset(self):
		from matrr.models import MonkeyHormone, Avg
		data_columns = \
			['mtd_etoh_intake',
			 'mtd_veh_intake',
			 'mtd_total_pellets',
			 'mtd_weight',
			 'mtd_pct_etoh',
			 'mtd_etoh_g_kg',
			 'mtd_etoh_bout',
			 'mtd_etoh_drink_bout',
			 'mtd_etoh_mean_drink_length',
			 'mtd_etoh_median_idi',
			 'mtd_etoh_mean_drink_vol',
			 'mtd_etoh_mean_bout_length',
			 'mtd_etoh_media_ibi',
			 'mtd_etoh_mean_bout_vol',
			 'mtd_etoh_st_1',
			 'mtd_etoh_st_2',
			 'mtd_etoh_st_3',
			 'mtd_veh_st_2',
			 'mtd_veh_st_3',
			 'mtd_pellets_st_1',
			 'mtd_pellets_st_3',
			 'mtd_length_st_1',
			 'mtd_length_st_2',
			 'mtd_length_st_3',
			 'mtd_vol_1st_bout',
			 'mtd_pct_etoh_in_1st_bout',
			 'mtd_drinks_1st_bout',
			 'mtd_mean_drink_vol_1st_bout',
			 'mtd_fi_wo_drinking_st_1',
			 'mtd_pct_fi_with_drinking_st_1',
			 'mtd_latency_1st_drink',
			 'mtd_st_1_ioc_avg',
			 'mtd_max_bout',
			 'mtd_max_bout_start',
			 'mtd_max_bout_end',
			 'mtd_max_bout_length',
			 'mtd_max_bout_vol',
			 'mtd_pct_max_bout_vol_total_etoh',
			 'mtd_seconds_to_stageone',
			 'mtd_mean_seconds_between_meals',
			 'mhm_cort',
			 'mhm_acth',
			 'mhm_t',
			 'mhm_doc',
			 'mhm_ald',
			 'mhm_dheas'
			 ]
		loop_mtd_columns = data_columns[:40]
		loop_mhm_columns = data_columns[40:]

		means = list()
		for col in loop_mtd_columns:
			mean = self.monkey_mtds.aggregate(Avg(col))[col+'__avg']
			means.append(mean)

		mtd_dates = self.monkey_mtds.dates('drinking_experiment__dex_date', 'day').distinct()
		mtd_dates = list(mtd_dates)
		mhms = MonkeyHormone.objects.filter(monkey=self.monkey_pk, mhm_date__in=mtd_dates)
		for col in loop_mhm_columns:
			mean = mhms.aggregate(Avg(col))[col+'__avg']
			means.append(mean)
		return means


class RhesusBeyesDataset():
	monkey_ids = None
	monkey_datasets = list()
	training_dataset = None
	training_targetset = None

	def __init__(self, train_split=.8, monkey_ids=None):
		assert 0 < train_split < 1
		self.train_split = .8
		if monkey_ids:
			self.monkey_ids = monkey_ids
		self.create_datasets()

	def create_datasets(self):
		from matrr.models import MonkeyToDrinkingExperiment

		training_dataset = list()
		training_targetset = list()
		for monkey_pk in self.monkey_ids:
			induction_mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=monkey_pk).order_by('?')
			data_divider = int(induction_mtds.count()*self.train_split)
			training_mtds = induction_mtds[:data_divider]
			testing_mtds = induction_mtds[data_divider:]
			self.monkey_datasets.append(RhesusMonkeyBeyesDataset(testing_mtds))
			data, target = create_dataset_from_mtds(training_mtds)
			training_dataset.extend(data)
			training_targetset.extend(target)
		self.training_dataset = numpy.array(training_dataset)
		self.training_targetset = numpy.array(training_targetset)


class RhesusBeyesDataset_Stage3():
	monkey_ids = None
	monkey_datasets = list()
	training_dataset = None
	training_targetset = None

	def __init__(self, monkey_ids=None):
		if monkey_ids:
			self.monkey_ids = monkey_ids
		self.create_datasets()

	def create_datasets(self):
		from matrr.models import MonkeyToDrinkingExperiment

		training_dataset = list()
		training_targetset = list()
		for monkey_pk in self.monkey_ids:
			stage_3_induction_mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=monkey_pk, mtd_etoh_g_kg__gt=1.3)
			self.monkey_datasets.append(RhesusMonkeyBeyesDataset(stage_3_induction_mtds))
			data, target = create_dataset_from_mtds(stage_3_induction_mtds)
			training_dataset.extend(data)
			training_targetset.extend(target)
		self.training_dataset = numpy.array(training_dataset)
		self.training_targetset = numpy.array(training_targetset)


