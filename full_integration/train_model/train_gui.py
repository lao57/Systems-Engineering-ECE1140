import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QFileDialog, QFrame, QDial, QGroupBox, QGridLayout
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer
import train_model.train_model as train_class
import numpy as np


CABIN_HEIGHT = 11.2  # ft
CABIN_WIDTH = 8.7  # ft

station_naming = {
    '0001': "PIONEER",
    '0010': "EDGEBROOK",
    '0100': "WHITED",
    '0101': "SOUTH BANK",
    '0110': "CENTRAL",
    '0111': "INGLEWOOD",
    '1000': "OVERBROOK",
    '1001': "GLENBURY",
    '1010': "DORMONT",
    '1011': "MT LEBANON",
    '1100': "POPLAR",
    '1101': "CASTLE SHANNON",
    '0011': "STATION",
    '0000': "To be Announced",
    '1110': "EXTRA",
    '1111': "EXTRA" 
}

station_naming_red = {
    '0001': "SHADYSIDE",
    '0010': "HERRON AVE",
    '0100': "SWISSVILLE",
    '0101': "PENN STATION",
    '0110': "STEEL PLAZA",
    '0111': "FIRST AVE",
    '1000': "STATION SQUARE",
    '1001': "SOUTH HILLS JUNCTION",
    '1010': "EXTRA",
    '1011': "EXTRA",
    '1100': "EXTRA",
    '1101': "EXTRA",
    '0011': "EXTRA",
    '0000': "To be Announced",
    '1110': "EXTRA",
    '1111': "EXTRA" 
    }

