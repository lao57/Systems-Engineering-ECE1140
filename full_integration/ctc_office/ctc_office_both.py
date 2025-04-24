import sys
from typing import List, Dict
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel
import track_controller.testbench_track_controller as testbench_track_controller
from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel


class CTC:
    def __init__(self):

        # Read-only from Track Controller.
        self.block_occupancy = [False] * 150
        self.switch_states = [False] * 6
        self.light_states = [False] * 6
        self.crossing_states = [False] * 2

        # Read-only from Track Controller Red.
        self.block_occupancy_red = [False] * 76
        self.red_switch_states = [False] * 7
        self.red_light_states = [False] * 4
        self.red_crossing_states = [False] * 2

        #Send to Track Controller.
        self.block_authority = [[False] * 10 for _ in range(150)] # Each block's authority is represented as a 10-bit boolean array.
        self.maintenance = [False] * 150

        # Send to Track Controller Red.
        self.red_block_authority = [[False] * 10 for _ in range(76)]
        self.maintenance_red = [False] * 76

        # Stop signals (10-bit arrays for each block).
        self.stop_signals = [False] * 150
        self.red_stop_signals = [False] * 76

        self.track_controller = None
        self.red_track_controller = None


    def connect_track_controller(self, track_controller):
        self.track_controller = track_controller
        if self.track_controller:
            self.block_occupancy = self.track_controller.get_block_occupancy().copy()
            self.switch_states = self.track_controller.get_switch_state().copy()
            self.light_states = self.track_controller.get_light_state().copy()
            self.crossing_states = self.track_controller.get_crossing_state().copy()


    def connect_red_track_controller(self, red_track_controller):
        self.red_track_controller = red_track_controller
        if self.red_track_controller:
            self.block_occupancy_red = self.red_track_controller.get_block_occupancy().copy()
            self.red_switch_states = red_track_controller.get_switch_state().copy()
            self.red_light_states = red_track_controller.get_light_state().copy()
            self.red_crossing_states = red_track_controller.get_crossing_state().copy()

    def send_to_track_controller(self):
        if self.track_controller:
            self.track_controller.receive_authority(self.block_authority.copy())
            self.track_controller.receive_maintenance(self.maintenance.copy())

        if self.red_track_controller:
            self.red_track_controller.receive_authority(self.red_block_authority.copy())
            self.red_track_controller.receive_maintenance(self.maintenance_red.copy())

    def get_block_authority(self):
        return self.block_authority.copy()

    def red_get_block_authority(self):
        return self.red_block_authority.copy()

    def get_maintenance_status(self):
        return self.maintenance.copy()

    def red_get_maintenance_status(self):
        return self.maintenance_red.copy()

    def get_block_occupancy(self):
        return self.block_occupancy.copy()

    def red_get_block_occupancy(self):
        return self.block_occupancy_red.copy()

    def get_stop_signals(self):
        return self.stop_signals.copy()

    def red_get_stop_signals(self):
        return self.red_stop_signals.copy()



STATION_BLOCKS_GREEN = {
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
        'DORMONT': 105,
        'GLENBURY': 114,
        'OVERBROOK': 123,
        'INGLEWOOD': 132,
        'CENTRAL': 141
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
        105: 'DORMONT',
        114: 'GLENBURY',
        123: 'OVERBROOK',
        132: 'INGLEWOOD',
        141: 'CENTRAL'
    }
}

STATION_BLOCKS_RED = {
    "Red Line": {
        "SHADYSIDE": 7,
        "HERRON AVE": 16,
        "SWISSVILLE": 21,
        "PENN STATION": 25,
        "STEEL PLAZA": 35,
        "FIRST AVE": 45,
        "STATION SQUARE": 48,
        "SOUTH HILLS JUNCTION": 60
    },
    "BLOCK_TO_STATION": {
        7: "SHADYSIDE",
        16: "HERRON AVE",
        21: "SWISSVILLE",
        25: "PENN STATION",
        35: "STEEL PLAZA",
        45: "FIRST AVE",
        48: "STATION SQUARE",
        60: "SOUTH HILLS JUNCTION"
    }
}


