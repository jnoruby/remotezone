import json
import pickle
import requests
import datetime as dt
from datetime import datetime, timedelta
from dateutil import parser
from zoneinfo import ZoneInfo, available_timezones
from consts import *


def get_max_dst_distance_two_zones(tz1, tz2, year=datetime.now().year):
    d = get_zone_transitions_dict(year)
    zt1, zt2 = d[tz1], d[tz2]
    if len(zt1) != len(zt2):
        dst_distance = timedelta(days=365)
    else:
        dst_distance = abs(zt1[0] - zt2[0])
        for i in range(1, len(zt1)):
            if abs(zt1[i] - zt2[i]) > dst_distance:
                dst_distance = abs(zt1[i] - zt2[i])
    if zt1 == zt2:  # same timezone
        dst_distance = timedelta(seconds=0)
    return dst_distance


def get_dst_zone_transition_non_alignment_types(year=datetime.now().year):
    filename = f'tz_data/zt_nonalignment_lookup_{year}.pickle'
    _, repr_tz_d = get_representative_tz_dicts(year)

    def get_misalignment_category(dst_distance):
        if dst_distance == timedelta(seconds=0):
            misalignment_category = None
        elif timedelta(seconds=1) <= dst_distance < timedelta(seconds=12*3600):
            misalignment_category = 'hours'
        elif timedelta(seconds=12*3600) <= dst_distance < timedelta(days=7):
            misalignment_category = 'within a week'
        elif timedelta(days=7) <= dst_distance < timedelta(days=30):
            misalignment_category = 'weeks'
        else:  # dst_distance >= timedelta(days=30):
            misalignment_category = 'months'
        return misalignment_category

    try:
        with open(filename, 'rb') as f:
            zt_nonalignment_d = pickle.load(f)
    except FileNotFoundError:
        zt_nonalignment_d = {}
        dst_repr_tzs = [tz for tz in repr_tz_d.keys() 
                        if has_zone_transitions(tz)]
        for tz1 in dst_repr_tzs:
            for tz2 in dst_repr_tzs:
                dst_distance = get_max_dst_distance_two_zones(tz1, tz2)
                misalignment_category = get_misalignment_category(dst_distance)
                zt_nonalignment_d[(tz1, tz2)] = misalignment_category
        with open(filename, 'wb') as f:
            pickle.dump(zt_nonalignment_d, f)
    return zt_nonalignment_d


