from django.db.models import Sum
import numpy
from matplotlib import pyplot, gridspec, ticker, cm, patches
from scipy import cluster
from matrr.models import *
from utils import plotting




def cohorts_daytime_bouts_histogram():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	main_plot = None
	for cohort in cohorts:
		fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
		main_gs = gridspec.GridSpec(3, 40)
		main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
		main_plot = fig.add_subplot(main_gs[:,:], sharey=main_plot)
		main_plot.set_title(cohort.coh_cohort_name + " Open Access Only")
		main_plot.set_xlabel("Seconds of day, binned by hour")
		main_plot.set_ylabel("Total bout count during hour")
		x_axis = list()
		y_axes = list()
		labels = list()
		index = 0
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey)
			bout_starts = bouts.values_list('ebt_start_time', flat=True)
			bout_starts = numpy.array(bout_starts)
			y_axes.append(bout_starts)
			x_axis.append(index)
			labels.append(str(monkey.pk))
			index += 1
		bin_edges = range(0, _22_hour, _1_hour)
		n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
		main_plot.axvspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
		main_plot.legend(ncol=5, loc=9)
		main_plot.set_ylim(ymax=1600)

def cohorts_daytime_volbouts_bargraph():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	width = 1
	main_plot = None
	for cohort in cohorts:
		index = 0
		night_time = list()
		labels = set()
		fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
		main_gs = gridspec.GridSpec(3, 40)
		main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
		main_plot = fig.add_subplot(main_gs[:,1:], sharey=main_plot)
		main_plot.set_title(cohort.coh_cohort_name + " Open Access Only")
		main_plot.set_xlabel("Hour of day")
		main_plot.set_ylabel("Total vol etoh consumed during hour")

		monkeys = cohort.monkey_set.exclude(mky_drinking=False)
		mky_count = float(monkeys.count())
		cmap = cm.get_cmap('jet')
		mky_color = list()
		for idx, key in enumerate(monkeys):
			mky_color.append(cmap(idx / (mky_count-1)))
		for start_time in range(0, _22_hour, _1_hour):
			x_axis = list()
			y_axis = list()
			if start_time >= lights_out and start_time <= lights_on:
				night_time.append(index)
			for monkey in monkeys:
				bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
				bout_vols = bouts.values_list('ebt_volume', flat=True)
				bouts_sum = numpy.array(bout_vols).sum()
	#			bout_starts = bout_starts - diff
				y_axis.append(bouts_sum	)
				x_axis.append(index)
				index += 1
				labels.add(str(monkey.pk))
			rects1 = main_plot.bar(x_axis, y_axis, width, color=mky_color, alpha=.7)
			index += 2
		main_plot.legend(rects1, labels, ncol=5, loc=9)
		main_plot.axvspan(min(night_time), max(night_time), color='black', alpha=.2, zorder=-100)
		x_labels = ['hr %d' % i for i in range(1,23)]
		main_plot.set_xlim(xmax=index-2)
		main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
		xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
		pyplot.setp(xtickNames, rotation=45)
		main_plot.set_ylim(ymax=100000)


def cohorts_daytime_bouts_boxplot():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	x_axis = list()
	y_axes = list()
	labels = list()
	index = 0
	for cohort in cohorts:
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			bouts = ExperimentBout.objects.filter(mtd__monkey=monkey)
			bout_starts = bouts.values_list('ebt_start_time', flat=True)
			bout_starts = numpy.array(bout_starts)
			y_axes.append(bout_starts)
			x_axis.append(index)
			labels.append(str(monkey.pk))
			index += 1
		index += 3

	bp = main_plot.boxplot(y_axes, positions=x_axis, whis=2, sym='.')
	main_plot.axvspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)

	xtickNames = pyplot.setp(main_plot, xticklabels=labels)
	pyplot.setp(xtickNames, rotation=45)
	return fig, False

def cohorts_daytime_bouts_boxplot_remix():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
#	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
#	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	x_axis = list()
	y_axes = list()
	labels = list()
	index = 0
	for cohort in cohorts:
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey)
			night_bouts = bouts.filter(ebt_start_time__gte=lights_out).filter(ebt_start_time__lt=lights_on).values_list('ebt_start_time', flat=True)
			day_bouts = bouts.filter(ebt_start_time__gte=lights_on) | bouts.filter(ebt_start_time__lt=lights_out)
			day_bouts = day_bouts.values_list('ebt_start_time', flat=True)
			new_bouts = list(night_bouts)
			for v in day_bouts:
				if v >= lights_on:
					new_v = v - _24_hour
					new_bouts.append(new_v)
				else:
					new_bouts.append(v)
