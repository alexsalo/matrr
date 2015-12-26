__author__ = 'alex'
from matrr import settings
from matrr.models import CohortEvent, Cohort
from matplotlib import pyplot as plt
import pandas as pd
import json

DPI            = 100
WIDTH          = 1000  # to be consistent
HEIGHT         = 700   # with matrr styling of images
DPI_MULTIPLIER = 2     # we want to have actual picture of good quality

FIG_SIZE = (WIDTH * DPI_MULTIPLIER / DPI, HEIGHT * DPI_MULTIPLIER / DPI)

def create_cohorts_timeline():
    coords, coh_names, coh_ids = create_cohort_timeline_plot(collect_timeline_dataframes())

    # Dump JSON
    zipped_timeline_coords = zip(coords, coh_names, coh_ids)
    #context = {'headers': headers, 'data_rows': data_rows, 'last_updated': datetime.now().strftime('%Y-%m-%d') }

    if settings.DEBUG:
        outjson = open('/home/alex/pycharm/ve1/matrr/matrr/utils/DATA/json/current_cohorts_zipped_timeline.json', 'w')
    else:
        outjson = open('matrr/utils/DATA/json/current_cohorts_zipped_timeline.json', 'w')

    json_string = json.dumps({'zipped_timeline_coords': zipped_timeline_coords})
    outjson.write(json_string)
    outjson.close()

    return coords, coh_names, coh_ids

def get_cohort_timeline_durations(cohort):
    # Create canonical data frame with which all other to be aligned - for consistency
    canonical_coh = Cohort.objects.get(coh_cohort_name="INIA Rhesus 10")
    indexdf = pd.DataFrame(list(CohortEvent.objects.filter(cohort=canonical_coh).order_by('cev_date').
                                values_list('event__evt_name')), columns=['event'])
    indexdf.set_index('event', inplace=True)

    # Create data frame with events for current cohort
    cev = CohortEvent.objects.filter(cohort=cohort).order_by('cev_date')
    df = pd.DataFrame(list(cev.values_list('cev_date', 'event__evt_name')), columns=['date', 'event'])
    df.set_index('event', inplace=True)

    # Make consistent with canonical data frame
    df = pd.concat([indexdf, df], axis=1, join='inner')

    # Convert into date-time format; dates -> durations from first event
    df.date = pd.to_datetime(df.date)
    df[cohort.coh_cohort_name] = df.date.diff().fillna(0).dt.days

    # Filter out undesirable event names
    df['ind'] = df.index                    # ad-hoc for regex filters in next line
    df = df[df.ind.str.contains('.*End$')]

    # Drop auxillary info and return data frame
    df.drop(['ind', 'date'], axis=1, inplace=True)
    return df


def collect_timeline_dataframes():
    # we use one most representative cohort with to align the events
    r10df = get_cohort_timeline_durations(Cohort.objects.get(coh_cohort_name="INIA Rhesus 10"))

    # Find available cohort ids and get such cohorts
    coh_ids = list(CohortEvent.objects.all().values_list('cohort__coh_cohort_id', flat=True).distinct())
    coh_ids = [x for x in coh_ids if x not in [12, 13]]  # remove Rhesus 1 & 2
    timelined_cohorts = Cohort.objects.filter(coh_cohort_id__in=coh_ids)

    # Collect data frames
    dataframes_coh_durations = list()
    for cohort in timelined_cohorts:
        dataframes_coh_durations.append(get_cohort_timeline_durations(cohort))

    # Concat on index causes sorted index, so we keep our designed index of r10
    df = pd.concat(dataframes_coh_durations, axis=1).reindex(r10df.index)

    # Fill resulting NAs with 0 (in case event has not happened in given cohort)
    df = df.fillna(0)
    return df


def create_cohort_timeline_plot(df):
    # Find point of First 6mo OA and negate values before it
    align_point = df.index.get_loc('First 6 Month Open Access End')
    df.iloc[:align_point] = -df.iloc[:align_point]   # align on 1st6mo
    print "Creating cohort's timeline plots"

    # Aux for stacked barh: reverse values in list before 1st 6mo OA
    def reverse_before_align_point(list_to_reverse, align_point):
        list_to_reverse[:align_point] = reversed(list_to_reverse[:align_point])
        return list_to_reverse

    # Reindex to be linear in barh
    new_index = reverse_before_align_point(list(df.index), align_point)
    df = df.reindex(new_index)

    # Transpose data frame and Barh plot it
    df = df.transpose()
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    ax = fig.add_subplot(111)
    df.plot(kind='barh', stacked=True, ax=ax)
    ax.set_xlabel('Days')
    ax.set_ylabel('Cohort')

    # Adjust for the alignment
    xticks = ax.get_xticks()
    ax.set_xticklabels([(t - xticks[0]).astype(int) for t in xticks])  # start days from zero

    # Adjust labels and handles
    handles, labels = ax.get_legend_handles_labels()
    labels = [label[:-3] for label in labels]  # remove 'end' at labels
    ax.legend(reverse_before_align_point(handles, align_point), reverse_before_align_point(labels, align_point),
              loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    fig.subplots_adjust(right=0.65)

    # Save figure
    if settings.DEBUG:
        path = '/home/alex/MATRR/generated_cohorts_timeline.png'
    else:
        path = settings.STATIC_ROOT + '/images/generated_cohorts_timeline.png'
    plt.savefig(path, format='png')

    # Return a dict with barhs coordinates
    i = 0
    bar_coords = list()
    for p in ax.patches:
        if i < len(df):  # we only care about y-axis, so don't need all the patches
            i += 1

            # transform bbox into image coords and get coords [[x0, y0], [x1, y1]]
            bbox = p.get_bbox().transformed(ax.transData).get_points()

            # divide to compensate for multiplied resolution
            bar_coords.append(((bbox[0][1]/DPI_MULTIPLIER).astype(int), (bbox[1][1]/DPI_MULTIPLIER).astype(int)))

    # Patches coords are weird; this offset makes them correct.
    offset = ((bar_coords[0][1] - bar_coords[1][1])/DPI_MULTIPLIER).astype(int)

    # Collect coords in HTML5 map format
    coords = list()
    for c in bar_coords:
        coords.append('0,' + str(c[0]+offset) + ',1000,' + str(c[1]+offset))

    # Collect cohorts name, id for title and linkage
    coh_names = list(reversed(df.index))
    coh_ids = [Cohort.objects.get(coh_cohort_name=cname).coh_cohort_id for cname in coh_names]

    return coords, coh_names, coh_ids