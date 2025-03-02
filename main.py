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
from Track_model.Track_model import TrackModel
from simulator.simulator import Simulator


def main():
    k_p = 2e5
    k_i = 2e4

    sim_time = int(1e3)
    app = QApplication(sys.argv)
    Blue_line = TrackModel()
    Blue_line.add_block(1, '0000000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010010110110110110110110110110110100000000000000000NONENONENONENONENONEStaBStaBStaBStaBStaB', [0,0,0,0,0,0,0,0,0,0], [1,2,3,4,5,6,7,8,9,10])
    Blue_line.add_block(2)
    Blue_line.add_block(3)
    Blue_line.add_block(4)
    Blue_line.add_block(5)
    Blue_line.add_block(6)
    Blue_line.add_block(7)
    Blue_line.add_block(8)
    Blue_line.add_block(9)
    Blue_line.add_block(10)

    Blue_line.set_baud_sig(1, '0000100000')

    train_controller_gui = TrainControllerGUI(k_p, k_i)
    train_controller_testbench = TestbenchGUI()
    train_model = TrainModel(k_p, k_i, train_controller_gui, train_controller_testbench)
    train_model.add_classes(Blue_line)

    train_controller_gui.show()
    train_controller_testbench.show()

    # Start the master simulation loop
    sim = Simulator(train_controller_gui, train_controller_testbench, train_model, sim_time=sim_time, timer_interval=int(1e3))

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
