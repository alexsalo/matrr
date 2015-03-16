__author__ = 'alex'
from header import *
import sklearn.decomposition as deco

# x = (x - np.mean(x, 0)) / np.std(x, 0) # You need to normalize your data first
# pca = deco.PCA(n_components) # n_components is the components number after reduction
# x_r = pca.fit(x).transform(x)
# print ('explained variance (first %d components): %.2f'%(n_components, sum(pca.explained_variance_ratio_)))

sas_filename = '/home/alex/Dropbox/Baylor/Matrr/luminex/sas.csv'
n_components = 2
df = pd.DataFrame.from_csv(sas_filename, header=0)

#split phase and label
df['label'] = df['Phase'].str[1]
df['Phase'] = df['Phase'].str[0]
cols = df.columns.tolist()
cols = cols[-1:] + cols[:-1]
df = df[cols]

# fix dashes in colnames
newconames = [column.replace('-', '') for column in df.columns]
df.columns = newconames

df = df.sort_index()
df = df.dropna()
print df.columns
float_columns = [column for column in df.columns if df[column].dtype == 'float64']
df[float_columns] = normalize(df[float_columns])

#df.to_csv('/home/alex/Dropbox/Baylor/Matrr/sas_r.csv')




df_floats = df[float_columns].drop('Cohort', 1)

pca = deco.PCA(n_components)
df_pca = pca.fit(df_floats).transform(df_floats)
print ('explained variance (first %d components): %.2f'%(n_components, sum(pca.explained_variance_ratio_)))
print pca.explained_variance_ratio_
i = np.identity(df_floats.shape[1])
coef = pca.transform(i)
print coef
pca_weights = pd.DataFrame(coef, columns=['PC-1', 'PC-2'], index=df_floats.columns)
print pca_weights[['PC-2']].values

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
            plt.title(str(column))
            path = '/home/alex/MATRR/christa_pca/'
            plotname = str(column) + '_pre_post.png'
            fig.savefig(os.path.join(path, plotname), dpi=100)
#plot_christa(df)

def plot_qqplots(df):
    df = df[df.label == 'A']
    float_columns = [column for column in df.columns if df[column].dtype == 'float64']
    df = df[float_columns]
    for column in df.columns:
        if str(column) != 'Cohort':
            fig = plt.figure(figsize=(12, 12))
            fig.clf()
            stats.probplot(df[str(column)].values, dist="norm", plot=pylab)
            plt.title(str(column))
            path = '/home/alex/MATRR/christa_pca/qqplots'
            plotname = str(column) + '_qqplot.png'
            fig.savefig(os.path.join(path, plotname), dpi=100)
#plot_qqplots(df)

#pylab.show()