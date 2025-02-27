from PyQt6.QtCore import Qt, pyqtSlot, QTimer


class Simulator:
    def __init__(self, gui, testbench, train_model, sim_time=100, timer_interval=100):
        # TODO: Extend to list of train_model objects
        self.gui = gui
        self.testbench = testbench
        self.train_model = train_model
        self.sim_time = sim_time
        self.current_step = 0
        self.world_time = {'day': 0, 'hour': 0, 'min': 0}
        self.driver_speed = 10  # active in manual mode
        self.driver_inputs = {}
        self.cmd_power = 0

        # Create the master clock timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.master_loop)
        self.timer.start(timer_interval)  # ms

    def master_loop(self):
        """ The main loop that updates global time. """
        if self.current_step >= self.sim_time:
            print("Simulation complete.")
            self.timer.stop()
            return

        print(f"Master Loop - Step {self.current_step}")

        # Update world time
        self.world_time['min'] += 5
        if self.world_time['min'] >= 60:
            self.world_time['min'] -= 60
            self.world_time['hour'] += 1
        if self.world_time['hour'] >= 24:
            self.world_time['hour'] = 0
            self.world_time['day'] += 1

        # Update all modules (1 train controller per train model)
        self.train_model.iterate(self.world_time)

        # Increment step count
        self.current_step += 1
