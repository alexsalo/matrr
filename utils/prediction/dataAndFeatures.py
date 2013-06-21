'''
Created on Jun 12, 2012

@author: slavka
'''

from django.db.models import Q
import numpy

class Dataset(object):
	data = list()
	target = list()

def collect_oa_drinking_of_monkeys(monkeys):
	"""
	Returns a list() of tuple()
	tuple:
		0: Monkey
		1: mean OA daily gkg etoh intake
		2: median OA daily gkg etoh intake
	"""
	values = list()
	for m in monkeys:
		v =  m.mtd_set.filter(~Q(drinking_experiment__dex_type='Induction')).filter(~Q(mtd_etoh_g_kg=None)).values_list('mtd_etoh_g_kg', flat=True)
		if len(v) > 0:
#			v = [value[0]/value[1] for value in v]
			mean = sum(v)/len(v)
			median = numpy.median(v)
			values.append((m, mean, median))
	return values

def collect_reg_of_monkeys(monkeys):
	"""
	Returns a dict(), keys = Monkey.pk, values = mean OA daily gkg etoh intake
	"""
	values = collect_oa_drinking_of_monkeys(monkeys)
	mky_reg = dict()
	for m, mean, median in values:
		mky_reg[m.mky_id] = mean
	return mky_reg
	
def collect_3class_of_monkeys(monkeys):
	light_class = 0
	medium_class = 1
	heavy_class = 2
	
	heavy = 4
	light = 2
	values = collect_oa_drinking_of_monkeys(monkeys)
	monkey_classes = dict()
	for m, mean, median in values:
		used_value = median
		if used_value >= heavy:
			mky_class = heavy_class
		elif used_value <= light:
			mky_class = light_class
		else:
			mky_class = medium_class 
		monkey_classes[m.mky_id] = mky_class
	return monkey_classes

def collect_4class_of_monkeys(monkeys):
	light_class = 0
	avg_class = 1
	medium_class = 2
	heavy_class = 3
	
	heavy = 3.5
	med = 2.5
	avg = 2
	
	values = collect_oa_drinking_of_monkeys(monkeys)
	monkey_classes = dict()
	for m, mean, median in values:
		used_value = median
		if used_value >= heavy:
			mky_class = heavy_class
		elif used_value >= med:
			mky_class = medium_class
		elif used_value >= avg:
			mky_class = avg_class
		else:
			mky_class = light_class 
		monkey_classes[m.mky_id] = mky_class
	return monkey_classes
		
def collect_features_pca_by_grant_of_monkeys(monkeys):
	"""
	Returns a dict(),
	keys = Monkey.pk
	value = tuple()
		0: daily average mtd_max_bout_vol/mtd_weight
		1: daily average mtd_max_bout_vol
		2: daily average mtd_pct_max_bout_vol_total_etoh
	"""
	values = dict()
	for m in monkeys:
		v = m.mtd_set.filter(drinking_experiment__dex_type='Induction').filter(~Q(mtd_max_bout_vol=None)).order_by(
				'drinking_experiment__dex_date')[59:].values_list('mtd_weight', 'mtd_max_bout_vol', 'mtd_max_bout_length',
				'mtd_pct_max_bout_vol_total_etoh')
		if len(v) > 0:
			vol = 0 # sum of all day's (max_bout_vol / weight), units= ml/kg
			length = 0 # sum of all day's max_bout_length
			pct = 0 # sum of all day's pct_max_bout_vol_total_etoh
			for value in v:		
				vol += value[1]/value[0]
				length += value[2]
				pct += value[3] 
			mtds_len = len(v)
			# store the sums averaged by number of days
			values[m.mky_id] = (vol/mtds_len, length/mtds_len, pct/mtds_len)
	return values

def create_dataset(monkeys, feature_fce, class_fce, normalize=True):
	monkey_data = feature_fce(monkeys)
	monkey_classes = class_fce(monkeys)
	data = list()
	klass =  list()
	for mky, mky_class in monkey_classes.iteritems():
		data.append(monkey_data[mky])
		klass.append(mky_class)
	dataset = Dataset()
	
	adata = numpy.array(data)
	if normalize:
#		z-score normalization of each feature
		for i in range(len(adata[0,:])):
			column = adata[:, i]
			adata[:, i] = (column - column.mean())/column.std()

	dataset.data = adata
	dataset.target = klass
	return dataset
	
	
		
