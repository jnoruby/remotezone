import json
import pickle
import requests
import datetime as dt
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import parser
from zoneinfo import ZoneInfo, available_timezones
from consts import *

""" USED IN LATEST VERSION  """
# get_year() )
# get_transitions_dict() - updating an old version with more efficiency
# get_repr_tz_dicts() - updating an old version with both offsets in dict
#   get_offsets()
# get_dst_transition_misalignment_type_d() - update
"""                         """


def get_dst_misalignment_d(dst_repr_tz_d, year=datetime.now().year,
                           overwrite=False):
    def write_dst_misalignment_dict(dst_repr_tz_d):
        misalignment_d = dict()
        for tz1, data in dst_repr_tz_d.items():
            zt1 = data[1]
            for tz2, data in dst_repr_tz_d.items():
                zt2 = data[1]
                dst_distance = get_max_misalignment(zt1, zt2)
                misalignment_category = get_misalignment_category(dst_distance)
                misalignment_d[(tz1, tz2)] = misalignment_category
        with open(filename, 'wb') as f:
            pickle.dump(misalignment_d, f)
        return misalignment_d

    def get_misalignment_category(dst_distance):
        if dst_distance == timedelta(seconds=0):
            misalignment_category = None
        elif timedelta(seconds=1) <= dst_distance < timedelta(
                seconds=12 * 3600):
            misalignment_category = 'hours'
        elif timedelta(seconds=12 * 3600) <= dst_distance < timedelta(days=7):
            misalignment_category = 'within a week'
        elif timedelta(days=7) <= dst_distance < timedelta(days=30):
            misalignment_category = 'weeks'
        else:  # dst_distance >= timedelta(days=30):
            misalignment_category = 'months'
        return misalignment_category

    def get_max_misalignment(zt1, zt2, year=datetime.now().year):
        print(zt1)
        print(zt2)
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

    filename = f'rz_data/zt_nonalignment_lookup_{year}.pickle'
    if not overwrite:
        try:
            with open(filename, 'rb') as f:
                misalignment_d = pickle.load(f)
        except FileNotFoundError:
            misalignment_d = write_dst_misalignment_dict(dst_repr_tz_d)
    else:
        misalignment_d = write_dst_misalignment_dict(dst_repr_tz_d)
    return misalignment_d


def get_transitions_dict(year=datetime.now().year, overwrite=False):
    def write_transitions_dict(filename, year, tzs):
        zone_transitions_d = dict()
        for tz in tzs:
            zone_transitions = get_transitions_from_hourly_dts(tz, year)
            zone_transitions_d[tz] = zone_transitions
        with open(filename, 'wb') as fd:
            pickle.dump(zone_transitions_d, fd)
        return zone_transitions_d

    def get_transitions_from_hourly_dts(tz='UTC', year=datetime.now().year):
        zone_transitions = list()
        curr_dt = datetime(year, 1, 1, 0, tzinfo=ZoneInfo(tz))
        next_year = datetime(year + 1, 1, 1, 0, tzinfo=ZoneInfo(tz))
        while curr_dt < next_year:
            curr_offset = curr_dt.tzinfo.utcoffset(curr_dt)
            next_dt = curr_dt + timedelta(seconds=3600)
            if next_dt.tzinfo.utcoffset(next_dt) != curr_offset:
                zone_transitions.append(next_dt)
            curr_dt = next_dt
        return zone_transitions

    tzs = available_timezones()
    filename = f'rz_data/zone_transitions_{year}.pickle'
    if not overwrite:
        try:
            with open(filename, 'rb') as fd:
                zone_transitions_d = pickle.load(fd)
        except FileNotFoundError:
            zone_transitions_d = write_transitions_dict(filename, year, tzs)
    else:
        zone_transitions_d = write_transitions_dict(filename, year, tzs)

    return zone_transitions_d


