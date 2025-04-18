import sys
from typing import List, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel

import track_model.TrackModelBackend as TrackModelBackend
import track_model.track_gui_and_testbench_unified as track_gui_and_testbench_unified
import track_controller.testbench_track_controller as testbench_track_controller
from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel

# CTC (from ctc.py)
class CTC:
    def __init__(self):
        # Read-only from Track Controller.
        self.block_occupancy = [False] * 150
        self.switch_states = [False] * 6
        self.light_states = [False] * 6
        self.crossing_states = [False] * 2

        # Each block's authority is represented as a 10-bit boolean array.
        self.block_authority = [[False] * 10 for _ in range(150)]
        self.maintenance = [False] * 150

        # Stop signals (10-bit arrays for each block).
        self.stop_signals = [False] * 150

        self.track_controller = None

    def connect_track_controller(self, track_controller):
        self.track_controller = track_controller
        if self.track_controller:
            self.block_occupancy = self.track_controller.get_block_occupancy().copy()
            self.switch_states = self.track_controller.get_switch_state().copy()
            self.light_states = self.track_controller.get_light_state().copy()
            self.crossing_states = self.track_controller.get_crossing_state().copy()

    def send_to_track_controller(self):
        if self.track_controller:
            self.track_controller.receive_authority(self.block_authority.copy())
            self.track_controller.receive_maintenance(self.maintenance.copy())

    def get_block_authority(self):
        return self.block_authority.copy()

    def get_maintenance_status(self):
        return self.maintenance.copy()

    def get_block_occupancy(self):
        return self.block_occupancy.copy()

    def get_stop_signals(self):
        return self.stop_signals.copy()


# Station map (from station_map.py)
STATION_BLOCKS = {
    'Green Line': {
        'PIONEER': 2,
        'EDGEBROOK': 9,
        'WHITED': 22,
        'SOUTH BANK': 31,
        'CENTRAL': 39,
        'INGLEWOOD': 48,
        'OVERBROOK': 57,
        'GLENBURY': 65,
        'DORMONT': 73,
        'MT LEBANON': 77,
        'POPLAR': 88,
        'CASTLE SHANNON': 96,
        'DORMONT2': 105,
        'GLENBURY2': 114,
        'OVERBROOK2': 123,
        'INGLEWOOD2': 132,
        'CENTRAL2': 141
    },
    'BLOCK_TO_STATION': {
        2: 'PIONEER',
        9: 'EDGEBROOK',
        22: 'WHITED',
        31: 'SOUTH BANK',
        39: 'CENTRAL',
        48: 'INGLEWOOD',
        57: 'OVERBROOK',
        65: 'GLENBURY',
        73: 'DORMONT',
        77: 'MT LEBANON',
        88: 'POPLAR',
        96: 'CASTLE SHANNON',
        105: 'DORMONT2',
        114: 'GLENBURY2',
        123: 'OVERBROOK2',
        132: 'INGLEWOOD2',
        141: 'CENTRAL2'
    }
}


# Schedule loader (from schedule_loader.py)
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
import re
from typing import Dict


@dataclass
class ScheduleEntry:
    train_id: int
    stops: list
    line: str
    departure_time: int  # in minutes from midnight (departure_time = first expected arrival - 30 minutes)

