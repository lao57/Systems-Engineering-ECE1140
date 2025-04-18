import sys
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import track_controller.track_controller_red as track_controller_red
import track_model.track_model_backend as track_model_backend
import track_model.track_gui_and_testbench_unified as track_gui_and_testbench_unified
import track_controller.testbench_track_controller as testbench_track_controller
from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel
from ctc_office.ctc_office import CTCOffice, CTC, ScheduleLoader, load_track_layout
from ctc_office.ctc_gui import CTCGUI
from track_controller.track_controller import socket_client_thread

if __name__ == "__main__":
    app = QApplication(sys.argv)
    k_p = 20
    k_i = 5
    world_time = {'day': 0, 'hour': 6, 'min': 30, 'sec': 0} #30 mins before 7 to give setup time

    # --- Create core modules ---
    LOOP_INTERVAL_MS = 10 # 1 second in milliseconds
    track_model = track_model_backend.TrackModelBackend()
    track_controller = track_controller_red.TrackControllerRed()

    # --- CTC Init ---
    track_layout = load_track_layout("assets/Track_Layout.xlsx")
    schedule_loader = ScheduleLoader(track_layout)
    schedules = schedule_loader.load_from_excel("assets/Train_Scheduling.xlsx")

    ctc = CTC()
    ctc_office = CTCOffice(track_layout, schedules, k_p=k_p, k_i=k_i, loop_int_ms=LOOP_INTERVAL_MS)
    ctc_office.set_ctc(ctc)
    ctc_office.set_track_model(track_model)

    # socket_thread = threading.Thread(target=socket_client_thread, args=(ctc, track_controller, track_model), daemon=True)
    # socket_thread.start()

    # --- Wire components ---

    ctc.connect_track_controller(track_controller)
    track_controller.set_ctc(ctc)
    track_controller.set_track_model(track_model)
    track_model.set_track_controller(track_controller)
    # track_model.set_train_model(train_model)

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



    # ctc_gui = CTCGUI(ctc=ctc, ctc_office=ctc_office,
    #                  track_layout=track_layout,
    #                  schedule_loader=schedule_loader,
    #                  track_controller=track_controller)
    # ctc_gui.show()

    # --- Show Unified TrackModelUI + Testbench window and pass backend ---
    # window = track_gui_and_testbench_unified.UnifiedTrackUI(backend=track_model)
    # window.show()

    # --- Set up continuous controller update ---
    # update_timer = QTimer()
    # update_timer.timeout.connect(track_controller.update)
    # update_timer.timeout.connect(track_model.update)
    # update_timer.timeout.connect(train_model.update_train)
    # update_timer.start(1000)  # Update every 1 second

    def update_world():
        """Update the world state periodically."""
        global world_time

        # Increment world time by 1 second per update cycle.
        world_time['sec'] += 1
        if world_time['sec'] >= 60:
            world_time['sec'] = 0
            world_time['min'] += 1
            if world_time['min'] >= 60:
                world_time['min'] = 0
                world_time['hour'] += 1
                if world_time['hour'] >= 24:
                    world_time['hour'] = 0
                    world_time['day'] += 1

        # Compute current minutes since midnight.
        current_minutes = world_time['hour'] * 60 + world_time['min']

        # Launch pending trains if their departure time (expected arrival minus 30 min) is reached.
        # ctc_office.launch_pending_trains(current_minutes)

        # Call update functions on each component.
        # ctc_gui.update_all()
        track_controller.update()
        # track_model.update()
        if len(track_model.blocks) > 0:  # Update train models only if blocks exist
            ctc_office.update_all_trains(world_time, delta_t=1)

        # Update the world clock display on the CTC UI.
        # ctc_gui.update_world_clock(world_time)


    # Use QTimer to control the update frequency
    update_timer = QTimer()
    update_timer.timeout.connect(update_world)
    update_timer.start(LOOP_INTERVAL_MS)  # Update every 1 second

    sys.exit(app.exec())
