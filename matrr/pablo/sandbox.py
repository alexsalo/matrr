__author__ = 'rivas_perea'

import sys, os
sys.path.append('/home/rivas_perea/virtenv/matrr')
sys.path.append('/home/rivas_perea/virtenv/matrr/matrr')
os.environ['DJANGO_SETTINGS_MODULE'] = 'local_settings'

from header import *
from matrr.models import *
import django
django.setup()
import time

# This for loop considers the
for TotMins in xrange(1, 121):  # From 1 to 120 (this is the number of minutes to analyze).

    data_s = pd.DataFrame()  # Data Statistics: from the drinking pattern of monkeys
    data_b = pd.DataFrame()  # Data of Bone: from Bone Density

    for k in range(Monkey.objects.count()):    # From 1 to ~211 (this is the number of monkeys to look for).
        m = Monkey.objects.all()[k]     # Retrieve the monkey object.
        mdt, mbd = Monkey.bd_etoh_during_ind(m, TotMins)    # see models.py for info on this function

        if (not mdt.empty) and (not mbd.empty):     # enters this part only of there is both drinking data and
                                                    # bone data for that monkey

            print m     # Prints the name of the monkey that is actually contributing to results.

            if data_s.empty:    # If it is empty make an = assignment, otherwise concatenate (see else condition below).
                data_s = pd.DataFrame({'Mean': mdt.mean(0, skipna=True)[0],     # These are all the statistics one can
                                     'Median': mdt.median(0, skipna=True)[0],   # obtain from pandas DataFrames... there
                                     'Sum': mdt.sum(0, skipna=True)[0],         # is no reason to get all of them, but
                                     'Unbiased Standard Deviation': mdt.std(0, skipna=True)[0],     # if some of these
                                     'Unbiased Variance': mdt.var(0, skipna=True)[0],   # are not useful, you can ignore
                                     'Unbiased Standard Error of The Mean': mdt.sem(0, skipna=True)[0],     # them, ok?
                                     'Unbiased Skewness (3rd Moment)': mdt.skew(0, skipna=True)[0],
                                     'Unbiased Kurtosis (4th Moment)': mdt.kurt(0, skipna=True)[0],
                                     'Mean Absolute Deviation': mdt.mad(0, skipna=True)[0],
                                     'Minimum Value': mdt.min(0, skipna=True)[0],
                                     'Maximum Value': mdt.max(0, skipna=True)[0],
                                     'Percentile 1': mdt.quantile(0.01, 0, numeric_only=True)[0],
                                     'Percentile 5': mdt.quantile(0.05, 0, numeric_only=True)[0],
                                     'Percentile 10': mdt.quantile(0.1, 0, numeric_only=True)[0],
                                     'Percentile 20': mdt.quantile(0.2, 0, numeric_only=True)[0],
                                     'Percentile 30': mdt.quantile(0.3, 0, numeric_only=True)[0],
                                     'Percentile 40': mdt.quantile(0.4, 0, numeric_only=True)[0],
                                     'Percentile 50': mdt.quantile(0.5, 0, numeric_only=True)[0],
                                     'Percentile 60': mdt.quantile(0.6, 0, numeric_only=True)[0],
                                     'Percentile 70': mdt.quantile(0.7, 0, numeric_only=True)[0],
                                     'Percentile 80': mdt.quantile(0.8, 0, numeric_only=True)[0],
                                     'Percentile 90': mdt.quantile(0.9, 0, numeric_only=True)[0],
                                     'Percentile 95': mdt.quantile(0.95, 0, numeric_only=True)[0],
                                     'Percentile 99': mdt.quantile(0.99, 0, numeric_only=True)[0]}, index=[m.mky_id])

                data_b = pd.DataFrame({'Bone Area': mbd[0][0],
                                     'Bone Mineral Content': mbd[0][1],
                                     'Bone Mineral Density': mbd[0][2]}, index=[m.mky_id])
            else:
                newdata = pd.DataFrame({'Mean': mdt.mean(0, skipna=True)[0],
                                     'Median': mdt.median(0, skipna=True)[0],
                                     'Sum': mdt.sum(0, skipna=True)[0],
                                     'Unbiased Standard Deviation': mdt.std(0, skipna=True)[0],
                                     'Unbiased Variance': mdt.var(0, skipna=True)[0],
                                     'Unbiased Standard Error of The Mean': mdt.sem(0, skipna=True)[0],
                                     'Unbiased Skewness (3rd Moment)': mdt.skew(0, skipna=True)[0],
                                     'Unbiased Kurtosis (4th Moment)': mdt.kurt(0, skipna=True)[0],
                                     'Mean Absolute Deviation': mdt.mad(0, skipna=True)[0],
                                     'Minimum Value': mdt.min(0, skipna=True)[0],
                                     'Maximum Value': mdt.max(0, skipna=True)[0],
                                     'Percentile 1': mdt.quantile(0.01, 0, numeric_only=True)[0],
                                     'Percentile 5': mdt.quantile(0.05, 0, numeric_only=True)[0],
                                     'Percentile 10': mdt.quantile(0.1, 0, numeric_only=True)[0],
                                     'Percentile 20': mdt.quantile(0.2, 0, numeric_only=True)[0],
                                     'Percentile 30': mdt.quantile(0.3, 0, numeric_only=True)[0],
                                     'Percentile 40': mdt.quantile(0.4, 0, numeric_only=True)[0],
                                     'Percentile 50': mdt.quantile(0.5, 0, numeric_only=True)[0],
                                     'Percentile 60': mdt.quantile(0.6, 0, numeric_only=True)[0],
                                     'Percentile 70': mdt.quantile(0.7, 0, numeric_only=True)[0],
                                     'Percentile 80': mdt.quantile(0.8, 0, numeric_only=True)[0],
                                     'Percentile 90': mdt.quantile(0.9, 0, numeric_only=True)[0],
                                     'Percentile 95': mdt.quantile(0.95, 0, numeric_only=True)[0],
                                     'Percentile 99': mdt.quantile(0.99, 0, numeric_only=True)[0]}, index=[m.mky_id])
                frames = [data_s, newdata]
                data_s = pd.concat(frames)      # Here is the concatenation and again below for data_b.

                newdata = pd.DataFrame({'Bone Area': mbd[0][0],
                                     'Bone Mineral Content': mbd[0][1],
                                     'Bone Mineral Density': mbd[0][2]}, index=[m.mky_id])
                frames = [data_b, newdata]
                data_b = pd.concat(frames)

            # if (k % 20) == 0:     # Uncomment this section if you want to see the data as it is generated every time
            #     print data_s      # there is the 20th iteration.
            #     print data_b

    print data_s    # This prints the statistical results and then saves them to csv files
    print data_b
    data_s.to_csv('data_s' + str(TotMins) + '.csv', encoding='utf-8')
    data_b.to_csv('data_b' + str(TotMins) + '.csv', encoding='utf-8')
    time.sleep(1)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '.csv', encoding='utf-8')






