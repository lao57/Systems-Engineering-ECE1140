import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from CTCOffice_UI import Ui_MainWindow
from ctc_office import CTCOffice
from ctc import CTC
from station_map import STATION_BLOCKS
from track_loader import load_track_layout
from schedule_loader import ScheduleLoader

class CTCGUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.ctc = CTC()
        self.track_layout = load_track_layout("track_layout.xlsx")
        self.schedule_loader = ScheduleLoader(self.track_layout)
        self.ctc_office = CTCOffice(self.track_layout, {'Green Line': [], 'Red Line': []})
        self.ctc_office.set_ctc(self.ctc)

        self.setup_connections()
        self.update_block_combobox()


        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self.update_all)
        self.ui_update_timer.start(1000)

    def setup_connections(self):
        self.btnUploadSchedule.clicked.connect(self.load_schedule)
        self.btnManualUpload.clicked.connect(self.load_schedule)
        self.btnCloseTrack.clicked.connect(lambda: self.set_maintenance(True))
        self.btnOpenTrack.clicked.connect(lambda: self.set_maintenance(False))
        self.maintLine.currentTextChanged.connect(self.update_block_combobox)
        self.comboBlockOccupancy.currentTextChanged.connect(self.update_block_occupancy_table)

    def load_schedule(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Schedule File", "", "Excel Files (*.xlsx)")
        if path:
            try:
                schedules = self.schedule_loader.load_from_excel(path)
                self.ctc_office.schedules = schedules

                for line in ['Green Line', 'Red Line']:
                    if line in schedules:
                        for idx in range(len(schedules[line])):
                            self.ctc_office.schedule_train(line, idx)
                self.update_all()
                QMessageBox.information(self, "Success", "Schedule loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load schedule: {str(e)}")

    def set_maintenance(self, closed: bool):
        line = self.maintLine.currentText().strip().title()
        block_text = self.maintBlock.currentText().replace("Block", "").strip()
        try:
            block = int(block_text)
        except ValueError:
            return
        idx = block - 1
        if 0 <= idx < 150:
            self.ctc.maintenance[idx] = closed
            self.ctc_office.update_maintenance(self.ctc.maintenance.copy())

    def update_block_combobox(self):
        line = self.maintLine.currentText().strip().title()
        blocks = [str(b['block_number']) for b in self.track_layout.get(line, [])]
        self.maintBlock.clear()
        self.maintBlock.addItems([f"Block {b}" for b in blocks[:6]])

    def update_all(self):
        self.ctc_office.update()
        self.update_train_table()
        self.update_block_occupancy_table()
        self.update_track_states()
        self.update_system_analysis()

    def update_train_table(self):
        trains = self.ctc_office.active_trains
        self.tableTrainMonitor.setRowCount(len(trains))
        for row, train in enumerate(trains):
            next_stop = None
            if train.next_stop_index < len(train.scheduled_stops):
                next_stop = train.scheduled_stops[train.next_stop_index]
            else:
                next_stop = "None"

            items = [
                QTableWidgetItem(str(train.train_id)),
                QTableWidgetItem("Green Line"),  # or read from schedule line
                QTableWidgetItem(str(train.current_block.block_number if train.current_block else "N/A")),
                QTableWidgetItem(f"{train.authority_meters:.1f} m"),
                QTableWidgetItem(self.get_station_name(next_stop) if isinstance(next_stop, int) else str(next_stop))
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableTrainMonitor.setItem(row, col, item)

    def get_station_name(self, block: int) -> str:
        return STATION_BLOCKS['BLOCK_TO_STATION'].get(block, f"Block {block}")

    def update_block_occupancy_table(self):
        line = self.comboBlockOccupancy.currentText().replace(" Occupancy", "").strip().title()
        blocks = self.track_layout.get(line, [])
        self.tableBlockOccupancy.setRowCount(len(blocks))
        for i, blk in enumerate(blocks):
            block_num = blk['block_number']
            self.tableBlockOccupancy.setItem(i, 0, QTableWidgetItem(str(block_num)))
            occ = self.ctc.block_occupancy[block_num - 1]
            status = "Occupied" if occ else "Unoccupied"
            item = QTableWidgetItem(status)
            if occ:
                item.setBackground(Qt.GlobalColor.red)
            else:
                item.setBackground(Qt.GlobalColor.green)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tableBlockOccupancy.setItem(i, 1, item)

    def update_track_states(self):

        mapping = [
            ("Crossing 1", self.ctc.crossing_states[0]),
            ("Crossing 2", self.ctc.crossing_states[1]),
            ("Switch 1", self.ctc.switch_states[0]),
            ("Light 1", self.ctc.light_states[0]),
            ("Switch 2", self.ctc.switch_states[1]),
            ("Light 2", self.ctc.light_states[1]),
            ("Switch 3", self.ctc.switch_states[2]),
            ("Light 3", self.ctc.light_states[2]),
            ("Switch 4", self.ctc.switch_states[3]),
            ("Light 4", self.ctc.light_states[3]),
            ("Switch 5", self.ctc.switch_states[4]),
            ("Light 5", self.ctc.light_states[4]),
            ("Switch 6", self.ctc.switch_states[5]),
            ("Light 6", self.ctc.light_states[5])
        ]
        for row, (desc, state) in enumerate(mapping):
            item = QTableWidgetItem("Active" if state else "Inactive")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates.setItem(row, 0, item)

    def update_system_analysis(self):

        dummy_data = {
            0: ["100", "1", "1.0%"],   # Red
            1: ["120", "2", "1.6%"]    # Green
        }
        for row in range(2):
            for col in range(3):
                item = QTableWidgetItem(dummy_data[row][col])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableSystemAnalysis.setItem(row, col, item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CTCGUI()
    gui.show()
    sys.exit(app.exec())