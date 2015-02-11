__author__ = 'alex'
from datetime import datetime as dt
import string
import csv
import re
from django.db.transaction import commit_on_success
from django.db import transaction

from matrr.models import *
from matrr.utils.database import dingus, create

def load_bec_data_vervet(file_name, overwrite=False, header=True):
    def format_time(unformatted):
        """
        Converts "hh:MM AM" into HH:MM
        --OR--
        -- because consistency is overrated --
        Converts "hh:MM:SS AM" into HH:MM
        --OR--
        -- BECAUSE CONSISTENCY IS WILDLY OVERRATED --
        Converts "HH:MM:SS" into HH:MM
        """
        if 'am' in unformatted.lower() or 'pm' in unformatted.lower():
            time, afternoon = unformatted.split(' ')
            colon_separated_time = time.split(":")
            if afternoon.lower() == 'pm':
                HH = int(colon_separated_time[0]) + 12
            else:
                HH = int(colon_separated_time[0])
            HH = 12 if HH == 24 else HH
            return "%s:%s" % (str(HH), str(colon_separated_time[1]))
        HHMMSS = unformatted.split(":")
        if len(HHMMSS) == 3:
            return "%s:%s" % (HHMMSS[0], HHMMSS[1])
        return unformatted

    fields = (
    '__bec_collect_date', # 0
    '__dummy',    #1
    '__sample_num', #2
    'mky_real_id', # 3
    'bec_session_start', # 4
    'bec_vol_etoh', # 5
    'bec_gkg_etoh', # 6
    'bec_mg_pct', # 7
    'bec_daily_gkg_etoh', # 8
    )
    print_warning = True
    FIELDS_INDEX = (0, 9) #(4,15) => 4,5,6,7,8,9,10,11,12,13,14
    with open(file_name, 'r') as f:
        read_data = f.readlines()
        offset = 1 if header else 0
        for line_number, line in enumerate(read_data[offset:]):
            print line_number, len(read_data)
            if not line:
                continue # usually just the last line, which is blank
            # split the line assuming its tab-delimited
            data = line.split("\t")
            # BUT!
            if len(data) == 1: # if there's only one value in the list...
                # then homie decided 'fuck the man AND your standards!'
                # see if it's comma-separated -.-
                data = line.split(',')
            if len(data) == 1: # If it's STILL not right
                # fuck it, i quit.
                raise Exception("WTF!  I have no idea how this file's cells are separated.  Tabs and commas failed.")
            try:
                monkey = Monkey.objects.get(mky_real_id=data[3])
            except Monkey.DoesNotExist:
                print dingus.ERROR_OUTPUT % (line_number, "Monkey does not exist.", line)
                continue

            bec_collect_date = dingus.get_datetime_from_steve(data[0])
            if not bec_collect_date:
                print dingus.ERROR_OUTPUT % (line_number, "Wrong date format", line)
                continue

            bec = MonkeyBEC.objects.filter(monkey=monkey, bec_collect_date=bec_collect_date)
            if bec:
                if overwrite:
                    bec.delete()
                    bec = MonkeyBEC(monkey=monkey, bec_collect_date=bec_collect_date)
                else:
                    print dingus.ERROR_OUTPUT % (line_number, "Monkey+Date exists", line)
                    continue
            else:
                bec = MonkeyBEC(monkey=monkey, bec_collect_date=bec_collect_date)


            data_fields = data[FIELDS_INDEX[0]:FIELDS_INDEX[1]]
            model_fields = fields[FIELDS_INDEX[0]:FIELDS_INDEX[1]]
            for i, field in enumerate(model_fields):
                if model_fields[i].startswith('__'):
                    continue
                try:
                    value = data_fields[i]
                except IndexError:
                    if print_warning:
                        print "There was an index error, probably means this file doesn't have a bec_daily_vol_etoh column."
                        print_warning = False
                    continue
                if value != '':
                    if i == 4: # time field
                        setattr(bec, field, format_time(value))
                    else:
                        setattr(bec, field, value)
            try:
                bec.full_clean()
            except Exception as e:
                print dingus.ERROR_OUTPUT % (line_number, e, line)
                continue
            bec.save()
    print "Data load complete."
# from matrr.utils.database import load_unusual_formats
# #bec_vervet1_file = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet1_BEC.csv'
# bec_vervet2_file = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet2_BEC.csv'
# load_unusual_formats.load_bec_data_vervet(bec_vervet2_file, True, True)

###LOAD vervet1 daily 22hr etoh
def read_daily_22hr_etoh(file, cohort, parsenames=False):
    with open(file, 'r') as f:
        #1. Parse header to get monkeys
        monkeys = []
        names = []
        header = f.readline()
        header_split = header.split(',')
        for s in header_split:
            s_split = s.split(' ')
            for s2 in s_split:
                if s2.isdigit():
                    m = Monkey.objects.get(mky_real_id = s2)
                    monkeys.append(m)
                else:
                    names.append(s2)
        if parsenames:
            for i in xrange(len(monkeys)):
                m = monkeys[i]
                m.mky_name = names[i+2]
                m.save()
        #2. Parse Data
        read_data = f.readlines()
        cnt = 0
        for line_number, line in enumerate(read_data):
            #print line_number
            #print line
            cnt += 1
            print cnt
            # if cnt > 2:
            #        break
            data = line.split(',')

            #2.1 Create Drinking Experiments
            dex_date = dingus.get_datetime_from_steve(data[1])
            des = DrinkingExperiment.objects.filter(dex_type="Open Access", dex_date = dex_date,
                                                    cohort = cohort)
            if des.count() == 0:
                de = DrinkingExperiment(dex_type="Open Access", dex_date = dex_date,
                                                    cohort = cohort)
            elif des.count() == 1:
                de = des[0]
            elif des.count() > 1:
                print "too many drinking experiments!"
            #save notes if any
            notepos = len(monkeys)+2
            if len(data[notepos]) > 2:
                de.dex_notes = data[notepos]
            de.save()

            #2.2 Create MonkeyToDrinkingExperiment
            pos = 2
            for monkey in monkeys:
                mtds = MonkeyToDrinkingExperiment.objects.filter(drinking_experiment = de, monkey = monkey)
                if mtds.count() != 0:
                    mtd = mtds[0]
                else:
                    mtd = MonkeyToDrinkingExperiment()
                    mtd.monkey = monkey
                    mtd.drinking_experiment = de
                    mtd.mtd_total_pellets = 0

                #print mtd
                if data[pos]:
                    mtd.mtd_etoh_g_kg = data[pos]
                else:
                    mtd.mtd_etoh_g_kg = None
                    mtd.mtd_total_pellets = 0
                #print mtd

                mtd.save()
                pos +=1

#file_name = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet1_daily_22h_etoh.csv'
# file_name = '/home/alex/Dropbox/Baylor/Matrr/vervet_data/vervet2_daily_22h_etoh.csv'
# #cohort_vervet_1 = Cohort.objects.get(coh_cohort_name="INIA Vervet 1")
# cohort_vervet_2 = Cohort.objects.get(coh_cohort_name="INIA Vervet 2")
#
# read_daily_22hr_etoh(file_name, cohort_vervet_2, True)
