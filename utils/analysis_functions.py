from __future__ import division
import numpy as np
import numpy
from scipy.cluster import vq

dot = np.dot
__author__ = 'jarquet'

dict_header = "key=Monkey', columns=['hippocampus+allocortex','cortisol','ACTH','DOC','aldosterone','DHEAS','EtOH (vol)','H2O (vol)', 'isocortex','lateral ventricles']"
_6dict = dict()
_6dict[23779] = [ -0.0017,15.36, -27.87,103.6,244.33,0.043,69.8,203.7, -0.0071,0.0011]
_6dict[21177] = [0.0021, -5.21, -3.3333,168.1667, -40.2467,0.016,10.3,103.8,0.0022, -0.0004, ]
_6dict[23582] = [ -0.0002,38.235, -48.51,62.2,68.46,0.0225,64.9,243.3, -0.0086,0.0013, ]
_6dict[21178] = [0.0011,7.8633,4,226, -24.0967,0.0677,5.3,163.1,0.0045, -0.0001, ]
_6dict[21119] = [0.0006, -14.8467, -16.3333,146.2333, -16.8233,0.0373,63.7,167.2,0.0013, -0.0002, ]
_6dict[22517] = [0.0004,1.81,5.6667,173.3333,1.6633,0.0327,46.7,191.4,0.0048, -0.0001, ]
_6dict[23762] = [ -0.0005, -3.255, -47.36,78.85,66.005, -0.046,96.6,170.1, -0.0107,0, ]
_6dict[20357] = [ -0.001, -3.11, -5,225.4667,25.7167,0.0167,62,131.7, -0.0042,0, ]
_6dict[22215] = [ -0.0002, -7.5667, -2.6667,180, -58.04,0.087,37.5,112.8, -0.0036,0, ]
_6dict[20336] = [ -0.0008, -7.0933,3.3333,177.3, -53.53,0.062,36.1,73.2, -0.0037,0.0001, ]
_6dict[23838] = [0.0003, -8.3, -24.47,116, -47.63,0.071,81.5,57.6, -0.0023, -0.0006, ]
_6dict[22427] = [0.0002,2.6767,5.6667,194.2667,31.4933,0.107,56.6,147.2, -0.0068, -0.0001, ]
_6dict[23764] = [ -0.0027,2.045, -15.98,67.2,211.26,0.0185,109.9,205.8, -0.0156,0.0008, ]
_6dict[23773] = [ -0.0022, -6.835, -27,29.65,118.85,0.0425,95.9,260.8, -0.0076,0.0002, ]
_6dict[21607] = [0.0013, -13.3567, -4.3333,156.7333, -2.8267,0.0317,59.3,53.6,0.0013, -0.0001, ]
_6dict[23784] = [ -0.0014, -16.755, -47.84,2.5, -8.615,0.006,91.6,178.2, -0.0098,0.0001, ]

_12dict = dict()
_12dict[23779] = [ -0.0012,9.36, -28.83,94.6,190.84,0.042,76.6,195.2, -0.0044,0.0009,]
_12dict[21177] = [0.0008, -7.85, -2.3333,154.1667, -44.1967,0.012,11.6,97.5,0.0047, -0.0005, ]
_12dict[23582] = [0,32.235, -49.46,61.2,63.28,0.0435,63,209.9, -0.0052,0.001, ]
_12dict[21178] = [0.0004,5.2133, -1,208, -32.9967,0.0727,6.8,162.8, -0.0037, -0.0003, ]
_12dict[21119] = [0.0014, -12.9367, -17.3333,160.2333, -20.6633,0.0333,65.9,170.1,0.0037, -0.0006, ]
_12dict[22517] = [0.0004,3.24,3.6667,189.3333,9.5633,0.0387,50.5,190.7,0.0031, -0.0003, ]
_12dict[23762] = [ -0.0004, -2.255, -48.92,92.85,40.575, -0.034,91.9,155.5, -0.0117,0.0004, ]
_12dict[20357] = [ -0.0002, -2.6, -6,240.4667,39.1367,0.0137,65.2,125.1, -0.0035, -0.0002, ]
_12dict[22215] = [0.0005, -7.3267, -4.6667,185, -59.03,0.095,38.7,118, -0.0001, -0.0004, ]
_12dict[20336] = [ -0.0004, -8.3433,3.3333,161.3, -42.6,0.054,30.6,98.9, -0.0036, -0.0001, ]
_12dict[23838] = [0.0013, -10.3, -26.86,111, -72.66,0.09,76.3,49.2,0.0011, -0.0003, ]
_12dict[22427] = [0.0003,1.8667,6.6667,198.2667,52.9733,0.126,57.2,153.7, -0.0012, -0.0001, ]
_12dict[23764] = [ -0.0012, -0.955, -19.67,69.2,194.26,0.0315,101.4,209.8, -0.0118,0.0009, ]
_12dict[23773] = [ -0.0016, -7.835, -29.4,22.65,57.88,0.0525,76.9,294.3, -0.0139,0.0008, ]
_12dict[21607] = [0.0008, -13.3667, -4.3333,143.7333,12.0933,0.0287,62.6,59.4, -0.0014, -0.0004, ]
_12dict[23784] = [ -0.0003, -16.755, -47.32,33.5, -39.485,0.004,81.5,139.7, -0.003,0, ]

