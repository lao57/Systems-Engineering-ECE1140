import pandas as pd
from datetime import datetime, time
from dataclasses import dataclass
from track_loader import load_track_layout

@dataclass
class ScheduleEntry:
    train_id: int
    stops: list[dict]  # [{"block": int, "station": str, "arrival_time": time}]
    line: str

class ScheduleLoader:
    def __init__(self, track_layout):
        self.track_layout = track_layout
        self.station_map = self._build_station_map()

    def _build_station_map(self):
        station_map = {}
        for line_name, blocks in self.track_layout.items():
            for block in blocks:
                if block['infrastructure'] and 'STATION' in block['infrastructure']:
                    station_name = block['infrastructure'].split(':')[-1].split(';')[-1].strip()
                    station_map[station_name.upper()] = block['block_number']
        return station_map

    def load_from_excel(self, file_path):
        schedules = {'Red Line': [], 'Green Line': []}

        # Load Red Line schedules
        red_df = pd.read_excel(file_path, sheet_name='Red Line Scheduling')
        red_df.rename(columns=lambda c: c.strip(), inplace=True)
        for _, row in red_df.iterrows():
            if pd.isna(row.get('Train ID')):
                continue
            schedule = self._process_row(row, 'Red Line')
            schedules['Red Line'].append(schedule)

        # Load Green Line schedules
        green_df = pd.read_excel(file_path, sheet_name='Green Line Scheduling')
        green_df.rename(columns=lambda c: c.strip(), inplace=True)
        for _, row in green_df.iterrows():
            if pd.isna(row.get('Train ID')):
                continue
            schedule = self._process_row(row, 'Green Line')
            schedules['Green Line'].append(schedule)

        # --- Debug output to confirm schedules were loaded ---
        for line_name, schedule_list in schedules.items():
            print(f"Loaded {len(schedule_list)} schedules for {line_name}:")
            for sched in schedule_list:
                # Example: list each train's ID and its stops
                stops_str = ", ".join(
                    f"[block={stop['block']}, station={stop['station']}, time={stop['arrival_time']}]"
                    for stop in sched.stops
                )
                print(f"  - Train {sched.train_id}, stops: {stops_str}")
        # ------------------------------------------------------

        return schedules

    def _process_row(self, row, line_type):
        try:
            train_id = int(pd.to_numeric(row['Train ID'], errors='coerce'))
            if pd.isna(train_id):
                raise ValueError("Train ID must be a number")
        except ValueError:
            raise ValueError(f"Invalid Train ID: {row['Train ID']} - must be numeric")

        stops = [s.strip() for s in str(row['Stops']).split(',')]
        times = [t.strip() for t in str(row['expected_arrival_times']).split(',')]

        if len(stops) != len(times):
            raise ValueError(f"Mismatched stops/times for train {train_id}")

        schedule_stops = []
        for stop, time_str in zip(stops, times):
            # Convert to block number if numeric, else match station
            try:
                block = int(stop)
            except ValueError:
                block = self.station_map.get(stop.upper().strip())
                if not block:
                    raise ValueError(f"Unknown station: '{stop}' for train {train_id}")

            # Parse arrival time
            try:
                arrival_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                try:
                    arrival_time = datetime.strptime(time_str, "%H:%M:%S").time()
                except ValueError:
                    raise ValueError(f"Invalid time format: '{time_str}' for train {train_id}")

            schedule_stops.append({
                'block': block,
                'station': None if stop.isdigit() else stop,
                'arrival_time': arrival_time
            })

        return ScheduleEntry(
            train_id=train_id,
            stops=schedule_stops,
            line=line_type
        )
