"""
This module should include the GUI for the train controller, and be able to simulate all of its I/O.
"""
import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread

from train_controller import TrainController
from train_controller_gui import TrainControllerGUI
from testbench_gui import TestbenchGUI
from simulator import Simulator


def main():
    # train parameters
    k_p = 50000
    k_i = 5000
    max_engine_power = 1000  # 1000 W
    sample_period = 1
    comfortable_temp = 70  # 70 deg F

    # Test params
    cmd_speed = 14
    authority = 200
    cur_speed = 0
    failure_modes = [False, False, False]
    underground = False
    cabin_temp = 40
    doors_status = [False, False]
    lights_status = [False, False]
    station_to_be_reached = 'Dormont'

    test_params = [cmd_speed, authority, cur_speed, failure_modes, underground, cabin_temp, doors_status,
                   lights_status, station_to_be_reached]

    train_controller = TrainController(k_p, k_i, max_engine_power, sample_period, comfortable_temp)

    sim_time = int(1e3)
    app = QApplication(sys.argv)
    gui = TrainControllerGUI(k_p, k_i)
    testbench = TestbenchGUI()
    gui.show()
    testbench.show()

    # Start the master simulation loop
    sim = Simulator(gui, testbench, train_controller, test_params, sim_time=sim_time, timer_interval=int(1e3))

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