def lookup(zt_d, worker_tz='UTC', year=datetime.now().year, w_start_hr=17,
           w_start_min=0, w_end_hr=6, w_end_min=0, r_start_hr=9,
           r_start_min=0, r_end_hr=17, r_end_min=0):

    def to_utc(month, day, w_hr, w_min):
        return datetime(year, month, day, w_hr, w_min, 
                        tzinfo=ZoneInfo(worker_tz)).astimezone(ZoneInfo('UTC'))

    def is_southern_hemisphere(dts):
        """ Direction of DST transition """
        if dts.index(min(dts, key=lambda x: x.tzinfo.utcoffset(x))):
            return True
        else:
            return False

    failed_but_within_hours = []
    failed_but_within_a_week = []
    failed_but_within_weeks = []
    failed = []

    filename = f'tz_data/utc_based_results_dict_{year}.pickle'
    with open(filename, 'rb') as f:
        d = pickle.load(f)
    if worker_tz == 'UTC':
        lookup_str = (f'UTC+00:00 {w_start_hr} {w_start_min} {w_end_hr} '
                      f'{w_end_min}')
        remote_tzs = d[lookup_str]
    elif not has_zone_transitions(worker_tz):
        # For a time zone without DST it doesn't matter what day we use to get
        # equivalent UTC time. 
        utc_start_dt = to_utc(6, 1, w_start_hr, w_start_min)
        utc_end_dt = to_utc(6, 1, w_end_hr, w_end_min)
        lookup_str = (f'UTC+00:00 {utc_start_dt.hour} {utc_start_dt.minute}'
                      f' {utc_end_dt.hour} {utc_end_dt.minute}')
        remote_tzs = d[lookup_str]
    # DST time zone
    else:
        # Use the day AFTER zone transitions for defining UTC offset to avoid 
        # error caused by using an end hour before the transition time. NOTE:
        # current version assumes a constant weekday shift in remote zone.
        test_zts = [zt + timedelta(days=1) for zt in zt_d[worker_tz]]
        # Only check if the DST time zones are in a category of misalignment,
        # rather than returning exact days, which can just be defined in a list.
        misalignment_d = get_dst_zone_transition_non_alignment_types(year)
        all_to_repr_tz_d, _ = get_representative_tz_dicts(year)

        # For DST time zone, define search range (n + 1) compared to n for 
        # a standard time zone equivalent. Valid remote time zones include 
        # other DST time zones that are in the larger range.
        utc_start_dts = [to_utc(dt.month, dt.day, w_start_hr, w_start_min)
                         for dt in test_zts]
        utc_end_dts = [to_utc(dt.month, dt.day, w_end_hr, w_end_min)
                       for dt in test_zts]

        # Determine which transition dates are standard, DST (hemispheric)
        local_transitions = [dt.astimezone(ZoneInfo(worker_tz)) 
                             for dt in utc_start_dts]
        is_southern = is_southern_hemisphere(local_transitions)
        dst_start_dt = utc_start_dts[0] if is_southern else utc_start_dts[1]
        std_end_dt = utc_end_dts[1] if is_southern else utc_end_dts[0]
        
        lookup_str = (f'UTC+00:00 {dst_start_dt.hour} {dst_start_dt.minute}'
                      f' {std_end_dt.hour} {std_end_dt.minute}')
        whole_range = d[lookup_str]

        # Figure out a way to check only at temporal edges, reduce expense TODO
        remote_tzs = list(whole_range)
        for r_tz_tuple in whole_range:
            r_tz = r_tz_tuple[0]
            if 0 < worker_can_work_in_tz(worker_tz, r_tz, zt_d, test_zts,
                                         year=year, w_start_hr=w_start_hr, 
                                         w_start_min=w_start_min, 
                                         r_start_hr=r_start_hr,
                                         r_start_min=r_start_min,
                                         w_length=shift_length(
                                             w_start_hr, w_start_min,
                                             w_end_hr, w_end_min),
                                         r_length=shift_length(
                                             r_start_hr, r_start_min,
                                             r_end_hr, r_end_min)):
                remote_tzs.remove(r_tz_tuple)
            w_repr_tz = all_to_repr_tz_d[worker_tz]
            r_repr_tz = all_to_repr_tz_d[r_tz]
            # Get range of time where remote work fails due to misaligned DST
            try:
                misalignment_category = misalignment_d[(w_repr_tz, r_repr_tz)]
            except KeyError:
                misalignment_category = None
            if misalignment_category == 'hours':
                failed_but_within_hours.append(r_tz_tuple)
            elif misalignment_category == 'within a week':
                failed_but_within_a_week.append(r_tz_tuple)
            elif misalignment_category == 'weeks':
                failed_but_within_weeks.append(r_tz_tuple)
            elif misalignment_category == 'months':
                failed.append(r_tz_tuple)

        failed_but_within_hours = tuple(failed_but_within_hours)
        failed_but_within_a_week = tuple(failed_but_within_a_week)
        failed_but_within_weeks = tuple(failed_but_within_weeks)
        failed = tuple(failed)
        remote_tzs = tuple(remote_tzs)

        remote_tzs = tuple(tz for tz in remote_tzs if
                           tz not in failed_but_within_hours and
                           tz not in failed_but_within_a_week and
                           tz not in failed_but_within_weeks and
                           tz not in failed)

        print(lookup_str)

    return {'remote tzs': remote_tzs,
            'failed but within hours': failed_but_within_hours,
            'failed but within a week': failed_but_within_a_week,
            'failed but within weeks': failed_but_within_weeks,
            'failed': failed
            }

        
