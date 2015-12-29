__author__ = 'alex'
import sys
import os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import timedelta

from matrr.models import MonkeyBEC, MonkeyToDrinkingExperiment, Monkey, Cohort, ExperimentBout
from matrr.utils.database import dingus

#r10 = Cohort.objects.get(coh_cohort_id=19)
#r10monkeys = r10.monkey_set.all()

mtd = MonkeyToDrinkingExperiment.objects.get(drinking_experiment__dex_data=dingus.get_datetime_from_steve('5/14/2014'))
vols = ExperimentBout.objects.filter(mtd=mtd)
print vols.values_list('ebt_volume', flat=True)