CorrDataCubeP = np.zeros((24, 3, 120))
CorrDataCubeK = np.zeros((24, 3, 120))
CorrDataCubeS = np.zeros((24, 3, 120))

corr_data_p = []
corr_data_k = []
corr_data_s = []

for TotMins in xrange(1, 121):  # 1 to 120
    corr_data_p = pd.read_csv('Pearson_correlation_results_' + str(TotMins) + '.csv', header=0, index_col=0)
    corr_data_k = pd.read_csv('Kendall_correlation_results_' + str(TotMins) + '.csv', header=0, index_col=0)
    corr_data_s = pd.read_csv('Spearman_correlation_results_' + str(TotMins) + '.csv', header=0, index_col=0)

    # print TotMins

    p = corr_data_p.values
    k = corr_data_k.values
    s = corr_data_s.values

    CorrDataCubeP[:, :, TotMins-1] = p
    CorrDataCubeK[:, :, TotMins-1] = k
    CorrDataCubeS[:, :, TotMins-1] = s

rows = list(corr_data_p.index.values)
cols = list(corr_data_p.columns.values)

print rows
print cols


# this just gets the maximum and minimum
idxOfBoneData = 2       # index 0 is Bone Area, 1 is Bone Mineral Content, etc.
a, b = np.unravel_index(CorrDataCubeP[:, idxOfBoneData, :].argmax(), CorrDataCubeP[:, idxOfBoneData, :].shape)
print "Maximum value is: ", CorrDataCubeP[a, idxOfBoneData, b]
print "Between " + rows[a] + " and " + cols[idxOfBoneData]
a, b = np.unravel_index(CorrDataCubeP[:, idxOfBoneData, :].argmin(), CorrDataCubeP[:, idxOfBoneData, :].shape)
print "Minimum value is: ", CorrDataCubeP[a, idxOfBoneData, b]
print "Between " + rows[a] + " and " + cols[idxOfBoneData]

