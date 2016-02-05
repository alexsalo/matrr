__author__ = 'farro'
import matplotlib
import numpy as np
from matplotlib import pyplot, cm, gridspec
from matplotlib import pyplot as plt
from django.db.models import Sum, Min, Max, Q
from matplotlib.cm import get_cmap
from matplotlib.ticker import MaxNLocator
import numpy, operator
from scipy.linalg import LinAlgError
from scipy.cluster import vq
from matrr.models import *
from matrr.utils.gadgets import Treemap
from matrr.plotting import * #specific_callables, plot_tools, DEFAULT_FIG_SIZE, DEFAULT_DPI, HISTOGRAM_FIG_SIZE, RHESUS_COLORS
import matplotlib.patches as mpatches

def cohort_oa_cumsum_drinking_pattern_22hr(cohort):
    return _cohort_oa_cumsum_drinking_pattern(cohorts=[cohort], schedule='22hr', remove_trend=False)
def cohort_oa_cumsum_drinking_pattern_daylight(cohort):
    return _cohort_oa_cumsum_drinking_pattern(cohorts=[cohort], schedule='Day Light', remove_trend=True)
def _cohort_oa_cumsum_drinking_pattern(cohorts, schedule='Day Light', remove_trend=False):
    # Redefining constants by Kathy's request (which kind of make sense by the look ofthe plot)
    LIGHTS_OUT = 7 * ONE_HOUR
    LIGHTS_ON = 20 * ONE_HOUR
    PREV_DAY_LIGHT = 22 * ONE_HOUR - LIGHTS_ON
    DAYLIGHT = PREV_DAY_LIGHT + LIGHTS_OUT

    def get_mky_oa_drinks_cumsum(mky):
        def get_mtd_drinks(mtd):
            try:
                bouts = ExperimentBout.objects.filter(mtd=mtd)
                edrs = ExperimentDrink.objects.filter(ebt__in=bouts).order_by('edr_start_time')

                drinks = pd.DataFrame(list(edrs.values_list('edr_start_time', 'edr_volume')),
                                      columns=['start_time', 'volume'])
                drinks.set_index('start_time', inplace=True)
                gkg_ratio = 0.04 / mtd.mtd_weight
                drinks['gkg'] = drinks.volume * gkg_ratio
                return drinks
            except Exception as e:
                print e
                pass

        mtds = MonkeyToDrinkingExperiment.objects.OA().filter(monkey=mky).order_by('drinking_experiment__dex_date')

        drinks_cumsum = get_mtd_drinks(mtds[0])
        imtd = 1
        while drinks_cumsum is None:  # make sure we got the data
            drinks_cumsum = get_mtd_drinks(mtds[imtd])
            imtd += 1
        print imtd, mky

        mtds_used = 1
        for mtd in mtds[imtd:]:
            drinks_cumsum = drinks_cumsum.append(get_mtd_drinks(mtd))
            mtds_used += 1

        drinks_cumsum.sort_index(inplace=True)
        return drinks_cumsum, mtds_used

    DURATION = SESSION_END if schedule == '22hr' else DAYLIGHT
    remove_trend_title = {True: '(De-trended) ', False: ''}
    remove_trend_legend_loc = {True: 3, False: 2}
    matplotlib.rc('font', family='monospace')
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111)

    monkeys = Monkey.objects.filter(cohort__in=cohorts).filter(mky_drinking=True).order_by('mky_drinking_category')

    for mky in monkeys:
        mky_drink_cumsum, mtds_used = get_mky_oa_drinks_cumsum(mky)

        if schedule == 'Day Light':
            mky_drink_cumsum['new_index'] = list(mky_drink_cumsum.index)
            mky_drink_cumsum.new_index[mky_drink_cumsum.new_index > LIGHTS_ON] -= TWENTYTWO_HOUR
            mky_drink_cumsum.new_index += PREV_DAY_LIGHT
            mky_drink_cumsum = mky_drink_cumsum.set_index('new_index').sort_index()
            mky_drink_cumsum = mky_drink_cumsum[mky_drink_cumsum.index < DAYLIGHT]  # Drop unseen

        # Normalize (average) values, remove trend and plot
        mky_drink_cumsum.gkg = mky_drink_cumsum.gkg.cumsum() / mtds_used
        mky_drink_cumsum.index /= ONE_HOUR * 1.0

        if remove_trend:
            fit = np.polyfit(mky_drink_cumsum.index, mky_drink_cumsum.gkg, deg=1)
            mky_drink_cumsum.gkg = mky_drink_cumsum.gkg - (fit[0] * mky_drink_cumsum.index + fit[1])

        #ax.plot(mky_drink_cumsum.index, fit[0] * mky_drink_cumsum.index + fit[1], color='k')
        mky_drink_cumsum.gkg.plot(color=DRINKING_CATEGORIES_COLORS[mky.mky_drinking_category], ax=ax,
                                  label="%3s" % mky.mky_drinking_category + ' ' + str(mky.mky_id))

    plt.legend(loc=remove_trend_legend_loc[remove_trend])
    if len(cohorts) > 1:  # Compress the legend - we have monkeys from multiple cohorts
        handles, labels = ax.get_legend_handles_labels()
        used_cols = []
        unique_handles = []
        unique_labels = []
        for i, handle in enumerate(handles):
            if handle.get_c() not in used_cols:
                used_cols.append(handle.get_c())
                unique_handles.append(handle)
                unique_labels.append(labels[i].split(' 1')[0])

        ax.legend(unique_handles, unique_labels, loc=remove_trend_legend_loc[remove_trend])

    # Plot pellets for entire cohort
    pellets_eevs = ExperimentEvent.objects.filter(monkey__in=monkeys).filter(eev_event_type=ExperimentEventType.Pellet)
    pellets = pd.DataFrame(list(pellets_eevs.values_list('eev_session_time', flat=True)))
    if schedule == 'Day Light':
        pellets += PREV_DAY_LIGHT
    pellets /= ONE_HOUR * 1.0
    ax_pellet = ax.twinx()
    pellets.hist(bins=10*60, ax=ax_pellet, alpha=.4)
    ax_pellet.set_ylabel('Pellet Consumption Distribution (Cohort)')
    ax_pellet.get_yaxis().set_ticks([])
    ax_pellet.set_xlabel('Time (session hour)')

    # Tune plot
    plt.xticks(np.arange(SESSION_START / ONE_HOUR, (DURATION / ONE_HOUR + 1), 1))
    if schedule == '22hr':
        plt.axvspan(LIGHTS_OUT/ONE_HOUR, LIGHTS_ON/ONE_HOUR, color='black', alpha=.2, zorder=-100)
    else:
        ax.set_xlim(0, DAYLIGHT / ONE_HOUR)

    ax.set_xlabel('Time (session hour)')
    ax.set_ylabel('Average ' + remove_trend_title[remove_trend] + 'cumulative EtOH (gkg)')
    cohort_short_names = [x.coh_cohort_name.encode('utf-8') for x in cohorts] # .split(' ')[2]
    plt.title("Cumulative Drinking Pattern for Cohort %s\n%s Session Schedule" % (cohort_short_names, schedule))
    if len(cohorts) == 1:  # annotate target start time if only one cohort
        target_start_time = cohorts[0].coh_target_start_time
        if target_start_time is not None:
            fig.text(0.065, 0.02, 'Target start time: %s' % target_start_time.strftime("%H:%M %p"), ha='left')
    plt.tight_layout()
    return fig, True


