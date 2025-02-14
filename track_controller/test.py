import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout, QScrollArea
)

class TestBench(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Test Bench")
        self.setGeometry(200, 200, 800, 600)
        self.current_block = None
        self.initUI()
    
    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        
        self.occupancy_buttons = []
        for i in range(self.controller.num_blocks):
            btn = QPushButton(f"Block {i+1}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, block=i: self.select_block(block))
            self.occupancy_buttons.append(btn)
            self.grid_layout.addWidget(btn, i // 10, i % 10)
        
        scroll_widget.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        self.occupancy_dropdown = QComboBox()
        self.occupancy_dropdown.addItems(["Occupied by...", "Train", "Maintenance", "Error", "Empty"])
        self.occupancy_dropdown.currentIndexChanged.connect(self.update_occupancy_type)
        
        self.train_number_input = QLineEdit()  # Input for train number
        self.train_number_input.setPlaceholderText("Train Number")
        self.train_number_input.setVisible(False)
        
        self.authority_input = QLineEdit()
        self.authority_input.setPlaceholderText("Authority (feet)")
        self.authority_input.setVisible(False)
        self.authority_input.textChanged.connect(self.update_authority)
        
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Occupancy Type:"))
        options_layout.addWidget(self.occupancy_dropdown)
        options_layout.addWidget(self.train_number_input)
        options_layout.addWidget(self.authority_input)
        
        layout.addLayout(options_layout)
        centralWidget.setLayout(layout)
    
    def select_block(self, block):
        if not self.controller.manual_mode:
            self.current_block = block
            if self.controller.block_occupancy[block]:
                occupancy_type = self.controller.occupancy_type[block]
                if occupancy_type == "Train":
                    self.occupancy_dropdown.setCurrentText("Train")
                    self.train_number_input.setVisible(True)
                    self.authority_input.setVisible(True)
                    self.train_number_input.setText(str(self.controller.train_numbers[block]))
                    self.authority_input.setText(str(self.controller.train_authority[block]))
                else:
                    self.train_number_input.setVisible(False)
                    self.authority_input.setVisible(False)
            else:
                self.occupancy_dropdown.setCurrentText("Empty")
                self.train_number_input.setVisible(False)
                self.authority_input.setVisible(False)
            
            self.controller.block_occupancy[block] = self.occupancy_buttons[block].isChecked()
            if not self.controller.block_occupancy[block]:
                self.controller.train_numbers[block] = None
                self.controller.train_authority[block] = None
                self.train_number_input.clear()
                self.authority_input.clear()
            
            self.controller.update_plc_states()
            self.controller.update_ui()
    
    def update_occupancy_type(self):
        if not self.controller.manual_mode:
            occupancy_type = self.occupancy_dropdown.currentText()
            self.train_number_input.setVisible(occupancy_type == "Train")
            self.authority_input.setVisible(occupancy_type == "Train")
            if self.current_block is not None:
                if occupancy_type == "Empty":
                    self.controller.block_occupancy[self.current_block] = False
                    self.controller.occupancy_type[self.current_block] = None
                    self.controller.train_numbers[self.current_block] = None
                    self.controller.train_authority[self.current_block] = None
                    self.train_number_input.clear()
                    self.authority_input.clear()
                else:
                    self.controller.occupancy_type[self.current_block] = occupancy_type
                self.controller.update_plc_states()
                self.controller.update_ui()
    
    def update_authority(self):
        if not self.controller.manual_mode:
            if self.current_block is not None and self.controller.occupancy_type[self.current_block] == "Train":
                train_number = self.train_number_input.text()
                authority = self.authority_input.text()
                self.controller.train_numbers[self.current_block] = int(train_number) if train_number.isdigit() else None
                self.controller.train_authority[self.current_block] = int(authority) if authority.isdigit() else None
                self.controller.update_plc_states()
                self.controller.update_ui()

class TrackController(QMainWindow):
    def __init__(self, line_name, num_blocks, num_switches, num_lights, num_crossings):
        super().__init__()
        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 800, 600)
        self.line_name = line_name
        self.num_blocks = num_blocks
        self.num_switches = num_switches
        self.num_lights = num_lights
        self.num_crossings = num_crossings
        
        self.block_occupancy = [False] * num_blocks
        self.occupancy_type = [None] * num_blocks
        self.train_numbers = [None] * num_blocks  # Store train numbers
        self.train_authority = [None] * num_blocks  # Store authority
        self.switch_states = [False] * num_switches
        self.light_states = [False] * num_lights
        self.crossing_states = [False] * num_crossings
        self.manual_mode = False
        self.initUI()
    
    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()
        
        self.line_label = QLabel(self.line_name)
        self.manual_mode_checkbox = QCheckBox("Manual Mode")
        self.manual_mode_checkbox.stateChanged.connect(self.toggle_manual_mode)
        
        self.block_table = QTableWidget(self.num_blocks, 2)
        self.block_table.setHorizontalHeaderLabels(["Block", "Occupancy"])
        for i in range(self.num_blocks):
            self.block_table.setItem(i, 0, QTableWidgetItem(f"{i+1}"))
            self.block_table.setItem(i, 1, QTableWidgetItem("Empty"))
        self.block_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Train table now includes train number and authority
        self.train_table = QTableWidget(self.num_blocks, 3)
        self.train_table.setHorizontalHeaderLabels(["Block", "Train Number", "Authority"])
        for i in range(self.num_blocks):
            self.train_table.setItem(i, 0, QTableWidgetItem(f"{i+1}"))
            self.train_table.setItem(i, 1, QTableWidgetItem(""))
            self.train_table.setItem(i, 2, QTableWidgetItem(""))
        self.train_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Add other UI elements (switches, lights, crossings, etc.)
        # ...
        
        layout.addWidget(self.line_label)
        layout.addWidget(self.manual_mode_checkbox)
        layout.addWidget(QLabel("Block Occupancy"))
        layout.addWidget(self.block_table)
        layout.addWidget(QLabel("Train Information"))
        layout.addWidget(self.train_table)
        
        self.testbench_button = QPushButton("Open Test Bench")
        self.testbench_button.clicked.connect(self.open_testbench)
        layout.addWidget(self.testbench_button)
        
        centralWidget.setLayout(layout)
    
    def update_ui(self):
        # Update block occupancy table
        for i in range(self.num_blocks):
            occupancy_text = "Occupied" if self.block_occupancy[i] else "Empty"
            self.block_table.setItem(i, 1, QTableWidgetItem(occupancy_text))
        
        # Update train table with train number and authority
        for i in range(self.num_blocks):
            train_number_text = str(self.train_numbers[i]) if self.train_numbers[i] is not None else ""
            authority_text = str(self.train_authority[i]) if self.train_authority[i] is not None else ""
            self.train_table.setItem(i, 1, QTableWidgetItem(train_number_text))
            self.train_table.setItem(i, 2, QTableWidgetItem(authority_text))
        
        # Update other UI elements (switches, lights, crossings, etc.)
        # ...

def main():
    app = QApplication(sys.argv)
    window = TrackController("Red Line", 15, 1, 2, 1)  # blocks, switch, lights, crossings
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()