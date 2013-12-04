from matrr.utils import apriori
import json


def print_apriori_nighttime_minutes(cohort_pk=8, gap_minutes=()):
    for minutes in gap_minutes:
        print "Minutes=%d" % minutes
        supports = apriori.get_nighttime_confederate_groups(cohort_pk, minutes=minutes, force_regen=False)
        for key in sorted(supports.iterkeys()):
            print "%.2f - %s" % (float(key), str(supports[key]))
        print '---'


def dump_apriori_output(minutes=(20,)):
    file_path = 'matrr/utils/DATA/apriori/'
    for cohort_pk in [5,6,8,9,10]:
        for gap_minute in minutes:
            supports = apriori.get_nighttime_confederate_groups(cohort_pk, minutes=gap_minute, force_regen=False)
            file_name = 'nighttime_confederates-%s-%s.json' % (str(cohort_pk), str(gap_minute))
            f = open(file_path+file_name, 'w')
            f.write(json.dumps(supports))
            f.close()

def load_apriori_output(cohort_pk, gap_minutes):
    file_path = 'matrr/utils/DATA/apriori/'
    file_name = 'nighttime_confederates-%s-%s.json' % (str(cohort_pk), str(gap_minutes))
    f = open(file_path+file_name, 'r')
    supports = json.loads(f.readline())
    f.close()
    return supports



