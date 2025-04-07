from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox,
    QSlider, QLineEdit, QGridLayout, QFrame
)
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
from PyQt6.QtCore import Qt


class TrainControllerGUIv2(QWidget):
    def __init__(self, k_p, k_i):
        super().__init__()
        self.setWindowTitle("Train Controller GUI")
        self.resize(900, 600)

        #palette = self.palette()
        #palette.setColor(QPalette.ColorRole.Window, QColor("#E6F2FF"))
        #self.setPalette(palette)
        self.setFont(QFont("Segoe UI", 12))

        # Simulated state variables
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
        self.doors_status = [False, False]
        self.lights_status = [False, False]
        self.underground = False
        self.cur_cabin_temp = 0.0
        self.e_brake_on = False
        self.service_brake_decel = 0.0
        self.max_sbrake_decel = 1.2
        self.failure_modes = [False, False, False]
        self.driver_speed = 10

        self.setup_widgets()
        self.build_layout()

    def setup_widgets(self):
        self.world_time_lbl = QLabel("World time (24-hr): Day 0 00:00")
        self.power_gain_lbl = QLabel("Power delivered (W): 0")
        self.cur_speed_lbl = QLabel("Current speed (ft/s): 0")
        self.cmd_speed_lbl = QLabel("Commanded speed (ft/s): 0")
        self.speed_limit_lbl = QLabel("Speed limit (ft/s): 0")
        self.authority_lbl = QLabel("Authority (ft): 1000.00")
        self.p_gain_lbl = QLabel(f"K_P (Proportional gain): {self.k_p}")
        self.i_gain_lbl = QLabel(f"K_I (Integral gain): {self.k_i}")

        self.station_lbl = QLabel("Next station: Yard")
        self.announcement_lbl = QLabel("Time to announce: False")
        self.left_door_status_lbl = QLabel("Left door open: Closed")
        self.right_door_status_lbl = QLabel("Right door open: Closed")
        self.in_light_status_lbl = QLabel("Indoor light on: Off")
        self.out_light_status_lbl = QLabel("Outdoor light on: Off")
        self.underground_lbl = QLabel("Underground: False")
        self.cur_cabin_temp_lbl = QLabel("Current cabin temp (F): 0.0")
        self.e_brake_lbl = QLabel("E brake on: False")
        self.s_brake_lbl = QLabel("Service brake deceleration (ft/s^2): 0.0")

        self.tc_mode_slider = QSlider(Qt.Orientation.Horizontal)
        self.tc_mode_slider.setMinimum(0)
        self.tc_mode_slider.setMaximum(1)
        self.tc_mode_slider.setValue(0)
        self.tc_mode_slider.setSingleStep(1)
        self.tc_mode_slider.setFixedWidth(80)
        self.tc_mode_slider.valueChanged.connect(self.update_train_controller_mode)
        self.tc_mode_lbl = QLabel(self.train_controller_mode)

        self.driver_speed_lbl = QLabel("Driver Commanded speed (if in automatic mode): 10")
        self.driver_speed_textbox = QLineEdit()
        self.driver_speed_textbox.setPlaceholderText("Enter driver speed...")
        self.driver_speed_textbox.setFixedWidth(200)
        self.driver_speed_button = QPushButton("Submit")
        self.driver_speed_button.setFixedWidth(100)
        self.driver_speed_button.clicked.connect(self.update_commanded_speed)

        self.driver_sbrake_slider = QSlider(Qt.Orientation.Horizontal)
        self.driver_sbrake_slider.setMinimum(0)
        self.driver_sbrake_slider.setMaximum(4)
        self.driver_sbrake_slider.setValue(0)
        self.driver_sbrake_slider.setSingleStep(1)
        self.driver_sbrake_slider.setFixedWidth(120)
        self.driver_sbrake_slider.valueChanged.connect(self.update_driver_sbrake_decel)

        self.driver_ebrake_button = QPushButton("EBrake")
        self.driver_ebrake_button.setFixedSize(60, 60)
        self.driver_ebrake_button.setStyleSheet("""
            QPushButton {
                border-radius: 30px;
                background-color: lightgray;
                color: white;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)
        self.driver_ebrake_button.clicked.connect(self.update_driver_ebrake_status)

        self.driver_cabin_temp_textbox = QLineEdit()
        self.driver_cabin_temp_textbox.setPlaceholderText("Enter cabin temp...")
        self.driver_cabin_temp_textbox.setFixedWidth(200)
        self.driver_cabin_temp_button = QPushButton("Submit")
        self.driver_cabin_temp_button.setFixedWidth(100)
        self.driver_cabin_temp_button.clicked.connect(self.update_driver_cabin_temp)

        self.driver_indoor_light_slider = QSlider(Qt.Orientation.Horizontal)
        self.driver_indoor_light_slider.setMinimum(0)
        self.driver_indoor_light_slider.setMaximum(1)
        self.driver_indoor_light_slider.setValue(0)
        self.driver_indoor_light_slider.setSingleStep(1)
        self.driver_indoor_light_slider.setFixedWidth(80)
        self.driver_indoor_light_slider.valueChanged.connect(self.update_driver_in_light_status)

        self.train_engine_fail_icon = QLabel()
        self.signal_pickup_fail_icon = QLabel()
        self.sbrake_fail_icon = QLabel()
        self.train_engine_fail_lbl = QLabel("Train engine failure")
        self.signal_pickup_fail_lbl = QLabel("Signal pickup failure")
        self.sbrake_fail_lbl = QLabel("Service brake failure")
        self.update_failure_modes(self.failure_modes)

    def build_layout(self):
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Controller Mode:"))
        mode_layout.addWidget(self.tc_mode_slider)
        mode_layout.addWidget(self.tc_mode_lbl)

        train_info = QGroupBox("Train Information")
        train_info_layout = QVBoxLayout()
        for w in [self.power_gain_lbl, self.cur_speed_lbl, self.cmd_speed_lbl,
                  self.speed_limit_lbl, self.authority_lbl, self.p_gain_lbl, self.i_gain_lbl]:
            train_info_layout.addWidget(w)
        train_info.setLayout(train_info_layout)

        driver_control = QGroupBox("Driver Controls")
        driver_layout = QVBoxLayout()
        for w in [self.driver_speed_lbl, self.driver_speed_textbox, self.driver_speed_button,
                  self.driver_indoor_light_slider, self.in_light_status_lbl,
                  self.driver_cabin_temp_textbox, self.driver_cabin_temp_button,
                  self.driver_sbrake_slider, self.s_brake_lbl,
                  self.driver_ebrake_button, self.e_brake_lbl]:
            driver_layout.addWidget(w)
        driver_control.setLayout(driver_layout)

        status = QGroupBox("Environment Status")
        status_layout = QVBoxLayout()
        for w in [self.station_lbl, self.announcement_lbl,
                  self.left_door_status_lbl, self.right_door_status_lbl,
                  self.out_light_status_lbl, self.underground_lbl]:
            status_layout.addWidget(w)
        status.setLayout(status_layout)

        failures = QGroupBox("Failure Modes")
        fail_layout = QGridLayout()

        def vline():
            line = QFrame()
            line.setFrameShape(QFrame.Shape.VLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            return line

        fail_layout.addWidget(self.train_engine_fail_icon, 0, 0)
        fail_layout.addWidget(vline(), 0, 1)
        fail_layout.addWidget(self.signal_pickup_fail_icon, 0, 2)
        fail_layout.addWidget(vline(), 0, 3)
        fail_layout.addWidget(self.sbrake_fail_icon, 0, 4)

        fail_layout.addWidget(self.train_engine_fail_lbl, 1, 0)
        fail_layout.addWidget(vline(), 1, 1)
        fail_layout.addWidget(self.signal_pickup_fail_lbl, 1, 2)
        fail_layout.addWidget(vline(), 1, 3)
        fail_layout.addWidget(self.sbrake_fail_lbl, 1, 4)

        failures.setLayout(fail_layout)

        main_layout = QGridLayout()
        main_layout.addLayout(mode_layout, 0, 0, 1, 2)
        main_layout.addWidget(train_info, 1, 0)
        main_layout.addWidget(driver_control, 1, 1)
        main_layout.addWidget(status, 2, 0)
        main_layout.addWidget(failures, 2, 1)
        self.setLayout(main_layout)

    def update_train_controller_mode(self, value):
        self.train_controller_mode = "Automatic" if value == 0 else "Manual"
        self.tc_mode_lbl.setText(self.train_controller_mode)

    def update_commanded_speed(self):
        self.driver_speed = float(self.driver_speed_textbox.text())
        self.driver_speed_lbl.setText(f"Driver Commanded speed (if in automatic mode): {self.driver_speed:.2f}")

    def update_driver_cabin_temp(self):
        self.cur_cabin_temp = float(self.driver_cabin_temp_textbox.text())
        self.cur_cabin_temp_lbl.setText(f"Current cabin temp (F): {self.cur_cabin_temp:.2f}")

    # def update_driver_sbrake_decel(self, value):
    #     self.service_brake_decel = value / 4 * self.max_sbrake_decel
    #     self.s_brake_lbl.setText(f"Service brake deceleration (m/s^2): {self.service_brake_decel:.2f}")

    def update_driver_sbrake_decel(self, value):
        self.service_brake_decel = value / 4 * self.max_sbrake_decel
        decel_ftps2 = self.service_brake_decel * 3.28084
        self.s_brake_lbl.setText(f"Service brake deceleration (ft/s²): {decel_ftps2:.2f}")

    def update_driver_ebrake_status(self):
        self.e_brake_on = not self.e_brake_on
        self.e_brake_lbl.setText(f"E brake on: {'True' if self.e_brake_on else 'False'}")
        self.driver_ebrake_button.setStyleSheet(f"""
            QPushButton {{
                border-radius: 30px;
                background-color: {'red' if self.e_brake_on else 'lightgray'};
                color: black;
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background-color: {'darkred' if self.e_brake_on else 'gray'};
            }}
        """)
        # self.driver_ebrake_button.setFixedSize(60, 60)

    def update_driver_in_light_status(self, value):
        self.lights_status[0] = bool(value)
        self.in_light_status_lbl.setText(f"Indoor light on: {'On' if self.lights_status[0] else 'Off'}")

    def update_failure_modes(self, failure_modes):
        size = 20
        pixmap_list = []
        for i in range(len(failure_modes)):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(Qt.GlobalColor.red if failure_modes[i] else Qt.GlobalColor.green)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(1, 1, size - 2, size - 2)
            painter.end()
            pixmap_list.append(pixmap)

        self.train_engine_fail_icon.setPixmap(pixmap_list[0])
        self.signal_pickup_fail_icon.setPixmap(pixmap_list[1])
        self.sbrake_fail_icon.setPixmap(pixmap_list[2])

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

    def update_cabin_temp(self, cabin_temp):
        self.cur_cabin_temp = cabin_temp
        self.cur_cabin_temp_lbl.setText(f"Current cabin temp (F): {self.cur_cabin_temp:.2f}")

    def update_cur_speed(self, cur_speed):
        self.cur_speed = cur_speed
        speed_mph = self.cur_speed * 2.23694
        self.cur_speed_lbl.setText(f"Current speed (mph): {speed_mph:.2f}")

    def update_cmd_speed(self, cmd_speed):
        self.cmd_speed = cmd_speed
        cmd_mph = self.cmd_speed * 2.23694
        self.cmd_speed_lbl.setText(f"Commanded speed (mph): {cmd_mph:.2f}")

    def update_speed_limit(self, speed_limit):
        self.speed_limit = speed_limit
        limit_mph = (self.speed_limit * 2.23694) / 0.75
        self.speed_limit_lbl.setText(f"Speed limit (mph): {limit_mph:.2f}")

    def update_authority(self, authority):
        self.authority = authority
        authority_ft = self.authority * 3.28084
        self.authority_lbl.setText(f"Authority (ft): {authority_ft:.2f}")

    def update_sbrake_decel(self, decel):
        self.service_brake_decel = decel
        decel_ftps2 = self.service_brake_decel * 3.28084
        self.s_brake_lbl.setText(f"Service brake deceleration (ft/s²): {decel_ftps2:.2f}")

    def update_ebrake_status(self, value):
        self.e_brake_on = value
        self.e_brake_lbl.setText(f"E brake on: {'True' if self.e_brake_on else 'False'}")

    def update_ebrake(self, e_brake_on):
        self.e_brake_on = e_brake_on
        self.e_brake_lbl.setText(f"E brake on: {'True' if self.e_brake_on else 'False'}")
        # change button color
        if self.e_brake_on:
            self.driver_ebrake_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.driver_ebrake_button.setStyleSheet("background-color: lightgray; color: black;")

    def update_underground(self, underground):
        self.underground = underground
        self.underground_lbl.setText(f"Underground: {'True' if self.underground else 'False'}")


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = TrainControllerGUIv2(k_p=1.0, k_i=0.5)
    window.show()
    sys.exit(app.exec())
