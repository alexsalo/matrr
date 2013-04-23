from django.db.transaction import commit_on_success
from matrr.models import *
from django.db import transaction
from datetime import datetime as dt
#from datetime import date
from datetime import timedelta, time
import string
import datetime
import csv
import re
import gc
import logging

def queryset_iterator(queryset, chunksize=5000):
	'''
	http://djangosnippets.org/snippets/1949/

	Iterate over a Django Queryset ordered by the primary key

	This method loads a maximum of chunksize (default: 1000) rows in it's
	memory at the same time while django normally would load all rows in it's
	memory. Using the iterator() method only causes it to not preload all the
	classes.

	Note that the implementation of the iterator does not support ordered query sets.
	'''
	pk = 0
	last_pk = queryset.order_by('-pk')[0].pk
	queryset = queryset.order_by('pk')
	while pk < last_pk:
		for row in queryset.filter(pk__gt=pk)[:chunksize]:
			pk = row.pk
			yield row
		gc.collect()

def __get_datetime_from_steve(steve_date):
	def minimalist_xldate_as_datetime(xldate, datemode):
		# datemode: 0 for 1900-based, 1 for 1904-based
		return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(xldate) + 1462 * datemode)
	try:
		real_date = dt.strptime(steve_date, "%m/%d/%y")
		return real_date
	except Exception as e:
		pass
	try:
		real_date = dt.strptime(steve_date, "%Y-%m-%d")
		return real_date
	except Exception as e:
		pass
	try:
		real_date = dt.strptime(steve_date, "%Y_%m_%d")
		return real_date
	except Exception as e:
		pass
	try:
		real_date = minimalist_xldate_as_datetime(steve_date, 1)
		return real_date
	except Exception as e:
		pass
	return None

def convert_MonkeyProtein_dates_to_correct_datetimes():

	dates = (
			(2002,4,15),
			(2003,3,5),
			(2003,4,28),
			(2003,4,30),
			(2003,12,19),
			(2004,8,2),
			)
	times = (
			(12,0),
			(17,30),
			(12,0),
			(17,30),
			(7,0),
			(12,0),
			)
	for d,t in zip(dates, times):
		old_datetime = dt(*d)
		monkeys = MonkeyProtein.objects.filter(mpn_date=old_datetime)
		new_datetime = old_datetime.combine(old_datetime.date(), time(*t))
		monkeys.update(mpn_date = new_datetime)

@transaction.commit_on_success
def load_initial_inventory(file, output_file, load_tissue_types=False,  delete_name_duplicates=False, create_tissue_samples=False):
	"""
	  This function will load freezer inventories from a csv file.
	  !!!!! It will only load monkeys that are already in the database !!!!!
	  It assumes that the cohorts and monkeys have already been created.
	  It will create tissue categories if they do not already exist.
	  It also assumes the columns are in the following order:
		0 - Cohort Name -- ignoring this column for now
		1 - Monkey ID
		2 - Necropsy Date (or necropsy start date)
		3 - Date Range End
		4 - MATRR TissueType Name
		5 - Shelf
		6 - Rack
		7 - Column
		8 - Box
		9 - Available samples
		10 - Freezer
	  """
	if load_tissue_types:
		load_TissueTypes('utils/DATA/tissuetypes.txt', delete_name_duplicates, create_tissue_samples)
	input = csv.reader(open(file, 'rU'), delimiter=',')
	output = csv.writer(open(output_file, 'w'), delimiter=',')
	unknown_monkeys = csv.writer(open('unknown_monkeys.csv', 'w'), delimiter=',')
	# get the column headers
	columns = input.next()
	columns[11:] = ["MATRR parsing error"]
	output.writerow(columns)
	unknown_monkeys.writerow(columns)
	monkeys = []
	units = "whole"
	for row in input:
		# Empty monkey cell
		if row[1] is '' or row[1] is None:
			row[len(row):] = "empty monkey"
			output.writerow(row)
			continue
		if "---" in row[4]:
			continue

		monkey_id = row[1].rstrip().lstrip()
		necropsy_start_date = row[2].rstrip().lstrip()
		necropsy_end_date = row[3].rstrip().lstrip()
		raw_tissue_types = row[4].rstrip().lstrip()
		shelf = row[5].rstrip().lstrip()		### 	"SHELF #" to "#" with find/replace in spreadsheet apps
		drawer = row[6].rstrip().lstrip()		### 	"Drawer #"  -->  "#"
		tower = row[7].rstrip().lstrip()
		box = row[8].rstrip().lstrip()		### 	"bag" --> "0"
		available_samples = row[9].rstrip().lstrip()
		freezer = row[10].rstrip().lstrip()

		if Monkey.objects.filter(mky_real_id=monkey_id).count() == 1:
			monkey = Monkey.objects.get(mky_real_id=monkey_id)

			# Update necropsy dates if there are none.
			if monkey_id not in monkeys:
				if necropsy_start_date and not monkey.mky_necropsy_start_date:
					monkey.mky_necropsy_start_date = re.sub(r'(\d{2})/(\d{2})/(\d{2})', r'20\3-\1-\2', necropsy_start_date)
				if necropsy_end_date and not monkey.mky_necropsy_end_date:
					monkey.mky_necropsy_end_date = re.sub(r'(\d{2})/(\d{2})/(\d{2})', r'20\3-\1-\2', necropsy_end_date)
				monkey.save()
				monkeys.append(monkey_id)

			dump = False
			# get the tissue type
			raw_tissue_types = raw_tissue_types.split("|")
			tissue_types = []
			for tissue_name in raw_tissue_types:
				if TissueType.objects.filter(tst_tissue_name=tissue_name).count():
					tissue_types[len(tissue_types):] = [TissueType.objects.get(tst_tissue_name=tissue_name)]
				else:
					if tissue_name:
						# If it isn't empty and doesn't exist, dump the row to the outfile
						row[11:] = ["Unmatched tissue type, %s.  Check for typos" % tissue_name]
						output.writerow(row)

			for tissue_type in tissue_types:
				#  Must have created tissue samples before running this function
				#  Only intended to update records, not create them
				sample = TissueSample.objects.get(tissue_type=tissue_type, monkey=monkey)
				# build the location string
				shelf = str(shelf)
				drawer = str(drawer)
				tower = str(tower)
				box = str(box)
				if shelf and drawer and tower and box: # evaluates True if shelf=drawer=tower=box=0, but False if any are empty
					location = shelf + '-' + drawer + '-' + tower + '-' + box
				else:
					location = "None"
				sample.tss_location = location
				if freezer:
					sample.tss_freezer = freezer
				if available_samples or available_samples == 0:
					sample.tss_sample_quantity = float(available_samples)
					sample.units = units
				else:
					if "ohsu" in freezer.lower():
						sample.tss_sample_quantity = 1
						sample.units = units
					else:
						sample.tss_sample_quantity = 0
						sample.units = units
						row[4] = tissue_type
						row[11:] = ["AvailableQuantity is empty and freezer is not OHSU.  Assuming 0 quantity"]
						dump = True
				sample.save()
				if dump:
					output.writerow(row)
		else:
			# if the monkey does not exist, or we have more than 1 monkey record,
			# add the monkey to the list of left out monkeys
			row[11:] = ["No MATRR record for this monkey"]
			unknown_monkeys.writerow(row)
		#raise Exception('Just testing') #uncomment for testing purposes