def get_repr_tz_dicts(zone_transition_d, year=datetime.now().year,
                      overwrite=False):
    def write_repr_tz_dicts(zone_transition_d, repr_filename,
                            all_to_repr_filename, year):
        tzs = available_timezones()
        tz_characteristics_d = dict()
        all_to_repr_tz_d = dict()

        for tz in tzs:
            try:
                zone_transitions = zone_transition_d[tz]
            except KeyError:
                zone_transitions = list()
            std_offset, dst_offset = get_offsets(zone_transitions, tz, year)
            tz_characteristics_d[tz] = (
                (std_offset, dst_offset),
                tuple(zone_transitions))

        unique_values_d = dict()
        for key, value in tz_characteristics_d.items():
            if value not in unique_values_d.values():
                unique_values_d[key] = value
        inverted_unique_values_d = {v: k for k, v in unique_values_d.items()}
        for key, value in tz_characteristics_d.items():
            all_to_repr_tz_d[key] = inverted_unique_values_d[value]

        repr_tz_d = {k: v for (k, v) in tz_characteristics_d.items() if k in
                     all_to_repr_tz_d.values()}

        with open(repr_filename, 'wb') as fd:
            pickle.dump(repr_tz_d, fd)
        with open(all_to_repr_filename, 'wb') as fd:
            pickle.dump(all_to_repr_tz_d, fd)

        return all_to_repr_tz_d, repr_tz_d

    repr_filename = f'rz_data/representative_tzs_{year}.pickle'
    all_to_repr_filename = f'rz_data/all_to_repr_tzs_{year}.pickle'
    if not overwrite:
        try:
            with open(repr_filename, 'rb') as fd:
                repr_tz_d = pickle.load(fd)
            with open(all_to_repr_filename, 'rb') as fd:
                all_to_repr_tz_d = pickle.load(fd)
        except FileNotFoundError:
            all_to_repr_tz_d, repr_tz_d = write_repr_tz_dicts(
                zone_transition_d, repr_filename,
                all_to_repr_filename, year)
    else:
        all_to_repr_tz_d, repr_tz_d = write_repr_tz_dicts(
            zone_transition_d, repr_filename,
            all_to_repr_filename, year)

    return all_to_repr_tz_d, repr_tz_d


def get_year(args=None):
    def year_error(bad_year):
        print(f'Entered string \'{bad_year}\' cannot be interpreted as a '
              f'calendar year that can be used for time zone calculations.'
              f'\nCalculating for the current year instead. Usage: '
              f'{MIN_TZ_YEAR} <= year <= {MAX_TZ_YEAR}')
        return datetime.now().year

    try:
        year = int(args.year)
        _dt = datetime(year + 1, 1, 1)  # Prohibit datetime maximum year
    except ValueError:
        year = year_error(args.year)

    if year < 1970:
        year = year_error(args.year)

    return year


def get_offsets(zone_transitions, tz='UTC', year=datetime.now().year):
    def calculate_offsets_from_repr_dts(test_zts):
        std_offset_i = test_zts.index(
            min(test_zts, key=lambda x: x.tzinfo.utcoffset(x)))
        dst_offset_i = test_zts.index(
            max(test_zts, key=lambda x: x.tzinfo.utcoffset(x)))
        std_offset = test_zts[std_offset_i].tzinfo.utcoffset(
            test_zts[std_offset_i])
        dst_offset = test_zts[dst_offset_i].tzinfo.utcoffset(
            test_zts[dst_offset_i])
        # print(f'{tz} {std_offset} {dst_offset}')
        return std_offset, dst_offset

    test_zts = []
    if len(zone_transitions) == 0:
        test_zts = [datetime(year, 1, 1, 0, tzinfo=ZoneInfo(tz))]
    elif len(zone_transitions) == 1:
        zt = zone_transitions[0]
        test_zts = [zt + timedelta(days=-1), zt + timedelta(days=1)]
    elif len(zone_transitions) == 2:
        test_zts = [zt + timedelta(days=1) for zt in zone_transitions]
    else:
        print(f'FATAL BUILD ERROR. {tz} has outside of 0, 1, or 2 or more '
              f'zone transitions and no code accounts for that')
        exit()

    return calculate_offsets_from_repr_dts(test_zts)