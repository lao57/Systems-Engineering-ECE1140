import sys
from typing import List, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

import TrackModelBackend
import track_gui_and_testbench_unified
import testbench_track_controller
from train_controller.train_controller_gui import TrainControllerGUI
from train_model.train_model import TrainModel
from ctc import CTC
from station_map import STATION_BLOCKS


# add attribute to block for middle distance
class TrackBlock:
    def __init__(self, block_number: int, block_length: float):
        self.block_number = block_number
        self.block_length = block_length
        self.next = None  # pointer to next block in route


class Train:
    def __init__(
            self, train_id: int, route_head: TrackBlock, scheduled_stops: List[int] = None,
            current_block: TrackBlock = None, next_stop_index: int = 0,
            authority_meters: float = 0.0, last_stop_passed: int = None
    ):
        self.train_id = train_id  # unique train id
        self.route_head = route_head  # head node of L.L. representing route
        self.scheduled_stops = scheduled_stops if scheduled_stops is not None else []  # list of block nums to stop
        self.current_block = current_block  # current block train on
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
        index = 0  # init index counter @ 0
        node = self.route_head  # start at head of L.L. representing route
        while node:
            # if current node matches train's current block, return index
            if node == self.current_block:
                return index
            node = node.next  # move to next node & increment index
            index += 1
        return -1  # if curr block not found (shouldn't happen)


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

    def __init__(self, track_layout: Dict[str, List[dict]], schedules: Dict[str, List]):
        self.track_layout = track_layout  # save track layout
        self.schedules = schedules  # save schedule
        self.ctc: CTC = None  # set later
        self.active_trains: List[Train] = []  # list to keep track of active trains
        self.real_active_trains = []
        # dict mapping blk nums to blk data; easier to lookup block lengths on Green Line
        self.green_blocks = {b['block_number']: b for b in track_layout.get('Green Line', [])}
        self.track_model = None
        self.k_p = 2e5
        self.k_i = 2e4

    def set_ctc(self, ctc: CTC):
        self.ctc = ctc  # assign ctc

    def build_linked_route(self, route_numbers: List[int]) -> TrackBlock:
        head = None  # 1st block in route
        curr = None  # track current end of L.L.
        # iterate thru each block num in route
        for num in route_numbers:
            # look up block length from green_blocks dict; if not found, default to 0.0
            length = self.green_blocks[num]['block_length'] if num in self.green_blocks else 0.0
            node = TrackBlock(num, length)  # create new TrackBlock instance
            if head is None:  # if first node, set as head of list
                head = node
                curr = node
            else:
                curr.next = node  # otherwise, link current node to new node
                curr = node  # update curr pointer to new node
        return head  # return head of L.L. representing route

    def schedule_train(self, line: str, train_index: int):
        # get schedule for line and train index.
        try:
            schedule = self.schedules[line][train_index]
        except (KeyError, IndexError):
            return

        # Get stops from schedule
        stops = sorted([item['block'] for item in schedule.stops])

        # Build route from yard exit (62) to each stop in order.
        route_numbers = []
        # current_position = 62  # always start from yard exit on Green
        current_position = 64  # always start from yard exit on Green

        # go through each stop block in route
        for stop_block in stops:
            if stop_block not in self.green_line_route:
                print(f"Stop block {stop_block} not in green_line_route. Skipping.")
                return
            try:
                start_index = self.green_line_route.index(current_position)  # find index for current position
                target_index = self.green_line_route.index(stop_block)  # find index for scheduled stop
            except ValueError:
                print(f"Error: {current_position} or {stop_block} not found in route array.")
                return
            # if stop coming up, take segment directly.
            if target_index >= start_index:
                segment = self.green_line_route[start_index:target_index + 1]
            else:
                # Reverse slice if desired stop already passed.
                segment = self.green_line_route[target_index:start_index + 1][::-1]
            # add segment to route_numbers list and avoid duplicating current block if last element
            if route_numbers and route_numbers[-1] == current_position:
                route_numbers += segment[1:]
            else:
                route_numbers += segment
            current_position = stop_block  # update current pos to stop

        print("route_numbers: ", route_numbers)

        # Convert list of route numbers to linked list
        route_head = self.build_linked_route(route_numbers)
        # create new train instance with route and schedule
        train = Train(
            train_id=schedule.train_id,
            route_head=route_head,
            scheduled_stops=stops,
            current_block=route_head,
            next_stop_index=1
        )
        train_model = TrainModel(k_p=self.k_p, k_i=self.k_i)
        train_model.add_classes(self.track_model)
        self.update_authority(train)  # calculate authority
        self.active_trains.append(train)  # add train to active list of trains
        self.real_active_trains.append(train_model)
        print(f"Scheduled Train {train.train_id} with route {route_numbers}")

    @staticmethod
    def update_authority(train: Train):
        print(f"Calculating authority for Train {train.train_id}:")
        # Check if any stops left. If not, set train's authority to 0.
        if train.next_stop_index >= len(train.scheduled_stops):
            train.authority_meters = 0.0
            print("No next stop; authority = 0.0")
            return
        # If the train is already at its target stop, set authority to 0.
        if train.current_block and train.current_block.block_number == train.scheduled_stops[train.next_stop_index]:
            train.authority_meters = 0.0
            print(f"Train {train.train_id} is at stop {train.scheduled_stops[train.next_stop_index]}; authority = 0.0")
            return
        target_stop = train.scheduled_stops[train.next_stop_index]  # get next scheduled stop's block number
        total = 0.0  # init accumulator for total allowed distance
        node = train.current_block  # start at train's current position in route
        # Sum lengths of blocks in route until target stop is reached.
        while node and node.block_number != target_stop:
            total += node.block_length
            node = node.next
        if node:
            if target_stop in STATION_BLOCKS['BLOCK_TO_STATION']:
                total += node.block_length / 2.0
            else:
                total += node.block_length
        # Do not add the target block's length, so that when the train arrives, authority is 0.
        train.authority_meters = total
        print(
            f"Authority from {train.current_block.block_number if train.current_block else '??'} to {target_stop} = {total} m")

    def update_train_positions(self):
        if not self.ctc:
            return
        # Create list of blocks that are currently occupied (blocks are 1-indexed).
        occupied_blocks = [i + 1 for i, occ in enumerate(self.ctc.get_block_occupancy()) if occ]
        # Iterate over all active trains.
        for train in self.active_trains:
            if train.current_block is None:
                continue
            curr_num = train.current_block.block_number  # get current block number
            # If current block is still occupied, do nothing.
            if curr_num in occupied_blocks:
                continue
            # Check next block in the route.
            nxt = train.current_block.next
            if not nxt:
                print(f"Train {train.train_id} finished route at block {curr_num}.")
                continue
            nxt_num = nxt.block_number  # get next block number
            # If next block is occupied, then the train has moved into that block.
            if nxt_num in occupied_blocks:
                train.current_block = nxt  # update train's current block to next block
                self.update_authority(train)  # recalculate authority after moving
                print(train.authority_meters)
                # If there are still stops:
                if train.next_stop_index < len(train.scheduled_stops):
                    # Check if the train has reached the scheduled stop.
                    if nxt_num == train.scheduled_stops[train.next_stop_index]:
                        train.last_stop_passed = nxt_num  # store that train passed this stop
                        train.next_stop_index += 1  # increment to point to the next scheduled stop
                        print(
                            f"Train {train.train_id} arrived at stop {nxt_num}. Next stop index = {train.next_stop_index}")
                        self.update_authority(train)  # recalculate authority; should become 0 at the stop
                        print(train.authority_meters)

    def update_maintenance(self, maintenance_list):
        if self.ctc:
            self.ctc.maintenance = maintenance_list.copy()

    def update(self):
        if not self.ctc:
            return
        self.ctc.stop_signals = self.ctc.track_controller.stop_states
        # Reset each block's authority to a 10-bit array of [False].
        self.ctc.block_authority = [[False] * 10 for _ in range(150)]
        max_auth = 1023  # max value of 10 bits
        # For each active train, update authority for the route.
        for train in self.active_trains:
            remaining = train.authority_meters  # remaining allowed travel distance (in meters)
            node = train.current_block  # start from train's current block
            # Traverse the route until no remaining authority or end of route is reached.
            while remaining > 0 and node:
                auth_value = min(int(remaining), max_auth)  # cap authority value to max_auth
                # Convert auth_value to a 10-bit boolean list (MSB first)
                bits = [(auth_value >> i) & 1 == 1 for i in range(9, -1, -1)]
                index = node.block_number - 1  # compute index for block in authority array
                if 0 <= index < 150:
                    self.ctc.block_authority[index] = bits  # assign the 10-bit list to the block
                remaining -= node.block_length  # subtract block length from remaining authority
                node = node.next  # move to next block
        # Overwrite authority for blocks under maintenance.
        for i, m in enumerate(self.ctc.maintenance):
            if m:
                self.ctc.block_authority[i] = [False] * 10
        # Stop signals
        for i, stop in enumerate(self.ctc.get_stop_signals()):
            if stop:
                self.ctc.block_authority[i] = [False] * 10
        self.ctc.send_to_track_controller()  # update track controller with latest authority and maintenance
        self.update_train_positions()  # update train positions based on block occupancy

    def update_all_trains(self, world_time, delta_t=1):
        for train in self.real_active_trains:
            train.update_train(world_time)
            train.display_train()

    def update_track_states(self):
        mapping = [
            ("Crossing 1", self.ctc.crossing_states[0]),
            ("Crossing 2", self.ctc.crossing_states[1]),
            ("Switch 1", self.ctc.switch_states[0]),
            ("Light 1", self.ctc.light_states[0]),
            ("Switch 2", self.ctc.switch_states[1]),
            ("Light 2", self.ctc.light_states[1]),
            ("Switch 3", self.ctc.switch_states[2]),
            ("Light 3", self.ctc.light_states[2]),
            ("Switch 4", self.ctc.switch_states[3]),
            ("Light 4", self.ctc.light_states[3]),
            ("Switch 5", self.ctc.switch_states[4]),
            ("Light 5", self.ctc.light_states[4]),
            ("Switch 6", self.ctc.switch_states[5]),
            ("Light 6", self.ctc.light_states[5])
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

    def set_ctc(self, ctc):
        self.ctc = ctc

    def set_track_model(self, track_model):
        self.track_model = track_model
