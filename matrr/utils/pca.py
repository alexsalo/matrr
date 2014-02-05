import numpy
from matplotlib import pyplot
from matrr import models, plotting
from matrr.utils import plotting_beta


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
            empty_columns.append(field)
        else:
            full_columns.append(field)
    return sorted(full_columns), sorted(empty_columns)

class PCAConfiguration(object):
    figure_title = "Horray for PCA!"
    notes = "Notes are for jokes"
    cohort = 5
    include_mtd_columns = True
    columns = list()

    def __init__(self, cohort=cohort, include_mtd_columns=True):
        self.cohort = cohort
        self.figure_title = "cohort_pk=%d" % cohort
        self.include_mtd_columns = include_mtd_columns
        self.generate_columns()

    def dump_self_to_json(self):
        ego = {'figure_title': self.figure_title, 'notes': self.notes, 'cohort': str(self.cohort)}
        ego['include_mtd_columns'] = self.include_mtd_columns
        serialiazed_ego = json.dumps(ego)
        return serialiazed_ego

    def fetch_mtd_columns(self):
        mtd_columns = ['mtd_total_pellets', 'mtd_weight', 'mtd_pct_etoh', 'mtd_etoh_g_kg', 'mtd_etoh_conc', 'mtd_pct_etoh_in_1st_bout', 'mtd_drinks_1st_bout',
                       'mtd_mean_drink_vol_1st_bout', 'mtd_mean_seconds_between_meals']
        mtd_columns = ['mtd__'+_c for _c in mtd_columns]
        return mtd_columns

    def generate_columns(self):
        columns = list()
        if self.include_mtd_columns:
            columns.extend(self.fetch_mtd_columns())
        self.columns = columns

    def get_data_row_count(self, data_model):
        data = data_model.objects.OA().exclude_exceptions().filter(monkey__cohort=self.cohort)
        return data.count()

    def gather_pca_data(self):
        data = list()
        categories = list()
        color_values = list()
        return data, categories, color_values


class PCAConfigMonkeyBEC(PCAConfiguration):
    def __init__(self, *args, **kwargs):
        super(PCAConfigMonkeyBEC, self).__init__(*args, **kwargs)
        self.figure_title += " - BEC"
        self.notes = "\n".join(self.columns)

    def generate_columns(self):
        super(PCAConfigMonkeyBEC, self).generate_columns()
        self.columns.extend(['bec_daily_gkg_etoh', 'bec_gkg_etoh', 'bec_mg_pct', 'bec_pct_intake', 'bec_vol_etoh', 'bec_weight'])

    def gather_pca_data(self): # Used to be named self.__swoon() and swoon()
        becs = models.MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey__cohort=self.cohort)
        categories = becs.values_list('monkey__mky_drinking_category', flat=True) # only needed for colors, but need to pull the categories before casting data to a list
        color_values = [plotting.RHESUS_COLORS[cat] for cat in categories]
        data = list(becs.values_list(*self.columns))
        return data, categories, color_values


class PCAConfigMonkeyHormone(PCAConfiguration):
    def __init__(self, *args, **kwargs):
        super(PCAConfigMonkeyHormone, self).__init__(*args, **kwargs)
        self.figure_title += " - Hormones"
        self.notes = "\n".join(self.columns)

    def generate_columns(self):
        super(PCAConfigMonkeyHormone, self).generate_columns()
        self.columns.extend(['mhm_cort', 'mhm_acth', 'mhm_t', 'mhm_doc', 'mhm_ald', 'mhm_dheas'])

    def gather_pca_data(self): # Used to be named self.__swoon() and swoon()
        mhms = models.MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey__cohort=self.cohort)
        categories = mhms.values_list('monkey__mky_drinking_category', flat=True) # only needed for colors, but need to pull the categories before casting data to a list
        color_values = [plotting.RHESUS_COLORS[cat] for cat in categories]
        data = list(mhms.values_list(*self.columns))
        return data, categories, color_values


