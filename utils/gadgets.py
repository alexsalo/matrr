import numpy, pylab
from django.db.models import Max, Min
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator
from scipy import stats
from matrr.models import MonkeyToDrinkingExperiment, Avg, MonkeyBEC, MonkeyHormone
from matrr import plotting


def convex_hull(points, graphic=False, smidgen=0.0075):
    """
    Calculate subset of points that make a convex hull around points

    Recursively eliminates points that lie inside two neighbouring points until only convex hull is remaining.

    :Parameters:
        points : ndarray (2 x m)
            array of points for which to find hull
        graphic : bool
            use pylab to show progress?
        smidgen : float
            offset for graphic number labels - useful values depend on your data range

    :Returns:
        hull_points : ndarray (2 x n)
            convex hull surrounding points
    """

    def _angle_to_point(point, centre):
        '''calculate angle in 2-D between points and x axis'''
        delta = point - centre
        res = numpy.arctan(delta[1] / delta[0])
        if delta[0] < 0:
            res += numpy.pi
        return res

    def _draw_triangle(p1, p2, p3, **kwargs):
        tmp = numpy.vstack((p1, p2, p3))
        x, y = [x[0] for x in zip(tmp.transpose())]
        pylab.fill(x, y, **kwargs)

    #time.sleep(0.2)
    def area_of_triangle(p1, p2, p3):
        '''calculate area of any triangle given co-ordinates of the corners'''
        return numpy.linalg.norm(numpy.cross((p2 - p1), (p3 - p1), axis=0)) / 2.


    if graphic:
        pylab.clf()
        pylab.plot(points[0], points[1], 'ro')
    n_pts = points.shape[1]
    #	assert(n_pts > 5)
    centre = points.mean(1)
    if graphic: pylab.plot((centre[0],), (centre[1],), 'bo')
    angles = numpy.apply_along_axis(_angle_to_point, 0, points, centre)
    pts_ord = points[:, angles.argsort()]
    if graphic:
        for i in xrange(n_pts):
            pylab.text(pts_ord[0, i] + smidgen, pts_ord[1, i] + smidgen, '%d' % i)
    pts = [x[0] for x in zip(pts_ord.transpose())]
    prev_pts = len(pts) + 1
    k = 0
    while prev_pts > n_pts:
        prev_pts = n_pts
        n_pts = len(pts)
        if graphic: pylab.gca().patches = []
        i = -2
        while i < (n_pts - 2):
            Aij = area_of_triangle(centre, pts[i], pts[(i + 1) % n_pts])
            Ajk = area_of_triangle(centre, pts[(i + 1) % n_pts], \
                                   pts[(i + 2) % n_pts])
            Aik = area_of_triangle(centre, pts[i], pts[(i + 2) % n_pts])
            if graphic:
                _draw_triangle(centre, pts[i], pts[(i + 1) % n_pts], \
                               facecolor='blue', alpha=0.2)
                _draw_triangle(centre, pts[(i + 1) % n_pts], \
                               pts[(i + 2) % n_pts], \
                               facecolor='green', alpha=0.2)
                _draw_triangle(centre, pts[i], pts[(i + 2) % n_pts], \
                               facecolor='red', alpha=0.2)
            if Aij + Ajk < Aik:
                if graphic: pylab.plot((pts[i + 1][0],), (pts[i + 1][1],), 'go')
                del pts[i + 1]
            i += 1
            n_pts = len(pts)
        k += 1
    return numpy.asarray(pts)


def Treemap(ax, node_tree, color_tree, size_method, color_method, x_labels=None):
    def addnode(ax, node, color, lower=[0, 0], upper=[1, 1], axis=0):
        axis %= 2
        draw_rectangle(ax, lower, upper, node, color)
        width = upper[axis] - lower[axis]
        try:
            for child, color in zip(node, color):
                upper[axis] = lower[axis] + (width * float(size_method(child))) / size_method(node)
                addnode(ax, child, color, list(lower), list(upper), axis + 1)
                lower[axis] = upper[axis]
        except TypeError:
            pass

    def draw_rectangle(ax, lower, upper, node, color):
        c = color_method(color)
        r = Rectangle(lower, upper[0] - lower[0], upper[1] - lower[1],
                      edgecolor='k',
                      facecolor=c)
        ax.add_patch(r)

    def assign_x_labels(ax, labels):
        def sort_patches_by_xcoords(patches):
            sorted_patches = []
            # This method returns a list of patches sorted by each patch's X coordinate
            xcoords = sorted([patch.get_x() for patch in patches])
            for x in xcoords:
                for patch in patches:
                    if patch.get_x() == x:
                        sorted_patches.append(patch)
            return sorted_patches

        patches = ax.patches
        # A primary_patch is a Rectangle which takes up the full height of the treemap.  In the cohort treemap implementation, a primary patch is a monkey
        primary_patches = [patch for patch in patches if patch.get_height() == 1 and patch.get_width() != 1]
        sorted_patches = sort_patches_by_xcoords(primary_patches)

        label_locations = []
        patch_edge = 0
        for patch in sorted_patches:
            width = patch.get_width()
            _location = patch_edge + (width / 2.)
            label_locations.append(_location)
            patch_edge += width

        Axis_Locator = FixedLocator(label_locations)
        ax.xaxis.set_major_locator(Axis_Locator)
        ax.set_xticklabels(labels, rotation=45)


    addnode(ax, node_tree, color_tree)
    if x_labels:
        assign_x_labels(ax, x_labels)
    else:
        ax.set_xticks([])

