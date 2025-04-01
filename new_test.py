import sys
import importlib.util
import socket        # [Optional] Ensure socket is imported for client thread
import json          # [Optional] Ensure json is imported for client thread
import threading     # [Optional] Ensure threading is imported for client thread
import time          # [Optional] Ensure time is imported for client thread
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QCheckBox, QHeaderView, QComboBox, QScrollArea, QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from wayside import WAYSIDE

# ---------------------------
# Existing CTC, TrackModel, TestBench, TrackController definitions
# ---------------------------

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

class TrackModel:
    def __init__(self):
        self.block_occupancy = [False] * 150  # Occupancy status for all blocks
        self.track_controller = None  # Will be set later

    def set_track_controller(self, track_controller):
        self.track_controller = track_controller

    def get_block_occupancy(self):
        return self.block_occupancy

class TestBench(QMainWindow):
    def __init__(self, ctc, track_model):
        super().__init__()
        self.ctc = ctc
        self.track_model = track_model
        self.setWindowTitle("Test Bench")
        self.setGeometry(200, 200, 800, 600)
        self.initUI()

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        # Scroll Area for the grid of buttons
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)

        # Create 150 buttons in a grid for blocks 1-150
        self.block_buttons = []
        for block_num in range(1, 151):
            btn = QPushButton(f"Block {block_num}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, block=block_num - 1: self.toggle_block(block))
            self.block_buttons.append(btn)
            self.grid_layout.addWidget(btn, (block_num - 1) // 10, (block_num - 1) % 10)

        scroll_widget.setLayout(self.grid_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        centralWidget.setLayout(layout)

    def toggle_block(self, block_num):
        """Toggle occupancy and maintenance status for the selected block."""
        self.track_model.block_occupancy[block_num] = not self.track_model.block_occupancy[block_num]
        self.ctc.maintenance[block_num] = 0

        # Update button color to reflect occupancy status
        btn = self.block_buttons[block_num]
        if self.track_model.block_occupancy[block_num]:
            btn.setStyleSheet("background-color: lightGray")
        else:
            btn.setStyleSheet("")

class TrackController(QMainWindow):
    def __init__(self, ctc, track_model):
        super().__init__()
        self.ctc = ctc
        self.track_model = track_model

        # Initialize global state arrays
        self.switch_states = [False] * 6    # Total switches across all waysides
        self.light_states = [False] * 6     # Total lights across all waysides
        self.crossing_states = [False] * 2  # Total crossings across all waysides
        self.block_occupancy = [False] * 150  # Block occupancy for all blocks
        self.block_authority = [0] * 150      # Block authority for all blocks

        self.count = 0  # Temporary counter (if needed for testing)

        # Define wayside controllers and their block assignments
        self.wayside_controllers = {
            "wayside1": {
                "blocks": list(range(1, 29)) + list(range(146, 151)),  # Blocks 1-28 and 146-150
                "switches": [0, 1],
                "lights": [0, 1],
                "crossings": [0],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [False] * 1,
            },
            "wayside2": {
                "blocks": list(range(29, 74)) + list(range(104, 146)),  # Blocks 29-73 and 104-145
                "switches": [2, 3],
                "lights": [2, 3],
                "crossings": [1],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [False] * 1,
            },
            "wayside3": {
                "blocks": list(range(74, 104)),  # Blocks 74-103
                "switches": [4, 5],
                "lights": [4, 5],
                "crossings": [],
                "logic_function": None,
                "switch_states": [False] * 2,
                "light_states": [False] * 2,
                "crossing_states": [],
            }
        }

        self.current_wayside = "wayside1"  # Default to display wayside1 initially
        self.manual_mode = False
        self.current_page = 0  # Current page index for block tables (pagination)

        self.setWindowTitle("Track Controller")
        self.setGeometry(100, 100, 300, 600)
        self.initUI()
        self.update_ui_elements()

        # Timer to update UI periodically
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(1000)  # Update every second

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()

        # Wayside Controller selection dropdown
        self.wayside_dropdown = QComboBox()
        self.wayside_dropdown.addItems(self.wayside_controllers.keys())
        self.wayside_dropdown.currentTextChanged.connect(self.switch_wayside)
        layout.addWidget(QLabel("Select Wayside Controller:"))
        layout.addWidget(self.wayside_dropdown)

        # Upload PLC Logic button
        self.upload_button = QPushButton("Upload PLC Logic")
        self.upload_button.clicked.connect(self.upload_plc_logic)
        layout.addWidget(self.upload_button)

        # Manual Mode checkbox
        self.manual_mode_checkbox = QCheckBox("Manual Mode")
        self.manual_mode_checkbox.stateChanged.connect(self.toggle_manual_mode)
        layout.addWidget(self.manual_mode_checkbox)

        # Block Occupancy table
        self.block_table = QTableWidget(20, 2)
        self.block_table.setHorizontalHeaderLabels(["Block", "Occupancy"])
        self.block_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Block Occupancy"))
        layout.addWidget(self.block_table)

        # Pagination buttons for block lists
        self.pagination_buttons = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.pagination_buttons.addWidget(self.prev_button)
        self.pagination_buttons.addWidget(self.next_button)
        layout.addLayout(self.pagination_buttons)

        # Block Authority table
        self.authority_table = QTableWidget(20, 2)
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
                file_name = file_path.split("/")[-1]   # Get the file name from the path
                wayside_name = file_name.split("_")[0]  # Extract the wayside name (e.g., "wayside1")
                print(wayside_name)
                # --- Modification: Prevent uploading logic for wayside2 ---
                if wayside_name == "wayside2":
                    print("PLC logic upload for wayside2 is disabled.")
                    return
                # Dynamically load the uploaded Python file for logic
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
        """Switch the displayed wayside controller and update UI accordingly."""
        self.current_wayside = wayside_name
        self.current_page = 0
        # Update tables for the newly selected wayside
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), 0)
        self.update_authority_table(0)
        self.update_ui_elements()  # Refresh UI elements (if any) for the new wayside
        # --- Modification: Disable upload button for wayside2 on PC ---
        if wayside_name == "wayside2":
            self.upload_button.setEnabled(False)  # Disable upload for wayside2
        else:
            self.upload_button.setEnabled(True)   # Enable upload for other waysides

    def toggle_manual_mode(self):
        self.manual_mode = self.manual_mode_checkbox.isChecked()

    # (Optional) Functions to manually toggle switch/light/crossing states if needed
    def toggle_switch_state(self, idx):
        wayside = self.wayside_controllers[self.current_wayside]
        if idx < len(wayside["switch_states"]):
            wayside["switch_states"][idx] = not wayside["switch_states"][idx]
            # If needed, update global state or send to server in manual mode
            self.update_ui_elements()

    def toggle_light_state(self, idx):
        wayside = self.wayside_controllers[self.current_wayside]
        if idx < len(wayside["light_states"]):
            wayside["light_states"][idx] = not wayside["light_states"][idx]
            self.update_ui_elements()

    def toggle_crossing_state(self, idx):
        wayside = self.wayside_controllers[self.current_wayside]
        if idx < len(wayside["crossing_states"]):
            wayside["crossing_states"][idx] = not wayside["crossing_states"][idx]
            self.update_ui_elements()

    def update(self):
        # Gather latest data from CTC and TrackModel
        self.maintenance = self.ctc.get_maintenance_status()
        self.block_authorities = self.ctc.get_block_authority()
        self.block_occupancy = self.track_model.get_block_occupancy()
        # If a block is under maintenance, treat it as occupied in the logic
        self.block_occupancy = [self.block_occupancy[i] or self.maintenance[i] for i in range(len(self.block_occupancy))]
        # Update the tables for the current page and wayside
        self.update_block_table(self.block_occupancy, self.maintenance, self.current_page * 20)
        self.update_authority_table(self.current_page * 20)
        # If not in manual mode, update wayside controllers logic
        if not self.manual_mode:
            self.update_wayside_controllers(self.block_occupancy, self.maintenance, self.block_authorities)
        # Refresh any UI elements to reflect new states
        self.update_ui_elements()
        # Example counter update (if needed for something)
        self.count = (self.count + 1) % 6

    def update_block_table(self, block_occupancy, maintenance, start_block=0):
        """Populate the block occupancy table for the current wayside and page."""
        self.block_table.setRowCount(20)
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]
        for i in range(20):
            block_num = start_block + i
            if block_num < len(wayside_blocks):
                block_id = wayside_blocks[block_num]
                block_item = QTableWidgetItem(f"{block_id}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.block_table.setItem(i, 0, block_item)
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
        """Populate the block authority table for the current wayside and page."""
        self.authority_table.setRowCount(20)
        wayside_blocks = self.wayside_controllers[self.current_wayside]["blocks"]
        block_authority = self.ctc.get_block_authority()
        for i in range(20):
            block_num = start_block + i
            if block_num < len(wayside_blocks):
                block_id = wayside_blocks[block_num]
                block_item = QTableWidgetItem(f"{block_id}")
                block_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 0, block_item)
                authority_item = QTableWidgetItem(str(block_authority[block_id - 1]))
                authority_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.authority_table.setItem(i, 1, authority_item)
            else:
                # Clear the row if there are no more blocks to display
                self.authority_table.setItem(i, 0, QTableWidgetItem(""))
                self.authority_table.setItem(i, 1, QTableWidgetItem(""))

    def update_wayside_controllers(self, block_occupancy, maintenance, block_authorities):
        """Update each wayside controller's logic (except wayside2, which is remote-controlled)."""
        if not self.manual_mode:
            for wayside_name, config in self.wayside_controllers.items():
                # Get the block data for this wayside
                wayside_blocks = config["blocks"]
                wayside_block_occupancy = [block_occupancy[block - 1] for block in wayside_blocks]
                wayside_maintenance = [maintenance[block - 1] for block in wayside_blocks]
                wayside_block_authorities = [block_authorities[block - 1] for block in wayside_blocks]

                # --- Modification: Skip local logic for wayside2; update from socket only ---
                if wayside_name == "wayside2":
                    # Update global switch/light/crossing states from the socket-updated config
                    for i, switch_index in enumerate(config["switches"]):
                        self.switch_states[switch_index] = config["switch_states"][i]
                    for i, light_index in enumerate(config["lights"]):
                        self.light_states[light_index] = config["light_states"][i]
                    for i, crossing_index in enumerate(config["crossings"]):
                        if i < len(config["crossing_states"]):
                            self.crossing_states[crossing_index] = config["crossing_states"][i]
                    continue  # Skip executing any local logic for wayside2

                # If a PLC logic function is loaded for this wayside (wayside1 or wayside3), execute it
                if config["logic_function"] is not None:
                    wayside = WAYSIDE(
                        switches=config["switches"],
                        lights=config["lights"],
                        crossings=config["crossings"],
                        logic_function=config["logic_function"],
                        prev_switch_states=config["switch_states"],
                        block_authorities=wayside_block_authorities
                    )
                    # Execute the PLC logic to get new states
                    switch_states, light_states, crossing_states = wayside.update_wayside(
                        wayside_block_occupancy,
                        wayside_maintenance
                    )
                    # Save the updated states back into the config
                    config["switch_states"] = switch_states
                    config["light_states"] = light_states
                    config["crossing_states"] = crossing_states
                    # Update the global state arrays for switches, lights, crossings
                    for i, switch_index in enumerate(config["switches"]):
                        self.switch_states[switch_index] = switch_states[i]
                    for i, light_index in enumerate(config["lights"]):
                        self.light_states[light_index] = light_states[i]
                    for i, crossing_index in enumerate(config["crossings"]):
                        self.crossing_states[crossing_index] = crossing_states[i]
                # If no logic_function (and not wayside2, since we handled that), do nothing

    def prev_page(self):
        """Go to the previous page of blocks in the tables."""
        self.current_page = max(self.current_page - 1, 0)
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

    def next_page(self):
        """Go to the next page of blocks in the tables."""
        total_blocks = len(self.wayside_controllers[self.current_wayside]["blocks"])
        max_page = (total_blocks + 19) // 20 - 1
        self.current_page = min(self.current_page + 1, max_page)
        self.update_block_table(self.track_model.get_block_occupancy(), self.ctc.get_maintenance_status(), self.current_page * 20)
        self.update_authority_table(self.current_page * 20)

    def update_ui_elements(self):
        """Update any UI elements (e.g., indicators for switches/lights) based on the current wayside state."""
        # (This can be expanded as needed to update UI components that reflect switch/light states)
        pass

    # Getter methods for global states (if needed elsewhere)
    def get_switch_state(self):
        return self.switch_states

    def get_light_state(self):
        return self.light_states

    def get_crossing_state(self):
        return self.crossing_states

    def get_block_occupancy(self):
        return self.block_occupancy

    def get_block_authority(self):
        return self.block_authority

