import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import json
import hashlib
import time
from utils.sb_functions import convert_to_time
from utils.teamup_functions import (
    list_all_subcalendars,
    list_training_group_subcalendars,
    list_venue_subcalendars,
    parse_iso,
    make_version,
    add_event_to_sub_calendar
)

### Overview ###

# Step 1: Get SB data
# Step 2: Merge on sub calendar
# Step 3: Push to Team Up

# ─── DATE RANGE ─────────────────────────────────────────────────────────────
# (adjust to whatever window you need)
start_date = datetime(2025, 5, 11).date()
end_date   = datetime(2025, 12, 31).date()

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
venue_list = [
    "Basement Track", "Blue Ice", "Fencing Hall", "Gym A", "Gym B", "Gym C",
    "Indoor Track", "Khalifa Stadium", "MPH 1", "Outdoor Throws", "Outdoor Track",
    "PadelIN", "Physiology Lab", "Sand Court", "Sport Psychology Suite Common Area",
    "Squash Courts", "Swimming Pool", "Table Tennis Hall", "MPH 2",
    "Aspire Park", "Federation", "FPC Pitch","_MISSING"
]

groups_to_remove = ["Jumps_Linus", "Jumps_Pawel", "Decathlon_Willem","Endurance_Driss","Endurance_Kada","Endurance_Khamis","Sprints_Francis","Sprints_Yasmani","Sprints_Rafal","Throws_Keida","Throws_Krzysztof"]

df = (
    data
    .drop(columns=['About', 'by', 'Academic Year', 'Day AM/PM', 'AM/PM', 'Day', 'Date Reverse'], errors='ignore')
    .drop_duplicates()
    .rename(columns=lambda c: c.strip().replace(' ', '_'))
)
# Strip spaces and standardize case just in case
df['Training_Group'] = df['Training_Group'].astype(str).str.strip()
df = df[~df['Training_Group'].isin(groups_to_remove)]

# Parse dates
df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True).dt.date

# Restrict to your window
df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# Convert times
df['Start_Time']  = pd.to_numeric(df['Start_Time'],  errors='coerce').apply(convert_to_time)
df['Finish_Time'] = pd.to_numeric(df['Finish_Time'], errors='coerce').apply(convert_to_time)

# Filter out unwanted rows
df = df[
    df['Sport'].notna() 
    & (df['Sport'].str.strip() != '') 
    & (df['Venue'] != 'AASMC') 
    & (df['Sport'] != 'Generic_Athlete') 
    & (df['Training_Group'] != 'Practice')
]




# Fill NA text fields
df['Session_Type'] = df['Session_Type'].fillna('').astype(str)

# Venue clean-up
df['Venue'] = df['Venue'].fillna('_MISSING')
df['Venue'] = df['Venue'].apply(lambda v: v if v in venue_list else '_OTHER')

# Output
# df.to_csv('invetsigate_group_structure.csv', index=False)

# ─── GET SUB CALENDAR INFO ─────────────────────────────

# Get Authorization token ──────────────────────────────────────────────────────────
load_dotenv(override=True)
API_TOKEN    = os.getenv("TEAMUP_TOKEN")         # ← calendar API key
CALENDAR_KEY = os.getenv("TEAMUP_CALENDAR_KEY")  # ← e.g. "oahota"

# 2) log in to get your user token
auth_resp = requests.post(
    "https://api.teamup.com/auth/tokens",
    headers={
        "Teamup-Token": API_TOKEN,
        "Content-Type":  "application/json",
        "Accept":        "application/json"
    },
    json={
        "app_name":  "My awesome new app",
        "device_id": "Jacks Laptop",
        "email":     "Alessandra.moretti@aspire.qa",
        "password":  "Aspire2025"
    }
)
auth_resp.raise_for_status()
user_token = auth_resp.json().get("auth_token")   # ← this is your Bearer token
print("▶︎ User token:", user_token)
# ─────────────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://api.teamup.com"
HEADERS  = {
    "Teamup-Token":  API_TOKEN,
    "Content-Type":  "application/json",
    "Authorization": f"Bearer {user_token}"
}

