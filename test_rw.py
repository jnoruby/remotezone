import unittest
import pickle
from rw import *
import random

all_tzs = available_timezones()
zt = get_zone_transitions_dict(2021)
all_to_repr_tz_d, repr_tz_d = get_all_to_repr_tz_dicts(all_tzs)
repr_tzs = list(set(v for v in all_to_repr_tz_d.values()))
test_repr_tzs = {
                (14, 14): 'Pacific/Kiritimati',
                (13, 14): 'Pacific/Apia',
                (13, 13): 'Pacific/Fakaofo',
                (12.75, 13.75): 'NZ-CHAT',
                (12, 13): 'Pacific/Fiji',
                (12, 13): 'Antarctica/South_Pole',
                (12, 12): 'Pacific/Funafuti',
                (11, 12): 'Pacific/Norfolk',
                (11, 11): 'Etc/GMT-11',
                (10.5, 11): 'Australia/Lord_Howe',
                (10, 10): 'Australia/Currie',
                (10, 10): 'Australia/Lindeman',
                (9.5, 10.5): 'Australia/Adelaide',
                (9.5, 9.5): 'Australia/North',
                (9, 9): 'Asia/Khandyga',
                (8.75, 8.75): 'Australia/Eucla',
                (8, 8): 'Asia/Choibalsan',
                (7, 7): 'Antarctica/Davis',
                (6.5, 6.5): 'Indian/Cocos',
                (6, 6): 'Asia/Omsk',
                (5.75, 5.75): 'Asia/Kathmandu',
                (5.5, 5.5): 'Asia/Colombo',
                (5, 5): 'Asia/Ashkhabad',
                (4.5, 4.5): 'Asia/Kabul',
                (4, 4): 'Asia/Dubai',
                (3.5, 4.5): 'Asia/Tehran',
                (3, 3): 'Europe/Kirov',
                (2, 3): 'Europe/Chisinau',
                (2, 3): 'Europe/Nicosia',
                (2, 3): 'Asia/Beirut',
                (2, 3): 'Israel',
                (2, 3): 'Asia/Amman',
                (2, 2): 'Africa/Johannesburg',
                (2, 3): 'Asia/Hebron',
                (2, 3): 'Africa/Juba',
                (2, 3): 'Asia/Damascus',
                (1, 2): 'Europe/Berlin',
                (0, 2): 'Antarctica/Troll',
                (1, 1): 'Africa/Malabo',
                (0, 1): 'Europe/Guernsey',
                (0, 0): 'America/Danmarkshavn',
                (0, 1): 'Africa/El_Aaiun',
                (-1, 0): 'Atlantic/Azores',
                (-1, -1): 'Atlantic/Cape_Verde',
                (-2, -2): 'America/Noronha',
                (-3, -2): 'America/Nuuk',
                (-3, -3): 'America/Argentina/Cordoba',
                (-3, -2): 'America/Miquelon',
                (-3.5, -2.5): 'America/St_Johns',
                (-4, -3): 'America/Santiago',
                (-4, -4): 'America/St_Barthelemy',
                (-4, -3): 'America/Glace_Bay',
                (-4, -3): 'America/Asuncion',
                (-5, -5): 'America/Atikokan',
                (-5, -4): 'America/Detroit',
                (-5, -4): 'America/Havana',
                (-6, -5): 'Pacific/Easter',
                (-6, -5): 'America/Bahia_Banderas',
                (-6, -6): 'America/Costa_Rica',
                (-6, -5): 'America/Chicago',
                (-7, -6): 'Mexico/BajaSur',
                (-7, -7): 'Canada/Yukon',
                (-7, -6): 'US/Mountain',
                (-8, -8): 'Pacific/Pitcairn',
                (-8, -7): 'US/Pacific',
                (-9, -9): 'Etc/GMT+9',
                (-9, -8): 'America/Nome',
                (-9.5, -9.5): 'Pacific/Marquesas',
                (-10, -10): 'America/Adak',
                (-10, -10): 'Pacific/Honolulu',
                (-11, -11): 'Etc/GMT+11',
                (-12, -12): 'Etc/GMT+12'}



