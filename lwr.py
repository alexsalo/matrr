__author__ = 'alex'
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import pylab
import matplotlib.pyplot as plt

#weighted linear regression
def wls(x, y, plot=True, draw='ro', tau=0.3):
    """
    :param x: feature matrix
    :param y: target vector
    :param tau: smoothing factor - Gaussian bump's width
    :return: plot of matplotlib
    """
    size = len(x)

    x = np.mat(x).T
    y = np.mat(y).T
    m = x.shape[0] #number of examples

    dummy = np.mat(np.ones((m,), dtype=np.int))
    X = np.hstack((dummy.T, x)) #design matrix

    #try predicting on new possible examples
    xpred = np.linspace(x.min(), x.max(), size)
    ypred = np.zeros(size)

    for i in xrange(len(xpred)):
        xval = xpred[i]

        W = np.eye(m) #weights for current ith example
        theta = np.zeros(m) #thetas for that

        #fill weights via Gaussian sigmoid
        for j in xrange(m):
            W[j][j] = np.exp(-np.linalg.norm(x[j] - xval)**2 / 2*tau**2)

        #calc theta
        theta = np.linalg.inv(X.T * W * X) * (X.T * (W*y))

        #make prediction
        ypred[i] = np.mat([1, xval]) * theta

    if plot:
        fig, ax = plt.subplots(1)
        ax.plot(x, y, draw, xpred, ypred, 'b-')
        # plt.axis([0, 90, 0, 50])
        # ax = plt.gca()
        # ax.set_autoscale_on(False)

        yy = np.array(y)
        mu = np.mean(yy)
        median = np.median(yy)
        sigma = np.std(yy)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textstr = '$\mu=%.2f$\n$\mathrm{median}=%.2f$\n$\sigma=%.2f$'%(mu, median, sigma)
        ax.text(0.65, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        pylab.show()
    return xpred, ypred #ax#x, y,

from pylab import *
#pylab.show()
