import os
import numpy
import json
from matrr.models import CohortBout, LIGHTS_OUT, LIGHTS_ON
from matrr.utils import apriori

def confederate_groups(cohort_pk, minutes, load_dataset, min_confidence=0, serializable=False):
    supports = dict()
    for _support in numpy.arange(.05, .96, .05):
        data = load_dataset(cohort_pk, minutes=minutes)
        l, sd = apriori.apriori(data, minsupport=_support)
        rules = apriori.generateRules(l, sd, min_confidence)
        supports[_support] = rules
    if serializable:
        supports = recreate_serializable_apriori_output(supports)
    return supports

def recreate_serializable_apriori_output(orig):
    new_dict = dict()
    for support, occurrences in orig.iteritems():
        new_occ = list()
        for cause, effect, confidence in occurrences:
            cause = tuple(cause)
            effect = tuple(effect)
            new_occ.append( (cause, effect, confidence) )
        new_dict[float(support)] = new_occ
    return new_dict

def get_all_confederate_groups(cohort_pk, minutes, min_confidence=0, dir_path='matrr/utils/DATA/apriori/'):
    def _fetch_all_CBT_monkey_groups(cohort_pk, minutes=0):
        cbts = CohortBout.objects.filter(cohort=cohort_pk, cbt_gap_definition=minutes*60)
        bout_groups = list()
        for cbt in cbts:
            monkeys = cbt.edr_set.all().values_list('ebt__mtd__monkey', flat=True).distinct()
            bout_groups.append(set(monkeys))
        return bout_groups

    file_name = "%d-%d-%.3f.json" % (cohort_pk, minutes, min_confidence)
    try:
        f = open(os.path.join(dir_path, file_name), 'r')
    except IOError:
        # pretty sure this will throw another IOException if dir_path doesn't exist
        f = open(os.path.join(dir_path, file_name), 'w')
    else:
        s = f.read()
        f.close()
        d = json.loads(s)
        return d

    supports = confederate_groups(cohort_pk, minutes, _fetch_all_CBT_monkey_groups, min_confidence=min_confidence, serializable=True)
    s = json.dumps(supports)
    f.write(s)
    f.close()
    return supports

def get_nighttime_confederate_groups(cohort_pk, minutes, min_confidence=0, dir_path='matrr/utils/DATA/apriori/', force_regen=False):
    def _fetch_nighttime_CBT_monkey_groups(cohort_pk, minutes=0):
        cbts = CohortBout.objects.filter(cohort=cohort_pk, cbt_gap_definition=minutes*60)
        cbts = cbts.filter(cbt_start_time__gte=LIGHTS_OUT).filter(cbt_start_time__lt=LIGHTS_ON)
        bout_groups = list()
        for cbt in cbts:
            monkeys = cbt.edr_set.all().values_list('ebt__mtd__monkey', flat=True)
            bout_groups.append(list(monkeys))
        return bout_groups

    file_name = "%d-%d-%.3f-nighttime.json" % (cohort_pk, minutes, min_confidence)
    if not force_regen:
        try:
            f = open(os.path.join(dir_path, file_name), 'r')
        except IOError:
            # This will throw another exception if dir_path doesn't exist
            f = open(os.path.join(dir_path, file_name), 'w')
        else:
            s = f.read()
            f.close()
            d = json.loads(s)
            return d
    else:
        f = open(os.path.join(dir_path, file_name), 'w')
    supports = confederate_groups(cohort_pk, minutes, _fetch_nighttime_CBT_monkey_groups, min_confidence=min_confidence, serializable=True)
    s = json.dumps(supports)
    f.write(s)
    f.close()
    return supports



def print_apriori_nighttime_minutes(cohort_pk=8, gap_minutes=()):
    for minutes in gap_minutes:
        print "Minutes=%d" % minutes
        supports = get_nighttime_confederate_groups(cohort_pk, minutes=minutes, force_regen=False)
        for key in sorted(supports.iterkeys()):
            print "%.2f - %s" % (float(key), str(supports[key]))
        print '---'

def dump_apriori_output(minutes=(20,)):
    for cohort_pk in [5,6,8,9,10]:
        for gap_minute in minutes:
            supports = get_nighttime_confederate_groups(cohort_pk, minutes=gap_minute, force_regen=False)

def load_apriori_output(cohort_pk, gap_minutes):
    supports = get_nighttime_confederate_groups(cohort_pk, gap_minutes)
    return supports
