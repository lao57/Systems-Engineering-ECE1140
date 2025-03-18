import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from CTCOffice_UI import Ui_MainWindow
from ctcOfficeLinkedList import CTCOffice
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
        self.setup_tables()
        self.update_block_combobox()

        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_all)
        self.ui_update_timer.start(1000)

        QTimer.singleShot(1000, self.launch_track_controller_mock)

    def setup_connections(self):
        self.btnUploadSchedule.clicked.connect(self.load_schedule)
        self.btnOpenTrack.clicked.connect(lambda: self.set_maintenance(False))
        self.btnCloseTrack.clicked.connect(lambda: self.set_maintenance(True))
        self.maintLine.currentTextChanged.connect(self.update_block_combobox)
        self.comboBlockOccupancy.currentTextChanged.connect(self.update_block_occupancy_table)

    def setup_tables(self):
        self.tableTrainMonitor.setHorizontalHeaderLabels([
            "Train ID", "Current Block", "Authority", "Next Stop", "Line"
        ])
        self.tableBlockOccupancy.setHorizontalHeaderLabels(["Block", "Status"])
        self.TrackStates.setHorizontalHeaderLabels(["State"])

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

    def update_all(self):
        self.ctc_office.update()
        self.update_train_table()
        self.update_track_states()
        self.update_block_occupancy_table()

    def update_train_table(self):
        self.tableTrainMonitor.setRowCount(len(self.ctc_office.active_trains))
        for row, train in enumerate(self.ctc_office.active_trains):
            next_stop = (train.scheduled_stops[train.next_stop_index]
                         if train.next_stop_index < len(train.scheduled_stops)
                         else 58)

            items = [
                QTableWidgetItem(str(train.train_id)),
                QTableWidgetItem(str(train.route_blocks[train.current_block_index])),
                QTableWidgetItem(f"{train.authority_meters:.1f} m"),
                QTableWidgetItem(self.get_station_name(next_stop)),
                QTableWidgetItem("Green Line")
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableTrainMonitor.setItem(row, col, item)

    def get_station_name(self, block: int) -> str:
        return STATION_BLOCKS['BLOCK_TO_STATION'].get(block, f"Block {block}")

    def update_block_combobox(self):
        line = self.maintLine.currentText().strip().title()
        blocks = [str(blk['block_number']) for blk in self.track_layout.get(line, [])]
        self.maintBlock.clear()
        self.maintBlock.addItems(blocks[:6])

    def set_maintenance(self, closed: bool):
        line = self.maintLine.currentText().strip().title()
        block = int(self.maintBlock.currentText())
        idx = block - 1
        if 0 <= idx < 150:
            self.ctc.maintenance[idx] = closed
            self.ctc_office.update_maintenance(self.ctc.maintenance.copy())

    def update_block_occupancy_table(self):
        line = self.comboBlockOccupancy.currentText().replace(" Occupancy", "").strip().title()
        blocks = self.track_layout.get(line, [])
        self.tableBlockOccupancy.setRowCount(len(blocks))
        for row, blk in enumerate(blocks):
            block_number = blk['block_number']
            occupied = self.ctc.block_occupancy[block_number - 1]
            status = "Occupied" if occupied else "Unoccupied"
            self.tableBlockOccupancy.setItem(row, 0, QTableWidgetItem(str(block_number)))
            self.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem(status))
            self.tableBlockOccupancy.item(row, 1).setBackground(
                Qt.GlobalColor.red if occupied else Qt.GlobalColor.green
            )

    def update_track_states(self):
        state_mapping = [
            (self.ctc.crossing_states[0], 0),
            (self.ctc.crossing_states[1], 1),
            *[(self.ctc.switch_states[i], 2 + i * 2) for i in range(6)],
            *[(self.ctc.light_states[i], 3 + i * 2) for i in range(6)]
        ]
        for state, row in state_mapping:
            item = QTableWidgetItem("Active" if state else "Inactive")
            self.TrackStates.setItem(row, 0, item)

    def launch_track_controller_mock(self):
        from test_ctcOffice import TrackControllerMock
        self.track_controller_mock = TrackControllerMock(self.ctc)
        self.track_controller_mock.occupancy_changed.connect(self.handle_occupancy_update)
        self.track_controller_mock.switches_changed.connect(self.handle_switch_update)
        self.track_controller_mock.crossings_changed.connect(self.handle_crossing_update)
        self.track_controller_mock.lights_changed.connect(self.handle_light_update)
        self.track_controller_mock.show()

    def handle_occupancy_update(self, occupancy):
        self.ctc.block_occupancy = occupancy.copy()
        self.ctc_office.update_train_positions()
        self.update_block_occupancy_table()

    def handle_switch_update(self, switches):
        self.ctc.switch_states = switches.copy()
        self.update_track_states()

    def handle_crossing_update(self, crossings):
        self.ctc.crossing_states = crossings.copy()
        self.update_track_states()

    def handle_light_update(self, lights):
        self.ctc.light_states = lights.copy()
        self.update_track_states()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTCGUI()
    window.show()
    sys.exit(app.exec())