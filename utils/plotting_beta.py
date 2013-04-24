from django.db.models import Sum
import numpy
from matplotlib import pyplot, gridspec, ticker, cm, patches
from scipy import cluster
import operator
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
			bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
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
				bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
				bout_vols = bouts.values_list('ebt_volume', flat=True)
				bouts_sum = numpy.array(bout_vols).sum()
	#			bout_starts = bout_starts - diff
				y_axis.append(bouts_sum)
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
			bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
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
			bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
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
			bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
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
			bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
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
				bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
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
			becs = MonkeyBEC.objects.Ind().filter(monkey=monkey).order_by('pk')
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
		mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=monkey)
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
		main_plot.set_title("Open Access, greater than %d g per kg Etoh" % gkg)

		monkeys = cohort.monkey_set.filter(mky_drinking=True).values_list('pk', flat=True)
		width = .9

		data = list()
		colors = list()
		for i, mky in enumerate(monkeys):
			mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky, mtd_etoh_g_kg__gte=gkg).count()
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

	becs = MonkeyBEC.objects.Ind().filter(monkey__cohort=cohort)# cohort and induction filter
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
				bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
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
			bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey)
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
				bouts = ExperimentBout.objects.OA().filter(mtd__monkey=monkey, ebt_start_time__gte=start_time, ebt_start_time__lt=start_time+_1_hour)
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
			mtds = MonkeyToDrinkingExperiment.objects.Ind().filter(monkey=monkey)
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

def _cohort_etoh_cumsum_nofood(cohort, subplot, minutes_excluded=5):
	mkys = cohort.monkey_set.filter(mky_drinking=True)
	mky_count = mkys.count()

	subplot.set_title("Induction Cumulative EtOH Intake for %s, excluding drinks less than %d minutes after food" % (str(cohort), minutes_excluded))
	subplot.set_ylabel("Volume EtOH / Monkey Weight, ml/kg")

	cmap = plotting.get_cmap('jet')
	mky_colors = dict()
	mky_ymax = dict()
	for idx, m in enumerate(mkys):
		eevs = ExperimentEvent.objects.Ind().filter(monkey=m).exclude(eev_etoh_volume=None).order_by('eev_occurred')
		eevs = eevs.exclude(eev_pellet_elapsed_time_since_last__gte=minutes_excluded*60)
		if not eevs.count():
			continue
		mky_colors[m] = cmap(idx / (mky_count-1.))
		volumes = numpy.array(eevs.values_list('eev_etoh_volume', flat=True))
		yaxis = numpy.cumsum(volumes)
		mky_ymax[m] = yaxis[-1]
		xaxis = numpy.array(eevs.values_list('eev_occurred', flat=True))
		subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=mky_colors[m], label=str(m.pk))
	pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45 )
	subplot.legend(loc=2)
	if not len(mky_ymax.values()):
		raise Exception("no eevs found")
	return subplot, mky_ymax, mky_colors

def _cohort_etoh_max_bout_cumsum(cohort, subplot):
	mkys = cohort.monkey_set.filter(mky_drinking=True)
	mky_count = mkys.count()

	subplot.set_title("Induction St. 3 Cumulative Max Bout EtOH Intake for %s" % str(cohort))
	subplot.set_ylabel("Volume EtOH / Monkey Weight, ml/kg")

	cmap = plotting.get_cmap('jet')
	mky_colors = dict()
	mky_ymax = dict()
	for idx, m in enumerate(mkys):
		mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m, drinking_experiment__dex_type="Induction").exclude(mtd_max_bout_vol=None).order_by('drinking_experiment__dex_date')
		mtds = mtds.filter(mtd_etoh_g_kg__gte=1.4).filter(mtd_etoh_g_kg__lte=1.6)
		if not mtds.count():
			continue
		mky_colors[m] = cmap(idx / (mky_count-1.))
		volumes = numpy.array(mtds.values_list('mtd_max_bout_vol', flat=True))
		weights = numpy.array(mtds.values_list('mtd_weight', flat=True))
		vw_div = volumes / weights
		yaxis = numpy.cumsum(vw_div)
		mky_ymax[m] = yaxis[-1]
		xaxis = numpy.array(mtds.values_list('drinking_experiment__dex_date', flat=True))
		subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=mky_colors[m], label=str(m.pk))
	pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45 )
	subplot.legend(loc=2)
	if not len(mky_ymax.values()):
		raise Exception("no MTDs found")
	return subplot, mky_ymax, mky_colors

def _cohort_etoh_horibar_ltgkg(cohort, subplot, mky_ymax, mky_colors):
	subplot.set_title("Lifetime EtOH Intake for %s" % str(cohort))
	subplot.set_xlabel("EtOH Intake, g/kg")

	sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

	bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
	bar_widths = list()
	bar_y = list()
	bar_colors = list()
	for mky, ymax in sorted_ymax:
		mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
		etoh_sum = mtds.aggregate(Sum('mtd_etoh_g_kg'))['mtd_etoh_g_kg__sum']
		bar_widths.append(etoh_sum)
		bar_colors.append(mky_colors[mky])
		if len(bar_y):
			highest_bar = bar_y[len(bar_y)-1]+bar_height
		else:
			highest_bar = 0+bar_height
		if ymax > highest_bar:
			bar_y.append(ymax)
		else:
			bar_y.append(highest_bar)
	subplot.barh(bar_y, bar_widths, height=bar_height, color=bar_colors)
	subplot.set_yticks([])
	subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
	pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45 )
	return subplot

def _cohort_etoh_horibar_3gkg(cohort, subplot, mky_ymax, mky_colors):
	subplot.set_title("# days over 3 g/kg")

	sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

	bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
	bar_3widths = list()
	bar_y = list()
	bar_colors = list()
	for mky, ymax in sorted_ymax:
		mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
		bar_3widths.append(mtds.filter(mtd_etoh_g_kg__gt=3).count())
		bar_colors.append(mky_colors[mky])
		if len(bar_y):
			highest_bar = bar_y[len(bar_y)-1]+bar_height
		else:
			highest_bar = 0+bar_height
		if ymax > highest_bar:
			bar_y.append(ymax)
		else:
			bar_y.append(highest_bar)
	subplot.barh(bar_y, bar_3widths, height=bar_height, color=bar_colors)
	subplot.set_yticks([])
	subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
	pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45 )
	return subplot

def _cohort_etoh_horibar_4gkg(cohort, subplot, mky_ymax, mky_colors):
	subplot.set_title("# days over 4 g/kg")
	sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))
	bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
	bar_4widths = list()
	bar_y = list()
	bar_colors = list()
	for mky, ymax in sorted_ymax:
		mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
		bar_4widths.append(mtds.filter(mtd_etoh_g_kg__gt=4).count())
		bar_colors.append(mky_colors[mky])
		if len(bar_y):
			highest_bar = bar_y[len(bar_y)-1]+bar_height
		else:
			highest_bar = 0+bar_height
		if ymax > highest_bar:
			bar_y.append(ymax)
		else:
			bar_y.append(highest_bar)
	subplot.barh(bar_y, bar_4widths, height=bar_height, color=bar_colors)
	subplot.set_yticks([])
	subplot.xaxis.set_major_locator(plotting.MaxNLocator(4, prune='lower'))
	pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45 )
	return subplot

def cohort_etoh_max_bout_cumsum_horibar_3gkg(cohort):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	line_subplot = fig.add_subplot(gs[:,:2])
	try:
		line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
	except:
		return None, False
	bar_subplot = fig.add_subplot(gs[:,2:], sharey=line_subplot)
	bar_subplot = _cohort_etoh_horibar_3gkg(cohort, bar_subplot, mky_ymax, mky_colors)
	return fig, None

