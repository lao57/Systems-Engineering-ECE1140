from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QSlider,
    QLineEdit
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt


class TrainControllerGUI(QWidget):
    def __init__(self, k_p, k_i):
        super().__init__()

        # Set Window Title
        self.setWindowTitle("Train Controller GUI")
        self.resize(800, 600)

        # Set Background Color to Blue
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ADD8E6"))  # Light Blue
        self.setPalette(palette)

        self.world_time = {'day': 0, 'hour': 0, 'min': 0}
        self.train_controller_mode = 'Automatic'
        self.cmd_power = 0
        self.cur_speed = 0
        self.cmd_speed = 0
        self.driver_speed = 0
        self.k_p = k_p
        self.k_i = k_i
        self.most_recent_station = None
        self.announcement = False
        self.doors_status = [False, False]  # [left_doors_open, right_doors_open]
        self.lights_status = [False, False]  # [interior_lights_open, exterior_lights_open]
        self.underground = False
        self.cur_cabin_temp = None
        self.e_brake_on = False
        self.service_brake_on = False

        # create widgets
        self.world_time_lbl = QLabel(f"World time (24-hr): Day {self.world_time['day']} "
                                     f"{self.world_time['hour']:02d}:{self.world_time['min']:02d}", self)
        self.power_gain_lbl = QLabel(f"Power delivered (W): {self.cmd_power}", self)
        self.cur_speed_lbl = QLabel(f"Current speed (mi/h): {self.cur_speed}", self)
        self.cmd_speed_lbl = QLabel(f"Commanded speed (mi/h): {self.cmd_speed}", self)

        self.p_gain_lbl = QLabel(f"K_P (Proportional gain): {k_p}", self)
        self.i_gain_lbl = QLabel(f"K_I (Integral gain): {k_i}", self)

        self.station_lbl = QLabel(f"Most recent station: {self.most_recent_station}", self)
        self.announcement_lbl = QLabel(f"Time to announce: {self.announcement}", self)
        self.left_door_status_lbl = QLabel(f"Left door open: {'Open' if self.doors_status[0] else 'Closed'}", self)
        self.right_door_status_lbl = QLabel(f"Left door open: {'Open' if self.doors_status[1] else 'Closed'}", self)
        self.in_light_status_lbl = QLabel(f"Indoor light on: {'On' if self.lights_status[0] else 'Off'}", self)
        self.out_light_status_lbl = QLabel(f"Outdoor light on: {'On' if self.doors_status[1] else 'Off'}", self)
        self.underground_lbl = QLabel(f"Underground: {'True' if self.underground else 'False'}", self)
        self.cur_cabin_temp_lbl = QLabel(f"Current cabin temp (F): {self.cur_cabin_temp}", self)
        self.e_brake_lbl = QLabel(f"E brake on: {'True' if self.e_brake_on else 'False'}", self)
        self.s_brake_lbl = QLabel(f"Service brake on: {'True' if self.service_brake_on else 'False'}", self)

        # Auto/manual train controller mode
        self.tc_mode_slider = QSlider(Qt.Orientation.Horizontal)
        self.tc_mode_slider.setMinimum(0)
        self.tc_mode_slider.setMaximum(1)
        self.tc_mode_slider.setValue(0)
        self.tc_mode_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.tc_mode_slider.setFixedWidth(80)
        self.tc_mode_lbl = QLabel(self.train_controller_mode)
        self.tc_mode_slider.valueChanged.connect(self.update_train_controller_mode)

        # Train Driver commanded speed
        self.driver_speed_lbl = QLabel(f"Driver Commanded speed (if in automatic mode): {self.driver_speed}", self)
        self.driver_speed_textbox = QLineEdit(self)
        self.driver_speed_textbox.setPlaceholderText("Type here...")
        self.driver_speed_button = QPushButton("Submit", self)
        self.driver_speed_button.clicked.connect(self.update_commanded_speed)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.world_time_lbl)
        layout.addWidget(self.tc_mode_slider)
        layout.addWidget(self.tc_mode_lbl)

        layout.addWidget(self.driver_speed_lbl)
        layout.addWidget(self.driver_speed_textbox)
        layout.addWidget(self.driver_speed_button)

        layout.addWidget(self.power_gain_lbl)
        layout.addWidget(self.cur_speed_lbl)
        layout.addWidget(self.cmd_speed_lbl)

        layout.addWidget(self.p_gain_lbl)
        layout.addWidget(self.i_gain_lbl)

        layout.addWidget(self.station_lbl)
        layout.addWidget(self.announcement_lbl)
        layout.addWidget(self.left_door_status_lbl)
        layout.addWidget(self.right_door_status_lbl)
        layout.addWidget(self.in_light_status_lbl)
        layout.addWidget(self.out_light_status_lbl)
        layout.addWidget(self.underground_lbl)
        layout.addWidget(self.cur_cabin_temp_lbl)
        layout.addWidget(self.e_brake_lbl)
        layout.addWidget(self.s_brake_lbl)

        self.setLayout(layout)

    def update_world_time(self, world_time):
        self.world_time = world_time
        self.world_time_lbl.setText(f"World time (24-hr): {self.world_time['hour']:02d}:{self.world_time['min']:02d}")

    def update_power_cmd(self, power):
        self.cmd_power = power
        self.power_gain_lbl.setText(f"Power delivered (W): {self.cmd_power}")

    def update_controller_gains(self, k_p, k_i):
        self.k_p = k_p
        self.k_i = k_i
        self.p_gain_lbl.setText(f"K_P (Proportional gain): {self.k_p}")
        self.i_gain_lbl.setText(f"K_I (Proportional gain): {self.k_i}")

    def update_most_recent_station(self, station_name):
        self.most_recent_station = station_name
        self.station_lbl.setText(f"Most recent station: {self.most_recent_station}")

    def update_doors_status(self, doors_status):
        self.doors_status = doors_status
        self.station_lbl.setText(f"K_I ((Proportional gain): {self.k_i}")

    def update_lights_status(self, lights_status):
        self.lights_status = lights_status
        self.in_light_status_lbl.setText(f"Indoor light on: {'On' if self.lights_status[0] else 'Off'}")

    def update_cur_speed(self, cur_speed):
        self.cur_speed = cur_speed
        self.cur_speed_lbl.setText(f"Current speed (mi/h): {self.cur_speed}")

    def update_cmd_speed(self, cmd_speed):
        self.cmd_speed = cmd_speed
        self.cmd_speed_lbl.setText(f"Commanded speed (mi/h): {self.cmd_speed}")

    def update_train_controller_mode(self, value):
        if value == 0:
            self.train_controller_mode = "Automatic"
            self.tc_mode_slider.setValue(0)
            self.tc_mode_lbl.setText(self.train_controller_mode)
        else:
            self.train_controller_mode = "Manual"
            self.tc_mode_slider.setValue(1)
            self.tc_mode_lbl.setText(self.train_controller_mode)

    def update_commanded_speed(self):
        """Train driver should be able to changed cmd_speed in manual mode."""
        self.driver_speed = float(self.driver_speed_textbox.text())
        self.driver_speed_lbl.setText(f"Driver Commanded speed (if in automatic mode): {self.driver_speed}")
