# ─── SMARTABASE FUNCTIONS ───────────────────────────────────────────────────
import pandas as pd
from datetime import datetime, timedelta, timezone

# ─── SB Cleaning Functions ───────────────────────────────────────────────────
def convert_to_time(timestamp_ms, offset_hours=12):
    """Convert a ms‐since‐epoch timestamp to local HH:MM, shifting by offset_hours."""
    # handle lists/Series recursively
    if isinstance(timestamp_ms, (pd.Series, list, tuple)):
        return [convert_to_time(x, offset_hours) for x in timestamp_ms]
    try:
        if pd.notnull(timestamp_ms):
            ts_sec = float(timestamp_ms) / 1000.0
            # from UTC, subtract offset to get local
            local_dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc) - timedelta(hours=offset_hours)
            return local_dt.strftime('%H:%M')
    except Exception as e:
        print(f"Error converting timestamp {timestamp_ms!r}: {e}")
    return None