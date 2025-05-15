import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta, timezone



# ─── DATE RANGE ─────────────────────────────────────────────────────────────
# (adjust to whatever window you need)
start_date = datetime(2025, 5, 1).date()
end_date   = datetime(2025, 5, 10).date()

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

# ─── Fetch & parse ──────────────────────────────────────────────────────────
session = requests.Session()
session.auth = ("sb_sap.etl", "A1s2p3!re")

url = (
    "https://aspire.smartabase.com/aspireacademy/live"
    "?report=PYTHON6_TRAINING_PLAN&updategroup=true"
)
response = session.get(url)
response.raise_for_status()

# read first HTML table
tables = pd.read_html(response.text)
if not tables:
    raise ValueError("No HTML tables found in the response")
data = tables[0]

# ─── Clean up ───────────────────────────────────────────────────────────────
df = (
    data
    .drop(columns=['About', 'by', 'Academic Year', 'Day AM/PM', 'AM/PM', 'Day', 'Date Reverse'], errors='ignore')
    .drop_duplicates()
    .rename(columns=lambda c: c.strip().replace(' ', '_'))
)

# convert times
df['Start_Time']  = pd.to_numeric(df['Start_Time'],  errors='coerce').apply(convert_to_time)
df['Finish_Time'] = pd.to_numeric(df['Finish_Time'], errors='coerce').apply(convert_to_time)

# filter out unwanted rows
df = df[
      df['Sport'].notna() 
    & (df['Sport'].str.strip() != '') 
    & (df['Venue'] != 'AASMC') 
    & (df['Sport'] != 'Generic_Athlete') 
    & (df['Training_Group'] != 'Practice')
]

# parse dates
df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True).dt.date

# restrict to your window
filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# fill NA text fields
for col in ['Session_Type']:
    filtered_df[col] = filtered_df[col].fillna('').astype(str)

# merge on sub calendar structure 

COMPLETE THIS SECTION

# ─── OUTPUT ────────────────────────────────────────────────────────────────
print(filtered_df.head())
filtered_df.to_csv("test_sb_export_via_excel.csv", index=False)