def load_cohort_6a_inventory(input_file):
	unmatched_output_file = input_file + "-unmatched-output.csv"

	input_data = csv.reader(open(input_file, 'rU'), delimiter=',')
	unmatched_output = csv.writer(open(unmatched_output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

	columns = input_data.next()
	unmatched_output.writerow(columns)

	print "Loading Inventory..."
	for row in input_data:
		mky_id 		= row[0]
		real_id	 	= row[1]
		excel_date	= row[2] #ignored
		txt_date 	= row[3] #ignored
		tissue_type	= row[4].strip()
		req_by		= row[5] #ignored
		freezer 	= row[6]
		shelf		= "shelf=%s" % row[7]
		flag		= row[8] #ignored

		if real_id == '0':
				continue
		try:
				monkey = Monkey.objects.get(pk=mky_id)
		except Monkey.DoesNotExist:
				error = "Error: Monkey not found:  " + str(mky_id)
				row.append(error)
				unmatched_output.writerow(row)
				print error
				continue
		if monkey.mky_real_id != int(real_id):
			error = "Error: mky_real_id %s does not match mky_id %s" % (str(real_id), str(mky_id))
			row.append(error)
			unmatched_output.writerow(row)
			print error
			continue


		tst = TissueType.objects.filter(tst_tissue_name__iexact=tissue_type)
		if not tst:
			error = "Error: Unknown tissue type"
			row.append(error)
			unmatched_output.writerow(row)
			print error
			continue
		elif tst.count() == 1:
			tss = TissueSample.objects.filter(monkey=monkey, tissue_type=tst[0])
			if tss.count() == 1:
				tss = tss[0]
			else:
				break
			tss.tss_freezer = freezer
			tss.tss_location = shelf
			tss.tss_sample_quantity = 1
			tss.save()
		else:
			error = "Error:  Too many TissueType matches."
			row.append(error)
			unmatched_output.writerow(row)
			print error

def load_cohort_8_inventory(input_file, load_tissue_types=False, delete_name_duplicates=False, create_tissue_samples=False):
	if load_tissue_types:
		load_TissueTypes('utils/DATA/tissuetypes.txt', delete_name_duplicates, create_tissue_samples)
	unmatched_output_file = input_file + "-unmatched-output.csv"

	input_data = csv.reader(open(input_file, 'rU'), delimiter=',')
	unmatched_output = csv.writer(open(unmatched_output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

	columns = input_data.next()
	unmatched_output.writerow(columns)

	print "Loading Inventory..."
	for row in input_data:
		tissue 		= row[0]
		name	 	= row[1]
		realid 		= row[2]
		freezer 	= row[3]
		location 	= row[4]
		details 	= row[5] #ignored
		quantity 	= row[6] #ignored
		units		= row[7] #ignored

		if realid == '0':
				continue
		try:
				monkey = Monkey.objects.get(mky_real_id=realid)
		except Monkey.DoesNotExist:
				error = "Error: Monkey not found:  " + str(realid)
				row.append(error)
				unmatched_output.writerow(row)
				print error
				continue

		tsts = TissueType.objects.filter(tst_tissue_name__iexact=tissue)
		if not tsts:
			if tissue == "Heart":
				heart_tsts = TissueType.objects.filter(tst_tissue_name__contains=tissue)
				for tst in heart_tsts:
					tss = TissueSample.objects.get(monkey=monkey, tissue_type=tst)
					tss.tss_freezer = freezer
					tss.tss_location = location
					tss.tss_sample_quantity = 1
					tss.save()
				print "Found a Heart.  Updated each quadrant's inventory."
				continue
			else:
				error = "Error: Unknown tissue type"
				row.append(error)
				unmatched_output.writerow(row)
				print error
				continue
		elif tsts.count() == 1:
			tss = TissueSample.objects.get(monkey=monkey, tissue_type=tsts[0])
			tss.tss_freezer = freezer
			tss.tss_location = location
			tss.tss_sample_quantity = 1
			tss.save()
		else:
			error = "Error:  Too many TissueType matches."
			row.append(error)
			unmatched_output.writerow(row)
			print error

def load_cohort_7b_inventory(input_file):
	output = input_file.split('/')
	output.reverse()
	output_file = output[0] + '-output.txt'

	input_data = csv.reader(open(input_file, 'rU'), delimiter=',')
	unmatched_output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

	columns = input_data.next()
	unmatched_output.writerow(columns)

	inv_fields = (2, 10)
	print "Loading Inventory..."

	# ordered by columns 2 thru 11
	mky_24818 = Monkey.objects.get(mky_real_id=24818)
	mky_25154 = Monkey.objects.get(mky_real_id=25154)
	mky_25157 = Monkey.objects.get(mky_real_id=25157)
	mky_25184 = Monkey.objects.get(mky_real_id=25184)
	mky_25207 = Monkey.objects.get(mky_real_id=25207)
	mky_25407 = Monkey.objects.get(mky_real_id=25407)
	mky_25240 = Monkey.objects.get(mky_real_id=25240)
	mky_25425 = Monkey.objects.get(mky_real_id=25425)
	mky_25526 = Monkey.objects.get(mky_real_id=25526)
	mkys = [mky_24818, mky_25154, mky_25157, mky_25184, mky_25207, mky_25407, mky_25240, mky_25425, mky_25526]
	for row in input_data:
		tissue_category		= row[0] #ignored
		tissue_name		 	= row[1]
		tissue_type = TissueType.objects.filter(tst_tissue_name__iexact=tissue_name)
		if not tissue_type:
			error = "Error: Unknown tissue type"
			row.append(error)
			print row
			unmatched_output.writerow(row)
			print error
			continue
		elif tissue_type.count() == 1:
			try:
				for mky, tissue_exists in zip(mkys, row[inv_fields[0]:inv_fields[1]]):
					tss = TissueSample.objects.filter(monkey=mky, tissue_type=tissue_type)
					if tss.count() == 1:
						tss = tss[0]
					else:
						error = "Error:  Too many or not enough tissues samples for monkey %s, tissue %s." % (str(mky), str(tissue_type))
						row.append(error)
						unmatched_output.writerow(row)
						print error
					tss.tss_freezer = "Ask OHSU"
					tss.tss_location = "Ask OHSU"
					tss.tss_sample_quantity = 1
					tss.save()
			except IndexError:
				print 'index error\n %s' % str(row)
		else:
			error = "Error:  Too many TissueType matches."
			row.append(error)
			unmatched_output.writerow(row)
			print error


## Dumps database rows into a CSV.  I'm sure i'll need this again at some point
## -jf
def dump_all_TissueSample(output_file):
	"""
		This function will dump existing tissue samples to CSV
		It writes columns in this order
		0 - Category.cat_internal
		1 - Category.parent_category
		2 - Catagory.cat_name
		3 - Category.cat_description
		--- Empty
		4 - TissueType.tst_tissue_name
		5 - TissueType.tst_description
		6 - TissueType.tst_count_per_monkey
		7 - TissueType.tst_cost
		--- Empty
		8 - TissueSample.tss.monkey
		9 - TissueSample.tss_details
		10- TissueSample.tss_freezer
		11- TissueSample.tss_location
		12- TissueSample.tss_sample_count
		13- TissueSample.tss_distributed_count

	"""
	output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	columns =\
	["Internal Category", "Parent Category", "Category:Name", "Category:Description", "Empty Column", "TissueType:Name", "TissueType:Description", "TissueType:count_per_monkey",
	 "TissueType:cost", "Empty Column", "TissueSample:Monkey", "TissueSample:Details", "TissueSample:Freezer", "TissueSample:Location", "TissueSample:sample_count",
	 "TissueSample:distributed_count"]
	output.writerow(columns)

	for TS in TissueSample.objects.all():
		row = []
		row[len(row):] = [str(TS.tissue_type.category.cat_internal)]
		row[len(row):] = [str(TS.tissue_type.category.parent_category)]
		row[len(row):] = [str(TS.tissue_type.category.cat_name)]
		row[len(row):] = [str(TS.tissue_type.category.cat_description)]
		row[len(row):] = [" "]
		row[len(row):] = [str(TS.tissue_type.tst_tissue_name)]
		row[len(row):] = [str(TS.tissue_type.tst_description)]
		row[len(row):] = [TS.tissue_type.tst_count_per_monkey]
		row[len(row):] = [TS.tissue_type.tst_cost]
		row[len(row):] = [" "]
		row[len(row):] = [TS.monkey]
		row[len(row):] = [str(TS.tss_details)]
		row[len(row):] = [str(TS.tss_freezer)]
		row[len(row):] = [str(TS.tss_location)]
		row[len(row):] = [TS.tss_sample_count]
		row[len(row):] = [TS.tss_distributed_count]
		output.writerow(row)
	print "Success"

## Dumps database rows into a CSV.  I'm sure i'll need this again at some point
## -jf
def dump_distinct_TissueType(output_file):
	"""
		This function will dump existing tissue catagories and tissuetypes to CSV
		It writes columns in this order
		0 - Catagory.cat_name
		1 - TissueType.tst_tissue_name
	"""
	output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	columns =\
	["Category:Name", "TissueType:Name"]
	output.writerow(columns)

	for TT in TissueType.objects.distinct().order_by("category"):
		row = []
		row[len(row):] = [str(TT.category.cat_name)]
		row[len(row):] = [str(TT.tst_tissue_name)]
		output.writerow(row)
	print "Success."

def dump_monkey_protein_data(queryset, output_file):
	if isinstance(queryset, QuerySet) and isinstance(queryset[0], MonkeyProtein):
		output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
		columns = ['monkey', 'protein', 'mpn_date', 'mpn_value']
		output.writerow(columns)
		for mpn in queryset:
			output.writerow([mpn.monkey, "%s" % mpn.protein.pro_name, mpn.mpn_date, mpn.mpn_value])
		return output
	else:
		raise Exception("queryset kwarg can only be a QuerySet of MonkeyProteins.")

def load_monkey_data(input_file):
	input_data = csv.reader(open(input_file, 'rU'), delimiter=',')
	columns = input_data.next()

	for row in input_data:
		if row[2] == '0':
				continue
		try:
				monkey = Monkey.objects.get(mky_real_id=row[2])
		except Monkey.DoesNotExist:
				print "Monkey not found:  " + str(row[2])
				continue 
		monkey.mky_name = str(row[3])
		monkey.mky_gender = str(row[4])
		year = int(row[5].split('/')[2])
		year = year + 2000 if year < 12 else year + 1900
		monkey.mky_birthdate = datetime.datetime(year, int(row[5].split('/')[0]), int(row[5].split('/')[1]))
		if row[6]:
			monkey.mky_weight = float(row[6])
		monkey.mky_drinking = row[7] == 'TRUE'
		monkey.mky_housing_control = row[8] == 'TRUE'
		if row[9]:
			year = int(row[9].split('/')[2])
			year = year + 2000 if year < 12 else year + 1900
			monkey.mky_necropsy_start_date = datetime.datetime(year, int(row[9].split('/')[0]), int(row[9].split('/')[1]))
		monkey.mky_study_complete = row[13] == 'TRUE'
		monkey.mky_stress_model = row[14]
		monkey.mky_age_at_necropsy = row[15]
		monkey.save()
	print "Success"

# Creates Tissue Types from following format:
# each tissue on a separate line
# first group of tissues are loaded under category brain tissues
# second group under peripheral tissues
# last under custom
# groups separated with empty line
# if empty group, just empty line
# no empty line at the end of file!!!
def load_TissueTypes(file_name, delete_name_duplicates=False, create_tissue_samples=False):
	categories = {'brain': "Brain Tissues", 'periph': "Peripheral Tissues", 'custom': "Custom",
				  'int_brain': "Internal Brain Tissues", 'int_periph': "Internal Peripheral Tissues"}
	categs = []
	try:
		categs.append(TissueCategory.objects.get(cat_name=categories['brain']))
		categs.append(TissueCategory.objects.get(cat_name=categories['periph']))
		categs.append(TissueCategory.objects.get(cat_name=categories['custom']))
		categs.append(TissueCategory.objects.get(cat_name=categories['int_brain']))
		categs.append(TissueCategory.objects.get(cat_name=categories['int_periph']))
	except Exception:
		print "TissueTypes not added, missing Tissue Categories. Following categories are necessary: "
		for cat in categories.itervalues():
			print cat

	from matrr.models import TissueTypeSexRelevant
	category_iter = categs.__iter__()
	current_category = category_iter.next()
	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line in read_data:
			line = line.rsplit('%')
			tst_name = line[0].rstrip()
			if len(line) > 1:
				tissueSexRelevant = line[1].strip()
				if tissueSexRelevant not in TissueTypeSexRelevant.enum_dict.values():
					tissueSexRelevant = TissueTypeSexRelevant.Both
			else:
				tissueSexRelevant = TissueTypeSexRelevant.Both
			if tst_name == "":
				current_category = category_iter.next()
				continue
			duplicates = TissueType.objects.filter(tst_tissue_name=tst_name)
			existing = list()
			wrong_sr = list()
			name_duplicates_ids = list()
			name_duplicates = list()
			if len(duplicates) > 0:
				for duplicate in duplicates:
					if duplicate.category == current_category:
						if duplicate.tst_sex_relevant == tissueSexRelevant:
							existing.append(duplicate.tst_type_id)
						else:
							wrong_sr.append(duplicate)
					else:
						name_duplicates_ids.append(duplicate.tst_type_id)
						name_duplicates.append(duplicate)
			if len(name_duplicates_ids) > 0:
				if delete_name_duplicates:
					for name_duplicate in name_duplicates:
						name_duplicate.delete()
					print "Deleting name duplicates for tissue type " + tst_name + " (with wrong category). Duplicate ids = " + `name_duplicates_ids`
				else:
					print "Found name duplicates for tissue type " + tst_name + " (with wrong category). Duplicate ids = " + `name_duplicates_ids`

			if len(existing) > 0:
				print "Tissue type " + tst_name + " already exists with correct category and sex relevant field. Duplicate ids = " + `existing`
				continue
			if len(wrong_sr) > 0:
				for wsr in wrong_sr:
					wsr.tst_sex_relevant = tissueSexRelevant
					wsr.save()
					print "Tissue type " + tst_name + " already exists with correct category but with wrong sex relevant field. Updating that filed for id = " + `wsr.tst_type_id`
				continue

			tt = TissueType()
			tt.tst_tissue_name = tst_name
			tt.tst_sex_relevant = tissueSexRelevant
			tt.category = current_category
			tt.save()

	if create_tissue_samples:
		print "Creating tissue samples"
		create_TissueSamples()

# Creates TissueCategories consistent with format agreed on 8/30/2011
# No parent categories yet.
# -jf
def load_TissueCategories():
###				   Category Name  (cat_name)		Description (cat_description)			Internal (cat_internal)
	categories = {"Custom": ("Custom Tissues", False),
				  "Internal Molecular Tissues": ("Only internal molecular tissues", True),
				  "Internal Blood Tissues": ("Only internal blood tissues", True),
				  "Internal Peripheral Tissues": ("Only internal peripheral tissues", True),
				  "Internal Brain Tissues": ("Only internal brain tissues", True),
				  "Brain Tissues": ("Brain tissues", False),
				  "Peripheral Tissues": ("Peripheral tissues", False)
	}
	for key in categories:
		tc, is_new = TissueCategory.objects.get_or_create(cat_name=key)
		tc.cat_description = categories[key][0]
		tc.cat_internal = categories[key][1]
		tc.save()


@transaction.commit_on_success
# Creates ALL tissue samples in the database, for every monkey:tissuetype combination.
def create_TissueSamples(tissue_type=None):
	units = Units[2][0]
	for monkey in Monkey.objects.all():
		quantity = 0
		if not tissue_type:
			tissuetypes = TissueType.objects.all()
			# Only create the "be specific" tissue samples for upcoming cohorts
			if monkey.cohort.coh_upcoming:
				quantity = 1
			else:
				tissuetypes = tissuetypes.exclude(tst_tissue_name__icontains="Be specific")
		else:
			tissuetypes = [tissue_type]

		for tt in tissuetypes:
			sample, is_new = TissueSample.objects.get_or_create(monkey=monkey, tissue_type=tt)
			if is_new:
				sample.tss_freezer = "<new record, no data>"
				sample.tss_location = "<new record, no data>"
#				sample.tss_units = units
#				sample.tss_sample_quantity = quantity
				sample.save()
				# Can be incredibly spammy
				print "New tissue sample: " + sample.__unicode__()

@transaction.commit_on_success
def create_Assay_Development_tree():
	institution = Institution.objects.all()[0]
	cohort = Cohort.objects.get_or_create(coh_cohort_name="Assay Development", coh_upcoming=False, institution=institution)
	monkey = Monkey.objects.get_or_create(mky_real_id=0, mky_drinking=False, cohort=cohort[0])
	for tt in TissueType.objects.exclude(category__cat_name__icontains="Internal"):
		tissue_sample = TissueSample.objects.get_or_create(tissue_type=tt, monkey=monkey[0])
		tissue_sample[0].tss_sample_quantity = 999 # Force quantity
		tissue_sample[0].tss_freezer = "Assay Tissue"
		tissue_sample[0].tss_location = "Assay Tissue"
		tissue_sample[0].tss_details = "MATRR does not track assay inventory."



ERROR_OUTPUT = "%d %s # %s"

@transaction.commit_on_success
def load_mtd(file_name, dex_type, cohort_name, dump_duplicates=True, has_headers=True, dump_file=False, truncate_data_columns=48):
	"""
		0 - date
		1 - monkey_real_id
		2-37 see fields
		38 - date - check field (0) - but current data are unknown - thus unused
		39 - monkey_real_id - check field (1)
		40-45 - see fields again
		46 - free
		47 - bad data flag
		48 - comment/notes

		All data in comma-separated csv format, no caption line at the beginning of file
		For data with mutiple cohorts, the will have to be computed from monkey real id instead of using a parameter.
	"""
	fields = (
		#	    data 2-37
		('mtd_etoh_intake'),
		('mtd_veh_intake'),
		('mtd_pct_etoh'),
		('mtd_etoh_g_kg'),
		('mtd_total_pellets'),
		('mtd_etoh_bout'),
		('mtd_etoh_drink_bout'),
		('mtd_veh_bout'),
		('mtd_veh_drink_bout'),
		('mtd_weight'),
		('mtd_etoh_conc'),
		('mtd_etoh_mean_drink_length'),
		('mtd_etoh_median_idi'),
		('mtd_etoh_mean_drink_vol'),
		('mtd_etoh_mean_bout_length'),
		('mtd_etoh_media_ibi'),## typo matches model field
		('mtd_etoh_mean_bout_vol'),
		('mtd_etoh_st_1'),
		('mtd_etoh_st_2'),
		('mtd_etoh_st_3'),
		('mtd_veh_st_2'),
		('mtd_veh_st_3'),
		('mtd_pellets_st_1'),
		('mtd_pellets_st_3'),
		('mtd_length_st_1'),
		('mtd_length_st_2'),
		('mtd_length_st_3'),
		('mtd_vol_1st_bout'),
		('mtd_pct_etoh_in_1st_bout'),
		('mtd_drinks_1st_bout'),
		('mtd_mean_drink_vol_1st_bout'),
		('mtd_fi_wo_drinking_st_1'),
		('mtd_pct_fi_with_drinking_st_1'),
		('mtd_latency_1st_drink'),
		('mtd_pct_exp_etoh'),
		('mtd_st_1_ioc_avg'),
		#		data 40-45
		('mtd_max_bout'),
		('mtd_max_bout_start'),
		('mtd_max_bout_end'),
		('mtd_max_bout_length'),
		('mtd_max_bout_vol'),
		('mtd_pct_max_bout_vol_total_etoh'),
	)
	if not dex_type in DexTypes:
		raise Exception("'%s' is not an acceptable drinking experiment type.  Please choose from:  %s" % (dex_type, DexTypes))

	if dump_file:
		_filename = file_name.split('/')
		_filename.reverse()
		dump_file = open(_filename[0] + '-output.txt', 'w')
	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)
	with open(file_name, 'r') as f:
		read_data = f.readlines()
		if len(read_data) == 1:
			read_data = read_data[0].split('\r')
		for line_number, line in enumerate(read_data):
			if line_number == 0 and has_headers: # cyno 2 had column headers
				continue
			data = line.split(',')
			if data[0] == '0.5' or data[0] == '1' or data[0] == '1.5' or data[0] == '1.0': # for some damn reason they added a column in cyno 2's induction file.
				ind_portion = data.pop(0)
			_truncate_columns = min(38, truncate_data_columns)
			data_fields = data[2:_truncate_columns]
			if truncate_data_columns > 40:
				data_fields.extend(data[40:truncate_data_columns])

			# create or get experiment - date, cohort, dex_type
			dex_date = __get_datetime_from_steve(data[0])
			if not dex_date:
				err = ERROR_OUTPUT % (line_number, "Wrong date format", line)
				if dump_file:
					dump_file.write(err + '\n')
				else:
					print err
				continue
			else:
				des = DrinkingExperiment.objects.filter(dex_type=dex_type, dex_date=dex_date, cohort=cohort)
				if des.count() == 0:
					de = DrinkingExperiment(dex_type=dex_type, dex_date=dex_date, cohort=cohort)
					de.save()
				elif des.count() == 1:
					de = des[0]
				else:
					err = ERROR_OUTPUT % (line_number, "Too many drinking experiments with type %s, cohort %d and specified date." % (dex_type, cohort.coh_cohort_id), line)
					if dump_file:
						dump_file.write(err + '\n')
					else:
						print err
					continue

			monkey_real_id = data[1]
			if truncate_data_columns > 38:
				monkey_real_id_check = data[39]
				if monkey_real_id != monkey_real_id_check:
					err = ERROR_OUTPUT % (line_number, "Monkey real id check failed", line)
					if dump_file:
						dump_file.write(err + '\n')
					else:
						print err
					continue
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey_real_id)
			except:
				err = ERROR_OUTPUT % (line_number, "Monkey does not exist", line)
				if dump_file:
					dump_file.write(err + '\n')
				else:
					print err
				continue

			try:
				bad_data = data[47]
			except IndexError:
				bad_data = ''
			if bad_data != '':
				err = ERROR_OUTPUT % (line_number, "Bad data flag", line)
				if dump_file:
					dump_file.write(err + '\n')
				else:
					print err
				continue

			mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment=de, monkey=monkey)
			if mtds.count() != 0:
				err = ERROR_OUTPUT % (line_number, "MTD with monkey and date already exists.", line)
				if dump_file:
					dump_file.write(err + '\n')
				else:
					if dump_duplicates:
						print err
				continue
			mtd = MonkeyToDrinkingExperiment()
			mtd.monkey = monkey
			mtd.drinking_experiment = de

			try:
				notes = data[48]
			except IndexError:
				notes = ''
			mtd.mtd_notes = notes

			for i, field in enumerate(fields):
				if i >= len(data_fields):
					break
				if not data_fields[i] in ['', '\n', '\r']:
					setattr(mtd, field, data_fields[i])

			try:
				mtd.clean_fields()
			except Exception as e:
				err = ERROR_OUTPUT % (line_number, e, line)
				if dump_file:
					dump_file.write(err + '\n')
				else:
					print err
				continue
			mtd.save()

def load_ebt_one_inst(data_list, line_number, create_mtd, dex, line, bout_index=1, dump_file=''):
	fields = (
		'ebt_number',
		'',
		'ebt_start_time',
		'ebt_end_time',
		'ebt_length',
		'ebt_ibi',
		'ebt_volume'
		)
	FIELDS_INDEX = (1,8) #[1,7) => 1,2,3,4,5,6
	MONKEY_DATA_INDEX = 0
	BOUT_NUMBER_DATA_INDEX = bout_index

	if data_list[MONKEY_DATA_INDEX] == '28479':
		return
	try:
		monkey = Monkey.objects.get(mky_real_id=data_list[MONKEY_DATA_INDEX])
	except:
		err = ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return

	mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey, drinking_experiment=dex)
	if mtds.count() == 0:
		if create_mtd:
			mtd = MonkeyToDrinkingExperiment(monkey=monkey, drinking_experiment=dex, mtd_etoh_intake=-1, mtd_veh_intake=-1, mtd_total_pellets=-1)
			mtd.save()
			mtd = [mtd,]
			print "%d Creating MTD." % line_number
		else:
			err = ERROR_OUTPUT % (line_number, "MonkeyToDrinkingExperiment does not exist.", line)
			if dump_file:
				dump_file.write(err + '\n')
			else:
				print err
			return
	if mtds.count() > 1:
		err = ERROR_OUTPUT % (line_number, "More than one MTD.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	mtd = mtds[0]

	ebts = ExperimentBout.objects.filter(mtd=mtd, ebt_number=data_list[BOUT_NUMBER_DATA_INDEX])
	if ebts.count() != 0:
		err = ERROR_OUTPUT % (line_number, "EBT with MTD and bout number already exists.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return

	ebt = ExperimentBout()
	ebt.mtd = mtd			
	data_fields = data_list[FIELDS_INDEX[0]:FIELDS_INDEX[1]]

	for i, field in enumerate(fields):

		if data_fields[i] != '':
				setattr(ebt, field, data_fields[i])

	try:
		ebt.full_clean()

	except Exception as e:
		err = ERROR_OUTPUT % (line_number, e, line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	ebt.save()

def load_ebt_one_file(file_name, dex, create_mtd=False):
	fields = (
		'ebt_number',
		'ebt_start_time',
		'ebt_end_time',
		'ebt_length',
		'ebt_ibi',
		'ebt_volume'
		)
	FIELDS_INDEX = (1,7) #[1,7) => 1,2,3,4,5,6
	MONKEY_DATA_INDEX = 0
	BOUT_NUMBER_DATA_INDEX = 1

	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line_number, line in enumerate(read_data[1:], start=1):
			data = line.split("\t")
			if data[MONKEY_DATA_INDEX] == '28479':
				continue
			try:
				monkey = Monkey.objects.get(mky_real_id=data[MONKEY_DATA_INDEX])
			except:
				print ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
				continue

			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey, drinking_experiment=dex)
			if mtds.count() == 0:
				if create_mtd:
					mtd = MonkeyToDrinkingExperiment(monkey=monkey, drinking_experiment=dex, mtd_etoh_intake=-1, mtd_veh_intake=-1, mtd_total_pellets=-1)
					mtd.save()
					mtd = [mtd,]
					print "%d Creating MTD." % line_number
				else:
					print ERROR_OUTPUT % (line_number, "MonkeyToDrinkingExperiment does not exist.", line)
					continue
			if mtds.count() > 1:
				print ERROR_OUTPUT % (line_number, "More than one MTD.", line)
				continue
			mtd = mtds[0]

			ebts = ExperimentBout.objects.filter(mtd=mtd, ebt_number = data[BOUT_NUMBER_DATA_INDEX])
			if ebts.count() != 0:
				print ERROR_OUTPUT % (line_number, "EBT with MTD and bout number already exists.", line)
				continue

			ebt = ExperimentBout()
			ebt.mtd = mtd			
			data_fields = data[FIELDS_INDEX[0]:FIELDS_INDEX[1]]

			for i, field in enumerate(fields):
				if data_fields[i] != '':
					setattr(ebt, field, data_fields[i])

			try:
				ebt.full_clean()

			except Exception as e:
				print ERROR_OUTPUT % (line_number, e, line)
				continue
			ebt.save()

def load_edr_one_inst(data_list, dex, line_number, line, bout_index=1, drink_index=2, dump_file=''):
	fields = (
		'edr_number',
		'edr_start_time',
		'edr_end_time',
		'edr_length',
		'edr_idi',
		'edr_volume'
		)
	FIELDS_INDEX = (2,8) #[2,8) => 2,3,4,5,6,7
	MONKEY_DATA_INDEX = 0
	BOUT_NUMBER_DATA_INDEX = bout_index
	DRINK_NUMBER_DATA_INDEX = drink_index

	if data_list[MONKEY_DATA_INDEX] == '28479':
		return
	try:
		monkey = Monkey.objects.get(mky_real_id=data_list[MONKEY_DATA_INDEX])
	except:
		err = ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return

	mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey, drinking_experiment=dex)
	if mtds.count() == 0:
		err =  ERROR_OUTPUT % (line_number, "MonkeyToDrinkingExperiment does not exist.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	if mtds.count() > 1:
		err = ERROR_OUTPUT % (line_number, "More than one MTD.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	mtd = mtds[0]

	ebts = ExperimentBout.objects.filter(mtd=mtd, ebt_number = data_list[BOUT_NUMBER_DATA_INDEX])
	if ebts.count() == 0:
		err = ERROR_OUTPUT % (line_number, "EBT does not exist.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	if ebts.count() > 1:
		err = ERROR_OUTPUT % (line_number, "More than one EBT.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	ebt = ebts[0]

	edrs = ExperimentDrink.objects.filter(ebt=ebt, edr_number = data_list[DRINK_NUMBER_DATA_INDEX])
	if edrs.count() != 0:
		err =  ERROR_OUTPUT % (line_number, "EDR with EBT and drink number already exists.", line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return

	edr = ExperimentDrink()
	edr.ebt = ebt

	data_fields = data_list[FIELDS_INDEX[0]:FIELDS_INDEX[1]]

	for i, field in enumerate(fields):
		if data_fields[i] != '':
			setattr(edr, field, data_fields[i])

	try:
		edr.full_clean()

	except Exception as e:
		err =  ERROR_OUTPUT % (line_number, e, line)
		if dump_file:
			dump_file.write(err + '\n')
		else:
			print err
		return
	edr.save()	

def load_edr_one_file(file_name, dex):
	fields = (
		'edr_number',
		'edr_start_time',
		'edr_end_time',
		'edr_length',
		'edr_idi',
		'edr_volume'
		)
	FIELDS_INDEX = (2,8) #[2,8) => 2,3,4,5,6,7
	MONKEY_DATA_INDEX = 0
	BOUT_NUMBER_DATA_INDEX = 1
	DRINK_NUMBER_DATA_INDEX = 2

	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line_number, line in enumerate(read_data[1:], start=1):
			data = line.split("\t")
			if data[MONKEY_DATA_INDEX] == '28479':
				continue
			try:
				monkey = Monkey.objects.get(mky_real_id=data[MONKEY_DATA_INDEX])
			except:
				print ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
				continue

			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey, drinking_experiment=dex)
			if mtds.count() == 0:
				print ERROR_OUTPUT % (line_number, "MonkeyToDrinkingExperiment does not exist.", line)
				continue
			if mtds.count() > 1:
				print ERROR_OUTPUT % (line_number, "More than one MTD.", line)
				continue
			mtd = mtds[0]

			ebts = ExperimentBout.objects.filter(mtd=mtd, ebt_number = data[BOUT_NUMBER_DATA_INDEX])
			if ebts.count() == 0:
				print ERROR_OUTPUT % (line_number, "EBT does not exist.", line)
				continue
			if ebts.count() > 1:
				print ERROR_OUTPUT % (line_number, "More than one EBT.", line)
				continue
			ebt = ebts[0]

			edrs = ExperimentDrink.objects.filter(ebt=ebt, edr_number = data[DRINK_NUMBER_DATA_INDEX])
			if edrs.count() != 0:
				print ERROR_OUTPUT % (line_number, "EDR with EBT and drink number already exists.", line)
				continue

			edr = ExperimentDrink()
			edr.ebt = ebt

			data_fields = data[FIELDS_INDEX[0]:FIELDS_INDEX[1]]

			for i, field in enumerate(fields):
				if data_fields[i] != '':
					setattr(edr, field, data_fields[i])

			try:
				edr.full_clean()

			except Exception as e:
				print ERROR_OUTPUT % (line_number, e, line)
				continue
			edr.save()	

def load_edrs_and_ebts_all_from_one_file(cohort_name, dex_type, file_name, bout_index=1, drink_index=2, create_dex=False, create_mtd=False, dump_file=False):
	if not dex_type in DexTypes:
		raise Exception("'%s' is not an acceptable drinking experiment type.  Please choose from:  %s" % (dex_type, DexTypes))

	""" Input file may start with header, but ONLY if entry[1] == 'Date'! """
	if dump_file:
		_filename = file_name.split('/')
		_filename.reverse()
		dump_file = open(_filename[0] + '-output.txt', 'w')
	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)
	bouts = list()
	drinks = list()
	last_date = None
	with open(file_name, 'r') as f:
		data = f.read()
		data = string.replace(data, '\r\n', '\n')
		data = string.replace(data, '\r', '\n')
		s =data.split('\n')

		for line_number, line in enumerate(s):
			if not line:
				continue
			entry = line.split("\t")
			if entry[1] == 'Date':
				continue
			date = __get_datetime_from_steve(entry[1])
			if last_date != date:
				dexs = DrinkingExperiment.objects.filter(cohort=cohort,dex_type=dex_type,dex_date=date)
				if dexs.count() == 0:
					if create_dex:
						dex = DrinkingExperiment(cohort=cohort,dex_type=dex_type,dex_date=date)
						dex.save()
						dexs = list()
						dexs.append(dex)
					else:
						err = "DEX does not exist: %s" % entry
						if dump_file:
							dump_file.write(err + '\n')
						else:
							print err
						continue
				if len(dexs) > 1:
					err = "More than one DEX: %s" % entry
					if dump_file:
						dump_file.write(err + '\n')
					else:
						print err
					continue
				dex = dexs[0]

			if entry[10].strip() == 'BoutRec':
				bouts.append((dex, line_number, line, entry[2:-1]))
			elif entry[10].strip() == 'DrinkRec':
				drinks.append((dex, line_number, line, entry[2:-1]))
			else:
				err = "unknown format at line %d -->%s<--" % (line_number, line)
				if dump_file:
					dump_file.write(err + '\n')
				else:
					print err
				continue
			last_date = date
		if dump_file:
			dump_file.flush()
#	return  bouts, drinks
	print "Loading bouts ..."
	for (dex, line_number, line, bout) in bouts:
		load_ebt_one_inst(bout, line_number, create_mtd, dex, line, bout_index=bout_index, dump_file=dump_file)
		if dump_file:
			dump_file.flush()
	print "Loading drinks ..."
	for (dex, line_number, line, drink) in drinks:
		load_edr_one_inst(drink, dex, line_number, line, bout_index=bout_index, drink_index=drink_index, dump_file=dump_file)
		if dump_file:
			dump_file.flush()
	if dump_file:
		dump_file.close()

def load_edrs_and_ebts(cohort_name, dex_type, file_dir, create_mtd=False):
	if not dex_type in DexTypes:
		raise Exception("'%s' is not an acceptable drinking experiment type.  Please choose from:  %s" % (dex_type, DexTypes))
	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)
	entries = os.listdir(file_dir)
	bouts = list()
	drinks = list()
	print "Reading list of files in folder..."
	for entry in entries:
		file_name = os.path.join(file_dir, entry)
		if not os.path.isdir(file_name):
			m = re.match(r'([0-9]+_[0-9]+_[0-9]+)_(bout|drink)', entry)
			if not m:
				m = re.match(r'([0-9]+_[0-9]+_[0-9]+)_(bout|drink).*', entry)
				if not m:
					print "Invalid file name format: %s" % entry
					continue
			try:
				day = dt.strptime(m.group(1), "%Y_%m_%d")
			except:
				print "Invalid date format in file name: %s" % entry
				continue
			type = m.group(2)
			dexs = DrinkingExperiment.objects.filter(cohort=cohort,dex_type=dex_type,dex_date=day)
			if dexs.count() == 0:
				print "DEX does not exist: %s" % entry
				continue
			if dexs.count() > 1:
				print "More than one DEX: %s" % entry
				continue
			dex = dexs[0]
			if type == 'bout':
				bouts.append((dex, file_name))
			else:
				drinks.append((dex, file_name))

	for (dex, bout) in bouts:
		print "Loading %s..." % bout
		load_ebt_one_file(bout, dex, create_mtd)
	for (dex, drink) in drinks:
		print "Loading %s..." % drink
		load_edr_one_file(drink, dex)

def convert_excel_time_to_datetime(time_string):
	DATE_BASE = dt(day=1, month=1, year=1904)
	SECONDS_BASE = 24*60*60
	data_days = int(time_string.split('.')[0])
	date_time = float("0.%s" % time_string.split('.')[1])
	seconds = round(date_time * SECONDS_BASE)
	return DATE_BASE + timedelta(days=data_days, seconds=seconds)

def parse_left_right(side_string):
	if string.count(side_string, "Left") != 0:
		return LeftRight.Left
	elif string.count(side_string, "Right") != 0:
		return LeftRight.Right
	else:
		return None

@commit_on_success
def load_eev_one_file(file_name, dex_type, date):

	fields = (
#		'eev_occurred',
		'eev_dose',
		'eev_panel',
		'eev_fixed_time',
		'eev_experiment_state',
#		'eev_event_type',
		'eev_session_time',
		'eev_segement_time',
		'eev_pellet_time',
#		'eev_etoh_side',
		'eev_etoh_volume',
		'eev_etoh_total',
		'eev_etoh_elapsed_time_since_last',
#		'eev_veh_side',
		'eev_veh_volume',
		'eev_veh_total',
		'eev_veh_elapsed_time_since_last',
		'eev_scale_string',
#		'eev_hand_in_bar',
		'eev_blank',
		'eev_etoh_bout_number',
		'eev_etoh_drink_number',
		'eev_veh_bout_number',
		'eev_veh_drink_number',
		'eev_timing_comment',		
			)
	FIELDS_INDEX = (
				(2,6),
				(9,12),
				(13,16),
				(17,21),
				(22,28),
				)
	MONKEY_DATA_INDEX = 0
	DATE_DATA_INDEX = 1
	DATA_TYPE_T_INDEX = 8
	DATA_TYPE_P_INDEX = 7
	DATA_TYPE_D_INDEX = 6
	DATA_ETOH_SIDE_INDEX = 11
	DATA_VEH_SIDE_INDEX = 15
	DATA_HIB_INDEX = 20

	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line_number, line in enumerate(read_data[1:], start=1):
			data = line.split("\t")
			if data[MONKEY_DATA_INDEX] == '28479':
				continue
			try:
				monkey = Monkey.objects.get(mky_real_id=data[MONKEY_DATA_INDEX])
			except:
				msg = ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
				logging.warning(msg)
				continue

			eev_date = convert_excel_time_to_datetime(data[DATE_DATA_INDEX])
			if date.date() != eev_date.date():
				msg = ERROR_OUTPUT % (line_number, "Filename date does not match line date.  Will use line date. filename_date=%s" % str(date), line)
				logging.info(msg)

#			eevs = ExperimentEvent.objects.filter(monkey=monkey, dex_type=dex_type, eev_source_row_number=line_number, eev_occurred=eev_date)
#			if eevs.count() != 0:
#				msg = ERROR_OUTPUT % (line_number, "EEV with monkey, dex_type, date occurred and source row number already exists.", line)
#				logging.debug(msg)
#				continue

			eev = ExperimentEvent()
			eev.monkey = monkey
			eev.dex_type = dex_type
			eev.eev_occurred = eev_date
			eev.eev_event_type = data[DATA_TYPE_D_INDEX] or data[DATA_TYPE_P_INDEX] or data[DATA_TYPE_T_INDEX]
			eev.eev_veh_side = parse_left_right(data[DATA_VEH_SIDE_INDEX])
			eev.eev_etoh_side = parse_left_right(data[DATA_ETOH_SIDE_INDEX])
			eev.eev_source_row_number = line_number

			if data[DATA_HIB_INDEX] == 'X':
				eev.eev_hand_in_bar = False
			else:
				eev.eev_hand_in_bar = True

			data_fields = list()
			for low_ind, high_ind in FIELDS_INDEX:
				data_fields.extend(data[low_ind:high_ind])

			for i, field in enumerate(fields):

				if data_fields[i] != '':
					setattr(eev, field, data_fields[i])

			try:
				eev.full_clean()

			except Exception as e:
				msg = ERROR_OUTPUT % (line_number, e, line)
				print msg
				logging.error(msg)
				continue
			eev.save()	

def load_eevs(file_dir, dex_type):
	if not dex_type in DexTypes:
		raise Exception("'%s' is not an acceptable drinking experiment type.  Please choose from:  %s" % (dex_type, DexTypes))

#	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)
	entries = os.listdir(file_dir)
	print "Reading list of files in folder..."
	for entry in entries:
		file_name = os.path.join(file_dir, entry)
		if not os.path.isdir(file_name):
			m = re.match(r'([0-9]+_[0-9]+_[0-9]+)_', entry)
			if not m:
				msg = "Invalid file name format: %s" % entry
				logging.warning(msg)
				continue
			try:
				day = dt.strptime(m.group(1), "%Y_%m_%d")
			except:
				msg =  "Invalid date format in file name: %s" % entry
				logging.warning(msg)
				continue
			msg = "Loading %s..." % file_name
			logging.debug(msg)
			print msg
			load_eev_one_file(file_name, dex_type, day)

def load_necropsy_summary(filename):
	"""
		This function will load a csv file in the format:
		row[0]	= matrr_number or mky_real_id
		(( if row[0] is a mky_real_id and row[1] is "primary_cohort" the function will add 2 to all row indexes
		row[1]	= cohort_broad_title 	# unused
		row[2]	= species 				# unused
		row[3]	= cohort_number 		# unused
		row[4]	= sex 					# unused
		row[5]	= birth_date (string, in format '%m/%d/%y' = 1/1/01)
		row[6]	= necropsy_date (string, in format '%m/%d/%y' = 1/1/01)
		row[7]	= age_at_necropsy
		row[8]	= date_of_etoh_onset (string, in format '%m/%d/%y' = 1/1/01)
		row[9]	= age_onset_etoh
		row[10]	= etoh_4%_ind
		row[11]	= etoh_4%_22hr
		row[12]	= lifetime_etoh_4%_mls
		row[13]	= lifetime etoh grams
		row[14]	= sum_g/kg_ind
		row[15]	= sum_g/kg_22hr
		row[16]	= lifetime_sum_g/kg
		row[17]	= 6 mos start (string, in format '%m/%d/%y' = 1/1/01)
		row[18]	= 6 mos end (string, in format '%m/%d/%y' = 1/1/01)
		row[19]	= 12 mos end (string, in format '%m/%d/%y' = 1/1/01)
		row[20]	= 22hr_6mos_avg_g/kg
		(row[21] = '22hr_2nd_6mos_avg_g/kg' if present, column_offset += 1 starting from this row)
		row[21]	= 22hr_12mos_avg_g/kg
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	columns = csv_infile.next()
	pre_columns_offset = 0
	unsure = False
	try:
		if columns[1] == 'matrr_number' and columns[2] == 'primary_cohort':
			pre_columns_offset = 2
		else:
			unsure = True
	except:
		csv_infile = csv.reader(open(filename, 'rU'), delimiter="\t")
		columns = csv_infile.next()
		if columns[1] == 'matrr_number' and columns[2] == 'primary_cohort':
			pre_columns_offset = 2
	if unsure:
			raise Exception("Unsure of format, investigate further and update this function.")

	if columns[21+pre_columns_offset] == '22hr_2nd_6mos_avg_g/kg':
		extra_22hr_column = True
	else:
		extra_22hr_column = False

	for row in csv_infile:
		columns_offset = pre_columns_offset
		if row[0]:
			try: # dont offset these columns, they should always be a monkey number of some sort (hopefully)
				monkey = Monkey.objects.get(pk=row[0])
			except Monkey.DoesNotExist:
				try:
					monkey = Monkey.objects.get(mky_real_id=row[0])
					column_offset = 2 #
				except Monkey.DoesNotExist:
					raise Exception("No such monkey:  %s" % str(row[0]))
			try:
				nec_sum = monkey.necropsy_summary
			except NecropsySummary.DoesNotExist:
				nec_sum = NecropsySummary(monkey=monkey)

			monkey.mky_birthdate 			= datetime.datetime.strptime(row[5+columns_offset], '%m/%d/%y')
			monkey.mky_necropsy_start_date 	= datetime.datetime.strptime(row[6+columns_offset], '%m/%d/%y')
			monkey.mky_age_at_necropsy 		= row[7]
			monkey.save()

			nec_sum.ncm_etoh_onset 				= datetime.datetime.strptime(row[8+columns_offset], '%m/%d/%y')
			nec_sum.ncm_age_onset_etoh 			= row[9+columns_offset]
			nec_sum.ncm_etoh_4pct_induction 	= row[10+columns_offset] if row[10+columns_offset] != "control" else 0
			nec_sum.ncm_etoh_4pct_22hr			= row[11+columns_offset] if row[11+columns_offset] != "control" else 0
			nec_sum.ncm_etoh_4pct_lifetime		= row[12+columns_offset] if row[12+columns_offset] != "control" else 0
			nec_sum.ncm_etoh_g_lifetime			= row[13+columns_offset] if row[13+columns_offset] != "control" else 0
			nec_sum.ncm_sum_g_per_kg_induction	= row[14+columns_offset] if row[14+columns_offset] != "control" else 0
			nec_sum.ncm_sum_g_per_kg_22hr		= row[15+columns_offset] if row[15+columns_offset] != "control" else 0
			nec_sum.ncm_sum_g_per_kg_lifetime	= row[16+columns_offset] if row[16+columns_offset] != "control" else 0
			nec_sum.ncm_6_mo_start 				= datetime.datetime.strptime(row[17+columns_offset], '%m/%d/%y')
			nec_sum.ncm_6_mo_end 				= datetime.datetime.strptime(row[18+columns_offset], '%m/%d/%y')
			nec_sum.ncm_12_mo_end 				= datetime.datetime.strptime(row[19+columns_offset], '%m/%d/%y')
			nec_sum.ncm_22hr_6mo_avg_g_per_kg	= row[20+columns_offset] if row[20+columns_offset] != "control" else 0
			if extra_22hr_column:
				nec_sum.ncm_22hr_2nd_6mos_avg_g_per_kg = row[21+columns_offset] if row[21+columns_offset] != "control" else 0
				columns_offset += 1
			nec_sum.ncm_22hr_12mo_avg_g_per_kg	= row[21+columns_offset] if row[21+columns_offset] != "control" else 0
			nec_sum.save()

def load_metabolites(filename):
	"""
		This function will load a csv file in the format
		row[0]	= Biochemical
		row[1]	= Super_Pathway
		row[2]	= Sub_Pathway
		row[3]	= Comp_ID
		row[4]	= Platform
		row[5]	= RI
		row[6]	= Mass
		row[7]	= CAS
		row[8]	= KEGG
		row[9]	= HMDB_ID
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	columns = csv_infile.next()
	for row in csv_infile:
		met_dict = {}
		if row[0]:
			met_dict['met_biochemical'] 	= row[0]
			met_dict['met_super_pathway'] 	= row[1]
			met_dict['met_sub_pathway'] 	= row[2]
			met_dict['met_comp_id'] 		= row[3]
			met_dict['met_platform'] 		= row[4]
			met_dict['met_ri'] 				= row[5]
			met_dict['met_mass'] 			= row[6]
			met_dict['met_cas'] 			= row[7]
			met_dict['met_kegg'] 			= row[8]
			met_dict['met_hmdb_id'] 		= row[9]

			metabolite, isnew = Metabolite.objects.get_or_create(**met_dict)
			if isnew:
				metabolite.save()

def load_monkey_metabolites(filename, values_normalized):
	"""
	Alright so, the format of the file they gave me is gonna be tough to parse through.  Scientists _love_ inverting axes in their spreadsheets.

	The first 8 rows of Column0 describe the monkey and the metabolite sample scenario.  They are:
	col0row0 = SAMPLE_NAME			# columns 1-30 hold 'OHSU-000001' , 'OHSU-000002', etc.
	col0row1 = SAMPLE_ID			# columns 1-30 hold unique, incrementing 6-digit integers
	col0row2 = CLIENT_INDENTIFIER	# columns 1-30 hold "1-<number>" where <number> == mky_real_id == row 6
	col0row3 = GROUP				# columns 1-30 hold a single digit integer which increments based on GROUP_ID.  1 == baseline, 2 = 6 months EtOH, etc
	col0row4 = DATE					# date the sample was taken
	col0row5 = TREATMENT			# rephrasing of GROUP_ID. Group_id's 'baseline' value is stored as 'ethanol naive' in these cells.
	col0row6 = SUBJECT ID			# mky_real_id
	col0row7 = GROUP_ID 			# described above -.-
	---
	For rows 8 thru *, the col0 value stored is the metabolite name (Metabolite.met_biochemical).  The value stored in col1 - col30 is the metabolite value.

	Lets figure out how to parse this -.-
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	monkey_datas = {}
	monkey_metabolite_datas = {}
	for row in csv_infile:
		if row[0]:
			if row[0] == 'SAMPLE_NAME':
				for idx, cell in enumerate(row[1:]):
					ts_dict = {'mmb_sample_name': cell}
					monkey_datas[idx] = ts_dict
			elif row[0] == 'SAMPLE_ID':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mmb_sample_id'] = cell
			elif row[0] == 'CLIENT_IDENTIFIER':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mmb_client_identifier'] = cell
			elif row[0] == 'GROUP':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mmb_group'] = cell
			elif row[0] == 'DATE':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mmb_date'] = datetime.datetime.strptime(cell, '%m/%d/%y')
			elif row[0] == 'TREATMENT':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mmb_treatment'] = cell
			elif row[0] == 'SUBJECT_ID':
				for idx, cell in enumerate(row[1:]):
					monkey = Monkey.objects.get(mky_real_id=cell)
					monkey_datas[idx]['monkey'] = monkey
					monkey_datas[idx]['mmb_subject_id'] = cell
			elif row[0] == 'GROUP_ID':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mmb_group_id'] = cell
			else:
				metabolite = Metabolite.objects.get(met_biochemical=row[0])
				metabolite_row = []
				for idx, cell in enumerate(row[1:]):
					metabolite_row.append((monkey_datas[idx], metabolite, cell))
				monkey_metabolite_datas[row[0]] = metabolite_row

	for index in monkey_metabolite_datas:
		for metabolite_row in monkey_metabolite_datas[index]:
			monkey_data 	= metabolite_row[0]
			metabolite 		= metabolite_row[1]
			met_value 		= metabolite_row[2] if metabolite_row[2] else None
			normalized		= True if values_normalized is True else False
			monkey_metabolite, isnew = MonkeyMetabolite.objects.get_or_create(metabolite=metabolite, mmb_value=met_value, mmb_is_normalized=normalized, **monkey_data)
			if isnew:
				monkey_metabolite.save()

def load_proteins(filename):
	"""
		This function will load a csv file in the format
		row[0]	= protein abbreviation (pro_abbrev)
		row[1]	= full protein name (pro_name)
		row[2]	= concentration units (pro_units)
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	columns = csv_infile.next()
	for row in csv_infile:
		pro_dict = {}
		if row[0]:
			pro_dict['pro_abbrev'] 	= row[0]
			pro_dict['pro_name'] 	= row[1]
			pro_dict['pro_units'] 	= row[2]

			protein, isnew = Protein.objects.get_or_create(**pro_dict)
			if isnew:
				protein.save()

def load_monkey_proteins(filename):
	"""
		row[0] = mky_real_id (monkey.mky_real_id)
		row[1] = date collected (mpn_date)
			the rest of the columns are proteins, header label is Protein.pro_abbrev
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	columns = csv_infile.next()
	junk = columns.pop(0) # take out the monkey column label
	junk = columns.pop(0) # take out the date column label

	proteins = []
	for column in columns:
		proteins.append(Protein.objects.get(pro_abbrev=column))

	monkey_protein_datas = []
	for row in csv_infile:
		if row[0]:
			monkey = Monkey.objects.get(mky_real_id=row.pop(0))
			mpn_date = datetime.datetime.strptime(row.pop(0), '%m/%d/%y')
			for index, value in enumerate(row):
				monkey_protein = {}
				monkey_protein['monkey'] = monkey
				monkey_protein['mpn_date'] = mpn_date
				monkey_protein['protein'] = proteins[index]
				monkey_protein['mpn_value'] = value
				monkey_protein_datas.append(monkey_protein)

	for mpn in monkey_protein_datas:
		monkey_protein, isnew = MonkeyProtein.objects.get_or_create(**mpn)
		if isnew:
			monkey_protein.save()

def load_institutions(file_name):
	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line in read_data:
			institution, isnew = Institution.objects.get_or_create(ins_institution_name=line.rstrip())
			if isnew:
				institution.save()
		institution, isnew = Institution.objects.get_or_create(ins_institution_name="Non-UBMTA Institution") # required to exist for MTA operations
		if isnew:
			institution.save()

def load_cohort_timelines(filename, delete_replaced_cvts=False):
	"""
		rows 0, 1 and 4 are ignored
		row[2] = cohort number
		row[3] = cohort species
			the rest of the columns are events, cells are dates of that event for the cohort described in rows 2/3, in format '%m/%d/%y'
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	columns = csv_infile.next() # empty row, row[0] warning of date format
	columns = csv_infile.next() # column names

	for idx, column in enumerate(columns):
		if idx <= 4:
			continue
		evt, is_new = EventType.objects.get_or_create(evt_name=column)
		if is_new:
			evt.save()
			print "New Event Type: %s" % evt.evt_name

	for row in csv_infile:
		cohort = Cohort.objects.filter(coh_cohort_name__icontains=row[2]).filter(coh_cohort_name__icontains=row[3])
		if cohort.count() == 1:
			cohort = cohort[0]
		else:
			raise Exception("Improper cohort filter count!")

		if delete_replaced_cvts:
			cvts = CohortEvent.objects.filter(cohort=cohort)
			count = cvts.count()
			cvts.delete()
			print "%d CohortEvents DELETED!" % count

		for idx, event in enumerate(columns):
			if idx <= 4:
				continue
			elif row[idx]:
				event_type = EventType.objects.get(evt_name__contains=event)
				cev_date = datetime.datetime.strptime(row[idx], '%m/%d/%y')
				cev, is_new = CohortEvent.objects.get_or_create(cohort=cohort, event=event_type, cev_date=cev_date)
				if is_new:
					cev.save()
					print "New CohortEvent: %s" % str(cev)

def assign_cohort_institutions():
	wfu = Institution.objects.get(ins_institution_name='Wake Forest University')
	ohsu = Institution.objects.get(ins_institution_name='Oregon Health Sciences University, Technology Management')

	cohort = Cohort.objects.get(coh_cohort_name='INIA Cyno 1')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Cyno 2')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Cyno 3')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Cyno 8')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 1')
	cohort.institution = wfu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 2')
	cohort.institution = wfu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 4')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 5')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6a')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 6b')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7a')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')
	cohort.institution = ohsu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Vervet 1')
	cohort.institution = wfu
	cohort.save()

	cohort = Cohort.objects.get(coh_cohort_name='INIA Vervet 2')
	cohort.institution = wfu
	cohort.save()

