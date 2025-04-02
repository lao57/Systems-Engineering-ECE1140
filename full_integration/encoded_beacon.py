import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QFileDialog

def encode_112bit(distance, speed_code, underground, at_station):
    """
    Encodes the following fields into an 11-bit core message:
      - distance: an integer (e.g. 50 for 50 meters) encoded in 6 bits.
      - speed_code: an integer (e.g. 5 for 40 km/hr) encoded in 3 bits.
      - underground: boolean (True -> '1', False -> '0').
      - at_station: boolean (True -> '1', False -> '0').

    The core message is 6 + 3 + 1 + 1 = 11 bits.
    To form a 112-bit core, the 11-bit core is repeated 10 times (110 bits)
    and the first 2 bits of the core are appended.
    """
    dist_bin = format(distance, "06b")
    speed_bin = format(speed_code, "03b")
    und_bin = "1" if underground else "0"
    station_bin = "1" if at_station else "0"
    core = dist_bin + speed_bin + und_bin + station_bin  # 11 bits
    full_repeats = 10
    remainder = 112 - full_repeats * len(core)  # should be 2
    final_core = core * full_repeats + core[:remainder]
    return final_core

class TrackModel:
    def __init__(self):
        self.blocks = {}  # Dictionary to store block information

    def add_block(self, block_number, beacon_signal="0000", grade=None, block_vector=None):
        self.blocks[block_number] = {
            'beacon_signal': beacon_signal,
            'grade': grade,
            'block_vector': block_vector,
            'baud_sig': None,
            'occupied': False
        }

    def get_beacon_from_block(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['beacon_signal'] is not None:
            return self.blocks[block_number]['beacon_signal']
        return None

    def get_grade_from_block(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['grade'] is not None:
            return self.blocks[block_number]['grade']
        return None

    def get_block_vector_from_block(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['block_vector'] is not None:
            return self.blocks[block_number]['block_vector']
        return None

    def set_baud_sig(self, block_number, baud_sig):
        if block_number in self.blocks:
            self.blocks[block_number]['baud_sig'] = baud_sig

    def display_track(self):
        for block in sorted(self.blocks.keys()):
            if self.blocks[block]['occupied']:
                print("[|^|]", end=" ")
            else:
                print("[|=|]", end=" ")
        print()

def main():
    app = QApplication(sys.argv)
    track_model = TrackModel()

    # Manually added Block 1
    track_model.add_block(
        1,
        '1000000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010010110110110110110110110110110100000000000000000NONENONENONENONENONEStaBStaBStaBStaBStaB',
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    )

    # Open a file dialog to select the Excel file containing the remaining block info.
    file_path, _ = QFileDialog.getOpenFileName(None, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
    if not file_path:
        print("No file selected.")
        sys.exit(0)

    try:
        df = pd.read_excel(file_path, sheet_name="Blue Line")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

    # Process each row in the Excel file to fill blocks 2 to 15.
    for index, row in df.iterrows():
        # Extract block number; default to row index+1.
        block_number = row.get("Block Number", index + 1)
        if int(block_number) == 1:
            continue  # Skip block 1; it's already added.

        # Extract parameters:
        distance = int(row.get("Block Length (m)", 50))
        speed_code = int(row.get("Speed limit", 5))
        underground_val = row.get("Underground", "No")
        if isinstance(underground_val, str):
            underground = underground_val.strip().lower() in ["yes", "true", "1"]
        else:
            underground = bool(underground_val)
        infrastructure = str(row.get("Infrastructure", ""))
        station_name = None
        if "station" in infrastructure.lower():
            temp = infrastructure.lower().replace("station", "").replace(":", "").strip()
            if temp:
                station_name = temp.upper()
        at_station = station_name is not None

        print(f"Block {block_number} Station Name: {station_name}")

        # Compute the 112-bit core from the parameters.
        beacon_core = encode_112bit(distance, speed_code, underground, at_station)
        # Append station text: if a station is present, repeat "Sta" plus station name 5 times; else, fixed "none" text.
        if at_station:
            station_text = ("Sta" + station_name) * 5
        else:
            station_text = "NONENONENONENONENONE"
        beacon = beacon_core + station_text

        # Optionally extract Grade and Block Vector from the Excel row.
        grade = row.get("Grade", None)
        block_vector_str = row.get("Block Vector", None)
        block_vector = None
        if block_vector_str is not None:
            try:
                block_vector = [int(x.strip()) for x in str(block_vector_str).split(",")]
            except Exception:
                block_vector = None

        # Add the block into the model.
        track_model.add_block(block_number, beacon, grade, block_vector)

    # Print out details for each block.
    for block in sorted(track_model.blocks.keys()):
        print(f"Block {block}:")
        print(f"  Beacon Signal: {track_model.get_beacon_from_block(block)}")
        print(f"  Grade: {track_model.get_grade_from_block(block)}")
        print(f"  Block Vector: {track_model.get_block_vector_from_block(block)}")
        print()

    # Display a simple occupancy visualization.
    track_model.display_track()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()