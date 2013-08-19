import numpy, pylab
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator


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

