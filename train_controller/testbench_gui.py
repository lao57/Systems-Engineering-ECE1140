from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QSlider,
    QLineEdit, QGridLayout
)
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
from PyQt6.QtCore import Qt


class TestbenchGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Set Window Title
        self.setWindowTitle("Train Controller Testbench GUI")
        self.resize(800, 600)

        self.cmd_speed = 10
        self.authority = 0
        self.cur_speed = 0
        self.failure_modes = [False, False, False]
        self.underground = False
        self.cabin_temp = 0
        self.doors_status = [False, False]
        self.lights_status = [False, False]
        self.station_to_be_reached = 'Yard'
        self.world_time = {'day': 0, 'hour': 0, 'min': 0}

        self.cmd_speed_event = False
        self.authority_event = False
        self.cur_speed_event = False
        self.failure_mode_event = False
        self.underground_event = False
        self.cabin_temp_event = False
        self.doors_status_event = False
        self.lights_status_event = False
        self.station_to_be_reached_event = False
        self.world_time_event = False

        self.cmd_speed_lbl = QLabel(f"Commanded speed (m/s)", self)
        self.cmd_speed_textbox = QLineEdit(self)
        self.cmd_speed_textbox.setPlaceholderText("Enter cmd speed...")
        self.cmd_speed_textbox.setFixedWidth(200)
        self.cmd_speed_button = QPushButton("Submit", self)
        self.cmd_speed_button.setFixedWidth(100)
        self.cmd_speed_button.clicked.connect(self.update_cmd_speed)

        self.authority_lbl = QLabel(f"Authority (m)", self)
        self.authority_textbox = QLineEdit(self)
        self.authority_textbox.setPlaceholderText("Enter authority...")
        self.authority_textbox.setFixedWidth(200)
        self.authority_button = QPushButton("Submit", self)
        self.authority_button.setFixedWidth(100)
        self.authority_button.clicked.connect(self.update_authority)

        self.cur_speed_lbl = QLabel(f"Current speed (m/s)", self)
        self.cur_speed_textbox = QLineEdit(self)
        self.cur_speed_textbox.setPlaceholderText("Enter current speed...")
        self.cur_speed_textbox.setFixedWidth(200)
        self.cur_speed_button = QPushButton("Submit", self)
        self.cur_speed_button.setFixedWidth(100)
        self.cur_speed_button.clicked.connect(self.update_cur_speed)

        self.train_engine_fail_slider = QSlider(Qt.Orientation.Horizontal)
        self.train_engine_fail_slider.setMinimum(0)
        self.train_engine_fail_slider.setMaximum(1)
        self.train_engine_fail_slider.setValue(0)
        self.train_engine_fail_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.train_engine_fail_slider.setFixedWidth(40)
        self.train_engine_fail_lbl = QLabel(f"Train engine failure", self)
        self.train_engine_fail_slider.valueChanged.connect(self.update_train_engine_fail)

        self.signal_pickup_fail_slider = QSlider(Qt.Orientation.Horizontal)
        self.signal_pickup_fail_slider.setMinimum(0)
        self.signal_pickup_fail_slider.setMaximum(1)
        self.signal_pickup_fail_slider.setValue(0)
        self.signal_pickup_fail_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.signal_pickup_fail_slider.setFixedWidth(40)
        self.signal_pickup_fail_lbl = QLabel(f"Signal pickup failure", self)
        self.signal_pickup_fail_slider.valueChanged.connect(self.update_signal_pickup_fail)

        self.sbrake_fail_slider = QSlider(Qt.Orientation.Horizontal)
        self.sbrake_fail_slider.setMinimum(0)
        self.sbrake_fail_slider.setMaximum(1)
        self.sbrake_fail_slider.setValue(0)
        self.sbrake_fail_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.sbrake_fail_slider.setFixedWidth(40)
        self.sbrake_fail_lbl = QLabel(f"Service brake failure", self)
        self.sbrake_fail_slider.valueChanged.connect(self.update_sbrake_fail)

        failure_sliders_layout = QHBoxLayout()
        failure_sliders_layout.addSpacing(50)
        failure_sliders_layout.addWidget(self.train_engine_fail_slider)
        failure_sliders_layout.addSpacing(100)
        failure_sliders_layout.addWidget(self.signal_pickup_fail_slider)
        failure_sliders_layout.addSpacing(100)
        failure_sliders_layout.addWidget(self.sbrake_fail_slider)

        failure_lbl_layout = QHBoxLayout()
        failure_lbl_layout.addWidget(self.train_engine_fail_lbl)
        failure_lbl_layout.addWidget(self.signal_pickup_fail_lbl)
        failure_lbl_layout.addWidget(self.sbrake_fail_lbl)

        self.underground_slider = QSlider(Qt.Orientation.Horizontal)
        self.underground_slider.setMinimum(0)
        self.underground_slider.setMaximum(1)
        self.underground_slider.setValue(0)
        self.underground_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.underground_slider.setFixedWidth(40)
        self.underground_lbl = QLabel(f"Underground", self)
        self.underground_slider.valueChanged.connect(self.update_sbrake_fail)

        self.cabin_temp_lbl = QLabel(f"Cabin temperature (F): {self.cabin_temp}", self)
        self.cabin_temp_textbox = QLineEdit(self)
        self.cabin_temp_textbox.setPlaceholderText("Enter cabin temp...")
        self.cabin_temp_textbox.setFixedWidth(200)
        self.cabin_temp_button = QPushButton("Submit", self)
        self.cabin_temp_button.setFixedWidth(100)
        self.cabin_temp_button.clicked.connect(self.update_cabin_temp)

        self.left_door_slider = QSlider(Qt.Orientation.Horizontal)
        self.left_door_slider.setMinimum(0)
        self.left_door_slider.setMaximum(1)
        self.left_door_slider.setValue(0)
        self.left_door_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.left_door_slider.setFixedWidth(40)
        self.left_door_lbl = QLabel(f"Left door status", self)
        self.left_door_slider.valueChanged.connect(self.update_left_door_status)

        self.right_door_slider = QSlider(Qt.Orientation.Horizontal)
        self.right_door_slider.setMinimum(0)
        self.right_door_slider.setMaximum(1)
        self.right_door_slider.setValue(0)
        self.right_door_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.right_door_slider.setFixedWidth(40)
        self.right_door_lbl = QLabel(f"Right door status", self)
        self.right_door_slider.valueChanged.connect(self.update_right_door_status)

        doors_sliders_layout = QHBoxLayout()
        doors_sliders_layout.addSpacing(50)
        doors_sliders_layout.addWidget(self.left_door_slider)
        doors_sliders_layout.addSpacing(100)
        doors_sliders_layout.addWidget(self.right_door_slider)

        doors_lbl_layout = QHBoxLayout()
        doors_lbl_layout.addWidget(self.left_door_lbl)
        doors_lbl_layout.addWidget(self.right_door_lbl)

        self.in_light_slider = QSlider(Qt.Orientation.Horizontal)
        self.in_light_slider.setMinimum(0)
        self.in_light_slider.setMaximum(1)
        self.in_light_slider.setValue(0)
        self.in_light_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.in_light_slider.setFixedWidth(40)
        self.in_light_lbl = QLabel(f"Indoor light status", self)
        self.in_light_slider.valueChanged.connect(self.update_indoor_lights_status)

        self.out_light_slider = QSlider(Qt.Orientation.Horizontal)
        self.out_light_slider.setMinimum(0)
        self.out_light_slider.setMaximum(1)
        self.out_light_slider.setValue(0)
        self.out_light_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.out_light_slider.setFixedWidth(40)
        self.out_light_lbl = QLabel(f"Outdoor light status", self)
        self.out_light_slider.valueChanged.connect(self.update_outdoor_lights_status)

        lights_sliders_layout = QHBoxLayout()
        lights_sliders_layout.addSpacing(50)
        lights_sliders_layout.addWidget(self.in_light_slider)
        lights_sliders_layout.addSpacing(100)
        lights_sliders_layout.addWidget(self.out_light_slider)

        lights_lbl_layout = QHBoxLayout()
        lights_lbl_layout.addWidget(self.in_light_lbl)
        lights_lbl_layout.addWidget(self.out_light_lbl)

        self.station_name_lbl = QLabel(f"Station name", self)
        self.station_name_textbox = QLineEdit(self)
        self.station_name_textbox.setPlaceholderText("Enter station name...")
        self.station_name_textbox.setFixedWidth(200)
        self.station_name_button = QPushButton("Submit", self)
        self.station_name_button.setFixedWidth(100)
        self.station_name_button.clicked.connect(self.update_station_name)

        self.world_time_lbl = QLabel(f"World time", self)
        self.world_time_day_textbox = QLineEdit(self)
        self.world_time_hour_textbox = QLineEdit(self)
        self.world_time_min_textbox = QLineEdit(self)
        self.world_time_day_textbox.setPlaceholderText("Enter world time day...")
        self.world_time_hour_textbox.setPlaceholderText("Enter world time hours...")
        self.world_time_min_textbox.setPlaceholderText("Enter world time min...")
        self.world_time_day_textbox.setFixedWidth(200)
        self.world_time_hour_textbox.setFixedWidth(200)
        self.world_time_min_textbox.setFixedWidth(200)
        self.world_time_button = QPushButton("Submit", self)
        self.world_time_button.setFixedWidth(100)
        self.world_time_button.clicked.connect(self.update_world_time)

        world_time_text_layout = QHBoxLayout()
        world_time_text_layout.addWidget(self.world_time_day_textbox)
        world_time_text_layout.addWidget(self.world_time_hour_textbox)
        world_time_text_layout.addWidget(self.world_time_min_textbox)

        # add layout
        layout = QVBoxLayout()
        layout.addWidget(self.cmd_speed_lbl)
        layout.addWidget(self.cmd_speed_textbox)
        layout.addWidget(self.cmd_speed_button)

        layout.addWidget(self.authority_lbl)
        layout.addWidget(self.authority_textbox)
        layout.addWidget(self.authority_button)

        layout.addWidget(self.cur_speed_lbl)
        layout.addWidget(self.cur_speed_textbox)
        layout.addWidget(self.cur_speed_button)

        layout.addLayout(failure_lbl_layout)
        layout.addLayout(failure_sliders_layout)

        layout.addWidget(self.underground_lbl)
        layout.addWidget(self.underground_slider)

        layout.addWidget(self.cabin_temp_lbl)
        layout.addWidget(self.cabin_temp_textbox)
        layout.addWidget(self.cabin_temp_button)

        layout.addLayout(doors_lbl_layout)
        layout.addLayout(doors_sliders_layout)

        layout.addLayout(lights_lbl_layout)
        layout.addLayout(lights_sliders_layout)

        layout.addWidget(self.station_name_lbl)
        layout.addWidget(self.station_name_textbox)
        layout.addWidget(self.station_name_button)

        layout.addWidget(self.world_time_lbl)
        layout.addLayout(world_time_text_layout)
        layout.addWidget(self.world_time_button)

        self.setLayout(layout)

    def update_cmd_speed(self):
        self.cmd_speed = float(self.cmd_speed_textbox.text())
        self.cmd_speed_event = True

    def update_authority(self):
        self.authority = float(self.authority_textbox.text())
        self.authority_event = True

    def update_cur_speed(self):
        self.cur_speed = float(self.cur_speed_textbox.text())
        self.cur_speed_event = True

    def update_train_engine_fail(self, value):
        self.failure_modes[0] = True if value == 1 else False
        self.failure_mode_event = True

    def update_signal_pickup_fail(self, value):
        self.failure_modes[1] = True if value == 1 else False
        self.failure_mode_event = True

    def update_sbrake_fail(self, value):
        self.failure_modes[2] = True if value == 1 else False
        self.failure_mode_event = True

    def update_underground(self, value):
        self.underground = True if value == 1 else False
        self.failure_mode_event = True

    def update_cabin_temp(self):
        self.cabin_temp = float(self.cabin_temp_textbox.text())
        self.cabin_temp_event = True

    def update_left_door_status(self, value):
        self.doors_status[0] = True if value == 1 else False
        self.doors_status_event = True

    def update_right_door_status(self, value):
        self.doors_status[1] = True if value == 1 else False
        self.doors_status_event = True

    def update_indoor_lights_status(self, value):
        self.lights_status[0] = True if value == 1 else False
        self.lights_status_event = True

    def update_outdoor_lights_status(self, value):
        self.lights_status[1] = True if value == 1 else False
        self.lights_status_event = True

    def update_station_name(self):
        self.station_to_be_reached = self.station_name_textbox.text()
        self.station_to_be_reached_event = True

    def update_world_time(self):
        self.world_time['day'] = int(self.world_time_day_textbox.text())
        self.world_time['hour'] = int(self.world_time_hour_textbox.text())
        self.world_time['min'] = int(self.world_time_min_textbox.text())
        self.world_time_event = True



