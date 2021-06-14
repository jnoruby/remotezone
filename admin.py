import json
import pickle
import requests
import datetime as dt
from datetime import datetime, timedelta
from dateutil import parser
from zoneinfo import ZoneInfo, available_timezones
from consts import *

import pprint


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
        # TODO calculate the other parts of the tuple when set of unique
        # TODO remote zone lists is created, along with dictionary where key
        # TODO is the remote zone list and value is list of worker zones and
        # TODO times. That will also be ranges when accessing data from client
        # TODO information
        standard_offset = get_standard_offset(tz, year)
        dst_offset = (get_standard_offset(tz, year)
                      if not has_zone_transitions(tz, year) else
                      get_standard_offset(tz, year) + timedelta(seconds=3600))
        if failed_days == 0:
            remote_repr_tzs.append((tz, standard_offset, dst_offset))
    return remote_repr_tzs


def calculate_utc_tz_sets(repr_tz_d, year=datetime.now().year):
    # TODO just do UTC first, then apply with shift to all non-DST TZs.
    # Same model and then shift for other smaller groups like Europe and Chile.
    # TODO then make the process for non-DST to all much faster by
    # just using subtraction to get a range, then check (always in)
    # TODO then make the process for DST to all much faster by
    # just using subtraction to get a (smaller DST-aware range),
    # then (depending on day miss tolerances) subtract uncoordinated zone
    # transition matches from the edge.
    # TODO these will be matches for equivalent non-9 to 5 shifts also
    utc_results = {}
    for w_start_hr in range(0, 24):
        for w_start_min in [0, 1, 15, 16, 30, 31, 45, 46]:
            for w_end_hr in range(0, 24):
                for w_end_min in [0, 1, 15, 30, 31, 45, 46]:
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
                    print(f'UTC worker'
                          f'starting at {w_start_hr}:{w_start_min}',
                          f'working until {w_end_hr}:{w_end_min}'
                          f'can work in {utc_results[k]}')
    s = set(v for v in utc_results.values())
    filename_all = f'tz_data/utc_based_results_dict_{year}.pickle'
    filename_set = f'tz_data/utc_based_results_dict_set_{year}.pickle'
    with open(filename_all, 'wb') as f:
        pickle.dump(utc_results, f)
    with open(filename_set, 'wb') as f:
        pickle.dump(s, f)
    return utc_results


def calculate_simple_shift_from_utc(repr_tz_d, utc_set, utc_dict,
                                    unique_set_utc,
                                    year=datetime.now().year):
    """
    # TODO this open will be contingent on file existing, not an update
    # TODO in this run:
    # filename = f' tz_data/utc_based_results_dict_{year}.pickle'
    # with open(filename, 'r') as f:
    #    utc_results = pickle.load(f)
    standard_time_results = {}
    for k1, v1 in repr_tz_d.items():
        # First step calculates from UTC for standard time only. But for DST
        # worker time zones can just test edges with function on DST time shift
        # equality. Can be old complex one or new one using transition dates
        # and returning bad periods.
        minutes = int(v1[0].days * 24 * 60 + v1[0].seconds / 60)
        hours = minutes // 60
        minutes_off_hour = minutes % 60
        new_utcoffset_str = f'UTC{str(hours).zfill(2)}:' \
                            f'{str(minutes_off_hour).zfill(2)}'
    """
    def correct_into_24(hrs):
        if hrs > 23:
            return hrs - 24
        elif hrs < 0:
            return hrs + 24
        else:
            return hrs

    def adjust_hours_minutes_by_offset(utc_hr, utc_min, all_minutes,
                                       hours, minutes_off_hour):
        if all_minutes > 0:
            offset_hr = int(utc_hr) + hours
            offset_min = int(utc_min) + minutes_off_hour
        else:
            offset_hr = int(utc_hr) - hours
            offset_min = int(utc_min) - minutes_off_hour
        offset_hr = correct_into_24(offset_hr)
        return offset_hr, offset_min
