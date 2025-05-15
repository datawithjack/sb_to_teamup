###################################################################################################
### MERGE ON SUB CALENDAR ID  INFO ################################################################  

from dotenv import load_dotenv
import os
import requests
import json

load_dotenv(override=True)  # reads .env into os.environ

# ——— Configuration ———
API_TOKEN     = os.getenv("TEAMUP_TOKEN")
CALENDAR_KEY  = os.getenv("TEAMUP_CALENDAR_KEY")
AUTHORIZATION_KEY = os.getenv("AUTHORIZATION_KEY")

BASE_URL      = "https://api.teamup.com"
HEADERS       = {
    "Teamup-Token": API_TOKEN,
    "Content-Type": "application/json",
    "Authorization": AUTHORIZATION_KEY
}

# Get sub calendar structure and ids
def list_subcalendars():
    url = f"{BASE_URL}/{CALENDAR_KEY}/subcalendars"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()

    subs = resp.json().get("subcalendars", [])
    result = []
    for sc in subs:
        name = sc.get("name", "")
        if name.startswith("Sport >"):
            training_group = name.rsplit(">", 1)[1].strip()
        else:
            training_group = None

        result.append({
            "id": sc["id"],
            "name": name,
            "Training Group": training_group
        })
    return result

# load your two files
with open("json_files/Attendance and Training Plan_data.json") as f1:
       # list of dicts from your Attendance file
    data1 = json.load(f1)

# 2) Build a lookup from data2 by Training Group, but only store the IDs
sub_calendar_ids = list_subcalendars() 
lookup = {}
for rec in sub_calendar_ids:
    tg = rec.get("Training Group")
    sid = rec.get("id")
    if tg and sid is not None:
        lookup.setdefault(tg, []).append(sid)

# 3) Merge: for each rec in data1, add a 'subcalendar_ids' list
merged = []
for rec in data1:
    tg = rec.get("Training Group")
    matched_ids = lookup.get(tg, [])
    # copy original record and inject the matching IDs
    merged_rec = rec.copy()
    merged_rec["subcalendar_ids"] = matched_ids
    merged.append(merged_rec)

###################################################################################################
### FORMAT READY FOR ADD TO CALENDAR FUNCTION 

import json
import hashlib
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

INPUT_FILE  = "merged.json"
OUTPUT_FILE = "converted.json"
# all events use fixed +03:00 offset and Asia/Riyadh tz label
TZ_OFFSET = "+03:00"
TZ_NAME   = "Asia/Riyadh"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def parse_iso(dt_str: str, tm_str: str) -> str:
    """
    Parse date in DD/MM/YYYY and time in h:mm AM/PM,
    return ISO-8601 string with fixed +03:00 offset.
    """
    dt = datetime.strptime(f"{dt_str} {tm_str}", "%d/%m/%Y %I:%M %p")
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S{TZ_OFFSET}")

def make_version(subcal_id, start_iso, end_iso) -> str:
    """
    Create a stable version hash for each event based on
    its key fields.
    """
    s = f"{subcal_id}|{start_iso}|{end_iso}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()

# ─── Main Conversion ──────────────────────────────────────────────────────────

def main():
    # with open(INPUT_FILE, "r", encoding="utf-8") as f:
    #     events = json.load(f)
    events = merged
    out_events = []
    for ev in events:
        # source fields
        venue          = ev.get("Venue", "") or ""
        training_grp   = ev.get("Training Group", "") or ""
        session_type   = ev.get("Session Type") or ""
        subs           = ev.get("subcalendar_ids", [])
        subcal_id      = subs[0] if subs else None

        # build title
        if session_type:
            title = f"{session_type} – {training_grp}"
        else:
            title = training_grp

        # parse start/end datetimes
        start_iso = parse_iso(ev.get("startdate",""), ev.get("starttime",""))
        end_iso   = parse_iso(ev.get("finishdate",""), ev.get("finishtime",""))

        # assemble output record
        rec = {
            "subcalendar_id": subcal_id,
            "subcalendar_ids": subs,
            "start_dt":       start_iso,
            "end_dt":         end_iso,
            "all_day":        False,
            "title":          title,
            "location":       venue,
            "version":        make_version(subcal_id, start_iso, end_iso),
            "readonly":       False,
            "tz":             TZ_NAME,
            "attachments":    []
        }
        out_events.append(rec)

    # write result
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out_events, f, indent=4, ensure_ascii=False)

    print(f"Converted {len(out_events)} events → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()


###################################################################################################

### NEED TO REMOVE DUPLCIATES #####################################################################

###################################################################################################


