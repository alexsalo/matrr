import pandas as pd
import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
import pylab
matplotlib.use('TkAgg')
matplotlib.rcParams['savefig.directory'] = '~/Dropbox/Baylor/MachineLearning/ass3/latex'
import random

N=500 #Number of examples
Delta = 0.5 #Confidence level for (1-delta) probability of uniform convergence

def plotHyperplane(intercept, slope, ax=plt):
    ax.plot([0, N/2], [intercept,  slope * N/2 + intercept], 'b-', linewidth=0.5)
def substract_lists(a, b, operator='diff'):
    if operator=='diff':
        return [a_i - b_i for a_i, b_i in zip(a, b)]
    if operator=='sum':
        return [a_i + b_i for a_i, b_i in zip(a, b)]

###Generate data
X_0 = pd.DataFrame([(x,- (N/2 - x) ** 1/2 * (random.random()+0.5) + 50, 0) for x in xrange(N/2)], columns=['x1','x2','y'])
X_1 = pd.DataFrame([(x, x ** 1/2 * (random.random()+0.5), 1) for x in xrange(N/2)], columns=['x1','x2','y'])
X = X_0.append(X_1,ignore_index = True)

###Plot the data
colors = ['go'] * 250 + ['ro'] * 250
plt.plot(X.x1[:N/2], X.x2[:N/2], 'go', label='class 0')
plt.plot(X.x1[N/2:], X.x2[N/2:], 'ro', label='class 1')
plt.plot([0, N/2], [-9,  0.25 * N/2 + -9], 'b-', linewidth=0.5, label='Correct hypothesis')
plt.legend(loc='upper left')
plt.tight_layout()
pylab.show()

##Define finite set of hypothesis
static_H = [[2, 0.3], [-30, 0.5], [-90, 0.3], [-50, 0.4], [-100, 0.8], [-50, 0.2], [-9, 0.22], [-9, 0.25], [60, -0.32], [40, 0.5],
     [-53, -0.25], [-50, 0.45], [-50, 0.41], [-70, 0.5], [-55, 0.3], [-52, 0.34]]
def generateH(num):
    H = [[-9 * (random.random() + 0.5) * 5, 0.25 * (3 * random.random() - 0.5)] for i in xrange(num)]
    H.append([-9, 0.25]) #add correct hypothesis
    return H

###Halving algorithm
    # By construction of our date we assume:
    # 1. All our training data were correct (i.e. there is no noise). Thus, during training, if a
    #    hypothesis h in H ever misclassifies an example, we know h must be wrong.
    # 2. The correct hypothesis exists in H.
def Halving(H, S, verbose=True):
    numMistakes = 0
    for i in S:
        votes = 0
        for h in H:
            votes +=  int(X.x2[i] > h[0] + X.x1[i] * h[1])
        #Derive majority vote
        p = int(votes >= len(H)/2.0)
        numMistakes += int(p <> X.y[i])
        #delete incorrect hypothesis
        [H.remove(h) for h in H if int(X.x2[i] > h[0] + X.x1[i] * h[1]) <> X.y[i]]

    if verbose:
        print 'h_cap:', H, 'numMistakes: ', numMistakes
    return numMistakes

###Testing Algorithm
delta = 0.1
def Test(N_RUN):
    mistakes = []
    #make 100 runs
    for i in xrange(N_RUN):
        #Define test sample space
        test_i = random.sample(xrange(N), N * 3 / 10)
        H_copy = [h for h in H]

        #Run Halving algorithm on test sample space and keep numMistakes
        mistakes.append(Halving(H_copy, test_i, False))

    ###Analysis
    print 'Mistakes: ', mistakes
    print "Mean mistake: %0.2f (sd = %0.2f); Mistake bound: %d;" \
          "Empirical Risk Bound: %0.2f"\
          % (np.mean(mistakes), np.std(mistakes), math.ceil(np.log2(len(H))), np.log2(len(H)/delta)/150)
    return mistakes, np.mean(mistakes), np.std(mistakes)

