#!/usr/bin/env python3
import argparse
import admin2 as admin
import pprint
from consts import *
from datetime import datetime, timedelta


def main():

    """ argparse """
    parser = argparse.ArgumentParser()
    parser.add_argument(type=int,
                        help='the year to calculate time zone dictionaries for',
                        dest='year')
    parser.add_argument('-o', action='store_true', 
                        help='overwrite year\'s time zone dictionaries')
    args = parser.parse_args()
        
    """ Load data structures containing a year's representative time zones,
        their UTC offsets, and their zone transitions for that year if any. 
        
        These functions create the data structures if they do not yet exist 
        for that year, or if a rewrite is needed for a current or future 
        year, prompted by an IANA tz database update, prompted by a
        change in law.
    """
    year = admin.get_year(args)
    zone_transitions_d = admin.get_transitions_dict(year, overwrite=args.o)
    all_to_repr_tz_d, repr_tz_d = admin.get_repr_tz_dicts(zone_transitions_d,
                                                          overwrite=args.o)
    std_repr_tz_d = {k:v for (k, v) in repr_tz_d.items() if v[0][0] == v[0][1]}
    dst_repr_tz_d = {k:v for (k, v) in repr_tz_d.items() if v[0][0] != v[0][1]}
    misalignment_d = admin.get_dst_misalignment_d(dst_repr_tz_d, year)
    
    print(f'Calculating for {year}.')
    print('Zone transition dictionary')
    pprint.pprint(zone_transitions_d)
    print('Representative time zone dictionary:')
    pprint.pprint(repr_tz_d)
    print('All to representative time zone dictionary:')
    pprint.pprint(all_to_repr_tz_d)
    print('Standard representative time zone dictionary')
    pprint.pprint(std_repr_tz_d)
    print('DST representative time zone dictionary')
    pprint.pprint(dst_repr_tz_d)
    print('Misaligned DST dictionary:')
    pprint.pprint(misalignment_d)

    def normalize_offset(offset):
        if offset <= timedelta(seconds=-12*3600):
            offset = offset + timedelta(days=1)
        elif offset > timedelta(seconds=12*3600):
            offset = offset + timedelta(days=-1)
        return offset

    def is_between(offset, westernmost_offset, easternmost_offset):
        if westernmost_offset <= easternmost_offset:
            if westernmost_offset <= offset <= easternmost_offset:
                return True
        if easternmost_offset < westernmost_offset:
            if westernmost_offset <= offset <= timedelta(seconds=12*3600) or timedelta(seconds=-12*3600) <= offset <= easternmost_offset:
                return True
        return False

    def calculate_std_remote_tzs(west_offset, east_offset):
        remote_tzs = list()

        for repr_tz, data in repr_tz_d.items():
            std_r_tz_offset = data[0][0]
            dst_r_tz_offset = data[0][1]
            print(f'{repr_tz} {std_r_tz_offset} {dst_r_tz_offset} {west_offset} {east_offset}')
            if (is_between(std_r_tz_offset, west_offset, east_offset) and
                is_between(dst_r_tz_offset, west_offset, east_offset)):
                remote_tzs.append(repr_tz)
                print('passed')
            else:
                print('failed')
        return remote_tzs
        pass


    # Create all valid sets of remote zones that are valid remote work 
    # zones for any availability start time, remote work start time, 
    # availability length, remote work length.
    #
    # Test these sets and write them to a dictionary. They do not need 
    # to be updated until a system tz update prompted by an IANA tz 
    # database update.
    utc_remote_tzs_d = dict()
    r_start_hr = 9
    r_shift_start = datetime(year, 1, 1, r_start_hr, 0)
    worker_tz = all_to_repr_tz_d['UTC']
    worker_tz_offset = repr_tz_d[worker_tz][0][0]
    for w_start_hr in range(0, 24):
        for w_start_min in [0, 15, 30, 45]:
            for w_end_hr in range(0, 24):
                for w_end_min in [0, 15, 30, 45]:
                    w_shift_start = datetime(year, 1, 1, w_start_hr, w_start_min)
                    w_shift_end = datetime(year, 1, 1, w_end_hr, w_end_min)
                    if w_start_hr == w_end_hr and w_start_min == w_end_min:
                        w_shift_end = datetime(year, 1, 2, w_end_hr, w_end_min)
                    w_shift_length = (w_shift_end - w_shift_start) % timedelta(days=1)
                    east_offset = normalize_offset(r_shift_start - w_shift_start + worker_tz_offset)
                    for r_length_hrs in range(0, 24):
                        r_end_hr = (r_start_hr + r_length_hrs) % 24
                        r_shift_length = timedelta(seconds=r_length_hrs*3600) % timedelta(days=1)
                        west_offset = normalize_offset(east_offset - (w_shift_length - r_shift_length))
                        if w_shift_length >= r_shift_length:
                            """
                            print(f'I live in Dakar in {worker_tz_offset}. My '
                                  f'availability is {str(w_start_hr).zfill(2)}:'
                                  f'{str(w_start_min).zfill(2)} to '
                                  f'{str(w_end_hr).zfill(2)}:'
                                  f'{str(w_end_min).zfill(2)}. I can start a '
                                  f'{r_length_hrs}-hour remote '
                                  f'shift from 09:00 to {str(r_end_hr).zfill(2)}:'
                                  f'00 as far east as {east_offset} and can end one'
                                  f' as far west as {west_offset}')
                            """
                            k = (w_start_hr, w_start_min, w_end_hr, w_end_min,
                                 r_start_hr, 0, r_end_hr, 0) 
                            utc_remote_tzs_d[k] = calculate_std_remote_tzs(
                                    west_offset, east_offset)
                            print(k)
                            print(utc_remote_tzs_d[k])
                            print(w_shift_length)
                            print(r_shift_length)
                            print(west_offset)
                            print(east_offset)

                        else:
                            print(f'{w_shift_length} availability is not long'
                                  f' enough to work {r_shift_length}')
    set_tuple = tuple(tuple(v) for v in utc_remote_tzs_d.values())
    print(len(set(set_tuple)))
    # Determine algorithm that will take any lookup from a standard 
    # time zone and determine which of the valid remote zones calculated
    # for UTC apply.

    # Actually TODO do the DST misalignment removals first from each of the 
    # 1122 sets so that each alignment-set can key in there. LHI gets its own
    # for :30, programmatically of course

    
    # Do the same for representative DST time zones, with a more 
    # restricted west and east due to move.


    # For each representative DST time zone, for each set of remote 
    # time zones were it standard time, move remote zones in the 
    # westernmost (usually hour) that would otherwise fit but do 
    # not because DST zone transition times are different.

    # Do not need to calulate datetimes each time here. Just modify
    # the standard time sets based on the distance (within hours,
    # within a week, within weeks, fail, etc) and key in.


if __name__ == "__main__":
    main()

