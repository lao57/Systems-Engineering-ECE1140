import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QVBoxLayout, QDialog, QLabel, \
    QCheckBox, QPushButton
from PyQt6.QtGui import QPalette, QColor
from CTCOffice_UI import Ui_MainWindow  # Import the converted UI file
from testbench import TestBench  # Import the testbench module


class ManualUploadDialog(QDialog):
    def __init__(self, selected_line):
        super().__init__()
        self.setWindowTitle(f"Manual Upload - {selected_line}")
        self.layout = QVBoxLayout()

        # Define stations for each train line
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

        # create checkboxes for each line
        self.checkboxes = []
        self.selected_order = []  # Stores checked stations in order

        for station in self.stations.get(selected_line, []):
            checkbox = QCheckBox(station)
            checkbox.stateChanged.connect(lambda _, cb=checkbox: self.update_selection_order(cb))
            self.layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        # Submit button to confirm selection
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_selection)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)

    def update_selection_order(self, checkbox):
        # Track the order of selected checkboxes while maintaining sequence
        if checkbox.isChecked():
            if checkbox.text() not in self.selected_order:
                self.selected_order.append(checkbox.text())
        else:
            if checkbox.text() in self.selected_order:
                self.selected_order.remove(checkbox.text())

        print(f"Current selection order: {self.selected_order}")

    def submit_selection(self):
        # Collect selected stations and maintain order
        print(f"Final selected stations in order: {', '.join(self.selected_order)}")
        self.accept()


class CTCOffice(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Load UI components
        self.testbench = TestBench(self)  # Initialize testbench module

        # Connect UI elements to functions
        self.comboTrainLine.currentIndexChanged.connect(self.switch_train_line)  # Handles train line selection
        self.btnManualUpload.clicked.connect(self.open_manual_upload_screen)  # Opens manual upload
        self.btnUploadSchedule.clicked.connect(self.upload_pdf_schedule)  # Opens file selection for schedule upload
        self.comboBlockOccupancy.currentIndexChanged.connect(
            self.switch_block_occupancy)  # Handles block occupancy switch
        self.comboSelectBlock.currentIndexChanged.connect(self.block_selected)  # Handles block selection
        self.btnOpenTrack.clicked.connect(self.open_track)  # Opens selected track
        self.btnCloseTrack.clicked.connect(self.close_track)  # Closes selected track

        # Set button colors
        self.btnOpenTrack.setStyleSheet("background-color: green; color: white;")  # Green button for opening track
        self.btnCloseTrack.setStyleSheet("background-color: red; color: white;")  # Red button for closing track

        # Initialize UI with correct values
        self.switch_train_line()
        self.switch_block_occupancy()

        # Simulate data
        self.testbench.simulate_train_updates()
        self.testbench.simulate_track_data()

    def switch_train_line(self):
        # Updates the UI when switching train lines
        selected_line = self.comboTrainLine.currentText()
        print(f"Switched to {selected_line} Line")


    #Needs updated with real values
    def switch_block_occupancy(self):
        # Updates the block occupancy table when switching lines
        selected_line = self.comboBlockOccupancy.currentText()
        print(f"Switched to {selected_line} Block Occupancy")
        self.testbench.simulate_track_data(selected_line)

        # Change color of the combo box based on selected train line
        if "red" in selected_line.lower():
            self.comboBlockOccupancy.setStyleSheet("background-color: red; color: white;")
        elif "green" in selected_line.lower():
            self.comboBlockOccupancy.setStyleSheet("background-color: green; color: white;")

    #Needs updated with real values
    def block_selected(self):
        # Prints the selected block for maintenance control
        selected_block = self.comboSelectBlock.currentText()
        print(f"Selected block: {selected_block}")


    #Needs updated with real values
    def open_track(self):
        # Marks the selected track as open
        selected_block = self.comboSelectBlock.currentText()
        print(f"Track {selected_block} is now OPEN")

    # Needs updated with real values
    def close_track(self):
        # Marks the selected track as closed
        selected_block = self.comboSelectBlock.currentText()
        print(f"Track {selected_block} is now CLOSED")

    def open_manual_upload_screen(self):
        # Opens the manual upload dialog for selecting stations based on the selected train line
        selected_line = self.comboTrainLine.currentText()
        dialog = ManualUploadDialog(selected_line)
        dialog.exec()

    def upload_pdf_schedule(self):
        # Opens a file dialog for uploading a train schedule
        selected_line = self.comboTrainLine.currentText()
        filename, _ = QFileDialog.getOpenFileName(self, f"Upload {selected_line} Schedule", "",
                                                  "PDF Files (*.pdf);;All Files (*)")
        if filename:
            print(f"{selected_line} schedule uploaded: {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTCOffice()
    window.show()
    sys.exit(app.exec())
