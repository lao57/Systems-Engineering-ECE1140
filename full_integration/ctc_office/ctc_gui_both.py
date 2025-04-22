import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from ctc_office.ctc_office_ui_both import Ui_MainWindow
from ctc_office.ctc_office_both import CTC, ScheduleLoader, load_track_layout, CTCOffice, STATION_BLOCKS_GREEN, STATION_BLOCKS_RED

class CTCGUI(QMainWindow, Ui_MainWindow):

    def __init__(self, ctc=None, ctc_office=None, track_layout=None, schedule_loader=None, track_controller=None):
        super().__init__()
        self.setupUi(self)

        self.ctc = ctc if ctc is not None else CTC()
        self.track_layout = load_track_layout(
            "C:/Users/dillo/PycharmProjects/Systems-Engineering-ECE1140/full_integration/assets/Track_Layout.xlsx")

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
        self.ctc_office.set_system_analysis_table(self.tableSystemAnalysis)

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

                selected_line = self.scheduleTrainLine.currentText().strip()

                if selected_line in schedules:
                    for idx in range(len(schedules[selected_line])):
                        self.ctc_office.schedule_train(selected_line, idx)

                self.update_all()
                QMessageBox.information(self, "Success", f"{selected_line} schedule loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load schedule: {str(e)}")

    def set_maintenance(self, closed: bool):
        line = self.maintLine.currentText().strip().title()
        block_text = self.maintBlock.currentText().replace("Block", "").strip()
        try:
            block = int(block_text)
        except ValueError:
            return

        if line == "Green Line":
            idx = block - 1
            if 0 <= idx < len(self.ctc.maintenance):
                self.ctc.maintenance[idx] = closed
        elif line == "Red Line":
            idx = block - 1
            if 0 <= idx < len(self.ctc.maintenance_red):
                self.ctc.maintenance_red[idx] = closed
        else:
            return

        self.ctc_office.update_maintenance(
            self.ctc.maintenance.copy(), self.ctc.maintenance_red.copy()
        )

    def update_block_combobox(self):
        line = self.maintLine.currentText().strip().title()
        blocks = [str(b['block_number']) for b in self.track_layout.get(line, [])]
        self.maintBlock.clear()
        self.maintBlock.addItems([f"Block {b}" for b in blocks])

    def update_all(self):
        # Update Green Line occupancy
        self.ctc.block_occupancy = self.track_controller.block_occupancy
        # Update Red Line occupancy
        if hasattr(self.ctc, "red_track_controller") and self.ctc.red_track_controller:
            self.ctc.block_occupancy_red = self.ctc.red_track_controller.block_occupancy

        # Call the update logic
        self.ctc_office.update()
        self.update_train_table()
        self.update_block_occupancy_table()
        self.update_track_states()
        self.update_system_analysis()
        self.update_wayside_controllers()

        # Clock cycle count
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
                QTableWidgetItem(train.line_name),
                QTableWidgetItem(str(train.current_block.block_number if train.current_block else "N/A")),
                QTableWidgetItem(f"{(train.authority_meters*3.2808399):.1f} ft"),
                QTableWidgetItem(self.get_station_name(next_stop) if isinstance(next_stop, int) else str(next_stop))
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableTrainMonitor.setItem(row, col, item)

    def get_station_name(self, block: int) -> str:
        all_blocks = {}
        all_blocks.update(STATION_BLOCKS_GREEN["BLOCK_TO_STATION"])
        all_blocks.update(STATION_BLOCKS_RED["BLOCK_TO_STATION"])
        return all_blocks.get(block, f"Block {block}")

    def update_block_occupancy_table(self):
        line = self.comboBlockOccupancy.currentText().replace(" Occupancy", "").strip().title()
        blocks = self.track_layout.get(line, [])
        self.tableBlockOccupancy.setRowCount(len(blocks))
        for i, blk in enumerate(blocks):
            block_num = blk['block_number']
            self.tableBlockOccupancy.setItem(i, 0, QTableWidgetItem(str(block_num)))
            if line == "Green Line":
                if 1 <= block_num <= len(self.ctc.block_occupancy):
                    occ = self.ctc.block_occupancy[block_num - 1]
                else:
                    occ = False
            else:
                if 1 <= block_num <= len(self.ctc.block_occupancy_red):
                    occ = self.ctc.block_occupancy_red[block_num - 1]
                else:
                    occ = False

            status = "Occupied" if occ else "Unoccupied"
            item = QTableWidgetItem(status)
            item.setBackground(Qt.GlobalColor.red if occ else Qt.GlobalColor.green)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tableBlockOccupancy.setItem(i, 1, item)

    def update_track_states(self):
        green_mapping = [
            ("Crossing 1", self.ctc.crossing_states[18]),
            ("Crossing 2", self.ctc.crossing_states[107]),
            ("Switch 1", self.ctc.switch_states[11]),
            ("Light 1", self.ctc.light_states[0]),
            ("Switch 2", self.ctc.switch_states[27]),
            ("Light 2", self.ctc.light_states[149]),
            ("Switch 3", self.ctc.switch_states[57]),
            ("Light 3", self.ctc.light_states[60]),
            ("Switch 4", self.ctc.switch_states[61]),
            ("Light 4", self.ctc.light_states[59]),
            ("Switch 5", self.ctc.switch_states[75]),
            ("Light 5", self.ctc.light_states[74]),
            ("Switch 6", self.ctc.switch_states[85]),
            ("Light 6", self.ctc.light_states[98])
        ]

        red_mapping = [
            ("Red Crossing 1", self.ctc.red_crossing_states[10]),
            ("Red Crossing 2", self.ctc.red_crossing_states[46]),
            ("Red Switch 1", self.ctc.red_switch_states[8]),
            ("Red Light 1", self.ctc.red_light_states[0]),
            ("Red Switch 2", self.ctc.red_switch_states[15]),
            ("Red Light 2", self.ctc.red_light_states[75]),
            ("Red Switch 3", self.ctc.red_switch_states[51]),
            ("Red Switch 4", self.ctc.red_switch_states[43]),
            ("Red Light 3", self.ctc.red_light_states[70]),
            ("Red Switch 5", self.ctc.red_switch_states[37]),
            ("Red Switch 6", self.ctc.red_switch_states[32]),
            ("Red Light 4", self.ctc.red_light_states[65]),
            ("Red Switch 7", self.ctc.red_switch_states[26])
        ]

        for row, (desc, state) in enumerate(green_mapping):
            if "Light" in desc:
                item_text = "Green" if state else "Red"
            elif "Switch" in desc:
                item_text = "On" if state else "Off"
            elif "Crossing" in desc:
                item_text = "Closed" if state else "Open"
            else:
                item_text = "Active" if state else "Inactive"

            item = QTableWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates.setItem(row, 0, item)

        for row, (desc, state) in enumerate(red_mapping):
            if "Light" in desc:
                item_text = "Green" if state else "Red"
            elif "Switch" in desc:
                item_text = "On" if state else "Off"
            elif "Crossing" in desc:
                item_text = "Closed" if state else "Open"
            else:
                item_text = "Active" if state else "Inactive"

            item = QTableWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates_2.setItem(row, 0, item)

    def update_system_analysis(self):
        self.ctc_office.update_system_analysis()

    def update_wayside_controllers(self):
        # Update Green Line wayside controllers
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

        # Update Red Line wayside controllers
        if self.ctc.red_track_controller and hasattr(self.ctc.red_track_controller, "wayside_controllers"):
            for wayside_name, config in self.ctc.red_track_controller.wayside_controllers.items():
                for i, switch_state in enumerate(config["switch_states"]):
                    if i < len(config["switches"]):
                        self.ctc.red_switch_states[config["switches"][i]] = switch_state
                for i, light_state in enumerate(config["light_states"]):
                    if i < len(config["lights"]):
                        self.ctc.red_light_states[config["lights"][i]] = light_state
                for i, crossing_state in enumerate(config["crossing_states"]):
                    if i < len(config["crossings"]):
                        self.ctc.red_crossing_states[config["crossings"][i]] = crossing_state

    def get_block_authority(self):
        return {
            "Green Line": self.ctc.get_block_authority(),
            "Red Line": self.ctc.red_get_block_authority()
        }

    def set_ctc(self, ctc):
        self.ctc = ctc

    def manual_stop_selection(self):
        line = self.scheduleTrainLine.currentText().strip().title()
        train_id, ok = QInputDialog.getInt(self, "Manual Train", "Enter Train ID:")
        if not ok:
            return
        stops = []
        if line == "Green Line":
            possible_stops = [f"Block {b['block_number']}" for b in self.track_layout.get('Green Line', [])]
        else:
            possible_stops = [f"Block {b['block_number']}" for b in self.track_layout.get('Red Line', [])]
        possible_stops.insert(0, "Done")
        while True:
            stop_item, ok = QInputDialog.getItem(self, "Select Stop", "Select a stop (choose 'Done' when finished):", possible_stops, 1, False)
            if not ok:
                break
            if stop_item == "Done":
                break
            stop_block = int(stop_item.replace("Block ", ""))
            stops.append(stop_block)
        self.ctc_office.schedule_manual_train(line, train_id, stops)
        self.update_all()
        QMessageBox.information(self, "Success", f"Manually scheduled Train {train_id} on {line} with stops: {stops}")

    # update clock in UI
    def update_world_clock(self, world_time: dict):
        time_str = f"Time: Day {world_time['day']} {world_time['hour']:02d}:{world_time['min']:02d}:{world_time['sec']:02d}"
        self.worldTime.setText(time_str)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CTCGUI()
    gui.show()
    sys.exit(app.exec())
