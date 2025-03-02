import unittest
import os
from schedule_loader import ScheduleLoader
from track_loader import load_track_layout


class TestScheduleLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        track_file = os.path.join(current_dir, "Track_Layout.xlsx")
        schedule_file = os.path.join(current_dir, "Train_Scheduling.xlsx")

        cls.track_layout = load_track_layout(track_file)
        cls.loader = ScheduleLoader(cls.track_layout)
        cls.schedules = cls.loader.load_from_excel(schedule_file)

    def test_red_line_schedules(self):
        red_schedules = self.schedules['Red Line']
        self.assertGreater(len(red_schedules), 0, "No Red Line data loaded")

        sched = red_schedules[0]
        self.assertEqual(sched.line, 'Red Line')
        self.assertEqual(sched.train_id, 1)
        self.assertEqual(len(sched.stops), 3)
        self.assertEqual(sched.stops[0]['block'], 7)  # E.g. SHADYSIDE

    def test_green_line_schedules(self):
        green_schedules = self.schedules['Green Line']
        self.assertGreater(len(green_schedules), 0, "No Green Line data loaded")

        sched = green_schedules[0]
        self.assertEqual(sched.line, 'Green Line')
        self.assertEqual(sched.train_id, 101)
        self.assertEqual(sched.stops[0]['block'], 2)  # e.g. PIONEER

    def test_invalid_ids(self):
        with self.assertRaises(ValueError):
            invalid_row = {
                'Train ID': 'A123',
                'Stops': 'SHADYSIDE',
                'expected_arrival_times': '08:00'
            }
            self.loader._process_row(invalid_row, 'Red Line')


if __name__ == '__main__':
    unittest.main()
