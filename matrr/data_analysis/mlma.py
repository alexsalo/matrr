__author__ = 'alex'
import sys, os
sys.path.append('~/pycharm/ve1/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from matrr.models import *
from matrr.models import Monkey
from matrr.plotting import monkey_plots as mkplot
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
import pylab

import django
django.setup()
import lwr as lwr
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrices
from sklearn.linear_model import LogisticRegression
from sklearn.cross_validation import train_test_split
from sklearn import metrics
from sklearn.cross_validation import cross_val_score


###GENDER CYCLE###
from matrr.utils.plotting_beta import monkey_plots as mkplt
from matrr.plotting import *
from matrr.plotting import plot_tools
from django.db.models import Min, Max, Avg, Q

import matplotlib.pyplot as pyplot
from matplotlib import gridspec
from matplotlib.ticker import NullLocator, MaxNLocator

# m19 = Monkey.objects.get(mky_id=10019)
# m20 = Monkey.objects.get(mky_id=10020)
# m32 = Monkey.objects.get(mky_id=10032)
#mkplt.monkey_etoh_bouts_vol(m32, from_date = '02/10/07')

def oa_drinking_lwr(monkey=None):
    drinking_experiments = MonkeyToDrinkingExperiment.objects.filter(monkey=monkey)
    #drinking_experiments = drinking_experiments.exclude(mtd_etoh_bout=None, mtd_etoh_drink_bout=None)

    if drinking_experiments.count() > 0:
        dates = drinking_experiments.dates('drinking_experiment__dex_date', 'day').order_by('drinking_experiment__dex_date')
    else:
        return None, False

    scatter_y = list()
    for index, date in enumerate(dates, 1):
        de = drinking_experiments.get(drinking_experiment__dex_date=date)
        if de.drinking_experiment.dex_type != 'Induction':
            if not (de.mtd_etoh_g_kg is None):
                scatter_y.append(de.mtd_etoh_g_kg)
    xaxis = numpy.array(range(1, len(scatter_y) + 1))
    return xaxis, scatter_y

m = Monkey.objects.get(mky_id=10032)
x, y = oa_drinking_lwr(m)
#plt = lwr.wls(x, y, tau=0.3)
x, y = lwr.wls(x, y, False)
df = pd.DataFrame(x, columns=['x'])
df['y'] = y
df.save('sindrink.pkl')
# pylab.show()


# from pylab import *
# from scipy import *
# from scipy import optimize
#
# #data is imperfect!!! What to do?
# fitfunc = lambda p, x: 1.6 * cos(2*pi/35*x+p[2]) + p[3] # Target function
# errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
# p0 = [2, 1.99409782, -3.26085884,  3.60161903] # Initial guess for the parameters
# p1, success = optimize.leastsq(errfunc, p0[:], args=(x, y))
# print p1
# time = linspace(x.min(), x.max(), 100)
# plt.plot(x, y, "ro", time, fitfunc(p1, time), "r-") # Plot of the data and the fit
# plt.xticks(np.arange(min(x), max(x)+1, 10.0))
# # Legend the plot
# title("Oscillations in the compressed trap")
# xlabel("time [ms]")
# ylabel("displacement [um]")
# legend(('x position', 'x fit', 'y position', 'y fit'))
# ax = axes()
#
# text(0.8, 0.07,
#     'x freq :  %.3f kHz \n y freq :  %.3f kHz' % (1/p1[1],1/p1[1]),
#     fontsize=16,
#     horizontalalignment='center',
#     verticalalignment='center',
#     transform=ax.transAxes)




# num_points = 150
# Tx = linspace(5., 8., num_points)
# Ty = Tx
#
# tX = 11.86*cos(2*pi/0.81*Tx-1.32) + 0.64*Tx+4*((0.5-rand(num_points))*exp(2*rand(num_points)**2))
# tY = -32.14*cos(2*pi/0.8*Ty-1.94) + 0.15*Ty+7*((0.5-rand(num_points))*exp(2*rand(num_points)**2))
#
# fitfunc = lambda p, x: p[0]*np.cos(2*pi/p[1]*x+p[2]) + p[3]*x # Target function
# errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
# p0 = [-15., 0.8, 0., -1.] # Initial guess for the parameters
# p1, success = optimize.leastsq(errfunc, p0[:], args=(Tx, tX))
#
# time = linspace(Tx.min(), Tx.max(), 100)
# plot(Tx, tX, "ro", time, fitfunc(p1, time), "r-") # Plot of the data and the fit
#
# # Fit the second set
# p0 = [-15., 0.8, 0., -1.]
# p2,success = optimize.leastsq(errfunc, p0[:], args=(Ty, tY))
#
# time = linspace(Ty.min(), Ty.max(), 100)
# plot(Ty, tY, "b^", time, fitfunc(p2, time), "b-")
#
# # Legend the plot
# title("Oscillations in the compressed trap")
# xlabel("time [ms]")
# ylabel("displacement [um]")
# legend(('x position', 'x fit', 'y position', 'y fit'))
#
# ax = axes()
# text(0.8, 0.07,
#   'x freq :  %.3f kHz \n y freq :  %.3f kHz' % (1/p1[1],1/p2[1]),
#    fontsize=16,
#      horizontalalignment='center',
#        verticalalignment='center',
#       transform=ax.transAxes)
#
# show()

pylab.show()

# print x
# print y
#x, y = mplot(m32, from_date = '03/10/07', to_date = '09/4/08')
#HDMonkeys = Monkey.objects.filter(mky_drinking_category = "HD")
#VHDMonkeys = Monkey.objects.filter(mky_drinking_category = "VHD")
#LDMonkeys = Monkey.objects.filter(mky_drinking_category = "LD")
# BDMonkeys = Monkey.objects.filter(mky_drinking_category = "BD")
# print BDMonkeys.count()
# cnt = 1
# for m in BDMonkeys:
#     if cnt > 6:
#         break
#     print cnt
#     cnt += 1
#     x, y = oa_drinking_lwr(m)
#     if not (x is None) and not (y is False):
#         fig = pyplot.figure()
#         fig.set_size_inches(28.5,10.5)
#         plt = lwr.wls(x, y, tau=0.3)
#         path = '/home/alex/MATRR/oa_drinking_lwr/'
#         plotname = str(m.mky_gender) + '_' + str(m.mky_id) + '_' + str(m.mky_species) + '_' + \
#                    str(m.mky_drinking_category) + '.png'
#         fig.suptitle(plotname)
#         fig.savefig(os.path.join(path, plotname), dpi=100)
#


# ######GENDER DIFFERENCEs
# readymonkeys = Monkey.objects.filter(mky_study_complete = True).exclude(mky_drinking_category = None)
# print readymonkeys.count()
# data = []
# #print readymonkeys[1].mky_gender
# for mky in readymonkeys:
#     data.append([str(mky.mky_gender), str(mky.mky_drinking_category)])
#
# dta = pd.DataFrame(data, columns=['sex', 'DK'])
# #dta['gender'] = (dta.sex == 'M').astype(int)
# print dta
#
# #dk_sex = pd.crosstab(dta.DK, dta.sex).plot(kind='bar')
# dk_sex = pd.crosstab(dta.DK, dta.sex)
# #print dk_sex.sum(1)
# dk_sex.div(dk_sex.sum(1).astype(float), axis = 0).plot(kind = 'bar', stacked = True)
# # affair_yrs_married = pd.crosstab(dta.yrs_married, dta.affair.astype(bool))
# # affair_yrs_married.div(affair_yrs_married.sum(1).astype(float), axis=0).plot(kind='bar', stacked=True)
#
#
# class Parameter:
#         def __init__(self, value):
#                 self.value = value
#
#         def set(self, value):
#                 self.value = value
#
#        def __call__(self):
#                return self.value
#
#    def fit(function, parameters, y, x = None):
#        def f(params):
#            i = 0
#            for p in parameters:
#                p.set(params[i])
#                i += 1
#            return y - function(x)
#
#        if x is None: x = arange(y.shape[0])
#        p = [param() for param in parameters]
#        optimize.leastsq(f, p)