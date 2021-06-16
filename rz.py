#!usr/bin/env python3
import sys
from datetime import datetime
import admin

import pprint

def main():
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
        all_to_repr_tz_d, repr_tz_d = admin.get_representative_tz_dicts(year)
        repr_tzs = [k for k in repr_tz_d.keys()]
        zone_transitions = admin.get_zone_transitions_dict(year)

        # Calculate remote time zones for a worker in UTC+00:00 working 
        # remotely with the remote shift being 09:00-17:00, For DST-keeping 
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

    pprint.pprint(repr_tz_d)
    print(repr_tzs)
    print(len(repr_tzs))


if __name__ == "__main__":
    main()
