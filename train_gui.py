import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QFileDialog, QFrame, QDial
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
import train_class

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.train = None
        self.elapsed_seconds = 0  # Initialize elapsed time
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

        # Create button to initialize train
        self.init_train_button = QPushButton('Initialize Train', self)
        self.init_train_button.clicked.connect(self.initialize_train)

        # Create button to update train
        self.update_train_button = QPushButton('Update Train', self)
        self.update_train_button.clicked.connect(self.update_train)
        self.update_train_button.setEnabled(False)  # Disable until train is initialized

        # Create toggle buttons for train controls
        self.left_door_button = QPushButton('Toggle Left Door', self)
        self.left_door_button.clicked.connect(self.toggle_left_door)
        self.left_door_button.setEnabled(False)

        self.right_door_button = QPushButton('Toggle Right Door', self)
        self.right_door_button.clicked.connect(self.toggle_right_door)
        self.right_door_button.setEnabled(False)

        self.interior_light_button = QPushButton('Toggle Interior Light', self)
        self.interior_light_button.clicked.connect(self.toggle_interior_light)
        self.interior_light_button.setEnabled(False)

        self.exterior_light_button = QPushButton('Toggle Exterior Light', self)
        self.exterior_light_button.clicked.connect(self.toggle_exterior_light)
        self.exterior_light_button.setEnabled(False)

        self.ebrake_button = QPushButton('Emergency Brake', self)
        self.ebrake_button.setStyleSheet("background-color: red")
        self.ebrake_button.clicked.connect(self.toggle_ebrake)
        self.ebrake_button.setEnabled(False)

        # Create toggle buttons for new train controls
        self.signal_pickup_button = QPushButton('Toggle Signal Pickup', self)
        self.signal_pickup_button.clicked.connect(self.toggle_signal_pickup)
        self.signal_pickup_button.setEnabled(False)

        self.brake_status_button = QPushButton('Toggle Brake Status', self)
        self.brake_status_button.clicked.connect(self.toggle_brake_status)
        self.brake_status_button.setEnabled(False)

        self.engine_status_button = QPushButton('Toggle Engine Status', self)
        self.engine_status_button.clicked.connect(self.toggle_engine_status)
        self.engine_status_button.setEnabled(False)

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
        self.extra_bit_vector_label = QLabel("Next Station: N/A", self)
        
        # Add new labels for weight, number of carts, and length of the train
        self.weight_label = QLabel("Weight: N/A", self)
        self.num_carts_label = QLabel("Number of Carts: N/A", self)
        self.length_label = QLabel("Length: N/A", self)

        # Create a dial for velocity
        self.velocity_dial = QDial(self)
        self.velocity_dial.setRange(0, 75)  # Assuming max velocity is 70 mph
        self.velocity_dial.setNotchesVisible(True)
        self.velocity_dial.setEnabled(False)

        # Layout for input fields
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.init_train_button)

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
        train_layout.addWidget(self.extra_bit_vector_label)
        train_layout.addWidget(self.weight_label)  # Add the new labels
        train_layout.addWidget(self.num_carts_label)
        train_layout.addWidget(self.length_label)
        train_layout.addWidget(self.update_train_button)

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
        self.timer.timeout.connect(self.update_train)

    def initialize_train(self):
        train_number = 1
        number_of_passengers = 3

        self.train = train_class.Train(train_number, number_of_passengers)
        self.train.beacon_parse("0000000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010010110110110110110110110110110100000000000000000011NONENONENONENONENONEStaBStaBStaBStaBStaB", [0,0,0,0,0,0,0,0,0,0], [1,2,3,4,5,6,7,8,9,10])
        self.update_train_labels()
        self.left_door_button.setEnabled(True)
        self.right_door_button.setEnabled(True)
        self.interior_light_button.setEnabled(True)
        self.exterior_light_button.setEnabled(True)
        self.ebrake_button.setEnabled(True)
        self.velocity_dial.setEnabled(True)  # Enable the dial
        self.signal_pickup_button.setEnabled(True)
        self.brake_status_button.setEnabled(True)
        self.engine_status_button.setEnabled(True)

        # Start the timer to update the train every second
        self.timer.start(1000)

    def update_train(self):
        self.train.baud_read("0000101111")
        self.train.update_train(120)
        self.update_train_labels()
        self.update_clock()  # Update the clock each time the train is updated

    def update_train_labels(self):
        self.Train_Beacon_ID_Label.setText(f"Baud ID: {self.train.Baud_ID}")
        self.authority_label.setText(f"Authority: {self.train.authority * 3.2808399:.1f} ft")
        self.kph_velocity_label.setText(f"Velocity: {self.train.velocity * 2.23693629:.1f} mph")
        self.velocity_dial.setValue(int(self.train.velocity * 2.23693629))  # Update the dial with the velocity
        self.acceleration_label.setText(f"Acceleration: {self.train.acceleration * 0.81:.1f} miles/h^2")
        self.distance_travelled_label.setText(f"Distance Travelled: {self.train.distance_travelled * 3.2808399:.1f} ft")
        
        # Display only the first value of each vector
        self.distance_vector_label.setText(f"Distance Vector: {self.train.imperial_distance_vector[0]:.1f}")
        self.speeds_vector_label.setText(f"Speeds Vector: {self.train.speeds_vector[0]:.1f}")
        self.underground_vector_label.setText(f"Underground Vector: {self.train.underground_vector[0]}")
        self.at_station_vector_label.setText(f"At Station Vector: {self.train.at_station_vector[0]}")
        self.extra_bit_vector_label.setText(f"Next Station: {self.train.extra_bit_vector[0]}")
        
        # Update the new labels
        self.weight_label.setText(f"Weight: {int(self.train.weight_imperial)} lbs")
        self.num_carts_label.setText(f"Number of Carts: {self.train.numberOfCarts}")
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
    def update_clock(self):
        self.elapsed_seconds += 1
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.clock_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    # TOGGLABLES
    def toggle_left_door(self):
        self.left_door_button.setText(f"Left Door: {'Open' if self.train.left_door else 'Closed'}")

    def toggle_right_door(self):
        self.right_door_button.setText(f"Right Door: {'Open' if self.train.right_door else 'Closed'}")

    def toggle_interior_light(self):
        self.interior_light_button.setText(f"Interior Light: {'On' if self.train.interior_light else 'Off'}")

    def toggle_exterior_light(self):
        self.exterior_light_button.setText(f"Exterior Light: {'On' if self.train.exterior_light else 'Off'}")

    def toggle_ebrake(self):
        self.train.ebrake_signal = not self.train.ebrake_signal
        self.ebrake_button.setText(f"Emergency Brake: {'Engaged' if self.train.ebrake_signal else 'Disengaged'}")

    # Function to toggle signal pickup
    def toggle_signal_pickup(self):
        self.train.signal_pickup = not self.train.signal_pickup
        self.signal_pickup_button.setText(f"Signal Pickup: {'On' if self.train.signal_pickup else 'Off'}")

    # Function to toggle brake status
    def toggle_brake_status(self):
        self.train.brake_status = not self.train.brake_status
        self.brake_status_button.setText(f"Brake Status: {'Engaged' if self.train.brake_status else 'Disengaged'}")

    # Function to toggle engine status
    def toggle_engine_status(self):
        self.train.engine_status = not self.train.engine_status
        self.engine_status_button.setText(f"Engine Status: {'On' if self.train.engine_status else 'Off'}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())