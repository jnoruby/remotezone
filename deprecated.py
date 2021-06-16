# Wrote this for building DST time zones in 2020-06 routine but wound up 
# just directly using worker_can_work_in_tz
"""
def configure_starts_ends2(w_tz, r_tz, 
        test_dates, year=datetime.now().year, w_start_hr=17, w_start_min=0,
        w_end_hr=6, w_end_min=0, r_start_hr=9, r_start_min=0, r_end_hr=17, 
        r_end_min=0):
    w_starts = [datetime(year, dt.month, dt.day, w_start_hr, w_start_min,
        tzinfo=ZoneInfo(w_tz)) for dt in test_dates]
    w_ends = [datetime(year, dt.month, dt.day, w_end_hr, w_end_min,
        tzinfo=ZoneInfo(w_tz)) for dt in test_dates]

    same_day_starts = [datetime(year, dt.month, dt.day, r_start_hr, r_start_min,
        tzinfo=ZoneInfo(r_tz)) for dt in test_dates]
    same_day_ends = [datetime(year, dt.month, dt.day, r_end_hr, r_end_min,
        tzinfo=ZoneInfo(r_tz)) for dt in test_dates]
    
    next_day_starts = [dt + timedelta(days=1) for dt in same_day_starts]
    next_day_ends = [dt + timedelta(days=1) for dt in same_day_ends]
    
    return (w_starts, w_ends, same_day_starts, same_day_ends, 
            next_day_starts, next_day_ends)

"""

# Don't need this because of .astimezone()
"""
)
    def correct_hours(hrs):
        if hrs > 23:
            hrs = hrs - 24
        elif hrs < 0:
            hrs = hrs + 24
        return hrs

    def correct_minutes(mins):
        if mins > 59:
            mins = mins - 60
            changed = -1
        elif mins < 0:
            mins = mins + 60
            changed = 1
        else:
            changed = 0
        print(f'mins changed? {changed}')
        return mins, changed


    def adjust_hours_minutes_by_offset(w_hr, w_min, all_minutes,
                                       hours, minutes_off_hour):
        offset_hr = int(w_hr) - hours
        print(hours)
        print(f'Marquesas offset hour {offset_hr}')
        offset_min = int(w_min) - minutes_off_hour
        offset_min, changed = correct_minutes(offset_min)
        offset_hr = correct_hours(offset_hr)
        # Adjust for rollover minutes into hours
        if changed > 0:
            offset_hr = offset_hr - 1
        print(offset_hr)
        print(offset_min)
        return offset_hr, offset_min

    filename = f'tz_data/utc_based_results_dict_{year}.pickle'
    with open(filename, 'rb') as f:
        d = pickle.load(f)
    if worker_tz == 'UTC':
        lookup_str = (f'UTC+00:00 {w_start_hr} {w_start_min} {w_end_hr} '
                      f'{w_end_min}')
    else:
        std_offset = get_standard_offset(worker_tz, year)
        all_minutes = int((std_offset.days * 24 * 60) + (std_offset.seconds / 60))
        hours = all_minutes // 60
        minutes_off_hour = all_minutes % 60
        offset_start_hr, offset_start_min = (
            adjust_hours_minutes_by_offset(w_start_hr, w_start_min,
                                           all_minutes, hours,
                                           minutes_off_hour))
        offset_end_hr, offset_end_min = (
            adjust_hours_minutes_by_offset(w_end_hr, w_end_min,
                                           all_minutes, hours,
                                           minutes_off_hour))
"""
