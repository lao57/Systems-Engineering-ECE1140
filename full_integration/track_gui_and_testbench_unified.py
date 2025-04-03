import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFileDialog, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from TrackModelBackend import TrackModelBackend


class UnifiedTrackUI(QWidget):
    def __init__(self, backend=None):
        super().__init__()
        self.backend = backend
        self.backend.addUI(self)
        self.failures = {
            "Broken Rail": False,
            "Track Circuit": False,
            "Transponder": False,
            "Power Failure": False,
            "Maintenance": False
        }
        self.temperature = 70
        self.df_layout = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Testbench Section
        testbench_layout = QVBoxLayout()
        self.status_label = QLabel("Toggle failures to inject:")
        self.status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        testbench_layout.addWidget(self.status_label)

        self.failure_toggles = {}
        self.failure_status_labels = {}
        for failure in self.failures:
            toggle_layout = QHBoxLayout()
            toggle_button = QPushButton(failure)
            toggle_button.setFont(QFont("Arial", 12))
            toggle_button.setCheckable(True)
            toggle_button.clicked.connect(lambda checked, f=failure: self.toggle_failure(f, checked))
            toggle_layout.addWidget(toggle_button)

            status_label = QLabel("Inactive")
            status_label.setFont(QFont("Arial", 12))
            toggle_layout.addWidget(status_label)

            self.failure_toggles[failure] = toggle_button
            self.failure_status_labels[failure] = status_label
            testbench_layout.addLayout(toggle_layout)

        self.temp_label = QLabel(f"Temperature: {self.temperature}°F")
        self.temp_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        testbench_layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(-50)
        self.temp_slider.setMaximum(120)
        self.temp_slider.setValue(self.temperature)
        self.temp_slider.valueChanged.connect(self.update_temperature)
        testbench_layout.addWidget(self.temp_slider)

        main_layout.addLayout(testbench_layout)

        # Track Model Section
        track_model_layout = QVBoxLayout()

        upload_layout = QHBoxLayout()
        self.file_label = QLabel("Current Layout File:")
        self.file_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        upload_layout.addWidget(self.file_label)

        self.upload_button = QPushButton("Upload Layout")
        self.upload_button.setFont(QFont("Arial", 14))
        self.upload_button.setObjectName("uploadButton")
        self.upload_button.clicked.connect(self.upload_file)
        upload_layout.addWidget(self.upload_button)
        track_model_layout.addLayout(upload_layout)

        self.block_selector = QComboBox()
        self.block_selector.setFont(QFont("Arial", 12))
        self.block_selector.setObjectName("blockSelector")
        self.block_selector.currentIndexChanged.connect(self.reset_failures)
        track_model_layout.addWidget(self.block_selector)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        self.properties_label = QLabel("Properties")
        self.properties_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        grid_layout.addWidget(self.properties_label, 0, 0)

        labels = ["Speed Limit", "Direction of Travel", "Grade", "Elevation", "Block Size"]
        self.label_widgets = {}
        for i, text in enumerate(labels):
            label = QLabel(f"{text}: N/A")
            label.setFont(QFont("Arial", 12))
            self.label_widgets[text] = label
            grid_layout.addWidget(label, i + 1, 0)

        self.states_label = QLabel("Current States")
        self.states_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        grid_layout.addWidget(self.states_label, 0, 1)

        self.occupancy_label = QLabel("Track Occupancy: ✅")
        self.occupancy_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        grid_layout.addWidget(self.occupancy_label, 1, 1)

        self.switch_label = QLabel("Switch Position: N/A")
        self.switch_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.switch_label, 2, 1)

        self.crossing_label = QLabel("Railway Crossing: N/A")
        self.crossing_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.crossing_label, 3, 1)

        self.light_signal_label = QLabel("Light Signal: N/A")
        self.light_signal_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.light_signal_label, 4, 1)

        self.station_label = QLabel("Station: N/A")
        self.station_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.station_label, 5, 1)

        track_model_layout.addLayout(grid_layout)
        main_layout.addLayout(track_model_layout)

        self.setLayout(main_layout)

    def toggle_failure(self, failure, checked):
        """Toggle the failure status and update the label."""
        self.failures[failure] = checked
        self.failure_status_labels[failure].setText("Active" if checked else "Inactive")

    def reset_failures(self):
        """Reset all failures to inactive when switching blocks."""
        for failure in self.failures:
            self.failures[failure] = False
            self.failure_toggles[failure].setChecked(False)
            self.failure_status_labels[failure].setText("Inactive")

    def update_temperature(self):
        self.temperature = self.temp_slider.value()
        self.temp_label.setText(f"Temperature: {self.temperature}°F")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Layout File", "", "CSV Files (*.csv)")
        if not file_path:
            return
        self.backend.load_excel(file_path)  # Assuming the backend has a method to load Excel files
        self.load_csv_data(file_path)
        return file_path

    def load_csv_data(self, file_path):
        print(f"Loading CSV data from in bench: {file_path}")
        try:
            self.df_layout = pd.read_csv(file_path)
            if self.df_layout.empty:
                self.file_label.setText("Error: CSV file is empty or incorrectly formatted.")
                return
            self.file_label.setText(f"Loaded File: {file_path}")
            self.block_selector.clear()
            self.block_selector.addItems(self.df_layout['Block Number'].astype(str).tolist())
        except Exception as e:
            self.file_label.setText(f"Error loading file: {e}")

    def update(self):
        """Explicitly update the UI based on the backend state."""
        if self.backend is None or self.df_layout is None:
            return

        block_index = self.block_selector.currentIndex()
        if block_index >= 0:
            block = self.backend.blocks[block_index+1]
            speed_mph = round(block["speed_limit"] * 0.621371, 1)
            block_size_ft = round(block["block_size"] * 3.28084, 1)
            self.label_widgets["Speed Limit"].setText(f"Speed Limit: {speed_mph} mph")
            self.label_widgets["Block Size"].setText(f"Block Size: {block_size_ft} ft")
            self.label_widgets["Grade"].setText(f"Grade: {block['grade']}%")
            self.label_widgets["Elevation"].setText(f"Elevation: {block['elevation']} m")

            # Update states
            self.occupancy_label.setText(f"Track Occupancy: {'✅' if self.backend.get_occupancy_status(block_index) else '❌'}")
            self.switch_label.setText(f"Switch Position: {'On' if self.backend.get_switch_states(block_index) else 'Off'}")
            self.crossing_label.setText(f"Railway Crossing: {'Active' if self.backend.get_crossing_states(block_index) else 'Inactive'}")
            self.light_signal_label.setText(f"Light Signal: {'Green' if self.backend.get_light_signals(block_index) else 'Red'}")
            print(f"Block {block_index+1} Authority: {self.backend.get_block_authority(block_index)}")


def main():
    app = QApplication(sys.argv)
    track_model = TrackModelBackend()
    window = QMainWindow()
    window.setWindowTitle("Unified Track System Interface")
    unified_ui = UnifiedTrackUI(backend=track_model)
    window.setCentralWidget(unified_ui)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()