@dataclass
class ScheduleEntry:
    train_id: int   #unique id for train
    stops: list     #list of stop dictionaries, each with a 'block' and 'time' key
    line: str       #which line train is on
    departure_time: int  # in minutes from midnight (departure_time = first expected arrival - 30 minutes)


#class for loading and parsing train files in excel and mapping station names to blocks.
class ScheduleLoader:
    def __init__(self, track_layout):
        self.track_layout = track_layout
        self.station_map = self.build_station_map() # Maps station names to block numbers
        self.green_yard_exit = 62
        self.green_yard_entrance = 58
        self.red_yard_exit = 9
        self.red_yard_entrance = 10

    #helper to create a mapping of station names to block numbers for each line
    def build_station_map(self) -> dict:
        station_map = {} #dict to store final result

        #iterate through track layout
        for line, blocks in self.track_layout.items():
            line_map = {} #temp mapping for one line

            #each blk has data for blocks: length, infrastructure, etc.
            for blk in blocks:
                infra = blk.get('infrastructure', '').upper() #get infrastructure string for block
                #only care if it is a station
                if 'STATION' in infra:
                    # looks for something like "STATION: PIONEER" or "STATION PIONEER" and captures "PIONEER"
                    match = re.search(r'STATION[:\s]+([^;]+)', infra)
                    if match:

                        name = match.group(1).strip().upper() #clean station name
                        line_map[name] = blk['block_number'] #map station name to block number
            station_map[line] = line_map #once all blocks checked save mapping
        return station_map #return a nested dictionary including both lines

    #loads train schedules and returns dict of ScheduleEntry lists
    def load_from_excel(self, path: str) -> Dict[str, list]:
        schedules = {'Green Line': [], 'Red Line': []} #init empty schedule dict for both
        for line in ['Green Line', 'Red Line']:
            sheet_name = f"{line} Scheduling"
            try:
                #read excel sheet and only keep needed comments
                df = pd.read_excel(path, sheet_name=sheet_name,
                                   usecols=['Train ID', 'Stops', 'expected_arrival_times'])
                df = df.dropna(subset=['Stops']) #drop rows with no stops
            except Exception as e:
                print(e)
                continue

            line_schedules = []

            #parse each row into a ScheduleEntry
            for idx, row in df.iterrows():
                try:
                    entry = self.parse_row(row, line, idx + 2)
                    line_schedules.append(entry)
                except Exception as e:
                    print(f"Row {idx + 2} parsing error: {e}")
                    pass
            schedules[line] = line_schedules  # store the parsed schedules
        return schedules

    def parse_row(self, row, line: str, row_num: int) -> ScheduleEntry:
        train_id = int(row['Train ID']) #get train id
        stops_str = str(row['Stops']).strip() #get stops
        times_str = str(row['expected_arrival_times']) if pd.notna(row['expected_arrival_times']) else '' #get arrival times

        stop_list = [s.strip() for s in re.split(r',', stops_str) if s.strip()]
        time_list = [t.strip() for t in re.split(r',', times_str) if t.strip()]

        #make sure # of stops = # of arrival times
        if len(stop_list) != len(time_list):
            raise ValueError(f"{len(stop_list)} stops but {len(time_list)} times")

        stops = []

        # convert stop names and times into block + time dicts
        for station, time_str in zip(stop_list, time_list):
            st_up = station.upper()
            time_obj = datetime.strptime(time_str, '%H:%M').time()

            # handle "YARD"
            if st_up == 'YARD':
                block = self.red_yard_entrance if line.lower().strip() == "red line" else self.green_yard_entrance
            else:
                try:
                    #interpret station as block num
                    block = int(st_up)
                    if not any(blk['block_number'] == block for blk in self.track_layout[line]):
                        raise ValueError(f"Invalid block {block} on {line}")
                except ValueError:
                    block = self.station_map[line].get(st_up)
                    if not block:
                        valid_stations = ', '.join(self.station_map[line].keys())
                        raise ValueError(f"Unknown station '{station}'. Valid: {valid_stations}")
            stops.append({'block': block, 'time': time_obj})

        # departure_time = first expected arrival time - 30
        first_time_obj = datetime.strptime(time_list[0], '%H:%M').time()
        first_minutes = first_time_obj.hour * 60 + first_time_obj.minute
        departure_time = max(0, first_minutes - 30)

        return ScheduleEntry(train_id=train_id, stops=stops, line=line, departure_time=departure_time)



