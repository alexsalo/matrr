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
	image_dirs = ['etoh']
	images = []

	if test_dir == 'all':
		for dir in image_dirs:
			if os.path.exists(STATIC_ROOT + '/images/' + dir + "/" + cohort.coh_cohort_name + ".png"):
				images[len(images):] = [dir]
	else:
		if os.path.exists(STATIC_ROOT + '/images/' + test_dir + "/" + cohort.coh_cohort_name + ".png"):
			images[len(images):] = [test_dir]

	return images
