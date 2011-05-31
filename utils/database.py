from matrr.models import *
from django.db import transaction

import csv, re

@transaction.commit_on_success
def load_experiments(file):
  """
  This function will assume that the monkeys and cohorts are already entered into the database.
  Assumes the columns are in the following order:
    0 - Date
    1 - Cohort
    2 - Experiment Type
    3 - Monkey ID
    4 - EtOH Intake
    5 - Veh Intake
    6 - EtOH g/kg
    7 - Total Pellets Consumed
    8 - Weight
  """
  input = csv.reader(open( file, 'rU'), delimiter='\t', quoting=csv.QUOTE_NONE)
  # get the column headers
  columns = input.next()
  
  for row in input:
    # create the drinking_experiment if it does not already exist
    if DrinkingExperiment.objects.filter(dex_date=row[0], cohort=row[1], dex_type=row[2]).count() == 0:
      drinking_experiment = DrinkingExperiment(dex_date=row[0], cohort=row[1], dex_type=row[2])
      drinking_experiment.save()
      # saving the drinking_experiment will also create the MonkeyToExperiment objects
    else:
      # otherwise get the existing experiment
      experiment = DrinkingExperiment.objects.get(exp_date=row[0], cohort=row[1], dex_type=row[2])
    
    # get the MonkeyToDrinkingExperiment object for this row
    mtd = MonkeyToDrinkingExperiment.objects.get(monkey=Monkey.objects.get(mky_real_id=row[3]), drinking_experiment=drinking_experiment)
    
    # add the data to the MonkeyToExperiment object
    mtd.mtd_etoh_intake = row[4]
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
    4 - Gender (either 'male' or 'female')
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
    gender = None
    if row[4] == 'male':
      gender = 'M'
    elif row[4] == 'female':
      gender = 'F'

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
      monkey.mky_gender = gender
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
           mky_gender=gender,
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
  if Institution.objects.filter(ins_institution_name=placeholder_name).count() == 0:
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