def cohort_etoh_max_bout_cumsum_horibar_4gkg(cohort):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	line_subplot = fig.add_subplot(gs[:,:2])
	try:
		line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
	except:
		return None, False
	bar_subplot = fig.add_subplot(gs[:,2:], sharey=line_subplot)
	bar_subplot = _cohort_etoh_horibar_4gkg(cohort, bar_subplot, mky_ymax, mky_colors)
	return fig, None

def cohort_etoh_max_bout_cumsum_horibar_ltgkg(cohort):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	line_subplot = fig.add_subplot(gs[:,:2])
	try:
		line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
	except:
		return None, False
	bar_subplot = fig.add_subplot(gs[:,2:], sharey=line_subplot)
	bar_subplot = _cohort_etoh_horibar_ltgkg(cohort, bar_subplot, mky_ymax, mky_colors)
	return fig, None

def cohort_etoh_ind_cumsum_horibar_34gkg(cohort, minutes_excluded=5):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	line_subplot = fig.add_subplot(gs[:,:2])
	try:
		line_subplot, mky_ymax, mky_colors = _cohort_etoh_cumsum_nofood(cohort, line_subplot, minutes_excluded=minutes_excluded)
	except Exception as e:
		print e.message
		return None, False
	bar_subplot = fig.add_subplot(gs[:,2:], sharey=line_subplot)
	bar_subplot = _cohort_etoh_horibar_4gkg(cohort, bar_subplot, mky_ymax, mky_colors)
	return fig, None


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
			mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=monkey)
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

rhesus_drinkers = dict()
rhesus_drinkers['MD'] = [10082, 10057, 10087, 10088, 10059, 10054, 10086 ,10051, 10049, 10063, 10091, 10060, 10064, 10098, 10065, 10097, 10066, 10067, 10061, 10062]
rhesus_drinkers['HD'] = [10082, 10049, 10064, 10063, 10097, 10091, 10065, 10066, 10067, 10088, 10098, 10061, 10062]
rhesus_drinkers['VHD'] = [10088, 10091, 10066, 10098, 10063, 10061, 10062]

def rhesus_etoh_gkg_histogram():
	cohorts = Cohort.objects.filter(pk__in=[5,6,10])
	monkeys = Monkey.objects.none()
	for coh in cohorts:
		monkeys |= coh.monkey_set.filter(mky_drinking=True)
	mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey__in=monkeys)
	daily_gkgs = mtds.values_list('mtd_etoh_g_kg', flat=True)

	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	subplot = fig.add_subplot(gs[:,:])

	_bins = 150
	linspace = numpy.linspace(0, max(daily_gkgs), _bins) # defines number of bins in histogram
	n, bins, patches = subplot.hist(daily_gkgs, bins=linspace, normed=False, alpha=.5, color='gold')
	bincenters = 0.5*(bins[1:]+bins[:-1])
	newx = numpy.linspace(min(bincenters), max(bincenters), _bins/8) # smooth out the x axis
	newy = plotting.spline(bincenters, n, newx) # smooth out the y axis
	subplot.plot(newx, newy, color='r', linewidth=5) # smoothed line
	subplot.set_ylim(ymin=0)
	subplot.set_title("Rhesus 4/5/7a, g/kg per day")
	subplot.set_ylabel("Day Count")
	subplot.set_xlabel("Day's etoh intake, g/kg")
	return fig, None

def rhesus_etoh_gkg_bargraph(limit_step=1):
	cohorts = Cohort.objects.filter(pk__in=[5,6,10])
	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	subplot = fig.add_subplot(gs[:,:])

	monkeys = Monkey.objects.none()
	for coh in cohorts:
		monkeys |= coh.monkey_set.filter(mky_drinking=True)

	width = .90 / (.95/limit_step)
	limits = numpy.arange(1,9, limit_step)
	gkg_daycounts = numpy.zeros(len(limits))
	for monkey in monkeys:
		mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=monkey)
		if not mtds.count():
			continue
		max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
		min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
		days = float((max_date-min_date).days)
		for index, limit in enumerate(limits):
			_count = mtds.filter(mtd_etoh_g_kg__gt=limit).count()
			gkg_daycounts[index] += _count / days

	gkg_daycounts = list(gkg_daycounts)
	subplot.bar(limits, gkg_daycounts, width=width, color='navy')
	xmax = max(gkg_daycounts)*1.005
	subplot.set_ylim(ymin=0, ymax=xmax)
	subplot.set_title("Rhesus 4/5/7a, distribution of intakes exceeding g/kg minimums")
	subplot.set_ylabel("Summation of each monkey's percentage of days where EtoH intake exceeded x-value")
	subplot.set_xlabel("Etoh intake, g/kg")
	return fig, None

def rhesus_etoh_gkg_forced_histogram():
	cohorts = Cohort.objects.filter(pk__in=[5,6,9,10])
	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
	subplot = fig.add_subplot(gs[:,:])

	monkeys = Monkey.objects.none()
	for coh in cohorts:
		monkeys |= coh.monkey_set.filter(mky_drinking=True)

	increment = .1
	limits = numpy.arange(0, 8, increment)
	gkg_daycounts = numpy.zeros(len(limits))
	for monkey in monkeys:
		mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=monkey)
		if not mtds.count():
			continue
		max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
		min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
		days = float((max_date-min_date).days)
		for index, limit in enumerate(limits):
			if not limit:
				continue
			_count = mtds.filter(mtd_etoh_g_kg__gt=limits[index-1]).filter(mtd_etoh_g_kg__lte=limits[index]).count()
			gkg_daycounts[index] += _count / days

	gkg_daycounts = list(gkg_daycounts)
	subplot.bar(limits, gkg_daycounts, width=increment, color='gold')

	newx = numpy.linspace(min(limits), max(limits), 60) # smooth out the x axis
	newy = plotting.spline(limits, gkg_daycounts, newx) # smooth out the y axis
	subplot.plot(newx, newy, color='r', linewidth=5) # smoothed line

	xmax = max(gkg_daycounts)*1.005
	subplot.set_ylim(ymin=0, ymax=xmax)
	subplot.set_title("Rhesus 4/5/7a/7b, distribution of intakes")
	subplot.set_ylabel("Summation of each monkey's percentage of days where EtoH intake equaled x-value")
	subplot.set_xlabel("Etoh intake, g/kg")
	return fig, None

def rhesus_etoh_gkg_monkeybargraph():
	fig = pyplot.figure(figsize=plotting.HISTOGRAM_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	gs = gridspec.GridSpec(3, 3)
	gs.update(left=0.04, right=0.98, wspace=.08, hspace=0)

	monkeys = Monkey.objects.Drinkers().filter(cohort__in=[5,6,9,10]).values_list('pk', flat=True).distinct()
	limits = range(2,5,1)
	for index, limit in enumerate(limits):
		keys = list()
		values = list()
		for monkey in monkeys:
			mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=monkey)
			if not mtds.count():
				continue
			max_date = mtds.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
			min_date = mtds.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
			days = float((max_date-min_date).days)
			_count = mtds.filter(mtd_etoh_g_kg__gt=limit).count()
			values.append(_count / days)
			keys.append(str(monkey))

		subplot = fig.add_subplot(gs[:,index])
		sorted_x = sorted(zip(keys, values), key=operator.itemgetter(1))
		keys = list()
		values = list()
		for k, v in sorted_x:
			keys.append(k)
			values.append(v)
	#	subplot.bar(limits, gkg_daycounts, #width=.95, color='navy')
		xaxis = range(len(values))
		subplot.bar(xaxis, values, width=1, color='navy', edgecolor=None)
		subplot.set_xlim(xmax=len(monkeys))
		subplot.set_xticks(range(len(monkeys))) # this will force a tick for every monkey.  without this, labels become useless
		xtickNames = pyplot.setp(subplot, xticklabels=keys)
		pyplot.setp(xtickNames, rotation=45, fontsize=8)
		subplot.set_title("%% of days with intake over %d g/kg" % limit)
	return fig, None

