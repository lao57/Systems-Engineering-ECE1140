import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QSlider, QPushButton, QFileDialog, QSpinBox, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

import TrackModelBackend

class TestbenchGUI(QWidget):
    # Define signals
    failure_updated = pyqtSignal(dict)  # Signal for failure updates
    temperature_updated = pyqtSignal(int)  # Signal for temperature updates

    def __init__(self, backend):
        super().__init__()
        self.backend = backend  # Reference to the backend
        self.failures = {
            "Broken Rail": False,
            "Track Circuit": False,
            "Transponder": False,
            "Power Failure": False,
            "Maintenance": False
        }
        self.temperature = 70  # Default temperature in °F
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Failure Selection Section
        self.status_label = QLabel("Select failures to inject:")
        self.status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.status_label)

        self.checkboxes = {}
        for failure in self.failures:
            checkbox = QCheckBox(failure)
            checkbox.setFont(QFont("Arial", 12))
            checkbox.stateChanged.connect(self.update_failures)
            layout.addWidget(checkbox)
            self.checkboxes[failure] = checkbox

        # Temperature Control Section
        self.temp_label = QLabel(f"Temperature: {self.temperature}°F")
        self.temp_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(-50)
        self.temp_slider.setMaximum(120)
        self.temp_slider.setValue(self.temperature)
        self.temp_slider.valueChanged.connect(self.update_temperature)
        layout.addWidget(self.temp_slider)

        self.setLayout(layout)

    def update_failures(self):
        for failure, checkbox in self.checkboxes.items():
            self.failures[failure] = checkbox.isChecked()
        
        # Emit the failure_updated signal
        self.failure_updated.emit(self.failures)

    def update_temperature(self):
        self.temperature = self.temp_slider.value()
        self.temp_label.setText(f"Temperature: {self.temperature}°F")
        
        # Emit the temperature_updated signal
        self.temperature_updated.emit(self.temperature)


class TrackModelUI(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend  # Reference to the backend
        self.initUI()

        # Timer to periodically refresh the GUI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_gui_from_backend)
        self.timer.start(1000)  # Refresh every 1 second

    def initUI(self):
        main_layout = QVBoxLayout()

        # File Upload Section
        upload_layout = QHBoxLayout()
        self.file_label = QLabel("Current Layout File:")
        self.file_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        upload_layout.addWidget(self.file_label)

        self.upload_button = QPushButton("Upload Layout")
        self.upload_button.setFont(QFont("Arial", 14))
        self.upload_button.setObjectName("uploadButton")
        self.upload_button.clicked.connect(self.upload_file)
        upload_layout.addWidget(self.upload_button)
        main_layout.addLayout(upload_layout)

        # Block Selection Dropdown
        self.block_selector = QComboBox()
        self.block_selector.setFont(QFont("Arial", 12))
        self.block_selector.setObjectName("blockSelector")
        self.block_selector.currentIndexChanged.connect(self.update_block_info)
        main_layout.addWidget(self.block_selector)

        # Grid Layout for Properties and States
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # Properties Section
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

        # Current States Section
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

        self.beacon_label = QLabel("Beacon Signal: N/A")
        self.beacon_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.beacon_label, 4, 1)

        self.light_signal_label = QLabel("Light Signal: N/A")
        self.light_signal_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.light_signal_label, 5, 1)

        self.station_label = QLabel("Station: N/A")
        self.station_label.setFont(QFont("Arial", 12))
        grid_layout.addWidget(self.station_label, 6, 1)

        # Temperature Control Section
        temp_layout = QHBoxLayout()
        self.temp_label = QLabel("Temperature:")
        self.temp_label.setFont(QFont("Arial", 14))
        self.temp_input = QSpinBox()
        self.temp_input.setRange(-50, 120)
        self.temp_input.setSuffix(" °F")
        self.temp_input.setFont(QFont("Arial", 12))
        self.temp_input.valueChanged.connect(self.update_track_heater)
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_input)
        temp_layout.addStretch()
        grid_layout.addLayout(temp_layout, 7, 0, 1, 2)

        self.track_heater_label = QLabel("Track Heater: OFF")
        self.track_heater_label.setFont(QFont("Arial", 14))
        grid_layout.addWidget(self.track_heater_label, 8, 0)

        main_layout.addLayout(grid_layout)
        self.setLayout(main_layout)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Layout File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.backend.load_excel(file_path)
            self.block_selector.clear()
            self.block_selector.addItems([str(b) for b in self.backend.get_all_blocks()])

    def update_gui_from_backend(self):
        """Update the GUI based on the current state of the backend."""
        block_num = int(self.block_selector.currentText())
        block_data = self.backend.get_block_data(block_num)

        if block_data:
            # Update properties
            self.label_widgets["Speed Limit"].setText(f"Speed Limit: {block_data['speed_limit']} mph")
            self.label_widgets["Grade"].setText(f"Grade: {block_data['grade']}%")
            self.label_widgets["Elevation"].setText(f"Elevation: {block_data['elevation']} m")
            self.label_widgets["Block Size"].setText(f"Block Size: {block_data['block_size']} ft")

            # Update states
            occupancy = "✅" if self.backend.get_occupancy_status(block_num) else "❌"
            self.occupancy_label.setText(f"Track Occupancy: {occupancy}")

            switch_state = "Straight" if self.backend.get_switch_states(block_num) else "Diverging"
            self.switch_label.setText(f"Switch Position: {switch_state}")

            light_signal = "Green" if self.backend.get_light_signals(block_num) else "Red"
            self.light_signal_label.setText(f"Light Signal: {light_signal}")

            crossing = "Closed" if self.backend.get_crossing_states(block_num) else "Open"
            self.crossing_label.setText(f"Railway Crossing: {crossing}")

    def update_track_heater(self, temp=None):
        if temp is None:
            temp = self.temp_input.value()
        if temp <= 32:
            self.track_heater_label.setText("Track Heater: ON")
        else:
            self.track_heater_label.setText("Track Heater: OFF")

    def update_block_info(self):
        """Update the GUI with the current block's information from the backend."""
        try:
            # Get the currently selected block number from the dropdown
            block_num = int(self.block_selector.currentText())
            
            # Fetch the block data from the backend
            block_data = self.backend.get_block_data(block_num)
            
            if block_data:
                # Update properties
                self.label_widgets["Speed Limit"].setText(f"Speed Limit: {block_data['speed_limit']} mph")
                self.label_widgets["Grade"].setText(f"Grade: {block_data['grade']}%")
                self.label_widgets["Elevation"].setText(f"Elevation: {block_data['elevation']} m")
                self.label_widgets["Block Size"].setText(f"Block Size: {block_data['block_size']} ft")

                # Update states
                occupancy = "✅" if self.backend.get_occupancy_status(block_num) else "❌"
                self.occupancy_label.setText(f"Track Occupancy: {occupancy}")

                switch_state = "Straight" if self.backend.get_switch_states(block_num) else "Diverging"
                self.switch_label.setText(f"Switch Position: {switch_state}")

                light_signal = "Green" if self.backend.get_light_signals(block_num) else "Red"
                self.light_signal_label.setText(f"Light Signal: {light_signal}")

                crossing = "Closed" if self.backend.get_crossing_states(block_num) else "Open"
                self.crossing_label.setText(f"Railway Crossing: {crossing}")

                # Update infrastructure (station, beacon, etc.)
                infra = block_data.get("infrastructure", "")
                if "Station" in infra:
                    station_name = infra.split("Station")[-1].strip()
                    self.station_label.setText(f"Station: {station_name}")
                else:
                    self.station_label.setText("Station: None")

                if "Beacon" in infra:
                    self.beacon_label.setText("Beacon Signal: Present")
                else:
                    self.beacon_label.setText("Beacon Signal: None")

                # Update track heater status based on temperature
                track_heater_status = "ON" if block_data.get("track_heater", False) else "OFF"
                self.track_heater_label.setText(f"Track Heater: {track_heater_status}")

        except ValueError:
            # Handle case where block number is not a valid integer
            self.file_label.setText("Error: Invalid block number selected.")
        except Exception as e:
            # Handle any other exceptions
            self.file_label.setText(f"Error updating block info: {e}")

