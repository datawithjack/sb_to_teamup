import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_fixed
from time import time
import pandas as pd

# Step 1: Define folder paths for JSON files
json_folder = "json_files"
os.makedirs(json_folder, exist_ok=True)


from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(override=True)

# Configuration
JSON_FOLDER = "json_files"
os.makedirs(JSON_FOLDER, exist_ok=True)


# Headers: AUTHORIZATION and COOKIE loaded from environment variables
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-APP-ID': os.getenv('APP_ID', 'internal.testing.postman'),
    'Authorization': os.getenv('SB_AUTHORIZATION'),
    'Cookie': os.getenv('COOKIE')
}


# Step 2: Get All SB User IDs
url_users = "https://aspire.smartabase.com/aspireacademy/api/v1/usersynchronise?informat=json&format=json"
payload_users = json.dumps({"lastSynchronisationTimeOnServer": 0, "userIds": []})

headers = {
    'X-APP-ID': 'internal.testing.postman',
    #'Content-Type': 'text/plain',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic c2Jfc2FwLmV0bDpBMXMycDMhcmU=',
    'Cookie': 'JSESSIONID=UnkQAYeXdo7QgqKNIoU7Xy0S'
}

response = requests.post(url_users, headers=headers, data=payload_users)
user_ids = [user['userId'] for user in response.json().get('users', [])]
print(f"User IDs fetched: {user_ids}")

# Step 3: Define API endpoint for form data
url_forms = "https://aspire.smartabase.com/aspireacademy/api/v1/filteredeventsearch?informat=json&format=json"

### TEST SUBSET OF USERIDS ####
#user_ids = [29155] #, 29019, 29018


# Function to log failures
def log_failure(user_id, form, error_message):
    with open("fetch_failures.log", "a") as log_file:
        log_file.write(f"User: {user_id}, Form: {form}, Error: {error_message}\n")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_data(user_id, form):
    payload = {
        "filter": [
            {
                "formName":  form,
                "filterSet": []     # keep this empty array as per docs
            }
        ],
        "startDate": "20/04/2025",  # <-- dd/MM/yyyy
        "endDate":   "26/04/2025",  # <-- dd/MM/yyyy
        "userIds":   [user_id]
    }

    headers_json = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": headers["Authorization"]
    }

    resp = requests.post(
        url_forms,
        headers=headers_json,
        json=payload,      # <-- json=, not data=
        timeout=(5, 10)
    )

    # — DEBUG: inspect the *filter* request and response —
    req = resp.request
    print("→ FILTER REQUEST headers:", req.headers)
    print("→ FILTER REQUEST body   :", req.body)
    print("→ RESPONSE status       :", resp.status_code)
    print("→ RESPONSE body (200c)  :", resp.text[:200], "…")

    resp.raise_for_status()
    return resp.json().get("events", [])


def extract_records(events):
    records = []
    for ev in events:
        rec = {
            'Venue': None,
            'startdate': ev.get('startDate'),
            'starttime': ev.get('startTime'),
            'finishdate': ev.get('finishDate'),
            'finishtime': ev.get('finishTime'),
            'Training Group': None,
            'Session Type': None,
        }
        pairs = ev.get('rows', [{}])[0].get('pairs', [])
        for pair in pairs:
            key = pair.get('key')
            val = pair.get('value')
            if key in rec:
                rec[key] = val
        records.append(rec)
    return records



# Step 5: Worker function to process a single form
from datetime import datetime
from datetime import datetime, timedelta

def parse_event_date(dt_str: str) -> datetime:
    """
    Parse either an ISO timestamp (e.g. "2025-04-20T08:00:00")
    or a dd/MM/yyyy date (e.g. "03/09/2023").
    """
    # trim any Zulu suffix for ISO
    s = dt_str.rstrip("Z")
    # crude check for dd/MM/yyyy
    if "/" in s:
        return datetime.strptime(s, "%d/%m/%Y")
    else:
        return datetime.fromisoformat(s)

def process_form(form):
    combined_data = []
    # 1) fetch all users’ raw event dicts in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_data, user_id, form) for user_id in user_ids]
        for future in futures:
            try:
                combined_data.extend(future.result())
            except Exception as e:
                print(f"Skipping user due to repeated failures: {e}")

    # ─── NEW: pure-Python JSON date filter ────────────────────────────────
    # get start fo current week
    # assume local time is Qatar
    today = datetime.now()
    days_since_sunday = today.isoweekday() % 7

    # compute this week’s Sunday at midnight
    sunday = (today - timedelta(days=days_since_sunday)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt  = sunday
    #finish_dt = datetime.strptime("25/04/2025", "%d/%m/%Y")

    def parse_iso(dt_str):
        # adjust if your API returns a Z or timezone offset:
        return datetime.fromisoformat(dt_str.rstrip("Z"))

    filtered_events = [
        ev for ev in combined_data
        if (start := parse_event_date(ev.get("startDate", ""))) >= start_dt
        #and (end   := parse_event_date(ev.get("finishDate", ""))) <= finish_dt
    ]

    print(f"{len(filtered_events)} events between {start_dt.date()}")
    records = extract_records(filtered_events)

    # ─── (option B) OR dump the filtered JSON straight back out ───────────
    json_path = os.path.join(json_folder, f"{form}_data.json")
    with open(json_path, "w") as f:
        json.dump(records, f, indent=4)
    print(f"Filtered JSON for form '{form}' saved to {json_path}")


# Step 6: Execute the workflow
def main():
    start_time = time()  # Start timer
    #form_list = ["Student Athlete Profile", "Anthro_Height_Weight", "Attendance and Training Plan"]
    form_list = ["Attendance and Training Plan"]
    for form in form_list:
        print(f"Processing form: {form}")
        process_form(form)
    end_time = time()  # End timer
    elapsed_time = end_time - start_time
    print(f"Total time taken: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()