time.sleep(1)


for statistic in rows:
    for bone_data in cols:
        fig, ax = plt.subplots()
        N = 3
        styles = ['-', '--', '-.', ':']
        markers = list('o+x^psDv')
        x = range(1, 121, 1)
        y = np.zeros((3, 120))
        y[0, :] = CorrDataCubeP[rows.index(statistic), cols.index(bone_data), :]
        y[1, :] = CorrDataCubeK[rows.index(statistic), cols.index(bone_data), :]
        y[2, :] = CorrDataCubeS[rows.index(statistic), cols.index(bone_data), :]
        labels = ['Pearson', 'Kendall', 'Spearman']

        for i in range(N):
            s = styles[i % len(styles)]
            m = markers[i % len(markers)]
            ax.plot(x, y[i, :], label=labels[i], marker=m, linewidth=2, linestyle=s)
        ax.grid(True)
        ax.legend(loc='best', prop={'size': 'large'})
        fig.suptitle('Correlation between ' + statistic + ' of % Drinking and ' + bone_data, fontweight='bold')
        ax.set_xlabel('Minutes After Open Access')
        ax.set_ylabel('Correlation Coefficient')
        ax.set_ylim(-1, 1)
        fig.subplots_adjust(top=0.9)
        fig.savefig('p - ' + statistic + ' - ' + bone_data + '.png')
















































# This experiment will be for male/female correlation
for TotMins in xrange(1, 121):  # From 1 to 120 (this is the number of minutes to analyze).
    data_s = pd.read_csv('data_s' + str(TotMins) + '.csv', header=0, index_col=0)  # Data Statistics
    data_b = pd.read_csv('data_b' + str(TotMins) + '.csv', header=0, index_col=0)  # Data of Bone
    data_s["Gender"] = np.nan
    data_b["Gender"] = np.nan

    for k in xrange(0, Monkey.objects.count()):    # From 1 to ~211 (this is the number of monkeys to look for).
        m = Monkey.objects.all()[k]     # Retrieve the monkey object.
        # print m.mky_id in data_s.index
        if m.mky_id in data_s.index:
            data_s.loc[m.mky_id, 'Gender'] = m.mky_gender
            data_b.loc[m.mky_id, 'Gender'] = m.mky_gender
            # print m.mky_id, m.cohort, m.mky_gender, m.mky_age_at_intox, m.mky_drinking_category

    # print data_s
    # time.sleep(30)

    print data_s    # This prints the statistical results and then saves them to csv files
    print data_b

    data_s.to_csv('data_s_g' + str(TotMins) + '.csv', encoding='utf-8')
    data_b.to_csv('data_b_g' + str(TotMins) + '.csv', encoding='utf-8')
    data_s_g = data_s   # this copies will preserve the original data with gender info
    data_b_g = data_b
    # time.sleep(1)

    # And now we do this for each gender
    # ============== Female ============================================================================================
    data_b = data_b_g[data_b_g['Gender'] == 'F']
    data_s = data_s_g[data_s_g['Gender'] == 'F']
    data_b.drop(['Gender'], axis=1, inplace=True)
    data_s.drop(['Gender'], axis=1, inplace=True)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '_g_f.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '_g_f.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '_g_f.csv', encoding='utf-8')
    # ============== END of Female Data Analysis =======================================================================

    # ============== Male ============================================================================================
    data_b = data_b_g[data_b_g['Gender'] == 'M']
    data_s = data_s_g[data_s_g['Gender'] == 'M']
    data_b.drop(['Gender'], axis=1, inplace=True)
    data_s.drop(['Gender'], axis=1, inplace=True)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '_g_m.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '_g_m.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '_g_m.csv', encoding='utf-8')
    # ============== END of Male Data Analysis =========================================================================


