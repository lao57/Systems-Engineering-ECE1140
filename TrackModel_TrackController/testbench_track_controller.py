import sys
import importlib.util
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QCheckBox, QHeaderView, QComboBox, QScrollArea, QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from wayside import WAYSIDE

import TrackController 
import TrackModelBackend
#import TrackModelUI
import testbench


class TestBench(QMainWindow):
    def __init__(self, ctc, track_model):
        super().__init__()
        self.ctc = ctc
        self.track_model = track_model
        self.setWindowTitle("Test Bench")
        self.setGeometry(200, 200, 800, 600)
        self.initUI()

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        # Scroll Area for the grid of buttons
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)

        # Create 150 buttons in a grid
        self.block_buttons = []
        for block_num in range(1, 151):
            btn = QPushButton(f"Block {block_num}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, block=block_num - 1: self.toggle_block(block))
            self.block_buttons.append(btn)
            self.grid_layout.addWidget(btn, (block_num - 1) // 10, (block_num - 1) % 10)

        scroll_widget.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        centralWidget.setLayout(layout)

    def toggle_block(self, block_num):
        """Toggle occupancy and maintenance status for the selected block."""
        self.track_model.occupancy_status[block_num] = not self.track_model.occupancy_status[block_num]
        self.ctc.maintenance[block_num] = 0

        # Update button color
        btn = self.block_buttons[block_num]
        if self.track_model.occupancy_status[block_num]:
            btn.setStyleSheet("background-color: lightGray")
        else:
            btn.setStyleSheet("")