import pandas as pd

class TrackModelBackend:
    def __init__(self):
        """Initialize Track Model Backend with connections to other models."""
        self.track_controller = None  # to Track Controller
        self.train_model = None       # to Train Model

        self.ready = False  # Indicates if the backend is ready

        self.blocks = {}  # Stores track block data
        self.occupancy_status = [False]*150      # Block occupancy states (moving train)
        self.failure_occupancy = [False]*150     # Sticky occupancy flags set by failures
        self.switch_states = []                  # Switch states
        self.light_signals = []                  # Light signals
        self.crossing_states = []                # Railway crossings
        self.track_circuit_failures = []         # Track circuit failure states
        self.block_authority = []                # 10-bit block authority as string/int
        self.failure_status = []                 # Failure toggles per block

        # UI component
        self.ui = None

    def addUI(self, ui):
        self.ui = ui

    def get_occupancy_status(self, block_num):
        if 0 <= block_num < len(self.occupancy_status):
            return self.occupancy_status[block_num]
        return False

    def get_track_circuit_failures(self, block_num):
        if 0 <= block_num < len(self.track_circuit_failures):
            return self.track_circuit_failures[block_num]
        return False

    def get_switch_states(self, block_num):
        return self.switch_states[block_num] if 0 <= block_num < len(self.switch_states) else False

    def get_light_signals(self, block_num):
        return self.light_signals[block_num] if 0 <= block_num < len(self.light_signals) else False

    def get_crossing_states(self, block_num):
        return self.crossing_states[block_num] if 0 <= block_num < len(self.crossing_states) else False

    def get_block_authority(self, block_id):
        idx = block_id - 1
        if 0 <= idx < len(self.block_authority):
            bits = self.block_authority[idx]
            if isinstance(bits, int):
                return bits
            return int(''.join('1' if b else '0' for b in bits), 2)
        return 0

    def get_all_blocks(self):
        return list(self.blocks.keys())

    def get_block_data(self, block_num):
        return self.blocks.get(block_num)

    # ---------------------------
    # Load & parse layout
    # ---------------------------
    def load_excel(self, file_path):
        print(f"Loading layout from: {file_path}")
        try:
            df = pd.read_csv(file_path)
            self.parse_track_data(df)
        except Exception as e:
            print(f"Error loading layout: {e}")

    def parse_track_data(self, df):
        self.blocks.clear()
        for _, row in df.iterrows():
            num = int(row["Block Number"])
            self.blocks[num] = {
                "speed_limit": round(row["Speed Limit (Km/Hr)"] * 0.621371, 1),
                "grade": row["Block Grade (%)"],
                "elevation": row["ELEVATION (M)"],
                "block_size": round(row["Block Length (m)"] * 3.28084, 1),
                "occupancy": False,
                "track_heater": False,
            }
        n = len(self.blocks)
        self.occupancy_status       = [False]*n
        self.failure_occupancy      = [False]*n
        self.switch_states          = [False]*n
        self.light_signals          = [False]*n
        self.crossing_states        = [False]*n
        self.track_circuit_failures = [False]*n
        self.block_authority        = [0]*n
        self.failure_status         = [False]*n
        self.ready = True

    # ---------------------------
    # Failures
    # ---------------------------
    def handle_failures(self, failures):
        """
        failures: dict mapping failure-name -> bool
        Only marks that one selected block’s failure_occupancy.
        """
        # Expect GUI to call update_block_occupancy directly
        if self.ui:
            self.ui.update()

    # ---------------------------
    # Temperature → Heater
    # ---------------------------
    def update_temperature(self, temperature):
        on = (temperature <= 32)
        for blk in self.blocks:
            self.blocks[blk]["track_heater"] = on
        if self.ui:
            self.ui.update()

    # ---------------------------
    # Occupancy update
    # ---------------------------
    def update_block_occupancy(self, block_num, occupied=True):
        idx = block_num - 1
        if 0 <= idx < len(self.failure_occupancy):
            # Mark sticky occupancy if via failure toggle
            self.failure_occupancy[idx] = occupied
        if self.ui:
            self.ui.update()

    # ---------------------------
    # Periodic synchronization
    # ---------------------------
    def update(self):
        if not self.blocks:
            return

        # 1) Clear dynamic occupancy
        self.occupancy_status = [False]*len(self.blocks)

        # 2) Pull live occupancy from track_controller if set
        if self.track_controller and hasattr(self.track_controller, 'occupancy_status'):
            for blk in self.blocks:
                idx = blk - 1
                if 0 <= idx < len(self.occupancy_status):
                    self.occupancy_status[idx] = self.track_controller.occupancy_status[idx]

        # 3) Re-apply only those failure occupancy flags
        for i, flag in enumerate(self.failure_occupancy):
            if flag and 0 <= i < len(self.occupancy_status):
                self.occupancy_status[i] = True

        # 4) Sync other signals from controller
        if self.track_controller:
            self.switch_states       = self.track_controller.switch_states[:]
            self.light_signals       = self.track_controller.light_states[:]
            self.crossing_states     = self.track_controller.crossing_states[:]
            self.block_authority     = self.track_controller.block_authority[:]

        # 5) Refresh UI
        if self.ui:
            self.ui.update()

    # ---------------------------
    # Dependency setters
    # ---------------------------
    def set_track_controller(self, tc):
        self.track_controller = tc

    def set_train_model(self, tm):
        self.train_model = tm

    def station_stop(self, block, num_on_train, max_pass):
        passengers_on_block = 4
        new_num = num_on_train + passengers_on_block
        return min(new_num, max_pass)
