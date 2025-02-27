"""
This module should include the GUI for the train controller, and be able to simulate all of its I/O.
"""
import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread

from train_controller.train_controller_gui import TrainControllerGUI
from train_controller.testbench_gui import TestbenchGUI
from train_model.train_model import TrainModel
from simulator.simulator import Simulator


def main():
    k_p = 50000
    k_i = 5000

    sim_time = int(1e3)
    app = QApplication(sys.argv)

    train_controller_gui = TrainControllerGUI(k_p, k_i)
    train_controller_testbench = TestbenchGUI()
    train_model = TrainModel(k_p, k_i, train_controller_gui, train_controller_testbench)

    train_controller_gui.show()
    train_controller_testbench.show()

    # Start the master simulation loop
    sim = Simulator(train_controller_gui, train_controller_testbench, train_model, sim_time=sim_time, timer_interval=int(1e3))

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
