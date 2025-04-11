import sys
import importlib.util
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import track_controller.TrackController as TrackController
import TrackModelBackend
import track_gui_and_testbench_unified
import track_controller.testbench_track_controller as testbench_track_controller
from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel
from track_loader import load_track_layout
from schedule_loader import ScheduleLoader
from ctc import CTC
from ctc_office import CTCOffice
from CTC_GUI import CTCGUI
from track_controller.TrackController import socket_client_thread
from track_controller.TrackControllerRed import TrackControllerRed

import threading



if __name__ == "__main__":
    app = QApplication(sys.argv)
    k_p = 20
    k_i = 5
    i = 0
    world_time = {'day': 0, 'hour': 0, 'min': 0}
    # --- Create core modules ---

    track_model = TrackModelBackend.TrackModelBackend()
    #track_controller = TrackController.TrackController()
    track_controller = TrackControllerRed()


    # --- CTC Init ---
    track_layout = load_track_layout("assets/Track_Layout.xlsx")
    schedule_loader = ScheduleLoader(track_layout)
    schedules = schedule_loader.load_from_excel("assets/Train_Scheduling.xlsx")

    ctc = CTC()
    ctc_office = CTCOffice(track_layout, schedules, k_p=k_p, k_i=k_i)
    ctc_office.set_ctc(ctc)
    ctc_office.set_track_model(track_model)

    # socket_thread = threading.Thread(target=socket_client_thread, args=(ctc, track_controller, track_model), daemon=True)
    # socket_thread.start()

    # --- Wire components ---
    
    ctc.connect_track_controller(track_controller)
    track_controller.set_ctc(ctc)
    track_controller.set_track_model(track_model)
    track_model.set_track_controller(track_controller)
    #track_model.set_train_model(train_model)

    print("[Main] TrackModel connected to TrackController")


    # Ensure TrackModelBackend updates switches, lights, crossings, and authority
    def sync_backend_with_controller():
        for block_num in range(1, 151):
            # Sync switches
            switch_state = track_controller.switch_states[block_num % len(track_controller.switch_states)]
            track_model.receive_switch_state(block_num, switch_state)

            # Sync light signals
            light_state = track_controller.light_states[block_num % len(track_controller.light_states)]
            track_model.receive_light_signal(block_num, light_state)

            # Sync crossings
            crossing_state = track_controller.crossing_states[block_num % len(track_controller.crossing_states)]
            track_model.receive_crossing_state(block_num, crossing_state)

            # Sync block authority
            authority = track_controller.get_block_authority()[block_num - 1]
            track_model.receive_block_authority(block_num, authority)

        # Update GUI state
        track_model.gui.update_gui_display()
        print("[Main] Backend synced with Track Controller")

    # --- Show Track Controller UI ---
    track_controller.show()

    track_controller_tb = testbench_track_controller.TestBench(ctc, track_model)
    track_controller_tb.show()



    ctc_gui = CTCGUI(ctc=ctc, ctc_office=ctc_office,
                     track_layout=track_layout,
                     schedule_loader=schedule_loader,
                     track_controller=track_controller)
    ctc_gui.show()

    # --- Show Unified TrackModelUI + Testbench window and pass backend ---
    window = track_gui_and_testbench_unified.UnifiedTrackUI(backend=track_model)
    window.show()

    # --- Set up continuous controller update ---
    #update_timer = QTimer()
    #update_timer.timeout.connect(track_controller.update)
    #update_timer.timeout.connect(track_model.update)
    #update_timer.timeout.connect(train_model.update_train)
    #update_timer.start(1000)  # Update every 1 second

    def update_world():
        """Update the world state periodically."""
        global world_time
        ctc_gui.update_all()
        track_controller.update()
        track_model.update()
        if len(track_model.blocks) > 0: # Update train model only if blocks exist
            ctc_office.update_all_trains(world_time, delta_t=1)
            #print(len(track_model.blocks))

    # Use QTimer to control the update frequency
    update_timer = QTimer()
    update_timer.timeout.connect(update_world)
    update_timer.start(10)

    # --- Run the application loop ---
    sys.exit(app.exec())
