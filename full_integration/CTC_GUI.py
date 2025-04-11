import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from CTCOffice_UI import Ui_MainWindow
from ctc_office import CTC, ScheduleLoader, load_track_layout, CTCOffice, STATION_BLOCKS

class CTCGUI(QMainWindow, Ui_MainWindow):

    def __init__(self, ctc=None, ctc_office=None, track_layout=None, schedule_loader=None, track_controller=None):
        super().__init__()
        self.setupUi(self)


        self.ctc = ctc if ctc is not None else CTC()
        self.track_layout = track_layout if track_layout is not None else load_track_layout("Systems-Engineering-ECE1140/full_integration/assets/Track_Layout.xlsx")
        self.schedule_loader = schedule_loader if schedule_loader is not None else ScheduleLoader(self.track_layout)
        if ctc_office is not None:
            self.ctc_office = ctc_office
        else:
            self.ctc_office = CTCOffice(self.track_layout, {'Green Line': [], 'Red Line': []})
            self.ctc_office.set_ctc(self.ctc)
        # Save the track_controller reference
        self.track_controller = track_controller

        self.setup_connections()
        self.update_block_combobox()

        self.count = 0

    def setup_connections(self):
        self.btnUploadSchedule.clicked.connect(self.load_schedule)
        self.btnManualUpload.clicked.connect(self.manual_stop_selection)
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
        self.ctc.block_occupancy = self.track_controller.block_occupancy
        self.ctc_office.update()
        self.update_train_table()
        self.update_block_occupancy_table()
        self.update_track_states()
        self.update_system_analysis()
        self.update_wayside_controllers()
        if self.count >= 5:
            self.count = 0
        self.count += 1

    def update_train_table(self):
        trains = self.ctc_office.active_trains
        self.tableTrainMonitor.setRowCount(len(trains))
        for row, train in enumerate(trains):
            if train.next_stop_index < len(train.scheduled_stops):
                next_stop = train.scheduled_stops[train.next_stop_index]
            else:
                next_stop = "None"
            items = [
                QTableWidgetItem(str(train.train_id)),
                QTableWidgetItem("Green Line"),
                QTableWidgetItem(str(train.current_block.block_number if train.current_block else "N/A")),
                QTableWidgetItem(f"{(train.authority_meters*3.2808399):.1f} ft"),
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
            ("Switch 1", self.ctc.switch_states[2]),
            ("Light 1", self.ctc.light_states[3]),
            ("Switch 2", self.ctc.switch_states[4]),
            ("Light 2", self.ctc.light_states[5]),
            ("Switch 3", self.ctc.switch_states[6]),
            ("Light 3", self.ctc.light_states[7]),
            ("Switch 4", self.ctc.switch_states[8]),
            ("Light 4", self.ctc.light_states[9]),
            ("Switch 5", self.ctc.switch_states[10]),
            ("Light 5", self.ctc.light_states[11]),
            ("Switch 6", self.ctc.switch_states[12]),
            ("Light 6", self.ctc.light_states[75])
        ]
        for row, (desc, state) in enumerate(mapping):
            item = QTableWidgetItem("Active" if state else "Inactive")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates.setItem(row, 0, item)

    def update_system_analysis(self):
        dummy_data = {
            0: ["100", "1", "1.0%"],
            1: ["120", "2", "1.6%"]
        }
        for row in range(2):
            for col in range(3):
                item = QTableWidgetItem(dummy_data[row][col])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableSystemAnalysis.setItem(row, col, item)

    def update_wayside_controllers(self):
        # Update the global state arrays (switches, lights, crossings) from the Track Controller.
        if self.track_controller and hasattr(self.track_controller, "wayside_controllers"):
            for wayside_name, config in self.track_controller.wayside_controllers.items():
                for i, switch_state in enumerate(config["switch_states"]):
                    if i < len(config["switches"]):
                        self.ctc.switch_states[config["switches"][i]] = switch_state
                for i, light_state in enumerate(config["light_states"]):
                    if i < len(config["lights"]):
                        self.ctc.light_states[config["lights"][i]] = light_state
                for i, crossing_state in enumerate(config["crossing_states"]):
                    if i < len(config["crossings"]):
                        self.ctc.crossing_states[config["crossings"][i]] = crossing_state

    def get_block_authority(self):

        return self.ctc.get_block_authority()

    def set_ctc(self, ctc):
        self.ctc = ctc

    def manual_stop_selection(self):

        line = self.scheduleTrainLine.currentText().strip().title()
        # get train_id
        train_id, ok = QInputDialog.getInt(self, "Manual Train", "Enter Train ID:")
        if not ok:
            return

        # make empty list to get stops
        stops = []
        # possible stops
        if line == "Green Line":
            possible_stops = [f"Block {b['block_number']}" for b in self.track_layout.get('Green Line', [])]
        else:
            possible_stops = [f"Block {b['block_number']}" for b in self.track_layout.get('Red Line', [])]
        # click done for completion
        possible_stops.insert(0, "Done")

        # allow user to select as many stops as they want
        while True:
            stop_item, ok = QInputDialog.getItem(self, "Select Stop", "Select a stop (choose 'Done' when finished):",
                                                 possible_stops, 1, False)
            if not ok:
                break
            if stop_item == "Done":
                break
            # get block num
            stop_block = int(stop_item.replace("Block ", ""))
            stops.append(stop_block)

        # call manual scheduling func
        self.ctc_office.schedule_manual_train(line, train_id, stops)
        self.update_all()
        QMessageBox.information(self, "Success", f"Manually scheduled Train {train_id} on {line} with stops: {stops}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CTCGUI()
    gui.show()
    sys.exit(app.exec())
