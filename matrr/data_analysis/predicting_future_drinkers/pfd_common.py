import numpy as np
import pandas as pd
from setup_django import *
from matrr.models import Monkey, Cohort, MonkeyToDrinkingExperiment

pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 160)


def normalize_float_columns(df):
    def normalize(x):
        return (x - x.mean()) / (x.std())
    float_columns = [column for column in df.columns if df[column].dtype == 'float64']
    df[float_columns] = normalize(df[float_columns])
    return df


def print_full(x):
    pd.set_option('display.max_columns', len(x.columns))
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