#			new_bouts.extend(new_bouts)
			y_axes.append(new_bouts)
			x_axis.append(index)
			labels.append(str(monkey.pk))
			index += 1
		index += 3

	bp = main_plot.boxplot(y_axes, positions=x_axis, whis=1.5, sym='.')
	main_plot.axhspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)

	xtickNames = pyplot.setp(main_plot, xticklabels=labels)
	pyplot.setp(xtickNames, rotation=45)
	return fig, False

def cohorts_daytime_bouts_boxplot_doubleremix():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
#	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
#	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_2_hour = 2*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	x_axis = list()
	before_end = list()
	after_start = list()
	night_y = list()
	labels = list()
	index = 0
	for cohort in cohorts:
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey)
			night_bouts = bouts.filter(ebt_start_time__gte=lights_out).filter(ebt_start_time__lt=lights_on).values_list('ebt_start_time', flat=True)
			day_bouts = bouts.filter(ebt_start_time__gte=lights_on) | bouts.filter(ebt_start_time__lt=lights_out)
			day_bouts = day_bouts.values_list('ebt_start_time', flat=True)

			b4_end = list()
			_after_start = list()
			for v in day_bouts:
				if v >= lights_on:
					new_v = v - _24_hour
					b4_end.append(new_v)
				else:
					_after_start.append(v)

			night_y.append(night_bouts)
			before_end.append(b4_end)
			after_start.append(_after_start)
			x_axis.append(index)
			labels.append(str(monkey.pk))
			index += 1
		index += 3


	bp = main_plot.boxplot(before_end, positions=x_axis, whis=1.5, sym='.')
	bp = main_plot.boxplot(after_start, positions=x_axis, whis=1.5, sym='.')
	bp = main_plot.boxplot(night_y, positions=x_axis, whis=1.5, sym='.')

	main_plot.axhspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
	main_plot.axhspan(session_start, session_start-_2_hour, color='red', alpha=.2, zorder=-100)

	xtickNames = pyplot.setp(main_plot, xticklabels=labels)
	pyplot.setp(xtickNames, rotation=45)
	return fig, False

def cohorts_daytime_bouts_boxplot_hattrick():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_2_hour = 2*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	x_axis = list()
	before_end = list()
	after_start = list()
	night_y = list()
	labels = list()
	index = 0
	for cohort in cohorts:
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey)
			night_bouts = bouts.filter(ebt_start_time__gte=lights_out).filter(ebt_start_time__lt=lights_on).values_list('ebt_start_time', flat=True)
			day_bouts = bouts.filter(ebt_start_time__gte=lights_on) | bouts.filter(ebt_start_time__lt=lights_out)
			day_bouts = day_bouts.values_list('ebt_start_time', flat=True)

			b4_end = list()
			_after_start = list()
			for v in day_bouts:
				if v >= lights_on:
					new_v = v - _24_hour
					b4_end.append(new_v)
				else:
					_after_start.append(v)

			_after_start.extend(night_bouts)
			before_end.append(b4_end)
			after_start.append(_after_start)

			x_axis.append(index)
			labels.append(str(monkey.pk))
			index += 1
		index += 3

	bp = main_plot.boxplot(before_end, positions=x_axis, whis=1.5, sym='.')
	bp = main_plot.boxplot(after_start, positions=x_axis, whis=1.5, sym='.')

	main_plot.axhspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
	main_plot.axhspan(session_start, session_start-_2_hour, color='red', alpha=.2, zorder=-100)

	xtickNames = pyplot.setp(main_plot, xticklabels=labels)
	pyplot.setp(xtickNames, rotation=45)
	return fig, False

