import logging # track system events, errors, status
from dataclasses import dataclass
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ScheduleEntry:
    train_id: int # train identifier
    stops: List[Dict] #List of dicts w/ stops
    line: str #Green or Red


@dataclass
#Represents active train
class Train:
    train_id: int
    line: str
    route_blocks: List[int] #List of block numbers representing train's route.
    current_route_index: int = 0 #Tracks which block index the train is currently on in its route.
    authority: float = 0.0 #remaining track authority

    @property
    def current_block(self) -> Optional[int]:

        # returns current route block using the route index. if train on last block, return none.
        if self.current_route_index < len(self.route_blocks):
            return self.route_blocks[self.current_route_index]
        return None


class CTCOffice:

    #switch, yard exit, and yard entrance blocks
    SWITCH_MAP = {12: 0, 28: 1, 77: 2, 85: 3, 100: 4, 108: 5}
    GREEN_LINE_YARD_EXIT = 62
    GREEN_LINE_YARD_ENTRY = 58



    def __init__(self, track_layout: Dict[str, List[dict]], schedules: Dict[str, List[ScheduleEntry]]):
        self.track_layout = track_layout #stores track info
        self.schedules = schedules #stores schedules
        self.ctc = None
        self.active_trains: List[Train] = [] #list storing active trains

        #Green Line data
        self.green_line_blocks = {blk['block_number']: blk
                                  for blk in track_layout['Green Line']}
        self.green_line_route = self.build_green_route()

    #assigns ctc
    def set_ctc(self, ctc):
        self.ctc = ctc

    #builds green route
    def build_green_route(self) -> List[int]:

        return [
            # Yard exit (62) to 76
            62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
            # Through switch to 77-85
            77, 78, 79, 80, 81, 82, 83, 84, 85,
            # Switch to 86-100
            86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
            # Back to 85 through switch
            99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85,
            # Switch to 101-150
            101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114,
            115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128,
            129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142,
            143, 144, 145, 146, 147, 148, 149, 150,
            # Switch to 28
            28,
            # Down to 13
            27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13,
            # Switch to 13-1
            12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
            # Return to yard via 58
            58
        ]


    #checks if all required blocks are part of route
    def validate_schedule(self, schedule: ScheduleEntry) -> bool:

        required_blocks = {stop['block'] for stop in schedule.stops}
        route_blocks = set(self.green_line_route)
        missing = required_blocks - route_blocks

        if missing:
            logger.error(f"Train {schedule.train_id} has invalid stops: {missing}")
            return False
        return True

    def schedule_train(self, line: str, train_index: int):

        try:
            # Validate if the line exists in the schedule dictionary
            if line not in self.schedules:
                logger.error(f"Invalid line '{line}'")
                return

            # Validate if the train index is within the valid range
            if train_index < 0 or train_index >= len(self.schedules[line]):
                logger.error(f"Invalid train index {train_index} for {line}")
                return

            # Retrieve the train schedule for the specified line and index
            schedule = self.schedules[line][train_index]
            logger.info(f"Attempting to schedule Train {schedule.train_id} on {line}")

            # Route selection and validation
            if line == "Green Line":
                if not self.green_line_route:
                    logger.error("Green Line route not initialized!")
                    return

                # Validate that the train's stops are valid
                if not self.validate_schedule(schedule):
                    return

                # Use the Green Line route
                route = self.green_line_route

            else:
                route = [stop["block"] for stop in schedule.stops]
                if not route:
                    logger.error("Empty route generated for Red Line train")
                    return

            # First stop validation
            try:
                first_stop = schedule.stops[0]["block"] # Get the first stop block
                first_stop_idx = route.index(first_stop) # Find its index in the route
            except ValueError:
                logger.error(f"First stop {first_stop} not in route")
                return
            except IndexError:
                logger.error("Schedule has no stops")
                return

            # Calculate authority with bounds checking
            auth_segment = route[:first_stop_idx + 1] # Get blocks up to the first stop
            cumulative_auth = 0.0

            logger.debug(f"Processing authority for {len(auth_segment)} blocks")

            # Iterate over the authority segment in reverse order (backtracking from the first stop)
            for blk in reversed(auth_segment):
                # Block number validation
                if not (1 <= blk <= 150):
                    raise ValueError(f"Invalid block number {blk} in route")

                # Fetch block data from the track layout based on the train line
                blk_data = self.green_line_blocks.get(blk) if line == "Green Line" \
                    else next((b for b in self.track_layout[line] if b["block_number"] == blk), None)

                if not blk_data:
                    raise ValueError(f"Missing data for block {blk}")
                if "block_length" not in blk_data:
                    raise ValueError(f"Block {blk} missing length data")

                # Accumulate the total authority distance
                cumulative_auth += float(blk_data["block_length"])

                # update authority
                if 0 <= (blk - 1) < 150:
                    self.ctc.block_authority[blk - 1] = cumulative_auth
                else:
                    raise IndexError(f"Authority index out of bounds for block {blk}")

            # Train initialization
            train = Train(
                train_id=schedule.train_id,
                line=line,
                route_blocks=route,
                authority=cumulative_auth
            )
            self.active_trains.append(train)  # Add the train to active train list

            # Set the initial occupancy of the train at the starting block
            if route and 1 <= route[0] <= 150:
                self.ctc.block_occupancy[route[0] - 1] = True
                logger.info(f"Train {schedule.train_id} occupied block {route[0]}")
            else:
                logger.error("Invalid starting block for train occupation")

            logger.info(f"Successfully scheduled Train {schedule.train_id} on {line}")

        except Exception as e:
            logger.error(f"Failed to schedule train: {str(e)}", exc_info=True)
            # error handling
            if "blk" in locals():
                logger.error(f"Failure occurred at block {blk} during authority calculation")

    def update_trains(self):

        for train in self.active_trains[:]:  # Iterate over copy for safe removal
            current_idx = train.current_route_index # Get the train's current index in its route

            # Check if the train has reached the last block in its route
            if current_idx >= len(train.route_blocks) - 1:
                self._remove_train(train) # Remove train from active list
                continue

            # Identify the current block and the next block in the route
            current_block = train.route_blocks[current_idx]
            next_block = train.route_blocks[current_idx + 1]

            # Check movement conditions
            if (self.ctc.block_authority[next_block - 1] > 0 and  # Check if train has movement authority
                    not self.ctc.block_occupancy[next_block - 1] and # Ensure the next block is unoccupied
                    not self.ctc.maintenance[next_block - 1]):  # Ensure the next block is not under maintenance

                # Move train
                self.ctc.block_occupancy[current_block - 1] = False # Mark current block as unoccupied
                train.current_route_index += 1 # Increment train's position in the route
                self.ctc.block_occupancy[next_block - 1] = True  # Mark next block as occupied
                logger.debug(f"Train {train.train_id} moved to block {next_block}")

                # Update authority
                try:
                    blk_data = self.green_line_blocks[next_block]  # Retrieve data for the next block
                    train.authority -= blk_data['block_length'] # Reduce authority by block length
                except KeyError:
                    logger.error(f"Missing data for block {next_block}")

            # Check for final block
            if train.current_route_index >= len(train.route_blocks) - 1:
                self._remove_train(train) # Remove train if it has completed its route

    def _remove_train(self, train: Train):

        final_block = train.route_blocks[-1]  # Get the last block in the train's route
        self.ctc.block_occupancy[final_block - 1] = False  # Mark the final block as unoccupied
        self.active_trains.remove(train)  # Remove the train from the active trains list

        logger.info(f"Train {train.train_id} completed route")  # Log completion

    def update_maintenance(self, maintenance: List[bool]):

        if len(maintenance) != 150:
            raise ValueError("Maintenance array must be length 150")

        self.ctc.maintenance = maintenance.copy()  # Store maintenance status in the CTC system
        for i in range(150):
            if maintenance[i]:
                self.ctc.block_authority[i] = 0 # Set authority to 0, preventing train movement

    def update(self):

        self.update_trains() #update whole train system