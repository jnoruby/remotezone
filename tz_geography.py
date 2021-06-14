import fileutils
from zoneinfo import ZoneInfo, available_timezones
from datetime import datetime, timedelta
from rw import *
import pickle
from pprint import pprint
import json

def fake():
    d = {}

    year = datetime.now().year
    filename = f'zone_transition_files/zone_transitions_{year}.pickle'
    with open(filename, 'rb') as fd:
        zone_transitions = pickle.load(fd)
    
    all_tzs = available_timezones()
    representative_tz_dict = get_representative_tz_dict(all_tzs)
    representative_tzs = set(v for v in representative_tz_dict.values())

    print(len(representative_tzs) * 23 * 23 * 4 * 4)

def get_unique_r_tz_sets():
    """ Run once a year """
    # Dictionary to temporarily hold as key:
    #   (each worker time zone, each start hour, each start fifteen-minute interval,
    #    each length in hours, each length fifteen-minute interval)
    # as value, results of get_r_tzs [] 
    # TODO just assuming 8-hour shifts now of 9 to 5 in remote.
    d = {}

    year = datetime.now().year
    filename = f'zone_transition_files/zone_transitions_{year}.pickle'
    with open(filename, 'rb') as fd:
        zone_transitions = pickle.load(fd)
    
    all_tzs = available_timezones()
    representative_tz_dict = get_representative_tz_dict(all_tzs)
    representative_tzs = set(v for v in representative_tz_dict.values())

    print(len(representative_tzs) * 23 * 23 * 4 * 4)
    count = 1
    for tz in representative_tzs:
        for w_start_hr in range(0, 24):
            for start_min in range(0, 60, 15):
                for w_length_hrs in range(0, 24):
                    for w_length_mins in range(0, 60, 15):
                        count = count + 1
                        print(count)
                        d[tz] = get_r_tzs(zone_transitions, tz, 
                                          year=datetime.now().year,
                                          w_start_hr=w_start_hr,
                                          w_start_min=w_start_min,
                                          w_length_hrs=w_length_hrs,
                                          w_length_mins=w_length_mins)

    unique_values_dict = {}
    unique_r_tz_sets = {}
    for key, value in d.items():
        if value not in unique_values_dict.values():
            unique_values_dict[key] = value
    inverted_unique_values_dict = {v: k for k, v in unique_values_dict.items()}
    for key, value in d.items():
        unique_r_tz_sets[key] = inverted_unique_values_dict[value]    
    
    print(len(unique_r_tz_sets))
    with open('unique_r_tz_sets.json', 'w') as f:
        json.dump(unique_r_tz_sets, f)


def update_shapefiles_if_new():
    """ QGIS Server generation of the map of the set of valid time zones for
        the user request requires certain ESRI shapefiles.
        
        TODO: Should be run on a schedule. Daily perhaps? No need for constant
              requests.
    """
    
    # Evan Siroky's timezone-boundary-builder is used for the borders of time
    # zones covering Earth's land and territorial waters. Release may be behind
    # from IANA tz database. For instance, as of 2021-06, tz is on 2021a and 
    # timezone-boundary-builder is on 2020d. Changes of offset from predicted 
    # are more common than boundary changes, especially for future rather than 
    # past data, so this should not be a problem.

    # Fallback file - release 2020d, in case update routine fails
    tbb_backup_dir = 'geography_source/backup'
    
    # Compare latest release date on Github with date of latest update to file.
    # Retrieve JSON from Github if newer, an empty dict if not, and none if
    #   requests.ConnectionError
    tbb_date_path = 'geography_source/tbb-date-path.json'
    tbb_url = ('https://api.github.com/repos/evansiroky/' +
               'timezone-boundary-builder/releases/latest')
    _, github_json = fileutils.has_tbb_updated()

    # Retrieve and write to file if there has been an update. Update data file 
    # containing date of latest download.
    if github_json is not None:
        if len(github_json) > 0:
            tbb_dir = 'geography_source/'
            tbb_dt_string = github_json['published_at']
            fileutils.write_updated_shapefiles(github_json, tbb_dir)
            fileutils.update_latest_download_date(tbb_date_path, tbb_dt_string)
        else:
            # Github version not newer
            tbb_dir = 'geography_source/'
            print('Newest timezone-boundary-builder release already loaded.')
    else:
        # request went wrong somehow
        tbb_dir = tbb_backup_dir
        print('timezone-boundary-builder requests broken. Using backup.')
    return tbb_dir