def populate_mtd_fields(queryset=None):
	qs = queryset if queryset else MonkeyToDrinkingExperiment.objects.all()
	for mtd in qs:
		mtd.populate_max_bout_hours()

def load_brain_monkeyimages(directory):
	import os
	for file in os.listdir(directory):
		if file[-3:].lower() == 'png':
			filename, extension = file.split('.')
			mky_number_ish = filename.split('-')[-1]
			mky_number = mky_number_ish[-5:]
			try:
				monkey = Monkey.objects.get(mky_real_id=mky_number)
			except Monkey.DoesNotExist:
				print "Monkey does not exist:  " + mky_number
				continue

			mig = MonkeyImage.objects.create(monkey=monkey, method='__brain_image')

			filename = '/tmp/' + filename
			thumb_path = filename + '-thumb.jpg'
			image_file = Image.open(directory+file)
			image_file.thumbnail((240, 240), Image.ANTIALIAS)
			image_file.save(thumb_path)

			mig.image = File(open(directory+file, 'r'))
			mig.save()
			mig.thumbnail = File(open(thumb_path, 'r'))
			mig.save()
			html_frag = mig._build_html_fragment('NO MAP', add_footer=False)
			mig.html_fragment = File(open(html_frag))
			mig.save()

def create_7b_control_monkeys():
	import datetime
	cohort = Cohort.objects.get(coh_cohort_name='INIA Rhesus 7b')
	monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
					mky_real_id=24818,
					mky_birthdate=datetime.date(2005, 3, 13),
					mky_necropsy_start_date=datetime.date(2012, 7, 23),
					mky_age_at_necropsy='7 yrs 4 mos 10 days',
					)
	monkey.save()
	monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
					mky_real_id=25207,
					mky_birthdate=datetime.date(2005, 6, 1),
					mky_necropsy_start_date=datetime.date(2012, 7, 27),
					mky_age_at_necropsy='7 yrs 1 mos 26 days',
					)
	monkey.save()
	monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
					mky_real_id=25407,
					mky_birthdate=datetime.date(2005, 4, 1),
					mky_necropsy_start_date=datetime.date(2012, 7, 26),
					mky_age_at_necropsy='7 yrs 3 mos 25 days',
					)
	monkey.save()
	monkey = Monkey(cohort=cohort, mky_drinking=False, mky_study_complete=False, mky_gender='M', mky_stress_model='',
					mky_real_id=25526,
					mky_birthdate=datetime.date(2005, 2, 1),
					mky_necropsy_start_date=datetime.date(2012, 7, 24),
					mky_age_at_necropsy='7 yrs 5 mos 23 days',
					)
	monkey.save()

