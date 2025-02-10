"""
This module should include the GUI for the train controller, and be able to simulate all of its I/O.
"""
import sys
from PyQt6.QtWidgets import QApplication

from train_controller import TrainController
from train_controller_gui import TrainControllerGUI


def main():
    # train parameters
    k_p = 100
    k_i = 10
    max_engine_power = 1000  # 1000 W
    sample_period = 1
    comfortable_temp = 70  # 70 deg F

    train_controller = TrainController(k_p, k_i, max_engine_power, sample_period, comfortable_temp)

    sim_time = int(1e3)
    app = QApplication(sys.argv)
    gui = TrainControllerGUI(k_p, k_i)
    gui.show()

    sys.exit(app.exec())

    # for t in range(sim_time):


if __name__ == '__main__':
    main()
