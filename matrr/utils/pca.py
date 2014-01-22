import numpy
from matplotlib import pyplot
from matrr import models, plotting


def swoon(field_list, cohort_pk=8, colors=False, MATRR_MODEL=models.MonkeyToDrinkingExperiment):
    categories = list()
    color_values = list()

    data = MATRR_MODEL.objects.OA().exclude_exceptions().filter(monkey__cohort=cohort_pk)
    if colors:
        categories = data.values_list('monkey__mky_drinking_category', flat=True) # only needed for colors, but need to pull the categories before casting data to a list
        color_values = [plotting.RHESUS_COLORS[cat] for cat in categories]
    data = list(data.values_list(*field_list))
#    for index, row in enumerate(data):
#        if None in row:
#            data.pop(index)
    data = numpy.array(data, dtype=object)
    return data, categories, color_values

def matplotlib_pca_test():
    from matplotlib import mlab

    fields = ['mtd_etoh_intake', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_etoh_media_ibi', 'mtd_pct_etoh_in_1st_bout', 'mtd_etoh_g_kg']
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
    myData, categories, colors = swoon(fields, colors=True)
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

def find_empty_columns(cohort=8, empty_threshold=.5, MATRR_MODEL=models.MonkeyToDrinkingExperiment):
    mtds = MATRR_MODEL.objects.filter(monkey__cohort=cohort)
    mtd_count = float(mtds.count())
    if mtd_count == 0:
        raise ZeroDivisionError("No records for this cohort.")
    from django.db.models import DateField, DateTimeField, TimeField, TextField, CharField, AutoField, ForeignKey, OneToOneField, ManyToManyField, BooleanField
    exclude_field_types = (DateField, DateTimeField, TimeField, TextField, CharField, AutoField, ForeignKey, OneToOneField, ManyToManyField, BooleanField)
    fields = [f.name for f in MATRR_MODEL._meta.fields if type(f) not in exclude_field_types]

    empty_columns = list()
    full_columns = list()
    for field in fields:
        _mtds = mtds.exclude(**{field:None})
        pct = _mtds.count() / mtd_count
        if pct <= empty_threshold:
            print "%s :: %.2f" % (field, pct)
            empty_columns.append(field)
        else:
            full_columns.append(field)
    return full_columns, empty_columns

class ConfigObjectNeedsBetterName(object):
    cohort = 8
    matrr_model = models.MonkeyBEC
    empty_column_threshold = .5

    def __init__(self, cohort=8, matrr_model=models.MonkeyBEC, empty_column_threshold=.5):
        self.cohort = cohort
        self.matrr_model = matrr_model
        self.empty_column_threshold = empty_column_threshold

def PCA_data_collection_all_nonempty_model_fields(cfg=ConfigObjectNeedsBetterName()):
    from matplotlib import mlab
    full_columns, empty_columns = find_empty_columns(cfg.cohort, cfg.empty_column_threshold, cfg.matrr_model)

    data, categories, colors = swoon(full_columns, cohort_pk=cfg.cohort, MATRR_MODEL=cfg.matrr_model, colors=True)
    data = numpy.ma.masked_invalid(numpy.array(data, dtype=float))
    pca = mlab.PCA(data)

    print 'First Principle Component:  '
    for i in range(2):
        print "Principle Component %d" % i
        for index,column in enumerate(full_columns):
            print "%s:  %f" % (column, pca.Wt[5][index])

    first_principle_component = pca.Wt[0] * data
    second_principle_component = pca.Wt[1] * data
    X_axis = second_principle_component.sum(axis=1)
    Y_axis = first_principle_component.sum(axis=1)
    return X_axis, Y_axis, categories, colors

def matrr_pca_scatter(cfg=ConfigObjectNeedsBetterName()):
    X_axis, Y_axis, categories, colors = PCA_data_collection_all_nonempty_model_fields(cfg=cfg)

    from matrr.utils import plotting_beta
    fig = pyplot.figure(figsize=plotting_beta.DEFAULT_FIG_SIZE, dpi=plotting_beta.DEFAULT_DPI)
    main_gs = plotting_beta.gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title("Horray for PCA!")
    main_plot.set_xlabel("PC2")
    main_plot.set_ylabel("PC1")

    main_plot.scatter(X_axis, Y_axis, color=colors, s=30)
    return fig

def matrr_pca_scatter_centroids(cfg=ConfigObjectNeedsBetterName()):
    import collections
    from scipy import cluster
    from matrr.utils import plotting_beta

    fig = pyplot.figure(figsize=plotting_beta.DEFAULT_FIG_SIZE, dpi=plotting_beta.DEFAULT_DPI)
    main_gs = plotting_beta.gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title("ScatterCentroids")
    main_plot.set_xlabel("PC2 Centroids")
    main_plot.set_ylabel("PC1 Centroids")

    unorganized_data = PCA_data_collection_all_nonempty_model_fields(cfg=cfg)
    organized_data = collections.defaultdict(lambda: list())
    for datapoint in zip(*unorganized_data):
        X_value, Y_value, category, color = datapoint
        organized_data[category].append((X_value, Y_value))
    for category in organized_data.keys():
        plot_data = numpy.array(organized_data[category])
        res, idx = cluster.vq.kmeans2(plot_data, 1)
        centroid_xaxis = res[:, 0]
        centroid_yaxis = res[:, 1]
        main_plot.scatter(centroid_xaxis, centroid_yaxis, color=plotting.RHESUS_COLORS[category], s=150)
        main_plot.scatter(centroid_xaxis, centroid_yaxis, color=plotting.RHESUS_COLORS[category], s=300, marker='x')
    return fig