CorrDataCubeP = np.zeros((24, 3, 120, 2))
CorrDataCubeK = np.zeros((24, 3, 120, 2))
CorrDataCubeS = np.zeros((24, 3, 120, 2))

corr_data_p_f = []
corr_data_k_f = []
corr_data_s_f = []
corr_data_p_m = []
corr_data_k_m = []
corr_data_s_m = []

for TotMins in xrange(1, 121):  # 1 to 120
    corr_data_p_f = pd.read_csv('Pearson_correlation_results_' + str(TotMins) + '_g_f.csv', header=0, index_col=0)
    corr_data_k_f = pd.read_csv('Kendall_correlation_results_' + str(TotMins) + '_g_f.csv', header=0, index_col=0)
    corr_data_s_f = pd.read_csv('Spearman_correlation_results_' + str(TotMins) + '_g_f.csv', header=0, index_col=0)
    corr_data_p_m = pd.read_csv('Pearson_correlation_results_' + str(TotMins) + '_g_m.csv', header=0, index_col=0)
    corr_data_k_m = pd.read_csv('Kendall_correlation_results_' + str(TotMins) + '_g_m.csv', header=0, index_col=0)
    corr_data_s_m = pd.read_csv('Spearman_correlation_results_' + str(TotMins) + '_g_m.csv', header=0, index_col=0)

    # print TotMins

    CorrDataCubeP[:, :, TotMins-1, 0] = corr_data_p_f.values
    CorrDataCubeK[:, :, TotMins-1, 0] = corr_data_k_f.values
    CorrDataCubeS[:, :, TotMins-1, 0] = corr_data_s_f.values
    CorrDataCubeP[:, :, TotMins-1, 1] = corr_data_p_m.values
    CorrDataCubeK[:, :, TotMins-1, 1] = corr_data_k_m.values
    CorrDataCubeS[:, :, TotMins-1, 1] = corr_data_s_m.values

rows = list(corr_data_p_f.index.values)
cols = list(corr_data_p_f.columns.values)

print rows
print cols

# this just gets the maximum and minimum
idxOfBoneData = 2       # index 0 is Bone Area, 1 is Bone Mineral Content, etc.

# ============== Female ================================================================================================
FemaleIdx = 0
a, b = np.unravel_index(CorrDataCubeP[:, idxOfBoneData, :, FemaleIdx].argmax(), CorrDataCubeP[:, idxOfBoneData, :, FemaleIdx].shape)
print "Maximum value is: ", CorrDataCubeP[a, idxOfBoneData, b, FemaleIdx]
print "Between " + rows[a] + " and " + cols[idxOfBoneData]
a, b = np.unravel_index(CorrDataCubeP[:, idxOfBoneData, :,  FemaleIdx].argmin(), CorrDataCubeP[:, idxOfBoneData, :, FemaleIdx].shape)
print "Minimum value is: ", CorrDataCubeP[a, idxOfBoneData, b,  FemaleIdx]
print "Between " + rows[a] + " and " + cols[idxOfBoneData]