def load_hormone_data(file_name, overwrite=False, header=True):
	fields = (
		'mhm_date', # 0
		'monkey',	# 1
		'mhm_cort',	# 2
		'mhm_acth',	# 3
		'mhm_t',	# 4
		'mhm_doc',	# 5
		'mhm_ald',	# 6
		'mhm_dheas',# 7
		'__cohort',	# 8 Ignored, not a real data field.
		)
	FIELDS_INDEX = (2,8) #(2,8) => 2,3,4,5,6,7
	with open(file_name, 'r') as f:
		read_data = f.read()
		if '\r' in read_data:
			read_data = read_data.split('\r')
		elif '\n' in read_data:
			read_data = read_data.split('\n')
		else:
			raise Exception("WTF Line endings are in this file?")
		offset = 1 if header else 0
		for line_number, line in enumerate(read_data[offset:]):
			data = line.split("\t")
			try:
				mhm_date = dt.strptime(data[0], "%m/%d/%y")
				monkey = Monkey.objects.get(mky_real_id=data[1])
			except Monkey.DoesNotExist:
				print ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
				continue
			except Exception as e:
				print ERROR_OUTPUT % (line_number, "Wrong date format", line)
				continue
			mhm, is_new = MonkeyHormone.objects.get_or_create(monkey=monkey, mhm_date=mhm_date)
			if not is_new and not overwrite:
				print ERROR_OUTPUT % (line_number, "Monkey+Date exists", line)
				continue

			data_fields = data[FIELDS_INDEX[0]:FIELDS_INDEX[1]]
			model_fields = fields[FIELDS_INDEX[0]:FIELDS_INDEX[1]]
			for i, field in enumerate(model_fields):
				if data_fields[i] != '':
					setattr(mhm, field, data_fields[i])

			try:
				mhm.full_clean()
			except Exception as e:
				print ERROR_OUTPUT % (line_number, e, line)
				continue
	print "Data load complete."

