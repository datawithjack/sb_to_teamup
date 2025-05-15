import os
import json
import time
from datetime import date

import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from dateutil import parser
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(override=True)

# Configuration
JSON_FOLDER = "json_files"
os.makedirs(JSON_FOLDER, exist_ok=True)

URL_USERS = (
    "https://aspire.smartabase.com/aspireacademy/api/v1/"
    "usersynchronise?informat=json&format=json"
)
URL_FORMS = (
    "https://aspire.smartabase.com/aspireacademy/api/v1/"
    "filteredeventsearch?informat=json&format=json"
)

# Headers: AUTHORIZATION and COOKIE loaded from environment variables
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-APP-ID': os.getenv('APP_ID', 'internal.testing.postman'),
    'Authorization': os.getenv('SB_AUTHORIZATION'),
    'Cookie': os.getenv('COOKIE')
}

# Date window for filtering
START_DATE = date(2025, 5, 5)
END_DATE = date(2025, 5, 7)


def log_failure(user_id: int, form: str, error_message: str):
    """Append fetch failures to a log file."""
    with open("fetch_failures.log", "a") as log:
        log.write(f"User: {user_id}, Form: {form}, Error: {error_message}\n")


# def fetch_user_ids() -> list[int]:
#     """Retrieve all Smartabase user IDs for synchronization."""
#     payload = {"lastSynchronisationTimeOnServer": 0, "userIds": []}
#     resp = requests.post(URL_USERS, headers=HEADERS, json=payload)
#     resp.raise_for_status()
#     users = resp.json().get('users', [])
#     return [u.get('userId') for u in users]

users = [29155] # , 29019]

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_data(user_id: int, form: str) -> list[dict]:
    """Fetch events for a given user and form, retrying on failure."""
    payload = {
        "filter": [{"formName": form, "filterSet": []}],
        "startDate": START_DATE.strftime("%d/%m/%Y"),
        "endDate": END_DATE.strftime("%d/%m/%Y"),
        "userIds": [user_id]
    }
    resp = requests.post(URL_FORMS, headers=HEADERS, json=payload, timeout=(5, 10))
    resp.raise_for_status()
    all_events = resp.json().get('events', [])
    # Client-side date filtering
    return [ev for ev in all_events if START_DATE <= parser.isoparse(ev['startDate']).date() <= END_DATE]


def extract_records(events: list[dict]) -> list[dict]:
    """Convert raw event JSON into flat records for DataFrame."""
    records = []
    for ev in events:
        rec = {
            'Venue': None,
            'startDate': ev.get('startDate'),
            'startTime': ev.get('startTime'),
            'finishDate': ev.get('finishDate'),
            'finishTime': ev.get('finishTime'),
            'Training Group': None,
            'Session Type': None,
        }
        for row in ev.get('rows', []):
            for pair in row.get('pairs', []):
                key, val = pair.get('key'), pair.get('value')
                if key in rec:
                    rec[key] = val
        records.append(rec)
    return records


def process_form(form: str, user_ids: list[int]):
    """Fetch, normalize, and save data for a single form."""
    events = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_data, uid, form) for uid in user_ids]
        for future in futures:
            try:
                events.extend(future.result())
            except Exception as e:
                log_failure(None, form, str(e))
    records = extract_records(events)
    df = pd.DataFrame(records).drop_duplicates().reset_index(drop=True)

    csv_path = os.path.join(JSON_FOLDER, f"{form.replace(' ', '_')}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {len(df)} records to {csv_path}")


def main():
    start = time.time()
    # Fetch all user IDs (or override for testing)
    #user_ids = fetch_user_ids()
    user_ids = [29155, 29019]  # For debug/testing only

    forms = [
        "Attendance and Training Plan",
        # Add more form names here
    ]
    for form in forms:
        print(f"Processing form: {form}")
        process_form(form, user_ids)

    elapsed = time.time() - start
    print(f"Done in {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
