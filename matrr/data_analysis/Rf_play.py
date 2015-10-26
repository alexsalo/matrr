from sklearn.datasets import make_hastie_10_2
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble.partial_dependence import plot_partial_dependence
from header import  *

X, y = make_hastie_10_2(random_state=0)
# print X
# print y
# clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0,max_depth=1, random_state=0).fit(X, y)
# features = [0, 1, (0, 1)]
# fig, axs = plot_partial_dependence(clf, X, features)

from sklearn.datasets import load_iris
iris = load_iris()
mc_clf = GradientBoostingClassifier(n_estimators=10, max_depth=1).fit(iris.data, iris.target)
print iris.data
print iris.target
features = [3, 2, (3, 2)]
fig, axs = plot_partial_dependence(mc_clf, iris.data, features, label=0)

pylab.show()