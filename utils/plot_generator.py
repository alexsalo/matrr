from matrr.models import *

'''
This file should delete and regenerate all generated plots.

Goal is to make this more fancy, so that you can pass "MonkeyImage" as a parameter and only regenerate those images.
'''

MonkeyImage.objects.all().delete()
for monkey in Monkey.objects.all():
	for key in plotting.MONKEY_PLOTS:
		graph = key
		monkeyimage, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method=graph, title=plotting.MONKEY_PLOTS[key][1])
		monkeyimage.save()

CohortImage.objects.all().delete()
for cohort in Cohort.objects.all():
	for key in plotting.COHORT_PLOTS:
		graph = key
		cohortimage, is_new = CohortImage.objects.get_or_create(cohort=cohort, method=graph, title=plotting.COHORT_PLOTS[key][1])
		cohortimage.save()