def calculate_remote_tzs(repr_tz_d, worker_tz='UTC', year=datetime.now().year,
                         w_start_hr=19, w_start_min=0, w_end_hr=7, w_end_min=0,
                         r_start_hr=9, r_start_min=0, r_end_hr=17, r_end_min=0):
    """
    Determines time zones in which a worker based in worker_tz can work remotely
    given the worker's availability and the remote shift time. These are time
    zones that are within the worker's geographic range year-round, i.e. time
    zones where both standard and daylight saving time offsets are within.
    Assumption: worker has the same availability every day.
    TODO: allow different days.

    As of 2021-06-13 version, is only called for UTC, and only for 09:00-17:00
    remote shifts. Other time zones' remote time zones are calculated from UTC
    with an hour offset for worker time zones that only have standard time, and
    with non-aligned DST time zones subtracted from geographic range edges for
    worker time zones that use DST.

    :param repr_tz_d: dictionary of representative time zones - those with the
                      same offset from UTC and aligned DST transition times if
                      any.
    :param worker_tz: time zone where the worker lives
    :param year: year for which remote time zones are being calculated
    :param w_start_hr: local clock time in hours at time worker can start
    :param w_start_min: local clock time in minutes at time worker can start
    :param w_end_hr: local clock time in hours at time worker must end
    :param w_end_min: local clock time in minutes at time worker must end
    :param r_start_hr: remote local clock time in hours at time shift starts
    :param r_start_min: remote local clock time in minutes at time shift starts
    :param r_end_hr: remote local clock time in hours at time shift ends
    :param r_end_min: remote local clock time in minutes at time shift ends
    :return: list of tuples (time zone name, standard time offset, DST offset)
    """
    remote_repr_tzs = []
    w_shift = shift_length(w_start_hr, w_start_min, w_end_hr, w_end_min)
    r_shift = shift_length(r_start_hr, r_start_min, r_end_hr, r_end_min)
    # A worker cannot work a shift that exceeds worker availability
    if w_shift < r_shift:
        return list()
    # A worker available anytime in any 24 hour period can work anywhere
    if w_shift == timedelta(days=1):
        return list(repr_tz_d)

    zone_transitions = get_zone_transitions_dict(year)
    w_zone_transitions = get_w_zone_transitions(zone_transitions, worker_tz,
                                                year)
    # Get list of time zones where both standard and any DST in worker's range
    for tz in repr_tz_d:
        failed_days = worker_can_work_in_tz(worker_tz, tz, zone_transitions,
                                            w_zone_transitions,
                                            year=datetime.now().year,
                                            w_start_hr=w_start_hr,
                                            w_start_min=w_start_min,
                                            w_length=shift_length(
                                                w_start_hr, w_start_min,
                                                w_end_hr, w_end_min),
                                            r_length=shift_length(
                                                r_start_hr, r_start_min,
                                                r_end_hr, r_end_min))
        standard_offset = get_standard_offset(tz, year)
        dst_offset = (get_standard_offset(tz, year)
                      if not has_zone_transitions(tz, year) else
                      get_standard_offset(tz, year) + timedelta(seconds=3600))
        if failed_days == 0:
            remote_repr_tzs.append((tz, standard_offset, dst_offset))
    return remote_repr_tzs


def calculate_utc_tz_sets(repr_tz_d, year=datetime.now().year):
    utc_results = {}
    for w_start_hr in range(0, 24):
        for w_start_min in TEST_MINUTE_SET:
            for w_end_hr in range(0, 24):
                for w_end_min in TEST_MINUTE_SET:
                    k = (f'UTC+00:00 {w_start_hr} {w_start_min} '
                         f'{w_end_hr} {w_end_min}')
                    utc_results[k] = tuple(calculate_remote_tzs(
                        repr_tz_d,
                        worker_tz='UTC',
                        year=year,
                        w_start_hr=w_start_hr,
                        w_start_min=w_start_min,
                        w_end_hr=w_end_hr,
                        w_end_min=w_end_min))
                    print(f'{w_start_hr} {w_start_min} {w_end_hr} {w_end_min}')
    s = set(v for v in utc_results.values())
    filename_all = f'tz_data/utc_based_results_dict_{year}.pickle'
    filename_set = f'tz_data/utc_based_results_dict_set_{year}.pickle'
    with open(filename_all, 'wb') as f:
        pickle.dump(utc_results, f)
    with open(filename_set, 'wb') as f:
        pickle.dump(s, f)
    return utc_results


