import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QHBoxLayout, QSpinBox, QGridLayout, QComboBox, QCheckBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer, Qt


class TrackModelUI(QMainWindow):
    def __init__(self, backend=None):
        """Initialize the Track Model GUI."""
        super().__init__()

        self.backend = backend  # Connect to backend
        self.setWindowTitle("Track Model Interface")
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet("background-color: #2c3e50;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout()

        # Title Label
        self.title_label = QLabel("Track Model")
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff; text-align: center; padding: 10px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        # File Upload Section
        upload_layout = QHBoxLayout()
        self.file_label = QLabel("No File Uploaded")
        self.file_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.file_label.setStyleSheet("color: #ffffff;")
        upload_layout.addWidget(self.file_label)

        self.upload_button = QPushButton("Upload Track Layout")
        self.upload_button.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        self.upload_button.clicked.connect(self.upload_file)
        upload_layout.addWidget(self.upload_button)

        main_layout.addLayout(upload_layout)

        # Block Selection Dropdown
        self.block_selector = QComboBox()
        self.block_selector.setStyleSheet("background-color: black; font-size: 12px; padding: 5px;")
        self.block_selector.currentIndexChanged.connect(self.update_block_info)
        main_layout.addWidget(self.block_selector)

        # Grid Layout for Block Properties
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # Labels for Block Properties
        self.label_widgets = {}
        labels = ["Speed Limit", "Direction of Travel", "Grade", "Elevation", "Block Size"]
        for i, text in enumerate(labels):
            label = QLabel(f"{text}: N/A")
            label.setStyleSheet("color: #ffffff; font-size: 12px;")
            self.label_widgets[text] = label
            grid_layout.addWidget(label, i, 0)

        # Current Block States
        self.occupancy_label = QLabel("Track Occupancy: ✅")
        self.occupancy_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold;")
        grid_layout.addWidget(self.occupancy_label, 0, 1)

        self.switch_label = QLabel("Switch Position: N/A")
        self.switch_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.switch_label, 1, 1)

        self.crossing_label = QLabel("Railway Crossing: N/A")
        self.crossing_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.crossing_label, 2, 1)

        self.light_signal_label = QLabel("Light Signal: N/A")
        self.light_signal_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.light_signal_label, 3, 1)

        # Track Heater Control
        temp_layout = QHBoxLayout()
        self.temp_label = QLabel("Temperature:")
        self.temp_label.setStyleSheet("color: white; font-size: 14px;")

        self.temp_input = QSpinBox()
        self.temp_input.setRange(-50, 120)  # Fahrenheit range
        self.temp_input.setSuffix(" °F")
        self.temp_input.setStyleSheet("background-color: black; color: white; font-size: 12px; padding: 3px;")
        self.temp_input.valueChanged.connect(self.update_track_heater)

        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_input)
        temp_layout.addStretch()
        grid_layout.addLayout(temp_layout, 4, 0, 1, 2)

        self.track_heater_label = QLabel("Track Heater: OFF")
        self.track_heater_label.setStyleSheet("color: white; font-size: 14px;")
        grid_layout.addWidget(self.track_heater_label, 5, 0)

        main_layout.addLayout(grid_layout)
        self.central_widget.setLayout(main_layout)

    def upload_file(self):
        """Open a file dialog to select an Excel (.xlsx) file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Track Layout", "", "Excel Files (*.xlsx *.xls)")
        if file_path and self.backend:
            self.backend.upload_excel(file_path)

    def update_block_info(self):
        """Update the UI with selected block details."""
        if self.backend:
            self.backend.update_gui_display()

    def update_track_heater(self, temp=None):
        """Update the track heater based on temperature."""
        if temp is None:
            temp = self.temp_input.value()
        if temp <= 32:
            self.track_heater_label.setText("Track Heater: ON")
        else:
            self.track_heater_label.setText("Track Heater: OFF")

    def update_failure_status(self, block_number, failure_status):
        """Display track circuit failures in UI."""
        if failure_status:
            self.file_label.setText(f"⚠️ Track Circuit Failure at Block {block_number}")
        else:
            self.file_label.setText("No Active Failures")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TrackModelUI()
    window.show()
    sys.exit(app.exec())