def load_bec_data(file_name, overwrite=False, header=True):
	def format_time(unformatted):
		""" Converts "hh:MM AM" into HH:MM """
		if 'am' in unformatted.lower() or 'pm' in unformatted.lower():
			time, afternoon = unformatted.split(' ')
			hh, MM = time.split(":")
			if afternoon.lower() == 'pm':
				HH = int(hh) + 12
			else:
				HH = int(hh)
			HH = 12 if HH == 24 else HH
			return "%s:%s" % (str(HH), str(MM))
		return unformatted

	fields = (
		'mky_real_id',			# 0
		'mky_id',				# 1
		'bec_collect_date',		# 2
		'bec_run_date',			# 3
		'bec_exper',			# 4
		'bec_exper_day',		# 5
		'bec_session_start',	# 6
		'bec_sample',			# 7
		'bec_weight',			# 8
		'bec_vol_etoh',			# 9
		'bec_gkg_etoh',			# 10
		'bec_daily_gkg_etoh',	# 11
		'__(bec_gkg_etoh - bec_daily_gkg_etoh)', # 12, this column is ignored
		'bec_mg_pct',			# 13
		)
	FIELDS_INDEX = (4,14) #(4,14) => 4,5,6,7,8,9,10,11,12,13
	with open(file_name, 'r') as f:
		read_data = f.read()
		if '\r' in read_data:
			read_data = read_data.split('\r')
		elif '\n' in read_data:
			read_data = read_data.split('\n')
		else:
			raise Exception("WTF Line endings are in this file?")
		offset = 1 if header else 0
		for line_number, line in enumerate(read_data[offset:]):
			data = line.split("\t")
			if not data[0]:
				continue
			try:
				monkey = Monkey.objects.get(mky_real_id=data[0])
