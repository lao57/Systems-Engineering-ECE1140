import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, 
    QHBoxLayout, QCheckBox, QHeaderView, QLineEdit, QComboBox, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from wayside import WAYSIDE
from plc_logic import update_plc_logic, update_plc_logic2


class CTC:
    def __init__(self):
        self.maintenance = [False] * 155  # Example: 155 blocks
        self.block_authority = [10] * 155  # Example: block authority values

    def get_maintenance_status(self):
        return self.maintenance
    
    def get_block_authority(self):
        return self.block_authority


class TrackModel:
    def __init__(self):
        self.block_occupancy = [False] * 155  # Example: 155 blocks
        self.errors = [False] * 155  # Example: 155 blocks with errors

    def get_block_occupancy(self):
        return self.block_occupancy

    def get_errors(self):
        return self.errors


class TrackController(QMainWindow):
    def __init__(self, ctc, track_model):
        super().__init__()
        self.ctc = ctc
        self.track_model = track_model

        # Initialize internal states
        self.num_blocks = 155
        self.num_switches = 1
        self.num_lights = 2
        self.num_crossings = 1
        self.switch_state = [False] * self.num_switches
        self.crossing_state = [False] * self.num_crossings
        self.light_state = [False] * self.num_lights
        self.errors = [False] * self.num_blocks
        self.manual_mode = False
        self.current_page = 0  # Track the current page

        # Initialize the wayside controllers
        self.wayside = WAYSIDE(
            start_block=0,
            end_block=155,
            num_switches=1,
            num_lights=0,
            num_crossings=1,
            logic_function=update_plc_logic
        )
        self.wayside2 = WAYSIDE(
            start_block=0,
            end_block=155,
            num_switches=0,
            num_lights=2,
            num_crossings=0,
            logic_function=update_plc_logic2
        )

        # Initialize UI
        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 300, 600)
        self.initUI()

        # Set up a timer to periodically update the UI with external data
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(1000)  # Update every 1 second

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        # Manual Mode Checkbox
        self.manual_mode_checkbox = QCheckBox("Manual Mode")
        self.manual_mode_checkbox.stateChanged.connect(self.toggle_manual_mode)
        layout.addWidget(self.manual_mode_checkbox)

        # Block Occupancy Table
        self.block_table = QTableWidget(20, 2)  # Display 20 blocks at a time
        self.block_table.setHorizontalHeaderLabels(["Block", "Occupancy"])
        self.block_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Block Occupancy"))
        layout.addWidget(self.block_table)

        # Pagination Buttons
        self.pagination_buttons = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.pagination_buttons.addWidget(self.prev_button)
        self.pagination_buttons.addWidget(self.next_button)
        layout.addLayout(self.pagination_buttons)

        # Switch Button
        self.switch_button = QPushButton(f"Switch 1: {'On' if self.switch_state[0] else 'Off'}")
        self.switch_button.setStyleSheet(f"background-color: {'green' if self.switch_state[0] else 'red'}")
        self.switch_button.clicked.connect(lambda: self.toggle_switch_state(0))
        layout.addWidget(self.switch_button)

        # Light Buttons
        self.light_buttons = []
        light_layout = QHBoxLayout()
        for i in range(len(self.light_state)):
            btn = QPushButton(f"Light {i+1}: {'Green' if self.light_state[i] else 'Red'}")
            btn.setStyleSheet(f"background-color: {'green' if self.light_state[i] else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_light_state(idx))
            self.light_buttons.append(btn)
            light_layout.addWidget(btn)
        layout.addLayout(light_layout)

        # Crossing Button
        self.crossing_button = QPushButton(f"Crossing 1: {'Closed' if self.crossing_state[0] else 'Open'}")
        self.crossing_button.setStyleSheet(f"background-color: {'red' if self.crossing_state[0] else 'green'}")
        self.crossing_button.clicked.connect(lambda: self.toggle_crossing_state(0))
        layout.addWidget(self.crossing_button)

        # Block Authority Table
        self.authority_table = QTableWidget(20, 2)  # Display 20 blocks at a time
        self.authority_table.setHorizontalHeaderLabels(["Block", "Authority"])
        self.authority_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Block Authority"))
        layout.addWidget(self.authority_table)

        centralWidget.setLayout(layout)

    def toggle_manual_mode(self):
        self.manual_mode = self.manual_mode_checkbox.isChecked()
    def toggle_switch_state(self, idx):
        if self.manual_mode:
            block_occupancy = self.track_model.get_block_occupancy()
            errors = self.track_model.get_errors()
            maintenance = self.ctc.get_maintenance_status()
            block_occupancy = [block_occupancy[i] or errors[i] or maintenance[i] for i in range(len(block_occupancy))]

            block_a_occupied = block_occupancy[0] or block_occupancy[1] or block_occupancy[2] or block_occupancy[3] or block_occupancy[4]
            block_b_occupied = block_occupancy[5] or block_occupancy[6] or block_occupancy[7] or block_occupancy[8] or block_occupancy[9]
            block_c_occupied = block_occupancy[10] or block_occupancy[11] or block_occupancy[12] or block_occupancy[13] or block_occupancy[14]

            new_state = not self.switch_state[idx]

            # Prevent switch from being turned on if Block A and Block C are occupied
            if new_state and block_a_occupied and block_c_occupied and (not block_b_occupied):
                print("Illegal state: Cannot turn on switch when Block A and Block C are occupied.")
                return

            # Prevent switch from being turned off if Block A and Block B are occupied
            if not new_state and block_a_occupied and block_b_occupied and (not block_c_occupied):
                print("Illegal state: Cannot turn off switch when Block A and Block B are occupied.")
                return

        # Update the switch state
            self.switch_state[idx] = new_state
            self.update_ui_elements()  # Update the UI to reflect the new state
   
    def toggle_light_state(self, idx):
        if self.manual_mode:
            block_occupancy = self.track_model.get_block_occupancy()
            errors = self.track_model.get_errors()
            maintenance = self.ctc.get_maintenance_status()
            block_occupancy = [block_occupancy[i] or errors[i] or maintenance[i] for i in range(len(block_occupancy))]

            block_a_occupied = block_occupancy[0] or block_occupancy[1] or block_occupancy[2] or block_occupancy[3] or block_occupancy[4]
            block_b_occupied = block_occupancy[5] or block_occupancy[6] or block_occupancy[7] or block_occupancy[8] or block_occupancy[9]
            block_c_occupied = block_occupancy[10] or block_occupancy[11] or block_occupancy[12] or block_occupancy[13] or block_occupancy[14]

            # If Block A and Block B are occupied, turn off Light 1
            if idx == 0 and block_a_occupied and block_b_occupied:
                self.light_state[idx] = False
                self.update_ui_elements()
                print("Illegal state: Light 1 turned off due to Block A and Block B being occupied.")
                return

            # If Block A and Block C are occupied, turn off Light 2
            if idx == 1 and block_a_occupied and block_c_occupied:
                self.light_state[idx] = False
                self.update_ui_elements()
                print("Illegal state: Light 2 turned off due to Block A and Block C being occupied.")
                return

            # If Block A, Block B, and Block C are occupied, turn off both lights
            if block_a_occupied and block_b_occupied and block_c_occupied:
                self.light_state[0] = False
                self.light_state[1] = False
                self.update_ui_elements()
                print("Illegal state: Both lights turned off due to Block A, Block B, and Block C being occupied.")
                return

            # Otherwise, toggle the light state
            self.light_state[idx] = not self.light_state[idx]
            self.update_ui_elements()

    def toggle_crossing_state(self, idx):
        if self.manual_mode:
            block_occupancy = self.track_model.get_block_occupancy()
            errors = self.track_model.get_errors()
            maintenance = self.ctc.get_maintenance_status()
            block_occupancy = [block_occupancy[i] or errors[i] or maintenance[i] for i in range(len(block_occupancy))]

            crossing_occupied = block_occupancy[1] or block_occupancy[2] or block_occupancy[3]

            if crossing_occupied and self.crossing_state[idx]:
                print("Illegal state: Cannot toggle crossing when crossing blocks are occupied.")
                return

            # Update the crossing state
            self.crossing_state[idx] = not self.crossing_state[idx]
            self.update_ui_elements()

    def update(self):
        # Fetch data from CTC and Track Model
        maintenance = self.ctc.get_maintenance_status()
        block_occupancy = self.track_model.get_block_occupancy()
        errors = self.track_model.get_errors()
        block_occupancy = [block_occupancy[i] or errors[i] or maintenance[i] for i in range(len(block_occupancy))]

        # Update internal states
        self.errors = errors

        # Update the UI
        self.update_block_table(block_occupancy, maintenance, errors, self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

        # Skip wayside logic update if in manual mode
        if not self.manual_mode:
            self.update_wayside_controllers(block_occupancy, errors, maintenance)

        # Update UI elements (buttons) based on wayside logic
        self.update_ui_elements()

    def update_block_table(self, block_occupancy, maintenance, errors, start_block=0):
        self.block_table.setRowCount(20)  # Display 20 blocks at a time
        for i in range(20):
            block_num = start_block + i
            if block_num < len(block_occupancy):
                # Block number
                block_item = QTableWidgetItem(f"{block_num+1}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 0, block_item)

                # Occupancy status
                if block_occupancy[block_num] or maintenance[block_num] or errors[block_num]:
                    status = "Occupied"
                    if maintenance[block_num]:
                        status = "Maintenance"
                    elif errors[block_num]:
                        status = "Error"
                    background_color = Qt.GlobalColor.lightGray if block_occupancy[block_num] else Qt.GlobalColor.darkRed
                else:
                    status = "Unoccupied"
                    background_color = Qt.GlobalColor.transparent

                occupancy_item = QTableWidgetItem(status)
                occupancy_item.setBackground(background_color)
                occupancy_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 1, occupancy_item)

    def update_authority_table(self, start_block=0):
        self.authority_table.setRowCount(20)  # Display 20 blocks at a time
        block_authority = self.ctc.get_block_authority()
        for i in range(20):
            block_num = start_block + i
            if block_num < len(block_authority):
                # Block number
                block_item = QTableWidgetItem(f"{block_num+1}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 0, block_item)

                # Authority value
                authority_item = QTableWidgetItem(str(block_authority[block_num]))
                authority_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 1, authority_item)

    def update_wayside_controllers(self, block_occupancy, errors, maintenance):
        # Update wayside controllers
        switch_states1, light_states1, crossing_states1 = self.wayside.update_plc_logic(
            block_occupancy[self.wayside.start_block:self.wayside.end_block],
            errors[self.wayside.start_block:self.wayside.end_block],
            maintenance[self.wayside.start_block:self.wayside.end_block]
        )
        switch_states2, light_states2, crossing_states2 = self.wayside2.update_plc_logic(
            block_occupancy[self.wayside2.start_block:self.wayside2.end_block],
            errors[self.wayside2.start_block:self.wayside2.end_block],
            maintenance[self.wayside2.start_block:self.wayside2.end_block]
        )

        # Combine states
        self.switch_state = switch_states1 + switch_states2
        self.light_state = light_states1 + light_states2
        self.crossing_state = crossing_states1 + crossing_states2

    def prev_page(self):
        self.current_page = max(self.current_page - 1, 0)
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), self.track_model.get_errors(), self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

    def next_page(self):
        self.current_page = min(self.current_page + 1, (len(self.track_model.get_block_occupancy()) // 20))
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), self.track_model.get_errors(), self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

    def update_ui_elements(self):
    # Update switch button
        self.switch_button.setText(f"Switch 1: {'On' if self.switch_state[0] else 'Off'}")
        self.switch_button.setStyleSheet(f"background-color: {'green' if self.switch_state[0] else 'red'}")

        # Update light buttons
        for i, state in enumerate(self.light_state):
            self.light_buttons[i].setText(f"Light {i+1}: {'Green' if state else 'Red'}")
            self.light_buttons[i].setStyleSheet(f"background-color: {'green' if state else 'red'}")

        # Update crossing button
        self.crossing_button.setText(f"Crossing 1: {'Closed' if self.crossing_state[0] else 'Open'}")
        self.crossing_button.setStyleSheet(f"background-color: {'red' if self.crossing_state[0] else 'green'}")
    
    def get_block_occupancy(self):
        """Returns the current block occupancy status for CTC."""
        return self.track_model.get_block_occupancy()

    def get_switch_state(self):
        """Returns the current state of all switches."""
        return self.switch_state

    def get_crossing_state(self):
        """Returns the current state of all crossings."""
        return self.crossing_state

    def get_light_state(self):
        """Returns the current state of all lights."""
        return self.light_state

    def get_errors(self):
        """Returns the current error status for all blocks for Track Model."""
        return self.track_model.get_errors()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    # Create instances of CTC and TrackModel
    ctc = CTC()
    track_model = TrackModel()

    # Create the application
    app = QApplication(sys.argv)

    # Create the TrackController UI
    controller_ui = TrackController(ctc, track_model)
    controller_ui.show()

    # Start the application loop
    sys.exit(app.exec())