def cohorts_scatterbox():
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults
	colors = ['green', 'blue', 'red']

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,1:])
	main_plot.set_title("Ethanol Intake Distribution during Open Access ")
	main_plot.set_xlabel("Hour of day")
	main_plot.set_ylabel("Total vol etoh consumed during hour")

	width = 1
	day_hours = range(0, _22_hour, _1_hour)
	cohort_hours = list()
	for cohort in cohorts:
		monkeys = cohort.monkey_set.exclude(mky_drinking=False)
		monkey_hours = list()
		for start_time in day_hours:
			mky_sums = list()
			for monkey in monkeys:
				bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
				bout_vols = bouts.values_list('ebt_volume', flat=True)
				mky_sum = numpy.array(bout_vols).sum()
				mky_sums.append(mky_sum)
			monkey_hours.append(mky_sums)
		cohort_hours.append(monkey_hours)

	x_position = numpy.array([i*(2+len(cohorts)) for i in range(len(day_hours))])
	wrecktangles = list()
	for cohort, ch, color in zip(cohorts, cohort_hours, colors):
		bp = main_plot.boxplot(ch, positions=x_position, sym='.')
		x_position += 1

		wrect = patches.Rectangle((0, 0), 1, 1, fc=color, label=str(cohort))
		wrecktangles.append(wrect)
		for key in bp.keys():
			if key != 'medians':
				pyplot.setp(bp[key], color=color)

	main_plot.legend(wrecktangles, (wrect.get_label() for wrect in wrecktangles), loc=0)

	main_plot.set_xlim(xmin=-1) # i don't understand why i need this
	main_plot.axvspan(7*(2+len(cohorts))-1, 19*(2+len(cohorts))-1, color='black', alpha=.2, zorder=-100)

	x_labels = ['hr %d' % i for i in range(1,23)]
	main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
	xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
	pyplot.setp(xtickNames, rotation=45)

def cohorts_bec_stage_scatter(stage):
	cohorts = list()
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')) # adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')) # young adults
	cohorts.append(Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')) # adolescents
	colors = ["orange", 'blue', 'green']
	scatter_markers = ['+', 'x', '4']
	centroid_markers = ['s', 'D', 'v']

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot.set_title("Induction Stage %d" % (stage+1))
	main_plot.set_xlabel("BEC")
	main_plot.set_ylabel("Hours since last etoh intake")

	starts = [0, .9, 1.4]
	ends = [.6, 1.1, 1.6]
	stage_start = starts[stage]
	stage_end = ends[stage]
	sample_time = [30*60., 60*60., 90*60.]
	for index, cohort in enumerate(cohorts):
		x_axis = list()
		y_axis = list()
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			becs = MonkeyBEC.objects.filter(monkey=monkey).filter(mtd__drinking_experiment__dex_type='Induction').order_by('pk')
			becs = becs.filter(mtd__mtd_etoh_g_kg__gte=stage_start).filter(mtd__mtd_etoh_g_kg__lte=stage_end)
			seconds = becs.values_list('mtd__mtd_seconds_to_stageone', flat=True)
			try:
				y_axis.extend([(s-sample_time[stage])/(60*60) for s in seconds]) # time between end of drinking and sample taken
			except:
				print "skipping monkey %d" % monkey.pk
				continue
			x_axis.extend(becs.values_list('bec_mg_pct', flat=True))


		scatter = main_plot.scatter(x_axis, y_axis, color=colors[index], marker=scatter_markers[index], alpha=1, s=150, label=str(cohort))
		res, idx = cluster.vq.kmeans2(numpy.array(zip(x_axis, y_axis)), 1)
		scatter = main_plot.scatter(res[:,0][0], res[:,1][0], color=colors[index], marker=centroid_markers[index], alpha=1, s=250, label=str(cohort) + " Centroid")

	main_plot.axhspan(0, 0, color='black', alpha=.4, zorder=-100)
	main_plot.text(0, 0, "Blood Sample Taken")

	leg = main_plot.legend(loc=9, ncol=3, scatterpoints=1)
	ltext = leg.get_texts()
	pyplot.setp(ltext, fontsize=12)
	main_plot.set_xlim(xmin=0)
	main_plot.set_ylim(ymin=-1.7)
	yticks = [-1,]
	yticks.extend(range(0,13, 2))
	main_plot.set_yticks(yticks)

def cohort_etoh_gkg_histogram(cohort):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot.set_title(cohort.coh_cohort_name + " Open Access Only")
	main_plot.set_xlabel("# of days with ethanol intake")
	main_plot.set_ylabel("Ethanol Intake, g/kg")
	y_axes = list()
	labels = list()
	for monkey in cohort.monkey_set.exclude(mky_drinking=False):
		mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment__dex_type='Open Access', monkey=monkey)
		gkg_values = mtds.values_list('mtd_etoh_g_kg', flat=True)
		gkg_values = numpy.array(gkg_values)
		y_axes.append(gkg_values)
		labels.append(str(monkey.pk))
	bin_edges = range(9)
	n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
	main_plot.legend(ncol=2, loc=0)