def cohort_weights_plot(cohort):
    """
    Create mky weights plots
    """
    def weight_plot_makeup(ax):
        handles, labels = ax.get_legend_handles_labels()
        labels = [label.split(', ')[1][:-1] for label in labels]
        ax.legend(handles, labels, loc='upper left')  # reverse to keep order consistent
        ax.set_ylabel('Monkey Weight')
        ax.set_title('Animals Weights Change')
        plt.tight_layout()

    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=cohort.monkey_set.all())\
        .filter(mtd_weight__isnull=False).order_by('drinking_experiment__dex_date')
    df = pd.DataFrame(list(mtds.values_list('monkey__mky_id', 'drinking_experiment__dex_date', 'mtd_weight')),
                      columns=['mky_id', 'Date', 'weight'])
    df_pivot = df.pivot_table(index='Date', columns='mky_id')
    matplotlib.rcParams.update({'font.size': 14})
    fig = plt.figure(figsize=DEFAULT_FIG_SIZE_ALEX, dpi=DEFAULT_DPI)
    ax = fig.add_subplot(111)
    df_pivot.plot(ax=ax)
    weight_plot_makeup(ax)
    return fig, True

def cohort_bec_correlation(cohort):
    if MonkeyBEC.objects.filter(monkey__in=cohort.monkey_set.all()).count() < 10:  # arbitrary call
        return False, False
    else:
        return _cohort_bec_correlation(cohort)
