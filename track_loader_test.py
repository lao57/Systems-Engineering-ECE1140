import unittest
import os
from pprint import pprint
from track_loader import load_track_layout

class TestTrackLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(current_dir, "Track_Layout.xlsx")
        cls.track_layout = load_track_layout(test_file)

    def test_data_loading(self):

        for line in ['Red Line', 'Green Line']:
            self.assertIn(line, self.track_layout)
            self.assertIsInstance(self.track_layout[line], list)
            self.assertGreater(len(self.track_layout[line]), 10, f"{line} has insufficient blocks")

    def test_sample_data_output(self):
      
        print("\n\nSample Red Line Blocks:")
        red_samples = [7, 16, 25]  # SHADYSIDE, HERRON AVE, PENN STATION
        for num in red_samples:
            block = next((b for b in self.track_layout['Red Line'] if b['block_number'] == num), None)
            self.assertIsNotNone(block)
            print(f"\nRed Line Block {num}:")
            pprint(block)
            print("-" * 60)

        print("\n\nSample Green Line Blocks:")
        green_samples = [2, 28, 57]  # PIONEER, SWITCH, OVERBROOK
        for num in green_samples:
            block = next((b for b in self.track_layout['Green Line'] if b['block_number'] == num), None)
            self.assertIsNotNone(block)
            print(f"\nGreen Line Block {num}:")
            pprint(block)
            print("-" * 60)

if __name__ == '__main__':
    unittest.main()