list_header = ['Monkey','hippocampus+allocortex','cortisol','ACTH','DOC','aldosterone','DHEAS','EtOH (vol)','H2O (vol)', 'isocortex','lateral ventricles']
_6list = list()
_6list.append([23779, -0.0017,15.36, -27.87,103.6,244.33,0.043,69.8,203.7, -0.0071,0.0011])
_6list.append([21177,0.0021, -5.21, -3.3333,168.1667, -40.2467,0.016,10.3,103.8,0.0022, -0.0004, ])
_6list.append([23582, -0.0002,38.235, -48.51,62.2,68.46,0.0225,64.9,243.3, -0.0086,0.0013, ])
_6list.append([21178,0.0011,7.8633,4,226, -24.0967,0.0677,5.3,163.1,0.0045, -0.0001, ])
_6list.append([21119,0.0006, -14.8467, -16.3333,146.2333, -16.8233,0.0373,63.7,167.2,0.0013, -0.0002, ])
_6list.append([22517,0.0004,1.81,5.6667,173.3333,1.6633,0.0327,46.7,191.4,0.0048, -0.0001, ])
_6list.append([23762, -0.0005, -3.255, -47.36,78.85,66.005, -0.046,96.6,170.1, -0.0107,0, ])
_6list.append([20357, -0.001, -3.11, -5,225.4667,25.7167,0.0167,62,131.7, -0.0042,0, ])
_6list.append([22215, -0.0002, -7.5667, -2.6667,180, -58.04,0.087,37.5,112.8, -0.0036,0, ])
_6list.append([20336, -0.0008, -7.0933,3.3333,177.3, -53.53,0.062,36.1,73.2, -0.0037,0.0001, ])
_6list.append([23838,0.0003, -8.3, -24.47,116, -47.63,0.071,81.5,57.6, -0.0023, -0.0006, ])
_6list.append([22427,0.0002,2.6767,5.6667,194.2667,31.4933,0.107,56.6,147.2, -0.0068, -0.0001, ])
_6list.append([23764, -0.0027,2.045, -15.98,67.2,211.26,0.0185,109.9,205.8, -0.0156,0.0008, ])
_6list.append([23773, -0.0022, -6.835, -27,29.65,118.85,0.0425,95.9,260.8, -0.0076,0.0002, ])
_6list.append([21607,0.0013, -13.3567, -4.3333,156.7333, -2.8267,0.0317,59.3,53.6,0.0013, -0.0001, ])
_6list.append([23784, -0.0014, -16.755, -47.84,2.5, -8.615,0.006,91.6,178.2, -0.0098,0.0001, ])

_12list = list()
_12list.append([23779, -0.0012,9.36, -28.83,94.6,190.84,0.042,76.6,195.2, -0.0044,0.0009,])
_12list.append([21177,0.0008, -7.85, -2.3333,154.1667, -44.1967,0.012,11.6,97.5,0.0047, -0.0005, ])
_12list.append([23582,0,32.235, -49.46,61.2,63.28,0.0435,63,209.9, -0.0052,0.001, ])
_12list.append([21178,0.0004,5.2133, -1,208, -32.9967,0.0727,6.8,162.8, -0.0037, -0.0003, ])
_12list.append([21119,0.0014, -12.9367, -17.3333,160.2333, -20.6633,0.0333,65.9,170.1,0.0037, -0.0006, ])
_12list.append([22517,0.0004,3.24,3.6667,189.3333,9.5633,0.0387,50.5,190.7,0.0031, -0.0003, ])
_12list.append([23762, -0.0004, -2.255, -48.92,92.85,40.575, -0.034,91.9,155.5, -0.0117,0.0004, ])
_12list.append([20357, -0.0002, -2.6, -6,240.4667,39.1367,0.0137,65.2,125.1, -0.0035, -0.0002, ])
_12list.append([22215,0.0005, -7.3267, -4.6667,185, -59.03,0.095,38.7,118, -0.0001, -0.0004, ])
_12list.append([20336, -0.0004, -8.3433,3.3333,161.3, -42.6,0.054,30.6,98.9, -0.0036, -0.0001, ])
_12list.append([23838,0.0013, -10.3, -26.86,111, -72.66,0.09,76.3,49.2,0.0011, -0.0003, ])
_12list.append([22427,0.0003,1.8667,6.6667,198.2667,52.9733,0.126,57.2,153.7, -0.0012, -0.0001, ])
_12list.append([23764, -0.0012, -0.955, -19.67,69.2,194.26,0.0315,101.4,209.8, -0.0118,0.0009, ])
_12list.append([23773, -0.0016, -7.835, -29.4,22.65,57.88,0.0525,76.9,294.3, -0.0139,0.0008, ])
_12list.append([21607,0.0008, -13.3667, -4.3333,143.7333,12.0933,0.0287,62.6,59.4, -0.0014, -0.0004, ])
_12list.append([23784, -0.0003, -16.755, -47.32,33.5, -39.485,0.004,81.5,139.7, -0.003,0, ])

