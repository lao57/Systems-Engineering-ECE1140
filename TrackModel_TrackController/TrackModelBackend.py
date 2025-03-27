import pandas as pd

class TrackModelBackend:
    def __init__(self):
        """Initialize Track Model Backend with connections to other models."""
        self.track_controller = None  # to Track Controller
        self.train_model = None       # to Train Model

        self.blocks = {}  # Stores track block data
        self.occupancy_status = [False] * 150  # Block occupancy states
        self.switch_states = [False] * 6       # Switch states
        self.light_signals = [False] * 6       # Light signals
        self.crossing_states = [False] * 2     # Railway crossings
        self.track_circuit_failures = [False] * 150  # Track circuit failure states
        self.block_authority = ["0000000000"] * 150  # 10-bit block authority as string

    # ---------------------------
    # Methods to expose backend state
    # ---------------------------
    def get_occupancy_status(self, block_num):
        """Return the occupancy status of a block."""
        return self.occupancy_status[block_num]

    def get_track_circuit_failures(self, block_num):
        """Return the track circuit failure status of a block."""
        return self.track_circuit_failures[block_num]

    def get_switch_states(self, block_num):
        """Return the switch state of a block."""
        return self.switch_states[block_num]

    def get_light_signals(self, block_num):
        """Return the light signal state of a block."""
        return self.light_signals[block_num]

    def get_crossing_states(self, block_num):
        """Return the railway crossing state of a block."""
        return self.crossing_states[block_num]

    def get_block_authority(self, block_num):
        """Return the block authority of a block."""
        return self.block_authority[block_num]

    def get_all_blocks(self):
        """Return a list of all block numbers."""
        return list(self.blocks.keys())

    def get_block_data(self, block_num):
        """Return all data for a specific block."""
        if block_num in self.blocks:
            return self.blocks[block_num]
        return None

    def load_excel(self, file_path):
        """Load track layout from an Excel file."""
        try:
            df = pd.read_excel(file_path, sheet_name="Blue Line")
            self.parse_track_data(df)
        except Exception as e:
            print(f"Error loading file: {e}")

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
                "block_authority": "0000000000",  # 10-bit authority as a string
            }
            self.occupancy_status[block_num] = False

    def handle_failures(self, failures):
        """Update backend variables based on detected failures."""
        for failure, state in failures.items():
            if state:  # If the failure is active
                if failure == "Broken Rail":
                    # Mark all blocks as occupied (example logic)
                    for block_num in self.blocks:
                        self.update_block_occupancy(block_num, True)
                elif failure == "Track Circuit":
                    # Mark specific blocks as having a track circuit failure
                    for block_num in self.blocks:
                        self.update_track_circuit_failure(block_num, True)
                elif failure == "Power Failure":
                    # Handle power failure (e.g., disable signals)
                    for block_num in self.blocks:
                        self.blocks[block_num]["light_signal"] = False
                elif failure == "Maintenance":
                    # Handle maintenance mode (e.g., disable occupancy)
                    for block_num in self.blocks:
                        self.update_block_occupancy(block_num, False)

    def update_block_occupancy(self, block_num, occupied):
        """Update block occupancy state."""
        if block_num in self.blocks:
            self.blocks[block_num]["occupancy"] = occupied
            self.occupancy_status[block_num] = occupied

    def update_track_circuit_failure(self, block_num, failure_status):
        """Set track circuit failure without affecting block occupancy."""
        if block_num in self.blocks:
            self.blocks[block_num]["track_circuit_failure"] = failure_status
            self.track_circuit_failures[block_num] = failure_status

    def update_temperature(self, temperature):
        """Update backend variables based on temperature changes."""
        if temperature <= 32:
            # Enable track heaters for all blocks
            for block_num in self.blocks:
                self.blocks[block_num]["track_heater"] = True
        else:
            # Disable track heaters for all blocks
            for block_num in self.blocks:
                self.blocks[block_num]["track_heater"] = False

    # ---------------------------
    # SETTERS FOR DEPENDENCIES
    # ---------------------------
    def set_track_controller(self, track_controller):
        self.track_controller = track_controller

    def set_train_model(self, train_model):
        self.train_model = train_model