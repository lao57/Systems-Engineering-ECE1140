from PyQt6.QtCore import Qt
import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
                             QHBoxLayout, QSpinBox, QGridLayout, QComboBox, QCheckBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
import socket  # <-- import for communication with the testbench
import threading


class TrackModelUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Track Model Interface")
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet("background-color: #2c3e50;")  # Dark background for contrast

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.check_failures()  # Start listening for failure updates

        main_layout = QVBoxLayout()

        # Title Label
        self.title_label = QLabel("Track Model")
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff; text-align: center; padding: 10px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        # File Upload Section
        upload_layout = QHBoxLayout()
        self.file_label = QLabel("Current Layout File:")
        self.file_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.file_label.setStyleSheet("color: #ffffff;")
        upload_layout.addWidget(self.file_label)

        self.upload_button = QPushButton("Upload Excel File")
        self.upload_button.setStyleSheet(
            "background-color: #3498db; color: white; font-size: 14px; padding: 8px; border-radius: 5px;")
        self.upload_button.clicked.connect(self.upload_file)
        upload_layout.addWidget(self.upload_button)

        main_layout.addLayout(upload_layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_failures)
        self.timer.start(1000)  # Check failures every second

        # Block Selection Dropdown
        self.block_selector = QComboBox()
        self.block_selector.setStyleSheet("background-color: black; font-size: 12px; padding: 5px;")
        self.block_selector.currentIndexChanged.connect(self.update_block_info)
        main_layout.addWidget(self.block_selector)

        # Grid Layout for Properties and States
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # Properties Section
        self.properties_label = QLabel("Properties")
        self.properties_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.properties_label.setStyleSheet("color: #ffffff;")
        grid_layout.addWidget(self.properties_label, 0, 0)

        labels = ["Speed Limit", "Direction of Travel", "Grade", "Elevation", "Block Size"]
        self.label_widgets = {}
        for i, text in enumerate(labels):
            label = QLabel(f"{text}: N/A")
            label.setStyleSheet("color: #ffffff; font-size: 12px;")
            self.label_widgets[text] = label
            grid_layout.addWidget(label, i + 1, 0)

        # Current States
        self.states_label = QLabel("Current States")
        self.states_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.states_label.setStyleSheet("color: #ffffff;")
        grid_layout.addWidget(self.states_label, 0, 1)

        self.occupancy_label = QLabel("Track Occupancy: ✅")  # Default Unoccupied
        self.occupancy_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold;")  # Green color
        grid_layout.addWidget(self.occupancy_label, 1, 1)

        self.switch_label = QLabel("Switch Position: N/A")
        self.switch_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.switch_label, 2, 1)

        self.crossing_label = QLabel("Railway Crossing: N/A")
        self.crossing_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.crossing_label, 3, 1)

        self.beacon_label = QLabel("Beacon Signal: N/A")
        self.beacon_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.beacon_label, 4, 1)

        self.light_signal_label = QLabel("Light Signal: N/A")
        self.light_signal_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.light_signal_label, 5, 1)

        self.station_label = QLabel("Station: N/A")
        self.station_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        grid_layout.addWidget(self.station_label, 6, 1)

        # Temperature Control - Place Label & Input Together
        temp_layout = QHBoxLayout()

        # Label for temperature
        self.temp_label = QLabel("Temperature:")
        self.temp_label.setStyleSheet("color: white; font-size: 14px;")

        # Temperature input box
        self.temp_input = QSpinBox()
        self.temp_input.setRange(-50, 120)  # Fahrenheit range
        self.temp_input.setSuffix(" °F")  # Proper format
        self.temp_input.setStyleSheet("background-color: black; color: white; font-size: 12px; padding: 3px;")
        self.temp_input.valueChanged.connect(self.update_track_heater)  # Update track heater

        # Add widgets in a single row
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_input)
        temp_layout.addStretch()  # Aligns everything properly

        # Add the temperature layout to the grid
        grid_layout.addLayout(temp_layout, 7, 0, 1, 2)  # Ensures label & input are on the same line

        # Track Heater Status
        self.track_heater_label = QLabel("Track Heater: OFF")
        self.track_heater_label.setStyleSheet("color: white; font-size: 14px;")
        grid_layout.addWidget(self.track_heater_label, 8, 0)

        main_layout.addLayout(grid_layout)
        self.central_widget.setLayout(main_layout)

        # Failures Section
        self.failures_label = QLabel("Failures")
        self.failures_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.failures_label.setStyleSheet("color: #ffffff;")
        grid_layout.addWidget(self.failures_label, 9, 0)



    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Layout File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.load_excel_data(file_path)

    def load_excel_data(self, file_path):
        try:
            self.df_layout = pd.read_excel(file_path, sheet_name="Blue Line")
            if self.df_layout.empty:
                self.file_label.setText("Error: Blue Line sheet is empty or incorrectly formatted.")
                return
            self.block_selector.clear()
            self.block_selector.addItems(self.df_layout['Block Number'].astype(str).tolist())
        except Exception as e:
            self.file_label.setText(f"Error loading file: {e}")

    def update_block_info(self):
        block_index = self.block_selector.currentIndex()
        if self.df_layout is not None and block_index >= 0:
            row = self.df_layout.iloc[block_index]

            # Convert Speed Limit from km/h to mph
            speed_mph = round(row['Speed Limit (Km/Hr)'] * 0.621371, 1)

            # Convert Block Size from meters to feet
            block_size_ft = round(row['Block Length (m)'] * 3.28084, 1)

            # Update labels with imperial units
            self.label_widgets["Speed Limit"].setText(f"Speed Limit: {speed_mph} mph")
            self.label_widgets["Block Size"].setText(f"Block Size: {block_size_ft} ft")

            # Keep other properties the same
            self.label_widgets["Grade"].setText(f"Grade: {row['Block Grade (%)']}%")
            self.label_widgets["Elevation"].setText(f"Elevation: {row['ELEVATION (M)']} m")

            # Read infrastructure details
            infra = str(row.get('Infrastructure', '')).strip()
            light_signal = str(row.get('Light Signal', '')).strip()

            # Determine switch presence and light signal
            self.switch_label.setText(
                f"Switch Position: Present ({infra})" if "Switch" in infra else "Switch Position: None")
            self.light_signal_label.setText(f"Light Signal: {light_signal}" if light_signal else "Light Signal: None")
            self.beacon_label.setText("Beacon Signal: Present" if "Transponder" in infra else "Beacon Signal: None")
            self.station_label.setText(
                f"Station: {infra.split('Station')[-1].strip()}" if "Station" in infra else "Station: None")
            self.crossing_label.setText(
                "Railway Crossing: Present" if "RAILWAY CROSSING" in infra else "Railway Crossing: None")

    def update_track_heater(self, temp=None):
        """Update track heater based on the current temperature"""
        if temp is None:
            temp = self.temp_input.value()  # Use manual input if no argument passed

        if temp <= 32:
            self.track_heater_label.setText("Track Heater: ON")
            self.track_heater_label.setStyleSheet("color: red; font-size: 14px;")
        else:
            self.track_heater_label.setText("Track Heater: OFF")
            self.track_heater_label.setStyleSheet("color: white; font-size: 14px;")

    def check_failures(self):
        """Check failures from the testbench via socket."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.settimeout(2)  # Prevents UI from freezing if testbench isn't available
                client.connect(("localhost", 65432))  # Ensure port matches the testbench
                client.sendall(b"Request Failures")
                response = client.recv(1024).decode()

                if "Failure" in response and "No Failures" not in response:
                    self.occupancy_label.setText("Track Occupancy: ❌")
                    self.occupancy_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
                    self.file_label.setText(f"Active Failures: {response.replace('Failure: ', '')}")
                else:
                    self.occupancy_label.setText("Track Occupancy: ✅")
                    self.occupancy_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold;")
                    self.file_label.setText("No Active Failures")

                if "Temperature" in response:
                    temp_value = int(response.split("|")[-1].replace("Temperature: ", "").strip())
                    self.temp_input.setValue(temp_value)  # Update displayed temperature
                    self.update_track_heater(temp_value)  # Adjust heater based on temp

        except socket.timeout:
            print("Testbench not responding (timeout).")
        except ConnectionRefusedError:
            print("Testbench is not running. Start the testbench first!")
        except Exception as e:
            print(f"Error connecting to testbench: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TrackModelUI()
    window.show()
    sys.exit(app.exec())
