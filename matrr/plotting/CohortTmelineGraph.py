import matplotlib
from matplotlib import pyplot
from matrr import models, plotting


class CohortTimelineGraph(object):
    figure = pyplot.figure(figsize=plotting.DEFAULT_FIG_SIZE, dpi=plotting.DEFAULT_DPI)
    subplot = figure.add_subplot(111)
    cohorts = models.Cohort.objects.exclude(institution=434).order_by('institution')
    event_colors = dict() # must be populated by self._build_event_color_dict()

    def draw_subplot(self):
        self.subplot.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=.5)
        for coh_index, cohort in enumerate(self.cohorts):
            bar_lengths = list()
            bar_labels = list()
            events = models.CohortEvent.objects.filter(cohort=cohort).order_by('cev_date')
            events = list(events)
            before_OA = True
            for event_index in range(len(events)):
                try:
                    cev = events.pop(0)
                except IndexError:
                    break
                if 'start' in  cev.event.evt_name.lower():
                    start = cev
                    end = events.pop(0)
                    if before_OA and start.event.evt_name == 'First 6 mo Open Access Start':
                        before_OA = False
                    event_name = ''
                    for char_A, char_B in zip(start.event.evt_name, end.event.evt_name):
                        if char_A.lower() == char_B.lower():
                            event_name += char_A.lower()
                        else:
                            break
                    bar_labels.append(event_name)
                    offset_factor = -1 if before_OA else 1
                    event_length = (end.cev_date-start.cev_date).days * offset_factor
                    bar_lengths.append(event_length)
                else:
                    raise Exception("why didn't i hit a 'start' here?  %s" % str(cohort.pk))
            if not len(bar_lengths):
                continue
            for event_length in bar_lengths:
                self.subplot.bar(coh_index, event_length)

    def _build_event_color_dict(self):
        cevs = models.CohortEvent.objects.filter(cohort__in=self.cohorts)
        event_types = cevs.values_list('event').order_by().distinct()
        print len(event_types)
