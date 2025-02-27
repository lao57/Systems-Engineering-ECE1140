from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QSlider,
    QLineEdit, QGridLayout
)
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
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
        self.authority = 1000
        self.k_p = k_p
        self.k_i = k_i
        self.most_recent_station = 'Yard'
        self.speed_limit = 0
        self.announcement = False
        self.doors_status = [False, False]  # [left_doors_open, right_doors_open]
        self.lights_status = [False, False]  # [interior_lights_open, exterior_lights_open]
        self.underground = False
        self.cur_cabin_temp = 0.00
        self.e_brake_on = False
        self.service_brake_decel = 0.0
        self.max_sbrake_decel = 1.2  # 1.2 m/s
        self.failure_modes = [False, False, False]

        # create widgets
        self.world_time_lbl = QLabel(f"World time (24-hr): Day {self.world_time['day']} "
                                     f"{self.world_time['hour']:02d}:{self.world_time['min']:02d}", self)

        self.power_gain_lbl = QLabel(f"Power delivered (W): {self.cmd_power}", self)
        self.cur_speed_lbl = QLabel(f"Current speed (m/s): {self.cur_speed}", self)
        self.cmd_speed_lbl = QLabel(f"Commanded speed (m/s): {self.cmd_speed}", self)
        self.speed_limit_lbl = QLabel(f"Speed limit (m/s): {self.speed_limit}", self)
        self.authority_lbl = QLabel(f"Authority (m): {self.authority:.2f}", self)
        self.p_gain_lbl = QLabel(f"K_P (Proportional gain): {k_p}", self)
        self.i_gain_lbl = QLabel(f"K_I (Integral gain): {k_i}", self)

        self.train_engine_fail_icon = QLabel(self)
        self.train_engine_fail_lbl = QLabel(f"Train engine failure", self)
        self.signal_pickup_fail_icon = QLabel(self)
        self.signal_pickup_fail_lbl = QLabel(f"Signal pickup failure", self)
        self.sbrake_fail_icon = QLabel(self)
        self.sbrake_fail_lbl = QLabel(f"Service brake failure", self)
        self.update_failure_modes(self.failure_modes)

        failure_icons_layout = QHBoxLayout()
        failure_icons_layout.addSpacing(50)
        failure_icons_layout.addWidget(self.train_engine_fail_icon)
        failure_icons_layout.addSpacing(100)
        failure_icons_layout.addWidget(self.signal_pickup_fail_icon)
        failure_icons_layout.addSpacing(100)
        failure_icons_layout.addWidget(self.sbrake_fail_icon)

        failure_lbl_layout = QHBoxLayout()
        failure_icons_layout.addSpacing(50)
        failure_lbl_layout.addWidget(self.train_engine_fail_lbl)
        failure_lbl_layout.addWidget(self.signal_pickup_fail_lbl)
        failure_lbl_layout.addWidget(self.sbrake_fail_lbl)

        self.station_lbl = QLabel(f"Most recent station: {self.most_recent_station}", self)
        self.announcement_lbl = QLabel(f"Time to announce: {self.announcement}", self)
        self.left_door_status_lbl = QLabel(f"Left door open: {'Open' if self.doors_status[0] else 'Closed'}", self)
        self.right_door_status_lbl = QLabel(f"Right door open: {'Open' if self.doors_status[1] else 'Closed'}", self)
        self.in_light_status_lbl = QLabel(f"Indoor light on: {'On' if self.lights_status[0] else 'Off'}", self)
        self.out_light_status_lbl = QLabel(f"Outdoor light on: {'On' if self.doors_status[1] else 'Off'}", self)
        self.underground_lbl = QLabel(f"Underground: {'True' if self.underground else 'False'}", self)
        self.cur_cabin_temp_lbl = QLabel(f"Current cabin temp (F): {self.cur_cabin_temp}", self)
        self.e_brake_lbl = QLabel(f"E brake on: {'True' if self.e_brake_on else 'False'}", self)
        self.s_brake_lbl = QLabel(f"Service brake deceleration (m/s^2): {self.service_brake_decel}", self)

        self.driver_speed = 10

        # Auto/manual train controller mode
        self.tc_mode_slider = QSlider(Qt.Orientation.Horizontal)
        self.tc_mode_slider.setMinimum(0)
        self.tc_mode_slider.setMaximum(1)
        self.tc_mode_slider.setValue(0)
        self.tc_mode_slider.setSingleStep(1)  # Ensures the slider moves in steps of 1
        self.tc_mode_slider.setFixedWidth(80)
        self.tc_mode_lbl = QLabel(self.train_controller_mode)
        self.tc_mode_slider.valueChanged.connect(self.update_train_controller_mode)

        # Train Driver inputs
        self.driver_speed_lbl = QLabel(f"Driver Commanded speed (if in automatic mode): {self.driver_speed}", self)
        self.driver_speed_textbox = QLineEdit(self)
        self.driver_speed_textbox.setPlaceholderText("Enter driver speed...")
        self.driver_speed_textbox.setFixedWidth(200)
        self.driver_speed_button = QPushButton("Submit", self)
        self.driver_speed_button.setFixedWidth(100)
        self.driver_speed_button.clicked.connect(self.update_commanded_speed)

        self.driver_sbrake_slider = QSlider(Qt.Orientation.Horizontal)
        self.driver_sbrake_slider.setMinimum(0)
        self.driver_sbrake_slider.setMaximum(4)
        self.driver_sbrake_slider.setValue(0)
        self.driver_sbrake_slider.setSingleStep(1)
        self.driver_sbrake_slider.setFixedWidth(120)
        self.driver_sbrake_slider.valueChanged.connect(self.update_driver_sbrake_decel)

        self.driver_ebrake_button = QPushButton("Toggle EBrake", self)
        self.driver_ebrake_button.setFixedWidth(100)
        self.driver_ebrake_button.setStyleSheet("background-color: lightgray; color: black;")
        self.driver_ebrake_button.clicked.connect(self.update_driver_ebrake_status)

        self.driver_cabin_temp_textbox = QLineEdit(self)
        self.driver_cabin_temp_textbox.setPlaceholderText("Enter cabin temp...")
        self.driver_cabin_temp_textbox.setFixedWidth(200)
        self.driver_cabin_temp_button = QPushButton("Submit", self)
        self.driver_cabin_temp_button.setFixedWidth(100)
        self.driver_cabin_temp_button.clicked.connect(self.update_driver_cabin_temp)

        self.driver_indoor_light_slider = QSlider(Qt.Orientation.Horizontal)
        self.driver_indoor_light_slider.setMinimum(0)
        self.driver_indoor_light_slider.setMaximum(1)
        self.driver_indoor_light_slider.setValue(0)
        self.driver_indoor_light_slider.setSingleStep(1)
        self.driver_indoor_light_slider.setFixedWidth(80)
        self.driver_indoor_light_slider.valueChanged.connect(self.update_driver_in_light_status)

        # top left panel
        top_left_panel = QVBoxLayout()
        top_left_panel.addWidget(self.power_gain_lbl)
        top_left_panel.addWidget(self.cur_speed_lbl)
        top_left_panel.addWidget(self.cmd_speed_lbl)
        top_left_panel.addWidget(self.speed_limit_lbl)
        top_left_panel.addWidget(self.authority_lbl)
        top_left_panel.addWidget(self.p_gain_lbl)
        top_left_panel.addWidget(self.i_gain_lbl)
        top_left_panel.addStretch()  # Pushes elements to the top

        # bottom left panel
        bottom_left_panel = QVBoxLayout()
        bottom_left_panel.addStretch()

        bottom_left_panel.addWidget(self.driver_speed_lbl)
        bottom_left_panel.addWidget(self.driver_speed_textbox)
        bottom_left_panel.addWidget(self.driver_speed_button)

        bottom_left_panel.addWidget(self.cur_cabin_temp_lbl)
        bottom_left_panel.addWidget(self.driver_cabin_temp_textbox)
        bottom_left_panel.addWidget(self.driver_cabin_temp_button)

        # top right panel
        top_right_panel = QVBoxLayout()
        top_right_panel.addWidget(self.world_time_lbl)
        top_right_panel.addWidget(self.tc_mode_slider)
        top_right_panel.addWidget(self.tc_mode_lbl)

        top_right_panel.addLayout(failure_icons_layout)
        top_right_panel.addLayout(failure_lbl_layout)

        top_right_panel.addWidget(self.driver_sbrake_slider)
        top_right_panel.addWidget(self.s_brake_lbl)
        top_right_panel.addWidget(self.driver_ebrake_button)
        top_right_panel.addWidget(self.e_brake_lbl)

        # bottom right panel
        bottom_right_panel = QVBoxLayout()
        bottom_right_panel.addStretch()
        bottom_right_panel.addWidget(self.station_lbl)
        bottom_right_panel.addWidget(self.announcement_lbl)
        bottom_right_panel.addWidget(self.left_door_status_lbl)
        bottom_right_panel.addWidget(self.right_door_status_lbl)
        bottom_right_panel.addWidget(self.driver_indoor_light_slider)
        bottom_right_panel.addWidget(self.in_light_status_lbl)
        bottom_right_panel.addWidget(self.out_light_status_lbl)
        bottom_right_panel.addWidget(self.underground_lbl)

        main_layout = QGridLayout()
        main_layout.addLayout(top_left_panel, 0, 0)  # Top-left
        main_layout.addLayout(top_right_panel, 0, 1)  # Right half
        main_layout.addLayout(bottom_left_panel, 1, 0)  # Bottom-left
        main_layout.addLayout(bottom_right_panel, 1, 1)  # Bottom-right
        self.setLayout(main_layout)

        font = QFont("Arial", 16)  # Set font family and size
        self.setFont(font)

    def update_world_time(self, world_time):
        self.world_time = world_time
        self.world_time_lbl.setText(f"World time (24-hr): Day {self.world_time['day']} "
                                     f"{self.world_time['hour']:02d}:{self.world_time['min']:02d}")

    def update_power_cmd(self, power):
        self.cmd_power = power
        self.power_gain_lbl.setText(f"Power delivered (W): {self.cmd_power:.2f}")

    def update_controller_gains(self, k_p, k_i):
        self.k_p = k_p
        self.k_i = k_i
        self.p_gain_lbl.setText(f"K_P (Proportional gain): {self.k_p}")
        self.i_gain_lbl.setText(f"K_I (Proportional gain): {self.k_i}")

    def update_most_recent_station(self, station_name):
        if self.most_recent_station != station_name:
            self.announcement = True
        else:
            self.announcement = False
        self.most_recent_station = station_name
        self.station_lbl.setText(f"Most recent station: {self.most_recent_station}")
        self.announcement_lbl.setText(f"Time to announce: {self.announcement}")

    def update_doors_status(self, doors_status):
        self.doors_status = doors_status
        self.left_door_status_lbl.setText(f"Left door open: {'Open' if self.doors_status[0] else 'Closed'}")
        self.right_door_status_lbl.setText(f"Right door open: {'Open' if self.doors_status[1] else 'Closed'}")

    def update_lights_status(self, lights_status):
        self.lights_status = lights_status
        self.in_light_status_lbl.setText(f"Indoor light on: {'On' if self.lights_status[0] else 'Off'}")
        self.out_light_status_lbl.setText(f"Outdoor light on: {'On' if self.lights_status[1] else 'Off'}")

    def update_driver_in_light_status(self, in_lights_status):
        self.lights_status[0] = True if in_lights_status else False
        self.in_light_status_lbl.setText(f"Indoor light on: {'On' if self.lights_status[0] else 'Off'}")

    def update_cabin_temp(self, cabin_temp):
        self.cur_cabin_temp = cabin_temp
        self.cur_cabin_temp_lbl.setText(f"Current cabin temp (F): {self.cur_cabin_temp:.2f}")

    def update_driver_cabin_temp(self):
        self.cur_cabin_temp = float(self.driver_cabin_temp_textbox.text())
        self.cur_cabin_temp_lbl.setText(f"Current cabin temp (F): {self.cur_cabin_temp:.2f}")

    def update_cur_speed(self, cur_speed):
        self.cur_speed = cur_speed
        self.cur_speed_lbl.setText(f"Current speed (m/s): {self.cur_speed:.2f}")

    def update_cmd_speed(self, cmd_speed):
        print(f"updating cmd_speed to {cmd_speed}")
        self.cmd_speed = cmd_speed
        self.cmd_speed_lbl.setText(f"Commanded speed (m/s): {self.cmd_speed:.2f}")

    def update_speed_limit(self, speed_limit):
        self.speed_limit = speed_limit
        self.speed_limit_lbl.setText(f"Speed limit (m/s): {self.speed_limit:.2f}")

    def update_authority(self, authority):
        self.authority = authority
        self.authority_lbl.setText(f"Authority (m): {self.authority:.2f}")

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
        self.driver_speed_lbl.setText(f"Driver Commanded speed (if in automatic mode): {self.driver_speed:.2f}")

    def update_sbrake_decel(self, decel):
        self.service_brake_decel = decel
        self.s_brake_lbl.setText(f"Service brake deceleration (m/s^2): {self.service_brake_decel}")

    def update_driver_sbrake_decel(self, value):
        """Value between 0-4."""
        self.service_brake_decel = value / 4 * self.max_sbrake_decel
        self.s_brake_lbl.setText(f"Service brake deceleration (m/s^2): {self.service_brake_decel:.2f}")

    def update_ebrake_status(self, value):
        self.e_brake_on = value
        self.e_brake_lbl.setText(f"E brake on: {'True' if self.e_brake_on else 'False'}")

    def update_driver_ebrake_status(self):
        self.e_brake_on = not self.e_brake_on
        self.e_brake_lbl.setText(f"E brake on: {'True' if self.e_brake_on else 'False'}")
        # change button color
        if self.e_brake_on:
            self.driver_ebrake_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.driver_ebrake_button.setStyleSheet("background-color: lightgray; color: black;")

    def update_ebrake(self, e_brake_on):
        self.e_brake_on = e_brake_on
        self.e_brake_lbl.setText(f"E brake on: {'True' if self.e_brake_on else 'False'}")
        # change button color
        if self.e_brake_on:
            self.driver_ebrake_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.driver_ebrake_button.setStyleSheet("background-color: lightgray; color: black;")

    def update_failure_modes(self, failure_modes):
        size = 20
        pixmap_list = []
        for i in range(len(failure_modes)):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(Qt.GlobalColor.red if failure_modes[i] else Qt.GlobalColor.green)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))  # Black outline, 2px width
            # Draw a filled rectangle with a black outline
            painter.drawRect(1, 1, size - 2, size - 2)  # Leave 1px padding for outline
            painter.end()
            pixmap_list.append(pixmap)

        self.train_engine_fail_icon.setPixmap(pixmap_list[0])
        self.signal_pickup_fail_icon.setPixmap(pixmap_list[1])
        self.sbrake_fail_icon.setPixmap(pixmap_list[2])

    def update_underground(self, underground):
        self.underground = underground
        self.underground_lbl.setText(f"Underground: {'True' if self.underground else 'False'}")
