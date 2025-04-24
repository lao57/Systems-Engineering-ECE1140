import sys
import pandas as pd
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFileDialog, QGridLayout, QComboBox,
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


try:
    from track_model.track_model_backend import TrackModelBackend
except ImportError:
    from track_model_backend import TrackModelBackend

class UnifiedTrackUI(QWidget):
    def __init__(self, backend=None):
        super().__init__()
        self.backend = backend
        self.backend.addUI(self)
        self.failures = {
            "Broken Rail": False,
            "Track Circuit": False,
            "Transponder": False,
            "Power Failure": False,
            "Maintenance": False
        }
        self.temperature = 70
        self.df_layout = None
        self.setupUI()

    def setupUI(self):
        splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        from track_model.track_map import TrackMapViewer
        #from track_map import TrackMapViewer #to use without main
        self.map_left = TrackMapViewer(self.backend)
        self.map_right = TrackMapViewer(self.backend)

        # Layout to hold maps side-by-side
        map_row = QHBoxLayout()
        map_row.addWidget(self.map_left)
        map_row.addWidget(self.map_right)

        right_panel.addLayout(map_row)

        # -- Testbench Section --
        tb = QVBoxLayout()
        tb.addWidget(QLabel("Toggle failures to inject:", font=QFont("Arial", 14, QFont.Weight.Bold)))
        self.failure_toggles = {}
        self.failure_status_labels = {}
        for f in self.failures:
            row = QHBoxLayout()
            btn = QPushButton(f); btn.setCheckable(True)
            btn.clicked.connect(lambda checked, f=f: self.toggle_failure(f, checked))
            lbl = QLabel("Inactive"); lbl.setFont(QFont("Arial",12))
            row.addWidget(btn); row.addWidget(lbl)
            self.failure_toggles[f] = btn
            self.failure_status_labels[f] = lbl
            tb.addLayout(row)

        self.temp_label = QLabel(f"Temperature: {self.temperature}°F", font=QFont("Arial",14, QFont.Weight.Bold))
        tb.addWidget(self.temp_label)
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(-50,120); self.temp_slider.setValue(self.temperature)
        self.temp_slider.valueChanged.connect(self.update_temperature)
        tb.addWidget(self.temp_slider)
        self.heater_label = QLabel("Track Heater: OFF", font=QFont("Arial",12))
        tb.addWidget(self.heater_label)
        left_panel.addLayout(tb)

        # -- Track Model Section --
        tm = QVBoxLayout()
        up = QHBoxLayout()
        self.file_label = QLabel("Current Layout File:", font=QFont("Arial",12,QFont.Weight.Bold))
        up.addWidget(self.file_label)
        self.upload_button = QPushButton("Upload Layout")
        self.upload_button.clicked.connect(self.upload_file)
        up.addWidget(self.upload_button)
        tm.addLayout(up)

        self.block_selector = QComboBox(); self.block_selector.currentIndexChanged.connect(self.reset_failures)
        tm.addWidget(self.block_selector)

        grid = QGridLayout(); grid.setSpacing(15)
        # Properties labels
        props = ["Speed Limit","Direction of Travel","Grade","Elevation","Block Size"]
        self.label_widgets = {}
        grid.addWidget(QLabel("Properties", font=QFont("Arial",14, QFont.Weight.Bold)), 0,0)
        for i, txt in enumerate(props, start=1):
            lbl = QLabel(f"{txt}: N/A", font=QFont("Arial",12))
            self.label_widgets[txt] = lbl
            grid.addWidget(lbl, i, 0)
        # States
        grid.addWidget(QLabel("Current States", font=QFont("Arial",14, QFont.Weight.Bold)), 0,1)
        self.occupancy_label = QLabel("Track Occupancy: ✅", font=QFont("Arial",14, QFont.Weight.Bold))
        grid.addWidget(self.occupancy_label,1,1)
        self.switch_label = QLabel("Switch Position: N/A", font=QFont("Arial",12))
        grid.addWidget(self.switch_label,2,1)
        self.crossing_label = QLabel("Railway Crossing: N/A", font=QFont("Arial",12))
        grid.addWidget(self.crossing_label,3,1)
        self.light_signal_label = QLabel("Light Signal: N/A", font=QFont("Arial",12))
        grid.addWidget(self.light_signal_label,4,1)
        self.station_label = QLabel("Station: N/A", font=QFont("Arial",12))
        grid.addWidget(self.station_label,5,1)

        tm.addLayout(grid)
        left_panel.addLayout(tm)

        # Wrap left_panel in a QWidget
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_panel)

        # Wrap right_panel in a QWidget
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_panel)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Set initial sizes: [controls width, map width]
        splitter.setSizes([400, 1000])

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)



    def toggle_failure(self, failure, checked):
        print("fILURE: ", failure, checked)
        self.failures[failure] = checked
        self.failure_status_labels[failure].setText("Active" if checked else "Inactive")
        idx = self.block_selector.currentIndex()
        if idx >= 0 and self.df_layout is not None:
            print("entered df func")
            blk = int(self.df_layout.iloc[idx]["Block Number"])
            self.backend.update_block_occupancy(blk - 1, blk, blk + 1, checked)
            self.occupancy_label.setText(f"Track Occupancy: {'❌' if checked else '✅'}")

    def reset_failures(self):
        for f in self.failures:
            self.failures[f] = False
            self.failure_toggles[f].setChecked(False)
            self.failure_status_labels[f].setText("Inactive")

    def update_temperature(self):
        self.temperature = self.temp_slider.value()
        self.temp_label.setText(f"Temperature: {self.temperature}°F")
        self.backend.update_temperature(self.temperature)
        self.heater_label.setText("Track Heater: ON" if self.temperature<=32 else "Track Heater: OFF")

    def upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Layout File","", "CSV Files (*.csv)")
        if not path: return
        self.backend.load_excel(path)
        df = pd.read_csv(path)
        self.df_layout = df
        self.block_selector.clear()
        self.block_selector.addItems(df["Block Number"].astype(str).tolist())
        # force initial UI update
        if self.backend.ui: self.backend.ui.update()

    def update(self):
        if self.df_layout is None: return
        idx = self.block_selector.currentIndex()
        if idx<0: return
        row = self.df_layout.iloc[idx]
        blk = int(row["Block Number"])
        # Properties
        sp = round(row["Speed Limit (Km/Hr)"]*0.621371,1)
        bs = round(row["Block Length (m)"]*3.28084,1)
        self.label_widgets["Speed Limit"].setText(f"Speed Limit: {sp} mph")
        self.label_widgets["Block Size"].setText(f"Block Size: {bs} ft")
        self.label_widgets["Grade"].setText(f"Grade: {row['Block Grade (%)']}%")
        self.label_widgets["Elevation"].setText(f"Elevation: {row['ELEVATION (M)']} m")
        # States
        occ = self.backend.get_occupancy_status(blk-1)
        self.occupancy_label.setText(f"Track Occupancy: {'❌' if occ else '✅'}")
        self.switch_label.setText(f"Switch Position: {'On' if self.backend.get_switch_states(blk-1) else 'Off'}")
        self.crossing_label.setText(f"Railway Crossing: {'Active' if self.backend.get_crossing_states(blk-1) else 'Inactive'}")
        self.light_signal_label.setText(f"Light Signal: {'Green' if self.backend.get_light_signals(blk-1) else 'Red'}")
        # Station tooltip if any
        # …you can add more here

def main():
    app = QApplication(sys.argv)
    backend = TrackModelBackend()
    win = QMainWindow()
    ui = UnifiedTrackUI(backend=backend)
    win.setCentralWidget(ui)
    win.resize(1200, 800)
    win.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