def load_track_layout(path: str) -> Dict[str, List[dict]]:
    #mapping of column names from excel to internal field names
    COLUMN_MAP = {
        'block number': 'block_number',
        'block length (m)': 'block_length',
        'speed limit (km/hr)': 'speed_limit',
        'infrastructure': 'infrastructure'
    }
    #helper to process a sheet
    def process_sheet(sheet: str) -> List[dict]:
        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                engine='openpyxl'
            ).rename(columns=str.lower).rename(columns=COLUMN_MAP)

            # drop rows without a block number and make sure they are ints
            df = df.dropna(subset=['block_number'])
            df['block_number'] = pd.to_numeric(df['block_number'], errors='coerce').dropna().astype(int)

            valid_blocks = []
            # iterate over rows and build a dictionary for each valid block
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
                # skip any rows with missing stuff
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

class TrackBlock:
    def __init__(self, block_number: int, block_length: float):
        self.block_number = block_number
        self.block_length = block_length
        self.next = None  # pointer to next block in route
        self.prev = None  # pointer to previous block in route

class Train:
    def __init__(self, train_id: int, route_head: TrackBlock, scheduled_stops: List[int] = None,
                 current_block: TrackBlock = None, next_stop_index: int = 0, authority_meters: float = 0.0,
                 last_stop_passed: int = None, line_name: str = "Green Line"):
        self.train_id = train_id  # unique train id
        self.route_head = route_head # head node of L.L. representing route
        self.scheduled_stops = scheduled_stops if scheduled_stops is not None else [] # list of block nums to stop
        self.current_block = current_block  # current block train is on
        self.next_stop_index = next_stop_index  # index into scheduled_stops indicating next stop
        self.authority_meters = authority_meters  # remaining distance before reaching next stop
        self.last_stop_passed = last_stop_passed  # block num of most recent scheduled stop passed
        self.wait_for = 50  # num steps to wait if reached station
        self.line_name = line_name #which line

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
    # default green line route
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
    #default red line route
    red_line_route = [

        9, 8, 7, 6, 5, 4, 3, 2, 1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
        27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
        45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
        52, 51, 50, 49, 48, 47, 46, 45, 44, 67, 68, 69, 70, 71, 38, 37, 36, 35, 34, 33, 72,
        73, 74, 75, 76, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10
    ]

    def __init__(self, track_layout: Dict[str, List[dict]], schedules: Dict[str, List], k_p=1000, k_i=100,
                 loop_int_ms=1000):
        self.track_layout = track_layout #save track layout
        self.schedules = schedules #save schedule
        self.ctc: CTC = None
        self.active_trains: List[Train] = [] #list of active trains
        self.real_active_trains = []
        self.green_blocks = {b['block_number']: b for b in track_layout.get('Green Line', [])} # Dict mapping block numbers to block data for the Green Line
        self.red_blocks = {b['block_number']: b for b in track_layout.get('Red Line', [])} # Dict mapping block numbers to block data for the Red Line
        self.track_model = None
        self.k_p = k_p
        self.k_i = k_i
        self.loop_int_ms = loop_int_ms
        self.stopping_time = 20 * (1000 / loop_int_ms)
        self.pending_trains: List[ScheduleEntry] = [] #pending trains for dispatch
        self.zero_authority_green = [False] * 150 #zero auth for all blocks on green
        self.zero_authority_red = [False] * 76 #zero auth for all blocks on red
        self.TrainUIToggle = TrainUIToggle(self.real_active_trains)
        self.TrainUIToggle.show()
        self.green_trains_finished = 0  # Counts Green Line trains that reach the yard
        self.red_trains_finished = 0  # Counts Red Line trains that reach the yard
        self.tableSystemAnalysis = None  # Will be set by GUI

    def set_ctc(self, ctc: CTC):
        self.ctc = ctc  # assign ctc

    def build_linked_route(self, route_numbers: List[int], line: str) -> TrackBlock:

        #choose block dict based on line
        blocks_dict = self.green_blocks if line.lower().strip() == "green line" else self.red_blocks
        if not route_numbers:
            return None

        # initialize the head of the linked list with the first block
        block_num = route_numbers[0]
        length = blocks_dict[block_num]['block_length'] if block_num in blocks_dict else 0.0
        head = TrackBlock(block_num, length)
        head.prev = None

        # recursively build the rest of the linked list
        head.next = self.recursive_link_helper(route_numbers, 1, blocks_dict)
        # set the back-reference for the second node if it exists
        if head.next:
            head.next.prev = head
        return head # return the head of the linked list

    def recursive_link_helper(self, route_numbers: List[int], index: int, blocks_dict: dict) -> TrackBlock:
        if index >= len(route_numbers):
            return None #base case: end of list
        #get block number and it's length
        block_num = route_numbers[index]
        length = blocks_dict[block_num]['block_length'] if block_num in blocks_dict else 0.0
        node = TrackBlock(block_num, length) # create node for current block
        # recursively create next node and link it
        node.next = self.recursive_link_helper(route_numbers, index + 1, blocks_dict)

        # set the previous pointer of the next node
        if node.next:
            node.next.prev = node

        return node #return current node

    #instead of immediate dispatch add to pending
    def add_pending_train(self, schedule_entry: ScheduleEntry):
        self.pending_trains.append(schedule_entry)
        # sort pending trains by departure time
        self.pending_trains.sort(key=lambda x: x.departure_time)

    #launch pending trains whose departure time is reached.
    def launch_pending_trains(self, current_minutes: int):
        while self.pending_trains and self.pending_trains[0].departure_time <= current_minutes:
            entry = self.pending_trains.pop(0)
            self.launch_train(entry)

    def launch_train(self, schedule_entry: ScheduleEntry):
        stops = [item['block'] for item in schedule_entry.stops]
        #start from correct respective line
        if schedule_entry.line.lower().strip() == "green line":
            route_full = self.green_line_route
            current_position = 64
            blocks_dict = self.green_blocks
        elif schedule_entry.line.lower().strip() == "red line":
            route_full = self.red_line_route
            current_position = 9
            blocks_dict = self.red_blocks
        else:
            print(f"[LaunchTrain] Unknown line: {schedule_entry.line}")
            return

        route_numbers = []
        for stop_block in stops:
            if stop_block not in route_full:
                print(f"Stop block {stop_block} not in {schedule_entry.line} route. Skipping.")
                return
            try:
                start_index = route_full.index(current_position)
                target_index = route_full.index(stop_block)
            except ValueError:
                print(f"Error: {current_position} or {stop_block} not found in route.")
                return

            segment = route_full[start_index:target_index + 1] if target_index >= start_index else route_full[
                                                                                                   target_index:start_index + 1][
                                                                                                   ::-1]
            if route_numbers and route_numbers[-1] == current_position:
                route_numbers += segment[1:]
            else:
                route_numbers += segment
            current_position = stop_block

        print(f"Dispatched Train {schedule_entry.train_id} route: {route_numbers}")
        route_head = self.build_linked_route(route_numbers, schedule_entry.line)
        train = Train(
            train_id=schedule_entry.train_id,
            route_head=route_head,
            scheduled_stops=stops,
            current_block=route_head,
            next_stop_index=0,
            line_name=schedule_entry.line
        )
        train_model = TrainModel(train_number=schedule_entry.train_id, LOOP_INTERVAL_MS=self.loop_int_ms, k_p=self.k_p,
                                 k_i=self.k_i)
        train_model.add_classes(self.track_model)
        self.update_authority(train)
        self.active_trains.append(train)
        self.real_active_trains.append(train_model)
        self.TrainUIToggle.update_ui()

    # Instead of immediately scheduling a train when loaded, add it to pending.
    def schedule_train(self, line: str, train_index: int):
        try:
            schedule = self.schedules[line][train_index]
        except (KeyError, IndexError):
            return
        self.add_pending_train(schedule)
        print(f"Train {schedule.train_id} scheduled with departure time (minutes): {schedule.departure_time}")

    def schedule_manual_train(self, line: str, train_id: int, stops: List[int]):
        line = line.lower().strip()
        if line == "green line":
            yard_exit, yard_entrance = 64, 58
            route_full = self.green_line_route
            blocks_dict = self.green_blocks
        elif line == "red line":
            yard_exit, yard_entrance = 9, 10
            route_full = self.red_line_route
            blocks_dict = self.red_blocks
        else:
            print(f"[ManualSchedule] Unknown line: {line}")
            return

        if not stops or stops[-1] != yard_entrance:
            stops.append(yard_entrance)

        route_numbers = []
        current_position = yard_exit
        for stop_block in stops:
            if stop_block not in route_full:
                print(f"Error: Stop block {stop_block} not in {line} route.")
                return
            try:
                start_index = route_full.index(current_position)
                target_index = route_full.index(stop_block)
            except ValueError:
                print(f"Error: {current_position} or {stop_block} not found in route.")
                return
            segment = route_full[start_index:target_index + 1] if target_index >= start_index else route_full[
                                                                                                   target_index:start_index + 1][
                                                                                                   ::-1]
            if route_numbers and route_numbers[-1] == current_position:
                route_numbers += segment[1:]
            else:
                route_numbers += segment
            current_position = stop_block

        route_head = self.build_linked_route(route_numbers, line)
        existing_train = next((t for t in self.active_trains if t.train_id == train_id), None)
        if existing_train:
            existing_train.route_head = route_head
            existing_train.scheduled_stops = stops
            existing_train.next_stop_index = 0
            self.update_authority(existing_train)
            print(f"Updated Train {train_id} with new route: {route_numbers}")
        else:
            new_train = Train(train_id=train_id, route_head=route_head, scheduled_stops=stops, current_block=route_head,
                              next_stop_index=0, line_name=line)
            train_model = TrainModel(train_number=train_id, LOOP_INTERVAL_MS=self.loop_int_ms, k_p=self.k_p,
                                     k_i=self.k_i)
            train_model.add_classes(self.track_model)
            self.update_authority(new_train)
            self.active_trains.append(new_train)
            self.real_active_trains.append(train_model)
            self.TrainUIToggle.update_ui()
            print(f"Manually scheduled Train {train_id} on {line} with route: {route_numbers}")

    def update_authority(self, train: Train):
        print(f"Calculating authority for Train {train.train_id}:")
        if train.next_stop_index >= len(train.scheduled_stops):
            train.authority_meters = 0.0
            print("No next stop; authority = 0.0")
            return

        target_stop = train.scheduled_stops[train.next_stop_index]
        node = train.current_block

        is_green = train.line_name.lower().strip() == "green line"
        station_map = STATION_BLOCKS_GREEN["BLOCK_TO_STATION"] if is_green else STATION_BLOCKS_RED["BLOCK_TO_STATION"]
        zero_auth = self.zero_authority_green if is_green else self.zero_authority_red
        block_occupancy = self.ctc.block_occupancy if is_green else self.ctc.block_occupancy_red

        if node and node.block_number == target_stop:
            if target_stop in station_map:
                train.authority_meters = node.block_length / 2.0
                print(
                    f"Train {train.train_id} is at station {target_stop}; setting authority to half block length = {train.authority_meters} m")
            else:
                train.authority_meters = 0.0
                print(f"Train {train.train_id} is at target {target_stop}; authority = 0.0")
            return

        total = 0.0
        start_in_second_half = (train.last_stop_passed == node.block_number) if node else False

        while node and node.block_number != target_stop:
            if node.next and block_occupancy[node.next.block_number - 1] and node != train.current_block:
                if node.prev:
                    zero_auth[node.prev.block_number - 1] = True
                    total -= node.prev.block_length
                    if node.prev.prev:
                        zero_auth[node.prev.prev.block_number - 1] = True
                        total -= 0.5 * node.prev.prev.block_length
                train.authority_meters = total
                return

            total += node.block_length / 2.0 if start_in_second_half else node.block_length
            start_in_second_half = False
            node = node.next

        if node:
            if target_stop in station_map:
                total += node.block_length / 2.0
            else:
                total += node.block_length

        train.authority_meters = total
        print(
            f"Authority from block {train.current_block.block_number if train.current_block else '??'} to {target_stop} = {total} m")

    def update_train_positions(self):
        if not self.ctc:
            return

        green_occupied = [i + 1 for i, occ in enumerate(self.ctc.get_block_occupancy()) if occ]
        red_occupied = [i + 1 for i, occ in enumerate(self.ctc.red_get_block_occupancy()) if occ]

        for train in self.active_trains[:]:
            if train.current_block is None:
                continue

            curr_num = train.current_block.block_number
            is_green = train.line_name.lower().strip() == "green line"
            occupied_blocks = green_occupied if is_green else red_occupied
            yard_block = 58 if is_green else 10

            if hasattr(train, 'stop_timer'):
                train.stop_timer -= 1
                if train.stop_timer <= 0:
                    del train.stop_timer
                    train.last_stop_passed = curr_num
                    train.next_stop_index += 1
                    self.update_authority(train)
                continue

            if curr_num == yard_block:
                print(f"Train {train.train_id} has reached YARD. Deleting train.")
                if is_green:
                    self.green_trains_finished += 1
                else:
                    self.red_trains_finished += 1

                self.update_system_analysis()  # refresh the throughput table
                self.active_trains.remove(train)
                for tm in self.real_active_trains:
                    if tm.train_number == train.train_id:
                        tm.__del__()
                        self.real_active_trains.remove(tm)
                        break
                continue

            if curr_num in occupied_blocks:
                self.update_authority(train)
                continue

            nxt = train.current_block.next
            if not nxt:
                print(f"Train {train.train_id} finished route at block {curr_num}.")
                continue

            nxt_num = nxt.block_number
            if nxt_num in occupied_blocks:
                train.current_block = nxt
                self.update_authority(train)
                if nxt_num == yard_block:
                    print(f"Train {train.train_id} arriving at YARD. Starting final stop.")
                    if not hasattr(train, 'stop_timer'):
                        train.stop_timer = self.stopping_time
                elif train.next_stop_index < len(train.scheduled_stops) and nxt_num == train.scheduled_stops[
                    train.next_stop_index]:
                    if not hasattr(train, 'stop_timer'):
                        train.stop_timer = self.stopping_time
                        print(f"Train {train.train_id} arrived at stop {nxt_num}. Holding for 10 seconds.")

    def update_maintenance(self, green_maintenance_list, maintenance_red_list):
        if self.ctc:
            self.ctc.maintenance = green_maintenance_list.copy()
            self.ctc.maintenance_red = maintenance_red_list.copy()

    def update(self):
        if not self.ctc:
            return

        self.update_train_positions()
        self.ctc.stop_signals = self.ctc.track_controller.stop_states
        self.ctc.red_stop_signals = self.ctc.red_track_controller.stop_states

        self.ctc.block_authority = [[False] * 10 for _ in range(150)]
        self.ctc.red_block_authority = [[False] * 10 for _ in range(76)]

        max_auth = 1023
        update_window = 2

        for train in self.active_trains:
            is_green = train.line_name.lower().strip() == "green line"
            authority_arr = self.ctc.block_authority if is_green else self.ctc.red_block_authority
            zero_auth = self.zero_authority_green if is_green else self.zero_authority_red
            max_blocks = 150 if is_green else 76

            remaining = train.authority_meters
            node = train.current_block
            window_count = 0

            while remaining > 0 and node and window_count < update_window:
                auth_value = min(int(remaining), max_auth)
                bits = [(auth_value >> i) & 1 == 1 for i in range(9, -1, -1)]
                index = node.block_number - 1
                if 0 <= index < max_blocks:
                    if zero_auth[index]:
                        bits = [False] * 10
                    authority_arr[index] = bits
                remaining -= node.block_length
                node = node.next
                window_count += 1

        for i, m in enumerate(self.ctc.maintenance):
            if m:
                self.ctc.block_authority[i] = [False] * 10
        for i, m in enumerate(self.ctc.maintenance_red):
            if m:
                self.ctc.red_block_authority[i] = [False] * 10

        for i, stop in enumerate(self.ctc.get_stop_signals()):
            if stop:
                self.zero_authority_green[i] = True
                self.ctc.block_authority[i] = [False] * 10
        for i, stop in enumerate(self.ctc.red_get_stop_signals()):
            if stop:
                self.zero_authority_red[i] = True
                self.ctc.red_block_authority[i] = [False] * 10

        self.ctc.send_to_track_controller()


        self.zero_authority_green = [False] * 150
        self.zero_authority_red = [False] * 76

    def update_all_trains(self, world_time, delta_t=1):
        for train in self.real_active_trains:
            train.update_train(world_time, delta_t)
            delta_one_sec = delta_t
            while delta_one_sec < 1:
                train.update_train_no_signal_pickup(world_time, delta_t)
                delta_one_sec += delta_t

    def update_track_states(self):
        green_mapping = [
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

        red_mapping = [
            ("Red Crossing 1", self.ctc.red_crossing_states[0]),
            ("Red Crossing 2", self.ctc.red_crossing_states[1]),
            ("Red Switch 1", self.ctc.red_switch_states[0]),
            ("Red Switch 2", self.ctc.red_switch_states[1]),
            ("Red Switch 3", self.ctc.red_switch_states[2]),
            ("Red Switch 4", self.ctc.red_switch_states[3]),
            ("Red Switch 5", self.ctc.red_switch_states[4]),
            ("Red Switch 6", self.ctc.red_switch_states[5]),
            ("Red Switch 7", self.ctc.red_switch_states[6]),
            ("Red Light 1", self.ctc.red_light_states[0]),
            ("Red Light 2", self.ctc.red_light_states[1]),
            ("Red Light 3", self.ctc.red_light_states[2]),
            ("Red Light 4", self.ctc.red_light_states[3])
        ]

        for row, (desc, state) in enumerate(green_mapping):
            item = QTableWidgetItem("Active" if state else "Inactive")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates.setItem(row, 0, item)

        for row, (desc, state) in enumerate(red_mapping):
            item = QTableWidgetItem("Active" if state else "Inactive")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.TrackStates_2.setItem(row, 0, item)

    def set_system_analysis_table(self, table_widget):
        self.tableSystemAnalysis = table_widget

    def update_system_analysis(self):
        if self.tableSystemAnalysis is None:
            return  # don't crash if GUI didn't hook up the table

        data = {
            0: [str(self.red_trains_finished)],
            1: [str(self.green_trains_finished)]
        }

        for row in range(2):
            item = QTableWidgetItem(data[row][0])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tableSystemAnalysis.setItem(row, 0, item)

    def get_block_authority(self):
        return {
            "Green Line": self.ctc.get_block_authority(),
            "Red Line": self.ctc.red_get_block_authority()
        }

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
        # Remove checkboxes for trains that are no longer active
        for train_number in list(self.checkboxes.keys()):
            if not any(train_model.train_number == train_number for train_model in self.real_active_trains):
                checkbox = self.checkboxes.pop(train_number, None)
                if checkbox:
                    checkbox.deleteLater()

        # Add checkboxes for new trains
        for train_model in self.real_active_trains:
            if train_model.train_number not in self.checkboxes:
                checkbox = QCheckBox(f"Train {train_model.train_number}")
                checkbox.setChecked(False)
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