for statistic in rows:
    for bone_data in cols:
        fig, ax = plt.subplots()
        N = 3
        styles = ['-', '--', '-.', ':']
        markers = list('o+x^psDv')
        x = range(1, 121, 1)
        y = np.zeros((3, 120))
        y[0, :] = CorrDataCubeP[rows.index(statistic), cols.index(bone_data), :,  FemaleIdx]
        y[1, :] = CorrDataCubeK[rows.index(statistic), cols.index(bone_data), :,  FemaleIdx]
        y[2, :] = CorrDataCubeS[rows.index(statistic), cols.index(bone_data), :,  FemaleIdx]
        labels = ['Pearson', 'Kendall', 'Spearman']

        for i in range(N):
            s = styles[i % len(styles)]
            m = markers[i % len(markers)]
            ax.plot(x, y[i, :], label=labels[i], marker=m, linewidth=2, linestyle=s)
        ax.grid(True)
        ax.legend(loc='best', prop={'size': 'large'})
        fig.suptitle('Correlation between ' + statistic + ' of % Drinking and ' + bone_data, fontweight='bold')
        ax.set_xlabel('Minutes After Open Access')
        ax.set_ylabel('Correlation Coefficient')
        ax.set_ylim(-1, 1)
        fig.subplots_adjust(top=0.9)
        fig.savefig('p - ' + statistic + ' - ' + bone_data + '_f.png')
# ============== End ===================================================================================================

# ============== Male ==================================================================================================
MaleIdx = 1
a, b = np.unravel_index(CorrDataCubeP[:, idxOfBoneData, :, MaleIdx].argmax(), CorrDataCubeP[:, idxOfBoneData, :, MaleIdx].shape)
print "Maximum value is: ", CorrDataCubeP[a, idxOfBoneData, b, MaleIdx]
print "Between " + rows[a] + " and " + cols[idxOfBoneData]
a, b = np.unravel_index(CorrDataCubeP[:, idxOfBoneData, :,  MaleIdx].argmin(), CorrDataCubeP[:, idxOfBoneData, :, MaleIdx].shape)
print "Minimum value is: ", CorrDataCubeP[a, idxOfBoneData, b,  MaleIdx]
print "Between " + rows[a] + " and " + cols[idxOfBoneData]

for statistic in rows:
    for bone_data in cols:
        fig, ax = plt.subplots()
        N = 3
        styles = ['-', '--', '-.', ':']
        markers = list('o+x^psDv')
        x = range(1, 121, 1)
        y = np.zeros((3, 120))
        y[0, :] = CorrDataCubeP[rows.index(statistic), cols.index(bone_data), :,  MaleIdx]
        y[1, :] = CorrDataCubeK[rows.index(statistic), cols.index(bone_data), :,  MaleIdx]
        y[2, :] = CorrDataCubeS[rows.index(statistic), cols.index(bone_data), :,  MaleIdx]
        labels = ['Pearson', 'Kendall', 'Spearman']

        for i in range(N):
            s = styles[i % len(styles)]
            m = markers[i % len(markers)]
            ax.plot(x, y[i, :], label=labels[i], marker=m, linewidth=2, linestyle=s)
        ax.grid(True)
        ax.legend(loc='best', prop={'size': 'large'})
        fig.suptitle('Correlation between ' + statistic + ' of % Drinking and ' + bone_data, fontweight='bold')
        ax.set_xlabel('Minutes After Open Access')
        ax.set_ylabel('Correlation Coefficient')
        ax.set_ylim(-1, 1)
        fig.subplots_adjust(top=0.9)
        fig.savefig('p - ' + statistic + ' - ' + bone_data + '_m.png')
# ============== End ===================================================================================================























