def cohort_etoh_quadbar(cohort):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False
	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	fig.suptitle(str(cohort), size=18)
	main_gs = gridspec.GridSpec(2, 2)
	main_gs.update(left=0.08, right=.98, top=.92, bottom=.06, wspace=.02, hspace=.23)

	cohort_colors =  ['navy', 'slateblue']
	main_plot = None
	subplots = [(i, j) for i in range(2) for j in range(2)]
	for gkg, _sub in enumerate(subplots, 1):
		main_plot = fig.add_subplot(main_gs[_sub], sharey=main_plot)
		main_plot.set_title("Greater than %d g per kg Etoh" % gkg)

		monkeys = cohort.monkey_set.filter(mky_drinking=True).values_list('pk', flat=True)
		width = .9

		data = list()
		colors = list()
		for i, mky in enumerate(monkeys):
			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, mtd_etoh_g_kg__gte=gkg).count()
			mtds = mtds if mtds else .001
			data.append((mky, mtds))
			colors.append(cohort_colors[i%2]) # we don't want the colors sorted.  It breaks if you try anyway.
		sorted_data = sorted(data, key=lambda t: t[1])
		sorted_data = numpy.array(sorted_data)
		labels = sorted_data[:,0]
		yaxis = sorted_data[:,1]
		bar = main_plot.bar(range(len(monkeys)), yaxis, width, color=colors)

		if gkg % 2:
			main_plot.set_ylabel("Day count")
		else:
			main_plot.get_yaxis().set_visible(False)

		x_labels = ['%d' % i for i in labels]
		main_plot.set_xticks(range(len(monkeys)))
		xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
		pyplot.setp(xtickNames, rotation=45)
	return fig, True

def cohort_bec_day_distribution(cohort, stage):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False
	colors = ["orange", 'blue', 'green']

	sample_time = [60*30., 60*60., 60*90.]
	starts = [0, .9, 1.4]
	ends = [.6, 1.1, 1.6]
	stage_start = starts[stage]
	stage_end = ends[stage]

	becs = MonkeyBEC.objects.filter(monkey__cohort=cohort).filter(mtd__drinking_experiment__dex_type='Induction') # cohort and induction filter
	becs = becs.filter(mtd__mtd_etoh_g_kg__gte=stage_start).filter(mtd__mtd_etoh_g_kg__lte=stage_end).order_by('bec_collect_date') # stage filter and ordering
	dates = becs.dates('bec_collect_date', 'day').distinct()

	columns = 2
	rows = int( numpy.ceil( dates.count()/columns))

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(rows, columns)
	main_gs.update(left=0.08, right=.98, wspace=.15, hspace=.15)
	main_plot = None

	subplots = [(i, j) for i in range(rows) for j in range(columns)]
	for date, _sub in zip(dates, subplots):
		main_plot = fig.add_subplot(main_gs[_sub])
		x_axis = list()
		y_axis = list()
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			try:
				bec = becs.get(bec_collect_date=date, monkey=monkey)
			except:
				continue

			eevs = ExperimentEvent.objects.filter(monkey=monkey, eev_occurred__year=date.year, eev_occurred__month=date.month, eev_occurred__day=date.day)
			eevs = eevs.exclude(eev_etoh_volume=None).exclude(eev_etoh_volume=0)
			seconds = eevs.values_list('eev_session_time', flat=True)
			try:
				y_vals = [(s-sample_time[stage])/(60*60) for s in seconds] # time between end of drinking and sample taken
			except:
				print "skipping monkey %d" % monkey.pk
				continue

			x_axis.append(bec.bec_mg_pct)
			y_axis.append(y_vals)
		main_plot.boxplot(y_axis, positions=x_axis, widths=5)
		main_plot.axhspan(0, 0, color='black', alpha=.3)

	return fig, True

