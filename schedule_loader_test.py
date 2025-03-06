import unittest
from datetime import datetime
from schedule_loader import ScheduleLoader, ScheduleEntry

class TestUndergroundStations(unittest.TestCase):
    def test_underground_stations(self):

        fake_track_layout = {
            'Green': [
                {'infrastructure': "STATION: INGLEWOOD;UNDERGROUND", 'block_number': 132},
                {'infrastructure': "UNDERGROUND", 'block_number': 133},
                {'infrastructure': "UNDERGROUND", 'block_number': 134},
                {'infrastructure': "STATION: CENTRAL;UNDERGROUND",  'block_number': 141},
                {'infrastructure': "UNDERGROUND", 'block_number': 142},
            ]
        }

        loader = ScheduleLoader(fake_track_layout)

        row = {
            'Train ID': 1,
            'Stops': 'INGLEWOOD, CENTRAL',
            'expected_arrival_times': '08:00, 08:10'
        }

        # Call the loader's parser directly.
        schedule_entry = loader._parse_row(row, 'Green Line')

        # Basic sanity checks
        self.assertIsInstance(schedule_entry, ScheduleEntry)
        self.assertEqual(schedule_entry.line, 'Green Line')
        self.assertEqual(schedule_entry.train_id, 1)
        self.assertEqual(len(schedule_entry.stops), 2)

        # Make sure it mapped 'INGLEWOOD' -> block 132, 'CENTRAL' -> block 141
        self.assertEqual(schedule_entry.stops[0]['block'], 132)
        self.assertEqual(schedule_entry.stops[1]['block'], 141)

        # Also check that the times were parsed correctly
        self.assertEqual(schedule_entry.stops[0]['time'], datetime.strptime('08:00', '%H:%M').time())
        self.assertEqual(schedule_entry.stops[1]['time'], datetime.strptime('08:10', '%H:%M').time())


if __name__ == '__main__':
    unittest.main()
