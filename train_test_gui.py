import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout
import train_class

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.train = None
        self.initUI()

    def initUI(self):


        ####################################################################################################################
        """
        Create the input fields for vairables to store text input
        """
        ####################################################################################################################
        # Create input fields for train initialization
        self.train_number_input = QLineEdit(self)
        self.number_of_passengers_input = QLineEdit(self)
        self.beacon_input = QLineEdit(self)
        self.baud_input = QLineEdit(self)





        ####################################################################################################################
        """
        Create the Buttons
        """
        ####################################################################################################################
        
        # Create button to initialize train
        self.init_train_button = QPushButton('Initialize Train', self)
        self.init_train_button.clicked.connect(self.initialize_train)

        # Create button to parse beacon
        self.parse_beacon_button = QPushButton('Parse Beacon', self)
        self.parse_beacon_button.clicked.connect(self.parse_beacon)

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




        ####################################################################################################################
        """
        Create the labels
        """
        ####################################################################################################################
        
        # Create labels for input fields
        self.train_number_label = QLabel("Train Number:", self)
        self.number_of_passengers_label = QLabel("Number of Passengers:", self)
        self.beacon_input_label = QLabel("Beacon:", self)
        self.baud_input_label = QLabel("Baud Line:", self)
        
        # Create labels for train variables
        self.Train_Beacon_ID_Label = QLabel("Baud ID: 0", self)
        self.authority_label = QLabel("authority(m): 0", self)
        self.velocity_label = QLabel("Velocity: N/A", self)
        self.kph_velocity_label = QLabel("Velocity(KPH): N/A", self)
        self.acceleration_label = QLabel("Acceleration: N/A", self)
        self.distance_travelled_label = QLabel("Distance Travelled: N/A", self)
        self.distance_vector_label = QLabel("Distance Vector: N/A", self)
        self.speeds_vector_label = QLabel("Speeds Vector: N/A", self)
        self.underground_vector_label = QLabel("Underground Vector: N/A", self)
        self.at_station_vector_label = QLabel("At Station Vector: N/A", self)
        self.extra_bit_vector_label = QLabel("Extra Bit Vector: N/A", self)

        ####################################################################################################################
        """
        GUI Layout
        """
        ####################################################################################################################
       

        # Layout for input fields
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.train_number_label)
        input_layout.addWidget(self.train_number_input)
        input_layout.addWidget(self.number_of_passengers_label)
        input_layout.addWidget(self.number_of_passengers_input)
        input_layout.addWidget(self.init_train_button)
        input_layout.addWidget(self.beacon_input_label)
        input_layout.addWidget(self.beacon_input)
        input_layout.addWidget(self.parse_beacon_button)
        input_layout.addWidget(self.baud_input_label)
        input_layout.addWidget(self.baud_input)




        # Layout for train variables
        train_layout = QVBoxLayout()
        input_layout.addWidget(self.authority_label)
        input_layout.addWidget(self.Train_Beacon_ID_Label)
        train_layout.addWidget(self.velocity_label)
        train_layout.addWidget(self.kph_velocity_label)
        train_layout.addWidget(self.acceleration_label)
        train_layout.addWidget(self.distance_travelled_label)
        train_layout.addWidget(self.distance_vector_label)
        train_layout.addWidget(self.speeds_vector_label)
        train_layout.addWidget(self.underground_vector_label)
        train_layout.addWidget(self.at_station_vector_label)
        train_layout.addWidget(self.extra_bit_vector_label)
        train_layout.addWidget(self.update_train_button)

        # Layout for train controls
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.left_door_button)
        control_layout.addWidget(self.right_door_button)
        control_layout.addWidget(self.interior_light_button)
        control_layout.addWidget(self.exterior_light_button)
        control_layout.addWidget(self.ebrake_button)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addLayout(train_layout)
        main_layout.addLayout(control_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('PyQt5 GUI with Train Variables')
        self.setGeometry(300, 300, 600, 400)
        self.show()


    ####################################################################################################################
    """
    Button Functions
    """
    ####################################################################################################################
       

    def initialize_train(self):
        if self.train_number_input.text() == "":
            train_number = 1
        else:
            train_number = int(self.train_number_input.text())
        if self.number_of_passengers_input.text() == "":
            number_of_passengers = 3
        else:
            number_of_passengers = int(self.number_of_passengers_input.text())

        self.train = train_class.Train(train_number, number_of_passengers)
        self.update_train_labels()
        self.update_train_button.setEnabled(True)  # Enable update button
        self.parse_beacon_button.setEnabled(True)  # Enable parse beacon button
        self.left_door_button.setEnabled(True)
        self.right_door_button.setEnabled(True)
        self.interior_light_button.setEnabled(True)
        self.exterior_light_button.setEnabled(True)
        self.ebrake_button.setEnabled(True)

    def parse_beacon(self):
        beacon = self.beacon_input.text()
        self.train.beacon_parse(beacon)
        self.update_train_labels()

    def update_train(self):
        self.train.baud_read(self.baud_input.text())
        self.train.update_train(120, 0)
        self.update_train_labels()

    def update_train_labels(self):
        self.Train_Beacon_ID_Label.setText(f"Baud ID: {self.train.Baud_ID}")
        self.authority_label.setText(f"Authority: {self.train.authority} m")
        self.velocity_label.setText(f"Velocity: {self.train.velocity} m/s")
        self.kph_velocity_label.setText(f"Velocity(KPH): {self.train.velocity * 3.6} km/h")
        self.acceleration_label.setText(f"Acceleration: {self.train.acceleration} m/s^2")
        self.distance_travelled_label.setText(f"Distance Travelled: {self.train.distance_travelled} m")
        self.distance_vector_label.setText(f"Distance Vector: {self.train.distance_vector}")
        self.speeds_vector_label.setText(f"Speeds Vector: {self.train.speeds_vector}")
        self.underground_vector_label.setText(f"Underground Vector: {self.train.underground_vector}")
        self.at_station_vector_label.setText(f"At Station Vector: {self.train.at_station_vector}")
        self.extra_bit_vector_label.setText(f"Extra Bit Vector: {self.train.extra_bit_vector}")




    #TOGGLABLES
    def toggle_left_door(self):
        self.train.left_door = not self.train.left_door
        self.left_door_button.setText(f"Left Door: {'Open' if self.train.left_door else 'Closed'}")

    def toggle_right_door(self):
        self.train.right_door = not self.train.right_door
        self.right_door_button.setText(f"Right Door: {'Open' if self.train.right_door else 'Closed'}")

    def toggle_interior_light(self):
        self.train.interior_light = not self.train.interior_light
        self.interior_light_button.setText(f"Interior Light: {'On' if self.train.interior_light else 'Off'}")

    def toggle_exterior_light(self):
        self.train.exterior_light = not self.train.exterior_light
        self.exterior_light_button.setText(f"Exterior Light: {'On' if self.train.exterior_light else 'Off'}")

    def toggle_ebrake(self):
        self.train.ebrake_signal = not self.train.ebrake_signal
        self.ebrake_button.setText(f"Emergency Brake: {'Engaged' if self.train.ebrake_signal else 'Disengaged'}")


#################################################################################################################################################
"""
MAIN FUNCTION
"""
#################################################################################################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
    #000011010111010100110100101111UVSZE3