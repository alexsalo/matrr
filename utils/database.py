from matrr.models import *
from django.db import transaction
from datetime import datetime as dt
#from datetime import date
from datetime import timedelta
import string
import datetime
import csv, re

# This was _not_ built to be used often.  In fact, if it ever needs to be used again, you'll probably have to rewrite it.
# Like I just did.
# -jf
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

def dump_monkey_data(output_file):
	output = csv.writer(open(output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	columns = ['mky_id', 'cohort', 'mky_real_id', 'mky_name', 'mky_gender', 'mky_birthdate', 'mky_weight', 'mky_drinking', 'mky_housing_control',
			   'mky_necropsy_start_date', 'mky_necropsy_start_date_comments', 'mky_necropsy_end_date', 'mky_necropsy_end_date_comments',
			   'mky_study_complete', 'mky_stress_model', 'mky_age_at_necropsy',]
	output.writerow(columns)
	for cohort in Cohort.objects.all():
		for monkey in cohort.monkey_set.all():
			row = []
			row.append(monkey.mky_id)
			row.append(cohort)
			row.append(monkey.mky_real_id)
			row.append(monkey.mky_name)
			row.append(monkey.mky_gender)
			row.append(monkey.mky_birthdate)
			row.append(monkey.mky_weight)
			row.append(monkey.mky_drinking)
			row.append(monkey.mky_housing_control)
			row.append(monkey.mky_necropsy_start_date)
			row.append(monkey.mky_necropsy_start_date_comments)
			row.append(monkey.mky_necropsy_end_date)
			row.append(monkey.mky_necropsy_end_date_comments)
			row.append(monkey.mky_study_complete)
			row.append(monkey.mky_stress_model)
			row.append(monkey.mky_age_at_necropsy)
			output.writerow(row)
		print "Cohort %s Success" % cohort.coh_cohort_name

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
	for monkey in Monkey.objects.all():
		if not tissue_type:
			tissuetypes = TissueType.objects.all()
			# Only create the "be specific" tissue samples for upcoming cohorts
			if not monkey.cohort.coh_upcoming:
				tissuetypes = tissuetypes.exclude(tst_tissue_name__icontains="Be specific")
		else:
			tissuetypes = [tissue_type]

		for tt in tissuetypes:
			sample, is_new = TissueSample.objects.get_or_create(monkey=monkey, tissue_type=tt)
			if is_new:
				sample.tss_freezer = "<new record, no data>"
				sample.tss_location = "<new record, no data>"
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
def load_mtd(file_name, dex_type='Coh8_initial', cohort_name='INIA Cyno 8'):
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
		('mtd_etoh_media_ibi'),
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

	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)

	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line_number, line in enumerate(read_data):
			data = line.split(',')
			data_fields = data[2:38]
			data_fields.extend(data[40:46])

			#			create or get experiment - date, cohort, dex_type
			try:
				dex_date = dt.strptime(data[0], "%m/%d/%y")
			#				dex_check_date = dt.strptime(data[38], "%m/%d/%y")
			except Exception as e:
				print ERROR_OUTPUT % (line_number, "Wrong date format", line)
				continue
			#			if dex_date != dex_check_date:
			#				print error_output % (line_number, "Date check failed", line)
			#				continue
			else:
				des = DrinkingExperiment.objects.filter(dex_type=dex_type, dex_date=dex_date, cohort=cohort)
				if des.count() == 0:
					de = DrinkingExperiment(dex_type=dex_type, dex_date=dex_date, cohort=cohort)
					de.save()
				elif des.count() == 1:
					de = des[0]
				else:
					print ERROR_OUTPUT % (line_number, "Too many drinking experiments with type %s, cohort %d and specified date." % (dex_type, cohort.coh_cohort_id), line)
					continue

			monkey_real_id = data[1]
			monkey_real_id_check = data[39]
			if monkey_real_id != monkey_real_id_check:
				print ERROR_OUTPUT % (line_number, "Monkey real id check failed", line)
				continue
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey_real_id)
			except:
				print ERROR_OUTPUT % (line_number, "Monkey does not exist", line)
				continue

			bad_data = data[47]
			if bad_data != '':
				print ERROR_OUTPUT % (line_number, "Bad data flag", line)
				continue

			mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment=de, monkey=monkey)
			if mtds.count() != 0:
				print ERROR_OUTPUT % (line_number, "MTD with monkey and date already exists.", line)
				continue
			mtd = MonkeyToDrinkingExperiment()
			mtd.monkey = monkey
			mtd.drinking_experiment = de
			mtd.mtd_notes = data[48]

			for i, field in enumerate(fields):
				if data_fields[i] != '':
					setattr(mtd, field, data_fields[i])

			try:
				mtd.clean_fields()
			except Exception as e:
				print ERROR_OUTPUT % (line_number, e, line)
				continue
			mtd.save()

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
			