class ScheduleLoader:
    def __init__(self, track_layout):
        self.track_layout = track_layout
        self.station_map = self._build_station_map()
        self.green_yard_exit = 62
        self.green_yard_entrance = 58

    def _build_station_map(self) -> dict:
        station_map = {}
        for line, blocks in self.track_layout.items():
            line_map = {}
            for blk in blocks:
                infra = blk.get('infrastructure', '').upper()
                if 'STATION' in infra:
                    match = re.search(r'STATION[:\s]+([^;]+)', infra)
                    if match:
                        name = match.group(1).strip().upper()
                        line_map[name] = blk['block_number']
            station_map[line] = line_map
        return station_map

    def load_from_excel(self, path: str) -> Dict[str, list]:
        schedules = {'Green Line': [], 'Red Line': []}
        for line in ['Green Line', 'Red Line']:
            sheet_name = f"{line} Scheduling"
            try:
                df = pd.read_excel(path, sheet_name=sheet_name, usecols=['Train ID', 'Stops', 'expected_arrival_times'])
                df = df.dropna(subset=['Stops'])
            except Exception as e:
                print(e)
                continue

            line_schedules = []
            for idx, row in df.iterrows():
                try:
                    entry = self._parse_row(row, line, idx + 2)
                    line_schedules.append(entry)
                except Exception as e:
                    print(f"Row {idx+2} parsing error: {e}")
                    pass
            schedules[line] = line_schedules
        return schedules

    def _parse_row(self, row, line: str, row_num: int) -> ScheduleEntry:
        train_id = int(row['Train ID'])
        stops_str = str(row['Stops']).strip()
        times_str = str(row['expected_arrival_times']) if pd.notna(row['expected_arrival_times']) else ''

        stop_list = [s.strip() for s in re.split(r',', stops_str) if s.strip()]
        time_list = [t.strip() for t in re.split(r',', times_str) if t.strip()]

        if len(stop_list) != len(time_list):
            raise ValueError(f"{len(stop_list)} stops but {len(time_list)} times")

        stops = []
        for i, (station, time_str) in enumerate(zip(stop_list, time_list)):
            st_up = station.upper()
            time_obj = datetime.strptime(time_str, '%H:%M').time()

            # Handle YARD as block 58
            if st_up == 'YARD':
                block = self.green_yard_entrance  # 58
            else:
                try:
                    block = int(st_up)
                    if not any(blk['block_number'] == block for blk in self.track_layout[line]):
                        raise ValueError(f"Invalid block {block} on {line}")
                except ValueError:
                    block = self.station_map[line].get(st_up)
                    if not block:
                        valid_stations = ', '.join(self.station_map[line].keys())
                        raise ValueError(f"Unknown station '{station}'. Valid: {valid_stations}")
            stops.append({'block': block, 'time': time_obj})

        # departure_time = first expected arrival time - 30.
        first_time_obj = datetime.strptime(time_list[0], '%H:%M').time()
        first_minutes = first_time_obj.hour * 60 + first_time_obj.minute
        departure_time = max(0, first_minutes - 30)

        return ScheduleEntry(train_id=train_id, stops=stops, line=line, departure_time=departure_time)


# Track loader (from track_loader.py)
def load_track_layout(path: str) -> Dict[str, List[dict]]:
    import pandas as pd
    from typing import Dict, List

    COLUMN_MAP = {
        'block number': 'block_number',
        'block length (m)': 'block_length',
        'speed limit (km/hr)': 'speed_limit',
        'infrastructure': 'infrastructure'
    }

    def process_sheet(sheet: str) -> List[dict]:
        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                engine='openpyxl'
            ).rename(columns=str.lower).rename(columns=COLUMN_MAP)

            # Clean and validate data
            df = df.dropna(subset=['block_number'])
            df['block_number'] = pd.to_numeric(df['block_number'], errors='coerce').dropna().astype(int)

            valid_blocks = []
            for _, row in df.iterrows():
                try:
                    block_data = {
                        'line': sheet.strip(),
                        'block_number': int(row['block_number']),
                        'block_length': float(row['block_length']),
                        'speed_limit': int(row['speed_limit']),
                        'infrastructure': str(row.get('infrastructure', '')).strip().upper()
                    }
                    if 1 <= block_data['block_number'] <= 150:
                        valid_blocks.append(block_data)
                except Exception:
                    pass

            return valid_blocks

        except Exception as e:
            print(f"track loader exception: {e}")
            return []

    return {
        'Red Line': process_sheet('Red Line'),
        'Green Line': process_sheet('Green Line')
    }


# ctc_office.py
class TrackBlock:
    def __init__(self, block_number: int, block_length: float):
        self.block_number = block_number
        self.block_length = block_length
        self.next = None  # pointer to next block in route

