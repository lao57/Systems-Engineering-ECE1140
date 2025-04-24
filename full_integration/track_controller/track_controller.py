"""
Track Controller Module

This module implements the track controller interface for managing wayside controllers,
block occupancy, switches, signals, and crossings. It communicates with CTC and Track Model systems.
"""

import sys
import importlib.util
import socket
import json
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QCheckBox, QHeaderView, QComboBox, QScrollArea, QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from track_controller.wayside import WAYSIDE


class TrackController(QMainWindow):
    """
    Main Track Controller GUI class that manages wayside controllers and their components.
    
    This class provides the interface for:
    - Managing multiple wayside controllers
    - Displaying block occupancy and authority
    - Controlling switches, signals, and crossings
    - Uploading PLC logic for wayside controllers
    - Communicating with CTC and Track Model systems
    """
    
    def __init__(self):
        """Initialize the Track Controller with default states and UI."""
        super().__init__()
        self.ctc = None
        self.track_model = None

        # Initialize global states for all track components
        self.switch_states = [False] * 150    # All switches across system
        self.light_states = [False] * 150     # All signals across system
        self.crossing_states = [False] * 150  # All crossings across system
        self.block_occupancy = [False] * 150   # Occupancy status for all blocks
        self.block_authority = [0] * 150       # Authority values for all blocks
        self.stop_states = [False] * 150       # Stop signals for CTC
        self.dont_spawn = [False] * 1          # Spawn prevention flags

        # Define wayside controllers and their component assignments
        self.wayside_controllers = {
            "wayside1": {
                "blocks": list(range(1, 29)) + list(range(146, 151)),
                "switches": [11, 27],
                "lights": [0, 149],
                "crossings": [18],
                "stop_blocks": [0, 1, 2, 148, 149],
                "dont_spawn_flag": [],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [False] * 1,
                "stop_states": [False] * 5,
                "dont_spawn": [False] * 0
            },
            "wayside2": {
                "blocks": list(range(29, 74)) + list(range(104, 146)),
                "switches": [57, 61],
                "lights": [60, 59],
                "crossings": [107],
                "stop_blocks": [58, 59, 60],
                "dont_spawn_flag": [0],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [False] * 1,
                "stop_states": [False] * 3,
                "dont_spawn": [False] * 1
            },
            "wayside3": {
                "blocks": list(range(74, 104)),
                "switches": [75, 85],
                "lights": [74, 98],
                "crossings": [],
                "stop_blocks": [73, 74, 75, 97, 98, 99],
                "dont_spawn_flag": [],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [False] * 0,
                "stop_states": [False] * 6,
                "dont_spawn": [False] * 0
            }
        }

        # UI state variables
        self.current_wayside = "wayside1"  # Default selected wayside
        self.manual_mode = False           # Manual control flag
        self.current_page = 0              # Current pagination page

        # Initialize UI components
        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 300, 600)
        self.initUI()

        self.update_ui_elements()

        # Set up periodic UI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(1000)  # Update every 1 second

    def initUI(self):
        """Initialize all UI components and layouts."""
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        # Wayside selection dropdown
        self.wayside_dropdown = QComboBox()
        self.wayside_dropdown.addItems(self.wayside_controllers.keys())
        self.wayside_dropdown.currentTextChanged.connect(self.switch_wayside)
        layout.addWidget(QLabel("Select Wayside Controller:"))
        layout.addWidget(self.wayside_dropdown)

        # PLC logic upload button
        self.upload_button = QPushButton("Upload PLC Logic")
        self.upload_button.clicked.connect(self.upload_plc_logic)
        layout.addWidget(self.upload_button)

        # Manual mode toggle
        self.manual_mode_checkbox = QCheckBox("Manual Mode")
        self.manual_mode_checkbox.stateChanged.connect(self.toggle_manual_mode)
        layout.addWidget(self.manual_mode_checkbox)

        # Block occupancy table
        self.block_table = QTableWidget(20, 2)
        self.block_table.setHorizontalHeaderLabels(["Block", "Occupancy"])
        self.block_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Block Occupancy"))
        layout.addWidget(self.block_table)

        # Pagination controls
        self.pagination_buttons = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.pagination_buttons.addWidget(self.prev_button)
        self.pagination_buttons.addWidget(self.next_button)
        layout.addLayout(self.pagination_buttons)

        # Switch control buttons
        self.switch_buttons = []
        switch_layout = QHBoxLayout()
        for i in range(3):  # Max switches across all waysides
            btn = QPushButton(f"Switch {i + 1}: {'On' if False else 'Off'}")
            btn.setStyleSheet(f"background-color: {'green' if False else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_switch_state(idx))
            self.switch_buttons.append(btn)
            switch_layout.addWidget(btn)
        layout.addLayout(switch_layout)

        # Signal light control buttons
        self.light_buttons = []
        light_layout = QHBoxLayout()
        for i in range(6):  # Max lights across all waysides
            btn = QPushButton(f"Light {i + 1}: {'Green' if False else 'Red'}")
            btn.setStyleSheet(f"background-color: {'green' if False else 'red'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_light_state(idx))
            self.light_buttons.append(btn)
            light_layout.addWidget(btn)
        layout.addLayout(light_layout)

        # Crossing control buttons
        self.crossing_buttons = []
        crossing_layout = QHBoxLayout()
        for i in range(3):  # Max crossings across all waysides
            btn = QPushButton(f"Crossing {i + 1}: {'Closed' if False else 'Open'}")
            btn.setStyleSheet(f"background-color: {'red' if False else 'green'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_crossing_state(idx))
            self.crossing_buttons.append(btn)
            crossing_layout.addWidget(btn)
        layout.addLayout(crossing_layout)

        # Stop signal control buttons
        self.stop_buttons = []
        stop_layout = QHBoxLayout()
        for i in range(6):
            btn = QPushButton(f"Stop {i + 1}: {'stop' if False else 'allow'}")
            btn.setStyleSheet(f"background-color: {'red' if False else 'green'}")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_stop_state(idx))
            self.stop_buttons.append(btn)
            stop_layout.addWidget(btn)
        layout.addLayout(stop_layout)

        # Block authority table
        self.authority_table = QTableWidget(20, 2)
        self.authority_table.setHorizontalHeaderLabels(["Block", "Authority"])
        self.authority_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Block Authority"))
        layout.addWidget(self.authority_table)

        centralWidget.setLayout(layout)

    def upload_plc_logic(self):
        """
        Open file dialog to upload and load PLC logic for the current wayside.
        
        The uploaded Python file should contain a function called 'update_wayside'
        that implements the control logic for the wayside.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload PLC Logic", "", "Python Files (*.py)")
        if not file_path:
            return

        try:
            # Extract wayside name from filename (e.g., "wayside1_logic.py")
            file_name = file_path.split("/")[-1]
            wayside_name = file_name.split("_")[0]

            # Skip upload for wayside2 (handled by Raspberry Pi)
            if wayside_name == "wayside2":
                print("PLC logic upload for wayside2 is disabled.")
                return

            # Dynamically load the PLC module
            spec = importlib.util.spec_from_file_location(wayside_name + "_logic", file_path)
            plc_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plc_module)

            # Update the logic function if wayside exists
            if wayside_name in self.wayside_controllers:
                self.wayside_controllers[wayside_name]["logic_function"] = plc_module.update_wayside
                print(f"PLC logic updated for {wayside_name}")
            else:
                print(f"No wayside controller found for {wayside_name}")
        except Exception as e:
            print(f"Failed to load PLC logic: {e}")

    def switch_wayside(self, wayside_name):
        """
        Switch the active wayside controller being displayed.
        
        Args:
            wayside_name: Name of the wayside to switch to (e.g., "wayside1")
        """
        self.current_wayside = wayside_name
        self.current_page = 0

        # Disable upload for wayside2 (handled externally)
        self.upload_button.setEnabled(wayside_name != "wayside2")

        # Update UI with new wayside data
        self.update_block_table(self.track_model.occupancy_status, self.ctc.get_maintenance_status(), 0)
        self.update_authority_table(0)
        self.update_ui_elements()

    def toggle_manual_mode(self):
        """Toggle manual control mode for the current wayside."""
        self.manual_mode = self.manual_mode_checkbox.isChecked()
        self.update_ui_elements()

    def toggle_switch_state(self, idx):
        """Toggle the state of a switch in manual mode."""
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["switch_states"]):
                wayside["switch_states"][idx] = not wayside["switch_states"][idx]
                self.update_ui_elements()

    def toggle_light_state(self, idx):
        """Toggle the state of a signal light in manual mode."""
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["light_states"]):
                wayside["light_states"][idx] = not wayside["light_states"][idx]
                self.update_ui_elements()

    def toggle_crossing_state(self, idx):
        """Toggle the state of a crossing gate in manual mode."""
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["crossing_states"]):
                wayside["crossing_states"][idx] = not wayside["crossing_states"][idx]
                self.update_ui_elements()

    def toggle_stop_state(self, idx):
        """Toggle the state of a stop signal in manual mode."""
        if self.manual_mode:
            wayside = self.wayside_controllers[self.current_wayside]
            if idx < len(wayside["stop_states"]):
                wayside["stop_states"][idx] = not wayside["stop_states"][idx]
                self.update_ui_elements()

    def update(self):
        """
        Periodic update method called by timer.
        
        Fetches latest data from CTC and Track Model, updates wayside controllers,
        and refreshes the UI.
        """
        # Get latest system states
        self.maintenance = self.ctc.maintenance
        self.block_authorities = self.ctc.block_occupancy
        self.block_occupancy = self.track_model.occupancy_status

        # Combine occupancy and maintenance states
        self.block_occupancy = [self.block_occupancy[i] or self.maintenance[i] 
                               for i in range(len(self.block_occupancy))]

        # Update UI tables
        self.update_block_table(self.block_occupancy, self.maintenance, self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

        # Check if any blocks are occupied in current wayside
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]
        any_occupied = any(self.block_occupancy[block - 1] for block in wayside_blocks)

        # Disable manual mode if blocks are occupied
        if any_occupied:
            self.manual_mode = False
            self.manual_mode_checkbox.setChecked(False)
            self.manual_mode_checkbox.setEnabled(False)
        else:
            self.manual_mode_checkbox.setEnabled(True)

        # Update wayside controllers if not in manual mode
        if not self.manual_mode:
            self.update_wayside_controllers(self.block_occupancy, self.maintenance, self.block_authorities)

        self.update_ui_elements()

    def update_block_table(self, block_occupancy, maintenance, start_block=0):
        """
        Update the block occupancy table with current data.
        
        Args:
            block_occupancy: List of occupancy states for all blocks
            maintenance: List of maintenance states for all blocks
            start_block: Starting block index for pagination
        """
        self.block_table.setRowCount(20)
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]

        for i in range(20):
            block_num = start_block + i
            if block_num < len(wayside_blocks):
                block_id = wayside_blocks[block_num]
                
                # Block number cell
                block_item = QTableWidgetItem(f"{block_id}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 0, block_item)

                # Occupancy status cell
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
                # Clear empty rows
                self.block_table.setItem(i, 0, QTableWidgetItem(""))
                self.block_table.setItem(i, 1, QTableWidgetItem(""))

    def update_authority_table(self, start_block=0):
        """
        Update the block authority table with current data.
        
        Args:
            start_block: Starting block index for pagination
        """
        self.authority_table.setRowCount(20)
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]

        for i in range(20):
            block_num = start_block + i
            if block_num < len(wayside_blocks):
                block_id = wayside_blocks[block_num]

                # Block number cell
                block_item = QTableWidgetItem(f"{block_id}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 0, block_item)

                # Authority value cell (converted to meters)
                authority_int = 3.28 * self.get_block_authority(block_id)
                rounded_value = round(authority_int)
                authority_item = QTableWidgetItem(str(rounded_value))
                authority_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 1, authority_item)
            else:
                # Clear empty rows
                self.authority_table.setItem(i, 0, QTableWidgetItem(""))
                self.authority_table.setItem(i, 1, QTableWidgetItem(""))

    def update_wayside_controllers(self, block_occupancy, maintenance, block_authorities):
        """
        Update all wayside controllers with current system state.
        
        Args:
            block_occupancy: List of block occupancy states
            maintenance: List of maintenance states
            block_authorities: List of block authority values
        """
        if self.manual_mode:
            return

        for wayside_name, config in self.wayside_controllers.items():
            # Skip wayside2 which is handled by external system
            if wayside_name == "wayside2":
                # Update global states from external config
                for i, switch_index in enumerate(config["switches"]):
                    self.switch_states[switch_index] = config["switch_states"][i]
                for i, light_index in enumerate(config["lights"]):
                    self.light_states[light_index] = config["light_states"][i]
                for i, crossing_index in enumerate(config["crossings"]):
                    if i < len(config["crossing_states"]):
                        self.crossing_states[crossing_index] = config["crossing_states"][i]
                continue

            # Skip if no PLC logic loaded
            if config["logic_function"] is None:
                continue

            # Prepare wayside-specific data
            wayside_blocks = config["blocks"]
            wayside_block_occupancy = [block_occupancy[block - 1] for block in wayside_blocks]
            wayside_maintenance = [maintenance[block - 1] for block in wayside_blocks]
            wayside_block_authorities = [block_authorities[block - 1] for block in wayside_blocks]

            # Create wayside controller instance
            wayside = WAYSIDE(
                switches=config["switches"],
                lights=config["lights"],
                crossings=config["crossings"],
                stop_blocks=config["stop_blocks"],
                dont_spawn_flag=config["dont_spawn_flag"],
                logic_function=config["logic_function"],
                prev_switch_states=config["switch_states"],
                block_authorities=wayside_block_authorities
            )

            # Execute PLC logic
            switch_states, light_states, crossing_states, stop_states, dont_spawn = wayside.update_wayside(
                wayside_block_occupancy,
                wayside_maintenance
            )

            # Update wayside configuration
            config.update({
                "switch_states": switch_states,
                "light_states": light_states,
                "crossing_states": crossing_states,
                "stop_states": stop_states,
                "dont_spawn": dont_spawn
            })

            # Update global states
            for i, switch_index in enumerate(config["switches"]):
                self.switch_states[switch_index] = switch_states[i]

            for i, light_index in enumerate(config["lights"]):
                self.light_states[light_index] = light_states[i]

            for i, crossing_index in enumerate(config["crossings"]):
                self.crossing_states[crossing_index] = crossing_states[i]

            for i, stop_index in enumerate(config["stop_blocks"]):
                self.stop_states[stop_index] = stop_states[i]
            
            for i, dont_spawn_index in enumerate(config["dont_spawn_flag"]):
                self.dont_spawn[dont_spawn_index] = dont_spawn[i]

    def prev_page(self):
        """Navigate to the previous page of blocks."""
        self.current_page = max(self.current_page - 1, 0)
        self.update_block_table(
            self.track_model.occupancy_status,
            self.ctc.get_maintenance_status(),
            self.current_page * 20
        )
        self.update_authority_table(self.current_page * 20)

    def next_page(self):
        """Navigate to the next page of blocks."""
        total_blocks = len(self.wayside_controllers[self.current_wayside]["blocks"])
        max_page = (total_blocks + 19) // 20 - 1
        self.current_page = min(self.current_page + 1, max_page)
        self.update_block_table(
            self.track_model.occupancy_status,
            self.ctc.get_maintenance_status(),
            self.current_page * 20
        )
        self.update_authority_table(self.current_page * 20)

    def update_ui_elements(self):
        """Update all UI elements to reflect current system state."""
        wayside = self.wayside_controllers[self.current_wayside]

        # Update switch buttons
        for i, btn in enumerate(self.switch_buttons):
            if i < len(wayside["switches"]):
                state = wayside["switch_states"][i]
                btn.setText(f"Switch {i + 1}: {'On' if state else 'Off'}")
                btn.setStyleSheet(f"background-color: {'green' if state else 'red'}")
                btn.show()
            else:
                btn.hide()

        # Update light buttons
        for i, btn in enumerate(self.light_buttons):
            if i < len(wayside["lights"]):
                state = wayside["light_states"][i]
                btn.setText(f"Light {i + 1}: {'Green' if state else 'Red'}")
                btn.setStyleSheet(f"background-color: {'green' if state else 'red'}")
                btn.show()
            else:
                btn.hide()

        # Update crossing buttons
        for i, btn in enumerate(self.crossing_buttons):
            if i < len(wayside["crossings"]):
                state = wayside["crossing_states"][i]
                btn.setText(f"Crossing {i + 1}: {'Closed' if state else 'Open'}")
                btn.setStyleSheet(f"background-color: {'red' if state else 'green'}")
                btn.show()
            else:
                btn.hide()

        # Update stop buttons
        for i, btn in enumerate(self.stop_buttons):
            if i < len(wayside["stop_blocks"]):
                state = wayside["stop_states"][i]
                btn.setText(f"Stop {i + 1}: {'stop' if state else 'allow'}")
                btn.setStyleSheet(f"background-color: {'red' if state else 'green'}")
                btn.show()
            else:
                btn.hide()

    # System state access methods
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
        return self.block_occupancy

    def get_block_authority(self, block_id):
        """
        Get authority value for a specific block.
        
        Args:
            block_id: Block number (1-based index)
            
        Returns:
            Authority value as integer
        """
        authority_bits = self.block_authority[block_id - 1]
        if isinstance(authority_bits, int):
            return authority_bits
        binary_str = ''.join(['1' if bit else '0' for bit in authority_bits])
        return int(binary_str, 2)
    
    def get_stop_signals(self):
        """Return the combined stop signals for all blocks."""
        return self.stop_states

    # External system communication methods
    def receive_authority(self, authority):
        """Receive authority data from CTC system."""
        self.block_authority = [bit.copy() if isinstance(bit, list) else bit for bit in authority]

    def receive_maintenance(self, maintenance):
        """Receive maintenance data from CTC system."""
        self.maintenance = maintenance.copy()

    def set_ctc(self, ctc):
        """Set reference to CTC system."""
        self.ctc = ctc

    def set_track_model(self, track_model):
        """Set reference to Track Model system."""
        self.track_model = track_model


def socket_client_thread(ctc, track_controller, track_model):
    """
    Socket client thread for communicating with Raspberry Pi (wayside2 controller).
    
    This thread:
    - Maintains connection to Raspberry Pi
    - Sends current system state
    - Receives and applies wayside2 controller updates
    
    Args:
        ctc: Reference to CTC system
        track_controller: Reference to track controller
        track_model: Reference to track model
    """
    target_ip = "192.168.137.175"  # Raspberry Pi IP
    port = 12345
    
    # Establish socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((target_ip, port))
        print("Connected to Raspberry Pi server:", target_ip)
    except Exception as e:
        print("Failed to connect to Raspberry Pi server:", e)
        return

    while True:
        try:
            # Prepare data payload
            data = {
                "block_occupancy": track_model.occupancy_status,
                "block_authority": ctc.get_block_authority(),
                "maintenance": ctc.get_maintenance_status(),
                "prev_switch_states": track_controller.wayside_controllers["wayside2"]["switch_states"]
            }
            
            # Send data to Raspberry Pi
            s.sendall((json.dumps(data) + "\n").encode())

            # Receive response
            response = ""
            while "\n" not in response:
                chunk = s.recv(1024).decode()
                if not chunk:
                    break
                response += chunk

            if response:
                try:
                    resp_data = json.loads(response.strip())
                    # Update wayside2's state based on data from Raspberry Pi
                    track_controller.wayside_controllers["wayside2"]["switch_states"] = resp_data.get(
                        "switch_states", track_controller.wayside_controllers["wayside2"]["switch_states"])
                    track_controller.wayside_controllers["wayside2"]["light_states"] = resp_data.get(
                        "light_states", track_controller.wayside_controllers["wayside2"]["light_states"])
                    track_controller.wayside_controllers["wayside2"]["crossing_states"] = resp_data.get(
                        "crossing_states", track_controller.wayside_controllers["wayside2"]["crossing_states"])
                    track_controller.wayside_controllers["wayside2"]["dont_spawn"] = resp_data.get(
                        "dont_spawn", track_controller.wayside_controllers["wayside2"]["dont_spawn"])

                except Exception as e:
                    print("Error parsing returned data:", e)

            time.sleep(0.05)  # Small delay to prevent flooding
        except Exception as e:
            print("Socket client error:", e)
            time.sleep(1)