def load_edrs_and_ebts(cohort_name, dex_type, file_dir, create_mtd=False):

	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)
	entries = os.listdir(file_dir)
	bouts = list()
	drinks = list()
	print "Reading list of files in folder..."
	for entry in entries:
		file_name = os.path.join(file_dir, entry)
		if not os.path.isdir(file_name):
			m = re.match(r'([0-9]+_[0-9]+_[0-9]+)_(bout|drink)_', entry)
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
	
def load_eev_one_file(file_name, dex, create_mtd=False):
	
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
				print ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
				continue
			
			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey, drinking_experiment=dex)
			if mtds.count() == 0:
				if create_mtd:
					mtd = MonkeyToDrinkingExperiment(monkey=monkey, drinking_experiment=dex, mtd_etoh_intake=-1, mtd_veh_intake=-1, mtd_total_pellets=-1)
					mtd.save()
					mtds = [mtd,]
					print "%d Creating MTD." % line_number
				else:
					print ERROR_OUTPUT % (line_number, "MonkeyToDrinkingExperiment does not exist.", line)
					continue
			if mtds.count() > 1:
				print ERROR_OUTPUT % (line_number, "More than one MTD.", line)
				continue
			mtd = mtds[0]

			
			eev_date = convert_excel_time_to_datetime(data[DATE_DATA_INDEX])
			
			eevs = ExperimentEvent.objects.filter(mtd=mtd, eev_source_row_number=line_number, eev_occurred=eev_date)
			if eevs.count() != 0:
				print ERROR_OUTPUT % (line_number, "EEV with MTD, date occurred and source row number already exists.", line)
				continue
			
			eev = ExperimentEvent()
			eev.mtd = mtd
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
				print ERROR_OUTPUT % (line_number, e, line)
				continue
			eev.save()	
			
def load_eevs(cohort_name, dex_type, file_dir, create_mtd=False):

	cohort = Cohort.objects.get(coh_cohort_name=cohort_name)
	entries = os.listdir(file_dir)
	print "Reading list of files in folder..."
	for entry in entries:
		file_name = os.path.join(file_dir, entry)
		if not os.path.isdir(file_name):
			m = re.match(r'([0-9]+_[0-9]+_[0-9]+)_', entry)
			if not m:
				print "Invalid file name format: %s" % entry
				continue
			try:
				day = dt.strptime(m.group(1), "%Y_%m_%d")
			except:
				print "Invalid date format in file name: %s" % entry
				continue
			dexs = DrinkingExperiment.objects.filter(cohort=cohort,dex_type=dex_type,dex_date=day)
			if dexs.count() == 0:
				print "DEX does not exist: %s" % entry
				continue
			if dexs.count() > 1:
				print "More than one DEX: %s" % entry
				continue
			dex = dexs[0]	
			print "Loading %s..." % file_name
			load_eev_one_file(file_name, dex, create_mtd)

