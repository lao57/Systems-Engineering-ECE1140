from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem


class TestBench(QObject):
    component_changed = pyqtSignal()
    schedule_logged = pyqtSignal(str)

    def __init__(self, ctc_office):
        super().__init__()
        self.ctc_office = ctc_office
        self.block_data = {}

        # Component states
        self.crossing_open = True
        self.light1_green = False
        self.light2_green = False
        self.switch_open = False
        self.schedule_logs = []

        self.initialize_block_occupancy()

    def initialize_block_occupancy(self):
        self.block_data = {}
        # Red Line blocks (1-76)
        for block in range(1, 77):
            self.block_data[(block, "Red Line")] = "Unoccupied"
        # Green Line blocks (1-141)
        for block in range(1, 142):
            self.block_data[(block, "Green Line")] = "Unoccupied"

    def update_block_occupancy_table(self):
        current_line = self.ctc_office.comboBlockOccupancy.currentText().replace(" Occupancy", "")
        block_count = 76 if current_line == "Red Line" else 141

        self.ctc_office.tableBlockOccupancy.setRowCount(block_count)
        for row in range(block_count):
            block_number = row + 1
            status = self.block_data.get((block_number, current_line), "Unoccupied")
            self.ctc_office.tableBlockOccupancy.setItem(row, 0, QTableWidgetItem(f"Block {block_number}"))
            self.ctc_office.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem(status))

    def set_block_occupied(self, block_number, train_line):
        line = "Red Line" if "red" in train_line.lower() else "Green Line"
        self.block_data[(block_number, line)] = "Occupied"
        self.update_block_occupancy_table()

    def set_block_unoccupied(self, block_number, train_line):
        line = "Red Line" if "red" in train_line.lower() else "Green Line"
        self.block_data[(block_number, line)] = "Unoccupied"
        self.update_block_occupancy_table()

    def log_schedule_upload(self, line, data):
        if data and isinstance(data[0], str) and data[0].endswith('.pdf'):
            log_entry = f"PDF Schedule Upload: {line} - {data[0]}"
        else:
            stations = " → ".join(data) if data else "No stations selected"
            log_entry = f"Manual Schedule: {line} - {stations}"

        self.schedule_logs.append(log_entry)
        self.schedule_logged.emit(log_entry)

    def toggle_crossing(self):
        self.crossing_open = not self.crossing_open
        self.component_changed.emit()

    def toggle_light1(self):
        self.light1_green = not self.light1_green
        self.component_changed.emit()

    def toggle_light2(self):
        self.light2_green = not self.light2_green
        self.component_changed.emit()

    def toggle_switch(self):
        self.switch_open = not self.switch_open
        self.component_changed.emit()