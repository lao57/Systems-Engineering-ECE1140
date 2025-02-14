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
        self.cur_cabin_temp = None
        self.e_brake_on = False
        self.service_brake_on = False
        self.announce_station = False
        self.set_cabin_temp = comfortable_temp
        # manual/automatic mode
        self.train_controller_mode = "auto"

    def iterate(self, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                world_time: dict):
        """
        :param cmd_speed: Commanded speed (m/s)
        :param authority: Authority (m)
        :param cur_speed: Current speed (m/s)
        :param failure_modes: List of 3 booleans with train engine failure, signal pickup failure, brake failure (1 for failure)
        :param underground: True if underground
        :param cabin_temp: Cabin temperature (F)
        :param doors_status: [left_doors_open, right_doors_open] boolean list
        :param lights_status: [interior_lights_open, exterior_lights_open] boolean list
        :param station_to_be_reached: Station about to be reached
        :param world_time: Dict time: {'hours': int, 'minutes': int} in 24-hour format
        :return: emergency_brake signal: bool, service_brake_force (N), cmd_power (W), modified_cabin_temp (F),
        open_doors: [left_doors_open, right_doors_open], open_lights: [interior_lights_open, exterior_lights_open],
        announcement: bool
        """
        # Start of Safety critical section

        # Check for any failure modes
        if 1 in failure_modes:
            # train engine failure (pull emergence brake)
            if failure_modes[0]:
                self.e_brake_on = True
                return self.e_brake_on, None, None, None
            # signal pickup failure
            if failure_modes[1]:
                pass
            # service brake failure (pull emergence brake)
            if failure_modes[2]:
                self.e_brake_on = True
                return self.e_brake_on

        # check if train directly in front or low authority (risk of crashing)
        if authority <= 20:  # 20 m
            return True

        # End of safety critical section

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
                             world_time)

        return self.e_brake_on, self.service_brake_on, self.cmd_power, self.set_cabin_temp, self.doors_status, \
            self.lights_status, self.announce_station

    def automatic_mode(self, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                       failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                       doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                       world_time: dict):
        # # compute current speed error
        # self.speed_error.append(cmd_speed - cur_speed)
        # # deliver power (according to control law)
        # if len(self.integrated_error) >= 1:
        #     cur_integrated_error = self.integrated_error[-1] + \
        #                            (self.T / 2) * (self.speed_error[-1] + self.speed_error[-2])
        #     self.integrated_error.append(cur_integrated_error)
        # else:
        #     cur_integrated_error = 0
        #     self.integrated_error.append(cur_integrated_error)
        #
        # self.cmd_power = self.k_p * self.speed_error[-1] + self.k_i * cur_integrated_error
        # # recompute cmd_power if greater than or equal to maximum engine power
        # if self.cmd_power >= self.max_engine_power:
        #     cur_integrated_error = self.integrated_error[-1]
        #     self.cmd_power = self.k_p * self.speed_error[-1] + self.k_i * cur_integrated_error

        # about to reach station
        if station_to_be_reached is not None:
            # TODO: Does train model have to pass input regarding which doors to be opened?
            self.most_recent_station = station_to_be_reached
            # For now, open both doors
            self.doors_status = [True, True]
            self.announce_station = True
        else:
            self.doors_status = [False, False]
            self.announce_station = False

        # Check if underground (turn on exterior lights)
        if underground:
            self.lights_status[1] = True
        else:
            self.lights_status[1] = False

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

        # return train controller outputs
        self.e_brake_on = False
        self.service_brake_on = False

    def manual_mode(self, cmd_speed: int | float, authority: int | float, cur_speed: int | float,
                    failure_modes: List[bool], underground: bool, cabin_temp: int | float,
                    doors_status: List[bool], lights_status: List[bool], station_to_be_reached: str,
                    world_time: dict):
        print("cmd_speed in manual mode: ", cmd_speed)