#				assert monkey.pk == int(data[1])
			except Monkey.DoesNotExist:
				print ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
				continue

			bec_collect_date = __get_datetime_from_steve(data[2])
			bec_run_date = __get_datetime_from_steve(data[3])
			if not bec_collect_date or not bec_run_date:
				print ERROR_OUTPUT % (line_number, "Wrong date format", line)
				continue

			bec = MonkeyBEC.objects.filter(monkey=monkey, bec_collect_date=bec_collect_date, bec_run_date=bec_run_date)
			if bec:
				if overwrite:
					bec.delete()
					bec = MonkeyBEC(monkey=monkey, bec_collect_date=bec_collect_date, bec_run_date=bec_run_date)
				else:
					print ERROR_OUTPUT % (line_number, "Monkey+Date exists", line)
					continue
			else:
				bec = MonkeyBEC(monkey=monkey, bec_collect_date=bec_collect_date, bec_run_date=bec_run_date)

			data_fields = data[FIELDS_INDEX[0]:FIELDS_INDEX[1]]
			model_fields = fields[FIELDS_INDEX[0]:FIELDS_INDEX[1]]
			for i, field in enumerate(model_fields):
				if model_fields[i].startswith('__'):
					continue
				if data_fields[i] != '':
					if i in (2, 3): # time fields, fields[6] and fields[7]
						setattr(bec, field, format_time(data_fields[i]))
					else:
						setattr(bec, field, data_fields[i])

			try:
				bec.full_clean()
			except Exception as e:
				print ERROR_OUTPUT % (line_number, e, line)
				continue
			bec.save()
	print "Data load complete."