def cohorts_daytime_volbouts_bargraph_split(phase):
	assert type(phase) == int and 0 <= phase <= 2
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	cohort_1st_oa_end = {_7a: "2011-08-01", _5:"2009-10-13", _4:"2009-05-24"}
	_phase = 'mtd__drinking_experiment__dex_date__gt' if phase == 2 else 'mtd__drinking_experiment__dex_date__lte'

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	title_append = " Phase %d Open Access" % phase if phase else " All Open Access"
	width = 1
	figures = list()
	main_plot = None
	for cohort in cohorts:
		index = 0
		night_time = list()
		labels = set()
		fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
		main_gs = gridspec.GridSpec(3, 40)
		main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
		main_plot = fig.add_subplot(main_gs[:,1:], sharey=main_plot)
		main_plot.set_title(cohort.coh_cohort_name + title_append)
		main_plot.set_xlabel("Hour of day")
		main_plot.set_ylabel("Total vol etoh consumed during hour")

		monkeys = cohort.monkey_set.exclude(mky_drinking=False)
		mky_count = float(monkeys.count())
		cmap = cm.get_cmap('jet')
		mky_color = list()
		for idx, key in enumerate(monkeys):
			mky_color.append(cmap(idx / (mky_count-1)))
		for start_time in range(0, _22_hour, _1_hour):
			x_axis = list()
			y_axis = list()
			if start_time >= lights_out and start_time <= lights_on:
				night_time.append(index)
			for monkey in monkeys:
				bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
				if phase:
					bouts = bouts.filter(**{_phase:cohort_1st_oa_end[cohort]})
				bout_vols = bouts.values_list('ebt_volume', flat=True)
				bouts_sum = numpy.array(bout_vols).sum()
	#			bout_starts = bout_starts - diff
				y_axis.append(bouts_sum	)
				x_axis.append(index)
				index += 1
				labels.add(str(monkey.pk))
			rects1 = main_plot.bar(x_axis, y_axis, width, color=mky_color, alpha=.7)
			index += 2
		main_plot.legend(rects1, labels, ncol=5, loc=9)
		main_plot.axvspan(min(night_time), max(night_time), color='black', alpha=.2, zorder=-100)
		x_labels = ['hr %d' % i for i in range(1,23)]
		main_plot.set_xlim(xmax=index-2)
		main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
		xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
		pyplot.setp(xtickNames, rotation=45)
		main_plot.set_ylim(ymax=100000)
		figures.append((fig, cohort))
	return figures

def cohorts_daytime_bouts_histogram_split(phase):
	assert type(phase) == int and 0 <= phase <= 2
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	cohort_1st_oa_end = {_7a: "2011-08-01", _5:"2009-10-13", _4:"2009-05-24"}
	_phase = 'mtd__drinking_experiment__dex_date__gt' if phase == 2 else 'mtd__drinking_experiment__dex_date__lte'

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	title_append = " Phase %d Open Access" % phase if phase else " All Open Access"
	figures = list()
	main_plot = None
	for cohort in cohorts:
		fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
		main_gs = gridspec.GridSpec(3, 40)
		main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
		main_plot = fig.add_subplot(main_gs[:,:], sharey=main_plot)

		main_plot.set_title(cohort.coh_cohort_name + title_append)
		main_plot.set_xlabel("Hour of Session")
		main_plot.set_ylabel("Total bout count during hour")
		x_axis = list()
		y_axes = list()
		labels = list()
		index = 0
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey)
			if phase:
				bouts = bouts.filter(**{_phase:cohort_1st_oa_end[cohort]})
			bout_starts = bouts.values_list('ebt_start_time', flat=True)
			bout_starts = numpy.array(bout_starts)
			y_axes.append(bout_starts)
			x_axis.append(index)
			labels.append(str(monkey.pk))
			index += 1
		bin_edges = range(0, _22_hour+1, _1_hour)
		n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
		main_plot.axvspan(lights_out, lights_on, color='black', alpha=.2, zorder=-100)
		main_plot.legend(ncol=5, loc=9)
		main_plot.set_ylim(ymax=1600)

		x_labels = ['hr %d' % i for i in range(1,23)]
		new_xticks = range(0, _22_hour, _1_hour)
		new_xticks = [_x + (_1_hour/2.) for _x in new_xticks]
		main_plot.set_xticks(new_xticks)
		xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
		pyplot.setp(xtickNames, rotation=45)
		figures.append((fig, cohort))
	return figures