class Train_GUI(QWidget):
    def __init__(self, train_model):
        super().__init__()
        self.train = train_model
        self.setWindowIcon(QIcon('group3logo.png'))  
        self.initUI()

    def initUI(self):
        # Top banner
        self.banner_frame = QFrame(self)
        self.banner_frame.setStyleSheet("background-color: #001573; height: 100px;")
        self.banner_layout = QHBoxLayout()
        self.banner_frame.setLayout(self.banner_layout)

        self.logo_label = QLabel(self)
        pixmap = QPixmap("Systems-Engineering-ECE1140/full_integration/assets/group3logo.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo_label.setPixmap(pixmap)
        self.banner_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.upload_image_button = QPushButton('Upload Image', self)
        self.upload_image_button.setStyleSheet("color: white; background-color: #333; padding: 5px; border-radius: 5px;")
        self.upload_image_button.clicked.connect(self.upload_image)
        self.banner_layout.addWidget(self.upload_image_button)

        self.banner_image_label = QLabel(self)
        self.banner_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner_layout.addWidget(self.banner_image_label)

        #self.clock_label = QLabel(self)
        #self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        #self.clock_label.setStyleSheet("font-size: 20px; color: white;")
        #self.banner_layout.addWidget(self.clock_label)

        # Initialize labels and controls first
        self.init_labels()

        # Data group boxes
        self.travel_metrics_group = self.create_group_box("Travel Metrics", [
            "Train_Beacon_ID_Label", "authority_label", "kph_velocity_label", "acceleration_label",
            "distance_travelled_label", "distance_vector_label", "speeds_vector_label",
            "underground_vector_label", "at_station_vector_label", "station_name_vector_label"
        ])

        self.passenger_group = self.create_group_box("Passenger Information", [
            "passenger_count_label", "crew_count_label", "cabin_temp_label"
        ])

        self.train_specs_group = self.create_group_box("Train Specs", [
            "weight_label", "num_cars_label", "length_label", "width_label",
            "height_label"
        ])

        self.controls_group = self.create_group_box("Controls", [
            "left_door_button", "right_door_button", "interior_light_button",
            "exterior_light_button", "ebrake_button", "velocity_dial",
            "signal_pickup_button", "brake_status_button", "engine_status_button"
        ])

        # Layout setup
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.banner_frame)
        content_layout = QGridLayout()

        content_layout.addWidget(self.travel_metrics_group, 0, 0)
        content_layout.addWidget(self.passenger_group, 1, 1)
        content_layout.addWidget(self.train_specs_group, 1, 0)
        content_layout.addWidget(self.controls_group, 0, 1)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.setWindowTitle('Group 3 || Train Model User Interface')
        self.setGeometry(300, 300, 800, 600)
        self.show()

        self.timer = QTimer()
        self.elapsed_seconds = 0

    def init_labels(self):
        # Create all labels and controls
        for name in [
            "Train_Beacon_ID_Label", "authority_label", "cabin_temp_label", "kph_velocity_label",
            "acceleration_label", "distance_travelled_label", "distance_vector_label",
            "speeds_vector_label", "underground_vector_label", "at_station_vector_label",
            "station_name_vector_label", "weight_label", "num_cars_label", "length_label", "width_label",
            "height_label","passenger_count_label", "crew_count_label"]:
            setattr(self, name, QLabel("N/A", self))

        for name in [
            "left_door_button", "right_door_button", "interior_light_button", "exterior_light_button",
            "ebrake_button", "signal_pickup_button", "brake_status_button", "engine_status_button"]:
            btn = QPushButton(name.replace("_", " ").title(), self)
            if name == "ebrake_button":
                btn.setStyleSheet("background-color: red; color: white;")
            btn.clicked.connect(getattr(self, f"toggle_{name.replace('_button','')}", lambda: None))
            setattr(self, name, btn)

        self.velocity_dial = QDial(self)
        self.velocity_dial.setRange(0, 75)
        self.velocity_dial.setNotchesVisible(True)

    def create_group_box(self, title, elements):
        group_box = QGroupBox(title)
        layout = QVBoxLayout()
        for elem in elements:
            layout.addWidget(getattr(self, elem))
        group_box.setLayout(layout)
        return group_box

    def update_train_model_GUI(self, delta_t):
        self.update_train_labels()
        #self.update_clock(delta_t)  # Update the clock each time the train is updated

    def update_train_labels(self):
        self.Train_Beacon_ID_Label.setText(f"Train Number: {self.train.train_number}")
        self.authority_label.setText(f"Authority: {self.train.authority * 3.2808399:.1f} ft")
        self.kph_velocity_label.setText(f"Velocity: {np.average([self.train.velocity, self.train.previous_velocity]) * 2.23693629:.1f} mph")
        self.velocity_dial.setValue(int(self.train.velocity * 2.23693629))  # Update the dial with the velocity
        self.acceleration_label.setText(f"Acceleration: {np.average([self.train.acceleration, self.train.previous_acceleration])*8052.97:.1f} miles/h^2")
        self.distance_travelled_label.setText(f"Distance Travelled: {self.train.distance_travelled * 3.2808399:.1f} ft")
        
        # Display only the first value of each vector
        self.distance_vector_label.setText(f"Distance Left on Block: {self.train.imperial_distance_vector[0]:.1f}")
        # self.speeds_vector_label.setText(f"Speed Limit: {(float(self.train.speeds_vector[0])*0.62137119):.1f} mph")
        self.speeds_vector_label.setText(f"Speed Limit: {(float(self.train.speeds_vector[0]) * 2.23694):.1f} mph")
        if self.train.underground_vector[0] == '1':
            self.underground_vector_label.setText(f"Underground")
        else:
            self.underground_vector_label.setText(f"Above Ground")
        if self.train.at_station_vector[0] == '1':
            self.at_station_vector_label.setText(f"At Station")
        else:
            self.at_station_vector_label.setText(f"Not at Station")
        if self.train.announcement == True:
            if self.train.line == 'red':
                self.station_name_vector_label.setText(f"Now Arriving at: {station_naming_red[self.train.Next_station_names[0]]}")
            else:
                self.station_name_vector_label.setText(f"Now Arriving at: {station_naming[self.train.Next_station_names[0]]}")
        else:
            if self.train.line == 'red':
                self.station_name_vector_label.setText(f"Next Station: {station_naming_red[self.train.Next_station_names[0]]}")
            else:
                self.station_name_vector_label.setText(f"Next Station: {station_naming[self.train.Next_station_names[0]]}")
        
        # Update the new labels
        self.weight_label.setText(f"Weight: {int(self.train.weight_imperial)} lbs")
        self.num_cars_label.setText(f"Number of Carts: {self.train.numberOfCars}")
        self.length_label.setText(f"Length: {int(self.train.length_imperial)} ft")
        self.width_label.setText(f"Width: {CABIN_WIDTH} ft")
        self.height_label.setText(f"Height: {CABIN_HEIGHT} ft")
        # Update passenger count and crew count
        self.passenger_count_label.setText(f"Passenger Count: {self.train.passenger_count}")
        self.crew_count_label.setText(f"Crew Count: {self.train.crew_count}")
        # Update cabin temperature
        self.cabin_temp_label.setText(f"Cabin Temperature: {self.train.cabin_temp:.1f} °F")
        
        self.toggle_left_door()
        self.toggle_right_door()
        self.toggle_interior_light()
        self.toggle_exterior_light()

    # Function to upload and display an image on the banner
    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload Banner Image", "", "Images (*.png *.xpm *.jpg);;All Files (*)")
        if file_name:
            pixmap = QPixmap(file_name)
            pixmap = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)  # Scale image to fit the banner
            self.banner_image_label.setPixmap(pixmap)
            self.upload_image_button.deleteLater()  # Delete the button after clicking

    # Function to update the clock
    def update_clock(self, deltaT):
        self.elapsed_seconds += deltaT
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.clock_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")



    """Should not really be toggleable just want to get it running first"""
    # TOGGLABLES
    def toggle_left_door(self):
        self.left_door_button.setText(f"Left Door: {'Open' if self.train.doors_status[0] else 'Closed'}")

    def toggle_right_door(self):
        self.right_door_button.setText(f"Right Door: {'Open' if self.train.doors_status[1] else 'Closed'}")

    def toggle_interior_light(self):
        self.interior_light_button.setText(f"Interior Light: {'On' if self.train.lights_status[0] else 'Off'}")

    def toggle_exterior_light(self):
        self.exterior_light_button.setText(f"Exterior Light: {'On' if self.train.lights_status[1] else 'Off'}")

    def toggle_ebrake(self):
        self.train.ebrake_gui_signal = not self.train.ebrake_gui_signal
        self.ebrake_button.setText(f"Emergency Brake: {'Engaged' if self.train.ebrake_gui_signal else 'Disengaged'}")



    """ Functions for failures
    
    self.failure_modes = [False, False, False]  # [train engine failure, signal pickup failure, brake failure]
    
    """
    # Function to toggle signal pickup
    def toggle_signal_pickup(self):
        self.train.failure_modes[1] = not self.train.failure_modes[1]
        self.signal_pickup_button.setText(f"Signal Pickup Status: {'Failure' if self.train.failure_modes[1] else 'Normal'}")

    # Function to toggle brake status
    def toggle_brake_status(self):
        self.train.failure_modes[2] = not self.train.failure_modes[2]
        self.brake_status_button.setText(f"Brake Status: {'Failure' if self.train.failure_modes[2] else 'Normal'}")

    # Function to toggle engine status
    def toggle_engine_status(self):
        self.train.failure_modes[0] = not self.train.failure_modes[0]
        self.engine_status_button.setText(f"Engine Status: {'Failure' if self.train.failure_modes[0] else 'Normal'}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Train_GUI()
    sys.exit(app.exec())