def populate_mky_species():
	for coh in Cohort.objects.exclude(coh_cohort_name__icontains='assay'):
		coh.monkey_set.all().update(mky_species=coh.coh_species)

def load_mbb_images(image_dir):
	def create_mbb(monkey, image_path):
		##  Verify argument is actually a monkey
		if not isinstance(monkey, Monkey):
			try:
				monkey = Monkey.objects.get(pk=monkey)
			except Monkey.DoesNotExist:
				try:
					monkey = Monkey.objects.get(mky_real_id=monkey)
				except Monkey.DoesNotExist:
					print("That's not a valid monkey:  %s." % monkey)
					return
		_file = File(open(image_path, 'r'))
		mig, is_new = MonkeyImage.objects.get_or_create(monkey=monkey, method='__brain_image')
		if not is_new:
			return
		mig.image = _file
		mig.save()
		mig._build_html_fragment(None, add_footer=False, save_fragment=True)

		for i in range(1, 16, 1):
			mbb, is_new = MonkeyBrainBlock.objects.get_or_create(monkey=monkey, mbb_hemisphere='L', brain_image=mig, mbb_block_name='Block %02d' % i)
			mbb, is_new = MonkeyBrainBlock.objects.get_or_create(monkey=monkey, mbb_hemisphere='R', brain_image=mig, mbb_block_name='Block %02d' % i)

		brain_tissues = TissueType.objects.filter(category__cat_name__icontains='brain')
		mbb, is_new = MonkeyBrainBlock.objects.get_or_create(monkey=monkey, mbb_hemisphere='L', brain_image=mig, mbb_block_name='Block 15')
		mbb.assign_tissues(brain_tissues)
		mbb, is_new = MonkeyBrainBlock.objects.get_or_create(monkey=monkey, mbb_hemisphere='R', brain_image=mig, mbb_block_name='Block 15')
		mbb.assign_tissues(brain_tissues)

	recomp = re.compile('^.*([0-9]{5}).png$')
	files = os.listdir(image_dir)
	for file in files:
		if file.endswith('.png'):
			real_id = recomp.match(file).group(1)
			create_mbb(real_id, os.path.join(image_dir, file))

def load_monkey_exceptions(file_name, overwrite=False, header=True):
	"""
	Pre-7b format:
	"Cohort","Experiment","File Errors Corrected","Day not used at all","BEC for Lifetime Intake only, no behav","Date","animal","etoh intake (.04 conc)"
	"IniaRhesusMaleCoh4","Ind",,,"x","05/19/08",22215,377.2

	7b format:
	"Cohort","Experiment","File Errors Corrected","Day not used at all","BEC for Lifetime Intake only, no behav","Date","animal","etoh intake (.04 conc)", "2% etoh"
	"IniaRhesusMaleCoh4","Ind",,,"x","05/19/08",22215,377.2,"x"

	The "Cohort" column is gibberish, "INIARhesusMaleCoh7a"
	The "Experiment" column is either "ind" or "22hr"
	I don't yet know what "File errors Corrected" indicates, but its either "" or "x"
	I think "Day not used at all" flags should be deleted entirely, for serious forever.  Faulty mechanism or some such.
	"BEC for Lifetime Intake only" I think are exception days when monkeys were allowed to drink they knocked out the monkey with SpecialK or something
	"Date" format keeps changing.  use __get_datetime_From_steve()
	"Animal" == Monkey.mky_real_id
	I don't know exactly what "etoh intake" means.  I'm pretty sure it's the (corrected) volume of alcohol consumed.  This should allow me to delete bad records and keep accurate lifetime intake volumes
	"2% etoh" is a flag (""/"x") indicating this day the monkey received .02 conc alcohol instead of the normal .04 conc.
	"""
	csv_infile = csv.reader(open(file_name, 'rU'), delimiter=",")
	if header:
		columns = csv_infile.next()
	column_format = [
		'',
		'',
		'mex_file_corrected',
		'mex_excluded',
		'mex_lifetime',
		'',
		'',
		'mex_etoh_intake',
		'mex_2pct',
	]
	for line_number, row in enumerate(csv_infile):
		try:
			monkey = Monkey.objects.get(mky_real_id=row[6])
		except Monkey.DoesNotExist:
			msg = ERROR_OUTPUT % (line_number, "Monkey Does Not Exist", str(row))
			logging.error(msg)
			print msg
			continue
		except ValueError:
			msg = ERROR_OUTPUT % (line_number, "Monkey value isn't an integer", str(row))
			logging.error(msg)
			print msg
			continue

		date = __get_datetime_from_steve(row[5])
		if date is None:
			msg = ERROR_OUTPUT % (line_number, "Unknown Date Format", str(row))
			logging.error(msg)
			print msg
			continue

		exists = MonkeyException.objects.filter(monkey=monkey, mex_date=date).count()
		if exists >= 1 and not overwrite:
			msg = ERROR_OUTPUT % (line_number, "Exception Record Already Exists", str(row))
			logging.warning(msg)
			print msg
			continue

		if 'ind' in row[1].lower():
			stage = DexType.Ind
		elif row[1].lower() == '22hr':
			stage = DexType.OA
		else:
			msg = ERROR_OUTPUT % (line_number, "Unknown Experiment Stage", str(row))
			logging.error(msg)
			print msg
			continue

		mex = MonkeyException(monkey=monkey, mex_stage=stage, mex_date=date)
		for name, value in zip(column_format, row):
			if name and value:
				if str(value).lower() == 'x': # boolean flags
					value = True
				setattr(mex, name, value)

		try:
			mex.full_clean()
		except Exception as e:
			msg = ERROR_OUTPUT % (line_number, e, str(row))
			logging.error(msg)
			print msg
			continue

		mex.save()

