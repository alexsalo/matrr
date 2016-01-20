__author__ = 'alex'
from common import *

# within each monkey's data
def _split_bec_df_into_three(bec_df, split_by):
    if split_by == 'bec_mgpct':
        bec_df_less80mgpct = bec_df[bec_df.bec < 80]
        bec_df_over80mgpct = bec_df[bec_df.bec >= 80]
        return bec_df, bec_df_less80mgpct, bec_df_over80mgpct

    if split_by == 'bec_over2stdev':  # within vs outside
        mean_bec = np.mean(bec_df.bec)
        std_bec = np.std(bec_df.bec)
        y_lo = mean_bec - 2*std_bec
        y_hi = mean_bec + 2*std_bec
        bec_df_within2std = bec_df[(bec_df.bec > y_lo) & (bec_df.bec < y_hi)]
        bec_df_over2std = bec_df[(bec_df.bec < y_lo) | (bec_df.bec > y_hi)]
        return bec_df, bec_df_within2std, bec_df_over2std

    if split_by == 'bec_more2stdev':
        mean_bec = np.mean(bec_df.bec)
        std_bec = np.std(bec_df.bec)
        y_hi = mean_bec + 2*std_bec
        bec_df_normal = bec_df[bec_df.bec <= y_hi]
        bec_df_condition = bec_df[bec_df.bec > y_hi]
        return bec_df, bec_df_normal, bec_df_condition

    if split_by == 'bec_less2stdev':
        mean_bec = np.mean(bec_df.bec)
        std_bec = np.std(bec_df.bec)
        y_lo = mean_bec - 2*std_bec
        bec_df_normal = bec_df[bec_df.bec >= y_lo]
        bec_df_condition = bec_df[bec_df.bec < y_lo]
        return bec_df, bec_df_normal, bec_df_condition

# Using daylight etoh consumption rather than 22hr access
def mky_bec_corr_daylight(mky, split_by='bec_mgpct'):
    # 1. Find becs and create dataframe
    becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
    bec_df = pd.DataFrame(columns=['etoh_previos_day', 'etoh_at_bec_sample_time', 'etoh_next_day', 'bec', 'dc'])

    # 2. Collect values
    for bec in becs:
        today = bec.bec_collect_date
        yeday = today + timedelta(days=-1)
        tomor = today + timedelta(days=1)

        # If we have values for prev, to and next days - append to df_bec
        try:
            etoh_prev, etoh_at, etoh_next = mky.DL_total_etoh(yeday), mky.DL_total_etoh(today), mky.DL_total_etoh(tomor)
            bec_df.loc[len(bec_df)] = [etoh_prev, etoh_at, etoh_next, bec.bec_mg_pct, mky.mky_drinking_category]
        except:
            continue
    return _split_bec_df_into_three(bec_df, split_by)