# ─── 1) Fetch subcalendar list & build lookup by Training Group ──────────────
tg_subcals = list_training_group_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS)
lookup = {}
for rec in tg_subcals:
    tg  = rec["Training Group"]
    sid = rec["id"]
    if tg:
        lookup.setdefault(tg, []).append(sid)


# ─── Build JSON for by training group ───────────────────────────────
TZ_OFFSET = "+03:00"
TZ_NAME   = "Asia/Riyadh"
# df = pd.read_csv("test_sb_export_via_excel.csv")
tg_out = []
for _, row in df.iterrows():
    tg           = row["Training_Group"]
    session_type = row["Session_Type"] or ""
    venue        = row["Venue"] or ""
    subs         = lookup.get(tg, [])
    subcal_id    = subs[0] if subs else None

    # construct title exactly like your sample
    title = f"{session_type} – {tg}" if session_type else tg

    start_iso = parse_iso(row["Date"],       row["Start_Time"])
    end_iso   = parse_iso(row["Date"],       row["Finish_Time"])

    rec = {
        "subcalendar_id":  subcal_id,
        "subcalendar_ids": subs,
        "start_dt":        start_iso,
        "end_dt":          end_iso,
        "all_day":         False,
        "title":           title,
        "location":        venue,
        "version":         make_version(subcal_id, start_iso, end_iso),
        "readonly":        False,
        "tz":              TZ_NAME,
        "attachments":     []
    }
    tg_out.append(rec)

    # write out in the same shape as converted.json
    with open("NEW_Converted_from_csv.json", "w", encoding="utf-8") as f:
        json.dump(tg_out, f, indent=4, ensure_ascii=False)

    print(f"Converted {len(tg_out)} events → converted_from_csv.json")


# ─── PUSH TG EVENTS TO CALENDAR ─────────────────────────────
for ev in tg_out:

    try:
        created = add_event_to_sub_calendar(BASE_URL, CALENDAR_KEY, HEADERS, ev)
        print(f"[OK]   Created: {ev['title']} @ {ev['start_dt']}")
    except Exception as err:
        print(f"[FAIL] {ev['title']}  — {err}")
    # be kind to the API:
    time.sleep(0.2)

# ─── Build JSON for by venue ────────────────────────────
#df = pd.read_csv("test_sb_export_via_excel.csv")
ven_subcals = list_venue_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS)
lookup = {}
for rec in ven_subcals:
    ven  = rec["Venue"]
    sid = rec["id"]
    if ven:
        lookup.setdefault(ven, []).append(sid)


ven_out = []
for _, row in df.iterrows():
    ven           = row["Venue"]
    tg            = row["Training_Group"]
    session_type = row["Session_Type"] or ""
    venue        = row["Venue"] or ""
    subs         = lookup.get(ven, [])
    subcal_id    = subs[0] if subs else None

    # construct title exactly like your sample
    title = f"{tg} - {session_type}" if session_type else tg

    start_iso = parse_iso(row["Date"],       row["Start_Time"])
    end_iso   = parse_iso(row["Date"],       row["Finish_Time"])

    rec = {
        "subcalendar_id":  subcal_id,
        "subcalendar_ids": subs,
        "start_dt":        start_iso,
        "end_dt":          end_iso,
        "all_day":         False,
        "title":           title,
        "location":        venue,
        "version":         make_version(subcal_id, start_iso, end_iso),
        "readonly":        False,
        "tz":              TZ_NAME,
        "attachments":     []
    }
    ven_out.append(rec)

    # write out in the same shape as converted.json
    with open("NEW_VENUE_Converted_from_csv.json", "w", encoding="utf-8") as f:
        json.dump(ven_out, f, indent=4, ensure_ascii=False)

    print(f"Converted {len(ven_out)} events → converted_from_csv.json")

# ─── PUSH VENUE EVENTS TO CALENDAR ─────────────────────────────
for ev in ven_out:

    try:
        created = add_event_to_sub_calendar(BASE_URL, CALENDAR_KEY, HEADERS, ev)
        print(f"[OK]   Created: {ev['title']} @ {ev['start_dt']}")
    except Exception as err:
        print(f"[FAIL] {ev['title']}  — {err}")
    # be kind to the API:
    time.sleep(0.2)

