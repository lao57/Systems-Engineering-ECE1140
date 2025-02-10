from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt


class TrainControllerGUI(QWidget):
    def __init__(self, k_p, k_i):
        super().__init__()

        # Set Window Title
        self.setWindowTitle("Train Controller GUI")
        self.resize(400, 300)

        # Set Background Color to Blue
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ADD8E6"))  # Light Blue
        self.setPalette(palette)

        self.k_p = k_p
        self.k_i = k_i
        self.most_recent_station = None
        self.doors_status = [False, False]  # [left_doors_open, right_doors_open]
        self.lights_status = [False, False]  # [interior_lights_open, exterior_lights_open]
        self.underground = False
        self.cur_cabin_temp = None
        self.e_brake_on = False
        self.service_brake_on = False

        # create widgets
        self.p_gain_lbl = QLabel(f"K_P (Proportional gain): {k_p}", self)
        self.i_gain_lbl = QLabel(f"K_I (Integral gain): {k_i}", self)
        self.station_lbl = QLabel(f"Most recent station: {self.most_recent_station}", self)
        self.left_door_status_lbl = QLabel(f"Left door open: {'Open' if self.doors_status[0] else 'Closed'}", self)
        self.right_door_status_lbl = QLabel(f"Left door open: {'Open' if self.doors_status[1] else 'Closed'}", self)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.p_gain_lbl)
        layout.addWidget(self.i_gain_lbl)
        layout.addWidget(self.station_lbl)
        layout.addWidget(self.left_door_status_lbl)
        layout.addWidget(self.right_door_status_lbl)
        self.setLayout(layout)
