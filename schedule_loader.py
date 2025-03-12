import pandas as pd
from datetime import datetime
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class ScheduleEntry:
    train_id: int
    stops: list
    line: str


class ScheduleLoader:


    def __init__(self, track_layout):
        self.track_layout = track_layout
        self.station_map = self._build_station_map()
        self.yard_blocks = {'Green Line': 62, 'Red Line': 75}

    def _build_station_map(self) -> dict:
        """Map station names to block numbers across all lines"""
        station_map = {}
        for line, blocks in self.track_layout.items():
            line_map = {}
            for blk in blocks:
                if 'STATION' in blk['infrastructure']:
                    # Extract station name
                    match = re.search(r'STATION[:\s]+([^;]+)', blk['infrastructure'])
                    if match:
                        name = match.group(1).strip().upper()
                        line_map[name] = blk['block_number']
            station_map[line] = line_map
        return station_map

    def load_from_excel(self, path: str) -> dict:

        schedules = {}
        for line in ['Green Line', 'Red Line']:
            try:
                df = pd.read_excel(
                    path,
                    sheet_name=f"{line} Scheduling",
                    usecols=['Train ID', 'Stops', 'expected_arrival_times']
                ).dropna(subset=['Stops'])

                line_schedules = []
                for idx, row in df.iterrows():
                    try:
                        entry = self._parse_row(row, line, idx + 2)
                        line_schedules.append(entry)
                    except Exception as e:
                        logger.error(f"Row {idx + 2} error: {str(e)}")

                schedules[line] = line_schedules
                logger.info(f"Loaded {len(line_schedules)} {line} schedules")

            except Exception as e:
                logger.error(f"Error loading {line} schedules: {str(e)}")
                schedules[line] = []

        return schedules

    def _parse_row(self, row, line: str, row_num: int) -> ScheduleEntry:

        # Validate input format
        stops = str(row['Stops']).strip().upper()
        times = str(row['expected_arrival_times']).strip() if pd.notna(row['expected_arrival_times']) else ''

        # Split and validate components
        stop_list = [s.strip() for s in re.split(r'\s*,\s*', stops) if s]
        time_list = [t.strip() for t in re.split(r'\s*,\s*', times) if t]

        if len(stop_list) != len(time_list):
            raise ValueError(f"{len(stop_list)} stops but {len(time_list)} times")
        if not stop_list:
            raise ValueError("At least one stop required")

        # Convert to block numbers
        stops = []
        for station, time_str in zip(stop_list, time_list):
            # Handle yard specially
            if station == 'YARD':
                block = self.yard_blocks[line]
            else:
                # Try numeric block first
                try:
                    block = int(station)
                    if not any(blk['block_number'] == block for blk in self.track_layout[line]):
                        raise ValueError(f"Invalid block number: {block}")
                except ValueError:
                    # Look up station name
                    block = self.station_map[line].get(station.upper())
                    if not block:
                        valid = ', '.join(self.station_map[line].keys())
                        raise ValueError(f"Unknown station '{station}'. Valid: {valid}")

            # Parse time
            try:
                time_obj = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                raise ValueError(f"Invalid time format: '{time_str}'")

            stops.append({'block': block, 'time': time_obj})

        return ScheduleEntry(
            train_id=int(row['Train ID']),
            stops=stops,
            line=line
        )