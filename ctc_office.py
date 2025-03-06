import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ScheduleEntry:
    train_id: int
    stops: List[Dict]  # List of stop dictionaries ({block: X, time: Y})
    line: str


@dataclass
class Train:
    train_id: int
    line: str
    schedule_entry: ScheduleEntry
    route_blocks: List[int]
    current_route_index: int = 0
    authority_remaining: float = 0.0
    departed: bool = False

    @property
    def current_block(self):
        if self.current_route_index < len(self.route_blocks):
            return self.route_blocks[self.current_route_index]
        return None


class CTCOffice:
    def __init__(self, track_layout: Dict, schedules: Dict[str, List[ScheduleEntry]]):
        self.track_layout = track_layout
        self.schedules = schedules
        self.ctc = None
        self.block_length_map = self._build_block_length_map()
        self.yard_blocks = self._detect_yard_blocks()
        self.active_trains: List[Train] = []

    def _build_block_length_map(self) -> Dict[int, float]:
        return {
            blk['block_number']: blk['block_length']
            for line in self.track_layout.values()
            for blk in line if 1 <= blk['block_number'] <= 150 
        }

    def _detect_yard_blocks(self) -> Dict[str, int]:
        yards = {}
        for line in ['Green Line', 'Red Line']:
            for blk in self.track_layout.get(line, []):
                if 1 <= blk['block_number'] <= 150 and 'YARD' in str(blk.get('infrastructure', '')).upper():
                    yards[line] = blk['block_number']
                    break
            else:
                raise ValueError(f"No valid yard block (1-150) found in {line}")
        return yards

    def set_ctc(self, ctc):
        self.ctc = ctc

    def schedule_train(self, line: str = 'Green Line', train_index: int = 0):
        try:
            if line not in self.schedules:
                logger.warning(f"No schedules for {line}")
                return

            line_schedule = self.schedules[line]
            if train_index >= len(line_schedule):
                logger.warning(f"Invalid index {train_index} for {line}")
                return

            entry = line_schedule[train_index]
            if not entry.stops:
                logger.warning(f"Train {entry.train_id} has no stops")
                return

            yard_block = self.yard_blocks[line]
            first_stop_block = entry.stops[0]['block']

            if first_stop_block == yard_block:
                logger.error("First stop cannot be yard block")
                return

            distance, route_blocks = self._calculate_distance(yard_block, first_stop_block)

            # Set authority on yard block
            if self.ctc:
                yard_idx = yard_block - 1
                if 0 <= yard_idx < 150:
                    self.ctc.block_authority[yard_idx] = distance
                else:
                    raise ValueError(f"Invalid yard block index {yard_idx}")

            # Create and track train
            train = Train(
                train_id=entry.train_id,
                line=line,
                schedule_entry=entry,
                route_blocks=route_blocks,
                authority_remaining=distance
            )

            # Update occupancy
            if self.ctc and 0 <= yard_idx < 150:
                self.ctc.actual_occupancy[yard_idx] = True
                self.ctc._update_block_occupancy()

            self.active_trains.append(train)
            logger.info(f"Scheduled {entry.train_id} on {line}, Authority: {distance}m")

        except Exception as e:
            logger.error(f"Scheduling error: {str(e)}")
            raise

    def _calculate_distance(self, start: int, end: int) -> Tuple[float, List[int]]:
        if not (1 <= start <= 150) or not (1 <= end <= 150):
            raise ValueError(f"Block numbers must be 1-150 (got {start}->{end})")

        # Validate block existence
        missing = [b for b in [start, end] if b not in self.block_length_map]
        if missing:
            raise ValueError(f"Missing block data for: {missing}")

        direction = 1 if start <= end else -1
        blocks = list(range(start, end + direction, direction))

        # Validate all route blocks
        invalid_blocks = [b for b in blocks if b not in self.block_length_map]
        if invalid_blocks:
            raise ValueError(f"Invalid blocks in route: {invalid_blocks}")

        total_distance = sum(self.block_length_map[b] for b in blocks)
        return round(total_distance, 2), blocks

    def update_trains(self):
        if not self.ctc:
            logger.warning("CTC not connected")
            return

        for train in self.active_trains[:]:
            if train.authority_remaining <= 0:
                continue

            current_block = train.current_block
            if current_block is None:
                continue

            next_index = train.current_route_index + 1
            if next_index >= len(train.route_blocks):
                continue

            next_block = train.route_blocks[next_index]
            if self.ctc.block_occupancy[next_block - 1]:
                continue

            current_length = self.block_length_map.get(current_block, 0.0)
            if train.authority_remaining < current_length:
                continue

            train.authority_remaining -= current_length
            self.ctc.actual_occupancy[current_block - 1] = False
            self.ctc.actual_occupancy[next_block - 1] = True
            self.ctc._update_block_occupancy()
            train.current_route_index = next_index
            logger.info(f"Train {train.train_id} moved to block {next_block}")

    def get_maintenance_status(self):
        return self.ctc.maintenance if self.ctc else []

    def get_block_authority(self):
        return self.ctc.block_authority if self.ctc else []