def _cohort_bec_correlation(cohort):
    def mky_bec_corr(mky):
        # 1. Filter work data set
        becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_g_kg__isnull=True)

        # 2. Get bec dates and corresponding day before and day after dates lists
        bec_dates = becs.values_list('bec_collect_date', flat=True)
        bec_dates_prev = [date + timedelta(days=-1) for date in bec_dates]
        bec_dates_next = [date + timedelta(days=+1) for date in bec_dates]

        # 3. Get corresponding mtds
        mtds_prev = mtds.filter(drinking_experiment__dex_date__in=bec_dates_prev)
        mtds_next = mtds.filter(drinking_experiment__dex_date__in=bec_dates_next)

        # 4. Find intersection: we need data for prev day, bec day and next day
        mtds_prev_dates = [date + timedelta(days=+1) for date in mtds_prev.values_list('drinking_experiment__dex_date', flat=True)]
        mtds_next_dates = [date + timedelta(days=-1) for date in mtds_next.values_list('drinking_experiment__dex_date', flat=True)]
        mtds_intersection_dates = set(mtds_prev_dates).intersection(mtds_next_dates)

        # 5. Retain becs and mtds within days of intersection
        becs_retained = becs.filter(bec_collect_date__in=mtds_intersection_dates).order_by('bec_collect_date')
        mtds_prev_retained = mtds_prev.filter(drinking_experiment__dex_date__in=[date + timedelta(days=-1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')
        mtds_next_retained = mtds_next.filter(drinking_experiment__dex_date__in=[date + timedelta(days=+1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')

        # 6. Assert we have the same number of data daysa
        assert becs_retained.count() == mtds_prev_retained.count() == mtds_next_retained.count()

        # 7. Compile data frame
        if mtds_prev_retained.count() == 0:
            return pd.DataFrame() # empty to be ignored
        bec_df = pd.DataFrame(list(mtds_prev_retained.values_list('mtd_etoh_g_kg')), columns=['etoh_previos_day'])
        bec_df['etoh_at_bec_sample_time'] = list(becs_retained.values_list('bec_gkg_etoh', flat=True))
        bec_df['etoh_next_day'] = list(mtds_next_retained.values_list('mtd_etoh_g_kg', flat=True))
        bec_df['bec'] = list(becs_retained.values_list('bec_mg_pct', flat=True))
        return bec_df

    # 1. Collect BECs correlation DFs for each monkey
    becs = MonkeyBEC.objects.filter(monkey__in=cohort.monkey_set.all())
    monkeys = Monkey.objects.filter(mky_id__in=becs.values_list('monkey__mky_id', flat=True).distinct())
    bec_df = mky_bec_corr(monkeys[0])
    for mky in monkeys[1:]:
        bec_df = bec_df.append(mky_bec_corr(mky))
    print "Total BECs: %s" % len(bec_df)

    # 2. Scatter plot correlations
    fig, axs = plt.subplots(1, 3, figsize=(15, 8), facecolor='w', edgecolor='k')
    bec_df.plot(kind='scatter', x='etoh_previos_day', y='bec', ax=axs[0])
    bec_df.plot(kind='scatter', x='etoh_at_bec_sample_time', y='bec', ax=axs[1])
    bec_df.plot(kind='scatter', x='etoh_next_day', y='bec', ax=axs[2])
    plt.tight_layout()

    # 9. Plot fitted lines and correlation values
    def plot_regression_line_and_corr_text(ax, x, y):
        fit = np.polyfit(x, y, deg=1)
        ax.plot(x, fit[0] * x + fit[1], color='red')

        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        text = 'Correlation: %s' % np.round(x.corr(y), 4)
        ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)

    plot_regression_line_and_corr_text(axs[0], bec_df.etoh_previos_day, bec_df.bec)
    plot_regression_line_and_corr_text(axs[1], bec_df.etoh_at_bec_sample_time, bec_df.bec)
    plot_regression_line_and_corr_text(axs[2], bec_df.etoh_next_day, bec_df.bec)
    return fig, True

def cohort_dopamine_study_boxplots_accumben(cohort):
    return _cohort_dopamine_study_boxplots_by_tissue_type(cohort, tissue_type='Nucleus accumbens (Core)')
def cohort_dopamine_study_boxplots_caudate(cohort):
    return _cohort_dopamine_study_boxplots_by_tissue_type(cohort, tissue_type='caudate')
def _cohort_dopamine_study_boxplots_by_tissue_type(cohort, tissue_type='Nucleus accumbens (Core)'):
    try:
        tst = TissueType.objects.get(tst_tissue_name__iexact=tissue_type)
    except:
        raise Exception('No such tissue type: %s' % tissue_type)
        return False, False

    if DopamineStudy.objects.filter(monkey__cohort=cohort).count():
        return _plot_dopamine_study_boxplots(cohort, tissue_type)
    else:
        return False, False

def _plot_dopamine_study_boxplots(cohort, tissue_type):
    """
    :param tissue_type:
    :return:
    Usage: plot_dopamine_study_boxplots('Nucleus accumbens (Core)')
    """
    # 1. Get data
    tst = TissueType.objects.get(tst_tissue_name__iexact=tissue_type)
    dopes = DopamineStudy.objects.filter(tissue_type=tst).filter(monkey__cohort=cohort)

    dopes_drink = dopes.filter(monkey__mky_drinking=True)
    dopes_control = dopes.filter(monkey__mky_drinking=False)
    print dopes_drink
    print dopes_control

    baseline_300nm_effect = [dope.baseline_effect_300nm() for dope in dopes_drink]
    baseline_1um_effect = [dope.baseline_effect_1um() for dope in dopes_drink]

    baseline_300nm_effect_control = [dope.baseline_effect_300nm() for dope in dopes_control]
    baseline_1um_effect_control = [dope.baseline_effect_1um() for dope in dopes_control]

    # 2. Plot
    data = [baseline_300nm_effect, baseline_300nm_effect_control,
            baseline_1um_effect, baseline_1um_effect_control]
    tool_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = tool_figure.add_subplot(111)
    labels = ['300nm_drink', '300nm_control', '1um_drink', '1um_control']
    ax1.boxplot(data, labels=labels)
    ax1.set_title('Baseline effect on dopamine elicitation by U-50488 stimulation\n'
              'at concentrations 300 nM and 1 uM; comparison drinking vs control animals.\n'
              'Tissue Type: %s' % tissue_type, fontsize=13)
    tool_figure.tight_layout()
    return tool_figure, 'build HTML fragment'


def cohort_bone_densities(cohort):
    """
    This method will create a cohort graph for bone densities
    """
    if BoneDensity.objects.filter(monkey__cohort=cohort).count():
        return _cohort_bone_densities(cohort)
    else:
        return False, False

def _cohort_bone_densities(cohort):
    """
    Makes a plot of bone densities for cohort
    :param cohort:
    :return: figure
    """
    ld_patch = mpatches.Patch(color='g', label='LD')
    bd_patch = mpatches.Patch(color='b', label='BD')
    hd_patch = mpatches.Patch(color='y', label='HD')
    vhd_patch = mpatches.Patch(color='r', label='VHD')
    control_patch = mpatches.Patch(color='k', label='Control')
    dc_colors = {
        'LD' : 'g',
        'BD' : 'b',
        'HD' : 'y',
        'VHD' : 'r',
        'None' : 'k',
        None : 'k'
    }

    tool_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = tool_figure.add_subplot(111)
    bds = BoneDensity.objects.filter(monkey__in=Monkey.objects.filter(cohort=cohort))
    df = pd.DataFrame(list(bds.values_list('monkey__mky_id', 'monkey__mky_drinking_category', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd')), columns=['mky_id', 'dc', 'tissue_type', 'bdy_area', 'bdy_bmc', 'bdy_bmd'])
    df.color = df.dc.apply(lambda x: dc_colors[x])
    ax1.scatter(df.bdy_area, df.bdy_bmc, c=df.color, s=80, alpha=0)
    for label, x, y, col in zip(df.mky_id, df.bdy_area, df.bdy_bmc, df.color):
        ax1.annotate(
            label,
            xy = (x, y), xytext = (20, -7),
            textcoords = 'offset points', ha = 'right', va = 'bottom',
            bbox = dict(boxstyle = 'round,pad=0.5', fc = col, alpha = 0.5))
    ax1.grid()
    ax1.set_xlabel(r'Bone Area $(cm^2)$')
    ax1.set_ylabel('Bone Mineral Content $(g)$')
    ax1.set_title('BMA and BMC for NHP cohort ' + cohort.coh_cohort_name)
    matplotlib.rcParams.update({'font.size': 16})
    for dc in ['LD', 'BD','HD','VHD', 'None']:
        if dc == 'None':
            df2 = df[~df.dc.isin(['LD', 'BD','HD','VHD'])]
        else:
            df2 = df[df.dc == dc]
        # drop NaN values for densities, kkep None DCs
        df2.dropna(subset = ['bdy_area', 'bdy_bmc', 'bdy_bmd'], inplace=True)
        if len(df2) > 1:
            fit = np.polyfit(df2.bdy_area, df2.bdy_bmc, 1)
            fit_fn = np.poly1d(fit)
            ax1.plot(df2.bdy_area, fit_fn(df2.bdy_area), dc_colors[dc], lw=2)
    ax1.legend(handles=[ld_patch, bd_patch, hd_patch, vhd_patch, control_patch], loc=4)
    return tool_figure, 'build HTML fragment'


def necropsy_get_data(cohort, db_columns, colnames, sortby):
    """
    Retrieve DataFrame for barh plot for summaries in NecropsySummary, used in methods below
    """
    ns = NecropsySummary.objects.filter(monkey__in=cohort.monkey_set.all())
    if ns.count():
        db_columns = ['monkey__mky_id', 'monkey__mky_drinking_category'] + db_columns
        colnames = ['Monkey ID', 'DC'] + colnames

        df = pd.DataFrame(list(ns.values_list(*db_columns)), columns=colnames)
        df['Monkey ID'] = df['Monkey ID'].map(str) + '\n' + df['DC'].map(str)
        df = df[df[colnames[2]] != 0]  # remove empty
        df.set_index('Monkey ID', inplace=True)
        df = df.sort(sortby)
        float_columns = [column for column in df.columns if df[column].dtype == 'float64']
        df[float_columns] = np.round(df[float_columns], 2)
        return df

def _cohort_necropsy_barh_plot_base(df, graph_title, x_label):
    """
    Create legend and annotate axis with values.
    """
    matplotlib.rcParams.update({'font.size': 14})
    if len(df) > 1: # arbitrary call to avoid problem with partial cohorts
        fig = plt.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
        ax = fig.add_subplot(111)
        df.plot(kind='barh', ax=ax)

        xlim = ax.get_xlim()
        ax.set_xlim(xlim[0], xlim[1] * 1.015)  # to fit annotation

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(reversed(handles), reversed(labels), loc='upper left')  # reverse to keep order consistent
        for p in ax.patches:
            ax.annotate(str(p.get_width()), (p.get_width() * 1.005, p.get_y() * 1.005))
        ax.set_title(graph_title)
        ax.set_xlabel(x_label)
        plt.tight_layout()
        return fig, 'map'
    else:
        return False, False


def cohort_necropsy_avg_etoh_22hr_gkg(cohort):
    df = necropsy_get_data(cohort, sortby=['First 6 Months Average', 'Second 6 Months Average', '12 Month Average'],
                           db_columns=['ncm_22hr_1st_6mo_avg_gkg', 'ncm_22hr_2nd_6mo_avg_gkg',
                                       'ncm_22hr_12mo_avg_gkg'],
                           colnames=['First 6 Months Average', 'Second 6 Months Average', '12 Month Average'])
    return _cohort_necropsy_barh_plot_base(df,
                                          graph_title="Average Daily EtOH Intake (g/kg)",
                                          x_label='Average Daily Ethanol Intake (g/kg)')


def cohort_necropsy_sum_etoh_ml(cohort):
    df = necropsy_get_data(cohort, sortby='Lifetime EtOH Intake (ml)',
                           db_columns=['ncm_etoh_sum_ml_4pct_induction', 'ncm_etoh_sum_ml_4pct_22hr', 'ncm_etoh_sum_ml_4pct_lifetime'],
                           colnames=['Induction EtOH Intake (ml)', 'Open Access EtOH Intake (ml)',
                                     'Lifetime EtOH Intake (ml)'])
    return _cohort_necropsy_barh_plot_base(df,
                                          graph_title="Total EtOH Intake (mL)",
                                          x_label="Ethanol intake (4% w/v)")


def cohort_necropsy_sum_etoh_gkg(cohort):
    df = necropsy_get_data(cohort, sortby='Lifetime EtOH Intake (g/kg)',
                           db_columns=['ncm_etoh_sum_gkg_induction', 'ncm_etoh_sum_gkg_22hr',
                                       'ncm_etoh_sum_gkg_lifetime'],
                           colnames=['Induction EtOH Intake (g/kg)', 'Open Access EtOH Intake (g/kg)',
                                     'Lifetime EtOH Intake (g/kg)'])
    return _cohort_necropsy_barh_plot_base(df,
                                          graph_title="Total EtOH Intake (g/kg)",
                                          x_label="Ethanol intake (4% w/v, g/kg)")


def cohort_necropsy_avg_bec_mg_pct(cohort):
    """
    barh showing each monkey's average open access bec values
    """
    df = necropsy_get_data(cohort, sortby=['First 6 Months Average', 'Second 6 Months Average', '12 Month Average'],
                           db_columns=['ncm_22hr_1st_6mo_avg_bec', 'ncm_22hr_2nd_6mo_avg_bec',
                                       'ncm_22hr_12mo_avg_bec'],
                           colnames=['First 6 Months Average', 'Second 6 Months Average', '12 Month Average'])
    return _cohort_necropsy_barh_plot_base(df,
                                          graph_title="Average Blood Ethanol Concentration (Open Access)",
                                          x_label='Average BEC (mg percent)')


def _cohort_tools_boxplot(data, title, x_label, y_label, scale_x=(), scale_y=()):
    tool_figure = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = tool_figure.add_subplot(111)
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    ax1.set_axisbelow(True)
    ax1.set_title(title)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)

    if scale_x:
        ax1.set_xlim(scale_x)
    if scale_y:
        ax1.set_ylim(scale_y)

    sorted_keys = [item[0] for item in sorted(data.items())]
    sorted_values = [item[1] for item in sorted(data.items())]
    scatter_y = []
    scatter_x = []
    for index, dataset in enumerate(sorted_values):
        for data in dataset:
            scatter_x.append(index+1)
            scatter_y.append(data)

    ax1.scatter(scatter_x, scatter_y, marker='+', color='purple', s=80)
    bp = ax1.boxplot(sorted_values)
    pyplot.setp(bp['boxes'], linewidth=3, color='black')
    pyplot.setp(bp['whiskers'], linewidth=3, color='black')
    pyplot.setp(bp['fliers'], color='red', marker='o', markersize=10)
    xtickNames = pyplot.setp(ax1, xticklabels=sorted_keys)
    pyplot.setp(xtickNames, rotation=45)
    return tool_figure

def cohort_protein_boxplot(cohort=None, protein=None):
#	from matrr.models import Cohort, Protein, MonkeyProtein
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    if not isinstance(protein, Protein):
        try:
            protein = Protein.objects.get(pk=protein)
        except Protein.DoesNotExist:
            print("That's not a valid protein.")
            return False, False

    monkey_proteins = MonkeyProtein.objects.filter(monkey__in=cohort.monkey_set.all(), protein=protein).order_by('mpn_date')
    if monkey_proteins.count() > 0:
        title = '%s : %s' % (str(cohort), str(protein))
        x_label = "Date of sample"
        y_label = "Sample Value, in %s" % str(protein.pro_units)
        dates = monkey_proteins.values_list('mpn_date', flat=True)
        data = dict()
        for date in dates:
            data[str(date.date())] = monkey_proteins.filter(mpn_date=date).values_list('mpn_value')
        fig = _cohort_tools_boxplot(data, title, x_label, y_label)
        return fig, False

    else:
        msg = "No MonkeyProteins for cohort %s, pk=%d." % (str(cohort), cohort.pk)
        logging.warning(msg)
        return False, False

def cohort_hormone_boxplot(cohort=None, hormone="", scaled=False):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            msg = "That's not a valid cohort: %s" % str(cohort)
            logging.warning(msg)
            return False, False
    hormone_field_names = [f.name for f in MonkeyHormone._meta.fields]
    if not hormone in hormone_field_names:
        msg = "That's not a MonkeyHormone field name: %s." % hormone
        logging.warning(msg)
        return False, False

    cohort_hormones = MonkeyHormone.objects.filter(monkey__in=cohort.monkey_set.all()).order_by('mhm_date')
    cohort_hormones = cohort_hormones.exclude(Q(**{hormone: None}))
    if cohort_hormones.count() > 0:
        title = '%s : %s' % (str(cohort), hormone)
        x_label = "Date of sample"
        y_label = "Hormone Value, %s" % MonkeyHormone.UNITS[hormone]
        dates = cohort_hormones.values_list('mhm_date', flat=True)
        data = dict()
        for date in dates:
            data[str(date.date())] = cohort_hormones.filter(mhm_date=date).values_list(hormone)

        scale_y = ()
        if scaled:
            min_field = "cbc_%s_min" % hormone
            max_field = "cbc_%s_max" % hormone
            cbcs = CohortMetaData.objects.exclude(Q(**{min_field: None})).exclude(Q(**{max_field: None}))
            cbc_scales = cbcs.aggregate(Min(min_field), Max(max_field))
            scale_y = (cbc_scales[min_field+"__min"], cbc_scales[max_field+'__max'])
        fig = _cohort_tools_boxplot(data, title, x_label, y_label, scale_y=scale_y)
        return fig, False

    else:
        msg = "No MonkeyHormones for cohort %s, pk=%d." % (str(cohort), cohort.pk)
        logging.warning(msg)
        return False, False

def cohort_etoh_bihourly_treemap(cohort, from_date=None, to_date=None, dex_type=''):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    size_cache = {}
    def size(thing):
        """sum size of child nodes"""
        if isinstance(thing, dict):
            thing = thing['volume']
        if isinstance(thing, int) or isinstance(thing, float):
            return thing
        if thing in size_cache:
            return size_cache[thing]
        else:
            size_cache[thing] = reduce(operator.add, [size(x) for x in thing])
            return size_cache[thing]

    max_color = 0
    cmap = cm.Greens
    def color_by_pct_of_max_color(color):
        try:
            pct_of_max = 1. * color / max_color
            return cmap(pct_of_max)
        except TypeError:
            return 'white'

    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    cohort_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__in=monkeys)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        cohort_mtds = cohort_mtds.filter(drinking_experiment__dex_date__gte=from_date)
    if to_date:
        cohort_mtds = cohort_mtds.filter(drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        cohort_mtds = cohort_mtds.filter(drinking_experiment__dex_type=dex_type)
    cohort_bouts = ExperimentBout.objects.filter(mtd__in=cohort_mtds)

    if not cohort_mtds.count() or not cohort_bouts.count():
        return False, False

    monkey_pks = []
    hour_const = 0
    experiment_len = 22
    block_len = 2
    tree = list()
    color_tree = list()
    for monkey in monkeys:
        monkey_pks.append(str(monkey.pk))
        monkey_mtds = cohort_mtds.filter(monkey=monkey)
        num_days = monkey_mtds.order_by().values_list('drinking_experiment__dex_date').distinct().count()

        monkey_bar = list()
        color_monkey_bar = list()
        for hour_start in range(hour_const,hour_const + experiment_len, block_len ):
            hour_end = hour_start + block_len
            fraction_start = (hour_start-hour_const)*60*60
            fraction_end = (hour_end-hour_const)*60*60

            bouts_in_fraction = cohort_bouts.filter(mtd__in=monkey_mtds, ebt_start_time__gte=fraction_start, ebt_start_time__lte=fraction_end)
            mtds_in_fraction = MonkeyToDrinkingExperiment.objects.filter(mtd_id__in=bouts_in_fraction.values_list('mtd', flat=True).distinct())
            volume_sum = bouts_in_fraction.aggregate(Sum('ebt_volume'))['ebt_volume__sum']

            field_name = 'mtd_pct_max_bout_vol_total_etoh_hour_%d' % (hour_start/2)
            max_bout_pct_total = mtds_in_fraction.exclude(**{field_name:None}).values_list(field_name, flat=True)

            if max_bout_pct_total:
                max_bout_pct_total = numpy.array(max_bout_pct_total)
                avg_max_bout_pct_total = numpy.mean(max_bout_pct_total)
            else:
                avg_max_bout_pct_total = 0

            if not volume_sum:
                volume_sum = 0.1
            if not avg_max_bout_pct_total:
                avg_max_bout_pct_total = 0.01

            if (num_days * block_len) == 0:
                avg_vol_per_hour = 0.01
            else:
                avg_vol_per_hour = volume_sum / float(num_days * block_len)

            monkey_bar.append(avg_vol_per_hour)
            color_monkey_bar.append(avg_max_bout_pct_total)
            max_color = max(max_color, avg_max_bout_pct_total)
        tree.append(tuple(monkey_bar))
        color_tree.append(tuple(color_monkey_bar))
    tree = tuple(tree)
    color_tree = tuple(color_tree)

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    left, width = 0.02, 0.73
    bottom, height = 0.05, .85
    left_h = left+width+0.07
    ax_dims = [left, bottom, width, height]

    ax = fig.add_axes(ax_dims)
    ax.set_aspect('equal')
    ax.set_yticks([])

    Treemap(ax, tree, color_tree, size, color_by_pct_of_max_color, x_labels=monkey_pks)

    graph_title = "Bi-hourly distribution of Ethanol Intake"
    if dex_type:
        graph_title +=  " during %s" % dex_type
    elif from_date and to_date:
        graph_title +=  "\nfrom %s, to %s" % (str(from_date.date()), str(to_date.date()))
    elif from_date:
        graph_title +=  " after %s" % str(from_date)
    elif to_date:
        graph_title +=  " before %s" % str(to_date)
    ax.set_title(graph_title)

    ## Custom Colorbar
    color_ax = fig.add_axes([left_h, bottom, 0.08, height])
    m = numpy.outer(numpy.arange(0,1,0.01),numpy.ones(10))
    color_ax.imshow(m, cmap=cmap, origin="lower")
    color_ax.set_xticks(numpy.arange(0))
    labels = [str(int((max_color*100./4)*i))+'%' for i in range(5)]
    color_ax.set_yticks(numpy.arange(0,101,25), labels)
    color_ax.set_title("Average maximum bout,\nby ethanol intake,\nexpressed as percentage \nof total daily intake\n")

    return fig, 'has_caption'

def cohort_etoh_induction_cumsum(cohort, stage=1):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    stages = dict()
    stages[0] = Q(eev_dose__lte=1.5)
    stages[1] = Q(eev_dose=.5)
    stages[2] = Q(eev_dose=1)
    stages[3] = Q(eev_dose=1.5)

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
#   main graph
    main_gs = gridspec.GridSpec(monkeys.count(), 40)
    main_gs.update(left=0.02, right=0.95, wspace=0, hspace=.01*monkeys.count()) # sharing xaxis

    stage_plot = fig.add_subplot(main_gs[0:1,2:41])
    stage_text = "Stage %d" % stage if stage else "Induction"
    stage_plot.set_title("%s Cumulative Intraday EtOH Intake for %s" % (stage_text, str(cohort)))
    for index, monkey in enumerate(monkeys):
        if index:
            stage_plot = fig.add_subplot(main_gs[index:index+1,2:41], sharex=stage_plot, sharey=stage_plot) # sharing xaxis
        eevs = ExperimentEvent.objects.filter(monkey=monkey, dex_type='Induction').exclude(eev_etoh_volume=None).order_by('eev_occurred')
        stage_x = eevs.filter(stages[stage])
        plot_tools._days_cumsum_etoh(stage_x, stage_plot)
        stage_plot.get_xaxis().set_visible(False)
        stage_plot.legend((), title=str(monkey), loc=1, frameon=False, prop={'size':12})

#	ylims = stage_plot.get_ylim()
    stage_plot.set_ylim(ymin=0, )#ymax=ylims[1]*1.05)
    stage_plot.yaxis.set_major_locator(MaxNLocator(3, prune='lower'))
    stage_plot.set_xlim(xmin=0)

    # yxes label
    ylabel = fig.add_subplot(main_gs[:,0:2])
    ylabel.set_axis_off()
    ylabel.set_xlim(0, 1)
    ylabel.set_ylim(0, 1)
    ylabel.text(.05, 0.5, "Cumulative EtOH intake, ml", rotation='vertical', horizontalalignment='center', verticalalignment='center')
    return fig, True

def cohort_etoh_gkg_quadbar(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False
    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    fig.suptitle(str(cohort), size=18)
    main_gs = gridspec.GridSpec(2, 2)
    main_gs.update(left=0.08, right=.98, top=.92, bottom=.06, wspace=.02, hspace=.23)

    cohort_colors =  ['navy', 'slateblue']
    main_plot = None # this is so the first subplot has a sharey.  all subplots after the first will use the previous loop's subplot
    subplots = [(i, j) for i in range(2) for j in range(2)]
    for gkg, _sub in enumerate(subplots, 1):
        main_plot = fig.add_subplot(main_gs[_sub], sharey=main_plot)
        main_plot.set_title("Greater than %d g per kg Etoh" % gkg)

        monkeys = Monkey.objects.Drinkers().filter(cohort=cohort).values_list('pk', flat=True)
        data = list()
        colors = list()
        for i, mky in enumerate(monkeys):
            colors.append(cohort_colors[i%2]) # we don't want the colors sorted.  It breaks if you try anyway.
            mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, mtd_etoh_g_kg__gte=gkg).count()
            mtds = mtds if mtds else .001
            data.append((mky, mtds))

        sorted_data = sorted(data, key=lambda t: t[1]) # sort the data by the 2nd tuple value (mtds).  This is important to keep yvalue-monkey matching
        sorted_data = numpy.array(sorted_data)
        yaxis = sorted_data[:,1] # slice off the yaxis values
        main_plot.bar(range(len(monkeys)), yaxis, width=.9, color=colors)

        labels = sorted_data[:,0] # slice off the labels
        x_labels = ["%d" % l for l in labels] # this ensures that the monkey label is "10023" and not "10023.0" -.-
        main_plot.set_xticks(range(len(monkeys))) # this will force a tick for every monkey.  without this, labels become useless
        xtickNames = pyplot.setp(main_plot, xticklabels=x_labels)
        pyplot.setp(xtickNames, rotation=45)

        # this hides the yticklabels and ylabel for the right plots
        if gkg % 2:
            main_plot.set_ylabel("Day count")
        else:
            main_plot.get_yaxis().set_visible(False)
    return fig, True

def cohort_bec_firstbout_monkeycluster(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None, cluster_count=1):
    """
        Scatter plot for monkey
            x axis - first bout / total intake
            y axis - BEC
            color - Monkey
    """
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
    if to_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
    if sample_before:
        bec_records = bec_records.filter(bec_sample__lte=sample_before)
    if sample_after:
        bec_records = bec_records.filter(bec_sample__gte=sample_after)
    bec_records = bec_records.order_by('bec_collect_date')

    if bec_records.count() > 0:
        dates = list(bec_records.dates('bec_collect_date', 'day').order_by('bec_collect_date'))
    else:
        return False, False

    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    ax1 = fig.add_subplot(111)


    mkys = bec_records.order_by().values_list('monkey__pk', flat=True).distinct()
    mky_count = float(mkys.count())

    cmap = get_cmap('jet')
    mky_color = dict()
    for idx, key in enumerate(mkys):
        mky_color[key] = cmap(idx / (mky_count -1))

    mky_datas = list()
    centeroids = list()
    for mky in mkys:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky, drinking_experiment__dex_date__in=dates)
        mtds = mtds.exclude(bec_record=None).order_by('drinking_experiment__dex_date')
        xaxis = mtds.values_list('mtd_pct_etoh_in_1st_bout', flat=True)
        yaxis = mtds.values_list('bec_record__bec_mg_pct', flat=True)
        color = mky_color[mky]

        ax1.scatter(xaxis, yaxis, c=color, s=40, alpha=.1, edgecolor=color)
        try:
            res, idx = vq.kmeans2(numpy.array(zip(xaxis, yaxis)), cluster_count)
            ax1.scatter(res[:,0],res[:,1], marker='o', s=100, linewidths=3, c=color, edgecolor=color)
            ax1.scatter(res[:,0],res[:,1], marker='x', s=300, linewidths=3, c=color)
            centeroids.append([res[:,0][0], res[:,1][0]])
        except LinAlgError: # I'm not sure what about kmeans2() causes this, or how to avoid it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass
        except ValueError: # "Input has 0 items" has occurred
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log_output = ''.join('!! ' + line for line in lines)
            logging.warning(log_output)
            pass

        mky_datas.append((mky, zip(xaxis, yaxis), color))

    def create_convex_hull_polygon(cluster, color, label):
        from matrr.utils.gadgets import convex_hull
        from matplotlib.path import Path
        try:
            hull = convex_hull(numpy.array(cluster).transpose())
        except AssertionError: # usually means < 5 datapoints
            return
        path = Path(hull)
        x, y = zip(*path.vertices)
        x = list(x)
        x.append(x[0])
        y = list(y)
        y.append(y[0])
        line = ax1.plot(x, y, c=color, linewidth=3, label=label)
        return line

    for mky, data, color in mky_datas:
        create_convex_hull_polygon(data, color, `mky`)

    title = 'Cohort %s ' % cohort.coh_cohort_name
    if sample_before:
        title += "before %s " % str(sample_before)
    if sample_after:
        title += "after %s " % str(sample_after)

    ax1.axhspan(79, 81, color='black', alpha=.4, zorder=-100)
    ax1.text(0, 82, "80 mg pct")
    ax1.set_title(title)
    ax1.set_xlabel("First bout / total intake")
    ax1.set_ylabel("Blood Ethanol Concentration, mg %")
    ax1.legend(loc="upper left")
    ax1.set_xlim(0)
    ax1.set_ylim(0)

    zipped = numpy.vstack(centeroids)
    coordinates = ax1.transData.transform(zipped)
    xcoords, inv_ycoords = zip(*coordinates)
    ycoords = [fig.get_window_extent().height-point for point in inv_ycoords]
    datapoint_map = zip(mkys, xcoords, ycoords)
    return fig, datapoint_map

def cohort_bec_monthly_centroid_distance_general(cohort, mtd_x_axis, mtd_y_axis, title, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    """
    """
    def add_1_month(date):
        new_month = date.month + 1
        if new_month > 12:
            return datetime(date.year+1, 1, date.day)
        else:
            return datetime(date.year, new_month, date.day)
    def euclid_dist(point_a, point_b):
        import math
        if not any(point_a) or not any(point_b):
            return 0
        return math.hypot(point_b[0]-point_a[0], point_b[1]-point_a[1])

    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    bec_records = MonkeyBEC.objects.filter(monkey__cohort=cohort)
    from_date, to_date = plot_tools.validate_dates(from_date, to_date)
    if from_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__gte=from_date)
    if to_date:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_date__lte=to_date)
    if dex_type:
        bec_records = bec_records.filter(mtd__drinking_experiment__dex_type=dex_type)
    if sample_before:
        bec_records = bec_records.filter(bec_sample__lte=sample_before)
    if sample_after:
        bec_records = bec_records.filter(bec_sample__gte=sample_after)
    bec_records = bec_records.order_by('bec_collect_date')

    if bec_records.count() > 0:
        dates = sorted(set(bec_records.dates('bec_collect_date', 'month').distinct()))
        bar_x_labels = [_date.strftime('%h %Y') for _date in dates]
        bar_x = numpy.arange(0, len(dates)-1)
    else:
        return False, False

    monkeys = Monkey.objects.Drinkers().filter(cohort=cohort)

    cmap = get_cmap('jet')
    month_count = float(len(dates))
    month_color = dict()
    for idx, key in enumerate(dates):
        month_color[key] = cmap(idx / (month_count-1))

    mky_datas = dict()
    for mky in monkeys:
        bar_y = list()
        colors = list()
        for _date in dates:
            min_date = _date
            max_date = add_1_month(_date)
            color = month_color[_date]

            cohort_mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=cohort,
                                                                    drinking_experiment__dex_date__gte=min_date,
                                                                    drinking_experiment__dex_date__lt=max_date)
            cohort_mtds = cohort_mtds.exclude(bec_record= None).exclude(bec_record__bec_mg_pct = None).exclude(bec_record__bec_mg_pct = 0)
            month_data = list()
            if cohort_mtds.filter(monkey=mky):
                month_data.append(cohort_mtds.filter(monkey=mky))
                month_data.append(cohort_mtds.exclude(monkey=mky))
            if not month_data:
                # still need values stored for this monkey-month if there is no data
                bar_y.append(0)
                colors.append(color)
            else:
                coh_center = (0,0)
                mky_center = (0,0)
                for index, mtd_set in enumerate(month_data): # mtd_set[0] == monkey, mtd_set[1] == cohort
                    _xaxis = numpy.array(mtd_set.values_list(mtd_x_axis, flat=True))
                    _yaxis = mtd_set.values_list(mtd_y_axis, flat=True)

                    try:
                        res, idx = vq.kmeans2(numpy.array(zip(_xaxis, _yaxis)), 1)
                    except Exception as e:
                        # keep default coh/mky center as (0,0)
                        if not index: # if it's a monkey center
                            colors.append(color) # stash the color for later
                    else:
                        if index:
                            coh_center = [res[:,0][0], res[:,1][0]]
                        else:
                            mky_center = [res[:,0][0], res[:,1][0]]
                            colors.append(color)
                bar_y.append(euclid_dist(mky_center, coh_center))
        mky_datas[mky] = (bar_y, colors)


    fig = pyplot.figure(figsize=DEFAULT_FIG_SIZE, dpi=DEFAULT_DPI)
    main_gs = gridspec.GridSpec(monkeys.count(), 40)
    main_gs.update(left=0.03, right=0.98, wspace=0, hspace=.1) # sharing xaxis

    ax_index = 0
    ax = None
    for mky, data in mky_datas.items():
        ax = fig.add_subplot(main_gs[ax_index:ax_index+1, 3:], sharex=ax, sharey=ax)
        if ax_index == 0:
            ax.set_title(title)
        ax.legend((), title=str(mky.pk), loc=1, frameon=False, prop={'size':12})
        ax_index += 1
        bar_y, colors = data
        for _x, _y, _c in zip(bar_x, bar_y, colors):
            # this forloop, while appearing stupid, works out well when there is missing data between monkeys in the cohort.
            ax.bar(_x, _y, color=_c, edgecolor='none')
            ax.get_xaxis().set_visible(False)


    ax.get_xaxis().set_visible(True)
    ax.set_xticks(bar_x)
    ax.set_xticklabels(bar_x_labels, rotation=45)
    ax.yaxis.set_major_locator(MaxNLocator(2, prune='lower'))

    # yxes label
    ylabel = fig.add_subplot(main_gs[:,0:2])
    ylabel.set_axis_off()
    ylabel.set_xlim(0, 1)
    ylabel.set_ylim(0, 1)
    ylabel.text(.05, 0.5, "Euclidean distance between k-means centroids", rotation='vertical', horizontalalignment='center', verticalalignment='center')

    return fig, True

def cohort_bec_mcd_sessionVSbec(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    title = 'Euclidean monkey-cohort k-means centroids distance, etoh volume vs bec, by month'
    if sample_before:
        title += ", before %s" % str(sample_before)
    if sample_after:
        title += ", after %s" % str(sample_after)

    return cohort_bec_monthly_centroid_distance_general(cohort, 'bec_record__bec_vol_etoh', 'bec_record__bec_mg_pct', title,
                                                        from_date, to_date, dex_type, sample_before, sample_after)

def cohort_bec_mcd_beta(cohort, from_date=None, to_date=None, dex_type='', sample_before=None, sample_after=None):
    title = 'Euclidean monkey-cohort k-means centroids distance, median ibi vs bec, by month'
    if sample_before:
        title += ", before %s" % str(sample_before)
    if sample_after:
        title += ", after %s" % str(sample_after)
    return cohort_bec_monthly_centroid_distance_general(cohort, 'mtd_etoh_media_ibi', 'bec_record__bec_mg_pct', title,
                                                        from_date, to_date, dex_type, sample_before, sample_after)


def _cohort_etoh_max_bout_cumsum(cohort, subplot):
    mkys = Monkey.objects.Drinkers().filter(cohort=cohort).values_list('pk', flat=True)

    subplot.set_title("Induction St. 3 Cumulative Max Bout EtOH Intake for %s" % str(cohort))
    subplot.set_ylabel("Volume EtOH / Monkey Weight, mL./kg")

    mky_colors = dict()
    mky_ymax = dict()
    for idx, m in enumerate(mkys):
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=m, drinking_experiment__dex_type="Induction").exclude(
            mtd_max_bout_vol=None).order_by('drinking_experiment__dex_date')
        mtds = mtds.filter(mtd_etoh_g_kg__gte=1.4).filter(mtd_etoh_g_kg__lte=1.6)
        if not mtds.count():
            continue
        mky_colors[m] = RHESUS_COLORS[Monkey.objects.get(mky_id=m).mky_drinking_category]
        volumes = numpy.array(mtds.values_list('mtd_max_bout_vol', flat=True))
        weights = numpy.array(mtds.values_list('mtd_weight', flat=True))
        vw_div = volumes / weights
        yaxis = numpy.cumsum(vw_div)
        mky_ymax[m] = yaxis[-1]
        xaxis = numpy.array(mtds.values_list('drinking_experiment__dex_date', flat=True))
        subplot.plot(xaxis, yaxis, alpha=1, linewidth=3, color=mky_colors[m], label=str(m))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    legend = subplot.legend(loc=2)
    pyplot.setp(legend.legendHandles, lw=15)
    if not len(mky_ymax.values()):
        raise Exception("no MTDs found")
    return subplot, mky_ymax, mky_colors

def _cohort_etoh_horibar_ltgkg(cohort, subplot, mky_ymax, mky_colors):
    subplot.set_title("Lifetime EtOH Intake for %s" % str(cohort))
    subplot.set_xlabel("EtOH Intake, g/kg")

    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        etoh_sum = mtds.aggregate(Sum('mtd_etoh_g_kg'))['mtd_etoh_g_kg__sum']
        bar_widths.append(etoh_sum)
        bar_colors.append(mky_colors[mky])
        if len(bar_y):
            highest_bar = bar_y[len(bar_y) - 1] + bar_height
        else:
            highest_bar = 0 + bar_height
        if ymax > highest_bar:
            bar_y.append(ymax)
        else:
            bar_y.append(highest_bar)
    subplot.barh(bar_y, bar_widths, height=bar_height, color=bar_colors)
    subplot.set_yticks([])
    subplot.xaxis.set_major_locator(MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot

def _cohort_etoh_horibar_3gkg(cohort, subplot, mky_ymax, mky_colors):
    subplot.set_title("# days over 3 g/kg")

    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))

    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_3widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        bar_3widths.append(mtds.filter(mtd_etoh_g_kg__gt=3).count())
        bar_colors.append(mky_colors[mky])
        if len(bar_y):
            highest_bar = bar_y[len(bar_y) - 1] + bar_height
        else:
            highest_bar = 0 + bar_height
        if ymax > highest_bar:
            bar_y.append(ymax)
        else:
            bar_y.append(highest_bar)
    subplot.barh(bar_y, bar_3widths, height=bar_height, color=bar_colors)
    subplot.set_yticks([])
    subplot.xaxis.set_major_locator(MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot

def _cohort_etoh_horibar_4gkg(cohort, subplot, mky_ymax, mky_colors):
    subplot.set_title("# days over 4 g/kg")
    sorted_ymax = sorted(mky_ymax.iteritems(), key=operator.itemgetter(1))
    bar_height = max(mky_ymax.itervalues()) / len(mky_ymax.keys()) / 5.
    bar_4widths = list()
    bar_y = list()
    bar_colors = list()
    for mky, ymax in sorted_ymax:
        mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_intake=None)
        bar_4widths.append(mtds.filter(mtd_etoh_g_kg__gt=4).count())
        bar_colors.append(mky_colors[mky])
        if len(bar_y):
            highest_bar = bar_y[len(bar_y) - 1] + bar_height
        else:
            highest_bar = 0 + bar_height
        if ymax > highest_bar:
            bar_y.append(ymax)
        else:
            bar_y.append(highest_bar)
    subplot.barh(bar_y, bar_4widths, height=bar_height, color=bar_colors)
    subplot.set_yticks([])
    subplot.xaxis.set_major_locator(MaxNLocator(4, prune='lower'))
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=45)
    return subplot

def cohort_etoh_max_bout_cumsum_horibar_3gkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except Exception as e:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_3gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, 'build HTML fragment'

def cohort_etoh_max_bout_cumsum_horibar_4gkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except Exception as e:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_4gkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, 'build HTML fragment'

def cohort_etoh_max_bout_cumsum_horibar_ltgkg(cohort):
    if not isinstance(cohort, Cohort):
        try:
            cohort = Cohort.objects.get(pk=cohort)
        except Cohort.DoesNotExist:
            print("That's not a valid cohort.")
            return False, False

    fig = pyplot.figure(figsize=HISTOGRAM_FIG_SIZE, dpi=DEFAULT_DPI)
    gs = gridspec.GridSpec(3, 3)
    gs.update(left=0.06, right=0.98, wspace=.00, hspace=0)
    line_subplot = fig.add_subplot(gs[:, :2])
    try:
        line_subplot, mky_ymax, mky_colors = _cohort_etoh_max_bout_cumsum(cohort, line_subplot)
    except Exception as e:
        return None, False
    bar_subplot = fig.add_subplot(gs[:, 2:], sharey=line_subplot)
    bar_subplot = _cohort_etoh_horibar_ltgkg(cohort, bar_subplot, mky_ymax, mky_colors)
    return fig, 'build HTML fragment'

# Dictionary of ethanol cohort plots VIPs can customize
COHORT_ETOH_TOOLS_PLOTS = {"cohort_etoh_bihourly_treemap": (cohort_etoh_bihourly_treemap, "Cohort Bihourly Drinking Pattern"),}
# BEC plots
COHORT_BEC_TOOLS_PLOTS = {'cohort_bec_firstbout_monkeycluster': (cohort_bec_firstbout_monkeycluster, 'Monkey BEC vs First Bout'),
                          'cohort_bec_correlation': (cohort_bec_correlation, "Cohort's total EtOH - BEC correlation"),
                          }
# Dictionary of protein cohort plots VIPs can customize
COHORT_PROTEIN_TOOLS_PLOTS = {"cohort_protein_boxplot": (cohort_protein_boxplot, "Cohort Protein Boxplot")}
# Dictionary of hormone cohort plots VIPs can customize
COHORT_HORMONE_TOOLS_PLOTS = {"cohort_hormone_boxplot": (cohort_hormone_boxplot, "Cohort Hormone Boxplot")}

# Dictionary of Monkey Tools' plots
COHORT_TOOLS_PLOTS = dict()
COHORT_TOOLS_PLOTS.update(COHORT_ETOH_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_BEC_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_PROTEIN_TOOLS_PLOTS)
COHORT_TOOLS_PLOTS.update(COHORT_HORMONE_TOOLS_PLOTS)

# Dictionary of all cohort plots
COHORT_PLOTS = {}
COHORT_PLOTS.update(COHORT_TOOLS_PLOTS)
COHORT_PLOTS.update({"cohort_necropsy_avg_etoh_22hr_gkg": (cohort_necropsy_avg_etoh_22hr_gkg, 'Average Ethanol Intake, 22hr'),
                     "cohort_necropsy_sum_etoh_ml": (cohort_necropsy_sum_etoh_ml, "Total Ethanol Intake, ml"),
                     "cohort_necropsy_sum_etoh_gkg": (cohort_necropsy_sum_etoh_gkg, "Total Ethanol Intake, g per kg"),
                     "cohort_necropsy_avg_bec_mg_pct": (cohort_necropsy_avg_bec_mg_pct, "Average BEC, 22hr"),
                     'cohort_etoh_induction_cumsum': (cohort_etoh_induction_cumsum, 'Cohort Induction Daily Ethanol Intake'),
                     'cohort_etoh_max_bout_cumsum_horibar_ltgkg': (cohort_etoh_max_bout_cumsum_horibar_ltgkg, "Cohort Cumulative Daily Max Bout, Lifetime EtOH Intake"),
                     'cohort_etoh_max_bout_cumsum_horibar_3gkg': (cohort_etoh_max_bout_cumsum_horibar_3gkg, "Cohort Cumulative Daily Max Bout, Day count over 3 g per kg"),
                     'cohort_etoh_max_bout_cumsum_horibar_4gkg': (cohort_etoh_max_bout_cumsum_horibar_4gkg, "Cohort Cumulative Daily Max Bout, Day count over 4 g per kg"),
                     'cohort_etoh_gkg_quadbar': (cohort_etoh_gkg_quadbar, "Cohort Daily Ethanol Intake Counts"),
                     "cohort_bone_densities": (cohort_bone_densities, 'Bone Area and Content Trends by DC '),
                     "cohort_dopamine_study_boxplots_accumben": (cohort_dopamine_study_boxplots_accumben, 'Dopamine release on opioid stimulation. Acumbencore'),
                     "cohort_dopamine_study_boxplots_caudate": (cohort_dopamine_study_boxplots_caudate, 'Dopamine release on opioid stimulation. Caudate'),
                     "cohort_weights_plot": (cohort_weights_plot, 'Weight Change Over OA in Cohort'),
                     "cohort_oa_cumsum_drinking_pattern_22hr": (cohort_oa_cumsum_drinking_pattern_22hr, '22hr Drinking Pattern'),
                     "cohort_oa_cumsum_drinking_pattern_daylight": (cohort_oa_cumsum_drinking_pattern_daylight, 'Day Light Drinking Pattern'),
                     })