#### Specific callables used by other gadgets and/or plotting_beta (so far)
def get_mean_MTD_oa_field(monkey, field, six_months=0, three_months=0):
    """
    Designed to be used by get_percentile_callable){ and gather_monkey_three_month_average_by_field(), etc

    It will get the average value of a field from the MTD table for a given monkey, filtered by a quarter or a half of open access
    """
    assert not (six_months and three_months), "You cannot gather six month and three month intervals at the same time."
    if six_months == 1:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).first_six_months_oa()
    elif six_months == 2:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).second_six_months_oa()
    elif three_months == 1:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).first_three_months_oa()
    elif three_months == 2:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).second_three_months_oa()
    elif three_months == 3:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).third_three_months_oa()
    elif three_months == 4:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey).fourth_three_months_oa()
    else:
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey)
    return mtds.aggregate(Avg(field))[field+'__avg']

def get_mean_BEC_oa_field(monkey, field, six_months=0, three_months=0):
    """
    Designed to be used by get_percentile_callable){ and gather_monkey_three_month_average_by_field(), etc

    It will get the average value of a field from the BEC table for a given monkey, filtered by a quarter or a half of open access
    """
    assert not (six_months and three_months), "You cannot gather six month and three month intervals at the same time."
    if six_months == 1:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).first_six_months_oa()
    elif six_months == 2:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).second_six_months_oa()
    elif three_months == 1:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).first_three_months_oa()
    elif three_months == 2:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).second_three_months_oa()
    elif three_months == 3:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).third_three_months_oa()
    elif three_months == 4:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey).fourth_three_months_oa()
    else:
        becs = MonkeyBEC.objects.OA().exclude_exceptions().filter(monkey=monkey)
    return becs.aggregate(Avg(field))[field+'__avg']

def get_mean_MHM_oa_field(monkey, field, six_months=0, three_months=0):
    """
    Designed to be used by get_percentile_callable){ and gather_monkey_three_month_average_by_field(), etc

    It will get the average value of a field from the MHM table for a given monkey, filtered by a quarter or a half of open access
    """
    assert not (six_months and three_months), "You cannot gather six month and three month intervals at the same time."
    if six_months == 1:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey).first_six_months_oa()
    elif six_months == 2:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey).second_six_months_oa()
    elif three_months == 1:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey).first_three_months_oa()
    elif three_months == 2:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey).second_three_months_oa()
    elif three_months == 3:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey).third_three_months_oa()
    elif three_months == 4:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey).fourth_three_months_oa()
    else:
        mhms = MonkeyHormone.objects.OA().exclude_exceptions().filter(monkey=monkey)
    return mhms.aggregate(Avg(field))[field+'__avg']
####

def get_callable(field):
    if 'mtd' in field:
        return get_mean_MTD_oa_field
    if 'bec' in field:
        return get_mean_BEC_oa_field
    if 'mhm' in field:
        return get_mean_MHM_oa_field

def get_percentile_of_callable(monkey, monkeys, specific_callable, field, six_months=0, three_months=0):
    """
    This function converts a value generated by specific_callable into a percentile.  This percentile describes where
    monkey's data is compared to monkeys' values.

    monkey, field, six_months and three_months are parameters passed to specific_callable.
    """
    this_value = None
    all_values = list()
    for mky in monkeys:
        value = specific_callable(mky, field, six_months=six_months, three_months=three_months)
        all_values.append(value)
        if mky == monkey:
            this_value = value
    if this_value is None:
        raise Exception("monkey was not found in the monkeys collection.")
    return stats.percentileofscore(all_values, this_value)

def gather_monkey_percentiles_by_six_months(monkeys, six_months=0):
    """
    six_months == (0,1,2)
        0 == all OA
        1 == first 6 months of OA
        2 == second 6 months of OA

    This will return two variables, data{} and labels[].

    -Labels[] describe the data that's been collected
    -data{} is the collection of data
        keys are monkey pks
        values are 2-d numpy arrays.
            x-array is the index described by labels[]
            y-array is the monkey's percentile of labels[index] as compared to the other monkeys
    """
    # high drinkers == high percentiles
    high_high = ['mtd_etoh_g_kg', 'mhm_ald', 'bec_mg_pct', 'mtd_veh_intake', 'mtd_max_bout_vol']
    hh_label = ["Avg Daily Etoh (g/kg)", "Avg Aldosterone", "Avg BEC (% mg)", "Average Daily h20 (ml)", "Avg Daily Max Bout (ml)"]
    # high drinkers == low percentiles
    high_low = ['mhm_acth', 'mtd_pct_max_bout_vol_total_etoh', 'mhm_doc', 'mtd_total_pellets', 'mtd_latency_1st_drink',
                'bec_pct_intake']
    hl_label = ["Avg ACTH", "Avg Daily Max Bout / Total", "Avg Deoxycorticosterone", "Avg Daily Pellets",
                "Avg Time to First Drink (s)", "Avg % Etoh Before BEC Sample"]
    # scattered
    scattered = ['mhm_cort', 'mhm_t', 'mhm_dheas', 'mhm_ald_stdev', 'mhm_doc_stdev', 'mhm_acth_stdev']

    explore = []

    fields = []
    labels = []
    fields.extend(high_high)
    fields.extend(high_low)
    labels.extend(hh_label)
    labels.extend(hl_label)
