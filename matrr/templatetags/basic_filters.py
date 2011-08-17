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
def cohort_images(cohort):
	image_dirs = {'etoh':False}

	for key in image_dirs.keys():
		image_dirs[key] = os.path.exists(STATIC_ROOT + '/images/' + key + "/" + cohort.coh_cohort_name + ".png")

	return image_dirs
