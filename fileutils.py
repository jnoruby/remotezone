import json
import requests
import os

from dateutil import parser
import datetime as dt
from datetime import datetime
from zoneinfo import ZoneInfo

from pprint import pprint


def has_zoneinfo_updated():
    """ Not ready yet. Wait until deployment to server, as will be able to 
    check updates to system tz data then. Until that time, functions which 
    would otherwise use this to determine whether zoneinfo-update-dependent
    updates should run, should operated on a schedule instead.

    Return True in the meantime.
    """
    return True


def has_tbb_updated():
    """ Retrieve JSON object if remote release is newer than the release 
        current files are from.

        Currently used with Github timezone-boundary-builder. Can be used more
        widely if abstracted.
    """
    tbb_date_path = 'geography_source/tbb-date-path.json'
    tbb_url = ('https://api.github.com/repos/evansiroky/' +
               'timezone-boundary-builder/releases/latest')
    try:
        with open(tbb_date_path, 'r') as infile:
            local_dt_string = json.load(infile)
            local_dt = parser.parse(local_dt_string)
            is_remote_version_newer = False
    except FileNotFoundError:
        # Remote version is newer if file with latest update date is not found.
        # Create fake datetime for comparison that will always be the earlier.
        local_dt = datetime(dt.MINYEAR, 1, 1, tzinfo=ZoneInfo('UTC'))
        is_remote_version_newer = True
    if is_remote_version_newer:
        try:
            remote_dt_response = requests.get(tbb_url)
            remote_dt_string = remote_dt_response.json()['published_at']
            remote_dt = parser.parse(remote_dt_string)
            if remote_dt > local_dt:
                json_object = remote_dt_response.json()
                is_remote_version_newer = True
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
    else:
        json_object = dict()
    return is_remote_version_newer, json_object


def write_updated_shapefiles(github_json, out_path):
    for asset in github_json['assets']:
        url = asset['browser_download_url']
        outfile = os.path.join(out_path, url.split('/')[-1])
        r = requests.get(url)
        with open(outfile, 'wb') as f:
            f.write(r.content)


def update_latest_download_date(local_path, remote_dt_string):
    with open(local_path, 'w') as outfile:
        json.dump(remote_dt_string, outfile)
