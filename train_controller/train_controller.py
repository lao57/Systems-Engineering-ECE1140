from typing import List


class TrainController:
    """
    TrainController class for I/O with one train
    """

    def __init__(self, k_p, k_i, max_engine_power, sample_period, comfortable_temp):
        self.k_p = k_p
        self.k_i = k_i
        self.max_engine_power = max_engine_power
        self.integrated_error = []  # u_k
        self.speed_error = []  # e_k
        self.T = sample_period  # T (sample period)
        self.comfortable_temp = comfortable_temp
        # train status
        self.cmd_power = 0
        self.most_recent_station = None
        self.doors_status = [False, False]  # [left_doors_open, right_doors_open]
        self.lights_status = [False, False]  # [interior_lights_open, exterior_lights_open]
        self.underground = False
        self.cur_cabin_temp = 0.00
        self.e_brake_on = False
        self.service_brake_decel = 0
        self.announce_station = False
        self.set_cabin_temp = comfortable_temp
        # manual/automatic mode
        self.train_controller_mode = "auto"
        # train stats
        self.max_sbrake_decel = 1.2  # 1.2 m/s
        self.max_ebrake_decel = 2.73  # 2.73 m/s
        self.max_train_speed = 19.4  # 19.4 m/s
        # station speed limits (stored as a dict in train controller module)
        self.stations = {'Dormont': {'speed_limit': 18}, 'Edgebrook': {'speed_limit': 18.5},
                         'Pioneer': {'speed_limit': 18.5}}
        self.speed_limit = self.max_train_speed

    def iterate(self, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                driver_inputs: dict, world_time: dict):
        """
        :param cmd_speed: Commanded speed (m/s)
        :param authority: Authority (m)
        :param cur_speed: Current speed (m/s)
        :param failure_modes: List of 3 booleans with train engine failure, signal pickup failure, brake failure (1 for failure)
        :param underground: True if underground
        :param cabin_temp: Cabin temperature (F)
        :param doors_status: [left_doors_open, right_doors_open] boolean list
        :param lights_status: [interior_lights_on, exterior_lights_on] boolean list
        :param station_to_be_reached: Station about to be reached
        :param world_time: Dict time: {'hours': int, 'minutes': int} in 24-hour format
        :return: emergency_brake signal: bool, service_brake_force (m/s^2), cmd_power (W), modified_cabin_temp (F),
        open_doors: [left_doors_open, right_doors_open], open_lights: [interior_lights_open, exterior_lights_open],
        announcement: bool
        """
        # Start of Safety critical section

        # Check for any failure modes
        if True in failure_modes:
            # train engine failure (pull emergence brake)
            if failure_modes[0]:
                self.e_brake_on = True
                self.service_brake_decel = 0.0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station
            # signal pickup failure
            if failure_modes[1]:
                self.e_brake_on = True
                self.service_brake_decel = 0.0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station
            # service brake failure (pull emergence brake)
            if failure_modes[2]:
                self.e_brake_on = True
                self.service_brake_decel = 0.0
                self.cmd_power = 0
                return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                    self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station

        # check if train directly in front or low authority (risk of crashing)
        if authority <= 20:  # 20 m
            self.e_brake_on = True
            self.service_brake_decel = 0.0
            self.cmd_power = 0
            return self.e_brake_on, self.service_brake_decel, self.cmd_power, \
                self.set_cabin_temp, self.doors_status, self.lights_status, self.announce_station

        # End of safety critical section

        # about to reach station
        if station_to_be_reached != self.most_recent_station and station_to_be_reached in self.stations:
            self.most_recent_station = station_to_be_reached
            # For now, open both doors
            self.doors_status = doors_status
            self.announce_station = True
        else:
            self.doors_status = doors_status
            self.announce_station = False

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
        if underground:
            self.lights_status[1] = True
        else:
            self.lights_status[1] = False

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
                             driver_inputs, world_time)

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
        else:
            self.lights_status[0] = False

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

        # only modify indoor lights
        self.lights_status[0] = lights_status[0]
