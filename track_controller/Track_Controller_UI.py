import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, 
    QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout, QScrollArea, QHeaderView
)
from PyQt6.QtCore import Qt

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
        self.occupancy_dropdown.addItems(["Train", "Maintenance", "Error"])
        self.occupancy_dropdown.currentIndexChanged.connect(self.update_occupancy_type)
        
        self.authority_input = QLineEdit()
        self.authority_input.setPlaceholderText("Authority (feet)")
        self.authority_input.setVisible(False)
        self.authority_input.textChanged.connect(self.update_authority)
        
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Occupancy Type:"))
        options_layout.addWidget(self.occupancy_dropdown)
        options_layout.addWidget(self.authority_input)
        
        layout.addLayout(options_layout)
        centralWidget.setLayout(layout)
    
    def select_block(self, block):
        self.current_block = block
        if self.controller.block_occupancy[block]:
            occupancy_type = self.controller.occupancy_type[block]
            if occupancy_type == "Train":
                self.occupancy_dropdown.setCurrentText("Train")
                self.authority_input.setVisible(True)
                self.authority_input.setText(str(self.controller.train_authority[block]))
            elif occupancy_type == "Maintenance":
                self.occupancy_dropdown.setCurrentText("Maintenance")
                self.authority_input.setVisible(False)
            elif occupancy_type == "Error":
                self.occupancy_dropdown.setCurrentText("Error")
                self.authority_input.setVisible(False)
        else:
            self.occupancy_dropdown.setCurrentIndex(-1)
            self.authority_input.setVisible(False)
        
        self.controller.block_occupancy[block] = self.occupancy_buttons[block].isChecked()
        
        if not self.controller.block_occupancy[block]:
            self.controller.train_authority[block] = None
            self.authority_input.clear()
        
        self.controller.update_plc_states()
        self.controller.update_ui()
    
    def update_occupancy_type(self):
        occupancy_type = self.occupancy_dropdown.currentText()
        self.authority_input.setVisible(occupancy_type == "Train")
        if self.current_block is not None:
            if occupancy_type == "Empty":
                self.controller.block_occupancy[self.current_block] = False
                self.controller.occupancy_type[self.current_block] = None
                self.controller.train_authority[self.current_block] = None  
                self.authority_input.clear()
            else:
                self.controller.occupancy_type[self.current_block] = occupancy_type
            self.controller.update_plc_states()
            self.controller.update_ui()
    
    def update_authority(self):
        if self.current_block is not None and self.controller.occupancy_type[self.current_block] == "Train":
            authority = self.authority_input.text()
            self.controller.train_authority[self.current_block] = int(authority) if authority.isdigit() else None
            self.controller.update_plc_states()
            self.controller.update_ui()
    
    def set_manual_mode(self, manual_mode):
        for btn in self.occupancy_buttons:
            btn.setEnabled(not manual_mode)

