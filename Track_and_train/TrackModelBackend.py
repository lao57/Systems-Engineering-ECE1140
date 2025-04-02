import pandas as pd

class TrackModelBackend:
    def __init__(self):
        """Initialize Track Model Backend with connections to other models."""
        self.track_controller = None  # to Track Controller
        self.train_model = None       # to Train Model

        self.ready = False  # Indicates if the backend is ready

        self.blocks = {}  # Stores track block data
        self.occupancy_status = [False]*150  # Block occupancy states
        self.switch_states = []     # Switch states
        self.light_signals = []       # Light signals
        self.crossing_states = []    # Railway crossings
        self.track_circuit_failures = []  # Track circuit failure states
        self.block_authority = [] # 10-bit block authority as string
        self.failure_status = []  # Track circuit failure status

        #Addng UI
        self.ui = None  # Placeholder for UI component

    # ---------------------------
    # Methods to expose backend state
    # ---------------------------
    def addUI(self, ui):
        """Add UI component to the backend."""
        self.ui = ui

    def get_occupancy_status(self, block_num):
        """Return the occupancy status of a block."""
        return self.occupancy_status[block_num]

    def get_track_circuit_failures(self, block_num):
        """Return the track circuit failure status of a block."""
        return self.track_circuit_failures[block_num]

    def get_switch_states(self, block_num):
        """Return the switch state of a block."""
        if block_num >= len(self.switch_states):
            return False
        return self.switch_states[block_num]

    def get_light_signals(self, block_num):
        """Return the light signal state of a block."""
        if block_num >= len(self.light_signals):
            return False
        return self.light_signals[block_num]

    def get_crossing_states(self, block_num):
        """Return the railway crossing state of a block."""
        if block_num >= len(self.crossing_states):
            return False
        return self.crossing_states[block_num]

    def get_block_authority(self, block_num):
        """Return the block authority of a block."""
        return self.block_authority[int(block_num)]

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
        print(f"Loading Excel file in backend: {file_path}")
        try:
            df = pd.read_csv(file_path)
            self.parse_track_data(df)
        except Exception as e:
            print(f"Error loading file: {e}")

    def parse_track_data(self, df):
        """Parse track data from the Excel sheet and update backend data."""
        print(f"parsiing track data from {df}")
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
                "track_circuit_failure": [False, False, False, False, False],  # Track circuit failure states
                "track_heater": False,  # Track heater state
                "beacon_signal": row.get("beacon_signal", None),  # New: Beacon signal from Excel
                "block_authority": "0000000000",  # 10-bit authority as a string
                "grade_vector": row.get("grade_vector", None),  # New: Grade vector from Excel
                "block_vector": row.get("block_vector", None),  # New: Block vector from Excel
            }

        # Update backend state arrays
        self.occupancy_status = [False] * len(self.blocks)  # Block occupancy states
        self.switch_states = [False] * len(self.blocks)  # Switch states
        self.light_signals = [False] * len(self.blocks)  # Light signals
        self.crossing_states = [False] * len(self.blocks)  # Railway crossings
        self.track_circuit_failures = [False] * len(self.blocks)  # Track circuit failure states
        self.block_authority = ["0000000000"] * len(self.blocks)  # 10-bit block authority as string
        self.failure_status = [False] * len(self.blocks)  # Track circuit failure status
        self.ui.failure_vector = [[False] * 5 for _ in range(len(self.blocks))]  # Track circuit failure status

        # Print all blocks with their information
        for block_num, block_data in self.blocks.items():
            print(f"Block {block_num}: {block_data}")
            print("-----------------------------------------------------------")
            print("-----------------------------------------------------------")

        self.ready = True  # Mark backend as ready after loading data

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

    def update_block_occupancy(self, block_num_begin, block_num_middle, block_num_end, occupied = True):
        """Update block occupancy state."""
        if block_num_begin in self.blocks:
            self.blocks[block_num_begin]["occupancy"] = occupied
            self.occupancy_status[block_num_begin] = occupied
        if block_num_middle in self.blocks:
            self.blocks[block_num_middle]["occupancy"] = occupied
            self.occupancy_status[block_num_middle] = occupied
        if block_num_end in self.blocks:
            self.blocks[block_num_end]["occupancy"] = occupied
            self.occupancy_status[block_num_end] = occupied

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

    def get_beacon_from_block(self, block_num):
        """Return the beacon signal for a specific block."""
        if block_num in self.blocks:
            return self.blocks[block_num]["beacon_signal"]
        return "0000"
    
    def get_block_vector_from_block(self, block_num):
        """Return the block vector for a specific block."""
        if block_num in self.blocks:
            return self.blocks[block_num]["block_vector"]
        return None
    
    def get_grade_from_block(self, block_num):
        """Return the grade vector for a specific block."""
        if block_num in self.blocks:
            return self.blocks[block_num]["grade_vector"]
        return None


    def update(self):
        if not self.blocks:
            return
        else:
            self.occupancy_status = self.failure_status
            self.switch_states = self.track_controller.switch_states
            self.light_signals = self.track_controller.light_states
            self.crossing_states = self.track_controller.crossing_states
            self.block_authority = self.track_controller.block_authority
            self.blocks[1]["block_authority"] = "0000001010"
            for block_num in self.blocks:
                self.blocks[block_num]["switch_state"] = self.switch_states[block_num-1]
                self.blocks[block_num]["light_signal"] = self.light_signals[block_num-1]
                self.blocks[block_num]["crossing_state"] = self.crossing_states[block_num-1]
                self.blocks[block_num]["track_circuit_failure"] = self.track_circuit_failures[block_num-1]
                print(f"Block {block_num}: set with {block_num - 1}")
            print("Updating backend with track controller data")

        self.ui.update()

    # ---------------------------
    # SETTERS FOR DEPENDENCIES
    # ---------------------------
    def set_track_controller(self, track_controller):
        self.track_controller = track_controller

    def set_train_model(self, train_model):
        self.train_model = train_model