def monkey_volumetric_monteFA(out_var='execute', iterations=10):
	import mdp
	import csv
	import numpy
	from random import randint

	def monte_carlo(input, more_input=None, iterations=10):
		keys = input.keys()
		output = dict()
		for key in keys:
			output[key] = list()

		input_length = len(keys)
		node_exception_count = 0
		valueerror_exception_count = 0
		for i in range(15*iterations):# * 1000, num of iterations
			def sample_data():
				data = list()
				monkeys = list()
				for j in range(randint(5, 10)):# monkeys per sample, randint includes both endpoints
					id_index = randint(0, input_length-1)
					real_id = keys[id_index]
					if more_input and randint(0, 1): # randomly choose which input dictionary, if 2nd input dictionary exist
						_d = more_input[real_id]
					else:
						_d = input[real_id]
					if not _d in data:
						data.append(_d)
						monkeys.append(real_id)

				data = numpy.array(data)
				return data, monkeys

			while True:
				data, monkeys = sample_data()
				fa = mdp.nodes.FANode()
				try:
					fa.train(data)
					fa.stop_training()
					fa_output = fa.execute(data)
				except mdp.NodeException as m:
					node_exception_count += 1
					continue
				except ValueError as m:
					valueerror_exception_count += 1
					continue
				else:
					break

			if out_var == 'mu':
				fa_output = fa.mu
			elif out_var == 'A':
				fa_output = fa.A
			elif out_var == 'E_y_mtx':
				fa_output = fa.E_y_mtx
			elif out_var == 'sigma':
				fa_output = fa.sigma
			else:
				pass
			output_convert = list()
			if out_var == 'sigma':
				output_convert.append(list(fa_output))
			else:
				for row in fa_output:
					output_convert.append(list(row))

			for key, fa_o in zip(monkeys, output_convert):
				output[key].append(fa_o)
			if i % 1000 == 0:
				print "Pass %d complete. %d node exceptions, %d value exceptions." % (i, node_exception_count, valueerror_exception_count)
		return output

	six_month_output = monte_carlo(_6dict, iterations=iterations)
	twelve_month_output = monte_carlo(_12dict, iterations=iterations)
	all_output = monte_carlo(_6dict, _12dict, iterations=iterations)

	header = ['hippocampus+allocortex', 'cortisol', 'ACTH', 'DOC', 'aldosterone', 'DHEAS', 'EtOH (vol)', 'H2O (vol)', 'isocortex', 'lateral ventricles', 'mky_real_id']
	outputs = [all_output, six_month_output, twelve_month_output]
	labels = ['AllDataSampled', "First6MonthsSampled", "Second6MonthsSampled"]
	labels = ["%s.%s" % (l, out_var) for l in labels]

	for data, filename in zip(outputs, labels):
		output = csv.writer(open('%s.csv' % filename, 'w'))
		output.writerow(header)
		for key in data.keys():
			mky_data = data[key]
			for row in mky_data:
				row.append(key)
				output.writerow(row)