def load_necropsy_summary(filename):
	"""
		This function will load a csv file in the format
		row[0]	= matrr_number
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
		row[21]	= 22hr_12mos_avg_g/kg
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	columns = csv_infile.next()
	for row in csv_infile:
		if row[0]:
			try:
				monkey = Monkey.objects.get(pk=row[0])
			except Monkey.DoesNotExist:
				raise Exception("No such monkey:  %s" % str(row[0]))
			try:
				nec_sum = monkey.necropsy_summary
			except NecropsySummary.DoesNotExist:
				nec_sum = NecropsySummary(monkey=monkey)

			monkey.mky_birthdate 			= datetime.datetime.strptime(row[5], '%m/%d/%y')
			monkey.mky_necropsy_start_date 	= datetime.datetime.strptime(row[6], '%m/%d/%y')
			monkey.mky_age_at_necropsy 		= row[7]
			monkey.save()

			nec_sum.ncm_etoh_onset 				= datetime.datetime.strptime(row[8], '%m/%d/%y')
			nec_sum.ncm_age_onset_etoh 			= row[9]
			nec_sum.ncm_etoh_4pct_induction 	= row[10] if row[10] != "control" else 0
			nec_sum.ncm_etoh_4pct_22hr			= row[11] if row[11] != "control" else 0
			nec_sum.ncm_etoh_4pct_lifetime		= row[12] if row[12] != "control" else 0
			nec_sum.ncm_etoh_g_lifetime			= row[13] if row[13] != "control" else 0
			nec_sum.ncm_sum_g_per_kg_induction	= row[14] if row[14] != "control" else 0
			nec_sum.ncm_sum_g_per_kg_22hr		= row[15] if row[15] != "control" else 0
			nec_sum.ncm_sum_g_per_kg_lifetime	= row[16] if row[16] != "control" else 0
			nec_sum.ncm_6_mo_start 				= datetime.datetime.strptime(row[17], '%m/%d/%y')
			nec_sum.ncm_6_mo_end 				= datetime.datetime.strptime(row[18], '%m/%d/%y')
			nec_sum.ncm_12_mo_end 				= datetime.datetime.strptime(row[19], '%m/%d/%y')
			nec_sum.ncm_22hr_6mo_avg_g_per_kg	= row[20] if row[20] != "control" else 0
			nec_sum.ncm_22hr_12mo_avg_g_per_kg	= row[21] if row[21] != "control" else 0
			nec_sum.save()

def load_proteins(filename):
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
		pro_dict = {}
		if row[0]:
			pro_dict['pro_biochemical'] 	= row[0]
			pro_dict['pro_super_pathway'] 	= row[1]
			pro_dict['pro_sub_pathway'] 	= row[2]
			pro_dict['pro_comp_id'] 		= row[3]
			pro_dict['pro_platform'] 		= row[4]
			pro_dict['pro_ri'] 				= row[5]
			pro_dict['pro_mass'] 			= row[6]
			pro_dict['pro_cas'] 			= row[7]
			pro_dict['pro_kegg'] 			= row[8]
			pro_dict['pro_hmdb_id'] 		= row[9]

			protein, isnew = Protein.objects.get_or_create(**pro_dict)
			if isnew:
				protein.save()

def load_monkey_proteins(filename, values_normalized):
	"""
	Alright so, the format of the file they gave me is gonna be tough to parse through.  Scientists _love_ inverting axes in their spreadsheets.

	The first 8 rows of Column0 describe the monkey and the protein sample scenario.  They are:
	col0row0 = SAMPLE_NAME			# columns 1-30 hold 'OHSU-000001' , 'OHSU-000002', etc.
	col0row1 = SAMPLE_ID			# columns 1-30 hold unique, incrementing 6-digit integers
	col0row2 = CLIENT_INDENTIFIER	# columns 1-30 hold "1-<number>" where <number> == mky_real_id == row 6
	col0row3 = GROUP				# columns 1-30 hold a single digit integer which increments based on GROUP_ID.  1 == baseline, 2 = 6 months EtOH, etc
	col0row4 = DATE					# date the sample was taken
	col0row5 = TREATMENT			# rephrasing of GROUP_ID. Group_id's 'baseline' value is stored as 'ethanol naive' in these cells.
	col0row6 = SUBJECT ID			# mky_real_id
	col0row7 = GROUP_ID 			# described above -.-
	---
	For rows 8 thru *, the col0 value stored is the protein name (Protein.pro_biochemical).  The value stored in col1 - col30 is the protein value.

	Lets figure out how to parse this -.-
	"""
	csv_infile = csv.reader(open(filename, 'rU'), delimiter=",")
	monkey_datas = {}
	monkey_protein_datas = {}
	for row in csv_infile:
		if row[0]:
			if row[0] == 'SAMPLE_NAME':
				for idx, cell in enumerate(row[1:]):
					ts_dict = {'mpr_sample_name': cell}
					monkey_datas[idx] = ts_dict
			elif row[0] == 'SAMPLE_ID':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mpr_sample_id'] = cell
			elif row[0] == 'CLIENT_IDENTIFIER':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mpr_client_identifier'] = cell
			elif row[0] == 'GROUP':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mpr_group'] = cell
			elif row[0] == 'DATE':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mpr_date'] = datetime.datetime.strptime(cell, '%m/%d/%y')
			elif row[0] == 'TREATMENT':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mpr_treatment'] = cell
			elif row[0] == 'SUBJECT_ID':
				for idx, cell in enumerate(row[1:]):
					monkey = Monkey.objects.get(mky_real_id=cell)
					monkey_datas[idx]['monkey'] = monkey
					monkey_datas[idx]['mpr_subject_id'] = cell
			elif row[0] == 'GROUP_ID':
				for idx, cell in enumerate(row[1:]):
					monkey_datas[idx]['mpr_group_id'] = cell
			else:
				protein = Protein.objects.get(pro_biochemical=row[0])
				protein_row = []
				for idx, cell in enumerate(row[1:]):
					protein_row.append((monkey_datas[idx], protein, cell))
				monkey_protein_datas[row[0]] = protein_row

	for index in monkey_protein_datas:
		for protein_row in monkey_protein_datas[index]:
			monkey_data 	= protein_row[0]
			protein 		= protein_row[1]
			protein_value 	= protein_row[2] if protein_row[2] else None
			normalized		= True if values_normalized is True else False
			monkey_protein, isnew = MonkeyProtein.objects.get_or_create(protein=protein, mpr_protein_value=protein_value, mpr_is_normalized=normalized, **monkey_data)
			if isnew:
				monkey_protein.save()




