def mky_bec_corr_22hr(mky, split_by='bec_mgpct'):
    # 1. Filter work data set
    becs = MonkeyBEC.objects.OA().filter(monkey=mky).order_by('bec_collect_date')
    mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=mky).exclude(mtd_etoh_g_kg__isnull=True)

    # 2. Get bec dates and corresponding day before and day after dates lists
    bec_dates = becs.values_list('bec_collect_date', flat=True)
    bec_dates_prev = [date + timedelta(days=-1) for date in bec_dates]
    bec_dates_next = [date + timedelta(days=+1) for date in bec_dates]

    # 3. Get corresponding mtds
    mtds_prev = mtds.filter(drinking_experiment__dex_date__in=bec_dates_prev)
    mtds_next = mtds.filter(drinking_experiment__dex_date__in=bec_dates_next)

    # 4. Find intersection: we need data for prev day, bec day and next day
    mtds_prev_dates = [date + timedelta(days=+1) for date in mtds_prev.values_list('drinking_experiment__dex_date', flat=True)]
    mtds_next_dates = [date + timedelta(days=-1) for date in mtds_next.values_list('drinking_experiment__dex_date', flat=True)]
    mtds_intersection_dates = set(mtds_prev_dates).intersection(mtds_next_dates)

    # 5. Retain becs and mtds within days of intersection
    becs_retained = becs.filter(bec_collect_date__in=mtds_intersection_dates).order_by('bec_collect_date')
    mtds_prev_retained = mtds_prev.filter(drinking_experiment__dex_date__in=[date + timedelta(days=-1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')
    mtds_next_retained = mtds_next.filter(drinking_experiment__dex_date__in=[date + timedelta(days=+1) for date in mtds_intersection_dates]).order_by('drinking_experiment__dex_date')

    # 6. Assert we have the same number of data daysa
    print 'becs retained: %s' % becs_retained.count()
    print 'etoh on prev day retained: %s' % mtds_prev_retained.count()
    print 'etoh on next day retained: %s' % mtds_next_retained.count()
    assert becs_retained.count() == mtds_prev_retained.count() == mtds_next_retained.count()

    # 7. Compile data frame
    if mtds_prev_retained.count() == 0:
        return pd.DataFrame() # empty to be ignored

    bec_df = pd.DataFrame(list(mtds_prev_retained.values_list('mtd_etoh_g_kg')), columns=['etoh_previos_day'])
    bec_df['etoh_at_bec_sample_time'] = list(becs_retained.values_list('bec_gkg_etoh', flat=True))
    bec_df['etoh_next_day'] = list(mtds_next_retained.values_list('mtd_etoh_g_kg', flat=True))
    bec_df['bec'] = list(becs_retained.values_list('bec_mg_pct', flat=True))
    bec_df['dc'] = list(mtds_next_retained.values_list('monkey__mky_drinking_category', flat=True))

    return _split_bec_df_into_three(bec_df, split_by)


def collect_monkeys_bec(schedule, split_by, cohort='ALL'):
    if schedule == '22hr':
        collect_method = mky_bec_corr_22hr
    elif schedule == 'daylight':
        collect_method = mky_bec_corr_daylight
    else:
        raise Exception('You must specify schedule: 22hr or daylight')

    if cohort == 'ALL':
        monkeys = Monkey.objects.filter(mky_id__in=MonkeyBEC.objects.all().
                                        values_list('monkey__mky_id', flat=True).distinct())
    else:
        monkeys = Monkey.objects.filter(mky_id__in=MonkeyBEC.objects.all().
                                        values_list('monkey__mky_id', flat=True).distinct())
        monkeys = Monkey.objects.filter(mky_id__in=cohort.monkey_set.filter(mky_id__in=monkeys))

    bec_df_all, bec_df_group_1, bec_df_group_2 = collect_method(monkeys[0], split_by)
    for mky in monkeys[1:]:
        print mky
        try:
            new_df, new_df_group_1, new_df_group_2 = collect_method(mky, split_by)
            bec_df_all = bec_df_all.append(new_df)
            bec_df_group_1 = bec_df_group_1.append(new_df_group_1)
            bec_df_group_2 = bec_df_group_2.append(new_df_group_2)
        except Exception as e:
            print e
            continue

    print "Total BECs: %s" % len(bec_df_all)
    return bec_df_all, bec_df_group_1, bec_df_group_2


def get_bec_df_for_all_animals(schedule, split_by='bec_mgpct', regenerate=False):
    def generate():
        bec_df_all, bec_df_group_1, bec_df_group_2 = collect_monkeys_bec(schedule, split_by, cohort='ALL')
        bec_df_all.save('bec_df_all_' + schedule + '_' + split_by + '.plk')
        bec_df_group_1.save('bec_df_group_1_' + schedule + '_' + split_by + '.plk')
        bec_df_group_2.save('bec_df_group_2_' + schedule + '_' + split_by + '.plk')

    def read():
        bec_df_all = pd.read_pickle('bec_df_all_' + schedule + '_' + split_by + '.plk')
        bec_df_group_1 = pd.read_pickle('bec_df_group_1_' + schedule + '_' + split_by + '.plk')
        bec_df_group_2 = pd.read_pickle('bec_df_group_2_' + schedule + '_' + split_by + '.plk')
        return bec_df_all, bec_df_group_1, bec_df_group_2

    if regenerate:
        generate()
    else:
        try:
            return read()
        except IOError as e:
            print 'Generating some files...'
            generate()
            return read()