###Run experiment with various number of Hypothesis
runs_h = [1, 5, 10, 30, 50, 80]
fig, axs = plt.subplots(len(runs_h), 1, figsize=(12,16))
numMistake_means = []
numMistake_sds = []
mistake_bound = []
emp_risk_bound = []
for i, h_num in enumerate(runs_h):
    H = generateH(h_num)
    mistakes, mean, sd = Test(N_RUN=10)

    numMistake_means.append(mean)
    numMistake_sds.append(sd)
    mistake_bound.append(math.ceil(np.log2(len(H))))
    emp_risk_bound.append(np.log2(len(H)/delta)/150)

    ###Plot the data
    colors = ['go'] * 250 + ['ro'] * 250
    axs[i].plot(X.x1[:N/2], X.x2[:N/2], 'go', X.x1[N/2:], X.x2[N/2:], 'ro')
    [plotHyperplane(h[0], h[1], axs[i]) for h in H]
    axs[i].text(0.01, 0.95, "|H| = %s, numMistakes <= log2(|H|) = %d \n"
                    "NumMistakes for runs: %s\n"
                    "Empirical Risk Bound: %0.2f\n"
                    "Mean numMistake: %0.2f (sd = %0.2f)" % (len(H), math.ceil(np.log2(len(H))),
                                                             mistakes, np.log2(len(H)/delta)/150, mean, sd),
            horizontalalignment='left',
            verticalalignment='top',
            transform=axs[i].transAxes, fontsize=12)
    # Fine-tune figure; make subplots close to each other and hide x ticks for all but bottom plot.
    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)
    plt.setp([a.get_yticklabels() for a in fig.axes[1:]], visible=False)
plt.tight_layout()

###Plot numMistakes trend
fig2 = plt.figure()
ax = fig2.add_subplot(111)
t = runs_h
ax.plot(t, numMistake_means, 'b-o', lw=1, label='numMistakes mean')
ax.set_xlabel('Number of hypothesis')
ax.set_ylabel('Mistakes')
ax.plot(t, mistake_bound, 'b--', label='Mistake bound')
ax.plot(t, [elem * N for elem in emp_risk_bound], 'k--', label='Empirical Risk bound')
lower_bound = substract_lists(numMistake_means, numMistake_sds, 'sum')
upper_bound = substract_lists(numMistake_means, numMistake_sds, 'diff')
ax.fill_between(t, lower_bound, upper_bound, facecolor='yellow', alpha=0.5,
                label='1 sigma range')
#dummy plot to creaate legend since fill_between is not supported
ax.plot([], [], color='yellow', linewidth=10, label='1 sigma range')
ax.legend(loc='upper left')

########PART II - Empirical Risk bound###########
from sklearn import linear_model
def sigmoid(arg):
    return 1 / (1 + np.exp(-arg))

random.seed(123)
RUNS = 10
max_sample_size = 20
sample_start = 1
results = np.zeros([RUNS, max_sample_size - sample_start + 1])
for run in xrange(RUNS):
    run_results = []
    for size in xrange(sample_start, max_sample_size+1):
        test_i = random.sample(xrange(N/2), size) + random.sample(xrange(N/2, N), size)
        test_X = X.ix[test_i]
        #h = Halving(generateH(20), test_i, False)
        clf = linear_model.LogisticRegression()
        clf.fit(test_X[['x1','x2']], test_X[['y']])

        num_mistakes = 0
        for i in X.index:
            if int(sigmoid(np.dot([X.x1[i], X.x2[i]], clf.coef_.T) + clf.intercept_ ) > 0.5) <> X.y[i]:
            #if int(X.x2[i] > h[0] + X.x1[i] * h[1]) <> X.y[i]:
                num_mistakes += 1
        run_results.append(num_mistakes)
    results[run] = run_results

results = results / N #scale for percentages
res_means = np.mean(results, axis=0)
res_sds = np.std(results, axis=0)
print res_means
t = xrange((2 * sample_start), (2 * (max_sample_size+1)), 2)
delta = 0.1
empirical_risk_bound = [np.log2(1/delta) * 1.0 / tt for tt in t]
ttt = [tt for tt in t]
plt.plot(t, res_means, label='Average error rate')
plt.plot(ttt[2:], empirical_risk_bound[2:],'k--', label='Empirical risk bound, delta = 0.1')
plt.xlabel('Number of training examples, m')
plt.ylabel('Error rate of the best hypothesis on the entire distribution')
plt.grid()
plt.ylim(-0.05,0.6)

lower_bound = substract_lists(res_means, res_sds, 'sum')
upper_bound = substract_lists(res_means, res_sds, 'diff')
plt.fill_between(t, lower_bound, upper_bound, facecolor='yellow', alpha=0.5,
                label='+- sigma range')
#dummy plot to creaate legend since fill_between is not supported
plt.plot([], [], color='yellow', linewidth=10, label='+- sigma range')
plt.legend(loc='upper left')

pylab.show()





