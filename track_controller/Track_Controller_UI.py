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
        if not self.controller.manual_mode:  # Only allow selection if not in manual mode
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
                    self.occupancy_dropdown.setCurrentText("Occupied by...")
                    self.authority_input.setVisible(False)
            else:
                self.occupancy_dropdown.setCurrentText("Empty")
                self.authority_input.setVisible(False)
            
            # Update block occupancy
            self.controller.block_occupancy[block] = self.occupancy_buttons[block].isChecked()
            
            # Reset authority if block becomes unoccupied
            if not self.controller.block_occupancy[block]:
                self.controller.train_authority[block] = None
                self.authority_input.clear()
            
            self.controller.update_plc_states()
            self.controller.update_ui()
    
    def update_occupancy_type(self):
        if not self.controller.manual_mode:  
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
        if not self.controller.manual_mode:  
            if self.current_block is not None and self.controller.occupancy_type[self.current_block] == "Train":
                authority = self.authority_input.text()
                self.controller.train_authority[self.current_block] = int(authority) if authority.isdigit() else None
                self.controller.update_plc_states()
                self.controller.update_ui()
    
    def set_manual_mode(self, manual_mode):
        for btn in self.occupancy_buttons:
            btn.setEnabled(not manual_mode)
        self.occupancy_dropdown.setEnabled(not manual_mode)
        self.authority_input.setEnabled(not manual_mode)

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
        
        self.block_table = QTableWidget(self.num_blocks, 2)
        self.block_table.setHorizontalHeaderLabels(["Block", "Occupancy"])
        for i in range(self.num_blocks):
            self.block_table.setItem(i, 0, QTableWidgetItem(f"{i+1}"))
            self.block_table.setItem(i, 1, QTableWidgetItem("Empty"))
        self.block_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only
        
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
        
        self.train_table = QTableWidget(self.num_blocks, 2)
        self.train_table.setHorizontalHeaderLabels(["Block", "Authority"])
        for i in range(self.num_blocks):
            self.train_table.setItem(i, 0, QTableWidgetItem(f"{i+1}"))
            self.train_table.setItem(i, 1, QTableWidgetItem(""))
        self.train_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only
        
        layout.addWidget(self.line_label)
        layout.addWidget(self.manual_mode_checkbox)
        layout.addWidget(QLabel("Block Occupancy"))
        layout.addWidget(self.block_table)
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
        if hasattr(self, 'testbench'):
            self.testbench.set_manual_mode(self.manual_mode)
    
    def toggle_switch_state(self, idx):
        if self.manual_mode:
            self.switch_states[idx] = not self.switch_states[idx]
            self.switch_buttons[idx].setText(f"Switch {idx+1}: {'On' if self.switch_states[idx] else 'Off'}")
            self.switch_buttons[idx].setStyleSheet(f"background-color: {'green' if self.switch_states[idx] else 'red'}")
            self.update_ui()
    
    def toggle_light_state(self, idx):
        if self.manual_mode:
            self.light_states[idx] = not self.light_states[idx]
            self.light_buttons[idx].setText(f"Light {idx+1}: {'Green' if self.light_states[idx] else 'Red'}")
            self.light_buttons[idx].setStyleSheet(f"background-color: {'green' if self.light_states[idx] else 'red'}")
            self.update_ui()
    
    def toggle_crossing_state(self, idx):
        if self.manual_mode:
            self.crossing_states[idx] = not self.crossing_states[idx]
            self.crossing_buttons[idx].setText(f"Crossing {idx+1}: {'Closed' if self.crossing_states[idx] else 'Open'}")
            self.crossing_buttons[idx].setStyleSheet(f"background-color: {'red' if self.crossing_states[idx] else 'green'}")
            self.update_ui()
    
    def update_plc_states(self):
        self.switch_states, self.light_states, self.crossing_states = self.update_plc_logic(self.block_occupancy)
    
    def update_plc_logic(self, block_occupancy):
        switch_states = [False] * self.num_switches  # Boolean array
        light_states = [False] * self.num_lights  # Boolean array (Green = True, Red = False)
        crossing_states = [False] * self.num_crossings  # Boolean array (Closed = True, Open = False)

        # Input conditions
        block_a_occupied = any(block_occupancy[i] for i in range(5))
        block_b_occupied = any(block_occupancy[i] for i in range(5, 10))
        block_c_occupied = any(block_occupancy[i] for i in range(10, 15))

        # Switch Logic
        switch_states[0] = block_a_occupied and block_b_occupied

        # Light Logic (Green = True, Red = False)
        light_states[0] = not((block_a_occupied and  block_c_occupied) or (block_a_occupied and  block_b_occupied and block_c_occupied))
        light_states[1] = not((block_a_occupied and  block_b_occupied) or (block_a_occupied and  block_b_occupied and block_c_occupied))

        # Crossing Logic (Closed = True, Open = False)
        crossing_states[0] = any(block_occupancy[i] for i in [1, 2, 3])
        
        return switch_states, light_states, crossing_states
    
    def update_ui(self):
        # Update block occupancy table
        for i in range(self.num_blocks):
            occupancy_text = "Occupied" if self.block_occupancy[i] else "Empty"
            self.block_table.setItem(i, 1, QTableWidgetItem(occupancy_text))
        
        # Update train authority table
        for i in range(self.num_blocks):
            authority_text = str(self.train_authority[i]) if self.train_authority[i] is not None else ""
            self.train_table.setItem(i, 1, QTableWidgetItem(authority_text))
        
        # Update switch, light, and crossing buttons
        for i, state in enumerate(self.switch_states):
            self.switch_buttons[i].setText(f"Switch {i+1}: {'On' if state else 'Off'}")
            self.switch_buttons[i].setStyleSheet(f"background-color: {'green' if state else 'red'}")
        
        for i, state in enumerate(self.light_states):
            self.light_buttons[i].setText(f"Light {i+1}: {'Green' if state else 'Red'}")
            self.light_buttons[i].setStyleSheet(f"background-color: {'green' if state else 'red'}")
        
        for i, state in enumerate(self.crossing_states):
            self.crossing_buttons[i].setText(f"Crossing {i+1}: {'Closed' if state else 'Open'}")
            self.crossing_buttons[i].setStyleSheet(f"background-color: {'red' if state else 'green'}")

    def open_testbench(self):
        self.testbench = TestBench(self)
        self.testbench.show()

def main():
    app = QApplication(sys.argv)
    window = TrackController("Red Line", 15, 1, 2, 1)  # blocks, switch, lights, crossings
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()