def cohorts_maxbouts_histogram(phase):
	assert type(phase) == int and 0 <= phase <= 2
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	cohort_1st_oa_end = {_7a: "2011-08-01", _5:"2009-10-13", _4:"2009-05-24"}
	_phase = 'drinking_experiment__dex_date__gt' if phase == 2 else 'drinking_experiment__dex_date__lte'

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	title_append = " Phase %d Open Access" % phase if phase else " All Open Access"
	figures = list()
	main_plot = None
	for cohort in cohorts:
		fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
		main_gs = gridspec.GridSpec(3, 40)
		main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
		main_plot = fig.add_subplot(main_gs[:,:], sharey=main_plot)

		main_plot.set_title(cohort.coh_cohort_name + title_append)
		main_plot.set_xlabel("Maximum Bout Volume")
		main_plot.set_ylabel("Bout Count")
		y_axes = list()
		labels = list()
		max_bout = 0
		for monkey in cohort.monkey_set.exclude(mky_drinking=False):
			mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment__dex_type='Open Access', monkey=monkey)
			if phase:
				mtds = mtds.filter(**{_phase:cohort_1st_oa_end[cohort]})
			mtd_maxes = mtds.values_list('mtd_max_bout_vol', flat=True)
			mtd_maxes = numpy.array(mtd_maxes)
			try:
				max_bout = max_bout if max_bout > mtd_maxes.max() else mtd_maxes.max()
			except:
				continue
			y_axes.append(mtd_maxes)
			labels.append(str(monkey.pk))
		bin_max = 900
		bin_edges = range(0, bin_max, 100)
		n, bins, patches = main_plot.hist(y_axes, bins=bin_edges, normed=False, histtype='bar', alpha=.7, label=labels)
		main_plot.legend(ncol=5, loc=9)
		figures.append((fig, cohort))
	return figures

def cohorts_scatterbox_split(phase):
	assert type(phase) == int and 0 < phase < 3
	colors = ['green', 'blue', 'red']
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	cohort_1st_oa_end = {_7a: "2011-08-01", _5:"2009-10-13", _4:"2009-05-24"}
	_phase = 'mtd__drinking_experiment__dex_date__gt' if phase == 2 else 'mtd__drinking_experiment__dex_date__lte'

	_24_hour = 24*60*60
	_22_hour = 22*60*60
	_12_hour = 12*60*60
	_7_hour = 7*60*60
	_1_hour = 60*60
	session_start = 0
	session_end = session_start + _22_hour
	lights_out = session_start + _7_hour
	lights_on = lights_out + _12_hour
	diff = session_end - lights_on

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,1:])
	main_plot.set_title("Ethanol Intake Distribution during Phase %d Open Access" % phase)
	main_plot.set_xlabel("Hour of day")
	main_plot.set_ylabel("Total vol etoh consumed during hour")

	width = 1
	day_hours = range(0, _22_hour, _1_hour)
	cohort_hours = list()
	for cohort in cohorts:
		monkeys = cohort.monkey_set.exclude(mky_drinking=False)
		monkey_hours = list()
		for start_time in day_hours:
			mky_sums = list()
			for monkey in monkeys:
				bouts = ExperimentBout.objects.filter(mtd__drinking_experiment__dex_type='Open Access', mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
				bouts = bouts.filter(**{_phase:cohort_1st_oa_end[cohort]})
				bout_vols = bouts.values_list('ebt_volume', flat=True)
				mky_sum = numpy.array(bout_vols).sum()
				mky_sums.append(mky_sum)
			monkey_hours.append(mky_sums)
		cohort_hours.append(monkey_hours)

	x_position = numpy.array([i*(2+len(cohorts)) for i in range(len(day_hours))])
	wrecktangles = list()
	for cohort, ch, color in zip(cohorts, cohort_hours, colors):
		bp = main_plot.boxplot(ch, positions=x_position, sym='.')
		x_position += 1

		wrect = patches.Rectangle((0, 0), 1, 1, fc=color, label=str(cohort))
		wrecktangles.append(wrect)
		for key in bp.keys():
			if key != 'medians':
				pyplot.setp(bp[key], color=color)

	main_plot.legend(wrecktangles, (wrect.get_label() for wrect in wrecktangles), loc=0)

	main_plot.set_xlim(xmin=-1) # i don't understand why i need this
	main_plot.axvspan(7*(2+len(cohorts))-1, 19*(2+len(cohorts))-1, color='black', alpha=.2, zorder=-100)

	x_labels = ['hr %d' % i for i in range(1,23)]
	main_plot.xaxis.set_major_locator(ticker.LinearLocator(22))
	xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
	pyplot.setp(xtickNames, rotation=45)

def cohort_age_sessiontime(stage):
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	colors = ["orange", 'blue', 'green']
	scatter_markers = ['s', 'D', 'v']

	starts = [0, .9, 1.4]
	ends = [.6, 1.1, 1.6]
	stage_start = starts[stage]
	stage_end = ends[stage]

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot.set_title("Induction Stage %d" % (stage+1))
	main_plot.set_xlabel("age at first intox")
	main_plot.set_ylabel("average session1 time")

	for index, cohort in enumerate(cohorts):
		x = list()
		y = list()
		for monkey in cohort.monkey_set.exclude(mky_age_at_intox=None).exclude(mky_age_at_intox=0):
			age = monkey.mky_age_at_intox / 365.25
			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey, drinking_experiment__dex_type='Induction')
			mtds = mtds.filter(mtd_etoh_g_kg__gte=stage_start).filter(mtd_etoh_g_kg__lte=stage_end)
			avg = mtds.aggregate(Avg('mtd_seconds_to_stageone'))['mtd_seconds_to_stageone__avg']
			avg /= 3600
			x.append(age)
			y.append(avg)
		main_plot.scatter(x, y, label=str(cohort), color=colors[index], marker=scatter_markers[index], s=150)
	main_plot.legend(loc=0, scatterpoints=1)