# This experiment will be for correlation between drinking categories and bone density
for TotMins in xrange(1, 121):  # From 1 to 120 (this is the number of minutes to analyze).
    data_s = pd.read_csv('data_s' + str(TotMins) + '.csv', header=0, index_col=0)  # Data Statistics
    data_b = pd.read_csv('data_b' + str(TotMins) + '.csv', header=0, index_col=0)  # Data of Bone
    data_s["Drinking Category"] = np.nan
    data_b["Drinking Category"] = np.nan

    for k in xrange(0, Monkey.objects.count()):    # From 1 to ~211 (this is the number of monkeys to look for).
        m = Monkey.objects.all()[k]     # Retrieve the monkey object.
        # print m.mky_id in data_s.index
        if m.mky_id in data_s.index:
            data_s.loc[m.mky_id, 'Drinking Category'] = m.mky_drinking_category
            data_b.loc[m.mky_id, 'Drinking Category'] = m.mky_drinking_category
            # print m.mky_id, m.cohort, m.mky_gender, m.mky_age_at_intox, m.mky_drinking_category

    # print data_s
    # time.sleep(30)

    print data_s    # This prints the statistical results and then saves them to csv files
    print data_b

    data_s.to_csv('data_s_c_' + str(TotMins) + '.csv', encoding='utf-8')
    data_b.to_csv('data_b_c_' + str(TotMins) + '.csv', encoding='utf-8')
    data_s_c = data_s   # this copies will preserve the original data with gender info
    data_b_c = data_b
    # time.sleep(30)

    # And now we do this for each category, LD, BD, HD, VHD
    # ============== LD - Low Drinker ==================================================================================
    data_b = data_b_c[data_b_c['Drinking Category'] == 'LD']
    data_s = data_s_c[data_s_c['Drinking Category'] == 'LD']
    data_b.drop(['Drinking Category'], axis=1, inplace=True)
    data_s.drop(['Drinking Category'], axis=1, inplace=True)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '_c_LD.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '_c_LD.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '_c_LD.csv', encoding='utf-8')
    # ============== END of LD - Low Drinker Data Analysis =============================================================

    # ============== BD - Binge Drinker ==================================================================================
    data_b = data_b_c[data_b_c['Drinking Category'] == 'BD']
    data_s = data_s_c[data_s_c['Drinking Category'] == 'BD']
    data_b.drop(['Drinking Category'], axis=1, inplace=True)
    data_s.drop(['Drinking Category'], axis=1, inplace=True)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '_c_BD.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '_c_BD.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '_c_BD.csv', encoding='utf-8')
    # ============== END of BD - Binge Drinker Data Analysis =============================================================

    # ============== HD - Heavy Drinker ==================================================================================
    data_b = data_b_c[data_b_c['Drinking Category'] == 'HD']
    data_s = data_s_c[data_s_c['Drinking Category'] == 'HD']
    data_b.drop(['Drinking Category'], axis=1, inplace=True)
    data_s.drop(['Drinking Category'], axis=1, inplace=True)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '_c_HD.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '_c_HD.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '_c_HD.csv', encoding='utf-8')
    # ============== END of HD - Heavy Drinker Data Analysis =============================================================

    # ============== VHD - Very Heavy Drinker ==================================================================================
    data_b = data_b_c[data_b_c['Drinking Category'] == 'VHD']
    data_s = data_s_c[data_s_c['Drinking Category'] == 'VHD']
    data_b.drop(['Drinking Category'], axis=1, inplace=True)
    data_s.drop(['Drinking Category'], axis=1, inplace=True)

    corr_data_p = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # Here we create the DataFrame, but it
    corr_data_k = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # is blank; it only contains column and
    corr_data_s = pd.DataFrame(index=data_s.columns, columns=data_b.columns)    # row data. It is filled below.

    for idxm in data_s.columns:     # This loop iterates through all possible statistics, e.g., mean, std, sum, etc.
        for idxb in data_b.columns:     # This loop iterates through all bone data, e.g., Bone Area, etc.

            # print('Current is %s and %s' % (idxm, idxb))      # Uncomment this block if you want to see the results
            # print data_s[idxm].corr(data_b[idxb], method='pearson')   # as they are being generated.
            # print data_s[idxm].corr(data_b[idxb], method='kendall')
            # print data_s[idxm].corr(data_b[idxb], method='spearman')

            # This block calculates three different correlation coefficients and adds them to the blank DataFrames. So,
            # it computes the correlation between elements in the nested loops, e.g., the correlation between the mean
            # of the drinking (for a specific time frame, TotMins) and Bone Area.
            corr_data_p.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='pearson')
            corr_data_k.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='kendall')
            corr_data_s.at[idxm, idxb] = data_s[idxm].corr(data_b[idxb], method='spearman')

    # print corr_data_p     # Uncomment this block if you want to see the results after they were generated for each
    # time.sleep(1)         # specific time frame, TotMins.
    # print corr_data_k
    # time.sleep(1)
    # print corr_data_s

    corr_data_p.to_csv('Pearson_correlation_results_' + str(TotMins) + '_c_VHD.csv', encoding='utf-8')    # Save results to
    corr_data_k.to_csv('Kendall_correlation_results_' + str(TotMins) + '_c_VHD.csv', encoding='utf-8')    # csv format.
    corr_data_s.to_csv('Spearman_correlation_results_' + str(TotMins) + '_c_VHD.csv', encoding='utf-8')
    # ============== END of VHD - Very Heavy Drinker Data Analysis =============================================================