class UnifiedInterface(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.setWindowTitle("Unified Testbench & Track Model Interface")
        self.setGeometry(25, 25, 800, 600)  # Adjusted window size for better layout
        self.backend = backend  # Store the backend instance
        self.initUI()

    def initUI(self):
        # Create the central widget and set the main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create the TestbenchGUI and pass the backend to it
        self.testbench = TestbenchGUI(self.backend)
        
        # Create the TrackModelUI and pass the backend to it
        self.track_model_ui = TrackModelUI(self.backend)

        # Add both GUIs to the main layout
        layout.addWidget(self.testbench)
        layout.addWidget(self.track_model_ui)

        # Connect signals and slots (if needed)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals between the backend and GUIs (if needed)."""
        # Example: If the TestbenchGUI needs to notify the backend of failures
        self.testbench.failure_updated.connect(self.backend.handle_failures)
        self.testbench.temperature_updated.connect(self.backend.update_temperature)


def main():
    app = QApplication(sys.argv)

    # Global StyleSheet for the entire app
    app.setStyleSheet("""
        /* Global default for all widgets */
        QWidget {
            background-color: #2c3e50;
            color: white;
        }

        QSlider, QComboBox, QSpinBox, QCheckBox, QPushButton {
            background-color: #2c3e50; 
            color: white;
        }

        /* Make the Upload button stand out with a unique color */
        QPushButton#uploadButton {
            background-color: #3498db;
            color: white;
            border: 1px solid #fff;
            border-radius: 5px;
            padding: 6px 12px;
        }
        QPushButton#uploadButton:hover {
            background-color: #2980b9; /* Hover effect */
        }

        /* Make the track selection ComboBox stand out with a unique color */
        QComboBox#blockSelector {
            background-color: #e67e22;
            color: white;
            border: 1px solid #fff;
            border-radius: 3px;
            padding: 3px;
        }
        QComboBox#blockSelector:hover {
            background-color: #d35400; /* Hover effect */
        }

        /* Slider groove and handle for a more visible track/knob */
        QSlider::groove:horizontal {
            background: #FFFAFA; 
            height: 6px;
        }
        QSlider::handle:horizontal {
            background: #FF0000; 
            border: 1px solid #FF0000;
            width: 15px;
            margin: -5px 0;
            border-radius: 7px;
        }
    """)

    # Create the backend
    backend = TrackModelBackend.TrackModelBackend()

    # Create the main window and pass the backend to it
    window = UnifiedInterface(backend)
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()