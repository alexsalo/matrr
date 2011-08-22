__author__ = 'JonDev'
import os
from django import template
from settings import STATIC_ROOT

register = template.Library()

@register.filter()
def truncate_by_char(value, arg):
	try:
		array = value.split(arg)
	except ValueError:
		return value
	return array[0]

#  Returns a dictionary.
#  In this dictionary, keys are directories within static/images/
#  Values are bools indicating whether or not an image exists in that key directory for this cohort

@register.filter()
def cohort_images(cohort, test_dir):
	# Directories to check
	image_dirs = {'etoh' : "Ethanol Intake", 'pellet' : "Total Pellets", 'veh' : 'Veh Intake', 'weight' : 'Weights'}
	images = {}

	if test_dir == 'all':
		for dir in image_dirs:
			if os.path.exists(STATIC_ROOT + '/images/' + dir + "/" + cohort.coh_cohort_name + ".png"):
				images[dir] = image_dirs[dir]
	else:
		if os.path.exists(STATIC_ROOT + '/images/' + test_dir + "/" + cohort.coh_cohort_name + ".png"):
			images[test_dir] = image_dirs[test_dir]

	return images


@register.filter()
def monkey_images(monkey, test_dir):
	# Directories to check
	image_dirs = {'etoh' : "Ethanol Intake"}
	images = {}

	if test_dir == 'all':
		for dir in image_dirs:
			if os.path.exists(STATIC_ROOT + '/images/' + dir + "/" + str(monkey) + ".png"):
				images[dir] = image_dirs[dir]
	else:
		if os.path.exists(STATIC_ROOT + '/images/' + test_dir + "/" + str(monkey) + ".png"):
			images[test_dir] = image_dirs[test_dir]

	return images