import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from CTCOffice_UI import Ui_MainWindow
from ctc_office import CTCOffice
from ctc import CTC
from track_loader import load_track_layout
from schedule_loader import ScheduleLoader
from CTC_test_ui import TestbenchGUI

logging.basicConfig(level=logging.INFO)


class CTCGUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ctc = CTC()
        self.track_layout = load_track_layout("track_layout.xlsx")
        self.schedule_loader = ScheduleLoader(self.track_layout)
        self.ctc_office = CTCOffice(self.track_layout, {'Green Line': [], 'Red Line': []})
        self.ctc_office.set_ctc(self.ctc)

        # Initialize Testbench
        self.testbench = TestbenchGUI(self.ctc)
        self.testbench.show()

        # Initialize UI
        self.setup_connections()
        self.setup_tables()
        self.update_block_combobox()

        # Add update timer for real-time synchronization
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_all)
        self.ui_update_timer.start(500)  # Update UI every 500ms

    def setup_connections(self):
        self.btnUploadSchedule.clicked.connect(self.load_schedule)
        self.btnOpenTrack.clicked.connect(lambda: self.set_maintenance(False))
        self.btnCloseTrack.clicked.connect(lambda: self.set_maintenance(True))
        self.maintLine.currentTextChanged.connect(self.update_block_combobox)
        self.comboBlockOccupancy.currentTextChanged.connect(self.update_block_occupancy_table)

    def setup_tables(self):
        # Train Monitor Table
        self.tableTrainMonitor.setHorizontalHeaderLabels([
            "Train ID", "Line", "Current Block", "Next Stop",
            "Suggested Auth.", "Scheduled Time"
        ])

        # Block Occupancy Table
        self.tableBlockOccupancy.setHorizontalHeaderLabels(["Block", "Status"])

        # Track States Table
        self.TrackStates.setHorizontalHeaderLabels(["State"])
        self.TrackStates.setVerticalHeaderLabels([
            "Crossing 1 (Block 28)", "Crossing 2 (Block 108)",
            "Switch 1 (Block 12)", "Light 1", "Switch 2 (Block 28)", "Light 2",
            "Switch 3 (Block 58)", "Light 3", "Switch 4 (Block 62)", "Light 4",
            "Switch 5 (Block 76)", "Light 5", "Switch 6 (Block 85)", "Light 6"
        ])

    def load_schedule(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Schedule File", "", "Excel Files (*.xlsx)"
        )
        if path:
            try:
                schedules = self.schedule_loader.load_from_excel(path)
                self.ctc_office.schedules = schedules

                # Clear previous trains and authorities
                self.ctc_office.active_trains.clear()
                self.ctc.block_authority = [0.0] * 150

                # Schedule trains
                for line in ['Green Line', 'Red Line']:
                    if line in schedules:
                        for idx in range(len(schedules[line])):
                            self.ctc_office.schedule_train(line, idx)

                QMessageBox.information(self, "Success", "Schedule loaded successfully!")
                self.update_all()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load schedule: {str(e)}")

    def set_maintenance(self, closed: bool):
        line = self.maintLine.currentText()
        block_text = self.maintBlock.currentText()
        block_number = int(block_text.split()[-1])

        if line == "Green Line":
            yard_block = self.ctc_office.GREEN_LINE_YARD_EXIT
        else:
            yard_block = 75

        if block_number == yard_block:
            QMessageBox.warning(self, "Warning", "Cannot perform maintenance on yard blocks!")
            return

        idx = block_number - 1
        if 0 <= idx < 150:
            self.ctc.maintenance[idx] = closed
            self.ctc_office.update_maintenance(self.ctc.maintenance.copy())

    def update_all(self):
        """Update all UI elements with current CTC state"""
        self.update_train_table()
        self.update_track_states()
        self.update_block_occupancy_table()

    def update_train_table(self):
        self.tableTrainMonitor.setRowCount(len(self.ctc_office.active_trains))

        for row, train in enumerate(self.ctc_office.active_trains):
            schedule = next(
                (s for line in self.ctc_office.schedules.values() for s in line
                 if s.train_id == train.train_id), None
            )

            if schedule and schedule.stops:
                first_stop = schedule.stops[0]
                station_name = self.get_station_name(first_stop['block'])
                scheduled_time = first_stop['time'].strftime('%H:%M')
                authority = train.authority
                current_block = self.ctc_office.GREEN_LINE_YARD_EXIT if train.line == "Green Line" else 75
            else:
                station_name = "N/A"
                scheduled_time = "N/A"
                authority = 0.0
                current_block = "Yard"

            items = [
                QTableWidgetItem(str(train.train_id)),
                QTableWidgetItem(train.line),
                QTableWidgetItem(str(current_block)),
                QTableWidgetItem(station_name),
                QTableWidgetItem(f"{authority:.2f}m"),
                QTableWidgetItem(scheduled_time)
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableTrainMonitor.setItem(row, col, item)

    def get_station_name(self, block_number: int) -> str:
        for blk in self.track_layout['Green Line'] + self.track_layout['Red Line']:
            if blk['block_number'] == block_number:
                infra = blk.get('infrastructure', '')
                if 'STATION:' in infra:
                    return infra.split(':')[1].split(';')[0].strip()
        return f"Block {block_number}"

    def update_block_combobox(self):
        line = self.maintLine.currentText()
        blocks = [blk["block_number"] for blk in self.track_layout[line]]
        self.maintBlock.clear()
        self.maintBlock.addItems([f"Block {b}" for b in sorted(blocks)])

    def update_block_occupancy_table(self):
        line = self.comboBlockOccupancy.currentText().replace(" Occupancy", "")
        blocks = self.track_layout[line]
        self.tableBlockOccupancy.setRowCount(len(blocks))

        for row, blk in enumerate(blocks):
            block_number = blk["block_number"]
            occupied = self.ctc.block_occupancy[block_number - 1]
            status = "Occupied" if occupied else "Unoccupied"

            self.tableBlockOccupancy.setItem(row, 0, QTableWidgetItem(str(block_number)))
            self.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem(status))
            self.tableBlockOccupancy.item(row, 1).setBackground(
                Qt.GlobalColor.red if occupied else Qt.GlobalColor.green
            )

    def update_track_states(self):
        # Crossings
        self.TrackStates.setItem(0, 0, QTableWidgetItem(
            "Active" if self.ctc.crossing_states[0] else "Inactive"
        ))
        self.TrackStates.setItem(1, 0, QTableWidgetItem(
            "Active" if self.ctc.crossing_states[1] else "Inactive"
        ))

        # Switches and Lights
        for i in range(6):
            self.TrackStates.setItem(2 + i * 2, 0, QTableWidgetItem(
                "Active" if self.ctc.switch_states[i] else "Inactive"
            ))
            self.TrackStates.setItem(3 + i * 2, 0, QTableWidgetItem(
                "Green" if self.ctc.light_states[i] else "Red"
            ))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTCGUI()
    window.show()
    sys.exit(app.exec())