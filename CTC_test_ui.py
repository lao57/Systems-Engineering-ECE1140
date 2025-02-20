import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QTableWidgetItem
)
from CTC_GUI import CTCOffice  # Import your main system UI
from testbench import TestBench


class CTCTestUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CTC Office - Test UI")
        self.setGeometry(200, 200, 600, 400)

        # Connect to the actual CTCOffice system
        self.ctc_office = CTCOffice()
        self.ctc_office.show()  # Open the main UI alongside test UI

        self.initUI()

    def initUI(self):
        """Set up the Test UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Section 1: Train Input Testing
        layout.addWidget(QLabel("Test Train Inputs"))

        train_layout = QHBoxLayout()
        self.train_number = QLineEdit()
        self.train_number.setPlaceholderText("Train Number")

        self.train_line = QComboBox()
        self.train_line.addItems(["Red Line", "Green Line"])

        self.train_block = QLineEdit()
        self.train_block.setPlaceholderText("Current Block")

        self.train_speed = QLineEdit()
        self.train_speed.setPlaceholderText("Commanded Speed")

        self.train_authority = QLineEdit()
        self.train_authority.setPlaceholderText("Commanded Authority")

        train_button = QPushButton("Add Train")
        train_button.clicked.connect(self.add_train_to_monitor)

        train_layout.addWidget(self.train_number)
        train_layout.addWidget(self.train_line)
        train_layout.addWidget(self.train_block)
        train_layout.addWidget(self.train_speed)
        train_layout.addWidget(self.train_authority)
        train_layout.addWidget(train_button)
        layout.addLayout(train_layout)

        # Section 2: Block Occupancy Testing
        layout.addWidget(QLabel("Test Block Occupancy"))

        block_layout = QHBoxLayout()
        self.block_number = QLineEdit()
        self.block_number.setPlaceholderText("Block Number")

        self.block_line = QComboBox()
        self.block_line.addItems(["Red Line", "Green Line"])

        block_occupy_button = QPushButton("Occupy Block")
        block_occupy_button.clicked.connect(self.occupy_block)

        block_free_button = QPushButton("Free Block")
        block_free_button.clicked.connect(self.free_block)

        block_layout.addWidget(self.block_number)
        block_layout.addWidget(self.block_line)
        block_layout.addWidget(block_occupy_button)
        block_layout.addWidget(block_free_button)
        layout.addLayout(block_layout)

        # Section 3: Track Maintenance Testing
        layout.addWidget(QLabel("Test Track Maintenance"))

        maint_layout = QHBoxLayout()
        self.maint_block = QLineEdit()
        self.maint_block.setPlaceholderText("Block for Maintenance")

        self.maint_line = QComboBox()
        self.maint_line.addItems(["Red Line", "Green Line"])

        close_button = QPushButton("Close Track")
        close_button.clicked.connect(self.close_track)

        open_button = QPushButton("Open Track")
        open_button.clicked.connect(self.open_track)

        maint_layout.addWidget(self.maint_block)
        maint_layout.addWidget(self.maint_line)
        maint_layout.addWidget(close_button)
        maint_layout.addWidget(open_button)
        layout.addLayout(maint_layout)

        central_widget.setLayout(layout)

    def add_train_to_monitor(self):
        """Manually add a train to the Train Monitoring Table."""
        train_num = self.train_number.text()
        train_line = self.train_line.currentText()
        train_block = self.train_block.text()
        train_speed = self.train_speed.text()
        train_authority = self.train_authority.text()

        if not train_num or not train_block or not train_speed or not train_authority:
            print("Error: All train fields must be filled!")
            return

        row_count = self.ctc_office.tableTrainMonitor.rowCount()
        self.ctc_office.tableTrainMonitor.insertRow(row_count)
        self.ctc_office.tableTrainMonitor.setItem(row_count, 0, QTableWidgetItem(train_num))
        self.ctc_office.tableTrainMonitor.setItem(row_count, 1, QTableWidgetItem(train_line))
        self.ctc_office.tableTrainMonitor.setItem(row_count, 2, QTableWidgetItem(train_block))
        self.ctc_office.tableTrainMonitor.setItem(row_count, 3, QTableWidgetItem(train_speed))
        self.ctc_office.tableTrainMonitor.setItem(row_count, 4, QTableWidgetItem(train_authority))

        # Mark the block as occupied
        self.ctc_office.testbench.set_block_occupied(int(train_block), train_line)
        # Switch to the line's occupancy view and update table
        occupancy_line = f"{train_line} Occupancy"
        self.ctc_office.comboBlockOccupancy.setCurrentText(occupancy_line)
        self.ctc_office.testbench.update_block_occupancy_table()

        print(f"Added Train {train_num} on {train_line}, Block {train_block} at {train_speed} mph, Authority {train_authority}")

    def occupy_block(self):
        """Manually occupy a block."""
        block_num = self.block_number.text()
        block_line = self.block_line.currentText()

        if not block_num:
            print("Error: Block number is required!")
            return

        self.ctc_office.testbench.set_block_occupied(int(block_num), block_line)
        # Switch to the line's occupancy view and update table
        occupancy_line = f"{block_line} Occupancy"
        self.ctc_office.comboBlockOccupancy.setCurrentText(occupancy_line)
        self.ctc_office.testbench.update_block_occupancy_table()

        print(f"Block {block_num} on {block_line} is now OCCUPIED.")

    def free_block(self):
        """Manually free a block."""
        block_num = self.block_number.text()
        block_line = self.block_line.currentText()

        if not block_num:
            print("Error: Block number is required!")
            return

        self.ctc_office.testbench.set_block_unoccupied(int(block_num), block_line)
        # Switch to the line's occupancy view and update table
        occupancy_line = f"{block_line} Occupancy"
        self.ctc_office.comboBlockOccupancy.setCurrentText(occupancy_line)
        self.ctc_office.testbench.update_block_occupancy_table()

        print(f"Block {block_num} on {block_line} is now UNOCCUPIED.")

    def close_track(self):
        """Manually close a track for maintenance."""
        maint_block = self.maint_block.text()
        maint_line = self.maint_line.currentText()

        if not maint_block:
            print("Error: Block number is required!")
            return

        # Set the maintLine and maintBlock in the main UI
        self.ctc_office.maintLine.setCurrentText(maint_line)
        self.ctc_office.maintBlock.setCurrentText(f"Block {maint_block}")

        # Simulate button click to close track
        self.ctc_office.btnCloseTrack.click()

        # Switch to the line's occupancy view and update table
        occupancy_line = f"{maint_line} Occupancy"
        self.ctc_office.comboBlockOccupancy.setCurrentText(occupancy_line)
        self.ctc_office.testbench.update_block_occupancy_table()

        print(f"Track Block {maint_block} on {maint_line} is CLOSED for maintenance.")

    def open_track(self):
        """Manually open a track from maintenance."""
        maint_block = self.maint_block.text()
        maint_line = self.maint_line.currentText()

        if not maint_block:
            print("Error: Block number is required!")
            return

        # Set the maintLine and maintBlock in the main UI
        self.ctc_office.maintLine.setCurrentText(maint_line)
        self.ctc_office.maintBlock.setCurrentText(f"Block {maint_block}")

        # Simulate button click to open track
        self.ctc_office.btnOpenTrack.click()

        # Switch to the line's occupancy view and update table
        occupancy_line = f"{maint_line} Occupancy"
        self.ctc_office.comboBlockOccupancy.setCurrentText(occupancy_line)
        self.ctc_office.testbench.update_block_occupancy_table()

        print(f"Track Block {maint_block} on {maint_line} is OPEN.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_ui = CTCTestUI()
    test_ui.show()
    sys.exit(app.exec())