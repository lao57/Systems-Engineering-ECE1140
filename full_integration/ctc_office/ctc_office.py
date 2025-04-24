import sys
from typing import List, Dict
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem, QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel
import track_model.track_model_backend as track_model_backend
import track_model.track_gui_and_testbench_unified as track_gui_and_testbench_unified
import track_controller.testbench_track_controller as testbench_track_controller
from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
import re

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
            self.stop_signals = self.track_controller.stop_states

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

@dataclass
class ScheduleEntry:
    train_id: int  # unique id for train
    stops: list  # list of stop dictionaries, each with a 'block' and 'time' key
    line: str  # which line train is on
    departure_time: int  # in minutes from midnight (departure_time = first expected arrival - 30 minutes)

class ScheduleLoader:
    def __init__(self, track_layout):
        self.track_layout = track_layout
        self.station_map = self.build_station_map() #maps station names to block numbers
        self.green_yard_exit = 62
        self.green_yard_entrance = 58

    def build_station_map(self) -> dict:
        station_map = {} # Initialize an empty dictionary to store the final mapping.

        # Loop through each line in the track layout (e.g., "Green Line", "Red Line")
        for line, blocks in self.track_layout.items():
            line_map = {} #temporary mapping for current line

            # Loop through each block in the current line
            for blk in blocks:
                # Get the 'infrastructure' field of the block (e.g., "STATION: PIONEER")
                infra = blk.get('infrastructure', '').upper()
                if 'STATION' in infra:
                    # Look for the word "STATION" followed by either a colon or whitespace,
                    # then capture the station name that follows (up to but not including a semicolon, if present).
                    match = re.search(r'STATION[:\s]+([^;]+)', infra)

                    if match:
                        name = match.group(1).strip().upper() # Extract and clean the station name, and convert to uppercase
                        line_map[name] = blk['block_number'] # Map the station name to the corresponding block number

            station_map[line] = line_map # After processing all blocks in this line, store its station mapping
        return station_map #return mapping

    def load_from_excel(self, path: str) -> Dict[str, list]:
        # Initialize an empty dictionary to hold schedules for both lines
        schedules = {'Green Line': [], 'Red Line': []}
        # Loop over each line
        for line in ['Green Line', 'Red Line']:
            sheet_name = f"{line} Scheduling"
            try:
                # Attempt to read the Excel sheet, keeping only the relevant columns
                df = pd.read_excel(path, sheet_name=sheet_name, usecols=['Train ID', 'Stops', 'expected_arrival_times'])
                df = df.dropna(subset=['Stops']) # Drop rows that don't specify any stops (invalid)
            except Exception as e:
                print(e)
                continue

            line_schedules = [] # Temporary list to hold parsed schedule entries for this line
            # Iterate over each row in the DataFrame
            for idx, row in df.iterrows():
                try:
                    # Convert each row into a ScheduleEntry object
                    entry = self.parse_row(row, line, idx + 2) # Pass row number for easier error tracking
                    line_schedules.append(entry) # Add the parsed entry to the list
                except Exception as e:
                    print(f"Row {idx+2} parsing error: {e}")
                    pass
            schedules[line] = line_schedules # Save all valid schedule entries under the line's name
        return schedules # Return the complete schedule dictionary for both lines

    def parse_row(self, row, line: str, row_num: int) -> ScheduleEntry:
        train_id = int(row['Train ID']) # Extract the train ID from the row and cast to integer
        # Get the stop and time strings, stripping extra spaces
        stops_str = str(row['Stops']).strip()
        times_str = str(row['expected_arrival_times']) if pd.notna(row['expected_arrival_times']) else ''

        # Split the stop and time strings by commas into lists
        stop_list = [s.strip() for s in re.split(r',', stops_str) if s.strip()]
        time_list = [t.strip() for t in re.split(r',', times_str) if t.strip()]

        # Validate that the number of stops matches the number of times
        if len(stop_list) != len(time_list):
            raise ValueError(f"{len(stop_list)} stops but {len(time_list)} times")

        stops = [] # This will store block and time pairs
        # Iterate through each stop and time
        for i, (station, time_str) in enumerate(zip(stop_list, time_list)):
            st_up = station.upper()
            time_obj = datetime.strptime(time_str, '%H:%M').time() # Convert time string to time object

            # Handle YARD as block 58
            if st_up == 'YARD':
                block = self.green_yard_entrance  # 58
            else:
                try:
                    # Try interpreting station name as a raw block number
                    block = int(st_up)
                    # Validate block exists in track layout
                    if not any(blk['block_number'] == block for blk in self.track_layout[line]):
                        raise ValueError(f"Invalid block {block} on {line}")
                except ValueError:

                    # If not a valid int, look up station name in station map
                    block = self.station_map[line].get(st_up)
                    if not block:
                        valid_stations = ', '.join(self.station_map[line].keys())
                        raise ValueError(f"Unknown station '{station}'. Valid: {valid_stations}")

            stops.append({'block': block, 'time': time_obj}) # Append the parsed stop as a dictionary with block number and time

        # departure_time = first expected arrival time - 30.
        first_time_obj = datetime.strptime(time_list[0], '%H:%M').time()
        first_minutes = first_time_obj.hour * 60 + first_time_obj.minute
        departure_time = max(0, first_minutes - 30)
        # Return the parsed schedule entry
        return ScheduleEntry(train_id=train_id, stops=stops, line=line, departure_time=departure_time)