time.sleep(30)



data_s = pd.read_csv('data_s_c_120.csv', encoding='utf-8')
liCat = list(set(data_s['Drinking Category']))

CorrDataCubeP = np.zeros((24, 3, 120, len(liCat)))
CorrDataCubeK = np.zeros((24, 3, 120, len(liCat)))
CorrDataCubeS = np.zeros((24, 3, 120, len(liCat)))

corr_data_p_c = []
corr_data_k_c = []
corr_data_s_c = []

for TotMins in xrange(1, 121):  # 1 to 120
    tmpCounter = -1
    for sCat in liCat:
        tmpCounter += 1

        if pd.notnull(sCat):
            print 'Pearson_correlation_results_' + str(TotMins) + '_c_' + sCat + '.csv'

            corr_data_p_c = pd.read_csv('Pearson_correlation_results_' + str(TotMins) + '_c_' + sCat + '.csv', header=0, index_col=0)
            corr_data_k_c = pd.read_csv('Kendall_correlation_results_' + str(TotMins) + '_c_' + sCat + '.csv', header=0, index_col=0)
            corr_data_s_c = pd.read_csv('Spearman_correlation_results_' + str(TotMins) + '_c_' + sCat + '.csv', header=0, index_col=0)
            CorrDataCubeP[:, :, TotMins-1, tmpCounter] = corr_data_p_c.values
            CorrDataCubeK[:, :, TotMins-1, tmpCounter] = corr_data_k_c.values
            CorrDataCubeS[:, :, TotMins-1, tmpCounter] = corr_data_s_c.values

rows = list(corr_data_p_c.index.values)
cols = list(corr_data_p_c.columns.values)

print rows
print cols
print liCat

# print CorrDataCubeP[0, 0, :, 1]


# time.sleep(30)



# ============== all categories ================================================================================================
tmpCounter = -1
for sCat in liCat:
    tmpCounter += 1
    if pd.notnull(sCat):
        for statistic in rows:
            for bone_data in cols:
                fig, ax = plt.subplots()
                N = 3
                styles = ['-', '--', '-.', ':']
                markers = list('o+x^psDv')
                x = range(1, 121, 1)
                y = np.zeros((3, 120))
                y[0, :] = CorrDataCubeP[rows.index(statistic), cols.index(bone_data), :,  tmpCounter]
                y[1, :] = CorrDataCubeK[rows.index(statistic), cols.index(bone_data), :,  tmpCounter]
                y[2, :] = CorrDataCubeS[rows.index(statistic), cols.index(bone_data), :,  tmpCounter]
                labels = ['Pearson', 'Kendall', 'Spearman']

                # print y

                for i in range(N):
                    s = styles[i % len(styles)]
                    m = markers[i % len(markers)]
                    ax.plot(x, y[i, :], label=labels[i], marker=m, linewidth=2, linestyle=s)
                ax.grid(True)
                ax.legend(loc='best', prop={'size': 'large'})
                fig.suptitle('Correlation between ' + statistic + ' of % Drinking and ' + bone_data, fontweight='bold')
                ax.set_xlabel('Minutes After Open Access')
                ax.set_ylabel('Correlation Coefficient')
                ax.set_ylim(-1, 1)
                ax.set_title(sCat)
                fig.subplots_adjust(top=0.9)
                fig.savefig('p - ' + statistic + ' - ' + bone_data + '_c_' + sCat + '.png')
                # time.sleep(30)


