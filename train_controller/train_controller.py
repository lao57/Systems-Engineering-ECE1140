from typing import List


class TrainController:
    """
    TrainController class for I/O with one train
    """

    def __init__(self, k_p, k_i, max_engine_power, sample_period, comfortable_temp,
                 gui, testbench):
        self.k_p = k_p
        self.k_i = k_i
        self.max_engine_power = max_engine_power
        self.integrated_error = []  # u_k
        self.speed_error = []  # e_k
        self.T = sample_period  # T (sample period)
        self.comfortable_temp = comfortable_temp

        # train status
        self.cmd_power = 0
        self.cmd_speed = 0
        self.cur_speed = 0
        self.prev_speed = 0
        self.authority = 1000
        self.distance_travelled = 0

        self.nudge_train_fwd = False

        self.most_recent_station = 'Dormont'
        self.doors_status = [False, False]  # [left_doors_open, right_doors_open]
        self.lights_status = [False, False]  # [interior_lights_open, exterior_lights_open]
        self.underground = False
        self.cur_cabin_temp = 0.00
        self.e_brake_on = False
        self.service_brake_decel = 0
        self.announce_station = False
        self.set_cabin_temp = comfortable_temp
        self.driver_inputs = {'ebrake': False, 'sbrake': 0.0}
        self.failure_modes = [False, False, False]  # [train engine failure, signal pickup failure, brake failure]

        # manual/automatic mode
        self.train_controller_mode = "auto"
        # train stats
        self.max_sbrake_decel = 1.2  # 1.2 m/s
        self.max_ebrake_decel = 2.73  # 2.73 m/s
        self.max_train_speed = 19.4  # 19.4 m/s
        self.max_power = 120e3
        # station speed limits (stored as a dict in train controller module)
        self.stations = {'Dormont': {'speed_limit': 18}, 'Edgebrook': {'speed_limit': 18.5},
                         'Pioneer': {'speed_limit': 18.5}}
        self.speed_limit = self.max_train_speed

        # gui
        self.gui = gui
        self.testbench = testbench

    def iterate(self, cur_accel, prev_accel, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                world_time: dict):
        """
        :param cmd_speed: Commanded speed (m/s)
        :param authority: Authority (m)
        :param cur_speed: Current speed (m/s)
        :param failure_modes: List of 3 booleans: [train engine failure, signal pickup failure, brake failure (True for failure)]
        :param underground: underground vector (TODO)
        :param cabin_temp: Cabin temperature (F)
        :param doors_status: [left_doors_open, right_doors_open] boolean list
        :param lights_status: [interior_lights_on, exterior_lights_on] boolean list
        :param station_to_be_reached: (TODO)
        :param world_time: Dict time: {'hours': int, 'minutes': int} in 24-hour format
        :return: emergency_brake signal: bool, service_brake_force (m/s^2), cmd_power (W), modified_cabin_temp (F),
        open_doors: [left_doors_open, right_doors_open], open_lights: [interior_lights_open, exterior_lights_open],
        announcement: bool
        """
        # Start of Safety critical section
        self.failure_modes = failure_modes
        self.authority = authority
        self.cur_speed = cur_speed
        # Check for any failure modes
        if True in self.failure_modes:
            # train engine failure (pull emergence brake)
            if self.failure_modes[0]:
                self.e_brake_on = True
                self.service_brake_decel = 0.0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station
            # signal pickup failure
            if self.failure_modes[1]:
                self.e_brake_on = True
                self.service_brake_decel = 0.0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station
            # service brake failure (pull emergence brake)
            if self.failure_modes[2]:
                self.e_brake_on = True
                self.service_brake_decel = 0.0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station

        # check if train directly in front or low authority (risk of crashing)
        # if self.authority <= 20:  # 20 m
        # e_brake_stopping_distance = (self.cur_speed ** 2) / (2 * self.max_ebrake_decel) + 40

        # if stopped prematurely, nudge train ahead, until authority is approx 0
        ovr_world_time = world_time['day'] + world_time['hour'] + world_time['min']
        if self.authority > 1 and cur_speed == 0 and ovr_world_time != 0:  # 5 m
            cmd_speed = authority * 0.1
        else:
            stopping_distance = (self.cur_speed ** 2) / (2 * abs(self.max_sbrake_decel))
            if self.authority <= stopping_distance + 16:
                self.e_brake_on = False
                self.service_brake_decel = self.max_sbrake_decel
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station

            if self.authority <= 70 and self.service_brake_decel == 0:    # 70 m
                self.e_brake_on = True
                self.service_brake_decel = 0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station

        # End of safety critical section

        # about to reach station
        # TODO: Parse beacon signal
        # if station_to_be_reached != self.most_recent_station and station_to_be_reached in self.stations:
        #     self.most_recent_station = station_to_be_reached
        #     # For now, open both doors
        #     self.doors_status = doors_status
        #     self.announce_station = True
        # else:
        #     self.doors_status = doors_status
        #     self.announce_station = False

        # self.cmd_speed = cmd_speed
        self.speed_limit = self.stations[self.most_recent_station]['speed_limit']
        if self.speed_limit > self.max_train_speed:  # never exceed max train speed
            self.speed_limit = self.max_train_speed
        # clamp cmd_speed
        cmd_speed = min(cmd_speed, self.speed_limit)

        # compute current speed error
        self.speed_error.append(cmd_speed - cur_speed)
        # deliver power (according to control law)
        if len(self.integrated_error) >= 1:
            cur_integrated_error = self.integrated_error[-1] + \
                                   (self.T / 2) * (self.speed_error[-1] + self.speed_error[-2])
            self.integrated_error.append(cur_integrated_error)
        else:
            cur_integrated_error = 0
            self.integrated_error.append(cur_integrated_error)

        self.cmd_power = self.k_p * self.speed_error[-1] + self.k_i * cur_integrated_error
        # recompute cmd_power if greater than or equal to maximum engine power
        if self.cmd_power >= self.max_engine_power:
            cur_integrated_error = self.integrated_error[-1]
            self.cmd_power = self.k_p * self.speed_error[-1] + self.k_i * cur_integrated_error

        # Check if underground (turn on exterior lights)
        # TODO: Parse beacon signal
        # if underground:
        #     self.lights_status[1] = True

        # manual mode
        if self.train_controller_mode == "auto":
            self.automatic_mode(cmd_speed, authority, cur_speed,
                                failure_modes, underground, cabin_temp,
                                doors_status, lights_status, station_to_be_reached,
                                world_time)
        else:
            self.manual_mode(cmd_speed, authority, cur_speed,
                             failure_modes, underground, cabin_temp,
                             doors_status, lights_status, station_to_be_reached,
                             self.driver_inputs, world_time)

        self.cmd_power = max(self.cmd_power, 0)
        # self.cmd_power = min(self.cmd_power, self.max_power)

        # take testbench inputs as priority
        self.lights_status = lights_status

        # perform state estimation
        self.estimate_state(cur_speed, self.prev_speed)

        self.prev_speed = cur_speed

        return self.e_brake_on, self.service_brake_decel, self.cmd_power, self.set_cabin_temp, self.doors_status, \
            self.lights_status, self.announce_station

    def automatic_mode(self, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                       failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                       doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                       world_time: dict):
        if (cur_speed - cmd_speed) > 10 or (cur_speed - self.speed_limit) > 10:
            self.service_brake_decel = self.max_sbrake_decel
        elif (cur_speed - cmd_speed) > 3 or (cur_speed - self.speed_limit) > 3:
            self.service_brake_decel = self.max_sbrake_decel * 0.5
        else:
            self.service_brake_decel = 0.0

        # Check if nighttime (between 8 pm and 6 am)
        if world_time['hour'] >= 20 or world_time['hour'] <= 6:
            self.lights_status[0] = True

        # Check if comfortable cabin temp (F)
        self.cur_cabin_temp = cabin_temp
        self.set_cabin_temp = cabin_temp
        if self.cur_cabin_temp != self.comfortable_temp:
            self.set_cabin_temp = self.comfortable_temp

        self.e_brake_on = False

    def manual_mode(self, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                    failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                    doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                    driver_inputs: dict, world_time: dict):
        self.service_brake_decel = driver_inputs['sbrake']

        if driver_inputs['ebrake']:
            self.e_brake_on = True
            self.cmd_power = 0
            self.service_brake_decel = 0.0
        else:
            self.e_brake_on = False

        self.set_cabin_temp = cabin_temp

    def estimate_state(self, cur_speed, prev_speed):
        """State estimation: distance travelled estimation using speed."""
        # TODO: Use this info to know if underground, station name
        self.distance_travelled += 1/2 * (cur_speed + prev_speed) * self.T
        self.authority -= self.distance_travelled
        self.authority = max(self.authority, 0)
        # compute position using beacon (to check if we have arrived at the desired station/block)
        self.__use_beacon_info__()

    def __use_beacon_info__(self):
        pass

    def get_user_inputs(self):
        """
        Get user inputs from UI
        """
        # Train controller testbench
        if self.train_controller_mode == 'Manual':
            self.cmd_speed = self.gui.driver_speed
            self.train_controller_mode = 'manual'
            self.driver_inputs = {'ebrake': self.gui.e_brake_on, 'sbrake': self.gui.service_brake_decel}
            self.cur_cabin_temp = self.gui.cur_cabin_temp
            self.lights_status[0] = self.gui.lights_status[0]
        else:
            self.train_controller_mode = 'auto'

        # take testbench inputs if event occurs
        if self.testbench.cmd_speed_event:
            self.cmd_speed = self.testbench.cmd_speed
            self.testbench.cmd_speed_event = False

        if self.testbench.authority_event:
            self.authority = self.testbench.authority
            self.testbench.authority_event = False

        if self.testbench.cur_speed_event:
            self.cur_speed = self.testbench.cur_speed
            self.testbench.cur_speed_event = False

        if self.testbench.failure_mode_event:
            self.failure_modes = self.testbench.failure_modes
            self.testbench.failure_mode_event = False

        # if self.train_controller_testbench.underground_event:
        #     self.underground = self.train_controller_testbench.underground
        #     self.train_controller_testbench.underground_event = False

        if self.testbench.cabin_temp_event:
            self.set_cabin_temp = self.testbench.cabin_temp
            self.testbench.cabin_temp_event = False

        if self.testbench.doors_status_event:
            self.doors_status = self.testbench.doors_status
            self.testbench.doors_status_event = False

        if self.testbench.lights_status_event:
            self.lights_status = self.testbench.lights_status
            self.testbench.lights_status_event = False

        # if self.train_controller_testbench.station_to_be_reached_event:
        #     self.station_to_be_reached = self.train_controller_testbench.station_to_be_reached
        #     self.train_controller_testbench.station_to_be_reached_event = False
