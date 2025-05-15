# ─── Team Up FUNCTIONS ───────────────────────────────────────────────────
from datetime import datetime
import requests
import hashlib


def list_all_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS):
    url = f"{BASE_URL}/{CALENDAR_KEY}/subcalendars"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()

    subs = resp.json().get("subcalendars", [])
    result = []
    for sc in subs:
        name = sc.get("name", "")

        result.append({
            "id": sc["id"],
            "name": name
        })
    return result

def list_training_group_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS):
    url = f"{BASE_URL}/{CALENDAR_KEY}/subcalendars"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    subs = resp.json().get("subcalendars", [])
    result = []
    for sc in subs:
        name = sc.get("name", "")
        # your naming convention: e.g. "Sport > Endurance_Driss"
        if name.startswith("Sport >"):
            tg = name.rsplit(">", 1)[1].strip()
        else:
            tg = None
        result.append({
            "id": sc["id"],
            "Training Group": tg
        })
    return result


def list_venue_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS):
    url = f"{BASE_URL}/{CALENDAR_KEY}/subcalendars"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    subs = resp.json().get("subcalendars", [])
    result = []
    for sc in subs:
        name = sc.get("name", "")
        # your naming convention: e.g. "Venue > Gym A"
        if name.startswith("Venue >"):
            tg = name.rsplit(">", 1)[1].strip()
        else:
            tg = None
        result.append({
            "id": sc["id"],
            "Venue": tg
        })
    return result


def parse_iso(date_str: str, time_str: str) -> str:
    TZ_OFFSET = "+03:00"
    TZ_NAME   = "Asia/Riyadh"
    # date_str like "2025-05-10", time_str like "16:30"
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S{TZ_OFFSET}")

def make_version(subcal_id, start_iso, end_iso) -> str:
    s = f"{subcal_id}|{start_iso}|{end_iso}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def add_event_to_sub_calendar(base_url, calendar_key, headers, payload):
    url = f"{base_url}/{calendar_key}/events"
    resp = requests.post(url, json=payload, headers=headers)

    if not resp.ok:
        print(f"[ERROR {resp.status_code}] {payload.get('title')} @ {payload.get('start_dt')}")
        print("→", resp.text)
        resp.raise_for_status()

    return resp.json()

def delete_subcalendar(BASE_URL, CALENDAR_KEY, HEADERS, sub_id):
    url = f"{BASE_URL}/{CALENDAR_KEY}/subcalendars/{sub_id}"
    resp = requests.delete(url, headers=HEADERS)
    # Teamup returns 204 No Content on success
    if resp.status_code == 204:
        print(f"✅ Deleted sub-calendar {sub_id}")
    else:
        print(f"❌ Failed to delete {sub_id}: {resp.status_code} {resp.text}")
