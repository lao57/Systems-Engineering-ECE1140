from PyQt6.QtCore import Qt, pyqtSlot, QTimer


class Simulator:
    def __init__(self, gui, train_controller, test_params, sim_time=100, timer_interval=100):
        self.gui = gui
        self.train_controller = train_controller
        self.sim_time = sim_time
        self.current_step = 0
        self.world_time = {'day': 0, 'hour': 0, 'min': 0}
        self.driver_speed = 0   # active in manual mode
        self.cmd_speed, self.authority, self.cur_speed, self.failure_modes, self.underground, self.cabin_temp, \
            self.doors_status, self.lights_status, self.station_to_be_reached = test_params
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

        # Update GUI
        self.gui.update_world_time(self.world_time)
        self.gui.update_cur_speed(self.cur_speed)
        self.gui.update_cmd_speed(self.cmd_speed)

        # Update train controller mode (interaction from train driver)
        self.train_controller.train_controller_mode = self.gui.train_controller_mode
        self.driver_speed = self.gui.driver_speed

        if self.train_controller.train_controller_mode == 'Manual':
            print("In manual mode!")
            self.cmd_speed = self.driver_speed
            self.train_controller.train_controller_mode = 'manual'
        else:
            self.train_controller.train_controller_mode = 'auto'

        ebrake, sbrake, cmd_power, modified_cabin_temp, open_doors, open_lights, announcement = \
            self.train_controller.iterate(self.cmd_speed, self.authority, self.cur_speed,
                                          self.failure_modes, self.underground, self.cabin_temp, self.doors_status,
                                          self.lights_status, self.station_to_be_reached, self.world_time)

        self.cabin_temp = modified_cabin_temp
        self.cmd_power = max(cmd_power, 0)

        # Update power cmd
        self.gui.update_power_cmd(self.cmd_power)

        # get next speed based on simplified train model
        self.cur_speed = self.get_next_speed(self.cmd_power)

        # Increment step count
        self.current_step += 1

    def get_next_speed(self, cmd_power, dt=1.0):
        """
        Simulates train speed based on power input.
        Uses basic kinematic equations: F = ma, v = u + at.

        Parameters:
        - cmd_power: Power command (W)
        - dt: Time step (s), default = 1 second

        Returns:
        - cur_speed: Updated train speed (m/s)
        """
        mass = 50000  # Train mass (kg) (assume 50 tons)
        rolling_resistance = 1000  # Constant rolling resistance (N)

        # Calculate force: F = P / v (if v > 0 to avoid divide by zero)
        if self.cur_speed > 0:
            force = cmd_power / self.cur_speed
        else:
            force = cmd_power / 1

        # Apply rolling resistance
        force = force - rolling_resistance

        # Calculate acceleration: a = F / m
        acceleration = force / mass

        # Update speed: v = u + at
        self.cur_speed += acceleration * dt

        return self.cur_speed


