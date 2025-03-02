import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QVBoxLayout, QDialog, QLabel, \
    QCheckBox, QPushButton, QComboBox
from PyQt6.QtGui import QPalette, QColor
from CTCOffice_UI import Ui_MainWindow
from testbench import TestBench


class ManualUploadDialog(QDialog):
    def __init__(self, selected_line):
        super().__init__()
        self.setWindowTitle(f"Manual Upload - {selected_line}")
        self.layout = QVBoxLayout()
        self.selected_order = []

        self.stations = {
            "Red Line": [
                "Shadyside Station", "Herron Avenue Station", "Penn Station", "Steel Plaza Station",
                "First Avenue Station", "Station Square", "South Hills Junction"
            ],
            "Green Line": [
                "Pioneer Station", "Edgebrook Station", "Whited Station", "Southbank Station", "Central Station",
                "Inglewood Station", "Overbrook Station", "Glenbury Station", "Dormont Station", "Mt Lebanon Station",
                "Poplar Station", "Castle Shannon Station"
            ]
        }

        self.checkboxes = []
        for station in self.stations.get(selected_line, []):
            checkbox = QCheckBox(station)
            checkbox.stateChanged.connect(lambda _, cb=checkbox: self.update_selection_order(cb))
            self.layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_selection)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)

    def update_selection_order(self, checkbox):
        if checkbox.isChecked():
            if checkbox.text() not in self.selected_order:
                self.selected_order.append(checkbox.text())
        else:
            if checkbox.text() in self.selected_order:
                self.selected_order.remove(checkbox.text())

    def submit_selection(self):
        self.accept()


class CTCOffice(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.testbench = TestBench(self)

        # Connect signals
        self.comboTrainLine.currentIndexChanged.connect(self.switch_train_line)
        self.btnManualUpload.clicked.connect(self.open_manual_upload_screen)
        self.btnUploadSchedule.clicked.connect(self.upload_pdf_schedule)
        self.comboBlockOccupancy.currentIndexChanged.connect(self.switch_block_occupancy)
        self.maintLine.currentIndexChanged.connect(self.switch_maintenance_line)
        self.maintBlock.currentIndexChanged.connect(self.block_selected)
        self.btnOpenTrack.clicked.connect(self.open_track)
        self.btnCloseTrack.clicked.connect(self.close_track)
        self.testbench.component_changed.connect(self.update_component_states)

        # Initialize components
        self.update_component_states()
        self.btnOpenTrack.setStyleSheet("background-color: green; color: white;")
        self.btnCloseTrack.setStyleSheet("background-color: red; color: white;")
        self.switch_train_line()
        self.switch_block_occupancy()
        self.switch_maintenance_line()
        self.testbench.initialize_block_occupancy()
        self.initialize_train_monitor()
        self.initialize_system_analysis()

    def update_component_states(self):

        # Crossing
        self.crossingState.setText("OPEN" if self.testbench.crossing_open else "CLOSED")
        self.crossingState.setStyleSheet(
            "background-color: green; color: white;" if self.testbench.crossing_open
            else "background-color: red; color: white;"
        )

        # Light 1
        self.lightOneState.setText("GREEN" if self.testbench.light1_green else "RED")
        self.lightOneState.setStyleSheet(
            "background-color: green; color: white;" if self.testbench.light1_green
            else "background-color: red; color: white;"
        )

        # Light 2
        self.lightTwoState.setText("GREEN" if self.testbench.light2_green else "RED")
        self.lightTwoState.setStyleSheet(
            "background-color: green; color: white;" if self.testbench.light2_green
            else "background-color: red; color: white;"
        )

        # Switch
        self.switchState.setText("OPEN" if self.testbench.switch_open else "CLOSED")
        self.switchState.setStyleSheet(
            "background-color: green; color: white;" if self.testbench.switch_open
            else "background-color: red; color: white;"
        )

    def open_manual_upload_screen(self):
        selected_line = self.comboTrainLine.currentText()
        dialog = ManualUploadDialog(selected_line)
        if dialog.exec():
            selected_stations = dialog.selected_order
            self.testbench.log_schedule_upload(selected_line, selected_stations)

    def upload_pdf_schedule(self):
        selected_line = self.comboTrainLine.currentText()
        filename, _ = QFileDialog.getOpenFileName(self, f"Upload {selected_line} Schedule", "",
                                                  "PDF Files (*.pdf);;All Files (*)")
        if filename:
            self.testbench.log_schedule_upload(selected_line, [filename])

    def switch_train_line(self):
        selected_line = self.comboTrainLine.currentText()

    def switch_block_occupancy(self):
        selected_line = self.comboBlockOccupancy.currentText()
        block_count = 76 if "red" in selected_line.lower() else 141
        self.tableBlockOccupancy.setRowCount(block_count)
        for row in range(block_count):
            self.tableBlockOccupancy.setItem(row, 0, QTableWidgetItem(f"Block {row + 1}"))
            self.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem("Unoccupied"))
        self.testbench.update_block_occupancy_table()

    def switch_maintenance_line(self):
        selected_line = self.maintLine.currentText()
        self.maintBlock.clear()
        if "red" in selected_line.lower():
            self.maintBlock.addItems([f"Block {i}" for i in range(1, 77)])
        elif "green" in selected_line.lower():
            self.maintBlock.addItems([f"Block {i}" for i in range(1, 142)])

    def block_selected(self):
        pass

    def close_track(self):
        selected_block = self.maintBlock.currentText()
        if not selected_block: return
        block_number = int(selected_block.split(" ")[1])
        current_line = self.maintLine.currentText()
        self.testbench.set_block_occupied(block_number, current_line)

    def open_track(self):
        selected_block = self.maintBlock.currentText()
        if not selected_block: return
        block_number = int(selected_block.split(" ")[1])
        current_line = self.maintLine.currentText()
        self.testbench.set_block_unoccupied(block_number, current_line)

    def initialize_train_monitor(self):

        self.tableTrainMonitor.setRowCount(0)

    def initialize_system_analysis(self):

        self.tableSystemAnalysis.setRowCount(2)  # Red and Green lines

        # Clear all cells
        for row in range(2):
            for col in range(4):
                self.tableSystemAnalysis.setItem(row, col, QTableWidgetItem(""))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTCOffice()
    window.show()
    sys.exit(app.exec())