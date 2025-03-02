import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTableWidgetItem, QListWidget
)
from CTC_GUI import CTCOffice


class CTCTestUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CTC Office - Test UI")
        self.setGeometry(200, 200, 1000, 800)
        self.ctc_office = CTCOffice()
        self.ctc_office.show()
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Train Input Testing
        train_group = QVBoxLayout()
        train_group.addWidget(QLabel("Test Train Inputs"))
        train_layout = QHBoxLayout()

        self.train_number = QLineEdit(placeholderText="Train Number")
        self.train_line = QComboBox()
        self.train_line.addItems(["Red Line", "Green Line"])
        self.train_block = QLineEdit(placeholderText="Block")
        self.train_speed = QLineEdit(placeholderText="Speed")
        self.train_authority = QLineEdit(placeholderText="Authority")
        train_btn = QPushButton("Add Train", clicked=self.add_train_to_monitor)

        train_layout.addWidget(self.train_number)
        train_layout.addWidget(self.train_line)
        train_layout.addWidget(self.train_block)
        train_layout.addWidget(self.train_speed)
        train_layout.addWidget(self.train_authority)
        train_layout.addWidget(train_btn)
        train_group.addLayout(train_layout)
        layout.addLayout(train_group)

        # Block Occupancy Testing
        block_group = QVBoxLayout()
        block_group.addWidget(QLabel("Test Block Occupancy"))
        block_layout = QHBoxLayout()

        self.block_number = QLineEdit(placeholderText="Block #")
        self.block_line = QComboBox()
        self.block_line.addItems(["Red Line", "Green Line"])
        block_occupy_btn = QPushButton("Occupy", clicked=self.occupy_block)
        block_free_btn = QPushButton("Free", clicked=self.free_block)

        block_layout.addWidget(self.block_number)
        block_layout.addWidget(self.block_line)
        block_layout.addWidget(block_occupy_btn)
        block_layout.addWidget(block_free_btn)
        block_group.addLayout(block_layout)
        layout.addLayout(block_group)

        # Track Maintenance Testing
        maint_group = QVBoxLayout()
        maint_group.addWidget(QLabel("Test Maintenance"))
        maint_layout = QHBoxLayout()

        self.maint_block = QLineEdit(placeholderText="Block #")
        self.maint_line = QComboBox()
        self.maint_line.addItems(["Red Line", "Green Line"])
        close_btn = QPushButton("Close", clicked=self.close_track)
        open_btn = QPushButton("Open", clicked=self.open_track)

        maint_layout.addWidget(self.maint_block)
        maint_layout.addWidget(self.maint_line)
        maint_layout.addWidget(close_btn)
        maint_layout.addWidget(open_btn)
        maint_group.addLayout(maint_layout)
        layout.addLayout(maint_group)

        # Track Component Controls
        comp_group = QVBoxLayout()
        comp_group.addWidget(QLabel("Track Components"))
        comp_layout = QHBoxLayout()

        self.crossing_btn = QPushButton("Toggle Crossing", clicked=self.toggle_crossing)
        self.light1_btn = QPushButton("Toggle Light 1", clicked=self.toggle_light1)
        self.light2_btn = QPushButton("Toggle Light 2", clicked=self.toggle_light2)
        self.switch_btn = QPushButton("Toggle Switch", clicked=self.toggle_switch)

        comp_layout.addWidget(self.crossing_btn)
        comp_layout.addWidget(self.light1_btn)
        comp_layout.addWidget(self.light2_btn)
        comp_layout.addWidget(self.switch_btn)
        comp_group.addLayout(comp_layout)
        layout.addLayout(comp_group)

        # System Analysis Inputs
        sys_analysis_group = QVBoxLayout()
        sys_analysis_group.addWidget(QLabel("System Analysis Inputs"))

        # Line Selection
        line_layout = QHBoxLayout()
        line_layout.addWidget(QLabel("Select Line:"))
        self.sys_analysis_line = QComboBox()
        self.sys_analysis_line.addItems(["Red Line", "Green Line"])
        line_layout.addWidget(self.sys_analysis_line)
        sys_analysis_group.addLayout(line_layout)

        # Input Fields
        input_layout = QHBoxLayout()
        self.throughput_input = QLineEdit(placeholderText="Throughput")
        self.delay_input = QLineEdit(placeholderText="Avg Delay")
        self.failures_input = QLineEdit(placeholderText="# Failures")
        self.failure_pct_input = QLineEdit(placeholderText="Failure %")

        input_layout.addWidget(self.throughput_input)
        input_layout.addWidget(self.delay_input)
        input_layout.addWidget(self.failures_input)
        input_layout.addWidget(self.failure_pct_input)

        # Submit Button
        submit_btn = QPushButton("Update Analysis", clicked=self.update_system_analysis)
        input_layout.addWidget(submit_btn)

        sys_analysis_group.addLayout(input_layout)
        layout.addLayout(sys_analysis_group)

        # Schedule Logs
        layout.addWidget(QLabel("Schedule Logs:"))
        self.schedule_log = QListWidget()
        self.ctc_office.testbench.schedule_logged.connect(self.update_schedule_log)
        layout.addWidget(self.schedule_log)

        central_widget.setLayout(layout)

    def update_schedule_log(self, log_entry):
        self.schedule_log.addItem(log_entry)

    def toggle_crossing(self):
        self.ctc_office.testbench.toggle_crossing()

    def toggle_light1(self):
        self.ctc_office.testbench.toggle_light1()

    def toggle_light2(self):
        self.ctc_office.testbench.toggle_light2()

    def toggle_switch(self):
        self.ctc_office.testbench.toggle_switch()

    def add_train_to_monitor(self):
        train_num = self.train_number.text()
        train_line = self.train_line.currentText()
        train_block = self.train_block.text()
        train_speed = self.train_speed.text()
        train_authority = self.train_authority.text()

        if not all([train_num, train_block, train_speed, train_authority]):
            return

        row = self.ctc_office.tableTrainMonitor.rowCount()
        self.ctc_office.tableTrainMonitor.insertRow(row)
        self.ctc_office.tableTrainMonitor.setItem(row, 0, QTableWidgetItem(train_num))
        self.ctc_office.tableTrainMonitor.setItem(row, 1, QTableWidgetItem(train_line))
        self.ctc_office.tableTrainMonitor.setItem(row, 2, QTableWidgetItem(train_block))
        self.ctc_office.tableTrainMonitor.setItem(row, 3, QTableWidgetItem(train_speed))
        self.ctc_office.tableTrainMonitor.setItem(row, 4, QTableWidgetItem(train_authority))
        self.ctc_office.testbench.set_block_occupied(int(train_block), train_line)
        self.ctc_office.comboBlockOccupancy.setCurrentText(f"{train_line} Occupancy")
        self.ctc_office.testbench.update_block_occupancy_table()

    def occupy_block(self):
        block_num = self.block_number.text()
        block_line = self.block_line.currentText()
        if block_num:
            self.ctc_office.testbench.set_block_occupied(int(block_num), block_line)
            self.ctc_office.comboBlockOccupancy.setCurrentText(f"{block_line} Occupancy")
            self.ctc_office.testbench.update_block_occupancy_table()

    def free_block(self):
        block_num = self.block_number.text()
        block_line = self.block_line.currentText()
        if block_num:
            self.ctc_office.testbench.set_block_unoccupied(int(block_num), block_line)
            self.ctc_office.comboBlockOccupancy.setCurrentText(f"{block_line} Occupancy")
            self.ctc_office.testbench.update_block_occupancy_table()

    def close_track(self):
        block_num = self.maint_block.text()
        line = self.maint_line.currentText()
        if block_num:
            self.ctc_office.maintLine.setCurrentText(line)
            self.ctc_office.maintBlock.setCurrentText(f"Block {block_num}")
            self.ctc_office.btnCloseTrack.click()

    def open_track(self):
        block_num = self.maint_block.text()
        line = self.maint_line.currentText()
        if block_num:
            self.ctc_office.maintLine.setCurrentText(line)
            self.ctc_office.maintBlock.setCurrentText(f"Block {block_num}")
            self.ctc_office.btnOpenTrack.click()

    def update_system_analysis(self):
        line = self.sys_analysis_line.currentText()
        throughput = self.throughput_input.text()
        avg_delay = self.delay_input.text()
        failures = self.failures_input.text()
        failure_pct = self.failure_pct_input.text()

        # Determine row index (Red=0, Green=1)
        row = 0 if "Red" in line else 1


        if throughput:
            self.ctc_office.tableSystemAnalysis.setItem(row, 0, QTableWidgetItem(throughput))
        if avg_delay:
            self.ctc_office.tableSystemAnalysis.setItem(row, 1, QTableWidgetItem(avg_delay))
        if failures:
            self.ctc_office.tableSystemAnalysis.setItem(row, 2, QTableWidgetItem(failures))
        if failure_pct:
            self.ctc_office.tableSystemAnalysis.setItem(row, 3, QTableWidgetItem(f"{failure_pct}%"))

        # Clear inputs
        self.throughput_input.clear()
        self.delay_input.clear()
        self.failures_input.clear()
        self.failure_pct_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_ui = CTCTestUI()
    test_ui.show()
    sys.exit(app.exec())

