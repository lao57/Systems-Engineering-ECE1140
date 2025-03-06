import pandas as pd
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ScheduleEntry:
    train_id: int
    stops: list  # each => { "block": int, "time": datetime.time }
    line: str

class ScheduleLoader:
    def __init__(self, track_layout):
        self.track_layout = track_layout
        self.station_map = self._build_station_map()

    def _build_station_map(self):
        station_map = {}
        for line_blocks in self.track_layout.values():
            for block in line_blocks:
                infra = block.get('infrastructure', '')
                if infra and 'STATION' in infra.upper():
                    parts = infra.split(':', 1)
                    if len(parts) == 2:
                        after_colon = parts[1].strip()
                        station_name = after_colon.split(';', 1)[0].strip().upper()
                        station_map[station_name] = block['block_number']
        return station_map

    def load_from_excel(self, schedule_file):

        schedules = {'Green Line': [], 'Red Line': []}
        for line_name in schedules.keys():
            sheet = f"{line_name} Scheduling"
            try:
                df = pd.read_excel(schedule_file, sheet_name=sheet)
                line_entries = []
                for _, row in df.iterrows():
                    entry = self._parse_row(row, line_name)
                    line_entries.append(entry)
                schedules[line_name] = line_entries
            except Exception as e:
                print(f"Error loading {line_name} schedule: {e}")
        return schedules

    def _parse_row(self, row, line_name):
        train_id = int(row['Train ID'])

        # Force 'Stops' to string
        stops_val = row['Stops']
        stops_str = str(stops_val).strip()

        # Force 'expected_arrival_times' to string
        times_val = row['expected_arrival_times']
        times_str = str(times_val).strip()

        stops_data = self._parse_stops(stops_str, times_str)
        return ScheduleEntry(train_id, stops_data, line_name)

    def _parse_stops(self, stops_str, times_str):
        stop_list = stops_str.split(',')
        time_list = times_str.split(',')
        if len(stop_list) != len(time_list):
            raise ValueError("Mismatch in # of stops vs # of times")

        stops = []
        for sraw, tstr in zip(stop_list, time_list):
            station_name = sraw.strip()
            t_clean = tstr.strip()

            # parse the time with fallback
            dt_time = self._convert_time_str(t_clean)

            # find block number from station map
            block_num = self.station_map.get(station_name.upper())
            if not block_num:
                # if numeric
                try:
                    block_num = int(station_name)
                except ValueError:
                    raise ValueError(f"Invalid stop: {station_name}")

            stops.append({
                "block": block_num,
                "time": dt_time
            })
        return stops

    def _convert_time_str(self, t_str):

        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(t_str, fmt).time()
            except ValueError:
                pass
        # if all fail, raise an error
        raise ValueError(f"Could not parse time: {t_str}")
