from datetime import datetime as dt
import datetime
import string
import gc
from matrr import models

ERROR_OUTPUT = "%d %s # %s"


def get_monkey_by_number(mystery_number):
    try:
        monkey = models.Monkey.objects.get(pk=mystery_number)
    except models.Monkey.DoesNotExist:
        try:
            monkey = models.Monkey.objects.get(mky_real_id=mystery_number)
        except models.Monkey.DoesNotExist:
            raise Exception("No such monkey:  %s" % str(mystery_number))
    return monkey

def queryset_iterator(queryset, chunksize=5000):
    """
    http://djangosnippets.org/snippets/1949/

    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    """
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()

def get_datetime_from_steve(steve_date):
    def minimalist_xldate_as_datetime(xldate, datemode):
        # datemode: 0 for 1900-based, 1 for 1904-based
        return dt.datetime(1899, 12, 30) + dt.timedelta(days=int(xldate) + 1462 * datemode)

    try:
        real_date = dt.strptime(steve_date, "%m/%d/%y")
        return real_date
    except Exception as e:
        pass
    try:
        real_date = dt.strptime(steve_date, "%Y-%m-%d")
        return real_date
    except Exception as e:
        pass
    try:
        real_date = dt.strptime(steve_date, "%Y_%m_%d")
        return real_date
    except Exception as e:
        pass
    try:
        real_date = dt.strptime(steve_date, "%Y%m%d")
        return real_date
    except Exception as e:
        pass
    try:
        real_date = minimalist_xldate_as_datetime(steve_date, 1)
        return real_date
    except Exception as e:
        pass
    raise Exception("Unrecognized date format:  %s" % steve_date)

def convert_excel_time_to_datetime(time_string):
    DATE_BASE = dt(day=1, month=1, year=1904)
    SECONDS_BASE = 24 * 60 * 60
    data_days = int(time_string.split('.')[0])
    date_time = float("0.%s" % time_string.split('.')[1])
    seconds = round(date_time * SECONDS_BASE)
    return DATE_BASE + datetime.timedelta(days=data_days, seconds=seconds)

def parse_left_right(side_string):
    if string.count(side_string, "Left") != 0:
        return models.LeftRight.Left
    elif string.count(side_string, "Right") != 0:
        return models.LeftRight.Right
    else:
        return None