class Train:
    def __init__(self, train_id: int, route_head: TrackBlock, scheduled_stops: List[int] = None,
                 current_block: TrackBlock = None, next_stop_index: int = 0, authority_meters: float = 0.0,
                 last_stop_passed: int = None):
        self.train_id = train_id  # unique train id
        self.route_head = route_head  # head node of L.L. representing route
        self.scheduled_stops = scheduled_stops if scheduled_stops is not None else []  # list of block nums to stop
        self.current_block = current_block  # current block train is on
        self.next_stop_index = next_stop_index  # index into scheduled_stops indicating next stop
        self.authority_meters = authority_meters  # remaining distance before reaching next stop
        self.last_stop_passed = last_stop_passed  # block num of most recent scheduled stop passed
        self.wait_for = 50  # num steps to wait if reached station

    @property
    def route_blocks(self) -> List[int]:
        blocks = []  # init empty list to hold block nums
        node = self.route_head  # start at head of L.L. representing route
        while node:
            blocks.append(node.block_number)  # add block num of current node to list
            node = node.next  # move to next node in L.L.
        return blocks  # return list of block nums that form the route

    @property
    def current_block_index(self) -> int:
        index = 0  # init index counter
        node = self.route_head  # start at head
        while node:
            if node == self.current_block:
                return index
            node = node.next
            index += 1
        return -1  # if current block not found (should not happen)

