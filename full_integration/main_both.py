import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ctc_office.ctc_office_both import CTCOffice, CTC, ScheduleLoader, load_track_layout
from ctc_office.ctc_gui_both import CTCGUI
import track_controller.track_controller as track_controller
import track_model.track_model_backend as track_model_backend
import track_model.track_gui_and_testbench_unified as track_gui_and_testbench_unified
import track_controller.testbench_track_controller as testbench_track_controller
import track_controller.track_controller_red as track_controller_red

if __name__ == "__main__":
    app = QApplication(sys.argv)
    k_p = 20
    k_i = 5
    world_time = {'day': 0, 'hour': 6, 'min': 0, 'sec': 0} #30 mins before 7 to give setup time



    # --- Core modules ---
    LOOP_INTERVAL_MS = 10  # 1 second in milliseconds
    track_model = track_model_backend.TrackModelBackend()
    green_track_controller = track_controller.TrackController()
    red_track_controller = track_controller_red.TrackControllerRed()

    # --- Track Layout and Schedules ---
    track_layout = load_track_layout("assets/Track_Layout.xlsx")
    schedule_loader = ScheduleLoader(track_layout)
    schedules = schedule_loader.load_from_excel("assets/Train_Scheduling.xlsx")

    # --- CTC Office ---
    ctc = CTC()
    ctc_office = CTCOffice(track_layout, schedules, k_p=k_p, k_i=k_i, loop_int_ms=LOOP_INTERVAL_MS)
    ctc_office.set_ctc(ctc)
    ctc_office.set_track_model(track_model)

    # --- Wire components ---

    ctc.connect_track_controller(green_track_controller)
    ctc.connect_red_track_controller(red_track_controller)

    green_track_controller.set_ctc(ctc)
    green_track_controller.set_track_model(track_model)

    red_track_controller.set_ctc(ctc)
    red_track_controller.set_track_model(track_model)

    track_model.set_track_controller(green_track_controller)

    print("[Main] TrackModel connected to TrackController")


    # Ensure TrackModelBackend updates switches, lights, crossings, and authority
    def sync_backend_with_controller():
        for block_num in range(1, 151):
            # Sync switches
            switch_state = track_controller_red.switch_states[block_num % len(track_controller_red.switch_states)]
            track_model.receive_switch_state(block_num, switch_state)

            # Sync light signals
            light_state = track_controller_red.light_states[block_num % len(track_controller_red.light_states)]
            track_model.receive_light_signal(block_num, light_state)

            # Sync crossings
            crossing_state = track_controller_red.crossing_states[block_num % len(track_controller_red.crossing_states)]
            track_model.receive_crossing_state(block_num, crossing_state)

            # Sync block authority
            authority = track_controller_red.get_block_authority()[block_num - 1]
            track_model.receive_block_authority(block_num, authority)

        # Update GUI state
        track_model.gui.update_gui_display()
        print("[Main] Backend synced with Track Controller")

    # --- GUIs ---
    window = track_gui_and_testbench_unified.UnifiedTrackUI(backend=track_model)
    window.show()

    # green_tb = testbench_track_controller.TestBench(ctc, track_model)
    # green_tb.show()

    ctc_gui = CTCGUI(
        ctc=ctc,
        ctc_office=ctc_office,
        track_layout=track_layout,
        schedule_loader=schedule_loader,
        track_controller=green_track_controller
    )
    ctc_gui.ctc.red_track_controller = red_track_controller
    ctc_gui.show()

    green_track_controller.show()
    red_track_controller.show()

    # --- World update loop ---
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
        ctc_office.launch_pending_trains(current_minutes)

        # Call update functions on each component.
        ctc_gui.update_all()
        green_track_controller.update()
        red_track_controller.update()
        track_model.update()
        if len(track_model.blocks) > 0: # Update train models only if blocks exist
            ctc_office.update_all_trains(world_time, delta_t=1)

        # Update the world clock display on the CTC UI.
        ctc_gui.update_world_clock(world_time)



    # Use QTimer to control the update frequency
    update_timer = QTimer()
    update_timer.timeout.connect(update_world)
    update_timer.start(LOOP_INTERVAL_MS) # Update every 1 second

    sys.exit(app.exec())

