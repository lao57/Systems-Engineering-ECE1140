import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, 
    QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout, QScrollArea, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Import the external logic
from plc_logic import update_plc_logic
from plc_logic import update_plc_logic2
from wayside import WAYSIDE

app = QApplication(sys.argv)
app.setFont(QFont("Arial", 14))
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
        self.occupancy_dropdown.addItems(["Train", "Maintenance/Error"])
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
                self.authority_input.setText(str(self.controller.section_authority[self.controller.get_section(block)]))
            elif occupancy_type == "Maintenance/Error":
                self.occupancy_dropdown.setCurrentText("Maintenance/Error")
                self.authority_input.setVisible(False)

        else:
            self.occupancy_dropdown.setCurrentIndex(-1)
            self.authority_input.setVisible(False)
        
        self.controller.block_occupancy[block] = self.occupancy_buttons[block].isChecked()
        
        if not self.controller.block_occupancy[block]:
            self.controller.section_authority[self.controller.get_section(block)] = None
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
                self.controller.section_authority[self.controller.get_section(self.current_block)] = None  
                self.authority_input.clear()
            else:
                self.controller.occupancy_type[self.current_block] = occupancy_type
            self.controller.update_plc_states()
            self.controller.update_ui()
    
    def update_authority(self):
        if self.current_block is not None and self.controller.occupancy_type[self.current_block] == "Train":
            authority = self.authority_input.text()
            self.controller.section_authority[self.controller.get_section(self.current_block)] = int(authority) if authority.isdigit() else None
            self.controller.update_plc_states()
            self.controller.update_ui()
    
    def set_manual_mode(self, manual_mode):
        for btn in self.occupancy_buttons:
            btn.setEnabled(not manual_mode)

class TrackController(QMainWindow):
    def __init__(self, num_blocks, num_switches, num_lights, num_crossings):
        super().__init__()
        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 300, 600)
        self.num_blocks = num_blocks
        self.num_switches = num_switches
        self.num_lights = num_lights
        self.num_crossings = num_crossings
        
        self.block_occupancy = [False] * num_blocks
        self.occupancy_type = [None] * num_blocks
        self.section_authority = {"A": None, "B": None, "C": None}  # Section authority
        self.switch_states = [False] * num_switches  
        self.light_states = [False] * num_lights  
        self.crossing_states = [False] * num_crossings 
        self.manual_mode = False

        # Initialize the wayside controller
        self.wayside = WAYSIDE(
            start_block=0,
            end_block=15,
            num_switches=1,
            num_lights=0,
            num_crossings=1,
            logic_function=update_plc_logic
        )
        self.wayside2 = WAYSIDE(
            start_block=0,
            end_block= 15,
            num_switches=0,
            num_lights=2,
            num_crossings=0,
            logic_function=update_plc_logic2
        )

        self.initUI()
    
    def get_section(self, block):
        if block < 5:
            return "A"
        elif block < 10:
            return "B"
        else:
            return "C"
    
    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()
        
        self.manual_mode_checkbox = QCheckBox("Manual Mode")
        self.manual_mode_checkbox.stateChanged.connect(self.toggle_manual_mode)
        
        self.block_table = QTableWidget(20, 2) 
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
        
        self.section_table = QTableWidget(3, 2)  # Only 3 rows for sections A, B, C
        self.section_table.setHorizontalHeaderLabels(["Section", "Authority"])
        self.section_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.section_table.setMaximumHeight(150)  # Limit the height to make it compact
                
        layout.addWidget(QLabel("Outputs"))
        layout.addLayout(switch_layout)
        layout.addLayout(light_layout)
        layout.addWidget(self.crossing_label)
        layout.addLayout(crossing_layout)
        layout.addWidget(QLabel("Section Authority"))
        layout.addWidget(self.section_table)
        
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
        # Extract block occupancy for each wayside controller
        block_occupancy_wayside1 = [
            self.block_occupancy[block] for block in range(self.wayside.start_block, self.wayside.end_block)
        ]
        block_occupancy_wayside2 = [
            self.block_occupancy[block] for block in range(self.wayside2.start_block, self.wayside2.end_block)
        ]

        # Use the first wayside controller to update the PLC states for its blocks
        switch_states1, light_states1, crossing_states1 = self.wayside.update_plc_logic(
            block_occupancy=block_occupancy_wayside1,
            errors=None,  # You can pass errors if needed
            maintenance=None  # You can pass maintenance if needed
        )

        # Use the second wayside controller to update the PLC states for its blocks
        switch_states2, light_states2, crossing_states2 = self.wayside2.update_plc_logic(
            block_occupancy=block_occupancy_wayside2,
            errors=None,  # You can pass errors if needed
            maintenance=None  # You can pass maintenance if needed
        )

        # Combine the states from both wayside controllers
        self.switch_states = switch_states1 + switch_states2
        self.light_states = light_states1 + light_states2
        self.crossing_states = crossing_states1 + crossing_states2
        
    def update_ui(self):
        self.update_block_table()
        
        self.update_section_table()
        
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
        self.block_table.setRowCount(20)  
        for i in range(20):
            block_num = start_block + i
            if block_num < self.num_blocks:
                # Block number
                block_item = QTableWidgetItem(f"{block_num+1}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 0, block_item)

                # Occupancy status
                if self.block_occupancy[block_num]:
                    occupancy_type = self.occupancy_type[block_num]
                    if occupancy_type == "Train":
                        occupancy_display = "Train"
                        background_color = Qt.GlobalColor.lightGray  # Highlight for Train
                    elif occupancy_type == "Maintenance/Error":
                        occupancy_display = "Maintenance/Error"
                        background_color = Qt.GlobalColor.darkRed  # Highlight for Maintenance/Error
                    else:
                        occupancy_display = "Occupied"  # Fallback for other cases
                        background_color = Qt.GlobalColor.lightGray  # Default highlight
                else:
                    occupancy_display = "Unoccupied"
                    background_color = Qt.GlobalColor.transparent  # No highlight for unoccupied

                # Set the occupancy item with the appropriate background color
                occupancy_item = QTableWidgetItem(occupancy_display)
                occupancy_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                occupancy_item.setBackground(background_color)
                self.block_table.setItem(i, 1, occupancy_item)
            else:
                # Empty cells for blocks beyond the range
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 0, empty_item)
                self.block_table.setItem(i, 1, empty_item)      

    def update_section_table(self):
        self.section_table.setRowCount(3)
        sections = ["A", "B", "C"]
        for i, section in enumerate(sections):
            section_item = QTableWidgetItem(section)
            section_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  
            self.section_table.setItem(i, 0, section_item)

            authority_text = str(self.section_authority[section]) if self.section_authority[section] is not None else ""
            authority_item = QTableWidgetItem(authority_text)
            authority_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  
            self.section_table.setItem(i, 1, authority_item)

    def prev_page(self):
        current_start = int(self.block_table.item(0, 0).text()) if self.block_table.item(0, 0).text() else 1
        start_block = max(current_start - 20, 0)
        self.update_block_table(start_block)

    def next_page(self):
        current_start = int(self.block_table.item(0, 0).text()) if self.block_table.item(0, 0).text() else 1
        start_block = min(current_start + 19, self.num_blocks)  # Ensure start_block doesn't exceed the last block
        self.update_block_table(start_block)

    def open_testbench(self):
        self.testbench = TestBench(self)
        self.testbench.show()

def main():
    app = QApplication(sys.argv)
    window = TrackController(15, 1, 2, 1)  # blocks, switch, lights, crossings
    window.show()
    window2 = TestBench(window)  # blocks, switch, lights, crossings
    window2.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()