def configure_starts_ends(
        w_tz, r_tz, year,
        w_start_hr, w_start_min, w_length,
        r_start_hr, r_start_min, r_length, test_dates):
    w_starts = [datetime(year, dt.month, dt.day, w_start_hr, w_start_min,
                         tzinfo=ZoneInfo(w_tz)) for dt in test_dates]
    w_ends = [s + w_length for s in w_starts]
    same_day_starts = [datetime(year, dt.month, dt.day, r_start_hr, r_start_min,
                                tzinfo=ZoneInfo(r_tz)) for dt in test_dates]
    same_day_ends = [s + r_length for s in same_day_starts]
    try:
        next_day_starts = [datetime(year, dt.month, dt.day + 1,
                                    r_start_hr, r_start_min,
                                    tzinfo=ZoneInfo(r_tz)) for dt in test_dates]
    # Or next day if month, day is invalid will be 1st day of next month
    except ValueError:
        next_day_starts = [datetime(year, dt.month + 1, 1,
                                    r_start_hr, r_start_min,
                                    tzinfo=ZoneInfo(r_tz)) for dt in test_dates]
    next_day_ends = [s + r_length for s in next_day_starts]
    return (w_starts, w_ends,
            same_day_starts, same_day_ends,
            next_day_starts, next_day_ends)


def create_remote_tz_sets(repr_tz_d, year=datetime.now().year):

    filename = f'tz_data/utc_based_results_dict_{year}.pickle'
    filename_set = f'tz_data/utc_based_results_dict_set_{year}.pickle'
    try:
        with open(filename, 'rb') as f:
            utc_dict = pickle.load(f)
        with open(filename_set, 'rb') as f_set:
            utc_set = pickle.load(f_set)
    except FileNotFoundError:
        utc_dict = calculate_utc_tz_sets(repr_tz_d, year)
    unique_remote_tzs_to_utc_time_values = {}
    for item in list(utc_set):
        temp = []
        for k, v in utc_dict.items():
            if v == item:
                temp.append(k)
        unique_remote_tzs_to_utc_time_values[item] = temp
    return unique_remote_tzs_to_utc_time_values


def get_all_tzs_matching_repr_tzs(repr_tzs, all_to_repr_tz_d):
    all_tzs = available_timezones()
    tzs = []
    for tz in all_tzs:
        if all_to_repr_tz_d[tz] in repr_tzs:
            tzs.append(tz)
    return tzs


def get_hourly_datetimes(tz='UTC', year=datetime.now().year):
    dts = [datetime(year, 1, 1, 0, tzinfo=ZoneInfo(tz))]
    curr_dt = dts[0]
    while curr_dt < datetime(year + 1, 1, 1, 0, tzinfo=ZoneInfo(tz)):
        next_dt = curr_dt + timedelta(seconds=3600)
        dts.append(next_dt)
        curr_dt = next_dt
    return dts


def get_representative_tz_dicts(year=datetime.now().year):
    """
    Once representative time zones are determined per year per tz database
    update, there is no need to redetermine them. So first check to see if
    this has already been done (result kept in a pickle, as JSON can't serialize
    datetimes, then if not, run rest of function.
    :param year:
    :return:
    """
    repr_tzs_updated_path = f'tz_data/repr_tzs_updated_{year}.pickle'
    try:
        with open(repr_tzs_updated_path, 'rb') as infile:
            old_update = pickle.load(infile)
            if old_update + timedelta(days=7) > datetime.now():
                repr_path = f'tz_data/repr_tz_d_{year}.pickle'
                all_to_repr_path = f'tz_data/all_to_repr_tz_d_{year}.pickle'
                with open(repr_path, 'rb') as infile1:
                    repr_tz_d = pickle.load(infile1)
                with open(all_to_repr_path, 'rb') as infile2:
                    all_to_repr_tz_d = pickle.load(infile2)
                return all_to_repr_tz_d, repr_tz_d

    except FileNotFoundError:
        # Consider remote tz-boundary-builder data newer if no update file.
        print(f'ERROR: file containing latest determination of representative '
              f'time zones for {year} not found. Creating...')
        with open(repr_tzs_updated_path, 'wb') as outfile:
            pickle.dump(datetime.now(), outfile)

    all_tzs = available_timezones()
    zone_transition_dict = get_zone_transitions_dict(year)
    tz_characteristics_dict = {}
    all_to_repr_tz_d = {}

    for tz in all_tzs:
        try:
            zone_transitions = zone_transition_dict[tz]
        except KeyError:
            zone_transitions = []
        standard_offset = get_standard_offset(tz, year)
        tz_characteristics_dict[tz] = (standard_offset, tuple(zone_transitions))

    unique_values_dict = {}
    for key, value in tz_characteristics_dict.items():
        if value not in unique_values_dict.values():
            unique_values_dict[key] = value
    inverted_unique_values_dict = {v: k for k, v in unique_values_dict.items()}
    for key, value in tz_characteristics_dict.items():
        all_to_repr_tz_d[key] = inverted_unique_values_dict[value]

    repr_tz_d = {k: v for (k, v) in tz_characteristics_dict.items() if k in
                 all_to_repr_tz_d.values()}

    repr_tz_d_path = f'tz_data/repr_tz_d_{year}.pickle'
    all_to_repr_tz_d_path = f'tz_data/all_to_repr_tz_d_{year}.pickle'
    with open(repr_tz_d_path, 'wb') as outfile:
        pickle.dump(repr_tz_d, outfile)
    with open(all_to_repr_tz_d_path, 'wb') as outfile:
        pickle.dump(all_to_repr_tz_d, outfile)

    return all_to_repr_tz_d, repr_tz_d


