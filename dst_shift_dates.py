import pickle
from zoneinfo import ZoneInfo, available_timezones
from rw import create_year_of_same_datetimes
from datetime import datetime, timedelta

def write_dst_shifts(year=datetime.now().year):

    tzs = available_timezones()

    dst_shift_dates = {}
    for tz in tzs:
        dts = [datetime(year, 1, 1, 0, tzinfo=ZoneInfo(tz))]
        curr_dt = dts[0]
        while curr_dt < datetime(year + 1, 1, 1, 0, tzinfo=ZoneInfo(tz)):
            next_dt = curr_dt + timedelta(days=1)
            dts.append(next_dt)
            curr_dt = next_dt

        current_offset = dts[0].tzinfo.utcoffset(dts[0])
        shift_dates = []
        for dt in dts:
            if dt.tzinfo.utcoffset(dt) != current_offset:
                shift_dates.append(dt)
                current_offset = dt.tzinfo.utcoffset(dt)
        dst_shift_dates[tz] = shift_dates

    filename = f'dst_shift_dates_{year}.pickle'
    with open(filename, 'wb') as fd:
        pickle.dump(dst_shift_dates, fd)
