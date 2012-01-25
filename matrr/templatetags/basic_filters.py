__author__ = 'Jon'
import os
from django import template
from settings import STATIC_ROOT, STATICFILES_DIRS
import string
register = template.Library()


@register.filter()
def strip_account(value):
	
	
	if string.count(value, 'accounts/') != 0:
		return ""
	return value

@register.filter()
def truncate_by_char(value, arg):
	try:
		array = value.split(arg)
	except Exception:
		return value
	return array[0]

#  Returns a dictionary.
#  In this dictionary, keys are directories within static/images/
#  Values are the display name of that image
@register.filter()
def cohort_images(cohort, test_dir):
	# Directories to check
	image_dirs = {'etoh' : "Ethanol Intake", 'pellet' : "Total Pellets", 'veh' : 'Veh Intake', 'weight' : 'Weights'}
	images = {}

	if test_dir == 'all':
		for dir in image_dirs:
			path = STATIC_ROOT + '/images/' + dir + "/" + cohort.coh_cohort_name + ".png"
			if os.path.exists(path):
				images[dir] = image_dirs[dir]
	else:
		path = STATIC_ROOT + '/images/' + test_dir + "/" + cohort.coh_cohort_name + ".png"
		if os.path.exists(path):
			images[test_dir] = image_dirs[test_dir]
	
	return images


@register.filter()
def monkey_images(monkey, test_dir):
	# Directories to check
	image_dirs = {'etoh' : "Ethanol Intake", 'pellet' : "Total Pellets", 'veh' : 'Veh Intake', 'weight' : 'Weights', 'monkeys-bouts-drinks': 'Bouts, drinks per bout and total drinks'}
	images = {}

	if test_dir == 'all':
		for dir in image_dirs:
			if os.path.exists(STATIC_ROOT + '/images/' + dir + "/" + str(monkey) + ".png"):
				images[dir] = image_dirs[dir]
	else:
		if os.path.exists(STATIC_ROOT + '/images/' + test_dir + "/" + str(monkey) + ".png"):
			images[test_dir] = image_dirs[test_dir]

	return images

@register.filter_function
def order_by(queryset, args):
	args = [x.strip() for x in args.split(',')]
	return queryset.order_by(*args)