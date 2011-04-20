from matrr.models import *
import csv

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