# ---------------------------
# Socket client thread (running on PC to communicate with Raspberry Pi for wayside2)
# ---------------------------
def socket_client_thread(ctc, track_controller, track_model):
    target_ip = "192.168.137.175"  # Raspberry Pi server IP address
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((target_ip, port))
        print("Connected to Raspberry Pi server:", target_ip)
    except Exception as e:
        print("Failed to connect to Raspberry Pi server:", e)
        return
    while True:
        try:
            # Prepare data payload to send to Raspberry Pi (wayside2 logic)
            data = {
                "block_occupancy": track_model.get_block_occupancy(),
                "block_authority": ctc.get_block_authority(),
                "maintenance": ctc.get_maintenance_status(),
                "prev_switch_states": track_controller.wayside_controllers["wayside2"]["switch_states"]
            }
            s.sendall((json.dumps(data) + "\n").encode())
            # Receive response from Raspberry Pi
            response = ""
            while "\n" not in response:
                chunk = s.recv(1024).decode()
                if not chunk:
                    break
                response += chunk
            if response:
                try:
                    resp_data = json.loads(response.strip())
                    print("====== Raspberry Pi 返回结果 ======")
                    print("Switch States  :", resp_data.get("switch_states", []))
                    print("Light States   :", resp_data.get("light_states", []))
                    print("Crossing States:", resp_data.get("crossing_states", []))
                    print("===================================")
                    # Update wayside2's state based on data from Raspberry Pi
                    track_controller.wayside_controllers["wayside2"]["switch_states"] = resp_data.get(
                        "switch_states", track_controller.wayside_controllers["wayside2"]["switch_states"])
                    track_controller.wayside_controllers["wayside2"]["light_states"] = resp_data.get(
                        "light_states", track_controller.wayside_controllers["wayside2"]["light_states"])
                    track_controller.wayside_controllers["wayside2"]["crossing_states"] = resp_data.get(
                        "crossing_states", track_controller.wayside_controllers["wayside2"]["crossing_states"])
                except Exception as e:
                    print("Error parsing returned data:", e)
            # Small delay to avoid flooding the socket
            time.sleep(0.5)
        except Exception as e:
            print("Socket client error:", e)
            time.sleep(1)

# ---------------------------
# Main program entry point
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ctc = CTC()
    track_model = TrackModel()
    track_controller = TrackController(ctc, track_model)
    ctc.set_track_controller(track_controller)
    track_model.set_track_controller(track_controller)
    track_controller.show()
    track_controller.update()  # Initial update to populate UI
    test_bench = TestBench(ctc, track_model)
    test_bench.show()
    # Start the socket client thread for wayside2 communication
    socket_thread = threading.Thread(target=socket_client_thread, args=(ctc, track_controller, track_model), daemon=True)
    socket_thread.start()
    sys.exit(app.exec())
