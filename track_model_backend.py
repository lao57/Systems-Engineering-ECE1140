import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from TrackModelUI import TrackModelUI  # Import GUI
from TrainModel import TrainModel  # Import Train Model
from TrackController import TrackController  # Import Track Controller

class TrackModelBackend:
    def __init__(self, track_controller, train_model):
        """Initialize Track Model Backend with connections to other models."""
        self.app = QApplication(sys.argv)
        self.gui = TrackModelUI(backend=self)  # Connect GUI to backend
        self.track_controller = track_controller  # to Track Controller
        self.train_model = train_model  # to Train Model

        self.blocks = {}  # Stores track block data
        self.occupancy_status = {}  # Block occupancy states
        self.switch_states = {}  # Switch states
        self.light_signals = {}  # Light signals
        self.crossing_states = {}  # Railway crossings
        self.track_circuit_failures = {}  # Track circuit failure states
        self.block_authority = {}  # 10-bit block authority

        # Connect GUI events to backend functions
        self.gui.upload_button.clicked.connect(self.upload_excel)
        self.gui.block_selector.currentIndexChanged.connect(self.update_gui_display)

    ### **🔹 RECEIVING INPUTS FROM TRACK CONTROLLER**
    def receive_block_authority(self, block_num, authority_bits):
        """Update authority for a block from Track Controller."""
        if block_num in self.blocks:
            self.blocks[block_num]["block_authority"] = authority_bits
            self.update_gui_display()

    def receive_switch_state(self, block_num, state):
        """Update switch state from Track Controller."""
        if block_num in self.blocks:
            self.blocks[block_num]["switch_state"] = state
            self.update_gui_display()

    def receive_light_signal(self, block_num, state):
        """Update light signal from Track Controller."""
        if block_num in self.blocks:
            self.blocks[block_num]["light_signal"] = state
            self.update_gui_display()

    def receive_crossing_state(self, block_num, state):
        """Update railway crossing state from Track Controller."""
        if block_num in self.blocks:
            self.blocks[block_num]["crossing_state"] = state
            self.update_gui_display()

    ### **🔹 SENDING OUTPUTS TO TRACK CONTROLLER**
    def send_block_occupancy(self):
        """Send block occupancy status to Track Controller."""
        self.track_controller.receive_block_occupancy(self.occupancy_status)

    def send_failure_status(self):
        """Send failure status of each block to Track Controller."""
        failure_data = {b: self.blocks[b]["track_circuit_failure"] for b in self.blocks}
        self.track_controller.receive_failure_status(failure_data)

    ### **🔹 SENDING OUTPUTS TO TRAIN MODEL**
    def send_authority_to_train_model(self):
        """Send block authority data to Train Model."""
        self.train_model.receive_block_authority(self.block_authority)

    def send_passenger_data_to_train(self):
        """Send passenger count per station to Train Model."""
        passenger_data = {}
        for block in self.blocks:
            passenger_data[block] = self.generate_passenger_data()
        self.train_model.receive_passenger_data(passenger_data)

    ### **🔹 BLOCK OCCUPANCY MANAGEMENT**
    def update_block_occupancy(self, block_num, occupied):
        """Update block occupancy state."""
        if block_num in self.blocks and not self.blocks[block_num]['track_circuit_failure']:
            self.blocks[block_num]["occupancy"] = occupied
            self.occupancy_status[block_num] = occupied
            self.update_gui_display()
            self.send_block_occupancy()  # Notify Track Controller

    def update_track_circuit_failure(self, block_num, failure_status):
        """Set track circuit failure without affecting block occupancy."""
        if block_num in self.blocks:
            self.blocks[block_num]["track_circuit_failure"] = failure_status
            self.gui.update_failure_status(block_num, failure_status)
            self.send_failure_status()  # Notify Track Controller

    ### **🔹 EXCEL FILE UPLOAD & TRACK DATA PARSING**
    def upload_excel(self):
        """Load track layout from an Excel file (.xlsx)."""
        file_path, _ = self.gui.upload_file()
        if file_path:
            try:
                df = pd.read_excel(file_path, sheet_name="Blue Line")
                self.parse_track_data(df)
                self.gui.file_label.setText(f"Loaded: {file_path}")
            except Exception as e:
                self.gui.file_label.setText(f"Error loading file: {e}")

    def parse_track_data(self, df):
        """Parse track data from the Excel sheet and update backend data."""
        self.blocks.clear()
        for _, row in df.iterrows():
            block_num = int(row["Block Number"])
            self.blocks[block_num] = {
                "speed_limit": round(row["Speed Limit (Km/Hr)"] * 0.621371, 1),  # Convert to mph
                "grade": row["Block Grade (%)"],
                "elevation": row["ELEVATION (M)"],
                "block_size": round(row["Block Length (m)"] * 3.28084, 1),  # Convert to feet
                "switch_state": False,
                "light_signal": False,
                "crossing_state": False,
                "occupancy": False,
                "track_circuit_failure": False,
                "block_authority": "0000000000",  # 10-bit authority
            }
            self.occupancy_status[block_num] = False

        self.gui.block_selector.clear()
        self.gui.block_selector.addItems([str(b) for b in self.blocks.keys()])

    ### **🔹 GUI UPDATES**
    def update_gui_display(self):
        """Update GUI when the user selects a block."""
        block_num = int(self.gui.block_selector.currentText())
        if block_num in self.blocks:
            block_data = self.blocks[block_num]
            self.gui.label_widgets["Speed Limit"].setText(f"Speed Limit: {block_data['speed_limit']} mph")
            self.gui.label_widgets["Grade"].setText(f"Grade: {block_data['grade']}%")
            self.gui.label_widgets["Elevation"].setText(f"Elevation: {block_data['elevation']} m")
            self.gui.label_widgets["Block Size"].setText(f"Block Size: {block_data['block_size']} ft")

            self.gui.switch_label.setText(f"Switch Position: {'Straight' if block_data['switch_state'] else 'Diverging'}")
            self.gui.light_signal_label.setText(f"Light Signal: {'Green' if block_data['light_signal'] else 'Red'}")
            self.gui.crossing_label.setText(f"Railway Crossing: {'Closed' if block_data['crossing_state'] else 'Open'}")
            self.gui.occupancy_label.setText(f"Track Occupancy: {'✅' if block_data['occupancy'] else '❌'}")

    ### **🔹 RUN BACKEND**
    def run(self):
        """Launch the GUI event loop."""
        self.gui.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    track_controller = TrackController()  # Initialize Track Controller
    train_model = TrainModel()  # Initialize Train Model
    track_model = TrackModelBackend(track_controller, train_model)
    track_model.run()