class TestTZByRange(unittest.TestCase):

    def test_utc(self):

        self.tz = 'UTC'

        def test_availability_too_short(self):
            start_hr = random.randint(0, 24)
            end_hr = start_hr + 7
            end_hr = end_hr if end_hr < 24 else end_hr - 24
            self.assertEqual(list(), get_remote_tzs_by_range(worker_tz=self.tz,
                                                             w_start_hr = start_hr,
                                                             w_end_hr = end_hr))
        def test_24_hr_availability(self):
            start_hr = random.randint(0, 24)
            end_hr = start_hr
            self.assertEqual(list(repr_tz_d),
                             get_remote_tzs_by_range(worker_tz=self.tz,
                                                     w_start_hr=start_hr,
                                                     w_end_hr=end_hr))

        def test_8_hr_worker(self):
            # Should be 8 to the east (17 - 9) and 16 to the west (17 - 1)  only.
            # Actually could be other direction. TODO SLEEP
            
            def configure_variables(start_hr, start_min, end_hr, end_min):
                remote_repr_tzs = get_remote_tzs_by_range(worker_tz=self.tz,
                                                          w_start_hr=start_hr, 
                                                          w_start_min=start_min,
                                                          w_end_hr=end_hr,
                                                          w_end_min=end_min)
                remote_tzs = get_all_tzs_matching_repr_tzs(remote_repr_tzs,
                                                           all_to_repr_tz_d)
                return remote_tzs

            remote_tzs = configure_variables(17, 0, 1, 0)
            self.assertFalse('Etc/GMT+9' in remote_tzs)  # -9, -9
            self.assertFalse('America/Nome' in remote_tzs)  # -9, -8
            self.assertTrue('Pacific/Pitcairn' in remote_tzs)  # ===== -8
            self.assertFalse('US/Pacific' in remote_tzs)  # -8, -7
            self.assertFalse('Canada/Yukon' in remote_tzs)  # -7, -7
        
            remote_tzs = configure_variables(23, 0, 7, 0)
            self.assertFalse('Australia/North' in remote_tzs)  # +9.5, +9.5
            self.assertFalse('Australia/Adelaide' in remote_tzs)  # +9.5, +10.5
            self.assertTrue('Australia/Lindeman' in remote_tzs)  # ==== +10
            self.assertFalse('Australia/Currie' in remote_tzs)  # +10, +11
            self.assertFalse('Australia/Lord_Howe' in remote_tzs)  #  +10.5, +11

            remote_tzs = configure_variables(5, 0, 13, 0)
            self.assertFalse('Europe/Kirov' in remote_tzs)  # +3, +3
            self.assertFalse('Asia/Tehran' in remote_tzs)  # +3.5, 4.5
            self.assertTrue('Asia/Dubai' in remote_tzs)  # ==== +4
            self.assertFalse('Asia/Kabul' in remote_tzs)  # +4.5, +4.5
            self.assertFalse('Asia/Ashkhabad' in remote_tzs)  # +5, +5

            remote_tzs = configure_variables(11, 0, 19, 0)
            self.assertFalse('America/Sao_Paulo' in remote_tzs)  # -3 -3
            self.assertTrue('Atlantic/South_Georgia' in remote_tzs)  # -2, -2
            self.assertFalse('Atlantic/Azores' in remote_tzs) # -1 -1
        
        test_availability_too_short(self)
        test_24_hr_availability(self)
        test_8_hr_worker(self)
