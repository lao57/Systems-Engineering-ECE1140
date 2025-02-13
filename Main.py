import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QVBoxLayout, QDialog, QLabel, \
    QCheckBox, QPushButton
from ui_CTCOffice import Ui_MainWindow  # Import the converted UI file
from testbench import TestBench  # Import the testbench module



class ManualUploadDialog(QDialog):
    def __init__(self, selected_line):
        super().__init__()
        self.setWindowTitle(f"Manual Upload - {selected_line}")
        self.layout = QVBoxLayout()


        #Button to submit selected station
        ##NOT WORKING
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_selection)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)

    def submit_selection(self):
        self.accept()

class CTCOffice(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Load UI
        self.testbench = TestBench(self)



        # Connect UI elements to functions
        self.comboTrainLine.currentIndexChanged.connect(self.switch_train_line)
        self.btnManualUpload.clicked.connect(self.open_manual_upload_screen)
        self.btnUploadSchedule.clicked.connect(self.upload_pdf_schedule)
        self.comboBlockOccupancy.currentIndexChanged.connect(self.switch_block_occupancy)
        self.comboSelectBlock.currentIndexChanged.connect(self.block_selected)
        self.btnOpenTrack.clicked.connect(self.open_track)
        self.btnCloseTrack.clicked.connect(self.close_track)

        # Initialize UI with correct values
        self.switch_train_line()
        self.switch_block_occupancy()

        # Simulate data using testbench
        self.testbench.simulate_train_updates()
        self.testbench.simulate_track_data()

    def switch_train_line(self):
        selected_line = self.comboTrainLine.currentText()
        print(f"Switched to {selected_line} Line")

    def switch_block_occupancy(self):
        selected_line = self.comboBlockOccupancy.currentText()
        print(f"Switched to {selected_line} Block Occupancy")
        self.testbench.simulate_track_data(selected_line)

    def block_selected(self):
        selected_block = self.comboSelectBlock.currentText()
        print(f"Selected block: {selected_block}")

    def open_track(self):
        selected_block = self.comboSelectBlock.currentText()
        print(f"Track {selected_block} is now OPEN")

    def close_track(self):
        selected_block = self.comboSelectBlock.currentText()
        print(f"Track {selected_block} is now CLOSED")

    def open_manual_upload_screen(self):
        selected_line = self.comboTrainLine.currentText()
        dialog = ManualUploadDialog(selected_line)
        dialog.exec()

    def upload_pdf_schedule(self):
        selected_line = self.comboTrainLine.currentText()
        filename, _ = QFileDialog.getOpenFileName(self, f"Upload {selected_line} Schedule", "", "PDF Files (*.pdf);;All Files (*)")
        if filename:
            print(f"{selected_line} schedule uploaded: {filename}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTCOffice()
    window.show()
    sys.exit(app.exec())
