__author__ = 'alex'
from header import *
import sklearn.decomposition as deco

# x = (x - np.mean(x, 0)) / np.std(x, 0) # You need to normalize your data first
# pca = deco.PCA(n_components) # n_components is the components number after reduction
# x_r = pca.fit(x).transform(x)
# print ('explained variance (first %d components): %.2f'%(n_components, sum(pca.explained_variance_ratio_)))

sas_filename = '/home/alex/Dropbox/Baylor/Matrr/luminex/sas.csv'
n_components = 10
df = pd.DataFrame.from_csv(sas_filename, header=0)
df['label'] = df['Phase'].str[1]
df = df.sort_index()

# float_columns = [column for column in df.columns if df[column].dtype == 'float64']
# df_floats = df[float_columns].drop('Cohort', 1)
# df_floats_clean = df_floats.dropna()
# print len(df_floats.index), len(df_floats_clean.index)
# df_floats_norm = normalize(df_floats_clean)

# pca = deco.PCA(n_components)
# df_pca = pca.fit(df_floats_norm).transform(df_floats_norm)
# print ('explained variance (first %d components): %.2f'%(n_components, sum(pca.explained_variance_ratio_)))
# print pca.explained_variance_ratio_

def plot_christa(df):
    df_A = df[df.label == 'A']
    df_B = df[df.label == 'B']
    df_A_grouped = df_A.groupby('Monk')
    df_B_grouped = df_B.groupby('Monk')
    df_A_grouped_means = df_A_grouped.mean()
    df_B_grouped_means = df_B_grouped.mean()
    for column in df_A_grouped_means.columns:
        if str(column) != 'Cohort':
            fig = plt.figure(figsize=(20, 10))
            plt.clf()
            plt.plot(df_A_grouped_means[str(column)], 'r-o', label='pre-dexamethasone ("A")')
            plt.plot(df_B_grouped_means[str(column)], 'b-o', label='post-dexamethasone ("B")')
            plt.legend(loc=1)
            path = '/home/alex/MATRR/christa_pca/'
            plotname = str(column) + '_pre_post.png'
            fig.savefig(os.path.join(path, plotname), dpi=100)
#plot_christa(df)

pylab.show()