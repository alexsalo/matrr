__author__ = 'alex'
import sys
import os
sys.path.append('/home/alex/pycharm/ve1/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django
django.setup()

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import timedelta

from matrr.models import MonkeyBEC, MonkeyToDrinkingExperiment, Monkey