def get_standard_offset(tz='UTC', year=datetime.now().year):
    has_zt = has_zone_transitions(tz, year)
    if not has_zt:
        default_dt = datetime(year, 1, 1, 0, tzinfo=ZoneInfo(tz))
        standard_offset = default_dt.tzinfo.utcoffset(default_dt)
    else:
        dt_dec = datetime(year, 12, 20, 0, tzinfo=ZoneInfo(tz))
        dt_jun = datetime(year, 6, 20, 0, tzinfo=ZoneInfo(tz))
        standard_offset = min(dt_dec.tzinfo.utcoffset(dt_dec),
                              dt_jun.tzinfo.utcoffset(dt_jun))
    return standard_offset


def get_test_dates(w_tz, r_tz, year,
                   zone_transitions, w_zone_transitions):
    # Add default day to remove the no_dst function
    test_dates = [datetime(year, 6, 20, 9, tzinfo=ZoneInfo(w_tz))]
    if has_zone_transitions(w_tz):
        if w_zone_transitions is not None:
            for dt in w_zone_transitions:
                test_dates.append(dt)
                test_dates.append(dt + timedelta(days=-1))
                test_dates.append(dt + timedelta(days=1))
    if has_zone_transitions(r_tz, year=year):
        r_tz_dst_shifts = zone_transitions[r_tz]
        for dt in r_tz_dst_shifts:
            test_dates.append(dt)
            test_dates.append(dt + timedelta(days=-1))
            test_dates.append(dt + timedelta(days=1))
    unique_dates = []
    for d in test_dates:
        unique_dates.append((d.month, d.day))
    unique_dates = sorted(list(set(unique_dates)))

    test_dates = [datetime(year, d[0], d[1]) for d in unique_dates]

    return test_dates


def get_w_zone_transitions(zone_transitions,
                           tz='UTC', year=datetime.now().year):
    if has_zone_transitions(tz=tz, year=year):
        w_zone_transitions = zone_transitions[tz]
    else:
        w_zone_transitions = None
    return w_zone_transitions


def get_zone_transitions_from_datetime_list(dts):
    zone_transitions = []
    current_offset = dts[0].tzinfo.utcoffset(dts[0])
    for d in dts:
        if d.tzinfo.utcoffset(d) != current_offset:
            zone_transitions.append(d)
            current_offset = d.tzinfo.utcoffset(d)
    return zone_transitions


def get_zone_transitions_dict(year=datetime.now().year):
    """ Retrieves time zone transition dates (currently from file) for a
        particular calendar year. Uses write_zone_transitions(year) to write
        dictionary to file if it does not already exist.

        :param year: The calendar year to look up, defaults to
            datetime.now().year attribute
        :type year: int
        :return: A dictionary per year with all time zones (IANA tz database)
            key = time zone name, value = list of datetimes on which occurred
            (or are predicted to occur) zone transitions
        :rtype: dict
    """
    filename = f'tz_data/zone_transitions_{year}.pickle'
    try:
        with open(filename, 'rb') as fd:
            zone_transitions = pickle.load(fd)
    except FileNotFoundError:
        write_zone_transitions(filename, year)
        with open(filename, 'rb') as fd:
            zone_transitions = pickle.load(fd)
    return zone_transitions


