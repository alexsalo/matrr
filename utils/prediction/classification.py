'''
Created on Jun 18, 2012

@author: slavka
'''

from sklearn.svm import SVR
from sklearn.cross_validation import cross_val_score
from dataAndFeatures import *
from matrr.models import Monkey


def modified_slavka_code():
	monkeys = Monkey.objects.Drinkers().filter(cohort__in=[5,6,9,10])
	d = create_dataset(monkeys, collect_features_pca_by_grant_of_monkeys, collect_reg_of_monkeys)
	print d.target
	svr = SVR()


	svr.fit(d.data[:-1], d.target[:-1])
	print svr.predict(d.data[4])
	print svr.predict(d.data[-1])

	svr.fit(d.data[1:], d.target[1:])
	print svr.predict(d.data[0])

	svr.fit(d.data[2:], d.target[2:])
	print svr.predict(d.data[1])

	print cross_val_score(svr, d.data, numpy.asarray(d.target))

def GaussianNB_rhesus():
	from utils.prediction.datasets import RhesusPCADataset
	pca_data = RhesusPCADataset()
	from sklearn.naive_bayes import GaussianNB
	gnb = GaussianNB()
	y_pred = gnb.fit(pca_data.data, pca_data.target).predict(pca_data.data)
	print "Number of points : %d" % len(pca_data.target) # 2958
	print "Number of mislabeled points : %d" % (pca_data.target != y_pred).sum() # 1938

def BernoulliNB_rhesus():
	from utils.prediction.datasets import RhesusPCADataset
	pca_data = RhesusPCADataset()
	from sklearn.naive_bayes import BernoulliNB
	gnb = BernoulliNB()
	y_pred = gnb.fit(pca_data.data, pca_data.target).predict(pca_data.data)
	print "Number of points : %d" % len(pca_data.target) # 2958
	print "Number of mislabeled points : %d" % (pca_data.target != y_pred).sum() # 1870

def MultinomialNB_rhesus():
	from utils.prediction.datasets import RhesusPCADataset
	pca_data = RhesusPCADataset(MultinomialNB=True)
	from sklearn.naive_bayes import MultinomialNB
	gnb = MultinomialNB()
	y_pred = gnb.fit(pca_data.data, pca_data.target).predict(pca_data.data)
	print "Number of points : %d" % len(pca_data.target) # 2958
	print "Number of mislabeled points : %d" % (pca_data.target != y_pred).sum() # 2083

def GaussianNB_rhesus_trainHormone_predictAll():
	from utils.prediction.datasets import RhesusPCADataset
	only_hormone = RhesusPCADataset(include_only_hormone=True)
	with_hormone = RhesusPCADataset(include_hormone=True)
	from sklearn.naive_bayes import GaussianNB
	gnb = GaussianNB()
	trained = gnb.fit(only_hormone.data, only_hormone.target)
	y_pred = trained.predict(with_hormone.data)
	print "Number of points : %d" % len(with_hormone.target) # 2958
	print "Number of mislabeled points : %d" % (with_hormone.target != y_pred).sum() # 1931 # 1942

def BernoulliNB_rhesus_trainHormone_predictAll():
	from sklearn.naive_bayes import BernoulliNB
	from utils.prediction.datasets import RhesusPCADataset
	only_hormone = RhesusPCADataset(include_only_hormone=True)
	with_hormone = RhesusPCADataset(include_hormone=True)
	gnb = BernoulliNB()
	trained = gnb.fit(only_hormone.data, only_hormone.target)
	y_pred = trained.predict(with_hormone.data)
	print "Number of points : %d" % len(with_hormone.target) # 2958
	print "Number of mislabeled points : %d" % (with_hormone.target != y_pred).sum() # 2029

def MultinomialNB_rhesus_trainHormone_predictAll():
	from sklearn.naive_bayes import MultinomialNB
	from utils.prediction.datasets import RhesusPCADataset
	only_hormone = RhesusPCADataset(MultinomialNB=True, include_only_hormone=True)
	with_hormone = RhesusPCADataset(MultinomialNB=True, include_hormone=True)
	gnb = MultinomialNB()
	trained = gnb.fit(only_hormone.data, only_hormone.target)
	y_pred = trained.predict(with_hormone.data)
	print "Number of points : %d" % len(with_hormone.target) # 2958
	print "Number of mislabeled points : %d" % (with_hormone.target != y_pred).sum() # 2008

def _bernoulli_beyes_RBD_sample(rhesus_beyes_dataset):
	from sklearn.naive_bayes import BernoulliNB
	from utils import plotting_beta
	gnb = BernoulliNB()
	rhesus_beyes_dataset.sample_dataset()
	trained = gnb.fit(rhesus_beyes_dataset.training_dataset, rhesus_beyes_dataset.training_targetset)

	truePositiveCount = 0
	falsePositiveCount = 0
	for rmbd in rhesus_beyes_dataset.testing_datasets:
		test_data = rmbd.get_aggregate_dataset()
		y_pred = trained.predict(test_data)
		if y_pred == plotting_beta.rhesus_monkey_category[rmbd.monkey_pk]:
			truePositiveCount += 1
		else:
			falsePositiveCount += 1
	return truePositiveCount, falsePositiveCount

def bootstrap_bernouli_beyes_RBD(first_key, second_key, loop_count=10, all_monkeys=False):
	import gc
	from utils import plotting_beta
	from utils.prediction.datasets import RhesusBeyesDataset
	monkey_ids = plotting_beta.rhesus_drinkers_distinct[first_key]
	monkey_ids.extend(plotting_beta.rhesus_drinkers_distinct[second_key])
	if all_monkeys:
		monkey_ids = plotting_beta.all_rhesus_drinkers

	rbd = RhesusBeyesDataset(monkey_ids=monkey_ids)
	tpc = 0
	fpc = 0
	for i in range(loop_count):
		print "Loop %d of %d" % (i+1, loop_count)
		tp, fp = _bernoulli_beyes_RBD_sample(rbd)
		print "TruePositiveCount: %d" % tp
		print "FalseCount: %d" % fp
		print '---'
		tpc += tp
		fpc += fp
		gc.collect()
	print "Looping finished! All stages"
	print "Total TruePositive Count:"
	print tpc
	print "Total FalsePositive Count:"
	print fpc

def bootstrap_bernouli_beyes_RBD_Stage3(first_key, second_key, loop_count=10, all_monkeys=False):
	import gc
	from utils import plotting_beta
	from utils.prediction.datasets import RhesusBeyesDataset_Stage3
	monkey_ids = plotting_beta.rhesus_drinkers_distinct[first_key]
	monkey_ids.extend(plotting_beta.rhesus_drinkers_distinct[second_key])
	if all_monkeys:
		monkey_ids = plotting_beta.all_rhesus_drinkers

	rbd = RhesusBeyesDataset_Stage3(monkey_ids=monkey_ids)
	tpc = 0
	fpc = 0
	for i in range(loop_count):
		print "Loop %d of %d" % (i+1, loop_count)
		tp, fp = _bernoulli_beyes_RBD_sample(rbd)
		print "TruePositiveCount: %d" % tp
		print "FalseCount: %d" % fp
		print '---'
		tpc += tp
		fpc += fp
		gc.collect()
	print "Looping finished!"
	print "Total TruePositive Count:"
	print tpc
	print "Total FalsePositive Count:"
	print fpc
