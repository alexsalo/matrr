from matrr.models import *
from django.db import transaction
from datetime import datetime as dt
import datetime
import csv, re

## Old, might be useful in the future, but kept for reference
## Corrected improper birthday formatting.  match.group(0) = full string, not first group.  group.(1) is the first group.
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
	input = csv.reader(open(file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
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


## Old, might be useful in the future, but kept for reference
@transaction.commit_on_success
def load_monkeys(file):
	"""
	  This function will load monkeys from a csv file.
	  It assumes that the cohorts have already been created.
	  It also assumes the columns are in the following order:
		0 - DoB
		1 - Old ID (ignored)
		2 - Name (ignored)
		3 - New ID (ignored)
		4 - Birth Estimate (bool, "x"=true)
		5 - Animal #
		6 - Name (all == "INIA")
		7 - Alt Name (ignored)
		8 - Cohort (ignored)
		9 - Sub-Cohort (ignore)
		10 - Full Cohort ref (renamed to match matrr)
		11 - Species
		12 - SEX  (not gender, damnit, sex)
		13 - non-drinking ("control", "practice", "housing ctrl")
		14 - Name (None == "NULL")
		15 - Necropsy date
		16 - Incomplete study
	  """
	input = csv.reader(open(file, 'rU'), delimiter=',')
	# get the column headers
	columns = input.next()

	for row in input:
		cohort = Cohort.objects.get(coh_cohort_name=row[10])
		monkey_id = int(row[5])
		sex = row[12]
		drinking = True
		housing_control = False
		if row[13]:
			drinking = False
			if row[13] == 'housing ctrl':
				housing_control = True

		name = None
		if row[14] != 'NULL':
			name = row[14]

		# convert the birthdatedate from mm/dd/yy to ISO format
		if row[0]:
			match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2})', row[0])
			if int(match.group(3)) < 50:
				millennium = '20'
			else:
				millennium = '19'
			birthdate = millennium + match.group(3) + "-" + match.group(1) + "-" + match.group(2)
		else:
			birthdate = None
		# convert the necropsy date from mm/dd/yy to ISO format
		# this assumes all necropsy were after 2000.
		match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2})', row[15])
		necropsy = '20' + match.group(3) + "-" + match.group(1) + "-" + match.group(2)
		if not len(necropsy):
			necropsy = None

		complete_study = True
		if len(row[16]) != 0 or necropsy is None:
			complete_study = False

		# check if the monkey already exists
		if Monkey.objects.filter(mky_real_id=monkey_id).count():
			# Update the monkey
			monkey = Monkey.objects.get(mky_real_id=monkey_id)
			monkey.mky_birthdate = birthdate
			monkey.mky_gender = sex
			monkey.mky_drinking = drinking
			monkey.mky_name = name
			monkey.mky_necropsy_start_date = necropsy
			monkey.mky_housing_control = housing_control
			monkey.mky_study_complete = complete_study
			monkey.save()
			print monkey
		else:
			# Create the monkey and save it
			monkey = Monkey(cohort=cohort,
				   mky_real_id=monkey_id,
				   mky_birthdate=birthdate,
				   mky_gender=sex,
				   mky_drinking=drinking,
				   mky_name=name,
				   mky_necropsy_start_date=necropsy,
				   mky_housing_control=housing_control,
				   mky_study_complete=complete_study).save()
			print monkey


