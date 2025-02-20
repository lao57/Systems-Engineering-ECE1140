import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QVBoxLayout, QDialog, QLabel, \
    QCheckBox, QPushButton, QComboBox
from PyQt6.QtGui import QPalette, QColor
from CTCOffice_GUI import Ui_MainWindow  # Import the converted UI file
from testbench import TestBench  # Import the testbench module


class ManualUploadDialog(QDialog):
    def __init__(self, selected_line):
        super().__init__()
        self.setWindowTitle(f"Manual Upload - {selected_line}")
        self.layout = QVBoxLayout()

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
        self.selected_order = []

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

        print(f"Current selection order: {self.selected_order}")

    def submit_selection(self):
        print(f"Final selected stations in order: {', '.join(self.selected_order)}")
        self.accept()


class CTCOffice(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.testbench = TestBench(self)

        # Connect signals and slots
        self.comboTrainLine.currentIndexChanged.connect(self.switch_train_line)
        self.btnManualUpload.clicked.connect(self.open_manual_upload_screen)
        self.btnUploadSchedule.clicked.connect(self.upload_pdf_schedule)
        self.comboBlockOccupancy.currentIndexChanged.connect(self.switch_block_occupancy)
        self.maintLine.currentIndexChanged.connect(self.switch_maintenance_line)
        self.maintBlock.currentIndexChanged.connect(self.block_selected)
        self.btnOpenTrack.clicked.connect(self.open_track)
        self.btnCloseTrack.clicked.connect(self.close_track)

        # Style buttons
        self.btnOpenTrack.setStyleSheet("background-color: green; color: white;")
        self.btnCloseTrack.setStyleSheet("background-color: red; color: white;")

        # Initialize UI components
        self.switch_train_line()
        self.switch_block_occupancy()
        self.switch_maintenance_line()

        # Initialize block occupancy
        self.testbench.initialize_block_occupancy()

        # Add sample train data to the Train Monitor table
        self.initialize_train_monitor()

        # Initialize system analysis table
        self.initialize_system_analysis()

    def switch_train_line(self):
        """Handles switching between train lines."""
        selected_line = self.comboTrainLine.currentText()
        print(f"Switched to {selected_line} Line")

    def switch_block_occupancy(self):
        """Handles switching between block occupancy views."""
        selected_line = self.comboBlockOccupancy.currentText()
        print(f"Switched to {selected_line} Block Occupancy")
        block_count = 76 if "red" in selected_line.lower() else 141

        self.tableBlockOccupancy.clearContents()
        self.tableBlockOccupancy.setRowCount(block_count)

        for row in range(block_count):
            self.tableBlockOccupancy.setItem(row, 0, QTableWidgetItem(f"Block {row + 1}"))
            self.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem("Unoccupied"))

        if "red" in selected_line.lower():
            self.comboBlockOccupancy.setStyleSheet("background-color: red; color: white;")
        elif "green" in selected_line.lower():
            self.comboBlockOccupancy.setStyleSheet("background-color: green; color: white;")

        self.testbench.update_block_occupancy_table()

    def switch_maintenance_line(self):
        """Handles switching between maintenance lines."""
        selected_line = self.maintLine.currentText()
        print(f"Switched to {selected_line} for maintenance")

        self.maintBlock.clear()
        if "red" in selected_line.lower():
            self.maintBlock.addItems([f"Block {i}" for i in range(1, 77)])  # Red Line has 76 blocks
        elif "green" in selected_line.lower():
            self.maintBlock.addItems([f"Block {i}" for i in range(1, 142)])  # Green Line has 141 blocks

    def block_selected(self):
        """Handles selection of a block for maintenance."""
        selected_block = self.maintBlock.currentText()
        print(f"Selected maintenance block: {selected_block}")

    def close_track(self):
        """Mark the selected block as occupied and update the table."""
        selected_block = self.maintBlock.currentText()
        if not selected_block:
            return

        block_number = int(selected_block.split(" ")[1])  # Extract block number from "Block X"
        current_line = self.maintLine.currentText()

        # Update the block occupancy table
        row = block_number - 1  # Convert block number to row index
        self.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem("Occupied"))

        # Update the testbench
        self.testbench.set_block_occupied(block_number, current_line)
        print(f"Track {selected_block} on {current_line} is now CLOSED for maintenance")

    def open_track(self):
        """Mark the selected block as unoccupied and update the table."""
        selected_block = self.maintBlock.currentText()
        if not selected_block:
            return

        block_number = int(selected_block.split(" ")[1])  # Extract block number from "Block X"
        current_line = self.maintLine.currentText()

        # Update the block occupancy table
        row = block_number - 1  # Convert block number to row index
        self.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem("Unoccupied"))

        # Update the testbench
        self.testbench.set_block_unoccupied(block_number, current_line)
        print(f"Track {selected_block} on {current_line} is now OPEN")

    def open_manual_upload_screen(self):
        """Opens the manual upload dialog."""
        selected_line = self.comboTrainLine.currentText()
        dialog = ManualUploadDialog(selected_line)
        dialog.exec()

    def upload_pdf_schedule(self):
        """Handles uploading a PDF schedule."""
        selected_line = self.comboTrainLine.currentText()
        filename, _ = QFileDialog.getOpenFileName(self, f"Upload {selected_line} Schedule", "",
                                                  "PDF Files (*.pdf);;All Files (*)")
        if filename:
            print(f"{selected_line} schedule uploaded: {filename}")

    def initialize_train_monitor(self):
        """Initializes the Train Monitor table with sample data."""
        sample_trains = [
            {"Train Number": 2, "Current Line": "Red", "Current Block": 4, "Commanded Speed": 50, "Commanded Authority": 40},

        ]

        self.tableTrainMonitor.setRowCount(len(sample_trains))

        for row, train in enumerate(sample_trains):
            self.tableTrainMonitor.setItem(row, 0, QTableWidgetItem(str(train["Train Number"])))
            self.tableTrainMonitor.setItem(row, 1, QTableWidgetItem(train["Current Line"]))
            self.tableTrainMonitor.setItem(row, 2, QTableWidgetItem(str(train["Current Block"])))
            self.tableTrainMonitor.setItem(row, 3, QTableWidgetItem(str(train["Commanded Speed"])))
            self.tableTrainMonitor.setItem(row, 4, QTableWidgetItem(str(train["Commanded Authority"])))

            # Update block occupancy based on train data
            block_number = train["Current Block"]
            current_line = train["Current Line"]
            self.testbench.set_block_occupied(block_number, current_line)

        # Refresh the block occupancy table
        self.testbench.update_block_occupancy_table()

    def initialize_system_analysis(self):
        """Fills the System Analysis Table with sample throughput and failure data."""
        sample_analysis = [
            {"Throughput": "500 trains/day", "Avg Delay": "2 min", "Failures": 3,
             "Failure %": "1.2%"},
            {"Throughput": "620 trains/day", "Avg Delay": "1.5 min", "Failures": 5,
             "Failure %": "2.0%"},
        ]

        self.tableSystemAnalysis.setRowCount(len(sample_analysis))

        for row, data in enumerate(sample_analysis):

            self.tableSystemAnalysis.setItem(row, 0, QTableWidgetItem(data["Throughput"]))
            self.tableSystemAnalysis.setItem(row, 1, QTableWidgetItem(data["Avg Delay"]))
            self.tableSystemAnalysis.setItem(row, 2, QTableWidgetItem(str(data["Failures"])))
            self.tableSystemAnalysis.setItem(row, 3, QTableWidgetItem(data["Failure %"]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTCOffice()
    window.show()
    sys.exit(app.exec())