#	ltext = leg.get_texts()
#	pyplot.setp(ltext, fontsize=12)
#	main_plot.set_xlim(xmin=0)
	main_plot.set_ylim(ymin=0)
	return fig

def cohort_age_vol_hour(phase, hours): # phase = 0-2
	assert 0 <= phase <= 2
	assert 0 < hours < 3
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	cohort_1st_oa_end = {_7a: "2011-08-01", _5:"2009-10-13", _4:"2009-05-24"}
	oa_phases = ['', 'eev_occurred__lte', 'eev_occurred__gt']
	colors = ["orange", 'blue', 'green']
	scatter_markers = ['s', 'D', 'v']
	titles = ["Open Access, 12 months", "Open Access, 1st Six Months", "Open Access, 2nd Six Months"]
	titles = [t+", first %d hours" % hours for t in titles]

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot.set_title(titles[phase])
	main_plot.set_xlabel("Age at first intox")
	main_plot.set_ylabel("Daily Average Etoh Volume in First %d Hour%s" % (hours, '' if hours == 1 else 's'))

	for index, cohort in enumerate(cohorts):
		x = list()
		y = list()
		for monkey in cohort.monkey_set.exclude(mky_age_at_intox=None).exclude(mky_age_at_intox=0):
			age = monkey.mky_age_at_intox / 365.25
			x.append(age)

			eevs = ExperimentEvent.objects.filter(dex_type='Open Access', monkey=monkey).exclude(eev_etoh_volume=None).exclude(eev_etoh_volume=0)
			if phase:
				eevs = eevs.filter(**{oa_phases[phase]: cohort_1st_oa_end[cohort]})
			eevs = eevs.filter(eev_session_time__lt=hours*60*60)
			eev_count = eevs.dates('eev_occurred', 'day').count()*1.
			eev_vol = eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
			value = eev_vol / eev_count
			y.append(value)
		main_plot.scatter(x, y, label=str(cohort), color=colors[index], marker=scatter_markers[index], s=150)
	main_plot.legend(loc=0, scatterpoints=1)
	return fig

#--
def cohort_age_mtd_general(phase, mtd_callable_yvalue_generator): # phase = 0-2
	assert 0 <= phase <= 2
	_7a = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a') # adolescents
	_5 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5') # young adults
	_4 = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4') # adults
	cohorts = [_7a, _5, _4]
	cohort_1st_oa_end = {_7a: "2011-08-01", _5:"2009-10-13", _4:"2009-05-24"}
	oa_phases = ['', 'drinking_experiment__dex_date__lte', 'drinking_experiment__dex_date__gt']
	colors = ["orange", 'blue', 'green']
	scatter_markers = ['s', 'D', 'v']
	titles = ["Open Access, 12 months", "Open Access, 1st Six Months", "Open Access, 2nd Six Months"]

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])
	main_plot.set_title(titles[phase])
	main_plot.set_xlabel("Age at first intox")

	label = ''
	for index, cohort in enumerate(cohorts):
		x = list()
		y = list()
		for monkey in cohort.monkey_set.exclude(mky_age_at_intox=None).exclude(mky_age_at_intox=0):
			age = monkey.mky_age_at_intox / 365.25
			mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment__dex_type='Open Access', monkey=monkey)
			if phase:
				mtds = mtds.filter(**{oa_phases[phase]:cohort_1st_oa_end[cohort]})
			x.append(age)
			value, label = mtd_callable_yvalue_generator(mtds)
			y.append(value)
		main_plot.scatter(x, y, label=str(cohort), color=colors[index], marker=scatter_markers[index], s=150)
	main_plot.set_ylabel(label)
	main_plot.legend(loc=0, scatterpoints=1)
	return fig

