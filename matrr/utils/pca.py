import numpy
from matplotlib import pyplot
from matrr import models, plotting


def swoon(field_list, cohort_pk=8, colors=False):
    color_values = list()

    data = models.MonkeyToDrinkingExperiment.objects.OA().filter(monkey__cohort=cohort_pk)
    if colors:
        categories = data.values_list('monkey__mky_drinking_category', flat=True) # only needed for colors, but need to pull the categories before casting data to a list
        color_values = [plotting.RHESUS_COLORS[cat] for cat in categories]
    data = list(data.values_list(*field_list))
    for index, row in enumerate(data):
        if None in row:
            data.pop(index)
    data = numpy.array(data)
    return data, color_values


def matplotlib_pca_test():
    from matplotlib import mlab

    fields = ['mtd_etoh_intake', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_etoh_media_ibi', 'mtd_pct_etoh_in_1st_bout']
    pca = mlab.PCA(swoon(fields)[0])
    print pca.Wt
    print '------'
    print pca.fracs
    print '------'
    print pca.Y

    print '!!!!!!!!!!!!'

    fields = list(reversed(fields))
    pca = mlab.PCA(swoon(fields)[0])
    print pca.Wt
    print '------'
    print pca.fracs
    print '------'
    print pca.Y

def mdp_pca_test():
    import mdp
    fields = ['mtd_etoh_intake', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_etoh_media_ibi', 'mtd_pct_etoh_in_1st_bout']
    print fields
    node = mdp.nodes.PCANode(output_dim=.95)
    test = node.execute(swoon(fields)[0])
    print test

    print '-------'

    fields = list(reversed(fields))
    print fields
    NODE = mdp.nodes.PCANode(output_dim=.95)
    TEST = NODE.execute(swoon(fields)[0])
    print TEST

def mpl_3d_pca():
    from matplotlib.mlab import PCA
    #construct your numpy array of data
#    fields = ['mtd_etoh_intake', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_etoh_media_ibi', 'mtd_pct_etoh_in_1st_bout']
    fields = ['mtd_etoh_intake', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_pct_etoh', 'mtd_etoh_g_kg', 'mtd_etoh_bout', 'mtd_etoh_drink_bout', 'mtd_etoh_mean_drink_length', 'mtd_etoh_median_idi', 'mtd_etoh_mean_drink_vol', 'mtd_etoh_mean_bout_length', 'mtd_etoh_media_ibi', 'mtd_etoh_mean_bout_vol', 'mtd_vol_1st_bout', 'mtd_pct_etoh_in_1st_bout', 'mtd_drinks_1st_bout', 'mtd_mean_drink_vol_1st_bout', 'mtd_latency_1st_drink', 'mtd_max_bout', 'mtd_max_bout_start', 'mtd_max_bout_end', 'mtd_max_bout_length', 'mtd_max_bout_vol', 'mtd_pct_max_bout_vol_total_etoh']
    myData, colors = swoon(fields, colors=True)
    results = PCA(myData)

    x = []
    y = []
    for item in results.Y:
     x.append(item[0])
     y.append(item[1])

    pyplot.close('all') # close all latent plotting windows
    fig1 = pyplot.figure() # Make a plotting figure
    ax = fig1.add_subplot(111) # use the plotting figure to create a Axis3D object.
    pltData = [x,y]
    ax.scatter(pltData[0], pltData[1], c=colors) # make a scatter plot of blue dots from the data

    # label the axes
    ax.set_xlabel("x-axis label")
    ax.set_ylabel("y-axis label")
    ax.set_title("The title of the plot")
    pyplot.show() # show the plot

#matplotlib_pca_test()
#mdp_pca_test()
#mpl_3d_pca()