<<<<<<< HEAD

    standard_time_results = {}

=======

    standard_time_results = {}

>>>>>>> ecd648a (dictionary for all standard time offsets copied from utc 09:00-17:00)
    for k, v in unique_set_utc.items():
        new_vals = [val for val in v]
        for subval in v:
            for k2, v2, in repr_tz_d.items():
                (_, utc_start_hr, utc_start_min, utc_end_hr,
                utc_end_min) = subval.split(' ')
                all_minutes = int(v2[0].days * 24 * 60 + v2[0].seconds / 60)
                hours = all_minutes // 60
                minutes_off_hour = all_minutes % 60
                new_utcoffset_str = (f'UTC{str(hours).zfill(2)}:'
                                     f'{str(minutes_off_hour).zfill(2)}')
                offset_start_hr, offset_start_min = (
                    adjust_hours_minutes_by_offset(utc_start_hr, utc_start_min,
                                                   all_minutes, hours,
                                                   minutes_off_hour))
                offset_end_hr, offset_end_min = (
                    adjust_hours_minutes_by_offset(utc_end_hr, utc_end_min,
                                                   all_minutes, hours,
                                                   minutes_off_hour))
                offset_val = (f'{new_utcoffset_str} {k2} '
                              f'{offset_start_hr} {offset_start_min} '
                              f'{offset_end_hr} {offset_end_min}')
                new_vals.append(offset_val)
        standard_time_results[k] = new_vals

    """
    for k, v in utc_results.items():

            (_, w_start_hr, w_start_min, w_end_hr, w_end_min) = k.split(' ')
            if minutes > 0:
                new_w_start_hr = int(w_start_hr) + hours
                new_w_start_min = int(w_start_min) + minutes_off_hour
            else:
                new_w_start_hr = int(w_start_hr) - hours
                new_w_start_min = int(w_start_min) - minutes_off_hour
            new_w_start_hr = correct_into_24(new_w_start_hr)
            if minutes > 0:
                new_w_end_hr = int(w_end_hr) + hours
                new_w_end_min = int(w_end_min) + minutes_off_hour
            else:
                new_w_end_hr = int(w_end_hr) - hours
                new_w_end_min = int(w_end_min) - minutes_off_hour
            new_w_end_hr = correct_into_24(new_w_end_hr)
            new_key = (f'{new_utcoffset_str} {k1}'
                       f' {new_w_start_hr} {new_w_start_min} {new_w_end_hr} '
                       f'{new_w_end_min}')
            standard_time_results[new_key] = v
            # print(standard_time_results[new_key])
    # TODO as this is too slow the set of uniques must be done first.
    d1, d2 = subtract_edge_dst_tzs(repr_tz_d, standard_time_results, year=year)
    standard_time_results = d1
    non_overlapping_dst = d2
    """
    filename = f'tz_data/standard_time_results_{year}.pickle'

    with open(filename, 'wb') as f:
        pickle.dump(standard_time_results, f)

    return standard_time_results


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

<<<<<<< HEAD
=======




>>>>>>> ecd648a (dictionary for all standard time offsets copied from utc 09:00-17:00)
    # TODO fix the above function to load pickle if exists
    # TODO load pickle and create reverse set with key being timezone sets
    # and value being a tuple of all of the UTC combos calculated
    # n n n n (worker times) 9 0 17 0 (remote times)
    # TODO change simple_shift function to add to those tuples
    # TODO do the same to move remote shift times around the clock
    # data are enough
    # Then remove from these tuples for each non-DST time zones,
    # successively, those which create no match for 2 hours a year
    # those which create no match for a few days a year
    # those which create no match for a few weeks a year
    filename = f'tz_data/utc_based_results_dict_{year}.pickle'
    filename_set = f'tz_data/utc_based_results_dict_set_{year}.pickle'
    try:
        with open(filename, 'rb') as f:
            utc_dict = pickle.load(f)
        with open(filename_set, 'rb') as f_set:
            utc_set = pickle.load(f_set)
    except FileNotFoundError:
        utc_dict = calculate_utc_tz_sets(repr_tz_d, year)