"""
class TestExtractOffHourTZs(unittest.TestCase):

    def test_extract_off_hour_tzs(self):
        self.assertEqual(extract_off_hour_tzs(['America/St_Johns',
                                               'Asia/Kathmandu'], all_to_repr_tz_d,
                                               repr_tz_d),
                         ['America/St_Johns', 'Asia/Kathmandu'])
        self.assertEqual(extract_off_hour_tzs(['Asia/Karachi',
                                               'Asia/Kathmandu'], all_to_repr_tz_d,
                                               repr_tz_d),
                         ['Asia/Kathmandu'])
        self.assertEqual(extract_off_hour_tzs(['Asia/Karachi',
                                               'Asia/Dubai'], all_to_repr_tz_d,
                                               repr_tz_d),
                         [])

class TestFunctionalSlowMethod(unittest.TestCase):

    def test_functional_slow_method(self):

        off_hour_tzs = extract_off_hour_tzs(repr_tzs,
                                            all_to_repr_tz_d,
                                            repr_tz_d)

        
        # No remote time zones when w_length_hrs < r_length_hrs (default 8)
        w_length_hrs = 4
        for i in range(0, 2):
            tz = random.choice(repr_tzs)
            self.assertEqual(get_r_tzs(zt, tz=tz,
                                       w_length_hrs=w_length_hrs),
                             list())

        w_length_hrs = 8
        
        # Off-hour remote tzs only have off-hour matches when working 8 hrs 
        for i in range(0, 4):
            tz = random.choice(off_hour_tzs)
            for j in range(0, 4):
                w_start_hr = random.randint(0, 23)
                r_tzs = get_r_tzs(zt, tz=tz,
                                  w_length_hrs=w_length_hrs,
                                  w_start_hr=w_start_hr)
                if len(r_tzs) > 0:
                    self.assertEqual(r_tzs,
                                     extract_off_hour_tzs(r_tzs, all_to_repr_tz_d,
                                                          repr_tz_d))
        # All remote TZs when working 8 hrs have the same zone transitions 
        # or lack thereof. 
        # TODO new version should return impossible time periods, so that if 
        # the mismatch affects only one day, user can judge.
        for i in range(0, 4):
            tz = random.choice(repr_tzs)
            for j in range(0, 4):
                w_start_hr = random.randint(0, 23)
                r_tzs = get_r_tzs(zt, tz=tz,
                                  w_length_hrs=w_length_hrs,
                                  w_start_hr=w_start_hr)
                if len(r_tzs) > 0:
                    for tz in r_tzs:
                        r_zt = repr_tz_d[all_to_repr_tz_d[tz]][1]
                        self.assertEqual(zt[tz], list(r_zt))


class TestEasierWay(unittest.TestCase):

    def test_easier_way(self):

        representative_tz_d, repr_tz_d = get_representative_tz_dicts(all_tzs)
        representative_tzs = list(set(v for v in representative_tz_d.values()))
        non_dst_repr_tzs = [tz for tz in representative_tzs
                            if not has_zone_transitions(tz)]

        def test_easier_way_both_non_dst(self):
            tzs = representative_tzs
            for tz in tzs:
                remote_tz_offset_range = get_remote_tz_offset_range(tz)
                # pprint.pprint(representative_tz_d)
                # pprint.pprint(repr_tz_d)

                success_tzs = [tz for tz in list(representative_tzs) if
                        len(repr_tz_d[representative_tz_d[tz]][1]) == 0 and
                        get_offset_as_float(repr_tz_d[representative_tz_d[tz]][0])
                        == remote_tz_offset_range]

                old_way = get_r_tzs(zt, tz=tz)
                for r_tz in success_tzs:
                    print(f'{tz}: {r_tz}:'
                          f'\t{r_tz in old_way}')

                #print(tz)
                #print(remote_tz_offset_range)
                #print(success_tzs)
        
        test_easier_way_both_non_dst(self)

class TestHasZoneTransitions(unittest.TestCase):

    def test_tz_key_error(self):
        with self.assertRaises(KeyError):
            has_zone_transitions(tz='Essos/Yi_Ti')

    def test_year_value_error(self):
        # datetime "today" or "tomorrow" out of range
        with self.assertRaises(ValueError):
            has_zone_transitions(year=9999)
            has_zone_transitions(year=0)

    def test_year_type_error(self):
        with self.assertRaises(TypeError):
            has_zone_transitions(year=(1982, 1, 31))

    def test_default(self):
        # UTC has no zone transitions by definition.
        self.assertFalse(has_zone_transitions())

    def test_known_non_dst_tzs(self):
        self.assertFalse(has_zone_transitions(tz='America/Bogota', year=2021))
        self.assertFalse(has_zone_transitions(tz='Europe/Moscow', year=2021))

    def test_known_dst_tzs(self):
        self.assertTrue(has_zone_transitions(tz='Pacific/Apia', year=2021))
        self.assertTrue(has_zone_transitions(tz='Europe/Moscow', year=2010))


class TestWorkerCanWorkInTZ(unittest.TestCase):
    # A DST time zone is only a valid remote time zone for a DST-based worker
    # if within worker's availability for all dates in year. This is not the
    # case when DST shift dates are different between time zones and range is
    # not within worker's availability.

    def test_biggest(self):
        pass
        # for i in range(10000):
            # Generate random time zones and related time variables. Get the
            # number of bad days from worker_can_work_in_tz(). If 0, pick a
            # random day and compare the datetimes to confirm worker span is
            # within remote span. If positive,
            # TODO also return all days, not just sample, with range possible)

    def test_zone_transitions_misaligned(self):
        # As of 2021: EU, Lebanon, and Palestine all observed DST. Lebanon and
        # Palestine were 3 hours ahead of Azores. Lebanon's DST dates were
        # aligned with the EU's DST dates. Palestine's started on Saturday,
        # off by one day.
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        w_tz = 'Atlantic/Azores'
        w_zone_transitions = get_worker_zone_transitions(zone_transitions, w_tz, year)
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Asia/Beirut',
                                               zone_transitions, w_zone_transitions,
                                               w_start_hr=9, r_start_hr=12, year=year), 0)
        self.assertNotEqual(worker_can_work_in_tz(w_tz, 'Asia/Hebron',
                                                  zone_transitions, w_zone_transitions,
                                                  w_start_hr=9, r_start_hr=12, year=year), 0)

        # As of 2021: California and Chihuahua both observed DST. Most of
        # Chihuahua shifted along with the rest of Mexico (1st Sunday in April,
        # last Sunday in October). Regions within 20 km of the US border, like
        # Ojinaga, shifted along with the US instead.
        w_tz = 'America/Los_Angeles'
        w_zone_transitions = get_worker_zone_transitions(zone_transitions, w_tz, year)
        self.assertEqual(worker_can_work_in_tz(w_tz, 'America/Ojinaga',
                                               zone_transitions, w_zone_transitions,
                                               w_start_hr=0, r_start_hr=1, year=year), 0)
        self.assertNotEqual(worker_can_work_in_tz(w_tz, 'America/Chihuahua',
                                                  zone_transitions, w_zone_transitions,
                                                  w_start_hr=0, r_start_hr=1, year=year), 0)

    def test_zone_transitions_aligned_shifts_during_shift_hour(self):

        # Even where two DST time zones are within the same shifting zone, an 8
        # hour match will fail when either the worker's availability or the
        # remote work shift overlaps the exact time of DST shift.
        # TODO Make it such that where it's only a two-day mismatch like this
        # the failed days are returned, so that it's not an absolute no, but
        # something that the worker would simply have to add a single hour of
        # availability for those days.
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        w_tz = 'America/New_York'
        w_zone_transitions = get_worker_zone_transitions(zone_transitions, w_tz, year)
        # Worker shift and remote shifts are both after DST switch hour.
        self.assertEqual(worker_can_work_in_tz(w_tz, 'America/Denver',
                                               zone_transitions, w_zone_transitions,
                                               w_start_hr=8, r_start_hr=6, year=year), 0)
        # Worker shift starts after DST switch; remote has a DST switch.
        self.assertNotEqual(worker_can_work_in_tz(w_tz, 'America/Denver',
                                                  zone_transitions, w_zone_transitions,
                                                  w_start_hr=2, r_start_hr=0, year=year), 0)
        # Worker shift and remote shifts both span DST switch.
        self.assertEqual(worker_can_work_in_tz(w_tz, 'America/Denver',
                                               zone_transitions, w_zone_transitions,
                                               w_start_hr=21, r_start_hr=19, year=year), 0)

    # Representing a Southern-Hemisphere off-hour time zone without DST
    def test_australia_darwin(self):
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        w_tz = 'Australia/Darwin'
        w_zone_transitions = get_worker_zone_transitions(zone_transitions, w_tz, year)
        max_days_diff = 0

        # A worker starting at 10:30 in Darwin (default availability 8 hours)
        # should be able to start a remote shift (default 9:00 - 17:00)
        # in Shanghai (worker +09:30, remote +08:00. both no DST).
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Asia/Shanghai',
                                               zone_transitions, w_zone_transitions, w_start_hr=10,
                                               w_start_min=30), max_days_diff)
        # The same time variables will not work for neighboring non-DST TZs

        # +08:45
        self.assertGreater(worker_can_work_in_tz(w_tz, 'Australia/Eucla',
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=10,
                                                 w_start_min=30), max_days_diff)

        # +07:00
        self.assertGreater(worker_can_work_in_tz(w_tz, 'Asia/Ho_Chi_Minh',
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=10,
                                                 w_start_min=30), max_days_diff)

        # Nor will they work for neighboring DST off-hour time zone
        self.assertGreater(worker_can_work_in_tz(w_tz, 'Australia/Adelaide',
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=10,
                                                 w_start_min=30), max_days_diff)

        # A worker in Darwin limited to an on-hour 8-hour default shift will
        # only be able to work in half-hour offset time zones w/ no DST.
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Asia/Kolkata',
                                               zone_transitions, w_zone_transitions, w_start_hr=13,
                                               w_start_min=0), max_days_diff)

        # Not with DST
        self.assertGreater(worker_can_work_in_tz(w_tz, 'America/St_Johns',
                                                 zone_transitions, w_zone_transitions, w_start_hr=3,
                                                 w_start_min=0), max_days_diff)

        # Specific 45-minute offset would be required to work in Kathmandu`
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Asia/Kathmandu',
                                               zone_transitions, w_zone_transitions, w_start_hr=12,
                                               w_start_min=45), max_days_diff)
        self.assertGreater(worker_can_work_in_tz(w_tz, 'Asia/Kathmandu',
                                                 zone_transitions, w_zone_transitions, w_start_hr=0,
                                                 w_start_min=0), max_days_diff)

        # 8-hour shift (here from 18:00 - 02:00) matches no 9:00 - 17:00
        # remote shifts as there is no +00:30 offset.
        zones = available_timezones()
        for r_tz in zones:
            self.assertGreater(worker_can_work_in_tz(w_tz, r_tz,
                                                     zone_transitions, w_zone_transitions,
                                                     w_start_hr=18,
                                                     w_start_min=0), max_days_diff)

        # Expanding to a 9-hour shift (here from 18:00 - 03:00) allows work
        # from 08:30 - 17:30 UTC and adds first 09:00 - 17:00 on-hour offsets.
        # Specifically +00:00
        w_length = timedelta(seconds=9 * 3600)
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Africa/Bissau',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)
        # All DST time zones still off limits.
        for r_tz in zones:
            if has_zone_transitions(r_tz):
                self.assertGreater(worker_can_work_in_tz(w_tz, r_tz,
                                                         zone_transitions, w_zone_transitions,
                                                         w_start_hr=18,
                                                         w_start_min=0, w_length=w_length),
                                   max_days_diff)

        w_length = timedelta(seconds=10 * 3600)
        # Expanding to 10 hours (here from 18:00 - 04:00) allows work from
        # 08:30 - 18:30 UTC and adds -01:00 +00:00
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Atlantic/Azores',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)
        # Also adds -01:00 with no DST.
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Atlantic/Cape_Verde',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)
        # -02:00 -02:00 and -02:00 -01:00 still out of bounds.
        self.assertGreater(worker_can_work_in_tz(w_tz, 'America/Noronha',
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=18,
                                                 w_start_min=0, w_length=w_length),
                           max_days_diff)

        # Expanding to 13 hours (18:00 - 07:00)
        # UTC and adds up to -4:00 -4:00 and -04:00 -03:00
        w_length = timedelta(seconds=13 * 3600)
        self.assertEqual(worker_can_work_in_tz(w_tz, 'America/Santiago',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)
        self.assertEqual(worker_can_work_in_tz(w_tz, 'America/Puerto_Rico',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)

        # Expanding to 21 hours (18:00 - 15:00) has only 15:00 - 18:00 (+09:30)
        # unavailable, which is 05:30 - 08:30 UTC. This is in default work shift
        # in any TZ that has +01:00 at times to +11:00
        w_length = timedelta(seconds=21 * 3600)
        self.assertGreater(worker_can_work_in_tz(w_tz, 'Africa/Lagos',
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=18,
                                                 w_start_min=0, w_length=w_length),
                           max_days_diff)
        self.assertGreater(worker_can_work_in_tz(w_tz, 'Europe/London',
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=18,
                                                 w_start_min=0, w_length=w_length),
                           max_days_diff)
        self.assertGreater(worker_can_work_in_tz(w_tz, w_tz,
                                                 zone_transitions, w_zone_transitions,
                                                 w_start_hr=18,
                                                 w_start_min=0, w_length=w_length),
                           max_days_diff)
        # But OK 11:30 (can't work a home shift) - through 00:00
        self.assertEqual(worker_can_work_in_tz(w_tz, 'Antarctica/South_Pole',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)
        self.assertEqual(worker_can_work_in_tz(w_tz, 'UTC',
                                               zone_transitions, w_zone_transitions, w_start_hr=18,
                                               w_start_min=0, w_length=w_length),
                         max_days_diff)

    # Representing a Northern-Hemisphere on-hour time zone with DST.
    def test_america_new_york(self):
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        w_tz = 'America/New_York'
        w_zone_transitions = get_worker_zone_transitions(zone_transitions, w_tz, year)

        # Test 8-hour shifts, worker begins 10:00.
        w_length_hrs = 8
        max_days_diff = 0  # Better algorithm needed for low # of rule shifts

        # 1 hour behind. Should only yield -06:00 > -05:00 w/ aligned DST
        r_tzs = get_r_tzs(zone_transitions, w_tz, w_length_hrs=w_length_hrs,
                          w_start_hr=10, max_days_diff=max_days_diff,
                          year=year)
        r_tzs = [t for t in r_tzs if has_zone_transitions(t)]
        self.assertTrue('America/Chicago' in r_tzs)  # -06:00 w/ aligned DST
        self.assertFalse('America/Mexico_City' in r_tzs)  # -6:00 w/ unaligned DST N. Hem.
        self.assertFalse('Pacific/Eastern' in r_tzs)  # -6:00 w/ unaligned DST S. Hem.
        self.assertFalse('America/Managua' in r_tzs)  # -6:00 w/o DST
        self.assertFalse('Africa/Nairobi' in r_tzs)  # Outside range

        # 1.5 hours behind. Should be empty. TODO fix
        # r_tzs = get_r_tzs(zone_transitions, w_tz, w_length_hrs=w_length_hrs,
        #         w_start_hr=10, w_start_min=30, max_days_diff=max_days_diff,
        #         year=year)
        # self.assertEqual(r_tzs, list())

        # 12 hours behind. Should be empty as no timezone -12 from NYC has
        # aligned DST.
        r_tzs = get_r_tzs(zone_transitions, w_tz, w_length_hrs=w_length_hrs,
                          w_start_hr=21, w_start_min=0, max_days_diff=max_days_diff,
                          year=year)
        self.assertEqual(r_tzs, list())

        # Test 9-hour availability. Worker begins 10:00 ends 19:00
        # When UTC-4 - UTC 14:00 - 23:00 - allowed -6, -5
        # When UTC-5 - UTC 15:00 - 00:00 - allowed -7, -6
        # Allowed: -6, -5 aligned as above
        # Now also allowed: -6, -5 not aligned
        #   -7, -6 aligned
        #   -6, -6
        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=9, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)  # -6, -5 w/ aligned DST
        self.assertTrue('America/Ojinaga' in r_tzs)  # -7, -6 w/ aligned DST
        self.assertTrue('America/Managua' in r_tzs)  # -6, 6 w/o DST
        self.assertTrue('America/Mexico_City' in r_tzs)  # -6, -5 w/ unaligned DST
        self.assertFalse('America/Hermosillo' in r_tzs)  # -7, -7 out of range
        self.assertFalse('America/Chihuahua' in r_tzs)  # -7, -6 w/ unaligned DST

        # Test 10-hour availability
        # Add: -7, -6 not aligned, -8, -7 aligned, -7, -7
        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=10, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)  # -6, -5 w/ aligned DST
        self.assertTrue('America/Hermosillo' in r_tzs)  # -7, -7
        self.assertTrue('America/Chihuahua' in r_tzs)  # -7, -6 w/ unaligned DST
        self.assertTrue('America/Los_Angeles' in r_tzs)  # -8, -7 w/ aligned DST
        self.assertFalse('Pacific/Pitcairn' in r_tzs)  # -8, -8
        # No examples of -8, -7 unaligned because Baja

        # Test 12-hour availability
        # Add -8, -7 not aligned (n/a), -9, -8 not aligned (n/a)
        #   -9, -8 aligned, -10, -9 aligned,
        #   -8, -8, -9, -9
        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=12, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('America/Anchorage' in r_tzs)  # -9, -8 aligned
        self.assertTrue('America/Adak' in r_tzs)  # -10, -9 aligned
        self.assertTrue('Pacific/Pitcairn' in r_tzs)  # -8, -8
        self.assertTrue('Pacific/Gambier' in r_tzs)  # -9, -9
        self.assertFalse('Pacific/Marquesas' in r_tzs)  # -9:30, -9:30
        self.assertFalse('Pacific/Honolulu' in r_tzs)  # -10, -10

        # Test 14-hour availability
        # Add -10, -9 not aligned (n/a), -11, -10 not aligned (n/a),
        #       = +13, +14 not aligned
        #   -11, -10 aligned (n/a), -12, -11 aligned (n/a),
        #       = +13, +14 aligned (n/a), +12, +13 aligned (n/a)),
        #   -10, -10, -11, -11
        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=14, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('Pacific/Marquesas' in r_tzs)  # -9:30, -9:30
        self.assertTrue('Pacific/Honolulu' in r_tzs)  # -10, -10
        self.assertTrue('Pacific/Pago_Pago' in r_tzs)  # -11, -11
        self.assertFalse('Pacific/Chatham' in r_tzs)  # +12:45, +13:45 unaligned
        self.assertFalse('Pacific/Nauru' in r_tzs)  # 12, 12
        self.assertFalse('Pacific/Auckland' in r_tzs)  # +12, +13 unaligned

        # Test 16-hour availability
        # Add -12, -11 not aligned, +11, +12 not aligned,
        #       = +12, +13 not aligned
        #   12, 12, +11, +11
        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=16, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('Pacific/Chatham' in r_tzs)  # +12:45, +13:45 unaligned
        self.assertTrue('Pacific/Nauru' in r_tzs)  # 12, 12
        self.assertTrue('Pacific/Auckland' in r_tzs)  # +12, +13 unaligned
        self.assertTrue('Pacific/Bougainville' in r_tzs)  # 11, 11
        self.assertTrue('Pacific/Norfolk' in r_tzs)  # +11, +12 unaligned
        self.assertFalse('Pacific/Chuuk' in r_tzs)  # 10, 10
        self.assertFalse('Australia/Darwin' in r_tzs)  # 9:30, 9:30
        self.assertFalse('Asia/Seoul' in r_tzs)  # 9, 9
        self.assertFalse('Australia/Sydney' in r_tzs)  # +10, +11 unaligned

        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=18, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('Pacific/Chuuk' in r_tzs)  # 10, 10
        self.assertTrue('Australia/Darwin' in r_tzs)  # 9:30, 9:30
        self.assertTrue('Asia/Seoul' in r_tzs)  # 9, 9
        self.assertTrue('Australia/Sydney' in r_tzs)  # +10, +11 unaligned
        # No +9, +10 unaligned
        self.assertFalse('Asia/Singapore' in r_tzs)  # 8, 8
        self.assertFalse('Asia/Ho_Chi_Minh' in r_tzs)  # 7, 7
        # No 8, 9, no 7, 8

        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=20, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        # No +9, +10 unaligned
        self.assertTrue('Asia/Singapore' in r_tzs)  # 8, 8
        self.assertTrue('Asia/Ho_Chi_Minh' in r_tzs)  # 7, 7
        # No 8, 9, no 7, 8
        self.assertFalse('Asia/Yangon' in r_tzs)  # 6:30, 6:30
        self.assertFalse('Asia/Dhaka' in r_tzs)  # 6, 6
        self.assertFalse('Asia/Kathmandu' in r_tzs)  # 5:45, 5:45
        self.assertFalse('Asia/Kolkata' in r_tzs)  # 5:30, 5:30
        self.assertFalse('Asia/Ashgabat' in r_tzs)  # 5, 5
        # No 5, 6 or 6, 7

        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=22, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('Asia/Yangon' in r_tzs)  # 6:30, 6:30
        self.assertTrue('Asia/Dhaka' in r_tzs)  # 6, 6
        self.assertTrue('Asia/Kathmandu' in r_tzs)  # 5:45, 5:45
        self.assertTrue('Asia/Kolkata' in r_tzs)  # 5:30, 5:30
        self.assertTrue('Asia/Ashgabat' in r_tzs)  # 5, 5
        self.assertFalse('Asia/Kabul' in r_tzs)  # 4:30, 4:30
        self.assertFalse('Asia/Dubai' in r_tzs)  # 4, 4
        self.assertFalse('Asia/Tehran' in r_tzs)  # 3:30, 4:30 unaligned
        self.assertFalse('Africa/Addis_Ababa' in r_tzs)  # 3, 3

        # 1 hour not working period 9:00 to 10:00 is
        # 13:00 to 14:00 UTC or 14:00 to 15:00 UTC
        # and excludes any TZ where that's within 9:00 - 17:00
        # Still 16:00 - 17:00 missing in +3, 16:30-17:00 in +3:30.
        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=23, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('Asia/Yangon' in r_tzs)  # 6:30, 6:30
        self.assertTrue('Asia/Dhaka' in r_tzs)  # 6, 6
        self.assertTrue('Asia/Kathmandu' in r_tzs)  # 5:45, 5:45
        self.assertTrue('Asia/Kolkata' in r_tzs)  # 5:30, 5:30
        self.assertTrue('Asia/Ashgabat' in r_tzs)  # 5, 5
        self.assertTrue('Asia/Kabul' in r_tzs)  # 4:30, 4:30
        self.assertTrue('Asia/Dubai' in r_tzs)  # 4, 4
        self.assertFalse('Asia/Tehran' in r_tzs)  # 3:30, 4:30 unaligned
        self.assertFalse('Africa/Addis_Ababa' in r_tzs)  # 3, 3

        r_tzs = get_r_tzs(zone_transitions, w_tz,
                          w_start_hr=10, w_length_hrs=24, max_days_diff=max_days_diff,
                          year=year)
        self.assertTrue('America/Chicago' in r_tzs)
        self.assertTrue('Africa/Addis_Ababa' in r_tzs)
        self.assertTrue('Europe/London' in r_tzs)
        self.assertTrue('America/St_Johns' in r_tzs)


class TestRemoteDayInWorkerDay(unittest.TestCase):
    def test_remote_day_within_worker_day(self):
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        w_tz = 'Australia/Sydney'
        r_tz = 'Europe/Paris'
        w_zone_transitions = get_worker_zone_transitions(zone_transitions, w_tz, year)
        test_dates = get_test_dates(w_tz, r_tz, year, zone_transitions,
                                    w_zone_transitions)
        w_bounds = configure_starts_ends(w_tz, r_tz,
                                         year, 8, 0, timedelta(seconds=8 * 3600), 8, 0,
                                         timedelta(seconds=8 * 3600), test_dates)
        for b in remote_day_within_worker_day(w_bounds):
            print(b)

class TestGetRemoteTZs(unittest.TestCase):
    def test_equal_maps(self):
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        self.assertEqual(get_r_tzs(zone_transitions, tz='America/New_York',
            w_start_hr=9), get_r_tzs(zone_transitions, tz='America/Chicago',
                w_start_hr=8))
        self.assertEqual(get_r_tzs(zone_transitions, tz='Europe/Berlin',
            w_start_hr=9), get_r_tzs(zone_transitions, tz='Europe/London',
                w_start_hr=8))
        self.assertEqual(get_r_tzs(zone_transitions, tz='Europe/Moscow',
            w_start_hr=9), get_r_tzs(zone_transitions, tz='Australia/Darwin',
                w_start_hr=15, w_start_min=30))
        self.assertEqual(get_r_tzs(zone_transitions, tz='Africa/Nairobi',
            w_start_hr=9), get_r_tzs(zone_transitions, tz='Pacific/Kiritimati',
                w_start_hr=20), get_r_tzs(zone_transitions, tz='Pacific/Honolulu',
                w_start_hr=20))
        
        # Different DST dates will cause different lists
        self.assertNotEqual(get_r_tzs(zone_transitions, tz='America/New_York',
            w_start_hr=9), get_r_tzs(zone_transitions, tz='Europe/London',
                w_start_hr=14))
        self.assertNotEqual(get_r_tzs(zone_transitions, tz='Asia/Hebron',
            w_start_hr=9), get_r_tzs(zone_transitions, tz='Asia/Jerusalem',
                w_start_hr=9))

        # Are times within fifteen-minute periods the same?
        all_tzs = list(available_timezones())
        half_offset_tzs = []
        for tz in all_tzs:
            dt = datetime(2021, 1, 1, 0, tzinfo=ZoneInfo(tz))
            offset = dt.tzinfo.utcoffset(dt).days * 24.0 + dt.tzinfo.utcoffset(dt).seconds / 3600
            if not offset.is_integer():
                half_offset_tzs.append(tz)
        for j in range(1):
            tz = random.choice(all_tzs)
            print(tz)
            fifteen_minutes_1 = [get_r_tzs(zone_transitions, tz=tz,
                w_start_hr = 9, w_start_min = minute) for minute in range(1, 15)]
            fifteen_minutes_2 = [get_r_tzs(zone_transitions, tz=tz,
                w_start_hr = 9, w_start_min = minute) for minute in range(16, 30)]
            fifteen_minutes_3 = [get_r_tzs(zone_transitions, tz=tz,
                w_start_hr = 9, w_start_min = minute) for minute in range(31, 45)]
            fifteen_minutes_4 = [get_r_tzs(zone_transitions, tz=tz,
                w_start_hr = 9, w_start_min = minute) for minute in range(46, 60)]
            for i in range(1):
                self.assertEqual(fifteen_minutes_1[0], random.choice(fifteen_minutes_1))
                self.assertEqual(fifteen_minutes_2[0], random.choice(fifteen_minutes_2))
                self.assertEqual(fifteen_minutes_3[0], random.choice(fifteen_minutes_3))
                self.assertEqual(fifteen_minutes_4[0], random.choice(fifteen_minutes_4))

    def test_non_dst_offset_shifts(self):
        non_dst_repr_tzs = ['Etc/GMT+12',
                            'Etc/GMT+11',
                            'Pacific/Honolulu',
                            'Pacific/Marquesas',
                            'Etc/GMT+9',
                            'Pacific/Pitcairn',
                            'Canada/Yukon',
                            'America/Costa_Rica',
                            'America/Atikokan',
                            'America/St_Barthelemy',
                            'America/Argentina/Cordoba',
                            'America/Noronha',
                            'Atlantic/Cape_Verde',
                            'America/Danmarkshavn',
                            'Africa/Malabo', 
                            'Africa/Johannesburg',
                            'Europe/Kirov',
                            'Asia/Dubai',
                            'Asia/Kabul',
                            'Asia/Ashkhabad',
                            'Asia/Colombo',
                            'Asia/Kathmandu',
                            'Asia/Omsk',
                            'Indian/Cocos',
                            'Antarctica/Davis',
                            'Asia/Choibalsan',
                            'Australia/Eucla',
                            'Asia/Khandyga',
                            'Australia/North',
                            'Australia/Lindeman',
                            'Etc/GMT-11',
                            'Pacific/Funafuti',
                            'Pacific/Fakaofo',
                            'Pacific/Kiritimati']
        # Pacific/Fakaofo +13 should equal Etc/GMT+11 -11 in our system b/c don't care about day of wee
        # Same for Pacific/Funafuti +12 and Etc/GMT+12 -12
        # Same for Pacific/Honolulu -10 and Pacific/Kiritimati +14

    def test_usa_canada_offset_shifts(self):
        zt = get_zone_transitions_dict(2021)
        n_amer_tzs = ['America/Adak',
                      'America/Nome',
                      'US/Pacific',
                      'US/Mountain',
                      'America/Chicago',
                      'America/Detroit',
                      'America/Glace_Bay',
                      'America/Miquelon',
                      'America/St_Johns']
        cuba = 'America/Havana'
        count = 0
        while count < 7:
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=1))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=15))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=16))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=30))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=31))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=45))
            self.assertEqual(get_r_tzs(zt, tz=n_amer_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=n_amer_tzs[count + 1], w_start_hr=count+1,
                             w_start_min=54))
            count = count + 1

        self.assertEqual(get_r_tzs(zt, tz='America/Miquelon', w_start_hr=9,
            w_start_min=30), get_r_tzs(zt, tz='America/St_Johns', w_start_hr=9))
        self.assertNotEqual(get_r_tzs(zt, tz='America/Chicago', w_start_hr=4, r_start_hr=0, w_length_hrs=11),
                get_r_tzs(zt, tz='America/Adak', w_start_hr=0, r_start_hr=0, w_length_hrs=11))
    
    def test_europe_offset_shifts(self):
        zt = get_zone_transitions_dict(2021)
        # And see if different hours affect and make separated
        europe_tzs = ['America/Nuuk',
                      'Atlantic/Azores',
                      'Europe/Guernsey',
                      'Europe/Berlin',
                      'Europe/Nicosia']
        count = 0
        while count < 4:
            self.assertEqual(get_r_tzs(zt, tz=europe_tzs[count], w_start_hr=count),
                             get_r_tzs(zt, tz=europe_tzs[count + 1], w_start_hr=count+1))
            # Shift overnight won't work because DST shifts uncoord
            self.assertEqual(get_r_tzs(zt, tz=europe_tzs[count], w_start_hr=count, r_start_hr=0),
                    get_r_tzs(zt, tz=europe_tzs[count], w_start_hr=count, r_start_hr = 0)) 
        beirut = 'Asia/Beirut'
        troll = 'Antarctica/Troll' # Weird 2 hour forward in winter shift?
        chisinau = 'Europe/Chisinau' # Off from Europe same time shift (at different local times), by 1 hour
        # similar effect with Jordan/Syria 
        # and NZ/SouthPole 1 hour from Chatham, not 45 minutes


    def test_w_availability_less_than_shift_length(self):
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        self.assertEqual(get_r_tzs(zone_transitions,
                                   r_length_hrs=8, w_length_hrs=7), list())

    def test_w_availability_24_hrs(self):
        year = 2021
        zone_transitions = get_zone_transitions_dict(year)
        self.assertEqual(get_r_tzs(zone_transitions,
                                   w_length_hrs=24), all_tzs)
"""
if __name__ == "__main__":
    unittest.main()
