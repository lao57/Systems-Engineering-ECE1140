import sys
from PyQt6.QtWidgets import QApplication
from track_loader import load_track_layout
from schedule_loader import ScheduleLoader
from ctc import CTC
from ctc_office import CTCOffice
from CTC_GUI import CTCGUI
from TrackController import TrackController

#dummy model inplace of lamine
class DummyTrackModel:
    def __init__(self, ctc):
        self.ctc = ctc
    @property
    def occupancy_status(self):
        return self.ctc.get_block_occupancy()

def main():
    app = QApplication(sys.argv)


    track_layout = load_track_layout("track_layout.xlsx")
    schedule_loader = ScheduleLoader(track_layout)
    schedules = schedule_loader.load_from_excel("Train_Scheduling.xlsx")


    ctc = CTC()
    ctc_office = CTCOffice(track_layout, schedules)
    ctc_office.set_ctc(ctc)

    track_controller = TrackController()
    ctc.connect_track_controller(track_controller)
    track_controller.ctc = ctc

    if track_controller.track_model is None:
        track_controller.track_model = DummyTrackModel(ctc)


    ctc_gui = CTCGUI(ctc=ctc, ctc_office=ctc_office,
                     track_layout=track_layout,
                     schedule_loader=schedule_loader,
                     track_controller=track_controller)


    track_controller.show()
    ctc_gui.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