def get_year(args):
    prompt = 'Calculate all remote time zone sets for which calendar year? '
    year_str = args[1] if len(args) < 1 else input(prompt)

    def year_error(bad_year):
        print(f'Entered string \'{bad_year}\' cannot be interpreted as a '
              f'calendar year that can be used for time zone calculations.'
              f'\nCalculating for the current year instead. Usage: '
              f'{MIN_TZ_YEAR} <= year <= {MAX_TZ_YEAR}')

        return datetime.now().year

    try:
        year = int(year_str)
        _dt = datetime(year + 1, 1, 1)  # Prohibit datetime maximum year
    except ValueError:
        year = year_error(year_str)

    if year < 1970:
        year = year_error(year_str)

    return year


def has_tbb_updated():
    """ Check if Evan Siroky's timezone-boundary-builder has updated. This is
    used to determine when maps need to be redrawn.
    :rtype: bool
    """
    tbb_data_path = 'tz_data/tbb_json_download.json'
    tbb_url = ('https://api.github.com/repos/evansiroky/' +
               'timezone-boundary-builder/releases/latest')
    try:
        with open(tbb_data_path, 'r') as infile:
            old_update_str = json.load(infile)['published_at']
            old_update = parser.parse(old_update_str)
            print(f'Latest downloaded update of timezone-boundary-builder is '
                  f'from {old_update_str}.')
    except FileNotFoundError:
        # Consider remote tz-boundary-builder data newer if no update file.
        print('ERROR: file containing local data on timezone-boundary'
              '-builder update not found. New request to Github being made.')
        old_update = datetime(dt.MINYEAR, 1, 1, tzinfo=ZoneInfo('UTC'))
    try:
        github_response = requests.get(tbb_url)
        json_object = github_response.json()
    except requests.exceptions.RequestException as e:
        print(f'{e}. Error requesting data on timezone-boundary-builder from '
              f'Github.')
        json_object = dict()

    # In case remote dictionary keys have changed. TODO add logging
    try:
        new_update_str = json_object['published_at']
        new_update = parser.parse(new_update_str)
        print(f'Newest update of timezone-boundary-builder is from '
              f'{new_update_str}')
    except KeyError:
        new_update = old_update

    # Write JSON object to file, to be used to get URLS of shapefile assets.
    if new_update > old_update:
        with open(tbb_data_path, 'w') as outfile:
            json.dump(json_object, outfile)
        print('Writing new data on timezone-boundary-builder.')
        return True
    else:
        print('Old data from timezone-boundary-builder is sufficient.')
        return False


def has_tz_updated():
    """
    Not ready yet. Wait until deployment to server, as will be able to fetch
    updates to tz database when available and run relevant functions once server
    OS update is complete. These functions include re-selecting representative
    time zones, re-calculating correct remote zones, and re-drawing maps.
    """
    # TODO when deployed to server
    # For right now manually True while creating first data, then set to False
    # until update workflow is ready.
    return True


def has_zone_transitions(tz='UTC', year=datetime.now().year):
    """ Have not found a datetime equivalent for time.timezone() and
        time.altzone(), which would allow a simple check whether a time zone
        currently has DST.

        The approach here is to instead use persistent storage (r.n. pickle)
        which contains offset shifts for each timezone for each year.
        This in turn needs to be updated only when there is an IANA database
        update).

        As of 2021, all time zones using daylight saving time have different
        offsets on the December solstice and the June solstice. But this is not
        guaranteed for past years or future ones. Fiji's 2020/2021 DST started
        on 20 December 2020, and it can exit under current law as early as
        a 12 January. So this, along with unpredicted use for past years,
        means that the more complex approach is necessary.

        :param tz: Time zone name from tz https://www.iana.org/time-zones,
            defaults to 'UTC'.
        :type tz: str
        :param year: The calendar year to look up, defaults to
            datetime.now().year attribute
        :type year: int
        :return: Whether a time zone has zone transitions in that year's dict
        :rtype: bool
    """
    # TODO allow argument to be an arbitrary datetime span, not just a
    # calendar year.

    # Do not create datetimes where "today" and "tomorrow" are out of range.
    try:
        _dt = datetime(year, 1, 1)
        _dt = datetime(year + 1, 1, 1)
    except (ValueError, TypeError):
        raise

    zone_transition_dict = get_zone_transitions_dict(year)
    try:
        zone_transitions = zone_transition_dict[tz]
        return len(zone_transitions) > 0
    except KeyError:
        raise