def _rhesus_minute_volumes(subplot, minutes, monkey_category, volume_summation, vs_kwargs=None):
	from utils import plotting
	assert monkey_category in rhesus_drinkers.keys()
	light_data, light_count = volume_summation(rhesus_drinkers[monkey_category], minutes, exclude=True, **vs_kwargs)
	heavy_data, heavy_count = volume_summation(rhesus_drinkers[monkey_category], minutes, exclude=False, **vs_kwargs)
	assert light_data.keys() == heavy_data.keys()
	for x in light_data.keys():
		# lower, light drinkers
		_ld = light_data[x]/float(light_count)
		subplot.bar(x, _ld, width=.5, color='navy', edgecolor='none')
		# higher, heavy drinkers
		subplot.bar(x+.5, heavy_data[x]/float(heavy_count), width=.5, color='slateblue', edgecolor='none')
#	patches.append(Rectangle((0,0),1,1, color=value))
	subplot.legend([plotting.Rectangle((0,0),1,1, color='slate_blue'), plotting.Rectangle((0,0),1,1, color='navy')], [monkey_category ,"Not %s" % monkey_category], title="Monkey Category", loc='upper left')
	subplot.set_xlim(xmax=max(light_data.keys()))
	subplot.set_title("Average intake by minute after pellet")
	subplot.set_ylabel("Average volume, ml per monkey")
	subplot.set_xlabel("Minutes since last pellet")
	# rotate the xaxis labels
	xticks = [x+.5 for x in light_data.keys()]
	xtick_labels = ["%d" % x for x in light_data.keys() if x%5 == 0]
	subplot.set_xticks(xticks)
	subplot.set_xticklabels(xtick_labels)
	return subplot

def rhesus_oa_discrete_minute_volumes(minutes, monkey_category):
	def _oa_eev_volume_summation(monkey_set=(), minutes=20, exclude=False):
		data = dict()
		if exclude:
			eevs = ExperimentEvent.objects.OA().filter(monkey__cohort__in=[5,6,9,10]).exclude(monkey__in=monkey_set)
		else:
			eevs = ExperimentEvent.objects.OA().filter(monkey__in=monkey_set)
		for i in range(0, minutes):
			_eevs = eevs.filter(eev_pellet_elapsed_time_since_last__gte=i*60).filter(eev_pellet_elapsed_time_since_last__lt=(i+1)*60)
			data[i] = _eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
		return data, eevs.values_list('monkey', flat=True).distinct().count()

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
	subplot = fig.add_subplot(main_gs[:,:])
	subplot = _rhesus_minute_volumes(subplot, minutes, monkey_category, _oa_eev_volume_summation)
	return fig

def rhesus_thirds_oa_discrete_minute_volumes(minutes, monkey_category):
	def _thirds_oa_eev_volume_summation(monkey_set=(), minutes=20, exclude=False, offset=0):
		cohort_starts = {5: datetime(2008, 10, 20), }#6:datetime(2009, 4, 13), 9:datetime(2011, 7, 12), 10:datetime(2011,01,03)}
		monkeys = set()
		data = dict()
		for i in range(0, minutes):
			data[i] = 0
		for coh, start_date in cohort_starts.items():
			if exclude:
				eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__cohort=coh).exclude(monkey__in=monkey_set)
			else:
				eevs = ExperimentEvent.objects.OA().exclude_exceptions().filter(monkey__cohort=coh).filter(monkey__in=monkey_set)

			monkeys.update(eevs.values_list('monkey', flat=True).distinct())
			start = start_date + timedelta(days=offset)
			end = start + timedelta(days=120)
			for i in range(0, minutes):
				_eevs = eevs.filter(eev_occurred__gte=start).filter(eev_occurred__lt=end)
				_eevs = _eevs.filter(eev_pellet_elapsed_time_since_last__gte=i*60).filter(eev_pellet_elapsed_time_since_last__lt=(i+1)*60)
				data[i] += _eevs.aggregate(Sum('eev_etoh_volume'))['eev_etoh_volume__sum']
		return data, len(monkeys)

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 3)
	main_gs.update(left=0.04, right=0.98, wspace=.08, hspace=0)
	for index, offset in enumerate([0, 120, 240]):
		subplot = fig.add_subplot(main_gs[:,index])
		subplot = _rhesus_minute_volumes(subplot, minutes, monkey_category, _thirds_oa_eev_volume_summation, vs_kwargs={'offset':offset})
	return fig

#---
#plot
def confederate_boxplots(confederates, bout_column):
	from utils import plotting
	confeds = list()
	for c in confederates:
		if not isinstance(c, Monkey):
			try:
				mky = Monkey.objects.get(pk=c)
			except Monkey.DoesNotExist:
				try:
					mky = Monkey.objects.get(mky_real_id=c)
				except Monkey.DoesNotExist:
					print("That's not a valid monkey:  %s" % str(c))
					return False, False
		else:
			mky = c
		confeds.append(mky)
	cohort = mky.cohort
	monkeys = cohort.monkey_set.exclude(mky_drinking=False).exclude(pk__in=[c.pk for c in confeds])

	fig = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
	main_gs = gridspec.GridSpec(3, 40)
	main_gs.update(left=0.12, right=.98, wspace=0, hspace=0)
	main_plot = fig.add_subplot(main_gs[:,:])

	cohort_data = list()
	confed_data = list()
	monkey_data = list()
	minutes = numpy.array([0,1,5,10,15,20])
	min_oa_date = MonkeyToDrinkingExperiment.objects.OA().aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
	cbts = CohortBout.objects.filter(cohort=cohort).filter(dex_date__gte=min_oa_date)
	for _min in minutes:
		_cbts = cbts.filter(cbt_pellet_elapsed_time_since_last__gte=_min*60)
		cohort_bouts = _cbts.values_list('ebt_set', flat=True).distinct()

		confed_bouts = _cbts.filter(ebt_set__mtd__monkey__in=confeds).values_list('ebt_set', flat=True).distinct()
		print "confed_count = %d" % confed_bouts.count()
		monkey_bouts = _cbts.filter(ebt_set__mtd__monkey__in=monkeys).values_list('ebt_set', flat=True).distinct()
		print "monkey_count = %d" % monkey_bouts.count()
		cohort_data.append(ExperimentBout.objects.filter(pk__in=cohort_bouts).values_list(bout_column, flat=True))
		confed_data.append(ExperimentBout.objects.filter(pk__in=confed_bouts).values_list(bout_column, flat=True))
		monkey_data.append(ExperimentBout.objects.filter(pk__in=monkey_bouts).values_list(bout_column, flat=True))

	offset = 4
	cohort_pos = numpy.arange(offset, offset*len(minutes)+offset, offset)
	monkey_pos = cohort_pos + 1
	confed_pos = monkey_pos + 1

	bp = main_plot.boxplot(confed_data, positions=cohort_pos)
	pyplot.setp(bp['boxes'], linewidth=1, color='g')
	pyplot.setp(bp['whiskers'], linewidth=1, color='g')
	pyplot.setp(bp['fliers'], color='g', marker='+')

	bp = main_plot.boxplot(monkey_data, positions=monkey_pos)

	bp = main_plot.boxplot(confed_data, positions=confed_pos)
	pyplot.setp(bp['boxes'], linewidth=1, color='r')
	pyplot.setp(bp['whiskers'], linewidth=1, color='r')
	pyplot.setp(bp['fliers'], color='red', marker='+')

	main_plot.set_yscale('log')
	main_plot.set_xlim(xmin=offset-.5)
	ymin, ymax = main_plot.get_ylim()
	y_values = list()
	for x in numpy.arange(ymax):
		if x*10**x <= ymax:
			y_values.append(x*10**x)
		else:
			break
	y_values.append(ymax)
	y_values = numpy.array(y_values)
	main_plot.set_title("%s, Open Access Bout vs Time since last pellet" % str(cohort) )
	main_plot.set_xticks(monkey_pos)
	main_plot.set_xticklabels(minutes*60)
	main_plot.set_yticklabels(y_values)
	main_plot.set_xlabel("Minimum Seconds Since Pellet")
	_label = "Bout Length" if bout_column == 'ebt_length' else ''
	_label = "Bout Volume" if not _label and bout_column == 'ebt_volume' else ''
	main_plot.set_ylabel("%s, in seconds" % _label)
	return fig
