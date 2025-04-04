import sys
from PyQt6.QtWidgets import QApplication
from track_loader import load_track_layout
from schedule_loader import ScheduleLoader
from ctc import CTC
from ctc_office import CTCOffice
from CTC_GUI import CTCGUI
from track_controller.TrackController import TrackController
import track_controller.testbench_track_controller as testbench_track_controller
from PyQt6.QtCore import QTimer

class TrackModel:
    def __init__(self):
        self.occupancy_status = [False] * 150
        self.track_controller = None

    def set_track_controller(self, track_controller):
        self.track_controller = track_controller

    def set_ctc(self, ctc):
        self.track_controller = ctc

    def get_block_occupancy(self):
        return self.occupancy_status

if __name__ == "__main__":
    app = QApplication(sys.argv)

    track_layout = load_track_layout("Systems-Engineering-ECE1140/full_integration/Track_and_train/track_layout.xlsx")
    schedule_loader = ScheduleLoader(track_layout)
    schedules = schedule_loader.load_from_excel("Systems-Engineering-ECE1140/full_integration/Track_and_train/Train_Scheduling.xlsx")

    ctc = CTC()
    ctc_office = CTCOffice(track_layout, schedules)
    track_model = TrackModel()
    track_controller = TrackController()

    ctc_office.set_ctc(ctc)

    # wire dependencies together for CTC
    ctc.connect_track_controller(track_controller)
    track_model.set_track_controller(track_controller)

    # Wire dependencies together for TC
    track_controller.set_ctc(ctc)
    track_controller.set_track_model(track_model)
 
    #show the TC UI
    track_controller.show()
    track_controller.update()

    #show testbench UI
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
    update_timer.start(1000)

    sys.exit(app.exec())