## Old, might be useful in the future, but kept for reference
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
	input = csv.reader(open(file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
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


## Old, might be useful in the future, but kept for reference
@transaction.commit_on_success
def load_cohorts(file):
	"""
	  This function will load cohorts from a csv file.
	  It assumes the first column of every row (except the first row),
	  contains the cohort name and that the second column contains the species of monkey.
	  """
	input = csv.reader(open(file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
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

# This was _not_ built to be used often.  In fact, if it ever needs to be used again, you'll probably have to rewrite it.
# Like I just did.
# -jf
@transaction.commit_on_success
def load_inventory(file, output_file, load_tissue_types=False,  delete_name_duplicates=False, create_tissue_samples=False):
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
		load_TissueTypes('tissuetypes.txt', delete_name_duplicates, create_tissue_samples)
	input = csv.reader(open(file, 'rU'), delimiter=',')
	output = csv.writer(open(output_file, 'w'), delimiter=',')
	unknown_monkeys = csv.writer(open('unknown_monkeys.csv', 'w'), delimiter=',')
	# get the column headers
	columns = input.next()
	columns[11:] = ["MATRR parsing error"]
	output.writerow(columns)
	unknown_monkeys.writerow(columns)
	monkeys = []
	units = Unit.objects.get(unt_unit_name="whole")
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


## Wrote this to correct birthdate string formats which load_experiments had slaughtered.
## This still saves birthdays as a string, not a datetime.
## It is highly unlikely this will be needed again in the future
## -jf
def load_birthdates(file):
	"""
		This function will load a csv file in the format
		row[0] = Birthdate
		row[1] = Alt Birthdate format
		row[2] = Monkey Name
		row[3] = mky_real_id
	"""
	csv_infile = csv.reader(open(file, 'rU'), delimiter=",")
	csv_outfile = csv.writer(open("LostMonkeys-" + file, 'w'), delimiter=',')
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


## Wrote this, ended up not using it.  May still need it, necropsy dates in the DB are different than in the spreadsheet I was given.
## -jf
def load_necropsy_dates(file):
	"""
	  This function will load monkeys from a csv file.
	  It assumes that the cohorts have already been created.
	  It also assumes the columns are in the following order:
		0 - Monkey ID
		1 - Monkey Species
		2 - Sex
		3 - Date of Birth
		4 - birth_estimated ("t" if True)
		5 - Monkey's Name
		6 - Necropsy Date
		7 - Cohort Broad Title ("INIA")
		8 - Cohort Species
		9 - Cohort Number
		10- Role ("control" or "")
		11- Sub_type  (ignored in this function, 'housing' is stored in Monkey)
	  """
	input = csv.reader(open(file, 'rU'), delimiter=',')
	# get the column headers
	columns = input.next()

	for row in input:
		real_id = row[0].replace(" ", '')
		necropsy = row[6].replace(" ", '')
		name = row[5].strip()
		if name == '':
			name = None

		# the necropsy date was given in string yyyy/mm/dd format
		if len(necropsy):
			necropsy = necropsy.split('-')
			necropsy = datetime.date(int(necropsy[0]), int(necropsy[1]), int(necropsy[2]))
		else:
			necropsy = None

		# check if the monkey already exists
		if Monkey.objects.filter(mky_real_id=real_id).count():
			monkey = Monkey.objects.get(mky_real_id=real_id)
			# Update the monkey
			monkey.mky_name = name
			monkey.mky_necropsy_start_date = necropsy
			monkey.save()


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

	category_iter = categs.__iter__()
	current_category = category_iter.next()
	with open(file_name, 'r') as f:
		read_data = f.readlines()
		for line in read_data:
			line = line.rstrip()
			if line == "":
				current_category = category_iter.next()
				continue
			duplicates = TissueType.objects.filter(tst_tissue_name=line)
			existing = list()
			name_duplicates_ids = list()
			name_duplicates = list()
			if len(duplicates) > 0:
				for duplicate in duplicates:
					if duplicate.category == current_category:
						existing.append(duplicate.tst_type_id)
					else:
						name_duplicates_ids.append(duplicate.tst_type_id)
						name_duplicates.append(duplicate)
			if len(name_duplicates_ids) > 0:
				if delete_name_duplicates:
					for name_duplicate in name_duplicates:
						name_duplicate.delete()
					print "Deleting name duplicates for tissue type " + line + " (with wrong category). Duplicate ids = " + `name_duplicates_ids`
				else:
					print "Found name duplicates for tissue type " + line + " (with wrong category). Duplicate ids = " + `name_duplicates_ids`

			if len(existing) > 0:
				print "Tissue type " + line + " already exists with correct category. Duplicate ids = " + `existing`
				continue

			tt = TissueType()
			tt.tst_tissue_name = line
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


# Creates InventoryStatus'
# -jf
#def create_InventoryStatus():
####				 Status Name  		Description
#	statuses = {"Unverified": "TissueSample inventory unverified",
#				"Sufficient": "TissueSample inventory verified sufficient for this TissueRequest",
#				"Insufficient": "TissueSample inventory verified insufficient for this TissueRequest.",
#				}
#	for key in statuses:
#		inv, is_new = InventoryStatus.objects.get_or_create(inv_status=key)
#		inv.inv_description = statuses[key]
#		inv.save()


@transaction.commit_on_success
# Creates ALL tissue samples in the database, for every monkey:tissuetype combination.
def create_TissueSamples():
	for monkey in Monkey.objects.all():
		tissuetypes = TissueType.objects.all()
		# Only create the "be specific" tissue samples for upcoming cohorts
		if not monkey.cohort.coh_upcoming:
			tissuetypes = tissuetypes.exclude(tst_tissue_name__icontains="Be specific")
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
			error_output = "%d %s # %s"
			#			create or get experiment - date, cohort, dex_type
			try:
				dex_date = dt.strptime(data[0], "%m/%d/%y")
			#				dex_check_date = dt.strptime(data[38], "%m/%d/%y")
			except Exception as e:
				print error_output % (line_number, "Wrong date format", line)
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
					print error_output % (line_number, "Too many drinking experiments with type %s, cohort %d and specified date." % (dex_type, cohort.coh_cohort_id), line)
					continue

			monkey_real_id = data[1]
			monkey_real_id_check = data[39]
			if monkey_real_id != monkey_real_id_check:
				print error_output % (line_number, "Monkey real id check failed", line)
				continue
			try:
				monkey = Monkey.objects.get(mky_real_id=monkey_real_id)
			except:
				print error_output % (line_number, "Monkey does not exist", line)
				continue

			bad_data = data[47]
			if bad_data != '':
				print error_output % (line_number, "Bad data flag", line)
				continue

			mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment=de, monkey=monkey)
			if mtds.count() != 0:
				print error_output % (line_number, "MTD with monkey and date already exists.", line)
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
				print error_output % (line_number, e, line)
				continue
			mtd.save()

def create_Assay_Development_tree():
	category = TissueCategory.objects.get_or_create(cat_name="Assay Development", cat_internal=False)
	tissue_type = TissueType.objects.get_or_create(category=category[0], tst_tissue_name="Assay Tissue")
	institution = Institution.objects.all()[0]
	cohort = Cohort.objects.get_or_create(coh_cohort_name="Assay Cohort", coh_upcoming=False, institution=institution)
	monkey = Monkey.objects.get_or_create(mky_real_id=0, mky_drinking=False, cohort=cohort[0])
	tissue_sample = TissueSample.objects.get_or_create(tissue_type=tissue_type[0], monkey=monkey[0])
