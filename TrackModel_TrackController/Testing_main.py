import sys
import importlib.util
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QCheckBox, QHeaderView, QComboBox, QScrollArea, QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from wayside import WAYSIDE

import TrackController 
import TrackModelBackend
#import TrackModelUI
import testbench
import Track_Model_GUI
import testbench_track_controller


class CTC:
    def __init__(self):
        self.maintenance = [False] * 150  # Maintenance status for all blocks
        self.block_authority = [0b0000001010] * 150  # Example: block authority values
        self.track_controller = None  # Will be set later

    def set_track_controller(self, track_controller):
        self.track_controller = track_controller

    def get_maintenance_status(self):
        return self.maintenance

    def get_block_authority(self):
        return self.block_authority

class TrainModel:
    def __init__(self):
        self.block_occupancy = [False] * 150  # Maintenance status for all blocks

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create instances of CTC, TrackModel, and TrackController
    ctc = CTC()
    track_model = TrackModelBackend.TrackModelBackend()
    train_model = TrainModel()

    track_controller = TrackController.TrackController()
    
    # Wire the dependencies together
    ctc.set_track_controller(track_controller)
    track_controller.set_ctc(ctc)
    track_controller.set_track_model(track_model)
    track_model.set_track_controller(track_controller)
    track_model.set_train_model(train_model)

    # Show the TrackController UI
    track_controller.show()
    track_model.gui.show()
    
    # Show the Test Bench UI

    test_bench = testbench_track_controller.TestBench(ctc, track_model)
    test_bench.show()

    # Create a QTimer to update track controller and model continuously
    update_timer = QTimer()
    update_timer.timeout.connect(track_controller.update)
    update_timer.start(1000)  # Update every 100 ms (adjust as needed)

    # Start the application loop
    sys.exit(app.exec())