def delete_wonky_monkeys():
	monkey_pks = [10043, 10050, 10053]
	models = [MonkeyToDrinkingExperiment, MonkeyBEC, ExperimentEvent, MonkeyImage]

	for model in models:
		for mky in monkey_pks:
			print "Deleting mky %d from table %s" % (mky, model.__name__)
			model.objects.filter(monkey=mky).delete()

def find_outlier_datapoints(cohort, stdev_min):
	search_models = [MonkeyToDrinkingExperiment, MonkeyBEC,]# ExperimentEvent, ExperimentBout, ExperimentDrink]
	search_field = ['monkey__cohort', 'monkey__cohort', ]#'monkey__cohort', 'mtd__monkey__cohort', 'mtd__ebt__monkey__cohort']

	field_types = [models.FloatField, models.IntegerField, models.BigIntegerField, models.PositiveIntegerField, models.PositiveSmallIntegerField, models.SmallIntegerField]

	for model, search in zip(search_models, search_field):
		search_field_names = list()
		for field in model._meta.fields:
			if type(field) in field_types:
				search_field_names.append(field.name)
		for _name in search_field_names:
			all_rows = model.objects.filter(**{search: cohort}).exclude(**{_name: None})
			if all_rows.count():
				all_values = all_rows.values_list(_name, flat=True)
				all_values = numpy.array(all_values)
				mean = all_values.mean()
				std = all_values.std()
				low_std = mean - stdev_min*std
				high_std = mean + stdev_min*std
				low_search_dict = {_name+"__lt": low_std}
				high_search_dict = {_name+"__gt": high_std}
				low_outliers = all_rows.filter(**low_search_dict)
				high_outliers = all_rows.filter(**high_search_dict)

				if low_outliers or high_outliers:
					output_file = "%d.%s__%s-outliers.csv" % (cohort, model.__name__, _name)
					output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
					header = ["Outlier Value", "Mean value", "StDev"]
					all_field_names = [f.name for f in model._meta.fields]
					header.extend(all_field_names)
					output.writerow(header)
					for out in low_outliers|high_outliers:
						row = list()
						row.append(getattr(out, _name))
						row.append(mean)
						row.append(std)
						for f in all_field_names:
							row.append(getattr(out, f))
						output.writerow(row)
			else:
				print "No data: %s " % _name

	print 'done'

def populate_seconds_since_pellet(monkeys=None):
	if not monkeys:
		monkeys = ExperimentEvent.objects.filter(eev_pellet_elapsed_time_since_last=None).values_list('monkey', flat=True).distinct()
	for monkey in monkeys:
		results = list()
		eevs = ExperimentEvent.objects.filter(monkey=monkey, eev_pellet_elapsed_time_since_last=None).values('eev_id', 'eev_occurred', 'eev_event_type').order_by('eev_occurred')
		last_pellet = None
		for eev in eevs:
			if last_pellet == None:
				diff_seconds = 0
			else:
				diff_seconds = (eev['eev_occurred'] - last_pellet['eev_occurred']).seconds

			results.append((eev['eev_id'], diff_seconds))

			if eev['eev_event_type'] == ExperimentEventType.Pellet:
				last_pellet = eev
		for r in results:
			eev = ExperimentEvent.objects.get(pk=r[0])
			eev.eev_pellet_elapsed_time_since_last = r[1]
			eev.save()

def dump_tissue_inventory_csv(cohort):
	"""
		This function will dump the browse inventory page to CSV
		It writes columns == monkey, row == tissue.
		Cells where the tissue exists are given "Exists", non-existent tissues are left blank.
	"""
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			print("That's not a valid cohort.")
			return False, False

	filename = str(cohort).replace(' ', '_') + "-Inventory.csv"
	output = csv.writer(open(filename, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	columns = ["Tissue Type \ Monkey"]
	columns.extend(["%s/%s" % (str(m.pk), str(m.mky_real_id))  for m in cohort.monkey_set.all().order_by('pk')])
	output.writerow(columns)

	for tst in TissueType.objects.all().order_by('category__cat_name', 'tst_tissue_name'):
		row = [tst.tst_tissue_name]
		for mky in cohort.monkey_set.all().order_by('pk'):
			availability = tst.get_monkey_availability(mky)
			if availability == Availability.Unavailable:
				row.append("")
			else:
				row.append("Exists")
		output.writerow(row)
	print "Success."

def load_tissue_inventory_csv(filename):
	"""
		This function will load the updated output of dump_tissue_inventory_csv()
		TissueSamples are give a tss_sample_quantity=1, tss_units=Units[2][0] ('whole') if bool(cell_value) evaluates True.
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=',')
	columns = csv_infile.next()
	label = columns.pop(0) # "should read "Tissue Type \ Monkey"
	assert label == "Tissue Type \ Monkey"

	# This will convert the header row of "matrr_pk/mky_real_id" cells into a list of monkey objects
	monkeys = list()
	for h in columns:
		if h:
			_pk, _id = h.split('/')
			m = Monkey.objects.get(pk=_pk, mky_real_id=_id) # this will raise an Exception if the pk/id doesn't match or doesn't exist
			monkeys.append(m)

	for row in csv_infile:
		tst = TissueType.objects.get(tst_tissue_name=row.pop(0))
		for mky, cell in zip(monkeys, row):
			if bool(cell):
				tss = TissueSample.objects.get(monkey=mky, tissue_type=tst)
				tss.tss_sample_quantity = 1
				tss.tss_units = Units[2][0]
				tss.save()
	print "Success."

def _create_cbt(bouts, date, cohort, cbt_number=0, overwrite=False, seconds_to_exclude=0):
	"""
	This recursive function will iterate thru the bouts' start and end times to create a CohortBout.
	When it finds a bout start time that is over 5 minutes from this function's CohortBout it will call itself again to create a new CohortBout with the remaining bout times.
	"""
	if len(bouts):
		ov = overwrite # I need to be able to disable overwrite in a loop, but continue to pass the same argument into deeper recursions
		cbt, is_new = CohortBout.objects.get_or_create(cohort=cohort, dex_date=date, cbt_number=cbt_number, cbt_pellet_elapsed_time_since_last=seconds_to_exclude)
		if not is_new and not ov:
			msg = "CBT already exists, overwrite=False.  Returning..."
			print msg
			return
		for index, bout in enumerate(bouts):
			# First, a new or overwritten CBT needs an initial start time and end time
			if is_new or ov:
				cbt.cbt_start_time = bout['ebt_start_time']
				cbt.cbt_end_time = bout['ebt_end_time']
				is_new = False
				ov = False
				continue
			# Next, test if we need to trigger a new CBT
			# New CBT will need to be triggered if the bout's start time is >= 300 seconds after the cbt_end_time
			# this means there was a >300second gap between the end of a cohort bout and the start of another monkey bout.  This defines a new CBT
			bout_gap = bout['ebt_start_time'] - cbt.cbt_end_time
			if bout_gap >= 5*60:
				cbt.save() # first, save this CBT
				# next, begin(or continue) the recursion.
				# bouts[index:]: We don't need to pass in bouts we've already evaluated
				# cbt_number+1: We need to increment the cbt_number, to maintain distinct CBTs within a single day
				_create_cbt(bouts[index:], date, cohort, cbt_number+1, overwrite=overwrite, seconds_to_exclude=seconds_to_exclude)
				break # this break is crutial. the recursion will continue the rest of the bout loop.
			else:
				# This bout's start time within the current CBT's timespan
				# update the CBTs timespan
				# Because the bouts pasesd in are ordered by ebt_start_time, the cbt_start_time should always be less than the ebt_start_time
				cbt.cbt_end_time = max(cbt.cbt_end_time, bout['ebt_end_time'])
		cbt.save() # If we get here, we've run out of bouts to loop thru for this day.  This will end the recursion

def create_cohort_bouts(cohort, overwrite=False, seconds_to_exclude=0):
	if not isinstance(cohort, Cohort):
		try:
			cohort = Cohort.objects.get(pk=cohort)
		except Cohort.DoesNotExist:
			raise Exception("That's not a valid cohort")

	all_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort)
	# Get all the dates for this cohort
	all_dates = all_mtds.dates('drinking_experiment__dex_date', 'day', 'ASC').order_by('drinking_experiment__dex_date')
	for date in all_dates:
		# Get all the bout start and end times from each date
		bouts = ExperimentBout.objects.filter(mtd__monkey__cohort=cohort, mtd__drinking_experiment__dex_date=date).order_by('ebt_start_time')
		if seconds_to_exclude:
			bouts = bouts.filter(ebt_contains_pellet=False, ebt_pellet_elapsed_time_since_last__gte=seconds_to_exclude)
		bout_values = bouts.values('ebt_start_time', 'ebt_end_time')
		# And send the times into a recursion loop
		_create_cbt(bout_values, date, cohort, cbt_number=0, overwrite=overwrite, seconds_to_exclude=seconds_to_exclude)
		# After we've created all the cohort bouts, we need to update the bouts cbt foreign key association
		cbts = CohortBout.objects.filter(cohort=cohort, dex_date=date, cbt_pellet_elapsed_time_since_last=seconds_to_exclude)
		for cbt in cbts:
			# I didn't update the cbt fk in the recursion because this update should be faster
			cbt.populate_ebt_set()
