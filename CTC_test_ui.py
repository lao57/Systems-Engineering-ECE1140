import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QSpinBox, QCheckBox,
                             QPushButton, QLabel)
from PyQt6.QtCore import Qt, QTimer
from ctc import CTC


class MockTrackController:
    def __init__(self):
        self.block_occupancy = [False] * 150
        self.switch_states = [False] * 6
        self.light_states = [False] * 6
        self.crossing_states = [False] * 2


class TestbenchGUI(QMainWindow):
    def __init__(self, ctc: CTC):
        super().__init__()
        self.ctc = ctc
        self.mock = MockTrackController()
        self.ctc.connect_track_controller(self.mock)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Track Controller Testbench")
        self.setGeometry(100, 100, 600, 400)

        main_widget = QWidget()
        layout = QVBoxLayout()

        # Block Occupancy Control
        block_group = QGroupBox("Block Occupancy")
        block_layout = QHBoxLayout()

        self.block_spin = QSpinBox()
        self.block_spin.setRange(1, 150)
        self.occupancy_check = QCheckBox("Occupied")
        update_btn = QPushButton("Update Block", clicked=self.update_block)

        block_layout.addWidget(QLabel("Block:"))
        block_layout.addWidget(self.block_spin)
        block_layout.addWidget(self.occupancy_check)
        block_layout.addWidget(update_btn)
        block_group.setLayout(block_layout)

        # Switch Controls
        switch_group = QGroupBox("Switches (0-5)")
        switch_layout = QHBoxLayout()
        self.switch_checks = [QCheckBox(f"Switch {i}") for i in range(6)]
        for check in self.switch_checks:
            switch_layout.addWidget(check)
        switch_group.setLayout(switch_layout)

        # Light Controls
        light_group = QGroupBox("Lights (0-5)")
        light_layout = QHBoxLayout()
        self.light_checks = [QCheckBox(f"Light {i}") for i in range(6)]
        for check in self.light_checks:
            light_layout.addWidget(check)
        light_group.setLayout(light_layout)

        # Crossing Controls
        crossing_group = QGroupBox("Crossings (0-1)")
        crossing_layout = QHBoxLayout()
        self.crossing_checks = [QCheckBox(f"Crossing {i}") for i in range(2)]
        for check in self.crossing_checks:
            crossing_layout.addWidget(check)
        crossing_group.setLayout(crossing_layout)

        # Assemble layout
        layout.addWidget(block_group)
        layout.addWidget(switch_group)
        layout.addWidget(light_group)
        layout.addWidget(crossing_group)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Timer to push updates to CTC
        self.timer = QTimer()
        self.timer.timeout.connect(self.push_updates)
        self.timer.start(500)

    def update_block(self):
        block = self.block_spin.value() - 1
        occupied = self.occupancy_check.isChecked()
        self.mock.block_occupancy[block] = occupied

    def push_updates(self):
        # Update switches
        for i in range(6):
            self.mock.switch_states[i] = self.switch_checks[i].isChecked()

        # Update lights
        for i in range(6):
            self.mock.light_states[i] = self.light_checks[i].isChecked()

        # Update crossings
        for i in range(2):
            self.mock.crossing_states[i] = self.crossing_checks[i].isChecked()

        # Trigger CTC update
        self.ctc.update_states()


def run_testbench(ctc):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    tb = TestbenchGUI(ctc)
    tb.show()
    return tb  # Return the testbench instance
