import sys
from PyQt6.QtWidgets import QApplication
from track_loader import load_track_layout
from schedule_loader import ScheduleLoader
from ctc import CTC
from ctc_office import CTCOffice
from CTC_GUI import CTCGUI
from TrackController import TrackController
import testbench_track_controller
from PyQt6.QtCore import QTimer

class TrackModel:
    def __init__(self):
        self.occupancy_status = [False] * 150  # Occupancy status for all blocks
        self.track_controller = None  # Will be set later

    def set_track_controller(self, track_controller):
        self.track_controller = track_controller
    
    def set_ctc(self, ctc):
        self.track_controller = ctc

    def get_block_occupancy(self):
        return self.block_occupancy



if __name__ == "__main__":
    app = QApplication(sys.argv)

    track_layout = load_track_layout("track_layout.xlsx")
    schedule_loader = ScheduleLoader(track_layout)
    schedules = schedule_loader.load_from_excel("Train_Scheduling.xlsx")


    ctc = CTC()
    ctc_office = CTCOffice(track_layout, schedules)
    track_model = TrackModel()
    track_controller = TrackController()

    ctc_office.set_ctc(ctc)

    # Wire the dependencies together for CTC
    ctc.connect_track_controller(track_controller)
    track_model.set_track_controller(track_controller)
    
    # Wire the dependencies together for TC
    track_controller.set_ctc(ctc)
    track_controller.set_track_model(track_model)

    # Show the TrackController UI
    track_controller.show()
    track_controller.update()

    # Show the Test Bench UI
    test_bench = testbench_track_controller.TestBench(ctc, track_model)
    test_bench.show()
    
    ctc_gui = CTCGUI(ctc=ctc, ctc_office=ctc_office,
                     track_layout=track_layout,
                     schedule_loader=schedule_loader,
                     track_controller=track_controller)
    ctc_gui.show()

    update_timer = QTimer()
    update_timer.timeout.connect(track_controller.update)
    update_timer.timeout.connect(ctc_gui.update_all)
    update_timer.start(1000)  # Update every 100 ms (adjust as needed)

    # Start the application loop
    sys.exit(app.exec())