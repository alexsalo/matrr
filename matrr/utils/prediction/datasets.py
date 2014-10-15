import numpy

mtd_columns = [
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
    'mhm_record__mhm_cort',
    'mhm_record__mhm_acth',
    'mhm_record__mhm_t',
    'mhm_record__mhm_doc',
    'mhm_record__mhm_ald',
    'mhm_record__mhm_dheas',
]

class RhesusPCADataset():
    data = numpy.array([])
    target = numpy.array([])

    def __init__(self, MultinomialNB=False, include_hormone=False, include_only_hormone=False, monkey_pk=None):
        import django.db.models
        from matrr.models import MonkeyToDrinkingExperiment, MonkeyHormone
        from matrr.utils import plotting_beta
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

        monkeys = [monkey_pk,] if monkey_pk else plotting_beta.ALL_RHESUS_DRINKERS
        mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey__in=monkeys).order_by('monkey', 'mtd_etoh_g_kg')

        outlier_multiple = 5
        exclude_low = dict()
        exclude_high = dict()
        means = dict()
        for col in loop_mtd_columns:
            mean = mtds.aggregate(django.db.models.Avg(col))[col+'__avg']
            stdev = mtds.aggregate(django.db.models.StdDev(col))[col+'__stddev']
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

            target.append(plotting_beta.RHESUS_MONKEY_CATEGORY[mtd.monkey.pk])

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
                    if mhm is None:
                        row.append(0)
                    else:
                        row.append(getattr(mhm, col))
            data.append(row)
        self.target = numpy.array(target)
        self.data = numpy.array(data)

def create_dataset_from_mtds(mtds):
    from django.db import models
    from matrr.models import MonkeyHormone
    from matrr.utils import plotting_beta
    loop_mtd_columns = mtd_columns

    means = dict()
    for col in loop_mtd_columns:
        if col == 'mhm_record':
            continue
        mean = mtds.aggregate(models.Avg(col))[col+'__avg']
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

        target.append(plotting_beta.RHESUS_MONKEY_CATEGORY[mtd.monkey.pk])

        row = list()
        for col in loop_mtd_columns:
            value = getattr(mtd, col)
            if not value:
                value = means[col]
            if value is None:
#				value = 0
                value = .001
            row.append(value)

        data.append(row)
    return data, target

def create_dataset_from_mtd_values(monkey_pk, mtd_values):
    from matrr.utils import plotting_beta
    means = dict()
    for col in mtd_columns:
        _sum = 0
        _count = 0
        for row in mtd_values:
            if row[col]:
                _count += 1
                _sum += row[col]
        _avg = _sum / float(_count) if _count else 0
        means[col] = _avg

    target = list()
    data = list()
    for mtd_row in mtd_values:
        target.append(plotting_beta.RHESUS_MONKEY_CATEGORY[monkey_pk])

        data_row = list()
        for col in mtd_columns:
            value = mtd_row[col]
            if not value and not 'mhm_record' in col:
                value = means[col] # replace empty MTD records with the average, but do NOT replace empty MHM records
            if value is None:
                value = 0
            data_row.append(value)
        data.append(data_row)
    return data, target


class RhesusMonkeyBeyesDataset():
    monkey_pk = 0
    monkey_values = None

    def __init__(self, monkey_pk, mtd_values):
        self.monkey_values = mtd_values
        self.monkey_pk = monkey_pk

    def get_aggregate_dataset(self):
        means = list()
        for col in mtd_columns:
            _sum = 0
            _count = 0
            for row in self.monkey_values:
                if row[col]:
                    _count += 1
                    _sum += row[col]
            _avg = _sum / float(_count) if _count else 0
            means.append(_avg)
        return means


class RhesusBeyesDataset(object):
    __mtds = None
    _monkey_mtd_values= dict()
    monkey_ids = None
    testing_datasets = list()
    training_dataset = None
    training_targetset = None

    def __init__(self, train_split=.8, monkey_ids=None, mtds=None):
        from matrr.models import MonkeyToDrinkingExperiment
        assert 0 < train_split < 1
        self.train_split = .8
        if monkey_ids:
            self.monkey_ids = monkey_ids
        self.__mtds = mtds if mtds else MonkeyToDrinkingExperiment.objects.Ind().filter(monkey__in=self.monkey_ids).order_by('?')
        self.create_datasets()

    def create_datasets(self):
        for monkey_pk in self.monkey_ids:
            self._monkey_mtd_values[monkey_pk] = self.__mtds.values(*mtd_columns)

    def sample_dataset(self):
        import random
        self.testing_datasets = list()
        self.training_dataset = None
        self.training_targetset = None # clear any current datasets
        training_dataset = list()
        training_targetset = list()
        for monkey_pk in self.monkey_ids:
            mky_data = self._monkey_mtd_values[monkey_pk]
            data_length = len(mky_data)
            training_length = int(self.train_split * data_length)

            training_indices = sorted(random.sample(xrange(data_length), training_length)) # get random indices
            testing_indicies = sorted([i for i in xrange(data_length) if i not in training_indices]) # collect the indices that weren't sampled
            training_sample = [ mky_data[i] for i in training_indices] # collect training dataset from the indices
            testing_sample = [mky_data[i] for i in testing_indicies] # collect testing dataset from the indices
            self.testing_datasets.append(RhesusMonkeyBeyesDataset(monkey_pk, testing_sample))
            data, target = create_dataset_from_mtd_values(monkey_pk, training_sample)
            training_dataset.extend(data)
            training_targetset.extend(target)
        self.training_dataset = numpy.array(training_dataset)
        self.training_targetset = numpy.array(training_targetset)


class RhesusBeyesDataset_Stage3(RhesusBeyesDataset):
    def __init__(self, *args, **kwargs):
        from matrr.models import MonkeyToDrinkingExperiment
        mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(mtd_etoh_g_kg__gt=1.3)
        super(RhesusBeyesDataset_Stage3, self).__init__(mtds=mtds, *args, **kwargs)
