__author__ = 'jarquet'

def monkey_volumetric_monteFA():
	import mdp
	import json
	import numpy
	from random import randint
	fan = mdp.nodes.FANode

	_6dict = dict()
	_12dict = dict()
	dict_header = "key=Monkey', columns=['hippocampus+allocortex','cortisol','ACTH','DOC','aldosterone','DHEAS','EtOH (vol)','H2O (vol)', 'isocortex','lateral ventricles']"
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
	
	def monte_carlo(input, more_input=None):
		output = dict()
		keys = input.keys()
		input_length = len(keys)
		for i in range(15):# * 1000, num of iterations
			data = list()
			monkeys = list()
			for j in range(randint(1, input_length)):# monkeys per sample, randint includes both endpoints
				id_index = randint(0, input_length-1)
				real_id = keys[id_index]
				if more_input and randint(0, 1): # randomly choose which input dictionary, if 2nd input dictionary exist
					data.append(more_input[real_id])
					monkeys.append(real_id)
				else:
					data.append(input[real_id])
					monkeys.append(real_id)

			fa = mdp.nodes.FANode()
			data = numpy.array(list)
			fa_output = fa.execute(data)

			output_convert = list()
			for row in fa_output:
				output_convert.append(list(row))

			for key, fa_o in zip(monkeys, output_convert):
				output[key].append(fa_o)
		return output

	six_month_output = monte_carlo(_6dict)
	f = open('six_month_output.json.txt', 'w')
	f.write(str(dict_header))
	f.write(json.dumps(six_month_output))
	f.close()
	twelve_month_output = monte_carlo(_12dict)
	f = open('twelve_month_output.json.txt', 'w')
	f.write(str(dict_header))
	f.write(json.dumps(twelve_month_output))
	f.close()
	all_output = monte_carlo(_6dict, _12dict)
	f = open('all_month_output.json.txt', 'w')
	f.write(str(dict_header))
	f.write(json.dumps(all_output))
	f.close()