# ============== End ===================================================================================================


































# This experiment will be for knowing information between drinking categories, gender, and bone density
TotMins = 1
data_b = pd.read_csv('data_b' + str(TotMins) + '.csv', header=0, index_col=0)  # Data of Bone
liBoneCols = list(data_b.columns.values)
# liUnits = [r'$\text{cm}^2$', r'$\text{g}', r'$\frac{\text{g}}{\text{cm}^2}$']
liUnits = ['cm$^2$', 'g', 'g/cm$^2$']


data_b["Drinking Category"] = np.nan
data_b["Sex"] = np.nan

for k in xrange(0, Monkey.objects.count()):    # From 1 to ~211 (this is the number of monkeys to look for).
    m = Monkey.objects.all()[k]     # Retrieve the monkey object.
    # print m.mky_id in data_s.index
    if m.mky_id in data_b.index:
        data_b.loc[m.mky_id, 'Drinking Category'] = m.mky_drinking_category
        data_b.loc[m.mky_id, 'Sex'] = m.mky_gender
        # print m.mky_id, m.cohort, m.mky_gender, m.mky_age_at_intox, m.mky_drinking_category

print data_b

data_b.to_csv('data_b_c_s.csv', encoding='utf-8')
data_b_c_s = data_b   # this copies will preserve the original data with gender info

liCat = list(set(data_b['Drinking Category']))
liCat = [x for x in liCat if x is not None]
liSex = list(set(data_b['Sex']))

print liCat
print liSex

females = np.zeros((1, len(liCat)))
stdFc = np.zeros((1, len(liCat)))
males = np.zeros((1, len(liCat)))
stdMc = np.zeros((1, len(liCat)))

# ============== all categories ================================================================================================

for aBoneCol, aUnit in zip(liBoneCols, liUnits):
    for aCat in range(len(liCat)):
        for aSex in range(len(liSex)):
            # print liCat[aCat]
            # print liSex[aSex]
            df = data_b[data_b['Drinking Category'] == liCat[aCat]]
            # print df
            # print 'reduced'
            # print df[aBoneCol].where(data_b['Sex'] == liSex[aSex])

            if aSex == 0:
                males[0, aCat] = df[aBoneCol].where(data_b['Sex'] == liSex[aSex]).mean()
                stdMc[0, aCat] = df[aBoneCol].where(data_b['Sex'] == liSex[aSex]).std()
            else:
                females[0, aCat] = df[aBoneCol].where(data_b['Sex'] == liSex[aSex]).mean()
                stdFc[0, aCat] = df[aBoneCol].where(data_b['Sex'] == liSex[aSex]).std()

    print males
    print stdMc
    print females
    print stdFc


    # print liBoneCols
    # time.sleep(30)

    # --- get the data
    before = males[0, :]
    after = females[0, :]
    labels = liCat

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    # the plot - left then right
    fig, ax = plt.subplots()

    width = 0.4     # bar width
    print before
    xlocs = np.arange(len(before))
    print xlocs
    ax.bar(xlocs-width, before, width, color='wheat', label='Males', yerr=stdMc[0, :], ecolor='k')
    ax.bar(xlocs, after, width, color='#8B7E66', label='Females', yerr=stdFc[0, :], ecolor='k')
    # --- labels, grids and title, then save
    ax.set_xticks(ticks=range(len(before)))
    ax.set_xticklabels(labels)
    ax.yaxis.grid(True)
    ax.legend(loc='best', prop={'size': 'small'})
    ax.set_ylabel('Average ' + aBoneCol + '  (' + aUnit + ')')
    fig.suptitle(aBoneCol + ' by Sex and Drinking Category', fontweight='bold')
    fig.tight_layout(pad=1)
    fig.subplots_adjust(top=0.93)
    fig.savefig('data_b_c_s ' + aBoneCol + '.png')


time.sleep(30)



# ============== End ===================================================================================================






















for aMonkey in Monkey.objects.all():
    print aMonkey.mky_age_at_intox
# mky_age_at_intox