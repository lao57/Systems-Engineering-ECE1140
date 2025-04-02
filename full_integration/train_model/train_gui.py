import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QFileDialog, QFrame, QDial
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
import train_model.train_model as train_class

class Train_GUI(QWidget):
    def __init__(self, train_model):
        super().__init__()
        self.train = train_model
        self.initUI()

    def initUI(self):
        # Create the blue banner at the top
        self.banner_frame = QFrame(self)
        self.banner_frame.setStyleSheet("background-color: #001573; height: 100px;")
        self.banner_layout = QHBoxLayout()
        self.banner_frame.setLayout(self.banner_layout)

        # Add the group3logo.png image to the top left
        self.logo_label = QLabel(self)
        pixmap = QPixmap("group3logo.png")
        pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)  # Scale image to fit the banner
        self.logo_label.setPixmap(pixmap)
        self.banner_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignLeft)

        # Create an upload image button for the banner
        self.upload_image_button = QPushButton('Upload Image', self)
        self.upload_image_button.setStyleSheet("color: white; background-color: #333; padding: 5px; border-radius: 5px;")
        self.upload_image_button.clicked.connect(self.upload_image)
        self.banner_layout.addWidget(self.upload_image_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Create a label to hold the uploaded image
        self.banner_image_label = QLabel(self)
        self.banner_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner_layout.addWidget(self.banner_image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Create a clock label
        self.clock_label = QLabel(self)
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet("font-size: 20px; color: white;")
        self.banner_layout.addWidget(self.clock_label, alignment=Qt.AlignmentFlag.AlignRight)
        self.elapsed_seconds = 0

        # Create toggle buttons for train controls
        self.left_door_button = QPushButton('Toggle Left Door', self)
        self.left_door_button.clicked.connect(self.toggle_left_door)
        self.left_door_button.setEnabled(True)

        self.right_door_button = QPushButton('Toggle Right Door', self)
        self.right_door_button.clicked.connect(self.toggle_right_door)
        self.right_door_button.setEnabled(True)

        self.interior_light_button = QPushButton('Toggle Interior Light', self)
        self.interior_light_button.clicked.connect(self.toggle_interior_light)
        self.interior_light_button.setEnabled(True)

        self.exterior_light_button = QPushButton('Toggle Exterior Light', self)
        self.exterior_light_button.clicked.connect(self.toggle_exterior_light)
        self.exterior_light_button.setEnabled(True)

        self.ebrake_button = QPushButton('Emergency Brake', self)
        self.ebrake_button.setStyleSheet("background-color: red")
        self.ebrake_button.clicked.connect(self.toggle_ebrake)
        self.ebrake_button.setEnabled(True)

        # Create toggle buttons for new train controls
        self.signal_pickup_button = QPushButton('Toggle Signal Pickup', self)
        self.signal_pickup_button.clicked.connect(self.toggle_signal_pickup)
        self.signal_pickup_button.setEnabled(True)

        self.brake_status_button = QPushButton('Toggle Brake Status', self)
        self.brake_status_button.clicked.connect(self.toggle_brake_status)
        self.brake_status_button.setEnabled(True)

        self.engine_status_button = QPushButton('Toggle Engine Status', self)
        self.engine_status_button.clicked.connect(self.toggle_engine_status)
        self.engine_status_button.setEnabled(True)

        # Create labels for train variables
        self.Train_Beacon_ID_Label = QLabel("Baud ID: 0", self)
        self.authority_label = QLabel("authority(m): 0", self)
        self.kph_velocity_label = QLabel("Velocity(KPH): N/A", self)
        self.acceleration_label = QLabel("Acceleration: N/A", self)
        self.distance_travelled_label = QLabel("Distance Travelled: N/A", self)
        self.distance_vector_label = QLabel("Distance Vector: N/A", self)
        self.speeds_vector_label = QLabel("Speeds Vector: N/A", self)
        self.underground_vector_label = QLabel("Underground Vector: N/A", self)
        self.at_station_vector_label = QLabel("At Station Vector: N/A", self)
        self.station_name_vector_label = QLabel("Next Station: N/A", self)
        
        # Add new labels for weight, number of carts, and length of the train
        self.weight_label = QLabel("Weight: N/A", self)
        self.num_cars_label = QLabel("Number of Carts: N/A", self)
        self.length_label = QLabel("Length: N/A", self)

        # Create a dial for velocity
        self.velocity_dial = QDial(self)
        self.velocity_dial.setRange(0, 75)  # Assuming max velocity is 70 mph
        self.velocity_dial.setNotchesVisible(True)
        self.velocity_dial.setEnabled(True)

        # Layout for input fields
        input_layout = QVBoxLayout()

        # Layout for train variables
        train_layout = QVBoxLayout()
        input_layout.addWidget(self.authority_label)
        input_layout.addWidget(self.Train_Beacon_ID_Label)
        train_layout.addWidget(self.kph_velocity_label) #now mph
        train_layout.addWidget(self.acceleration_label)
        train_layout.addWidget(self.distance_travelled_label)
        train_layout.addWidget(self.distance_vector_label)
        train_layout.addWidget(self.speeds_vector_label)
        train_layout.addWidget(self.underground_vector_label)
        train_layout.addWidget(self.at_station_vector_label)
        train_layout.addWidget(self.station_name_vector_label)
        train_layout.addWidget(self.weight_label)  # Add the new labels
        train_layout.addWidget(self.num_cars_label)
        train_layout.addWidget(self.length_label)

        # Layout for train controls
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.left_door_button)
        control_layout.addWidget(self.right_door_button)
        control_layout.addWidget(self.interior_light_button)
        control_layout.addWidget(self.exterior_light_button)
        control_layout.addWidget(self.ebrake_button)
        control_layout.addWidget(self.velocity_dial)  # Add the dial to the control layout
        control_layout.addWidget(self.signal_pickup_button)  # Add the new buttons
        control_layout.addWidget(self.brake_status_button)
        control_layout.addWidget(self.engine_status_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.banner_frame)  # Add the banner first
        content_layout = QHBoxLayout()
        content_layout.addLayout(input_layout)
        content_layout.addLayout(train_layout)
        content_layout.addLayout(control_layout)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('Train GUI')
        self.setGeometry(300, 300, 600, 400)
        self.show()

        # Initialize the timer
        self.timer = QTimer()

    def update_train_model_GUI(self, delta_t):
        self.update_train_labels()
        self.update_clock(delta_t)  # Update the clock each time the train is updated

    def update_train_labels(self):
        self.Train_Beacon_ID_Label.setText(f"Train Number: {self.train.train_number}")
        self.authority_label.setText(f"Authority: {self.train.authority * 3.2808399:.1f} ft")
        self.kph_velocity_label.setText(f"Velocity: {self.train.velocity * 2.23693629:.1f} mph")
        self.velocity_dial.setValue(int(self.train.velocity * 2.23693629))  # Update the dial with the velocity
        self.acceleration_label.setText(f"Acceleration: {self.train.acceleration * 0.81:.1f} miles/h^2")
        self.distance_travelled_label.setText(f"Distance Travelled: {self.train.distance_travelled * 3.2808399:.1f} ft")
        
        # Display only the first value of each vector
        self.distance_vector_label.setText(f"Distance Left on Block: {self.train.imperial_distance_vector[0]:.1f}")
        self.speeds_vector_label.setText(f"Speed Limit: {self.train.speeds_vector[0]:.1f}")
        self.underground_vector_label.setText(f"Underground(1 = yes): {self.train.underground_vector[0]}")
        self.at_station_vector_label.setText(f"At Station(1 = yes): {self.train.at_station_vector[0]}")
        if self.train.announcement == True:
            self.station_name_vector_label.setText(f"Now Arriving at: {self.train.Next_station_names[0]}")
        self.station_name_vector_label.setText(f"Next Station: {self.train.Next_station_names[0]}")
        
        # Update the new labels
        self.weight_label.setText(f"Weight: {int(self.train.weight_imperial)} lbs")
        self.num_cars_label.setText(f"Number of Carts: {self.train.numberOfCars}")
        self.length_label.setText(f"Length: {int(self.train.length_imperial)} ft")
        
        self.toggle_left_door()
        self.toggle_right_door()
        self.toggle_interior_light()
        self.toggle_exterior_light()

    # Function to upload and display an image on the banner
    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload Banner Image", "", "Images (*.png *.xpm *.jpg);;All Files (*)")
        if file_name:
            pixmap = QPixmap(file_name)
            pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)  # Scale image to fit the banner
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