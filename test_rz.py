import unittest
from rz import *
from admin import *
import random

all_tzs = available_timezones()
zt = get_zone_transitions_dict(2021)
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


class TestStandardTimeCalcFromUTC(unittest.TestCase):

    def test_standard_time_calculation_from_utc(self):
        with open('tz_data/standard_time_results_2021.json', 'r') as f:
            d = json.load(f)
        for k, v in d.items():
            offset, tz, w_start_hr, w_start_min, w_end_hr, w_end_min = k.split(' ')
            # +7 from 11 - 21 should have 4 not 3, should have 10 but not 10:30
            if all_to_repr_tz_d['Asia/Hovd'] == tz:
                if (w_start_hr == 11 and w_start_min == 0
                        and w_end_hr == 21 and w_end_min == 0):
                    self.assertTrue('Asia/Dubai' in v)
                    self.assertFalse('Africa/Johannesburg' in v)
                    self.assertTrue('Australia/Brisbane' in v)
                    self.assertFalse('Australia/Sydney' in v)
            # -5 from 17 to 6 should have +6 but not +5:45, +11 but not +12
            if all_to_repr_tz_d['America/Rio_Branco'] == tz:
                if (w_start_hr == 17 and w_start_min == 0
                        and w_end_hr == 6 and w_end_min == 0):
                    self.assertFalse('Antarctica/South_Pole' in v)
                    self.assertTrue('Asia/Sakhalin' in v)
                    self.assertTrue('Asia/Dhaka' in v)
                    self.assertFalse('Asia/Kathmandu' in v)


class TestTZByRange(unittest.TestCase):

    def test_utc(self):
        self.tz = 'UTC'

        def test_availability_too_short(self):
            start_hr = random.randint(0, 24)
            end_hr = start_hr + 7
            end_hr = end_hr if end_hr < 24 else end_hr - 24
            self.assertEqual(list(), calculate_remote_tzs(repr_tz_d,
                                                          worker_tz=self.tz,
                                                          w_start_hr=start_hr,
                                                          w_end_hr=end_hr))

        def test_24_hr_availability(self):
            start_hr = random.randint(0, 24)
            end_hr = start_hr
            self.assertEqual(list(repr_tz_d),
                             calculate_remote_tzs(repr_tz_d,
                                                  worker_tz=self.tz,
                                                  w_start_hr=start_hr,
                                                  w_end_hr=end_hr))

        def test_8_hr_worker(self):
            # Should be 8 to the east (17 - 9) and 16 to the west (17 - 1)  only.
            # Actually could be other direction. TODO SLEEP

            def configure_variables(start_hr, start_min, end_hr, end_min):
                remote_repr_tzs = calculate_remote_tzs(repr_tz_d,
                                                       worker_tz=self.tz,
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
            self.assertFalse('Australia/Lord_Howe' in remote_tzs)  # +10.5, +11

            remote_tzs = configure_variables(5, 0, 13, 0)
            self.assertFalse('Europe/Kirov' in remote_tzs)  # +3, +3
            self.assertFalse('Asia/Tehran' in remote_tzs)  # +3.5, 4.5
            self.assertTrue('Asia/Dubai' in remote_tzs)  # ==== +4
            self.assertFalse('Asia/Kabul' in remote_tzs)  # +4.5, +4.5
            self.assertFalse('Asia/Ashkhabad' in remote_tzs)  # +5, +5

            remote_tzs = configure_variables(11, 0, 19, 0)
            self.assertFalse('America/Sao_Paulo' in remote_tzs)  # -3 -3
            self.assertTrue('Atlantic/South_Georgia' in remote_tzs)  # -2, -2
            self.assertFalse('Atlantic/Azores' in remote_tzs)  # -1 -1

            remote_tzs = None

        test_availability_too_short(self)
        test_24_hr_availability(self)
        test_8_hr_worker(self)


if __name__ == "__main__":
    unittest.main()