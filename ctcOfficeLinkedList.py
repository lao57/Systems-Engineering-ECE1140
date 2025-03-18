from typing import List, Dict
from ctc import CTC

class TrackBlock:
    def __init__(self, block_number: int, block_length: float):
        self.block_number = block_number  # block id
        self.block_length = block_length  # block length (m)
        self.next = None  # pointer to next block

class Train:
    def __init__(self, train_id: int, route_head: TrackBlock, scheduled_stops: List[int] = None, current_block: TrackBlock = None, next_stop_index: int = 0, authority_meters: float = 0.0, last_stop_passed: int = None):
        self.train_id = train_id  # train id
        self.route_head = route_head  # head node of the route linked list
        self.scheduled_stops = scheduled_stops if scheduled_stops is not None else []  # List of stops
        self.current_block = current_block  # current position in the route
        self.next_stop_index = next_stop_index  # next stop index in scheduled_stops
        self.authority_meters = authority_meters  # allowed travel distance
        self.last_stop_passed = last_stop_passed  # last processed stop

    @property
    def route_blocks(self) -> List[int]:
        blocks = []
        node = self.route_head
        while node:
            blocks.append(node.block_number)  # collect block ids from the route
            node = node.next
        return blocks

    @property
    def current_block_index(self) -> int:
        index = 0
        node = self.route_head
        while node is not None:
            if node == self.current_block:
                return index  # return position of current block
            index += 1
            node = node.next
        return -1  # not found (shouldn't happen)

class CTCOffice:

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
        self.track_layout = track_layout  # track layout data
        self.schedules = schedules  # schedule data
        self.ctc = None  # ctc instance (set later)
        self.active_trains: List[Train] = []  # list of active trains
        # map block number to its details for Green Line used for blk lengths
        self.green_blocks = {b['block_number']: b for b in track_layout.get('Green Line', [])}


    def set_ctc(self, ctc):
        self.ctc = ctc  #assigns central ctc


    def build_full_route(self, stops: List[int]) -> List[int]:
        full_route = []  # get full route block numbers
        try:
            current_index = self.green_line_route.index(62)  # start at block 62
        except ValueError:
            return full_route
        for stop in stops:
            try:
                target_index = self.green_line_route.index(stop, current_index)
            except ValueError:
                break
            full_route += self.green_line_route[current_index:target_index + 1]
            current_index = target_index
        return full_route

    def build_linked_route(self, route_numbers: List[int]) -> TrackBlock:
        head = None  # head of the linked list
        current = None
        for num in route_numbers:
            length = self.green_blocks[num]['block_length'] if num in self.green_blocks else 0.0
            node = TrackBlock(num, length)  # create a node for the block
            if head is None:
                head = node
                current = node
            else:
                current.next = node  # link node
                current = node
        return head

    def schedule_train(self, line: str, train_idx: int):
        try:
            schedule = self.schedules[line][train_idx]  # get train schedule
        except (KeyError, IndexError):
            return

        # list of stops (ignoring yard)
        stops = [stop['block'] for stop in schedule.stops if stop['block'] != 62]
        if 58 not in stops:
            stops.append(58)  # ensure final stop is included
        route_numbers = []
        current_position = 62
        for stop in stops:
            start_index = self.green_line_route.index(current_position) #Start
            target_index = self.green_line_route.index(stop) #End

            #get segment from curr. position to stop
            if target_index > start_index:
                segment = self.green_line_route[start_index:target_index + 1]
            else:
                #handles if stop num comes before current num
                segment = self.green_line_route[start_index:] + self.green_line_route[:target_index + 1]
            route_numbers += segment
            current_position = stop

        # Convert the route into a linked list of track blocks
        route_head = self.build_linked_route(route_numbers)

        #create new train w/ route
        train = Train(
            train_id=schedule.train_id,
            route_head=route_head,
            scheduled_stops=stops,
            current_block=route_head, #sets current position to route head
            next_stop_index=0 if stops else -1
        )
        self.update_authority(train)
        self.active_trains.append(train)

    @staticmethod
    def update_authority(train: Train):
        print(f"\nCalculating authority for Train {train.train_id}:")
        if train.next_stop_index >= len(train.scheduled_stops):
            train.authority_meters = 0.0
            print("No next stop; authority set to 0.0")
            return
        target_stop = train.scheduled_stops[train.next_stop_index]  # Next stop to reach
        total = 0.0
        node = train.current_block
        #skip dupe. nodes if already at the target stop
        while node is not None and node.block_number == target_stop:
            print(f"  Skipping duplicate block {node.block_number} ({node.block_length} m)")
            node = node.next
        #sum block lengths until the target stop is reached
        while node is not None and node.block_number != target_stop:
            print(f"  Adding block {node.block_number} ({node.block_length} m)")
            total += node.block_length
            node = node.next
        if node is not None:
            print(f"  Including stop block {node.block_number} ({node.block_length} m)")
            total += node.block_length
        train.authority_meters = total
        print(f"Total authority: {total} m\n")

    def update_train_positions(self):
        if not self.ctc:
            return

        #list of occupied blocks
        occupied_blocks = [i + 1 for i, occ in enumerate(self.ctc.block_occupancy) if occ]
        for train in self.active_trains:
            if train.current_block is None:
                continue
            current_block_num = train.current_block.block_number
            if current_block_num in occupied_blocks:  # advance if current block is occupied
                if train.current_block.next is not None:
                    train.current_block = train.current_block.next
                    if train.scheduled_stops and train.current_block.block_number != train.scheduled_stops[train.next_stop_index]:
                        self.update_authority(train)

            # process arrival at scheduled stop
            if train.next_stop_index < len(train.scheduled_stops):
                next_stop = train.scheduled_stops[train.next_stop_index]
                if train.current_block and train.current_block.block_number == next_stop:
                    if train.last_stop_passed != next_stop:
                        train.last_stop_passed = next_stop
                        train.next_stop_index += 1
                        print(f"Train {train.train_id} reached stop {next_stop}. Next stop index: {train.next_stop_index}.")

    def update_maintenance(self, maintenance: List[bool]):
        if self.ctc:
            self.ctc.maintenance = maintenance.copy()

    def update(self):

        if not self.ctc:
            return

        self.ctc.block_authority = [False] * 150  # reset block authority for all blocks
        max_authority = 1023  # max auth value

        for train in self.active_trains:
            remaining = train.authority_meters  # distance train is allowed to travel
            current_node = train.current_block  # start from train’s current position

            while remaining > 0 and current_node is not None:
                chunk = min(remaining, max_authority)  # limit chunk size to max authority
                bits = [bool((int(chunk) >> i) & 1) for i in range(10)]  # convert to 10-bit representation

                node = current_node
                for i, bit in enumerate(bits):
                    if node is None:
                        break  # stop if we run out of blocks

                    block_num = node.block_number
                    if 1 <= block_num <= 150:
                        self.ctc.block_authority[block_num - 1] = bit  # assign bit to corresponding block

                    node = node.next  # move to the next block

                remaining -= chunk  # reduce remaining authority distance

                # move forward by 10 blocks to continue assigning authority bits
                for i in range(10):
                    if current_node is not None:
                        current_node = current_node.next
                    else:
                        break

        # disable authority for blocks under maintenance
        for i, maint in enumerate(self.ctc.maintenance):
            if maint:
                self.ctc.block_authority[i] = False

        self.ctc.send_to_track_controller()  # Send updated authority data to the track controller
