import unittest
from rz import *
from admin import *
import random

all_tzs = available_timezones()
zt_d = get_zone_transitions_dict(2021)
all_to_repr_tz_d, repr_tz_d = get_representative_tz_dicts(2021)
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

class TestLookup(unittest.TestCase):
    # Non-DST time zones only

    zt_d = get_zone_transitions_dict(2021)

    def test_start_times_shifted_by_utc_offset(self):
        self.maxDiff = None
        utc_results = lookup(zt_d)['remote tzs']
        plus_4_results = lookup(zt_d, worker_tz='Asia/Dubai', 
                                    w_start_hr=21,
                                    w_end_hr=10)['remote tzs']
        plus_5_75_results = lookup(zt_d, worker_tz='Asia/Kathmandu',
                                       w_start_hr=22,
                                       w_start_min=45,
                                       w_end_hr=11,
                                       w_end_min=45)['remote tzs']
        minus_9_5_results = lookup(zt_d, worker_tz='Pacific/Marquesas',
                                       w_start_hr=7,
                                       w_start_min=30,
                                       w_end_hr=20,
                                       w_end_min=30)['remote tzs']
        plus_14_results = lookup(zt_d, worker_tz='Pacific/Kiritimati',
                                     w_start_hr=7,
                                     w_start_min=0,
                                     w_end_hr=20,
                                     w_end_min=0)['remote tzs']
        minus_10_results = lookup(zt_d, worker_tz='Pacific/Honolulu',
                                      w_start_hr=7,
                                      w_start_min=0,
                                      w_end_hr=20,
                                      w_end_min=0)['remote tzs']
        self.assertEqual(utc_results, plus_4_results)
        self.assertEqual(utc_results, plus_5_75_results)
        self.assertEqual(utc_results, minus_9_5_results)
        self.assertEqual(utc_results, plus_14_results)
        self.assertEqual(utc_results, minus_10_results)

    def test_off_hour_start_times_shifted_by_utc_offset(self):
        self.maxDiff = None
        utc_results_off_hour = lookup(zt_d, w_start_min=30)['remote tzs']
        plus_4_results_off_hour = lookup(zt_d, 
                worker_tz='Asia/Dubai',
                w_start_hr=21,
                w_start_min=30,
                w_end_hr=10)['remote tzs']
        plus_5_75_results_off_hour = lookup(zt_d, 
                worker_tz='Asia/Kathmandu',
                w_start_hr=23,
                w_start_min=15,
                w_end_hr=11,
                w_end_min=45)['remote tzs']
        minus_9_5_results_off_hour = lookup(zt_d, 
                worker_tz='Pacific/Marquesas',
                w_start_hr=8,
                w_start_min=0,
                w_end_hr=20,
                w_end_min=30)['remote tzs']
        self.assertEqual(utc_results_off_hour, plus_4_results_off_hour)
        self.assertEqual(utc_results_off_hour, plus_5_75_results_off_hour)
        self.assertEqual(utc_results_off_hour, minus_9_5_results_off_hour)

    def test_non_overlapping_dst_removal(self):
        
        def get_only_tz_name(in_tuple):
            return tuple(t[0] for t in in_tuple)
        self.maxDiff = None

        zt_d = get_zone_transitions_dict(2021)

        # 8 hour shift in New York (regular remote shift) from 17 to 1 has no 
        #   remote tzs. Potential match 'Pacific/Norfolk' is in +11/+12 but 
        #   has misaligned DST.
        r_tz_d = lookup(zt_d, worker_tz='America/New_York', w_start_hr=17, w_end_hr=1)
        self.assertEqual(tuple(), r_tz_d['remote tzs'])
        self.assertTrue(all_to_repr_tz_d['Pacific/Norfolk'] 
                        in get_only_tz_name(r_tz_d['failed']))
        # 8 hour shift in New York (regular remote shift) from 16 to 0 has no 
        #   remote tzs. Potential match 'Pacific/Auckland' is in +12/+13 but 
        #   has misaligned DST.
        r_tz_d = lookup(zt_d, worker_tz='America/New_York', w_start_hr=16, w_end_hr=0)
        self.assertEqual(tuple(), r_tz_d['remote tzs'])
        self.assertTrue(all_to_repr_tz_d['Pacific/Auckland']
                        in get_only_tz_name(r_tz_d['failed']))
        # 8 hour shift in New York (regular remote shift) from 15 to 23 has no 
        #   remote tzs. Potential match 'Pacific/Apia' is in +13/+14 but 
        #   has misaligned DST.
        r_tz_d = lookup(zt_d, worker_tz='America/New_York', w_start_hr=15, w_end_hr=23)
        self.assertEqual(tuple(), r_tz_d['remote tzs'])
        self.assertTrue(all_to_repr_tz_d['Pacific/Apia'] 
                        in get_only_tz_name(r_tz_d['failed']))
        # Because North America shifts in successive hours at the same local time 
        # rather than at the same UTC time, North American time zones are near-misses
        r_tz_d = lookup(zt_d, worker_tz='America/Yellowknife', w_start_hr=7, w_end_hr=15)
        self.assertTrue(all_to_repr_tz_d['America/Detroit']
                        in get_only_tz_name(r_tz_d['failed but within hours']))
        # Same occurs between otherwise coordinated DST Europe and Moldova
        r_tz_d = lookup(zt_d, worker_tz='Europe/Bucharest', w_start_hr=9, w_end_hr=17)
        self.assertTrue(all_to_repr_tz_d['Europe/Tiraspol']
                        in get_only_tz_name(r_tz_d['failed but within hours']))
        self.assertTrue(all_to_repr_tz_d['Europe/Kiev']
                        in get_only_tz_name(r_tz_d['remote tzs']))
        # The Levant is mostly coordinated with Europe, except Lebanon 
        # goes at 00:00 local time rather than 02:00 UTC (04:00 local)
        self.assertTrue(all_to_repr_tz_d['Asia/Beirut']
                        in get_only_tz_name(r_tz_d['failed but within hours']))
        # and other Levantine countries use local definitions of the weekend
        self.assertTrue(all_to_repr_tz_d['Asia/Damascus']
                        in get_only_tz_name(r_tz_d['failed but within a week']))
        self.assertTrue(all_to_repr_tz_d['Asia/Hebron']
                        in get_only_tz_name(r_tz_d['failed but within a week']))
        self.assertTrue(all_to_repr_tz_d['Asia/Jerusalem']
                        in get_only_tz_name(r_tz_d['failed but within a week']))
        self.assertTrue(all_to_repr_tz_d['Asia/Amman']
                        in get_only_tz_name(r_tz_d['failed but within a week']))
        # Other DST time zones are distant enough to have to take weeks off for 
        # remote work to function, or be willing to be flexible an hour during 
        # these times - like Mexico within 20km of US and Mexico not
        r_tz_d = lookup(zt_d, worker_tz='America/Ojinaga', w_start_hr=9, w_end_hr=17)
        self.assertTrue(all_to_repr_tz_d['America/Mazatlan']
                        in get_only_tz_name(r_tz_d['failed but within weeks']))
        # Or between North America and Europe (here represented by Greenland)
        r_tz_d = lookup(zt_d, worker_tz='America/Ojinaga', w_start_hr=3, w_end_hr=11)
        self.assertTrue(all_to_repr_tz_d['America/Scoresbysund']
                        in get_only_tz_name(r_tz_d['failed but within weeks']))
        
        
        # Pacific/Auckland and Pacific/Apia are in the same DST shift set:
        # 8 hour shift for worker in Samoa working remotely at South Pole (NZ
        #   time) has a match one hour behind
        r_tz_d = lookup(zt_d, worker_tz='Pacific/Apia', w_start_hr=10, w_end_hr=18)
        self.assertTrue(all_to_repr_tz_d['Antarctica/South_Pole'] 
                        in get_only_tz_name(r_tz_d['remote tzs']))
        # Same UTC time in Chile also 
        r_tz_d = lookup(zt_d, worker_tz='America/Santiago', w_start_hr=11, w_end_hr=19)
        self.assertTrue(all_to_repr_tz_d['Pacific/Easter'] 
                        in get_only_tz_name(r_tz_d['remote tzs']))




if __name__ == "__main__":
    unittest.main()
