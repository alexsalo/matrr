'''
Created on Jun 18, 2012

@author: slavka
'''

from sklearn.svm import SVR

#from sklearn.cross_validation import
from dataAndFeatures import *
from matrr.models import Cohort

cohort = Cohort.objects.get(pk=3)
d = create_dataset(cohort, collect_features_pca_by_grant_of_cohort, collect_reg_of_cohort)
print d.target
svr = SVR()


svr.fit(d.data[:-1], d.target[:-1])
print svr.predict(d.data[4])
print svr.predict(d.data[-1])

svr.fit(d.data[1:], d.target[1:])
print svr.predict(d.data[0])

svr.fit(d.data[2:], d.target[2:])
print svr.predict(d.data[1])

#print cross_val_score(svr, d.data, d.target, cv = len(d.target))