class CTCOffice:
    # default green line route (note: this list may include reversals)
    green_line_route = [
        62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
        81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
        85, 84, 83, 82, 81, 80, 79, 78, 77, 101, 102, 103, 104, 105, 106, 107, 108, 109,
        110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
        126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141,
        142, 143, 144, 145, 146, 147, 148, 149, 150, 28, 27, 26, 25, 24, 23, 22, 21,
        20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
        35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
        55, 56, 57, 58
    ]

    def __init__(self, track_layout: Dict[str, List[dict]], schedules: Dict[str, List],
                 k_p=1000, k_i=100, loop_int_ms=1000):
        self.track_layout = track_layout  # save track layout
        self.schedules = schedules  # save schedule
        self.ctc: CTC = None  # set later
        self.active_trains: List[Train] = []  # list of active trains
        self.real_active_trains = []
        # Dict mapping block numbers to block data for the Green Line
        self.green_blocks = {b['block_number']: b for b in track_layout.get('Green Line', [])}
        self.track_model = None
        self.k_p = k_p
        self.k_i = k_i
        self.loop_int_ms = loop_int_ms
        self.stopping_time = 20 * (1000 / loop_int_ms)
        self.pending_trains: List[ScheduleEntry] = [] #pending trains for dispatch


        from PyQt6.QtWidgets import QWidget  # already imported above
        self.TrainUIToggle = TrainUIToggle(self.real_active_trains)
        self.TrainUIToggle.show()

    def set_ctc(self, ctc: CTC):
        self.ctc = ctc  # assign ctc

    def build_linked_route(self, route_numbers: List[int]) -> TrackBlock:
        head = None  # first block in route
        curr = None  # pointer to current end of linked list
        # Iterate through each block number in the route
        for num in route_numbers:
            length = self.green_blocks[num]['block_length'] if num in self.green_blocks else 0.0
            node = TrackBlock(num, length)
            if head is None:
                head = node
                curr = node
            else:
                curr.next = node
                curr = node
        return head

    #instead of immediate dispatch add to pending
    def add_pending_train(self, schedule_entry: ScheduleEntry):
        self.pending_trains.append(schedule_entry)
        # sort pending trains by departure time
        self.pending_trains.sort(key=lambda x: x.departure_time)

    #launch pending trains whose departure time is reached.
    def launch_pending_trains(self, current_minutes: int):
        while self.pending_trains and self.pending_trains[0].departure_time <= current_minutes:
            entry = self.pending_trains.pop(0)
            self._launch_train(entry)

    def _launch_train(self, schedule_entry: ScheduleEntry):
        stops = [item['block'] for item in schedule_entry.stops]
        current_position = 64  # start from yard exit on Green Line
        route_numbers = []
        for stop_block in stops:
            if stop_block not in self.green_line_route:
                print(f"Stop block {stop_block} not in green_line_route. Skipping.")
                return
            try:
                start_index = self.green_line_route.index(current_position)
                target_index = self.green_line_route.index(stop_block)
            except ValueError:
                print(f"Error: {current_position} or {stop_block} not found in route array.")
                return
            if target_index >= start_index:
                segment = self.green_line_route[start_index:target_index + 1]
            else:
                segment = self.green_line_route[target_index:start_index + 1][::-1]
            if route_numbers and route_numbers[-1] == current_position:
                route_numbers += segment[1:]
            else:
                route_numbers += segment
            current_position = stop_block
        print("route_numbers: ", route_numbers)
        route_head = self.build_linked_route(route_numbers)
        train = Train(
            train_id=schedule_entry.train_id,
            route_head=route_head,
            scheduled_stops=stops,
            current_block=route_head,
            next_stop_index=0
        )
        train_model = TrainModel(train_number=schedule_entry.train_id, LOOP_INTERVAL_MS=self.loop_int_ms,
                                 k_p=self.k_p, k_i=self.k_i)
        train_model.add_classes(self.track_model)
        self.update_authority(train)
        self.active_trains.append(train)
        self.real_active_trains.append(train_model)
        self.TrainUIToggle.update_ui()
        print(f"Dispatched Train {train.train_id} with route {route_numbers}")

    # Instead of immediately scheduling a train when loaded, add it to pending.
    def schedule_train(self, line: str, train_index: int):
        try:
            schedule = self.schedules[line][train_index]
        except (KeyError, IndexError):
            return
        self.add_pending_train(schedule)
        print(f"Train {schedule.train_id} scheduled with departure time (minutes): {schedule.departure_time}")

    def schedule_manual_train(self, line: str, train_id: int, stops: List[int]):
        if line.lower().strip() != "green line":
            print("red line not working")
            return
        yard_exit = 64
        yard_entrance = 58
        if not stops or stops[-1] != yard_entrance:
            stops.append(yard_entrance)
        route_numbers = []
        current_position = yard_exit
        for stop_block in stops:
            try:
                start_index = self.green_line_route.index(current_position)
                target_index = self.green_line_route.index(stop_block)
            except ValueError:
                print(f"Error: {current_position} or {stop_block} not found in green_line_route.")
                return
            if target_index >= start_index:
                segment = self.green_line_route[start_index:target_index + 1]
            else:
                segment = self.green_line_route[target_index:start_index + 1][::-1]
            if route_numbers and route_numbers[-1] == current_position:
                route_numbers += segment[1:]
            else:
                route_numbers += segment
            current_position = stop_block
        route_head = self.build_linked_route(route_numbers)
        existing_train = None
        for t in self.active_trains:
            if t.train_id == train_id:
                existing_train = t
                break
        if existing_train is not None:
            existing_train.route_head = route_head
            existing_train.scheduled_stops = stops
            existing_train.next_stop_index = 0
            self.update_authority(existing_train)
            print(f"Manually updated Train {train_id} with new route: {route_numbers}")
        else:
            new_train = Train(
                train_id=train_id,
                route_head=route_head,
                scheduled_stops=stops,
                current_block=route_head,
                next_stop_index=0
            )
            train_model = TrainModel(train_number=train_id, LOOP_INTERVAL_MS=self.loop_int_ms, k_p=self.k_p, k_i=self.k_i)
            train_model.add_classes(self.track_model)
            self.update_authority(new_train)
            self.active_trains.append(new_train)
            self.real_active_trains.append(train_model)
            self.TrainUIToggle.update_ui()
            print(f"Manually scheduled Train {train_id} with route: {route_numbers}")


    def update_authority(self, train: Train):
        print(f"Calculating authority for Train {train.train_id}:")
        # Check if no more stops remain.
        if train.next_stop_index >= len(train.scheduled_stops):
            train.authority_meters = 0.0
            print("No next stop; authority = 0.0")
            return

        # If the target block is reached exactly, and it is a station, give half block length.
        target_stop = train.scheduled_stops[train.next_stop_index]
        if train.current_block and train.current_block.block_number == target_stop:
            if target_stop in STATION_BLOCKS['BLOCK_TO_STATION']:
                train.authority_meters = train.current_block.block_length / 2.0
                print(f"Train {train.train_id} is at station {target_stop}; setting authority to half block length = {train.authority_meters} m")
            else:
                train.authority_meters = 0.0
                print(f"Train {train.train_id} is at target {target_stop}; authority = 0.0")
            return

        total = 0.0  # initialize total allowed distance
        node = train.current_block  # starting from current position
        # if train just passed a stop, count half of current block length
        start_in_second_half = (train.last_stop_passed == node.block_number) if node else False

        # Sum block lengths until reaching the target stop.
        while node and node.block_number != target_stop:
            if start_in_second_half:
                total += node.block_length / 2.0
                start_in_second_half = False
            else:
                total += node.block_length
            node = node.next
        # If reached target, add half length if station; else full length.
        if node:
            if target_stop in STATION_BLOCKS['BLOCK_TO_STATION']:
                total += node.block_length / 2.0
            else:
                total += node.block_length
        # Do not add target block’s full length so that authority becomes zero upon arrival.
        train.authority_meters = total
        print(f"Authority from block {train.current_block.block_number if train.current_block else '??'} to {target_stop} = {total} m")

    def update_train_positions(self):
        if not self.ctc:
            return
        # Create list of blocks currently occupied (1-indexed).
        occupied_blocks = [i + 1 for i, occ in enumerate(self.ctc.get_block_occupancy()) if occ]
        for train in self.active_trains[:]:
            if train.current_block is None:
                continue
            curr_num = train.current_block.block_number
            # If train is holding at a stop, decrement its timer.
            if hasattr(train, 'stop_timer'):
                train.stop_timer -= 1
                if train.stop_timer <= 0:
                    print(f"Train {train.train_id} hold at stop complete.")
                    del train.stop_timer
                    train.last_stop_passed = curr_num
                    train.next_stop_index += 1
                    self.update_authority(train)
                continue
            # Delete train if it has reached the YARD (block 58).
            if curr_num == 58:
                print(f"Train {train.train_id} has reached YARD. Deleting train.")
                self.active_trains.remove(train)
                for tm in self.real_active_trains:
                    if tm.train_number == train.train_id:
                        tm.__del__()
                        self.real_active_trains.remove(tm)
                        break
                continue
            # If current block is still occupied, do nothing.
            if curr_num in occupied_blocks:
                continue
            # Check the next block in route.
            nxt = train.current_block.next
            if not nxt:
                print(f"Train {train.train_id} finished route at block {curr_num}.")
                continue
            nxt_num = nxt.block_number
            # If next block is occupied, assume train moved.
            if nxt_num in occupied_blocks:
                train.current_block = nxt
                self.update_authority(train)
                if nxt_num == 58:
                    print(f"Train {train.train_id} arriving at YARD. Starting final stop.")
                    if not hasattr(train, 'stop_timer'):
                        train.stop_timer = self.stopping_time
                elif train.next_stop_index < len(train.scheduled_stops) and nxt_num == train.scheduled_stops[train.next_stop_index]:
                    if not hasattr(train, 'stop_timer'):
                        train.stop_timer = self.stopping_time
                        print(f"Train {train.train_id} arrived at stop {nxt_num}. Holding for 10 seconds.")

    def update_maintenance(self, maintenance_list):
        if self.ctc:
            self.ctc.maintenance = maintenance_list.copy()

    def update(self):
        if not self.ctc:
            return
        # Update stop signals from the track controller.
        self.ctc.stop_signals = self.ctc.track_controller.stop_states
        # Clear authority for all blocks.
        self.ctc.block_authority = [[False] * 10 for _ in range(150)]
        max_auth = 1023  # maximum value of 10 bits
        update_window = 2  # number of blocks to update ahead
        # For each active train, update authority for next few blocks.
        for train in self.active_trains:
            remaining = train.authority_meters
            node = train.current_block
            window_count = 0
            while remaining > 0 and node and window_count < update_window:
                auth_value = min(int(remaining), max_auth)
                bits = [(auth_value >> i) & 1 == 1 for i in range(9, -1, -1)]
                index = node.block_number - 1
                if 0 <= index < 150:
                    self.ctc.block_authority[index] = bits
                remaining -= node.block_length
                node = node.next
                window_count += 1
        # Override authority for maintenance blocks.
        for i, m in enumerate(self.ctc.maintenance):
            if m:
                self.ctc.block_authority[i] = [False] * 10
        # Overwrite authority for blocks with stop signals.
        for i, stop in enumerate(self.ctc.get_stop_signals()):
            if stop:
                self.ctc.block_authority[i] = [False] * 10

        self.ctc.send_to_track_controller()
        self.update_train_positions()

    def update_all_trains(self, world_time, delta_t=1):
        for train in self.real_active_trains:
            train.update_train(world_time, delta_t)
            delta_one_sec = delta_t
            while delta_one_sec < 1:
                train.update_train_no_signal_pickup(world_time, delta_t)
                delta_one_sec += delta_t

    def update_track_states(self):
        mapping = [
            ("Crossing 1", self.ctc.crossing_states[18]),
            ("Crossing 2", self.ctc.crossing_states[107]),
            ("Switch 1", self.ctc.switch_states[11]),
            ("Light 1", self.ctc.light_states[0]),
            ("Switch 2", self.ctc.switch_states[27]),
            ("Light 2", self.ctc.light_states[149]),
            ("Switch 3", self.ctc.switch_states[57]),
            ("Light 3", self.ctc.light_states[60]),
            ("Switch 4", self.ctc.switch_states[61]),
            ("Light 4", self.ctc.light_states[59]),
            ("Switch 5", self.ctc.switch_states[75]),
            ("Light 5", self.ctc.light_states[74]),
            ("Switch 6", self.ctc.switch_states[85]),
            ("Light 6", self.ctc.light_states[98])
        ]
        for row, (desc, state) in enumerate(mapping):
            item = QTableWidgetItem("Active" if state else "Inactive")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates.setItem(row, 0, item)

    def update_system_analysis(self):
        dummy_data = {
            0: ["100", "1", "1.0%"],
            1: ["120", "2", "1.6%"]
        }
        for row in range(2):
            for col in range(3):
                item = QTableWidgetItem(dummy_data[row][col])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tableSystemAnalysis.setItem(row, col, item)

    def get_block_authority(self):
        return self.ctc.get_block_authority()

    def set_track_model(self, track_model):
        self.track_model = track_model