class TrackController(QMainWindow):
    def __init__(self, line_name, num_blocks, num_switches, num_lights, num_crossings):
        super().__init__()
        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 300, 600)
        self.line_name = line_name
        self.num_blocks = num_blocks
        self.num_switches = num_switches
        self.num_lights = num_lights
        self.num_crossings = num_crossings
        
        self.block_occupancy = [False] * num_blocks
        self.occupancy_type = [None] * num_blocks
        self.train_authority = [None] * num_blocks
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
        
        self.block_table = QTableWidget(10, 2) 
        self.block_table.setHorizontalHeaderLabels(["Block", "Occupancy"])
        self.block_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.update_block_table()
        
        self.pagination_buttons = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.pagination_buttons.addWidget(self.prev_button)
        self.pagination_buttons.addWidget(self.next_button)
        
        layout.addWidget(self.line_label)
        layout.addWidget(self.manual_mode_checkbox)
        layout.addWidget(QLabel("Block Occupancy"))
        layout.addWidget(self.block_table)
        layout.addLayout(self.pagination_buttons)
        
        self.switch_buttons = []
        switch_layout = QHBoxLayout()
        for i in range(self.num_switches):
            btn = QPushButton(f"Switch {i+1}: {'On' if self.switch_states[i] else 'Off'}")
            btn.setStyleSheet(f"background-color: {'green' if self.switch_states[i] else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_switch_state(idx))
            self.switch_buttons.append(btn)
            switch_layout.addWidget(btn)
        
        self.light_buttons = []
        light_layout = QHBoxLayout()
        for i in range(self.num_lights):
            btn = QPushButton(f"Light {i+1}: {'Green' if self.light_states[i] else 'Red'}")
            btn.setStyleSheet(f"background-color: {'green' if self.light_states[i] else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_light_state(idx))
            self.light_buttons.append(btn)
            light_layout.addWidget(btn)
        
        self.crossing_label = QLabel("Crossing States:")
        
        self.crossing_buttons = []
        crossing_layout = QHBoxLayout()
        for i in range(self.num_crossings):
            btn = QPushButton(f"Crossing {i+1}: {'Closed' if self.crossing_states[i] else 'Open'}")
            btn.setStyleSheet(f"background-color: {'red' if self.crossing_states[i] else 'green'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_crossing_state(idx))
            self.crossing_buttons.append(btn)
            crossing_layout.addWidget(btn)
        
        self.train_table = QTableWidget(10, 2)   
        self.train_table.setHorizontalHeaderLabels(["Block", "Authority"])
        self.train_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.update_train_table()
        
        layout.addWidget(QLabel("Outputs"))
        layout.addLayout(switch_layout)
        layout.addLayout(light_layout)
        layout.addWidget(self.crossing_label)
        layout.addLayout(crossing_layout)
        layout.addWidget(QLabel("Train Authority"))
        layout.addWidget(self.train_table)
        
        self.testbench_button = QPushButton("Open Test Bench")
        self.testbench_button.clicked.connect(self.open_testbench)
        layout.addWidget(self.testbench_button)
        
        centralWidget.setLayout(layout)
    
    def toggle_manual_mode(self):
        self.manual_mode = self.manual_mode_checkbox.isChecked()
        self.update_ui()
        
    def toggle_switch_state(self, idx):
        if self.manual_mode:
            block_a_occupied = self.block_occupancy[0] or self.block_occupancy[1] or self.block_occupancy[2] or self.block_occupancy[3] or self.block_occupancy[4]
            block_b_occupied = self.block_occupancy[5] or self.block_occupancy[6] or self.block_occupancy[7] or self.block_occupancy[8] or self.block_occupancy[9]
            block_c_occupied = self.block_occupancy[10] or self.block_occupancy[11] or self.block_occupancy[12] or self.block_occupancy[13] or self.block_occupancy[14]
            
            new_state = not self.switch_states[idx]
            
            # Prevent switch from being turned on if Block A and Block C are occupied
            if new_state and block_a_occupied and block_c_occupied and (not block_b_occupied):
                return
            
            # Prevent switch from being turned off if Block A and Block B are occupied
            if not new_state and block_a_occupied and block_b_occupied and (not block_c_occupied):
                return
            
            self.switch_states[idx] = new_state
            self.switch_buttons[idx].setText(f"Switch {idx+1}: {'On' if self.switch_states[idx] else 'Off'}")
            self.switch_buttons[idx].setStyleSheet(f"background-color: {'green' if self.switch_states[idx] else 'red'}")
            self.update_ui()

    def toggle_light_state(self, idx):
        if self.manual_mode:
            block_a_occupied = self.block_occupancy[0] or self.block_occupancy[1] or self.block_occupancy[2] or self.block_occupancy[3] or self.block_occupancy[4]
            block_b_occupied = self.block_occupancy[5] or self.block_occupancy[6] or self.block_occupancy[7] or self.block_occupancy[8] or self.block_occupancy[9]
            block_c_occupied = self.block_occupancy[10] or self.block_occupancy[11] or self.block_occupancy[12] or self.block_occupancy[13] or self.block_occupancy[14]
            
            # If Block A and Block B are occupied, turn off Light 1
            if idx == 0 and block_a_occupied and block_b_occupied:
                self.light_states[idx] = False
                self.light_buttons[idx].setText(f"Light {idx+1}: {'Green' if self.light_states[idx] else 'Red'}")
                self.light_buttons[idx].setStyleSheet(f"background-color: {'green' if self.light_states[idx] else 'red'}")
                self.update_ui()
                return
            
            # If Block A and Block C are occupied, turn off Light 2
            if idx == 1 and block_a_occupied and block_c_occupied:
                self.light_states[idx] = False
                self.light_buttons[idx].setText(f"Light {idx+1}: {'Green' if self.light_states[idx] else 'Red'}")
                self.light_buttons[idx].setStyleSheet(f"background-color: {'green' if self.light_states[idx] else 'red'}")
                self.update_ui()
                return
            
            # If Block A, Block B, and Block C are occupied, turn off both lights
            if block_a_occupied and block_b_occupied and block_c_occupied:
                self.light_states[0] = False
                self.light_states[1] = False
                self.light_buttons[0].setText(f"Light 1: {'Green' if self.light_states[0] else 'Red'}")
                self.light_buttons[0].setStyleSheet(f"background-color: {'green' if self.light_states[0] else 'red'}")
                self.light_buttons[1].setText(f"Light 2: {'Green' if self.light_states[1] else 'Red'}")
                self.light_buttons[1].setStyleSheet(f"background-color: {'green' if self.light_states[1] else 'red'}")
                self.update_ui()
                return
            
            # Otherwise, toggle the light state
            self.light_states[idx] = not self.light_states[idx]
            self.light_buttons[idx].setText(f"Light {idx+1}: {'Green' if self.light_states[idx] else 'Red'}")
            self.light_buttons[idx].setStyleSheet(f"background-color: {'green' if self.light_states[idx] else 'red'}")
            self.update_ui()

    def toggle_crossing_state(self, idx):
        if self.manual_mode:

            crossing_occupied = self.block_occupancy[1] or self.block_occupancy[2] or self.block_occupancy[3]
            
            if crossing_occupied and self.crossing_states[idx]:
                return
            
            self.crossing_states[idx] = not self.crossing_states[idx]
            self.crossing_buttons[idx].setText(f"Crossing {idx+1}: {'Closed' if self.crossing_states[idx] else 'Open'}")
            self.crossing_buttons[idx].setStyleSheet(f"background-color: {'red' if self.crossing_states[idx] else 'green'}")
            self.update_ui()
    
    def update_plc_states(self):
        self.switch_states, self.light_states, self.crossing_states = self.update_plc_logic(self.block_occupancy)
    
    def update_plc_logic(self, block_occupancy):
        switch_states = [False] * self.num_switches 
        light_states = [False] * self.num_lights  
        crossing_states = [False] * self.num_crossings  

        block_a_occupied = block_occupancy[0] or block_occupancy[1] or  block_occupancy[2] or  block_occupancy[3] or  block_occupancy[4] 
        block_b_occupied = block_occupancy[5] or block_occupancy[6] or  block_occupancy[7] or  block_occupancy[8] or  block_occupancy[9] 
        block_c_occupied = block_occupancy[10] or block_occupancy[11] or  block_occupancy[12] or  block_occupancy[13] or  block_occupancy[14] 

        switch_states[0] = block_a_occupied and block_b_occupied

        light_states[0] = not((block_a_occupied and  block_b_occupied) or (block_a_occupied and  block_b_occupied and block_c_occupied))
        light_states[1] = not((block_a_occupied and  block_c_occupied) or (block_a_occupied and  block_b_occupied and block_c_occupied))

        crossing_states[0] = block_occupancy[1] or block_occupancy[2] or  block_occupancy[3]
        
        return switch_states, light_states, crossing_states
    
    def update_ui(self):
        self.update_block_table()
        
        self.update_train_table()
        
        for i, state in enumerate(self.switch_states):
            self.switch_buttons[i].setText(f"Switch {i+1}: {'On' if state else 'Off'}")
            self.switch_buttons[i].setStyleSheet(f"background-color: {'green' if state else 'red'}")
        
        for i, state in enumerate(self.light_states):
            self.light_buttons[i].setText(f"Light {i+1}: {'Green' if state else 'Red'}")
            self.light_buttons[i].setStyleSheet(f"background-color: {'green' if state else 'red'}")
        
        for i, state in enumerate(self.crossing_states):
            self.crossing_buttons[i].setText(f"Crossing {i+1}: {'Closed' if state else 'Open'}")
            self.crossing_buttons[i].setStyleSheet(f"background-color: {'red' if state else 'green'}")

    def update_block_table(self, start_block=0):
        self.block_table.setRowCount(10)
        for i in range(10):
            block_num = start_block + i
            if block_num < self.num_blocks:
                block_item = QTableWidgetItem(f"{block_num+1}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Make it read-only
                self.block_table.setItem(i, 0, block_item)

                occupancy_text = "Occupied" if self.block_occupancy[block_num] else "Empty"
                occupancy_item = QTableWidgetItem(occupancy_text)
                occupancy_item.setFlags(Qt.ItemFlag.ItemIsEnabled) 
                self.block_table.setItem(i, 1, occupancy_item)
            else:
                # Empty rows
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(Qt.ItemFlag.ItemIsEnabled) 
                self.block_table.setItem(i, 0, empty_item)
                self.block_table.setItem(i, 1, empty_item)

    def update_train_table(self, start_block=0):
        self.train_table.setRowCount(10)
        for i in range(10):
            block_num = start_block + i
            if block_num < self.num_blocks:
                block_item = QTableWidgetItem(f"{block_num+1}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  
                self.train_table.setItem(i, 0, block_item)

                authority_text = str(self.train_authority[block_num]) if self.train_authority[block_num] is not None else ""
                authority_item = QTableWidgetItem(authority_text)
                authority_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  
                self.train_table.setItem(i, 1, authority_item)
            else:
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(Qt.ItemFlag.ItemIsEnabled) 
                self.train_table.setItem(i, 0, empty_item)
                self.train_table.setItem(i, 1, empty_item)
    
    def prev_page(self):
        current_start = self.block_table.item(0, 0).text()
        if current_start:
            start_block = max(int(current_start) - 10, 0)
            self.update_block_table(start_block)
            self.update_train_table(start_block)
    
    def next_page(self):
        current_start = self.block_table.item(0, 0).text()
        if current_start:
            start_block = min(int(current_start) + 10, self.num_blocks - 10)
            self.update_block_table(start_block)
            self.update_train_table(start_block)
    
    def open_testbench(self):
        self.testbench = TestBench(self)
        self.testbench.show()

def main():
    app = QApplication(sys.argv)
    window = TrackController("Red Line", 155, 1, 2, 1)  # blocks, switch, lights, crossings
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()