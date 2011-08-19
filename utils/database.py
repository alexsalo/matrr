from matrr.models import *
from django.db import transaction

import csv, re

@transaction.commit_on_success
def load_experiments(file):
	"""
	  This function will assume that the monkeys and cohorts are already entered into the database.
	  Assumes the columns are in the following order:
		0 - Date
		1 - Cohort - this is ignored.  we look at the monkey's cohort instead
		2 - Experiment Type
		3 - Monkey ID
		4 - EtOH Intake
		5 - Veh Intake
		6 - EtOH g/kg
		7 - Total Pellets Consumed
		8 - Weight
	  """
	input = csv.reader(open( file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	# get the column headers
	columns = input.next()

	for row in input:
		# get the monkey
		monkey = Monkey.objects.get(mky_real_id=row[3])
		# create the drinking_experiment if it does not already exist
		if DrinkingExperiment.objects.filter(dex_date=row[0], cohort=monkey.cohort, dex_type=row[2]).count() == 0:
			drinking_experiment = DrinkingExperiment(dex_date=row[0], cohort=monkey.cohort, dex_type=row[2])
			drinking_experiment.save()
			# saving the drinking_experiment will also create the MonkeyToExperiment objects
		else:
			# otherwise get the existing experiment
			drinking_experiment = DrinkingExperiment.objects.get(dex_date=row[0], cohort=monkey.cohort, dex_type=row[2])

		# get the MonkeyToDrinkingExperiment object for this row
		mtd = MonkeyToDrinkingExperiment(monkey=Monkey.objects.get(mky_real_id=row[3]), drinking_experiment=drinking_experiment)

		# add the data to the MonkeyToExperiment object
		if row[4]:
			mtd.mtd_etoh_intake = row[4]
		else:
			mtd.mtd_etoh_intake = 0
		mtd.mtd_veh_intake = row[5]
		mtd.mtd_total_pellets = row[7]
		mtd.mtd_weight = row[8]

		# save the data
		mtd.save()


@transaction.commit_on_success
def load_monkeys(file):
	"""
	  This function will load monkeys from a csv file.
	  It assumes that the cohorts have already been created.
	  It also assumes the columns are in the following order:
		0 - Monkey ID
		1 - Date of Birth
		2 - Cohort Name
		3 - Stress Model
		4 - Sex (either 'male' or 'female')
		5 - Drinking (marked if non-drinking or housing control)
		6 - Name
		7 - Necropsy Date
		8 - Complete Study (marked if incomplete)
	  """
	input = csv.reader(open( file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	# get the column headers
	columns = input.next()

	for row in input:
		# get the cohort
		cohort = Cohort.objects.get(coh_cohort_name=row[2])
		# clean up the input
		id = int(row[0])
		birthdate = row[1]
		stress_model = row[3]
		if len(stress_model) == 0:
			stress_model = None
		sex = None
		if row[4] == 'male':
			sex = 'M'
		elif row[4] == 'female':
			sex = 'F'

		drinking = True
		housing_control = False
		if len(row[5]) != 0:
			drinking = False
			if row[5] == 'housing ctrl':
				housing_control = True

		name = None
		if row[6] != 'NULL':
			name = row[6]

		# convert the necropsy date from mm/dd/yy to ISO format
		# this assumes all necropsy were after 2000.
		necropsy = re.sub(r'(\d+)/(\d+)/(\d+)',
						  r'20\3-\1-\2',
						  row[7])
		if len(necropsy) == 0:
			necropsy = None


		complete_study = True
		if len(row[8]) != 0 or necropsy is None:
			complete_study = False

		# check if the monkey already exists
		if Monkey.objects.filter(mky_real_id=id).count():
			# Update the monkey
			monkey = Monkey.objects.get(mky_real_id=id)
			monkey.mky_birthdate = birthdate
			monkey.mky_stress_model = stress_model
			monkey.mky_gender = sex
			monkey.mky_drinking = drinking
			monkey.mky_name = name
			monkey.mky_necropsy_date=necropsy
			monkey.mky_housing_control=housing_control
			monkey.mky_study_complete=complete_study
			monkey.save()
		else:
			# Create the monkey and save it
			Monkey(cohort=cohort,
				   mky_real_id=id,
				   mky_birthdate=birthdate,
				   mky_stress_model=stress_model,
				   mky_gender=sex,
				   mky_drinking=drinking,
				   mky_name=name,
				   mky_necropsy_date=necropsy,
				   mky_housing_control=housing_control,
				   mky_study_complete=complete_study).save()


@transaction.commit_on_success
def load_timelines(file):
	"""
	  This function will load monkeys from a csv file.
	  It assumes that the cohorts have already been created.
	  The first row should be table headers and the first
	  column should be cohort names.
	  If a column header has "Name" in it, it is not added as an
	  event and the following column is given the contents of the cell as
	  the info field.
	  """
	input = csv.reader(open( file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	# get the column headers
	columns = input.next()
	name_columns = list()
	for i, header in enumerate(columns):
		if re.match(r'.*Name.*', header) is not None:
			name_columns.append(i)
		elif i != 0:
			# if the event type does not exist, create it
			if EventType.objects.filter(evt_name=header).count() == 0:
				EventType(evt_name=header).save()

	for row in input:
		cohort = None
		info = None
		next_info = None
		for i, value in enumerate(row):
			if i == 0:
				cohort = Cohort.objects.get(coh_cohort_name=value)
			elif i in name_columns and len(value) != 0:
				info = value
			elif len(value) != 0:
				# skip empty cells

				#convert the date to ISO format
				date = re.sub(r'(\d+)/(\d+)/(\d+)',
							  r'\3-\1-\2',
							  value)
				CohortEvent(cohort=cohort,
							event=EventType.objects.get(evt_name=columns[i]),
							cev_date=date,
							cev_info=info).save()

				info = None


@transaction.commit_on_success
def load_cohorts(file):
	"""
	  This function will load cohorts from a csv file.
	  It assumes the first column of every row (except the first row),
	  contains the cohort name and that the second column contains the species of monkey.
	  """
	input = csv.reader(open( file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	# get the column headers
	columns = input.next()

	placeholder_name = 'Placeholder Institution'
	# check if a placeholder institution exists
	if not Institution.objects.filter(ins_institution_name=placeholder_name).count():
		# add a dummy institution
		placeholder = Institution(ins_institution_name=placeholder_name)
		placeholder.save()
	else:
		# get the dummy institution
		placeholder = Institution.objects.get(ins_institution_name=placeholder_name)

	for row in input:
		# Create the cohort and save it
		Cohort(coh_cohort_name=row[0],
			   coh_upcoming=False,
			   institution=placeholder,
			   coh_species=row[1]).save()


@transaction.commit_on_success
def load_inventory(file, output_file):
	"""
	  This function will load freezer inventories from a csv file.
	  !!!!! It will only load monkeys that are already in the database !!!!!
	  It assumes that the cohorts and monkeys have already been created.
	  It will create tissue categories if they do not already exist.
	  It also assumes the columns are in the following order:
		0 - Cohort Name -- ignoring this column for now
		1 - Monkey ID
		2 - Monkey Name
		3 - Species
		4 - Sex
		5 - Date of Birth
		6 - Necropsy Date (or necropsy start date)
		7 - Date/Date Range Start Comment
		8 - Date Range End
		9 - Date Range End Comment
		10 - Age at Necropsy
		11 - Weight at Necropsy
		12 - WFU Treatment Codes -- ignoring this column for now
		13 - Tissue Category
		14 - Tissue Detail
		15 - Comments
		16 - Additional Info for Specific Tissue
		17 - Shelf
		18 - Rack
		19 - Column
		20 - Box
		21 - Distributed
		22 - Reserved
		23 - Reserved Quantity
		24 - Samples in Inventory
		25 - Available samples
		26 - Freezer
		27 - Original Box Status -- ignoring for now
	  """
	input = csv.reader(open( file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	output = csv.writer(open( output_file, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	# get the column headers
	columns = input.next()
	output.writerow(columns)
	unused_monkeys = set()
	monkeys = []
	regex = re.compile(r'.*distributed.*', re.IGNORECASE)
	category_regex = re.compile(r'.*brain block.*', re.IGNORECASE)
	for row in input:
		if row[1] is '' or row[1] is None:
			continue

### 	had to fix some rows in 20110809 data, details in ### comments
		monkey_id = row[1]
		monkey_name = row[2]
		monkey_birthdate = row[5]
		necropsy_start_date = row[6]
		necropsy_start_date_comments = row[7]
		necropsy_end_date = row[8]
		necropsy_end_date_comments = row[9]
		age_at_necropsy = row[10]
		necropsy_weight = row[11]
		tissue_category = row[13]

### 	had to fix a few dozen cells to read "##" instead of plain ##.
		tissue_detail = row[14]
		comments = row[15]
		additional_info = row[16]

### 	"SHELF #" to "#" with find/replace in spreadsheet apps
		shelf = row[17]

### 	"Drawer #"  -->  "#"
		rack = row[18]
		column = row[19]

### 	"bag" --> "0"
		box = row[20]
		distributed = row[21]
		reserved = row[22]
		reserved_quantity = row[23]
		samples_in_inventory = row[24]
		available_samples = row[25]
		freezer = row[26]
		#original_box_status = row[27]

		if Monkey.objects.filter(mky_real_id=monkey_id).count():
			# if the monkey exists
			# update it
			if monkey_id not in monkeys:
				monkey = Monkey.objects.get(mky_real_id=monkey_id)
				if monkey_name:
					monkey.mky_name = monkey_name
				if monkey_birthdate:
					match = re.match(r'(\d{2})/(\d{2})/(\d{2})', monkey_birthdate)
					if int(match.group(3)) < 20:
						year_prefix = '20'
					else:
						year_prefix = '19'
					monkey.mky_birthdate = match.group(1) + "/" + match.group(1) + "/" + year_prefix + match.group(3)
				if necropsy_start_date:
					monkey.mky_necropsy_start_date = re.sub(r'(\d{2})/(\d{2})/(\d{2})', r'20\3-\1-\2', necropsy_start_date)
				if necropsy_start_date_comments:
					monkey.mky_necropsy_start_date_comments = necropsy_start_date_comments
				if necropsy_end_date:
					monkey.mky_necropsy_end_date = re.sub(r'(\d{2})/(\d{2})/(\d{2})', r'20\3-\1-\2', necropsy_end_date)
				if necropsy_end_date_comments:
					monkey.mky_necropsy_end_date_comments = necropsy_end_date_comments
				if age_at_necropsy:
					monkey.mky_age_at_necropsy = age_at_necropsy
				if necropsy_weight:
					monkey.mky_weight = necropsy_weight
				monkey.save()
				monkeys.append(monkey_id)

			# add the tissue category, type, and sample

			# if the tissue detail includes "distributed", then the tissue is distributed and should not be added
			if regex.match(tissue_detail):
				# skip the rest of the loop because the sample has been distributed
				continue

			# first, get the category
###			Renamed "Necropsy Perif
			if TissueCategory.objects.filter(cat_name=tissue_category).count():
				# don't bother updating the description, it shouldn't be changing
				category = TissueCategory.objects.get(cat_name=tissue_category)
			else:
				# if the category doesn't exist, create it
				category = TissueCategory(cat_name=tissue_category, cat_description=comments)

				# if the tissue category includes 'brain block' flag the category for internal use only
				if category_regex.match(tissue_category):
					category.cat_internal = True
				else:
					category.cat_internal = False
				category.save()

			# get the tissue type
			#    could be replaced with get_or_create() maybe
			if TissueType.objects.filter(tst_tissue_name=tissue_detail, category=category).count():
				tissue_type = TissueType.objects.get(tst_tissue_name=tissue_detail, category=category)
			else:
				# if the tissue type doesn't exist, create it
				tissue_type = TissueType(tst_tissue_name=tissue_detail, category=category)
				tissue_type.save()

			# build the location string
			if shelf and rack and column and box:
				location = str(int(shelf)) + '-' + str(int(rack)) + '-' + str(int(column)) + '-' + str(int(box))
			else:
				location = "None"

			if TissueSample.objects.filter(tissue_type=tissue_type, monkey=monkey, tss_freezer=freezer, tss_location=location).count():
				# if the sample already exists, update the counts for it and the location
				sample = TissueSample.objects.get(tissue_type=tissue_type, monkey=monkey, tss_freezer=freezer, tss_location=location)
				if location:
					sample.tss_location = location
				if freezer:
					sample.tss_freezer = freezer
				if reserved_quantity:
					sample.tss_distributed_count = int(reserved_quantity)
				if samples_in_inventory:
					sample.tss_sample_count = int(samples_in_inventory)
			else:
				# create the sample
				sample = TissueSample(tissue_type=tissue_type, monkey=monkey, tss_freezer=freezer, tss_location=location,)
				if samples_in_inventory:
					sample.tss_sample_count=samples_in_inventory
				else:
					sample.tss_sample_count=1
				if reserved_quantity:
					sample.tss_distributed_count=reserved_quantity
				else:
					sample.tss_distributed_count=0
				# save the newly created or updated sample
			sample.save()
		else:
			# if the monkey does not exist,
			# add the monkey to the list of left out monkeys
			output.writerow(row)
			unused_monkeys.add(monkey_id)

	# at the end, we need to print a list of monkey ids that were left out
	for monkey_id in unused_monkeys:
		print int(monkey_id)

		#raise Exception('Just testing') #uncomment for testing purposes

def load_birthdates(file):
	"""
		This function will load a csv file in the format
		row[0] = Birthdate
		row[1] = Alt Birthdate format
		row[2] = Monkey Name
		row[3] = mky_real_id
	"""
	csv_infile = csv.reader(open(file, 'rU'), delimiter=",")
	csv_outfile = csv.writer(open( "LostMonkeys-" + file, 'w'), delimiter=',')
	columns = csv_infile.next()
	csv_outfile.writerow(columns)
	for row in csv_infile:
		try:
			mon = Monkey.objects.get(mky_real_id=row[3])
		except Monkey.DoesNotExist:
			csv_outfile.writerow(row)
			continue
		if row[0] is not None:
			match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2})', row[0])
			if int(match.group(3)) < 20:
				year_prefix = '20'
			else:
				year_prefix = '19'
			new_bd = match.group(1).zfill(2) + "/" + match.group(2).zfill(2) + "/" + year_prefix + match.group(3).zfill(2)
			old_bd = mon.mky_birthdate
			if new_bd != old_bd:
				mon.mky_birthdate = new_bd
				mon.save()


def recursive_category_removal():
	dirtycategory = TissueCategory.objects.filter(cat_name="Necropsy Peripheral tissues")

	for tissue in TissueType.objects.filter(category=dirtycategory):
		for sample in TissueSample.objects.filter(tissue_type=tissue):
			sample.delete()
#			sample.save()
		tissue.delete()
#		tissue.save()
	dirtycategory.delete()

	##  or...
	TissueSample.objects.filter(tissue_type__category=dirtycategory).delete()
	TissueType.objects.filter(category=dirtycategory).delete()
	dirtycategory.delete()
	return