import sys
import importlib.util
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel



class TrackModelBackend:
    def __init__(self, block_auth = 0, beacon_signal = "0000", block_vector = [], grade_vector = [],):
        """Initialize Track Model Backend with connections to other models."""
        self.ready = False  # Indicates if the backend is ready

        self.blocks = {}  # Stores track block data
        self.occupancy_status = [False]*150  # Block occupancy states
        self.block_authority = [] # 10-bit block authority as string
        self.failure_status = []  # Track circuit failure status
        self.block_auth = block_auth  # Block authority value
        self.beacon_signal = beacon_signal  # Beacon signal value
        self.block_vector = block_vector  # Block vector value
        self.grade_vector = grade_vector  # Grade vector value


    
    def get_block_authority(self, block_id):
        return self.block_auth

    def update_block_occupancy(self, block_num_begin, block_num_middle, block_num_end, occupied = True):
        print(f"Updating occupancy for blocks {block_num_begin}, {block_num_middle}, {block_num_end} to {occupied}")

    def get_beacon_from_block(self, block_num):
        return self.beacon_signal
    
    def get_block_vector_from_block(self, block_num):
        return self.block_vector
    
    def get_grade_from_block(self, block_num):
        """Return the grade vector for a specific block."""
        if block_num in self.blocks:
            return self.blocks[block_num]["grade_vector"]
        return None

    def station_stop(self, block, number_of_passengers_on_train, max_num_passengers):
        #shouldn't be just four needs to have some type of number of passengers on the block
        passengers_on_block = 4
        new_number_of_passengers_on_train += passengers_on_block
        if new_number_of_passengers_on_train > max_num_passengers:
            # If the number of passengers exceeds the maximum, set it to the maximum
            passengers_getting_off = new_number_of_passengers_on_train - max_num_passengers
        new_number_of_passengers_on_train = min(new_number_of_passengers_on_train, max_num_passengers)

        return new_number_of_passengers_on_train


def test_4():
    train = TrainModel()
    train.beacon_parse("00100011001000011001000001100100000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000100101100010010110001001011000100101100010010110001001011000100101100010010110001001011000001100100000101011010011001000001001011000100101100010010110001001011000100101100010010110001001011000100101100010010110001001011000100101100010010110100101100010010110001001011000100101100010010110001001011000100101100010010110001001011000000100011000110010000011001000001010000000110010000011001000001011010000110010000011001000001100100000110010000011001000001100100001010001000011001000001100100000011001000001100100000101000000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000101110000000101000000010001100001100100000110010000110010000110010000100101100010010110001001011000100101100001001011000100101100010010110001001011000100101100010010110001001011000100101100001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000010010110001001011000100101100010010110001001011000100101100010010110001001011001001011000100101100010010110001001011000011001000000110010000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100111111111101101101101101101101101101101111111111111111111111111111011011011011011011011011011011011011011011011111111111111111111111111111011100100100100100100100100100100100100100100100001001001001001010010010010010010010010010010010010010010010010010010010010010010010010010010010010010100100111111111111111111110110110110111111111111101101101101101101101101101101101101111111111111110110110110111111111111111111100100100100100100100100100100100100100100100100100100100100100100100100100100100100100100100000000000000000000000000011100000000000000000000000000000000000000011111111111111111110110000000000000000000000011110000000000000000000000000000000111011111111111111111101000000010001000000000010000000100000000000010000100000000100000000100000000100000000100000000000000010000010000001000000100001000001000000001000000010000000010000000010000001100000000000000000000000000000011000000000000001100000000000000000000000000000000000000000011000000000000000000000000000000110000000000000000000000000000000000000000000000000011000000000000000000110000000000000000000000000000000000110000000000000000000000000000000000110000000000000000000000000000000000110000000000000000000000000000000000110000000000000000000000000000000000000000000000000000000000000011000000000000000000000011000000000000000000000000001000000000000000000000000000010000000000000000001100000000000000000000001100000000000000000000000000000000001100000000000000000000000000000011000000000000000000000000000000000011000000000000000000000000000000000011", 
                       [0, 0, 0], [1,2,3])
    print(train.distance_vector)
    print(train.grade_vector)
    print(train.blocknumbervector)
    print("should have printed [all blocks of green line distances], [0,0,0,], [1,2,3]")
    print("this shows that an empty beacon does not get added")

def test_5():
    train = TrainModel()
    train.beacon_parse("0000", [0, 0, 0], [1,2,3])
    print(train.distance_vector)
    print(train.grade_vector)
    print(train.blocknumbervector)
    print("should have printed [], [0,0,0,], [1,2,3]")
    print("this shows that an empty beacon does not get added")

def test_6():
    train = TrainModel()
    train.beacon_parse("0000", [0, 0, 0], [])
    print(train.distance_vector)
    print(train.grade_vector)
    print(train.blocknumbervector)
    print("should have printed [], [0,0,0,], []")
    print("this shows that an empty block vector does not get added")

def test_7():
    train = TrainModel()
    train.beacon_parse("0000", [], [1,2,3])
    print(train.distance_vector)
    print(train.grade_vector)
    print(train.blocknumbervector)
    print("should have printed [], [], [1,2,3]")
    print("this shows that an empty grade vector does not get added")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    k_p = 2e5
    k_i = 2e4
    i = 0
    world_time = {'day': 0, 'hour': 0, 'min': 0}
    # --- Create core modules ---

    print("Test 1: TrainModel initialization")
    train = TrainModel()
    if train is None:
        print("TrainModel initialization failed.")
        sys.exit(1)
    print("TrainModel initialized successfully.")
    print("Test 2: TrainController initialization")
    train_con = train.train_controller
    if train_con is None:
        print("TrainController initialization failed.")
        sys.exit(1)
    print("TrainController initialized successfully.")
    
    print("Test 3: TrackModelBackend initialization")
    track = TrackModelBackend()
    train.add_classes(track)
    track_test = train.Track_model
    if track_test is None:
        print("TrackModelBackend initialization failed.")
        sys.exit(1)
    print("TrackModelBackend initialized successfully.")
    print("Test 4: Beacon signal parse")
    test_4()
    print("Test 5: Beacon signal parse with empty beacon")
    test_5()
    print("Test 6: Beacon signal parse with empty block vector")
    test_6()
    print("Test 7: Beacon signal parse with empty grade vector")
    test_7()