def __mtd_call_gkg_etoh(mtds):
	avg = mtds.aggregate(Avg('mtd_etoh_g_kg'))['mtd_etoh_g_kg__avg']
	return avg, "Average daily ethanol intake, g/kg"

def __mtd_call_bec(mtds):
	avg = mtds.aggregate(Avg('bec_record__bec_mg_pct'))['bec_record__bec_mg_pct__avg']
	return avg, "Average BEC value"

def __mtd_call_over_3gkg(mtds):
	count = mtds.filter(mtd_etoh_g_kg__gte=3).count()
	return count, "Days over 3 g/kg"

def __mtd_call_over_4gkg(mtds):
	count = mtds.filter(mtd_etoh_g_kg__gte=4).count()
	return count, "Days over 4 g/kg"

def __mtd_call_max_bout_vol(mtds):
	avg = mtds.aggregate(Avg('mtd_max_bout_vol'))['mtd_max_bout_vol__avg']
	return avg, "Average Maximum Bout Volume"

def __mtd_call_max_bout_vol_pct(mtds):
	avg = mtds.aggregate(Avg('mtd_pct_max_bout_vol_total_etoh'))['mtd_pct_max_bout_vol_total_etoh__avg']
	return avg, "Average Maximum Bout, as % of total intake"
#--

def create_age_graphs():
	import settings
	output_path = settings.STATIC_ROOT
	output_path = os.path.join(output_path, "images/christa/")
	cohort_age_mtd_general_sets = \
	[__mtd_call_gkg_etoh, __mtd_call_bec, __mtd_call_over_3gkg, __mtd_call_over_4gkg, __mtd_call_max_bout_vol, __mtd_call_max_bout_vol_pct]
	for method in cohort_age_mtd_general_sets:
		for phase in range(3):
			fig = cohort_age_mtd_general(phase, method)
			DPI = fig.get_dpi()
			filename = output_path + '%s.Phase%d.png' % (method.__name__, phase)
			fig.savefig(filename, dpi=DPI)
	for stage in range(3):
		fig = cohort_age_sessiontime(stage)
		DPI = fig.get_dpi()
		filename = output_path + '%s.Stage%d.png' % ("cohort_age_sessiontime", stage)
		fig.savefig(filename, dpi=DPI)
	for phase in range(3):
		for hour in range(1,3):
			fig = cohort_age_vol_hour(phase, hour)
			DPI = fig.get_dpi()
			filename = output_path + '%s.Phase%d.Hour%d.png' % ("cohort_age_vol_hour", phase, hour)
			fig.savefig(filename, dpi=DPI)

def create_christa_graphs():
	import settings
	output_path = settings.STATIC_ROOT
	output_path = os.path.join(output_path, "images/christa/")
	for i in range(3):
		volbout_figs = cohorts_daytime_volbouts_bargraph_split(i)
		bouts_figs = cohorts_daytime_bouts_histogram_split(i)
		maxbout_figs = cohorts_maxbouts_histogram(i)
		for fig, cohort in volbout_figs:
			DPI = fig.get_dpi()
			filename = output_path + '%s.%s.Phase%d.png' % ("cohorts_daytime_volbouts_bargraph_split", str(cohort), i)
			fig.savefig(filename, dpi=DPI)
		for fig, cohort in bouts_figs:
			DPI = fig.get_dpi()
			filename = output_path + '%s.%s.Phase%d.png' % ("cohorts_daytime_bouts_histogram_split", str(cohort), i)
			fig.savefig(filename, dpi=DPI)
		for fig, cohort in maxbout_figs:
			DPI = fig.get_dpi()
			filename = output_path + '%s.%s.Phase%d.png' % ("cohorts_maxbouts_histogram", str(cohort), i)
			fig.savefig(filename, dpi=DPI)
	create_age_graphs()