<<<<<<< HEAD
    # Make dictionary reverse - all possible remote tz sets in UTC, with
    # values being the start and stop times that create those sets for
    # remote work time 09:00-17:00
=======
>>>>>>> ecd648a (dictionary for all standard time offsets copied from utc 09:00-17:00)
    unique_remote_tzs_to_utc_time_values = {}
    for l in list(utc_set):
        temp = []
        for k, v in utc_dict.items():
            if v == l:
                temp.append(k)
        unique_remote_tzs_to_utc_time_values[l] = temp
    print(unique_remote_tzs_to_utc_time_values)
<<<<<<< HEAD
    # Add to the reverse dictionary every start and stop time from all
    # representative worker time zones, not yet adjusted for DST transition
    # non-overlap
=======

>>>>>>> ecd648a (dictionary for all standard time offsets copied from utc 09:00-17:00)
    repr_tzs_r_tz_set_nodst = (
        calculate_simple_shift_from_utc(repr_tz_d, utc_set, utc_dict,
                                        unique_remote_tzs_to_utc_time_values))

<<<<<<< HEAD
    r_tzs, r_tzs_fail_dst_hours, r_tzs_fail_days, r_tzs_fail_weeks = (
        remove_edge_uncoordinated_transition_dst_tzs(
            repr_tzs_r_tz_set_nodst)
        )
    )

    # todo make a dictionary lookup function that takes these written
    # todo dictionaries and looks up based on variables. test all
    # representative time zones, times
    # todo, then redo dictionaries to include all times offset over from
    # 09:00 - 17:00 - that will be on the calculate_simple_shift step
    # todo then redo dst removal
    return repr_tzs_r_tz_set_nodst


def remove_edge_uncoordinated_transition_dst_tzs(repr_tzs_r_tz_set_nodst):
    r_tzs = {}
    r_tz_fail_dst_hours = {}
    r_tzs_fail_days = {}
    r_tzs_fail_weeks = {}
    return r_tzs, r_tzs_fail_dst_hours, r_tzs_fail_days, r_tzs_fail_weeks
=======
    # year)

    return repr_tzs_r_tz_set_nodst
>>>>>>> ecd648a (dictionary for all standard time offsets copied from utc 09:00-17:00)


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
            print(f'Latest determination of representative time zones in {year}'
                  f' is from {old_update}')
            new_enough = timedelta(days=7)
            print(datetime.now())
            print(old_update)
            print(new_enough)
            if old_update + timedelta(days=7) > datetime.now():
                print(f'As it is less than {new_enough}, not recalculating.')
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
    # TODO allow argument to be an arbitrary datetime span, not just a
    # calendar year.
    # TODO make aware of any updates from zoneinfo (from system or tz data)
    # and update those years (past, present, or future) on that update.
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


def subtract_edge_dst_tzs(repr_tz_d, standard_time_results,
                          year=datetime.now().year):
    # Subtract time zones that would be in the worker's range,
    # but are not because while they would be in range if they
    # changed to and from DST at the same times as the worker
    # they do not because of non-overlap. This non-overlap time
    # can be as little as an hour, such as in the rolling DST
    # transitions in North America, all at the same local time
    # but at different hours DST, to time zones that are non-
    # overlapping by mere days (Israel/Palestine) or by several
    # weeks. European Union / Lebanon vs. Canada, USA, 20km of
    # Mexico, Cuba. Should return which time zones are
    # excluded and by how much so they can be a different color
    # on the map or in red with a warning (not possible Nov 12
    pprint.pprint(repr_tz_d)
    print(year)
    still_within_range = {}
    non_overlapping_dst = {}
    pprint.pprint(standard_time_results)
    standard_time_results = still_within_range
    return standard_time_results, non_overlapping_dst


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
