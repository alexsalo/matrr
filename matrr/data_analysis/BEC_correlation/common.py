__author__ = 'alex'
import sys
import os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django
django.setup()

import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
matplotlib.rcParams['savefig.directory'] = '/home/alex/Dropbox/Baylor/Matrr/baker_salo/'
#matplotlib.rcParams['figure.dpi'] = 200
from datetime import timedelta

from matrr.models import MonkeyBEC, MonkeyToDrinkingExperiment, Monkey