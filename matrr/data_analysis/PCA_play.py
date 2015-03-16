__author__ = 'alex'
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.linalg import svd
# from scipy.misc import lena
#
# # the underlying signal is a sinusoidally modulated image
# img = lena()
# t = np.arange(100)
# time = np.sin(0.1*t)
# real = time[:,np.newaxis,np.newaxis] * img[np.newaxis,...]
#
# # we add some noise
# noisy = real + np.random.randn(*real.shape)*255
#
# # (observations, features) matrix
# M = noisy.reshape(noisy.shape[0],-1)
#
# # singular value decomposition factorises your data matrix such that:
# #
# #   M = U*S*V.T     (where '*' is matrix multiplication)
# #
# # * U and V are the singular matrices, containing orthogonal vectors of
# #   unit length in their rows and columns respectively.
# #
# # * S is a diagonal matrix containing the singular values of M - these
# #   values squared divided by the number of observations will give the
# #   variance explained by each PC.
# #
# # * if M is considered to be an (observations, features) matrix, the PCs
# #   themselves would correspond to the rows of S^(1/2)*V.T. if M is
# #   (features, observations) then the PCs would be the columns of
# #   U*S^(1/2).
# #
# # * since U and V both contain orthonormal vectors, U*V.T is equivalent
# #   to a whitened version of M.
#
# U, s, Vt = svd(M, full_matrices=False)
# V = Vt.T
#
# # sort the PCs by descending order of the singular values (i.e. by the
# # proportion of total variance they explain)
# ind = np.argsort(s)[::-1]
# U = U[:, ind]
# s = s[ind]
# V = V[:, ind]
#
# # if we use all of the PCs we can reconstruct the noisy signal perfectly
# S = np.diag(s)
# Mhat = np.dot(U, np.dot(S, V.T))
# print "Using all PCs, MSE = %.6G" %(np.mean((M - Mhat)**2))
#
# # if we use only the first 20 PCs the reconstruction is less accurate
# Mhat2 = np.dot(U[:, :20], np.dot(S[:20, :20], V[:,:20].T))
# print "Using first 20 PCs, MSE = %.6G" %(np.mean((M - Mhat2)**2))
#
# fig, [ax1, ax2, ax3] = plt.subplots(1, 3)
# ax1.imshow(img)
# ax1.set_title('true image')
# ax2.imshow(noisy.mean(0))
# ax2.set_title('mean of noisy images')
# ax3.imshow((s[0]**(1./2) * V[:,0]).reshape(img.shape))
# ax3.set_title('first spatial PC')
# plt.show()

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


from sklearn import decomposition
from sklearn import datasets

np.random.seed(5)

centers = [[1, 1], [-1, -1], [1, -1]]
iris = datasets.load_iris()
X = iris.data
y = iris.target

fig = plt.figure(1, figsize=(4, 3))
plt.clf()
ax = Axes3D(fig, rect=[0, 0, .95, 1], elev=48, azim=134)

plt.cla()
pca = decomposition.PCA(n_components=3)
pca.fit(X)
X = pca.transform(X)

for name, label in [('Setosa', 0), ('Versicolour', 1), ('Virginica', 2)]:
    ax.text3D(X[y == label, 0].mean(),
              X[y == label, 1].mean() + 1.5,
              X[y == label, 2].mean(), name,
              horizontalalignment='center',
              bbox=dict(alpha=.5, edgecolor='w', facecolor='w'))
# Reorder the labels to have colors matching the cluster results
y = np.choose(y, [1, 2, 0]).astype(np.float)
ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=y, cmap=plt.cm.spectral)

x_surf = [X[:, 0].min(), X[:, 0].max(),
          X[:, 0].min(), X[:, 0].max()]
y_surf = [X[:, 0].max(), X[:, 0].max(),
          X[:, 0].min(), X[:, 0].min()]
x_surf = np.array(x_surf)
y_surf = np.array(y_surf)
v0 = pca.transform(pca.components_[0])
v0 /= v0[-1]
v1 = pca.transform(pca.components_[1])
v1 /= v1[-1]

ax.w_xaxis.set_ticklabels([])
ax.w_yaxis.set_ticklabels([])
ax.w_zaxis.set_ticklabels([])

plt.show()