def write_zone_transitions(filename, year=datetime.now().year):
    tzs = available_timezones()
    zone_transitions_dict = {}

    # For each time zone, create for the calendar year all hourly datetimes.
    # Iterate through the list of datetimes, adding ones to a zone transition
    #   list when the UTC offset differs from that of the previous hour.
    # Add these lists to dictionary and write to file.
    # NOTE: Archaic zone transitions did not necessarily occur on the hour.
    # TODO: Account for the above, low priority as not generally used for past.

    for tz in tzs:
        dts = get_hourly_datetimes(tz, year)
        zone_transitions = get_zone_transitions_from_datetime_list(dts)
        zone_transitions_dict[tz] = zone_transitions
        """
        # Would be faster to use some already determined transition object
        # but pytz data not compatible with zoneinfo data
        dts = get_zone_transitions_pytz(tz=tz, year=year)
        zone_transitions = get_zone_transitions_from_datetime_list(dts)
        zone_transitions_dict[tz] = zone_transitions
        """

    with open(filename, 'wb') as fd:
        pickle.dump(zone_transitions_dict, fd)


def remote_day_within_worker_day(w_bounds):
    (w_starts, w_ends,
     same_day_starts, same_day_ends,
     next_day_starts, next_day_ends) = w_bounds
    can_start_same = can_end_same = can_start_next = can_end_next = True
    # If for any day pair of the year, worker's start is after shift
    # starts, worker cannot work that shift.
    cannot_start_same_days = []
    cannot_end_same_days = []
    cannot_start_next_days = []
    cannot_end_next_days = []
    for index, start in enumerate(w_starts):
        if start > same_day_starts[index]:
            can_start_same = False
            cannot_start_same_days.append(start)
        if start > next_day_starts[index]:
            can_start_next = False
            cannot_start_next_days.append(start)
    # If for any day pair of the year, worker's end is before shift
    # ends, worker cannot work that shift.
    for index, end in enumerate(w_ends):
        if end < same_day_ends[index]:
            can_end_same = False
            cannot_end_same_days.append(end)
        if end < next_day_ends[index]:
            can_end_next = False
            cannot_end_next_days.append(end)
    cannot_same = len(cannot_start_same_days) + len(cannot_end_same_days)
    cannot_next = len(cannot_start_next_days) + len(cannot_end_next_days)

    if (can_start_same and can_end_same) or (can_start_next and can_end_next):
        failed_days = []
    else:
        if cannot_same <= cannot_next:
            failed_days = cannot_start_same_days
            for d in cannot_end_same_days:
                failed_days.append(d)
        else:
            failed_days = cannot_start_next_days
            for d in cannot_end_next_days:
                failed_days.append(d)
    return (failed_days, cannot_start_same_days, cannot_end_same_days,
            cannot_start_next_days, cannot_end_next_days)


def shift_length(s_hr, s_min, e_hr, e_min):
    s = timedelta(seconds=((3600 * (e_hr - s_hr)) + (60 * (e_min - s_min))))
    return s if s > timedelta(seconds=0) else s + timedelta(days=1)


def worker_can_work_in_tz(w_tz, r_tz, zone_transitions,
                          w_zone_transitions, year=datetime.now().year,
                          w_start_hr=17, w_start_min=0,
                          w_length=timedelta(seconds=8 * 3600),
                          r_start_hr=9, r_start_min=0,
                          r_length=timedelta(seconds=8 * 3600)):

    # Determine test dates throughout the year, wrt DST shift dates.
    test_dates = get_test_dates(w_tz, r_tz, year, zone_transitions,
                                w_zone_transitions)
    # Beginning and end of worker availability, aligned with shifts on
    # the "same day" or the "next day" on sides of IDL.
    w_bounds = configure_starts_ends(w_tz, r_tz, year,
                                     w_start_hr, w_start_min, w_length,
                                     r_start_hr, r_start_min, r_length,
                                     test_dates)
    (failed_days, cannot_start_same_days, cannot_end_same_days,
     cannot_start_next_days,
     cannot_end_next_days) = remote_day_within_worker_day(w_bounds)

    return len(failed_days)