#data
def return_confeds(pk):
	# generated using apriori.confederate_groups(pk, 15, 0)
	if pk == 5:
		return {0.050000000000000003: [(frozenset([10059]),
		   frozenset([10048]),
		   0.270509977827051),
		  (frozenset([10048]), frozenset([10059]), 0.47749510763209396),
		  (frozenset([10054]), frozenset([10056]), 0.30555555555555552),
		  (frozenset([10056]), frozenset([10054]), 0.41284403669724767),
		  (frozenset([10055]), frozenset([10058]), 0.56225425950196595),
		  (frozenset([10058]), frozenset([10055]), 0.156170367673826),
		  (frozenset([10054]), frozenset([10059]), 0.44074074074074071),
		  (frozenset([10059]), frozenset([10054]), 0.39578713968957874),
		  (frozenset([10051]), frozenset([10048]), 0.16139130434782609),
		  (frozenset([10048]), frozenset([10051]), 0.45401174168297459),
		  (frozenset([10051]), frozenset([10049]), 0.15652173913043479),
		  (frozenset([10049]), frozenset([10051]), 0.29296875),
		  (frozenset([10059]), frozenset([10051]), 0.42405764966740578),
		  (frozenset([10051]), frozenset([10059]), 0.26608695652173914),
		  (frozenset([10051]), frozenset([10056]), 0.20034782608695653),
		  (frozenset([10056]), frozenset([10051]), 0.48040033361134282),
		  (frozenset([10058]), frozenset([10056]), 0.20203858755005458),
		  (frozenset([10056]), frozenset([10058]), 0.46288573811509592),
		  (frozenset([10059]), frozenset([10058]), 0.46286031042128606),
		  (frozenset([10058]), frozenset([10059]), 0.30396796505278484),
		  (frozenset([10054]), frozenset([10049]), 0.25308641975308643),
		  (frozenset([10049]), frozenset([10054]), 0.26692708333333331),
		  (frozenset([10051]), frozenset([10057]), 0.16139130434782609),
		  (frozenset([10057]), frozenset([10051]), 0.45224171539961011),
		  (frozenset([10059]), frozenset([10056]), 0.2754988913525499),
		  (frozenset([10056]), frozenset([10059]), 0.41451209341117601),
		  (frozenset([10058]), frozenset([10048]), 0.17946851110302148),
		  (frozenset([10048]), frozenset([10058]), 0.48238747553816053),
		  (frozenset([10051]), frozenset([10058]), 0.3036521739130435),
		  (frozenset([10058]), frozenset([10051]), 0.31780123771386964),
		  (frozenset([10059]), frozenset([10057]), 0.28880266075388022),
		  (frozenset([10057]), frozenset([10059]), 0.50779727095516558),
		  (frozenset([10058]), frozenset([10049]), 0.17582817619220967),
		  (frozenset([10049]), frozenset([10058]), 0.314453125),
		  (frozenset([10054]), frozenset([10058]), 0.43209876543209874),
		  (frozenset([10058]), frozenset([10054]), 0.25482344375682559),
		  (frozenset([10054]), frozenset([10048]), 0.27592592592592596),
		  (frozenset([10048]), frozenset([10054]), 0.4373776908023484),
		  (frozenset([10058]), frozenset([10057]), 0.20021842009464871),
		  (frozenset([10057]), frozenset([10058]), 0.53606237816764135),
		  (frozenset([10054]), frozenset([10057]), 0.2839506172839506),
		  (frozenset([10057]), frozenset([10054]), 0.44834307992202727),
		  (frozenset([10055]), frozenset([10054]), 0.54914809960681521),
		  (frozenset([10054]), frozenset([10055]), 0.25864197530864197),
		  (frozenset([10055]), frozenset([10059]), 0.51769331585845346),
		  (frozenset([10059]), frozenset([10055]), 0.21895787139689579),
		  (frozenset([10054]), frozenset([10051]), 0.42592592592592593),
		  (frozenset([10051]), frozenset([10054]), 0.23999999999999999),
		  (frozenset([10055]), frozenset([10051]), 0.57536041939711668),
		  (frozenset([10051]), frozenset([10055]), 0.15269565217391304),
		  (frozenset([10054]), frozenset([10058, 10051]), 0.27654320987654318),
		  (frozenset([10051]), frozenset([10058, 10054]), 0.15582608695652173),
		  (frozenset([10058]), frozenset([10051, 10054]), 0.1630870040043684),
		  (frozenset([10051]), frozenset([10058, 10059]), 0.16869565217391302),
		  (frozenset([10059]), frozenset([10058, 10051]), 0.26884700665188471),
		  (frozenset([10058]), frozenset([10051, 10059]), 0.17655624317437202),
		  (frozenset([10054]), frozenset([10051, 10059]), 0.27654320987654318),
		  (frozenset([10051]), frozenset([10059, 10054]), 0.15582608695652173),
		  (frozenset([10059]), frozenset([10051, 10054]), 0.24833702882483372),
		  (frozenset([10054]), frozenset([10058, 10059]), 0.28641975308641976),
		  (frozenset([10059]), frozenset([10058, 10054]), 0.25720620842572062),
		  (frozenset([10058]), frozenset([10059, 10054]), 0.16891153986166726)],
		 0.10000000000000001: [(frozenset([10059]),
		   frozenset([10058]),
		   0.46286031042128606),
		  (frozenset([10058]), frozenset([10059]), 0.30396796505278484),
		  (frozenset([10051]), frozenset([10058]), 0.3036521739130435),
		  (frozenset([10058]), frozenset([10051]), 0.31780123771386964)],
		 }
	if pk == 6:
		return {0.050000000000000003: [(frozenset([10065]),
		   frozenset([10064]),
		   0.36108048511576629),
		  (frozenset([10064]), frozenset([10065]), 0.5194290245836638),
		  (frozenset([10062]), frozenset([10060]), 0.1737789203084833),
		  (frozenset([10060]), frozenset([10062]), 0.75446428571428581),
		  (frozenset([10062]), frozenset([10067]), 0.2442159383033419),
		  (frozenset([10067]), frozenset([10062]), 0.60509554140127386),
		  (frozenset([10060]), frozenset([10064]), 0.5078125),
		  (frozenset([10064]), frozenset([10060]), 0.36082474226804123),
		  (frozenset([10060]), frozenset([10065]), 0.48102678571428575),
		  (frozenset([10065]), frozenset([10060]), 0.23759647188533628),
		  (frozenset([10061]), frozenset([10065]), 0.41365461847389562),
		  (frozenset([10065]), frozenset([10061]), 0.28390297684674753),
		  (frozenset([10067]), frozenset([10064]), 0.39363057324840767),
		  (frozenset([10064]), frozenset([10067]), 0.49008723235527363),
		  (frozenset([10062]), frozenset([10061]), 0.17403598971722364),
		  (frozenset([10061]), frozenset([10062]), 0.54377510040160637),
		  (frozenset([10060]), frozenset([10067]), 0.5301339285714286),
		  (frozenset([10067]), frozenset([10060]), 0.30254777070063693),
		  (frozenset([10066]), frozenset([10064]), 0.48141432456935629),
		  (frozenset([10064]), frozenset([10066]), 0.4210943695479778),
		  (frozenset([10067]), frozenset([10066]), 0.33885350318471336),
		  (frozenset([10066]), frozenset([10067]), 0.48232094288304622),
		  (frozenset([10061]), frozenset([10060]), 0.32048192771084338),
		  (frozenset([10060]), frozenset([10061]), 0.44531250000000006),
		  (frozenset([10063]), frozenset([10065]), 0.33314253005151689),
		  (frozenset([10065]), frozenset([10063]), 0.32083792723263505),
		  (frozenset([10063]), frozenset([10060]), 0.21637092157985119),
		  (frozenset([10060]), frozenset([10063]), 0.42187500000000006),
		  (frozenset([10061]), frozenset([10066]), 0.34779116465863452),
		  (frozenset([10066]), frozenset([10061]), 0.39256572982774252),
		  (frozenset([10063]), frozenset([10062]), 0.44361763022323986),
		  (frozenset([10062]), frozenset([10063]), 0.19922879177377892),
		  (frozenset([10061]), frozenset([10067]), 0.45220883534136547),
		  (frozenset([10067]), frozenset([10061]), 0.35859872611464971),
		  (frozenset([10061]), frozenset([10064]), 0.40562248995983941),
		  (frozenset([10064]), frozenset([10061]), 0.40047581284694689),
		  (frozenset([10062]), frozenset([10064]), 0.22210796915167097),
		  (frozenset([10064]), frozenset([10062]), 0.6851704996034893),
		  (frozenset([10063]), frozenset([10067]), 0.31825987406983403),
		  (frozenset([10067]), frozenset([10063]), 0.35414012738853506),
		  (frozenset([10066]), frozenset([10065]), 0.50407978241160478),
		  (frozenset([10065]), frozenset([10066]), 0.30650496141124589),
		  (frozenset([10067]), frozenset([10065]), 0.4229299363057325),
		  (frozenset([10065]), frozenset([10067]), 0.36604189636163181),
		  (frozenset([10062]), frozenset([10066]), 0.19614395886889463),
		  (frozenset([10066]), frozenset([10062]), 0.69174977334542165),
		  (frozenset([10063]), frozenset([10064]), 0.26788780767029197),
		  (frozenset([10064]), frozenset([10063]), 0.37113402061855671),
		  (frozenset([10062]), frozenset([10065]), 0.26452442159383033),
		  (frozenset([10065]), frozenset([10062]), 0.56725468577728777),
		  (frozenset([10060]), frozenset([10066]), 0.46093750000000006),
		  (frozenset([10066]), frozenset([10060]), 0.3744333635539438),
		  (frozenset([10063]), frozenset([10066]), 0.2604464796794505),
		  (frozenset([10066]), frozenset([10063]), 0.41251133272892115),
		  (frozenset([10063]), frozenset([10061]), 0.24041213508872356),
		  (frozenset([10061]), frozenset([10063]), 0.33734939759036148),
		  (frozenset([10063]), frozenset([10067, 10062]), 0.25815684029765312),
		  (frozenset([10062]), frozenset([10067, 10063]), 0.11593830334190232),
		  (frozenset([10067]), frozenset([10062, 10063]), 0.28726114649681528),
		  (frozenset([10062]), frozenset([10067, 10060]), 0.10668380462724937),
		  (frozenset([10060]), frozenset([10067, 10062]), 0.4631696428571429),
		  (frozenset([10067]), frozenset([10060, 10062]), 0.2643312101910828),
		  (frozenset([10067]), frozenset([10065, 10066]), 0.24267515923566879),
		  (frozenset([10066]), frozenset([10065, 10067]), 0.34542157751586583),
		  (frozenset([10065]), frozenset([10066, 10067]), 0.21003307607497243),
		  (frozenset([10062]), frozenset([10065, 10060]), 0.097429305912596409),
		  (frozenset([10060]), frozenset([10065, 10062]), 0.42299107142857151),
		  (frozenset([10065]), frozenset([10060, 10062]), 0.20893054024255789),
		  (frozenset([10062]), frozenset([10065, 10066]), 0.12544987146529563),
		  (frozenset([10066]), frozenset([10065, 10062]), 0.44242973708068906),
		  (frozenset([10065]), frozenset([10066, 10062]), 0.26901874310915108),
		  (frozenset([10062]), frozenset([10064, 10067]), 0.13624678663239076),
		  (frozenset([10067]), frozenset([10064, 10062]), 0.33757961783439494),
		  (frozenset([10064]), frozenset([10067, 10062]), 0.42030134813639969),
		  (frozenset([10062]), frozenset([10065, 10061]), 0.11465295629820052),
		  (frozenset([10061]), frozenset([10065, 10062]), 0.35823293172690762),
		  (frozenset([10065]), frozenset([10061, 10062]), 0.24586549062844543),
		  (frozenset([10062]), frozenset([10065, 10067]), 0.14730077120822624),
		  (frozenset([10067]), frozenset([10065, 10062]), 0.36496815286624207),
		  (frozenset([10065]), frozenset([10067, 10062]), 0.31587651598676958),
		  (frozenset([10063]), frozenset([10066, 10062]), 0.22095020034344592),
		  (frozenset([10062]), frozenset([10066, 10063]), 0.099228791773778927),
		  (frozenset([10066]), frozenset([10062, 10063]), 0.34995466908431555),
		  (frozenset([10061]), frozenset([10064, 10065]), 0.28674698795180725),
		  (frozenset([10065]), frozenset([10064, 10061]), 0.19680264608599779),
		  (frozenset([10064]), frozenset([10065, 10061]), 0.28310864393338619),
		  (frozenset([10062]), frozenset([10064, 10065]), 0.14061696658097689),
		  (frozenset([10065]), frozenset([10064, 10062]), 0.30154355016538043),
		  (frozenset([10064]), frozenset([10065, 10062]), 0.43378271213322761),
		  (frozenset([10063]), frozenset([10065, 10067]), 0.19862621637092159),
		  (frozenset([10067]), frozenset([10065, 10063]), 0.22101910828025478),
		  (frozenset([10065]), frozenset([10067, 10063]), 0.19128996692392503),
		  (frozenset([10062]), frozenset([10066, 10061]), 0.09640102827763497),
		  (frozenset([10061]), frozenset([10066, 10062]), 0.30120481927710846),
		  (frozenset([10066]), frozenset([10061, 10062]), 0.33998186763372623),
		  (frozenset([10061]), frozenset([10065, 10067]), 0.29477911646586347),
		  (frozenset([10067]), frozenset([10065, 10061]), 0.23375796178343949),
		  (frozenset([10065]), frozenset([10067, 10061]), 0.20231532524807055),
		  (frozenset([10062]), frozenset([10067, 10061]), 0.11696658097686376),
		  (frozenset([10061]), frozenset([10067, 10062]), 0.36546184738955823),
		  (frozenset([10067]), frozenset([10061, 10062]), 0.28980891719745222),
		  (frozenset([10062]), frozenset([10064, 10061]), 0.10874035989717223),
		  (frozenset([10061]), frozenset([10064, 10062]), 0.33975903614457831),
		  (frozenset([10064]), frozenset([10061, 10062]), 0.33544805709754161),
		  (frozenset([10062]), frozenset([10060, 10061]), 0.087917737789203088),
		  (frozenset([10061]), frozenset([10060, 10062]), 0.27469879518072293),
		  (frozenset([10060]), frozenset([10061, 10062]), 0.3816964285714286),
		  (frozenset([10061]), frozenset([10064, 10067]), 0.29718875502008035),
		  (frozenset([10067]), frozenset([10064, 10061]), 0.23566878980891723),
		  (frozenset([10064]), frozenset([10067, 10061]), 0.29341792228390168),
		  (frozenset([10067]), frozenset([10064, 10066]), 0.22993630573248408),
		  (frozenset([10066]), frozenset([10064, 10067]), 0.32728921124206711),
		  (frozenset([10064]), frozenset([10066, 10067]), 0.28628072957969863),
		  (frozenset([10062]), frozenset([10064, 10066]), 0.11696658097686376),
		  (frozenset([10066]), frozenset([10064, 10062]), 0.41251133272892115),
		  (frozenset([10064]), frozenset([10066, 10062]), 0.36082474226804123),
		  (frozenset([10062]), frozenset([10066, 10067]), 0.12262210796915168),
		  (frozenset([10067]), frozenset([10066, 10062]), 0.30382165605095546),
		  (frozenset([10066]), frozenset([10067, 10062]), 0.43245693563009974),
		  (frozenset([10063]), frozenset([10064, 10062]), 0.22839152833428736),
		  (frozenset([10062]), frozenset([10064, 10063]), 0.1025706940874036),
		  (frozenset([10064]), frozenset([10062, 10063]), 0.31641554321966692),
		  (frozenset([10067]), frozenset([10064, 10065]), 0.26687898089171974),
		  (frozenset([10065]), frozenset([10064, 10067]), 0.23098125689084897),
		  (frozenset([10064]), frozenset([10065, 10067]), 0.33227597145122917),
		  (frozenset([10062]), frozenset([10064, 10060]), 0.1012853470437018),
		  (frozenset([10060]), frozenset([10064, 10062]), 0.4397321428571429),
		  (frozenset([10064]), frozenset([10060, 10062]), 0.31245043616177637),
		  (frozenset([10063]), frozenset([10065, 10062]), 0.26445334859759589),
		  (frozenset([10062]), frozenset([10065, 10063]), 0.11876606683804627),
		  (frozenset([10065]), frozenset([10062, 10063]), 0.25468577728776182),
		  (frozenset([10066]), frozenset([10064, 10065]), 0.3445149592021759),
		  (frozenset([10065]), frozenset([10064, 10066]), 0.20948180815876516),
		  (frozenset([10064]), frozenset([10065, 10066]), 0.30134813639968278),
		  (frozenset([10062]), frozenset([10066, 10060]), 0.093059125964010281),
		  (frozenset([10060]), frozenset([10066, 10062]), 0.40401785714285715),
		  (frozenset([10066]), frozenset([10060, 10062]), 0.32819582955575699),
		  (frozenset([10066, 10062]), frozenset([10064, 10065]), 0.45478374836173002),
		  (frozenset([10065, 10062]), frozenset([10064, 10066]), 0.33722060252672498),
		  (frozenset([10065, 10066]), frozenset([10064, 10062]), 0.62410071942446044),
		  (frozenset([10064, 10062]), frozenset([10065, 10066]), 0.40162037037037041),
		  (frozenset([10064, 10066]), frozenset([10065, 10062]), 0.65348399246704336),
		  (frozenset([10064, 10065]), frozenset([10066, 10062]), 0.52977099236641223),
		  (frozenset([10062]), frozenset([10064, 10065, 10066]), 0.089203084832904886),
		  (frozenset([10066]), frozenset([10064, 10065, 10062]), 0.31459655485040799),
		  (frozenset([10065]), frozenset([10064, 10066, 10062]), 0.19128996692392503),
		  (frozenset([10064]), frozenset([10065, 10066, 10062]), 0.2751784298176051),
		  (frozenset([10067, 10062]), frozenset([10065, 10066]), 0.3747368421052632),
		  (frozenset([10066, 10062]), frozenset([10065, 10067]), 0.46657929226736566),
		  (frozenset([10066, 10067]), frozenset([10065, 10062]), 0.66917293233082709),
		  (frozenset([10065, 10062]), frozenset([10066, 10067]), 0.34596695821185619),
		  (frozenset([10065, 10067]), frozenset([10066, 10062]), 0.53614457831325302),
		  (frozenset([10065, 10066]), frozenset([10067, 10062]), 0.64028776978417268),
		  (frozenset([10062]), frozenset([10065, 10066, 10067]), 0.091516709511568137),
		  (frozenset([10067]), frozenset([10065, 10066, 10062]), 0.2267515923566879),
		  (frozenset([10066]), frozenset([10065, 10067, 10062]), 0.32275611967361745),
		  (frozenset([10065]), frozenset([10066, 10067, 10062]), 0.19625137816979052),
		  (frozenset([10067, 10062]), frozenset([10064, 10065]), 0.40947368421052632),
		  (frozenset([10065, 10062]), frozenset([10064, 10067]), 0.37803692905733727),
		  (frozenset([10065, 10067]), frozenset([10064, 10062]), 0.58584337349397586),
		  (frozenset([10064, 10062]), frozenset([10065, 10067]), 0.45023148148148151),
		  (frozenset([10064, 10067]), frozenset([10065, 10062]), 0.62944983818770228),
		  (frozenset([10064, 10065]), frozenset([10067, 10062]), 0.5938931297709924),
		  (frozenset([10062]), frozenset([10064, 10065, 10067]), 0.10000000000000001),
		  (frozenset([10067]), frozenset([10064, 10065, 10062]), 0.2477707006369427),
		  (frozenset([10065]), frozenset([10064, 10067, 10062]), 0.21444321940463065),
		  (frozenset([10064]), frozenset([10065, 10067, 10062]), 0.30848532910388582)],
		 0.10000000000000001: [(frozenset([10062]),
		   frozenset([10067]),
		   0.2442159383033419),
		  (frozenset([10067]), frozenset([10062]), 0.60509554140127386),
		  (frozenset([10063]), frozenset([10062]), 0.44361763022323986),
		  (frozenset([10062]), frozenset([10063]), 0.19922879177377892),
		  (frozenset([10062]), frozenset([10064]), 0.22210796915167097),
		  (frozenset([10064]), frozenset([10062]), 0.6851704996034893),
		  (frozenset([10062]), frozenset([10066]), 0.19614395886889463),
		  (frozenset([10066]), frozenset([10062]), 0.69174977334542165),
		  (frozenset([10062]), frozenset([10065]), 0.26452442159383033),
		  (frozenset([10065]), frozenset([10062]), 0.56725468577728777)],
		 0.15000000000000002: [(frozenset([10062]),
		   frozenset([10065]),
		   0.26452442159383033),
		  (frozenset([10065]), frozenset([10062]), 0.56725468577728777)],
		 }
	if pk == 10:
		return {0.050000000000000003: [(frozenset([10097]), frozenset([10088]), 0.34632034632034636),
									   (frozenset([10088]), frozenset([10097]), 0.53511705685618727),
									   (frozenset([10098]), frozenset([10097]), 0.26028806584362135),
									   (frozenset([10097]), frozenset([10098]), 0.54761904761904767),
									   (frozenset([10091]), frozenset([10089]), 0.29068825910931173),
									   (frozenset([10089]), frozenset([10091]), 0.5056338028169014),
									   (frozenset([10087]), frozenset([10097]), 0.28926905132192848),
									   (frozenset([10097]), frozenset([10087]), 0.26839826839826841),
									   (frozenset([10091]), frozenset([10088]), 0.39838056680161943),
									   (frozenset([10088]), frozenset([10091]), 0.54849498327759194),
									   (frozenset([10090]), frozenset([10089]), 0.28370221327967809),
									   (frozenset([10089]), frozenset([10090]), 0.39718309859154932),
									   (frozenset([10090]), frozenset([10088]), 0.41348088531187122),
									   (frozenset([10088]), frozenset([10090]), 0.45819397993311034),
									   (frozenset([10091]), frozenset([10090]), 0.42105263157894735),
									   (frozenset([10090]), frozenset([10091]), 0.52313883299798791),
									   (frozenset([10089]), frozenset([10088]), 0.41126760563380282),
									   (frozenset([10088]), frozenset([10089]), 0.32552954292084724),
									   (frozenset([10087]), frozenset([10091]), 0.25583203732503884),
									   (frozenset([10091]), frozenset([10087]), 0.26639676113360322),
									   (frozenset([10097]), frozenset([10089]), 0.24891774891774895),
									   (frozenset([10089]), frozenset([10097]), 0.4859154929577465),
									   (frozenset([10087]), frozenset([10088]), 0.21461897356143078),
									   (frozenset([10088]), frozenset([10087]), 0.30769230769230765),
									   (frozenset([10087]), frozenset([10098]), 0.36469673405909797),
									   (frozenset([10098]), frozenset([10087]), 0.16083676268861452),
									   (frozenset([10087]), frozenset([10090]), 0.22472783825816486),
									   (frozenset([10090]), frozenset([10087]), 0.29074446680080485),
									   (frozenset([10090]), frozenset([10098]), 0.59959758551307851),
									   (frozenset([10098]), frozenset([10090]), 0.20438957475994513),
									   (frozenset([10092]), frozenset([10097]), 0.64733178654292345),
									   (frozenset([10097]), frozenset([10092]), 0.20129870129870134),
									   (frozenset([10090]), frozenset([10097]), 0.48692152917505033),
									   (frozenset([10097]), frozenset([10090]), 0.34920634920634924),
									   (frozenset([10098]), frozenset([10088]), 0.19341563786008231),
									   (frozenset([10088]), frozenset([10098]), 0.62876254180602009),
									   (frozenset([10091]), frozenset([10098]), 0.59028340080971653),
									   (frozenset([10098]), frozenset([10091]), 0.25),
									   (frozenset([10098]), frozenset([10089]), 0.14574759945130317),
									   (frozenset([10089]), frozenset([10098]), 0.59859154929577463),
									   (frozenset([10091]), frozenset([10097]), 0.48825910931174088),
									   (frozenset([10097]), frozenset([10091]), 0.4350649350649351),
									   (frozenset([10092]), frozenset([10098]), 0.69605568445475641),
									   (frozenset([10098]), frozenset([10092]), 0.102880658436214),
									   (frozenset([10091]), frozenset([10088, 10097]), 0.31417004048582997),
									   (frozenset([10097]), frozenset([10088, 10091]), 0.27994227994227999),
									   (frozenset([10088]), frozenset([10097, 10091]), 0.43255295429208473),
									   (frozenset([10087]), frozenset([10097, 10098]), 0.23328149300155521),
									   (frozenset([10098]), frozenset([10097, 10087]), 0.102880658436214),
									   (frozenset([10097]), frozenset([10098, 10087]), 0.21645021645021648),
									   (frozenset([10098]), frozenset([10088, 10090]), 0.12105624142661178),
									   (frozenset([10090]), frozenset([10088, 10098]), 0.35513078470824944),
									   (frozenset([10088]), frozenset([10090, 10098]), 0.39353400222965434),
									   (frozenset([10091]), frozenset([10089, 10098]), 0.24615384615384617),
									   (frozenset([10098]), frozenset([10089, 10091]), 0.10425240054869685),
									   (frozenset([10089]), frozenset([10098, 10091]), 0.42816901408450708),
									   (frozenset([10091]), frozenset([10088, 10098]), 0.33522267206477729),
									   (frozenset([10098]), frozenset([10088, 10091]), 0.1419753086419753),
									   (frozenset([10088]), frozenset([10098, 10091]), 0.46153846153846151),
									   (frozenset([10091]), frozenset([10097, 10090]), 0.31174089068825911),
									   (frozenset([10090]), frozenset([10097, 10091]), 0.38732394366197187),
									   (frozenset([10097]), frozenset([10090, 10091]), 0.27777777777777779),
									   (frozenset([10090]), frozenset([10088, 10097]), 0.34004024144869216),
									   (frozenset([10097]), frozenset([10088, 10090]), 0.2438672438672439),
									   (frozenset([10088]), frozenset([10097, 10090]), 0.3768115942028985),
									   (frozenset([10090]), frozenset([10098, 10091]), 0.41549295774647882),
									   (frozenset([10091]), frozenset([10098, 10090]), 0.33441295546558703),
									   (frozenset([10098]), frozenset([10090, 10091]), 0.1416323731138546),
									   (frozenset([10097]), frozenset([10089, 10098]), 0.21789321789321792),
									   (frozenset([10098]), frozenset([10089, 10097]), 0.10356652949245543),
									   (frozenset([10089]), frozenset([10097, 10098]), 0.42535211267605633),
									   (frozenset([10097]), frozenset([10089, 10091]), 0.20129870129870134),
									   (frozenset([10091]), frozenset([10089, 10097]), 0.22591093117408906),
									   (frozenset([10089]), frozenset([10097, 10091]), 0.39295774647887327),
									   (frozenset([10090]), frozenset([10097, 10098]), 0.41146881287726361),
									   (frozenset([10098]), frozenset([10097, 10090]), 0.14026063100137176),
									   (frozenset([10097]), frozenset([10098, 10090]), 0.29509379509379513),
									   (frozenset([10091]), frozenset([10088, 10090]), 0.27692307692307694),
									   (frozenset([10090]), frozenset([10088, 10091]), 0.34406438631790748),
									   (frozenset([10088]), frozenset([10090, 10091]), 0.38127090301003341),
									   (frozenset([10091]), frozenset([10097, 10098]), 0.4072874493927125),
									   (frozenset([10098]), frozenset([10097, 10091]), 0.17249657064471879),
									   (frozenset([10097]), frozenset([10098, 10091]), 0.36291486291486291),
									   (frozenset([10098]), frozenset([10088, 10097]), 0.14266117969821673),
									   (frozenset([10097]), frozenset([10088, 10098]), 0.30014430014430016),
									   (frozenset([10088]), frozenset([10097, 10098]), 0.46376811594202894),
									   (frozenset([10090, 10091]), frozenset([10088, 10098]), 0.57884615384615379),
									   (frozenset([10088, 10091]), frozenset([10098, 10090]), 0.61178861788617878),
									   (frozenset([10088, 10090]), frozenset([10098, 10091]), 0.73236009732360097),
									   (frozenset([10098, 10091]), frozenset([10088, 10090]), 0.41289437585733879),
									   (frozenset([10098, 10090]), frozenset([10088, 10091]), 0.50503355704697983),
									   (frozenset([10088, 10098]), frozenset([10090, 10091]), 0.53368794326241131),
									   (frozenset([10091]), frozenset([10088, 10098, 10090]), 0.24372469635627528),
									   (frozenset([10090]), frozenset([10088, 10098, 10091]), 0.30281690140845069),
									   (frozenset([10088]), frozenset([10098, 10091, 10090]), 0.33556298773690074),
									   (frozenset([10098]), frozenset([10088, 10090, 10091]), 0.1032235939643347),
									   (frozenset([10088, 10091]), frozenset([10097, 10098]), 0.7032520325203252),
									   (frozenset([10098, 10091]), frozenset([10088, 10097]), 0.47462277091906724),
									   (frozenset([10088, 10098]), frozenset([10097, 10091]), 0.61347517730496459),
									   (frozenset([10097, 10091]), frozenset([10088, 10098]), 0.57379767827529027),
									   (frozenset([10088, 10097]), frozenset([10098, 10091]), 0.72083333333333344),
									   (frozenset([10097, 10098]), frozenset([10088, 10091]), 0.45586297760210814),
									   (frozenset([10088]), frozenset([10097, 10098, 10091]), 0.38573021181716838),
									   (frozenset([10091]), frozenset([10088, 10097, 10098]), 0.28016194331983807),
									   (frozenset([10098]), frozenset([10088, 10097, 10091]), 0.11865569272976681),
									   (frozenset([10097]), frozenset([10088, 10098, 10091]), 0.24963924963924969),
									   (frozenset([10090, 10091]), frozenset([10088, 10097]), 0.57307692307692304),
									   (frozenset([10088, 10091]), frozenset([10097, 10090]), 0.60569105691056901),
									   (frozenset([10088, 10090]), frozenset([10097, 10091]), 0.72506082725060828),
									   (frozenset([10097, 10091]), frozenset([10088, 10090]), 0.49419568822553894),
									   (frozenset([10097, 10090]), frozenset([10088, 10091]), 0.61570247933884292),
									   (frozenset([10088, 10097]), frozenset([10090, 10091]), 0.62083333333333335),
									   (frozenset([10091]), frozenset([10088, 10097, 10090]), 0.24129554655870444),
									   (frozenset([10090]), frozenset([10088, 10097, 10091]), 0.29979879275653926),
									   (frozenset([10088]), frozenset([10097, 10090, 10091]), 0.33221850613154957),
									   (frozenset([10097]), frozenset([10088, 10090, 10091]), 0.21500721500721504),
									   (frozenset([10090, 10091]), frozenset([10097, 10098]), 0.65384615384615374),
									   (frozenset([10098, 10091]), frozenset([10097, 10090]), 0.46639231824417005),
									   (frozenset([10098, 10090]), frozenset([10097, 10091]), 0.57046979865771807),
									   (frozenset([10097, 10091]), frozenset([10098, 10090]), 0.5638474295190713),
									   (frozenset([10097, 10090]), frozenset([10098, 10091]), 0.70247933884297509),
									   (frozenset([10097, 10098]), frozenset([10090, 10091]), 0.44795783926218707),
									   (frozenset([10091]), frozenset([10097, 10098, 10090]), 0.27530364372469635),
									   (frozenset([10090]), frozenset([10097, 10098, 10091]), 0.34205231388329976),
									   (frozenset([10098]), frozenset([10097, 10090, 10091]), 0.11659807956104251),
									   (frozenset([10097]), frozenset([10098, 10091, 10090]), 0.24531024531024531),
									   (frozenset([10088, 10090]), frozenset([10097, 10098]), 0.74695863746958635),
									   (frozenset([10098, 10090]), frozenset([10088, 10097]), 0.5151006711409396),
									   (frozenset([10088, 10098]), frozenset([10097, 10090]), 0.54432624113475181),
									   (frozenset([10097, 10090]), frozenset([10088, 10098]), 0.63429752066115708),
									   (frozenset([10088, 10097]), frozenset([10098, 10090]), 0.63958333333333339),
									   (frozenset([10097, 10098]), frozenset([10088, 10090]), 0.40447957839262194),
									   (frozenset([10088]), frozenset([10097, 10098, 10090]), 0.34225195094760313),
									   (frozenset([10090]), frozenset([10088, 10097, 10098]), 0.30885311871227367),
									   (frozenset([10098]), frozenset([10088, 10097, 10090]), 0.10528120713305898),
									   (frozenset([10097]), frozenset([10088, 10098, 10090]), 0.22150072150072153),
									   (frozenset([10097, 10098, 10091]), frozenset([10088, 10090]), 0.54274353876739567),
									   (frozenset([10097, 10090, 10098]), frozenset([10088, 10091]), 0.66748166259168695),
									   (frozenset([10090, 10091, 10098]), frozenset([10088, 10097]), 0.66101694915254239),
									   (frozenset([10097, 10090, 10091]), frozenset([10088, 10098]), 0.70909090909090899),
									   (frozenset([10088, 10097, 10098]), frozenset([10090, 10091]), 0.65625),
									   (frozenset([10088, 10098, 10091]), frozenset([10097, 10090]), 0.65942028985507251),
									   (frozenset([10088, 10097, 10091]), frozenset([10090, 10098]), 0.70360824742268036),
									   (frozenset([10088, 10090, 10098]), frozenset([10097, 10091]), 0.77337110481586413),
									   (frozenset([10088, 10097, 10090]), frozenset([10098, 10091]), 0.80769230769230771),
									   (frozenset([10088, 10090, 10091]), frozenset([10097, 10098]), 0.79824561403508765),
									   (frozenset([10097, 10098]), frozenset([10088, 10090, 10091]), 0.35968379446640319),
									   (frozenset([10098, 10091]), frozenset([10088, 10097, 10090]), 0.37448559670781889),
									   (frozenset([10097, 10091]), frozenset([10088, 10090, 10098]), 0.45273631840796019),
									   (frozenset([10090, 10098]), frozenset([10088, 10097, 10091]), 0.45805369127516776),
									   (frozenset([10097, 10090]), frozenset([10088, 10098, 10091]), 0.56404958677685946),
									   (frozenset([10090, 10091]), frozenset([10088, 10097, 10098]), 0.52500000000000002),
									   (frozenset([10088, 10097]), frozenset([10090, 10091, 10098]), 0.56874999999999998),
									   (frozenset([10088, 10098]), frozenset([10097, 10090, 10091]), 0.48404255319148931),
									   (frozenset([10088, 10091]), frozenset([10097, 10090, 10098]), 0.55487804878048774),
									   (frozenset([10088, 10090]), frozenset([10097, 10098, 10091]), 0.66423357664233573),
									   (frozenset([10097]), frozenset([10098, 10088, 10090, 10091]), 0.19696969696969699),
									   (frozenset([10098]), frozenset([10097, 10088, 10090, 10091]), 0.093621399176954723),
									   (frozenset([10091]), frozenset([10097, 10098, 10088, 10090]), 0.22105263157894736),
									   (frozenset([10090]), frozenset([10097, 10098, 10088, 10091]), 0.27464788732394363),
									   (frozenset([10088]), frozenset([10097, 10098, 10090, 10091]), 0.30434782608695649)],
				0.10000000000000001: [(frozenset([10098]), frozenset([10088]), 0.19341563786008231),
									  (frozenset([10088]), frozenset([10098]), 0.62876254180602009),
									  (frozenset([10091]), frozenset([10098]), 0.59028340080971653),
									  (frozenset([10098]), frozenset([10091]), 0.25),
									  (frozenset([10091]), frozenset([10097]), 0.48825910931174088),
									  (frozenset([10097]), frozenset([10091]), 0.4350649350649351),
									  (frozenset([10098]), frozenset([10097]), 0.26028806584362135),
									  (frozenset([10097]), frozenset([10098]), 0.54761904761904767),
									  (frozenset([10090]), frozenset([10098]), 0.59959758551307851),
									  (frozenset([10098]), frozenset([10090]), 0.20438957475994513)],
				}