def load_track_layout(path: str) -> Dict[str, List[dict]]:
    # Mapping of column names from Excel to internal dictionary keys
    COLUMN_MAP = {
        'block number': 'block_number',
        'block length (m)': 'block_length',
        'speed limit (km/hr)': 'speed_limit',
        'infrastructure': 'infrastructure'
    }

    # Helper function to process a single sheet (Red Line or Green Line)
    def process_sheet(sheet: str) -> List[dict]:
        try:
            # Read the sheet from Excel using openpyxl and rename columns to lowercase
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                engine='openpyxl'
            ).rename(columns=str.lower).rename(columns=COLUMN_MAP)

            # Drop rows without a block number
            df = df.dropna(subset=['block_number'])
            # Convert block_number column to integer (ignoring bad entries)
            df['block_number'] = pd.to_numeric(df['block_number'], errors='coerce').dropna().astype(int)

            valid_blocks = []
            # Iterate through each row and build a dictionary for valid blocks
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

            return valid_blocks # Return the list of validated block dictionaries

        except Exception as e:
            print(f"track loader exception: {e}")
            return []

    # Return dictionary of processed sheets for both Red and Green Line
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
        self.zero_authority = [False] * 150 #zero authority for all blocks
        self.green_trains_finished = 0  # Counts Green Line trains that reach the yard

        self.TrainUIToggle = TrainUIToggle(self.real_active_trains)
        self.TrainUIToggle.show()

    def set_ctc(self, ctc: CTC):
        self.ctc = ctc  # assign ctc

    def build_linked_route(self, route_numbers: List[int]) -> TrackBlock:
        head = None  # first block in route
        curr = None  # pointer to current end of linked list
        index = 0 # Start from the first block in the route list

        # Get the first block number in the route, if any
        block_num = route_numbers[index] if index < len(route_numbers) else None
        # Fetch the block length from the green_blocks dictionary; use 0.0 if block not found
        length = self.green_blocks[block_num]['block_length'] if block_num in self.green_blocks else 0.0
        node = TrackBlock(index, length) # Create the first TrackBlock node

        # Set both current and head pointer to the new node
        curr = node
        head = node
        node.prev = None # First node has no previous block
        curr.next = self.recursive_link_helper(route_numbers, 0) # Recursively build the rest of the linked list
        # If there's a second block, link its prev pointer to the current block
        if curr.next:
            curr.next.prev = curr
        return head # Return the head of the fully built linked list


    def recursive_link_helper(self, route_numbers: List[int], index: int) -> TrackBlock:
        if index >= len(route_numbers):
            return None
        block_num = route_numbers[index] #get block number and it's length
        length = self.green_blocks[block_num]['block_length'] if block_num in self.green_blocks else 0.0
        node = TrackBlock(block_num, length) #create node for current block
        node.next = self.recursive_link_helper(route_numbers, index + 1) #recursively create next node and link it
        if node.next:
            node.next.prev = node
        return node


    #instead of immediate dispatch add to pending
    def add_pending_train(self, schedule_entry: ScheduleEntry):
        self.pending_trains.append(schedule_entry)

        # Sort the list of pending trains by their departure time so that
        # the next train to launch is always first in the list
        self.pending_trains.sort(key=lambda x: x.departure_time)

    #launch pending trains whose departure time is reached.
    def launch_pending_trains(self, current_minutes: int):
        while self.pending_trains and self.pending_trains[0].departure_time <= current_minutes:
            entry = self.pending_trains.pop(0)
            self.launch_train(entry)

    def launch_train(self, schedule_entry: ScheduleEntry):
        # Extract the list of stop block numbers from the schedule entry
        stops = [item['block'] for item in schedule_entry.stops]
        current_position = 64  # start from yard exit on Green Line
        route_numbers = [] # This will store the full path of block numbers the train will follow

        # Build a list of blocks from the yard exit to each stop
        for stop_block in stops:
            if stop_block not in self.green_line_route:
                print(f"Stop block {stop_block} not in green_line_route. Skipping.")
                return
            try:
                # Get the index of the current position and the target stop in the route
                start_index = self.green_line_route.index(current_position)
                target_index = self.green_line_route.index(stop_block)
            except ValueError:
                return

            # Extract the segment from current to stop (forward or backward in route)
            if target_index >= start_index:
                segment = self.green_line_route[start_index:target_index + 1]
            else:
                segment = self.green_line_route[target_index:start_index + 1][::-1]

            # Avoid repeating the same block twice when stitching segments
            if route_numbers and route_numbers[-1] == current_position:
                route_numbers += segment[1:]
            else:
                route_numbers += segment
            current_position = stop_block # Update the current position to the latest stop

        route_head = self.build_linked_route(route_numbers)  # Convert the list of block numbers to a linked list of TrackBlock nodes
        # Create a Train object to track state during simulation
        train = Train(
            train_id=schedule_entry.train_id,
            route_head=route_head,
            scheduled_stops=stops,
            current_block=route_head,
            next_stop_index=0
        )
        # Create the actual train model used in simulation and GUI
        train_model = TrainModel(train_number=schedule_entry.train_id, LOOP_INTERVAL_MS=self.loop_int_ms,
                                 k_p=self.k_p, k_i=self.k_i, line = "green", start_block = 64)
        train_model.add_classes(self.track_model)
        self.update_authority(train) # Calculate the initial authority for this train
        # Add the train to both the simulation list and UI control list
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

        if line.lower().strip() != "green line":
            return
        yard_exit = 64
        yard_entrance = 58
        # If no stops provided or final stop isn't the yard entrance, append the yard
        if not stops or stops[-1] != yard_entrance:
            stops.append(yard_entrance)

        route_numbers = [] # This will store the full path of block numbers the train will follow
        current_position = yard_exit

        # Build a list of blocks from the yard exit to each stop
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

        # Check if a train with this ID already exists in the active trains
        existing_train = None
        for t in self.active_trains:
            if t.train_id == train_id:
                existing_train = t
                break
        if existing_train is not None:
            # If the train exists, just update its route and reset its stop index
            existing_train.route_head = route_head
            existing_train.scheduled_stops = stops
            existing_train.next_stop_index = 0
            self.update_authority(existing_train)

        else:
            new_train = Train(
                train_id=train_id,
                route_head=route_head,
                scheduled_stops=stops,
                current_block=route_head,
                next_stop_index=0
            )
            train_model = TrainModel(train_number=train_id, LOOP_INTERVAL_MS=self.loop_int_ms, k_p=self.k_p, k_i=self.k_i, line = "green", start_block = 64)
            train_model.add_classes(self.track_model)
            self.update_authority(new_train)
            self.active_trains.append(new_train)
            self.real_active_trains.append(train_model)
            self.TrainUIToggle.update_ui()



    def update_authority(self, train: Train):

        # Check if no more stops remain.
        if train.next_stop_index >= len(train.scheduled_stops):
            train.authority_meters = 0.0
            return

        # Determine the next block the train is scheduled to stop at
        target_stop = train.scheduled_stops[train.next_stop_index]
        node = train.current_block

        # If the train is already at the scheduled stop block
        if train.current_block and train.current_block.block_number == target_stop:
            # If it's a known station, only grant authority to half the block length
            if target_stop in STATION_BLOCKS['BLOCK_TO_STATION']:
                train.authority_meters = train.current_block.block_length / 2.0
            else:
                # Otherwise, grant zero authority (stop exactly at the block)
                train.authority_meters = 0.0
            return

        total = 0.0  # initialize total allowed distance
        node = train.current_block  # starting from current position
        # if train just passed a stop, count half of current block length
        start_in_second_half = (train.last_stop_passed == node.block_number) if node else False

        # Traverse the route to the next scheduled stop
        while node.block_number != target_stop:
            # If the next block is occupied, cut authority early
            if self.ctc.block_occupancy[(node.next.block_number-1)] and node != train.current_block:

                # Reduce authority slightly as a buffer for safe stopping
                total -= node.prev.block_length #subtract full previous block length
                total -= int((0.5*node.prev.prev.block_length)) # subtract half of two blocks back
                # Mark those two previous blocks to forcibly assign 0 authority in the update loop
                self.zero_authority[node.prev.block_number-1] = True
                self.zero_authority[node.prev.prev.block_number-1] = True

                train.authority_meters = total
                return

            # If the train just passed a stop, only count half of the block's length
            if start_in_second_half:
                total += node.block_length / 2.0
                start_in_second_half = False
            else:
                total += node.block_length
            node = node.next # Move to the next block in the train's linked route

        # If reached target, add half length if station; else full length.
        if node:
            if target_stop in STATION_BLOCKS['BLOCK_TO_STATION']:
                total += node.block_length / 2.0
            else:
                total += node.block_length

        #final authority given to train
        train.authority_meters = total


    def update_train_positions(self):
        if not self.ctc:
            return
        # Create list of blocks currently occupied (1-indexed).
        occupied_blocks = [i + 1 for i, occ in enumerate(self.ctc.block_occupancy) if occ]
        for train in self.active_trains[:]:

            if train.current_block is None: 
                continue
            curr_num = train.current_block.block_number # Current block number of the train

            # If train is holding at a stop, decrement its timer.
            if hasattr(train, 'stop_timer'):
                train.stop_timer -= 1
                if train.stop_timer <= 0:
                    del train.stop_timer # Stop complete, remove the timer
                    train.last_stop_passed = curr_num
                    train.next_stop_index += 1 # Move to the next scheduled stop
                    self.update_authority(train) # Recalculate authority
                continue

            # Delete train if it has reached the YARD (block 58).
            if curr_num == 58: # and train.next_stop_index >= len(train.scheduled_stops):

                self.green_trains_finished += 1

                self.active_trains.remove(train)
                for tm in self.real_active_trains:
                    if tm.train_number == train.train_id:
                        tm.__del__() #call destructor to close UI and stop loop
                        self.real_active_trains.remove(tm)
                        break
                continue

            # If current block is still occupied, only update authority
            if curr_num in occupied_blocks:
                self.update_authority(train)
                continue

            # Try to move train to the next block
            nxt = train.current_block.next
            if not nxt:
                continue # End of route; no next block to move to

            nxt_num = nxt.block_number
            # If next block is occupied, assume train moved.
            if nxt_num in occupied_blocks:
                # If two blocks ahead is also occupied, assume the train has moved two blocks
                if nxt.next:
                    if nxt.next.block_number in occupied_blocks:
                        train.current_block = nxt.next
                        self.update_authority(train)
                    else:
                        # Otherwise assume it moved to just the next block
                        train.current_block = nxt
                        self.update_authority(train) # Recalculate authority after movement
                else:
                    train.current_block = nxt
                    self.update_authority(train)

                # If train just entered yard or next stop, start the stop timer
                if nxt_num == 58:
                    if not hasattr(train, 'stop_timer'):
                        train.stop_timer = self.stopping_time
                elif train.next_stop_index < len(train.scheduled_stops) and nxt_num == train.scheduled_stops[train.next_stop_index]:
                    if not hasattr(train, 'stop_timer'):
                        train.stop_timer = self.stopping_time

            else:
                # If next block is not occupied, we assume the train hasn't moved yet
                self.update_authority(train) # Still recalculate authority for safety

    def update_maintenance(self, maintenance_list):
        if self.ctc:
            self.ctc.maintenance = maintenance_list.copy()

    def update(self):
        if not self.ctc:
            return
        # Update each train's position based on occupancy and movement rules
        self.update_train_positions()

        # Update stop signals from the track controller.
        self.ctc.stop_signals = self.ctc.track_controller.stop_states

        # Clear authority for all blocks.
        self.ctc.block_authority = [[False] * 10 for _ in range(150)]

        max_auth = 1023  # maximum value of 10 bits
        update_window = 2  # Number of blocks to look ahead when assigning authority

        # For each active train
        for train in self.active_trains:
            remaining = train.authority_meters # Distance the train is allowed to travel
            node = train.current_block # Start from current block

            window_count = 0 # Tracks how many blocks we’ve updated
            #enforce zero authority for stop signals
            for i, stop in enumerate(self.ctc.get_stop_signals()):
                if stop:
                    if self.zero_authority[i] == False:
                        self.zero_authority[i] = True

            # Apply authority block-by-block until distance is exhausted or window is full
            while remaining > 0 and node and window_count < update_window:
                # Convert the authority distance to a 10-bit binary representation
                auth_value = min(int(remaining), max_auth)
                bits = [(auth_value >> i) & 1 == 1 for i in range(9, -1, -1)]
                index = node.block_number - 1 # Convert block number to 0-based index
                if 0 <= index < 150:
                    # If the block is marked for zero authority, override it
                    if self.zero_authority[index]:
                        bits = [False] * 10
                    self.ctc.block_authority[index] = bits
                # Subtract block length from remaining authority and move to the next block
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

        # Send the updated authority values and maintenance status to the track controller
        self.ctc.send_to_track_controller()
        
        self.zero_authority = [False] * 150  # reset zero authority for next update

    def update_all_trains(self, world_time, delta_t=1):
        # Loop through all real train model objects
        for train in self.real_active_trains:
            train.update_train(world_time, delta_t) #call update
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

    def set_system_analysis_table(self, table_widget):
        self.tableSystemAnalysis = table_widget

    def update_system_analysis(self):
        if not hasattr(self, "tableSystemAnalysis") or self.tableSystemAnalysis is None:
            return  # GUI didn't hook up the table yet

        data = {
            0: [str(self.green_trains_finished)]
        }

        for row in data:
            item = QTableWidgetItem(data[row][0])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tableSystemAnalysis.setItem(row, 0, item)

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
            # checkbox.setChecked(True)
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
