import random
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtGui import QFont, QColor, QPalette

class TestBench:
    def __init__(self, ctc_office):
        self.ctc_office = ctc_office

    def simulate_train_updates(self):
        def update():
            train_data = [[101, "3", "50 kmh", "40 m"], [102, "5", "45 kmh", "40 m"]]
            self.update_train_monitor(train_data)

        self.timer_train_updates = QTimer(self.ctc_office)
        self.timer_train_updates.timeout.connect(update)
        self.timer_train_updates.start(5000)  # Update every 5 seconds

    def simulate_track_data(self, selected_line=None):
        def update():
            occupancy = {f"Block {i}": "Occupied" if random.choice([0, 1]) else "Unoccupied" for i in range(1, 11)}
            self.update_block_occupancy(occupancy)

        if selected_line:
            print(f"Updating block occupancy for {selected_line}")

        self.timer_track_data = QTimer(self.ctc_office)
        self.timer_track_data.timeout.connect(update)
        self.timer_track_data.start(5000)  # Update every 5 seconds

    def update_train_monitor(self, train_data):
        self.ctc_office.tableTrainMonitor.setRowCount(len(train_data))
        for row, train in enumerate(train_data):
            for col, data in enumerate(train):
                self.ctc_office.tableTrainMonitor.setItem(row, col, QTableWidgetItem(str(data)))

    def update_block_occupancy(self, occupancy):
        self.ctc_office.tableBlockOccupancy.setRowCount(len(occupancy))
        for row, (block, status) in enumerate(occupancy.items()):
            self.ctc_office.tableBlockOccupancy.setItem(row, 0, QTableWidgetItem(block))
            self.ctc_office.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem(status))
