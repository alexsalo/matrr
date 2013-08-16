import numpy, pylab

def convex_hull(points, graphic=False, smidgen=0.0075):
    '''Calculate subset of points that make a convex hull around points

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
    '''

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
