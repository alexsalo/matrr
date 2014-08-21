import hashlib
import warnings

from matplotlib import pyplot, gridspec

from matrr import plotting


cached_data_path = "matrr/utils/DATA/MATRRScatterPlot/"

class MATRRScatterPlot(object):
    cached = False
    figure = None
    figure_title = 'MATRR Scatter Plot'

    def __init__(self, cached=False,):
        self.cached = cached

    def draw_scatter_plot(self):
        fig = pyplot.figure(figsize=(14, 9), dpi=plotting.DEFAULT_DPI)
        gs = gridspec.GridSpec(1, 1)
        gs.update(left=0.02, right=0.98, top=.95, bottom=.55)
        subplot = fig.add_subplot(gs[:, :])

        subplot.scatter(self.gather_xaxis_data(),
                        self.gather_yaxis_data(),
                        s=self.gather_scale_data(),
                        c=self.gather_color_data(),
                        alpha=self.gather_alpha_data(),
                        marker=self.gather_marker_data(),
                        alpha=self.gather_alpha_data(),
        )
        subplot.set_title(self.figure_title)
        self.figure = fig
        return fig

    def gather_xaxis_data(self):
        raise NotImplementedError()

    def gather_yaxis_data(self):
        raise NotImplementedError()

    def gather_scale_data(self):
        warnings.warn("Scale data not implemented!")
        return ()

    def gather_color_data(self):
        warnings.warn("Color data not implemented!")
        return ()

    def gather_marker_data(self):
        warnings.warn("Marker data not implemented!")
        return ()

    def gather_alpha_data(self):
        warnings.warn("Alpha data not implemented!")
        return ()

    def savefig(self, dpi=200):
        fig = self.draw_scatter_plot()
        m = hashlib.sha224()
        m.update(str(self))
        hash_name = m.hexdigest()
        file_name = str(self) + hash_name + '.png'
        fig.savefig(file_name, dpi=dpi)


    def __str__(self):
        return "MATRRScatterPlot"