#analyze data
def analyze_MBA(pk):
	confeds_10 = return_confeds(pk)
	monkey_scores = dict()
	weight_cause = 1
	weight_effect = weight_cause * 1

	for support in confeds_10.keys():
		data = confeds_10[support]
		for cause, effect, confidence in data:
			for mky in cause:
				try:
					monkey_scores[mky] += weight_cause * confidence * support
				except KeyError:
					monkey_scores[mky] = weight_cause * confidence * support
			for mky in effect:
				try:
					monkey_scores[mky] += weight_effect * confidence * support
				except KeyError:
					monkey_scores[mky] = weight_effect * confidence * support
	return monkey_scores
#build boxplots
def rhesus_confederate_boxplots():
	figs = list()
	for i in [5, 6, 9, 10]:
		scores = analyze_MBA(i)
		confeds = list()
		mean = numpy.array(scores.values()).mean()
		for key in scores.keys():
			if scores[key] > mean:
				confeds.append(key)
		for _column in ['ebt_length', 'ebt_volume']:
			fig = confederate_boxplots(confeds, _column)
			figs.append((fig, i, _column))
	return figs
#--



#----------------------
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

def create_erich_graphs():
	import settings
	output_path = settings.STATIC_ROOT
	output_path = os.path.join(output_path, "images/erich/")

	minutes = 120
	for mky_cat in rhesus_drinkers.keys():
		fig = rhesus_oa_discrete_minute_volumes(minutes, mky_cat)
		DPI = fig.get_dpi()
		filename = output_path + '%s-%d-%s.png' % ("rhesus_discrete_minute_volumes", minutes, mky_cat)
		fig.savefig(filename, dpi=DPI)

	confed_boxplots = rhesus_confederate_boxplots()
	for fig, coh_pk, column in confed_boxplots:
		DPI = fig.get_dpi()
		filename = output_path + '%s-%d-%s.png' % ("rhesus_confederate_boxplots", coh_pk, column)
		fig.savefig(filename, dpi=DPI)