#    fields = ['mtd_etoh_g_kg', 'mhm_ald', 'bec_mg_pct', 'mtd_veh_intake', 'mtd_total_pellets', 'mtd_latency_1st_drink']

    data = dict()
    for monkey in monkeys:
        x_values = list()
        y_values = list()
        x = 0
        for field in fields:
            field_callable = get_callable(field)
            x_values.append(x)
            # this is a lazy, computationally intensive way to calculate this.  This could be refactored to be MUCH more efficient.
            # todo: refactor this so that we collect all the raw values once, and then calculate the percentile from these values
            # this collect all the raw values for all monkeys, every monkey.
            y_values.append(get_percentile_of_callable(monkey, monkeys, field_callable, field, six_months=six_months))
            x += 1
        data[monkey] = numpy.array(zip(x_values, y_values))
    return data, labels

def gather_three_month_monkey_percentiles_by_fieldname(monkeys, fieldname, three_months=0, six_months=0):
    """
    three_months == (0,1,2,3,4)
        1 == first 3 months of OA
        2 == second 3 months of OA
        3 == third 3 months of OA
        4 == fourth 3 months of OA
    six_months == (0,1,2)
        1 == first 6 months of OA
        2 == second 6 months of OA
    if six_months == three_months == 0, run on all of OA

    -data{} is the collection of data
        keys are monkey pks
        values is the monkey's percentile of fieldname's average over 3/6/all months of OA as compared to the other monkeys over the same period of OA
            These monkey's do not have to be from the same cohort.  It will be run on each monkey's section of OA
    """
    data = dict()
    for monkey in monkeys:
        field_callable = get_callable(fieldname)
        data[monkey] = get_percentile_of_callable(monkey, monkeys, field_callable, fieldname, three_months=three_months, six_months=six_months)
    return data

def gather_three_month_monkey_average_by_fieldname(monkeys, fieldname, three_months=0, six_months=0):
    """
    three_months == (0,1,2,3,4)
        1 == first 3 months of OA
        2 == second 3 months of OA
        3 == third 3 months of OA
        4 == fourth 3 months of OA
    six_months == (0,1,2)
        1 == first 6 months of OA
        2 == second 6 months of OA
    if six_months == three_months == 0, run on all of OA
    """
    data = dict()
    for monkey in monkeys:
        field_callable = get_callable(fieldname)
        data[monkey] = field_callable(monkey, fieldname, three_months=three_months, six_months=six_months)
    return data


def identify_drinking_category(mtd_queryset):
    assert len(mtd_queryset.values_list('monkey', flat=True).distinct()) == 1, "Nothing about this function will work with an MTD queryset with multiple monkeys"
    max_date = mtd_queryset.aggregate(Max('drinking_experiment__dex_date'))['drinking_experiment__dex_date__max']
    min_date = mtd_queryset.aggregate(Min('drinking_experiment__dex_date'))['drinking_experiment__dex_date__min']
    total_days = float((max_date-min_date).days)
    days_over_two = mtd_queryset.filter(mtd_etoh_g_kg__gt=2).count()
    days_over_three = mtd_queryset.filter(mtd_etoh_g_kg__gt=3).count()
    days_over_four = mtd_queryset.filter(mtd_etoh_g_kg__gt=4).count()

    pct_over_two = days_over_two / total_days
    pct_over_three = days_over_three / total_days
    pct_over_four = days_over_four / total_days

    is_BD = pct_over_two >= .55
    is_HD = pct_over_three >= .2
    is_VHD = pct_over_four >= .1

    if is_VHD:
        return 'VHD'
    elif is_HD:
        return 'HD'
    elif is_BD:
        return 'BD'
    return 'LD'
    
def get_category_population_by_quarter(quarter, monkeys=plotting.ALL_RHESUS_DRINKERS):
    quarter = str(quarter).lower()
    if quarter == 'first' or quarter == '1':
        mtd_queryset = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkeys).first_three_months_oa()
    elif quarter == 'second' or quarter == '2':
        mtd_queryset = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkeys).second_three_months_oa()
    elif quarter == 'third' or quarter == '3':
        mtd_queryset = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkeys).third_three_months_oa()
    elif quarter == 'fourth' or quarter == '4':
        mtd_queryset = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey__in=monkeys).fourth_three_months_oa()
    else:
        raise Exception("Quarter can only be ('first', 'second', 'third', 'fourth') or (1,2,3,4)")
    category_results = [identify_drinking_category(mtd_queryset.filter(monkey=monkey)) for monkey in monkeys]
    return category_results
