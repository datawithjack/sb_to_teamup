import json
import time
import requests
from dotenv import load_dotenv
import os

# ─── Load environment (BASE_URL, CALENDAR_KEY, HEADERS) ────────────────────────
load_dotenv(override=True)
BASE_URL     =  "https://api.teamup.com"       # e.g. "https://api.teamup.com"
CALENDAR_KEY = os.getenv("TEAMUP_CALENDAR_KEY")


# HEADERS needs at least your Teamup token + content type
HEADERS = {
    "Teamup-Token": os.getenv("TEAMUP_TOKEN"),
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": os.getenv("AUTHORIZATION_KEY")
}

# ─── Your helper from before ───────────────────────────────────────────────────

def add_event_to_sub_calendar(payload):
    url = f"{BASE_URL}/{CALENDAR_KEY}/events"
    resp = requests.post(url, json=payload, headers=HEADERS)
    if not resp.ok:
        print(f"[ERROR {resp.status_code}] {payload['title']} @ {payload['start_dt']}")
        print("→", resp.text)
        resp.raise_for_status()
    return resp.json()

# ─── Main push loop ────────────────────────────────────────────────────────────

def main():
    with open("converted.json", "r", encoding="utf-8") as f:
        events = json.load(f)

    for ev in events:
        try:
            created = add_event_to_sub_calendar(ev)
            print(f"[OK]   Created: {ev['title']} @ {ev['start_dt']}")
        except Exception as err:
            print(f"[FAIL] {ev['title']}  — {err}")
        # be kind to the API:
        time.sleep(0.2)

if __name__ == "__main__":
    main()
