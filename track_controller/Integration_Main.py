import sys
import pandas as pd
import importlib.util
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QCheckBox, QHeaderView, QComboBox, QScrollArea, QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from wayside import WAYSIDE

class CTC:
    def __init__(self):
        self.maintenance = [False] * 150  # Maintenance status for all blocks
        self.block_authority = [0b0000001010] * 150  # Example: block authority values
        self.track_controller = None  # Will be set later

    def set_track_controller(self, track_controller):
        self.track_controller = track_controller

    def get_maintenance_status(self):
        return self.maintenance

    def get_block_authority(self):
        return self.block_authority

class TrackController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ctc = None
        self.track_model = None

        # Initialize global states
        self.switch_states = [False] * 6  # Total switches across all waysides
        self.light_states = [False] * 6  # Total lights across all waysides
        self.crossing_states = [False] * 2  # Total crossings across all waysides
        self.block_occupancy = [False] * 150  # Block occupancy for all blocks
        self.block_authority = [0] * 150  # Block authority for all blocks

        self.count = 0  # get rid of later

        # Define wayside controllers and their block assignments
        self.wayside_controllers = {
            "wayside1": {
                "blocks": list(range(1, 29)) + list(range(146, 151)),  # Blocks 1-28 and 146-150
                "switches": [0, 1],  # Switches controlled by Wayside 1 (indices 0 and 1)
                "lights": [0, 1],  # Lights controlled by Wayside 1
                "crossings": [0],  # Crossings controlled by Wayside 1
                "logic_function": None,  # Will be set dynamically
                "switch_states": [False] * 2,  # Initial switch states for Wayside 1
                "light_states": [False] * 2,  # Initial light states for Wayside 1
                "crossing_states": [False] * 1,  # Initial crossing states for Wayside 1
            },
            "wayside2": {
                "blocks": list(range(29, 74)) + list(range(104, 146)),  # Blocks 29-73 and 104-146
                "switches": [2, 3],  # Switches controlled by Wayside 2 (indices 2, 3, and 4)
                "lights": [2, 3],  # Lights controlled by Wayside 2
                "crossings": [1],  # Crossings controlled by Wayside 2
                "logic_function": None,  # Will be set dynamically
                "switch_states": [False] * 2,  # Initial switch states for Wayside 2
                "light_states": [False] * 2,  # Initial light states for Wayside 2
                "crossing_states": [False] * 1,  # Initial crossing states for Wayside 2
            },
            "wayside3": {
                "blocks": list(range(74, 104)),  # Blocks 74-103
                "switches": [4, 5],
                "lights": [4, 5],
                "crossings": [],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [False] * 0,
            }
        }

        # Initialize internal states
        self.current_wayside = "wayside1"  # Default wayside controller
        self.manual_mode = False
        self.current_page = 0  # Track the current page

        # Initialize UI
        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 300, 600)
        self.initUI()

        self.update_ui_elements()

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        # Wayside Controller Dropdown
        self.wayside_dropdown = QComboBox()
        self.wayside_dropdown.addItems(self.wayside_controllers.keys())
        self.wayside_dropdown.currentTextChanged.connect(self.switch_wayside)
        layout.addWidget(QLabel("Select Wayside Controller:"))
        layout.addWidget(self.wayside_dropdown)

        # Upload PLC Logic Button
        self.upload_button = QPushButton("Upload PLC Logic")
        self.upload_button.clicked.connect(self.upload_plc_logic)
        layout.addWidget(self.upload_button)

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

        # Switch Buttons
        self.switch_buttons = []
        switch_layout = QHBoxLayout()
        for i in range(3):  # Max switches across all waysides
            btn = QPushButton(f"Switch {i+1}: {'On' if False else 'Off'}")
            btn.setStyleSheet(f"background-color: {'green' if False else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_switch_state(idx))
            self.switch_buttons.append(btn)
            switch_layout.addWidget(btn)
        layout.addLayout(switch_layout)

        # Light Buttons
        self.light_buttons = []
        light_layout = QHBoxLayout()
        for i in range(6):  # Max lights across all waysides
            btn = QPushButton(f"Light {i+1}: {'Green' if False else 'Red'}")
            btn.setStyleSheet(f"background-color: {'green' if False else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_light_state(idx))
            self.light_buttons.append(btn)
            light_layout.addWidget(btn)
        layout.addLayout(light_layout)

        # Crossing Buttons
        self.crossing_buttons = []
        crossing_layout = QHBoxLayout()
        for i in range(3):  # Max crossings across all waysides
            btn = QPushButton(f"Crossing {i+1}: {'Closed' if False else 'Open'}")
            btn.setStyleSheet(f"background-color: {'red' if False else 'green'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_crossing_state(idx))
            self.crossing_buttons.append(btn)
            crossing_layout.addWidget(btn)
        layout.addLayout(crossing_layout)

        # Block Authority Table
        self.authority_table = QTableWidget(20, 2)  # Display 20 blocks at a time
        self.authority_table.setHorizontalHeaderLabels(["Block", "Authority"])
        self.authority_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Block Authority"))
        layout.addWidget(self.authority_table)

        centralWidget.setLayout(layout)

    def upload_plc_logic(self):
        """Open a file dialog to upload a Python file containing the PLC logic."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload PLC Logic", "", "Python Files (*.py)")
        if file_path:
            try:
                # Extract the wayside name from the file name (e.g., "wayside1_logic.py" -> "wayside1")
                file_name = file_path.split("/")[-1]  # Get the file name from the path
                wayside_name = file_name.split("_")[0]  # Extract the wayside name (e.g., "wayside1")
                print(wayside_name)

                # Dynamically load the uploaded Python file
                spec = importlib.util.spec_from_file_location(wayside_name + "_logic", file_path)
                plc_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plc_module)

                # Update the logic function for the corresponding wayside controller
                if wayside_name in self.wayside_controllers:
                    self.wayside_controllers[wayside_name]["logic_function"] = plc_module.update_wayside
                    print(f"PLC logic updated for {wayside_name}")
                else:
                    print(f"No wayside controller found for {wayside_name}")
            except Exception as e:
                print(f"Failed to load PLC logic: {e}")

    def switch_wayside(self, wayside_name):
        """Switch the displayed wayside controller."""
        self.current_wayside = wayside_name
        self.current_page = 0
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), 0)
        self.update_authority_table(0)
        self.update_ui_elements()  # Refresh UI to show correct switches and lights

    def toggle_manual_mode(self):
        self.manual_mode = self.manual_mode_checkbox.isChecked()

    def toggle_switch_state(self, idx):
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["switch_states"]):
                wayside["switch_states"][idx] = not wayside["switch_states"][idx]
                self.update_ui_elements()

    def toggle_light_state(self, idx):
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["light_states"]):
                wayside["light_states"][idx] = not wayside["light_states"][idx]
                self.update_ui_elements()

    def toggle_crossing_state(self, idx):
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["crossing_states"]):
                wayside["crossing_states"][idx] = not wayside["crossing_states"][idx]
                self.update_ui_elements()

    def update(self):
        # Fetch data from CTC and Track Model
        self.maintenance = self.ctc.get_maintenance_status()
        self.block_authorities = self.ctc.get_block_authority()
        self.block_occupancy = self.track_model.get_block_occupancy()

        self.block_occupancy = [self.block_occupancy[i] or self.maintenance[i] for i in range(len(self.block_occupancy))]

        # Update the UI
        self.update_block_table(self.block_occupancy, self.maintenance, self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

        # Skip wayside logic update if in manual mode
        if not self.manual_mode:
            self.update_wayside_controllers(self.block_occupancy, self.maintenance, self.block_authorities)

        # Update UI elements (buttons) based on wayside logic
        self.update_ui_elements()
        
        if self.count >= 5:
            #print(self.switch_states)
            self.count = 0

        self.count = self.count+1

    def update_block_table(self, block_occupancy, maintenance, start_block=0):
        self.block_table.setRowCount(20)  # Display 20 blocks at a time
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]
        for i in range(20):
            block_num = start_block + i
            if block_num < len(wayside_blocks):
                block_id = wayside_blocks[block_num]
                # Block number
                block_item = QTableWidgetItem(f"{block_id}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 0, block_item)

                # Occupancy status
                if block_occupancy[block_id - 1]:
                    status = "Occupied"
                    background_color = Qt.GlobalColor.lightGray
                elif maintenance[block_id - 1]:
                    status = "Maintenance"
                    background_color = Qt.GlobalColor.darkRed
                else:
                    status = "Unoccupied"
                    background_color = Qt.GlobalColor.transparent

                occupancy_item = QTableWidgetItem(status)
                occupancy_item.setBackground(background_color)
                occupancy_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 1, occupancy_item)
            else:
                # Clear the row if there are no more blocks to display
                self.block_table.setItem(i, 0, QTableWidgetItem(""))
                self.block_table.setItem(i, 1, QTableWidgetItem(""))

    def update_authority_table(self, start_block=0):
        self.authority_table.setRowCount(20)  # Display 20 blocks at a time
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]
        block_authority = self.ctc.get_block_authority()
        for i in range(20):
            block_num = start_block + i
            if block_num < len(wayside_blocks):
                block_id = wayside_blocks[block_num]
                # Block number
                block_item = QTableWidgetItem(f"{block_id}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 0, block_item)

                # Authority value
                authority_item = QTableWidgetItem(str(block_authority[block_id - 1]))
                authority_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 1, authority_item)
            else:
                # Clear the row if there are no more blocks to display
                self.authority_table.setItem(i, 0, QTableWidgetItem(""))
                self.authority_table.setItem(i, 1, QTableWidgetItem(""))

    def update_wayside_controllers(self, block_occupancy, maintenance, block_authorities):
            if not self.manual_mode:
                for wayside_name, config in self.wayside_controllers.items():
                    # Get the blocks assigned to this wayside
                    wayside_blocks = config["blocks"]

                    # Filter block data for this wayside
                    wayside_block_occupancy = [block_occupancy[block - 1] for block in wayside_blocks]
                    wayside_maintenance = [maintenance[block - 1] for block in wayside_blocks]
                    wayside_block_authorities = [block_authorities[block - 1] for block in wayside_blocks]

                    #print(f"Prev switch states for {wayside_name}: {config['switch_states']}")

                    if config["logic_function"] is not None:
                        wayside = WAYSIDE(
                            switches=config["switches"],
                            lights=config["lights"],
                            crossings=config["crossings"],
                            logic_function=config["logic_function"],
                            prev_switch_states=config["switch_states"],
                            block_authorities=wayside_block_authorities
                        )
                        #print(wayside.prev_switch_states) #works here
                       
                        # Execute the PLC logic
                        switch_states, light_states, crossing_states = wayside.update_wayside(
                            wayside_block_occupancy,
                            wayside_maintenance
                        )

                        # Update the wayside's internal states
                        config["switch_states"] = switch_states
                        config["light_states"] = light_states
                        config["crossing_states"] = crossing_states

                        # Update global states
                        for i, switch_index in enumerate(config["switches"]):
                            self.switch_states[switch_index] = switch_states[i]

                        for i, light_index in enumerate(config["lights"]):
                            self.light_states[light_index] = light_states[i]

                        for i, crossing_index in enumerate(config["crossings"]):
                            self.crossing_states[crossing_index] = crossing_states[i]
    
    def prev_page(self):
        """Move to the previous page of blocks."""
        self.current_page = max(self.current_page - 1, 0)
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

    def next_page(self):
        """Move to the next page of blocks."""
        total_blocks = len(self.wayside_controllers[self.current_wayside]["blocks"])
        max_page = (total_blocks + 19) // 20 - 1
        self.current_page = min(self.current_page + 1, max_page)
        self.update_block_table(
            self.track_model.get_block_occupancy(),
            self.ctc.get_maintenance_status(),  # Pass maintenance status from CTC
            self.current_page * 20
        )
        self.update_authority_table(self.current_page * 20)
                                
    def update_ui_elements(self):
            wayside = self.wayside_controllers[self.current_wayside]
            num_switches = len(wayside["switches"])
            num_lights = len(wayside["lights"])
            num_crossings = len(wayside["crossings"])

            # Update switch buttons
            for i, btn in enumerate(self.switch_buttons):
                if i < num_switches:
                    btn.setText(f"Switch {i+1}: {'On' if wayside['switch_states'][i] else 'Off'}")
                    btn.setStyleSheet(f"background-color: {'green' if wayside['switch_states'][i] else 'red'}")
                    btn.show()
                else:
                    btn.hide()

            # Update light buttons
            for i, btn in enumerate(self.light_buttons):
                if i < num_lights:
                    btn.setText(f"Light {i+1}: {'Green' if wayside['light_states'][i] else 'Red'}")
                    btn.setStyleSheet(f"background-color: {'green' if wayside['light_states'][i] else 'red'}")
                    btn.show()
                else:
                    btn.hide()

            # Update crossing buttons
            for i, btn in enumerate(self.crossing_buttons):
                if i < num_crossings:
                    btn.setText(f"Crossing {i+1}: {'Closed' if wayside['crossing_states'][i] else 'Open'}")
                    btn.setStyleSheet(f"background-color: {'red' if wayside['crossing_states'][i] else 'green'}")
                    btn.show()
                else:
                    btn.hide()
    
    def get_switch_state(self):
        """Return the combined switch states for all waysides."""
        return self.switch_states

    def get_light_state(self):
        """Return the combined light states for all waysides."""
        return self.light_states

    def get_crossing_state(self):
        """Return the combined crossing states for all waysides."""
        return self.crossing_states

    def get_block_occupancy(self):
        """Return the combined block occupancy for all blocks."""
        return self.block_occupancy #self.track_model.get_block_occupancy() if I decide to do that

    def get_block_authority(self):
        """Return the combined block authority for all blocks."""
        return self.block_authority

    def set_ctc(self, ctc):
        self.ctc = ctc
    
    def set_track_model(self, track_model):
        self.track_model = track_model

class TrainModel:
    def __init__(self):
        """Initialize the Train Model with default values."""
        self.block_authority = {}  # Stores authority for each block
        self.passenger_data = {}  # Stores passenger count per station
        self.current_block = 1  # Current block the train is on
        self.speed = 0  # Current speed of the train
        self.direction = 1  # 1 for forward, -1 for backward

    def receive_block_authority(self, block_authority):
        """Receive block authority data from Track Model."""
        self.block_authority = block_authority
        print(f"Train Model: Received block authority data - {block_authority}")

    def receive_passenger_data(self, passenger_data):
        """Receive passenger count data from Track Model."""
        self.passenger_data = passenger_data
        print(f"Train Model: Received passenger data - {passenger_data}")

    def update_position(self):
        """Update the train's position based on block authority."""
        if self.current_block in self.block_authority:
            # Simulate moving to the next block if authority allows
            next_block = self.current_block + self.direction
            if next_block in self.block_authority and self.block_authority[next_block] == 1:
                self.current_block = next_block
                print(f"Train Model: Moved to block {self.current_block}")
            else:
                print(f"Train Model: Cannot move to block {next_block} - no authority")
        else:
            print(f"Train Model: Current block {self.current_block} has no authority")

    def get_current_block(self):
        """Return the current block the train is on."""
        return self.current_block

    def set_direction(self, direction):
        """Set the direction of the train (1 for forward, -1 for backward)."""
        self.direction = direction
        print(f"Train Model: Direction set to {'forward' if direction == 1 else 'backward'}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create instances of CTC, TrackModelBackend, and TrackController
    ctc = CTC()
    track_controller = TrackController()
    train_model = TrainModel()  # Assuming this is already defined
    track_model = TrackModelBackend(track_controller, train_model)

    # Wire the dependencies together
    ctc.set_track_controller(track_controller)
    track_controller.set_track_model(track_model)
    track_controller.set_ctc(ctc)

    # Show the TrackController UI
    track_controller.show()

    # Create a QTimer to call update every second
    timer = QTimer()
    timer.timeout.connect(track_controller.update)  # Connect the timer to the update function
    timer.start(1000)  # Set the interval to 1000 milliseconds (1 second)

    # Start the application loop
    sys.exit(app.exec())

    