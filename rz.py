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

        remote_tz_sets = admin.create_remote_tz_sets(repr_tz_d, year)

    pprint.pprint(repr_tz_d)
    print(repr_tzs)
    print(len(repr_tzs))


if __name__ == "__main__":
    main()
