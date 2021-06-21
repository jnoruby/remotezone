#!usr/bin/env python3
import sys
from admin import *
from admin2 import *
from datetime import datetime, timedelta


def normalize(offset):
    if offset <= -12:
        offset = offset + 24
    elif offset > 12:
        offset = offset - 24
    return offset

def get_std_remote_tz_sets(year=datetime.now().year, tz='UTC',
                           w_start_hr=17,
                           w_start_min=0,
                           w_end_hr=6,
                           w_end_min=0,
                           r_start_hr=9,
                           r_start_min=0,
                           r_end_hr=17,
                           r_end_min=0):

    worker_tz_offset = get_standard_offset(tz)
    w_length = shift_length(w_start_hr, w_start_min, w_end_hr, w_end_min)
    r_length = shift_length(r_start_hr, r_start_min, r_end_hr, r_end_min)
    repr_start_dt = datetime(year, 1, 1, w_start_hr, w_start_min)
    repr_end_dt = repr_start_dt + w_length
    r_repr_start_dt = datetime(year, 1, 1, r_start_hr, r_start_min)
    w_start_diff = r_repr_start_dt - repr_start_dt
    east_offset = worker_tz_offset + w_start_diff
    west_offset = east_offset - (w_length - r_length)
    print(w_length)
    print(repr_start_dt)
    print(repr_end_dt)
    print(worker_tz_offset)
    print(east_offset)
    print(west_offset)

    return None



def main():

    # Get query from user, containing:
    #     the user's time zone (IANA tz database string)
    #     for each weekday (usually all):
    #         the user's availability start time
    #         the user's availability end time 
    #     for each weekday (usually all)
    #         the remote shift start time
    #         the remote shift end time
    #         (assuming 09:00 to 17:00 by default.

    get_std_remote_tz_sets()


def main_old():
    """
    Temporary command-line interaction to:
        1) build correct sets of remote time zones for each worker time zone,
           availability period, and shift period.
        2) determine display data - cities, countries, maps for RemoteZone
    These functions need only be run when there is an update to the system's
    time zone information (used by zoneinfo), and for the maps,
    timezone-boundary-builder. Initial build can calculate for future years.
    :return: None
    """
    year = admin.get_year(sys.argv)

    # Check for updates of tz database, timezone-boundary-builder.
    tz_updated = admin.has_tz_updated()
    tbb_updated = admin.has_tbb_updated()

    if tz_updated:
        (all_unique_lookups, 
         all_unique_lookups_set) = admin.build_all_unique_remote_tz_sets(year)

        print(len(all_unique_lookups))
        print(len(all_unique_lookups_set))
    # Calculate remote time zones for a worker in UTC+00:00 working 
    # remotely with the remote shift being 09:00-17:00, 

    """"""
    # TODO restore right back. Make it check for dict before restoration
    # utc_results = admin.calculate_utc_tz_sets(repr_tz_d, year) 

    # For DST-keeping 
    # time zones, this means that the UTC (or any other standard-time)
    # worker, must be available n + 1 hours for an n hour shift.

    # All other standard time time zones are shifted over the relevant
    # number of hours, minutes from the UTC set. Still only calculated 
    # for 09:00-17:00. TODO this can only be a lookup

    # Calculate the above for DST time zones. Now we have to account 
    # for the worker's start and stop times shifting vis-a-vis UTC,
    # but these can still be based on UTC set. Also create categories 
    # of near hits, which the user should be able to see. These near 
    # hits are other DST time zones which are normally within range,
    # but are not because the zone transition times are not aligned - 
    # either within hours (as in rolling North American zone transitions,
    # within a week (Europe / Mexico / Levant), within several weeks,
    # or a month or more off for each shift.

    # The above three can be calculated only for representative tzs, 
    # that is only those with the same UTC offset and transition dates,
    # with like TZs kept in a dictionary for lookup.

    # TODO now the full set of maps should be constructable, ~750 for
    # the standard time to standard time maps, multiplied by needing 
    # to subtract almost-aligning DST time zones and recolor those.
    # Overall how many maps? 
    # 
    # Routine exists in QGIS to create these.
    # Upload them to the server to that user search can load them 
    # instantly based on variable, without having to generate them 
    # in moment. If there are too many (~17 different representative
    # DST time zones, sqrt(729) edge sets would still be 350,000 maps
    # math may be wrong but if it isn't, may have to figure out 
    # QGIS server for adding a layer to maps. 

    # TODO Now there is a single dictionary for all worker_tzs for all
    # time periods (hours 0-23, minutes 0, 1-14, 15, 16-29, 30, 31-44, 
    # 45, 46-59) working 9:00-17:00 containing the sets of remote time
    # zones that work for each (or nearly work, with this indicated).

    # Lookup function can 
    
    # Testing how many DST unique maps there are,
    # actually need to test for fewer by using get_max_distance_two_zones
    # Add each tz to a done list
    #    Check max_distance_two_zones for this match.
    #    If match, add to list of matched with the match and the offset from it 
    #    Finish going through first list
    #    Go through the second list in the same way as the UTC to STD function, using a piece of it.
    #        shifting results over by offset.
    #    Make sure this is writing a dictionary to a pickle before entering a long run.
    # Data structure of DST-time-zone worker remote time zones is a dictionary containing a 
    # dictionary for each DST-time-zone worker.
    # 
    # That dictionary has keys 'remote tzs', 'failed but within hours' with values which
    # are a tuple when full. Tuple has tuples for each remote time zone, with 3 items,
    # string time zone name, datetime offsets. 
    #
    # It is currently missing 'Africa/Juba' - 1 zone transition issue not relevant to 2022 -
    # and missing all representative DST time zones whose result sets are an offset from 
    # a covered one. Current keys: 
    #
    #



if __name__ == "__main__":
    main()
