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

            if line == 'Green Line':
                if st_up == 'YARD':
                    if i == len(stop_list) - 1:
                        block = self.green_yard_entrance
                    else:
                        block = self.green_yard_exit
                else:

                    try:
                        block = int(st_up)
                        if not any(blk['block_number'] == block for blk in self.track_layout[line]):
                            raise ValueError(f"Invalid block number {block} on {line}.")
                    except ValueError:
                        block = self.station_map[line].get(st_up)
                        if not block:
                            valid_stations = ', '.join(self.station_map[line].keys())
                            raise ValueError(f"Unknown station '{station}'. Valid: {valid_stations}")
            else:

                try:
                    block = int(st_up)
                    if not any(blk['block_number'] == block for blk in self.track_layout[line]):
                        raise ValueError(f"Invalid block number {block} on {line}.")
                except ValueError:
                    block = self.station_map[line].get(st_up)
                    if not block:
                        valid_stations = ', '.join(self.station_map[line].keys())
                        raise ValueError(f"Unknown station '{station}'. Valid: {valid_stations}")

            stops.append({'block': block, 'time': time_obj})

        return ScheduleEntry(train_id=train_id, stops=stops, line=line)