class TrainUIToggle(QWidget):
    def __init__(self, real_active_trains):
        super().__init__()
        self.real_active_trains = real_active_trains
        self.checkboxes = {}  # store checkboxes for each train
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Train UI Toggle")
        self.setGeometry(0, 0, 200, 300)
        self.layout = QVBoxLayout()
        title_label = QLabel("Toggle Train UIs")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title_label)
        toggle_all_button = QPushButton("Toggle All UIs")
        toggle_all_button.clicked.connect(self.toggle_all_uis)
        self.layout.addWidget(toggle_all_button)
        self.train_checkbox_layout = QVBoxLayout()
        self.layout.addLayout(self.train_checkbox_layout)
        self.setLayout(self.layout)
        self.update_ui()

    def update_ui(self):
        for i in reversed(range(self.train_checkbox_layout.count())):
            widget = self.train_checkbox_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.checkboxes = {}
        for train_model in self.real_active_trains:
            checkbox = QCheckBox(f"Train {train_model.train_number}")
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.toggle_train_ui)
            self.train_checkbox_layout.addWidget(checkbox)
            self.checkboxes[train_model.train_number] = checkbox

    def toggle_train_ui(self, state):
        for train_model in self.real_active_trains:
            checkbox = self.checkboxes.get(train_model.train_number)
            if checkbox and checkbox.isChecked():
                if train_model.train_gui.isHidden():
                    train_model.train_gui.show()
                if train_model.train_controller_gui.isHidden():
                    train_model.train_controller_gui.show()
            elif checkbox:
                train_model.train_gui.hide()
                train_model.train_controller_gui.hide()

    def toggle_all_uis(self):
        all_checked = all(checkbox.isChecked() for checkbox in self.checkboxes.values())
        new_state = not all_checked
        for train_model in self.real_active_trains:
            checkbox = self.checkboxes.get(train_model.train_number)
            if checkbox:
                checkbox.setChecked(new_state)