def dump_postprandial_matrices(monkeys_only=False):
	import csv
	from matrr.models import Monkey, Cohort, MonkeyToDrinkingExperiment, ExperimentEvent, Sum
	def _cluster_assignment(monkeys):
		_gte2 = dict()
		_gte3 = dict()
		_gte4 = dict()
		for mky in monkeys:
			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky)
			_gte2[mky] = mtds.filter(mtd_etoh_g_kg__gte=2).count()
			_gte3[mky] = mtds.filter(mtd_etoh_g_kg__gte=3).count()
			_gte4[mky] = mtds.filter(mtd_etoh_g_kg__gte=4).count()
		res2, idx2 = vq.kmeans2(numpy.array([_gte2[mky] for mky in monkeys]), 2)
		res3, idx3 = vq.kmeans2(numpy.array([_gte3[mky] for mky in monkeys]), 2)
		res4, idx4 = vq.kmeans2(numpy.array([_gte4[mky] for mky in monkeys]), 2)
		for i, mky in enumerate(monkeys):
			_gte2[mky] = idx2[i]
			_gte3[mky] = idx3[i]
			_gte4[mky] = idx4[i]
		return [_gte2, _gte3, _gte4]
	def _build_postprandial_matrix(cohort, minutes, cluster_assignment, monkeys=None):
		"""
		This makes a data structure fitting the following design.
		list( # Monkey # % etoh consumed outside (minutes) after pellet # Cluster assignment, based on day count >= 2/3/4 gkg # ect...
			[<Monkey: 10048>, [0.97319840076047681, 0], [0.97319840076047681, 0], [0.97319840076047681, 1]]
			[<Monkey: 10049>, [0.97096354516853889, 1], [0.97096354516853889, 0], [0.97096354516853889, 1]]
			[<Monkey: 10050>, [0.61919341891216129, 0], [0.61919341891216129, 0], [0.61919341891216129, 1]]
			[<Monkey: 10051>, [0.98696245904495228, 1], [0.98696245904495228, 0], [0.98696245904495228, 0]]
			[<Monkey: 10052>, [0.90424440706200804, 0], [0.90424440706200804, 0], [0.90424440706200804, 1]]
			[<Monkey: 10053>, [0.73065151067833833, 0], [0.73065151067833833, 0], [0.73065151067833833, 1]]
			[<Monkey: 10054>, [0.9953534385998023, 1], [0.9953534385998023, 0], [0.9953534385998023, 0]]
			[<Monkey: 10055>, [0.99405465790184422, 0], [0.99405465790184422, 0], [0.99405465790184422, 1]]
			[<Monkey: 10056>, [0.94261800522588424, 0], [0.94261800522588424, 0], [0.94261800522588424, 1]]
			[<Monkey: 10057>, [0.96637110291771489, 1], [0.96637110291771489, 0], [0.96637110291771489, 1]]
			[<Monkey: 10058>, [0.97357126215980005, 1], [0.97357126215980005, 0], [0.97357126215980005, 1]]
			[<Monkey: 10059>, [0.96442083938613721, 1], [0.96442083938613721, 0], [0.96442083938613721, 0]]
		"""
		assert bool(int(minutes))
		if not monkeys:
			if not isinstance(cohort, Cohort):
				try:
					cohort = Cohort.objects.get(pk=cohort)
				except Cohort.DoesNotExist:
					raise Exception("%s not a valid cohort." % str(cohort))
			monkeys = cohort.monkey_set.filter(mky_drinking=True).order_by('pk')

		_min = dict()
		for mky in monkeys:
			eevs = ExperimentEvent.objects.filter(monkey=mky).exclude(eev_etoh_volume=None).exclude(eev_etoh_volume=0)
			total_volume = eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
			_min[mky] = eevs.exclude(eev_pellet_elapsed_time_since_last__lte=minutes*60).aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum'] / total_volume

		cohort_matrix = list()
		header = ['mky', '%% drinking OUTSIDE %d minutes from last pellet' % minutes, "2 gkg group id"]
		header.extend(['%% drinking OUTSIDE %d minutes from last pellet' % minutes, "3 gkg group id"])
		header.extend(['%% drinking OUTSIDE %d minutes from last pellet' % minutes, "4 gkg group id"])
		for mky in monkeys:
			row = [str(mky),]
			for cluster in cluster_assignment:
				c = [_min[mky], cluster[mky]]
				row.extend(c)
			cohort_matrix.append(row)
		return cohort_matrix, header
	#------
	cohorts = Cohort.objects.filter(pk__in=[5, 6, 10])
	minutes = [1]
	minutes.extend([i for i in range(5, 31, 5)])

	if not monkeys_only:
		for coh in cohorts:
			filename = "%s.csv" % str(coh)
			filename = filename.replace(" ", "_")
			dump = csv.writer(open(filename % coh, 'w'))
			cluster_assignment = _cluster_assignment(coh.monkey_set.filter(mky_drinking=True))
			for _min in minutes:
				data, header = _build_postprandial_matrix(coh, _min, cluster_assignment)
				dump.writerow(header)
				for row in data:
					dump.writerow(row)

	mky_ids = cohorts.filter(monkey__mky_drinking=True).values_list('monkey__pk', flat=True)
	monkeys = Monkey.objects.filter(pk__in=mky_ids)
	cluster_assignment = _cluster_assignment(monkeys)
	dump = csv.writer(open("AllRhesusMonkeys.csv", 'w'))
	for _min in minutes:
		data, header = _build_postprandial_matrix(None, _min, cluster_assignment, monkeys=monkeys)
		dump.writerow(header)
		for row in data:
			dump.writerow(row)