def pca_data_collections(cfg=PCAConfigMonkeyBEC()):
    """
    """
    from matplotlib import mlab
    data, categories, colors = cfg.gather_pca_data()
    data = numpy.array(data, dtype=float)
    pca = mlab.PCA(data)

    first_principle_component = pca.Wt[0] * data
    second_principle_component = pca.Wt[1] * data
    X_axis = second_principle_component.sum(axis=1)
    Y_axis = first_principle_component.sum(axis=1)
    return X_axis, Y_axis, categories, colors

def pca_data_exploration(cfg=PCAConfigMonkeyBEC()):
    from matplotlib import mlab

    bec_field_names = ['bec_daily_gkg_etoh', 'bec_gkg_etoh', 'bec_mg_pct', 'bec_pct_intake', 'bec_vol_etoh', 'bec_weight']
    mtd_field_names = []
    bad_field_names = list()
    for field_index, _field in enumerate(models.MonkeyToDrinkingExperiment._meta.fields):
        try:
            data, categories, colors = cfg.get_data_find_bad_columns(bec_field_names=bec_field_names, mtd_field_names=mtd_field_names)
            data = numpy.array(data, dtype=float)
            pca = mlab.PCA(data)
            mtd_field_names.append(_field.name)
        except:
            bad_field_names.append(_field.name)
    print bad_field_names
    print '--'
    print mtd_field_names

def matrr_pca_scatter(cfg=PCAConfiguration()):
    X_axis, Y_axis, categories, colors = pca_data_collections(cfg=cfg)

    from matrr.utils import plotting_beta
    fig = pyplot.figure(figsize=plotting_beta.DEFAULT_FIG_SIZE, dpi=plotting_beta.DEFAULT_DPI)
    main_gs = plotting_beta.gridspec.GridSpec(3, 40)
    main_gs.update(left=0.08, right=.98, wspace=0, hspace=0)
    main_plot = fig.add_subplot(main_gs[:, :])
    main_plot.set_title(cfg.figure_title)
    main_plot.set_xlabel("PC2")
    main_plot.set_ylabel("PC1")

    main_plot.text(.98, .98, cfg.notes, bbox=dict(facecolor='black', alpha=0.1), transform=main_plot.transAxes, horizontalalignment='right', verticalalignment='top')
    main_plot.scatter(X_axis, Y_axis, color=colors, alpha=1, s=50)
    return fig

def matrr_pca_scatter_centroids(cfg=PCAConfigMonkeyBEC()):
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

    unorganized_data = pca_data_collections(cfg=cfg)
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

def dump_BEC_MHM_PCA_graphs(cohorts=(5,6,9,10), BEC=True, MHM=True, dump_image=False):
    def dump_json_config(cfg, file_path):
        f = open(file_path, 'w')
        json_data = cfg.dump_self_to_json()
        f.write(json_data)
        f.close()
    counter = 0
    filename_template = "%s_PCA_Figure_%d"
    for include_mtd_columns in [True, False]:
        for cohort_pk in cohorts:
            if BEC:
                bec_cfg = PCAConfigMonkeyBEC(cohort_pk, include_mtd_columns=include_mtd_columns)
                bec_fig = matrr_pca_scatter(bec_cfg)
                if dump_image:
                    filename = filename_template % ('BEC', counter)
                    plotting_beta.dump_figure_to_file(bec_fig, filename+'.png')
                    dump_json_config(bec_cfg, filename+'.json')
                counter += 1
            if MHM:
                mhm_cfg = PCAConfigMonkeyHormone(cohort_pk, include_mtd_columns=include_mtd_columns)
                mhm_fig = matrr_pca_scatter(mhm_cfg)
                if dump_image:
                    filename = filename_template % ('MHM', counter)
                    plotting_beta.dump_figure_to_file(mhm_fig, filename+'.png')
                    dump_json_config(mhm_cfg, filename+'.json')
                counter += 1