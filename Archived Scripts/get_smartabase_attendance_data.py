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
user_ids = [29155] #, 29019, 29018
]

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

    # 2) normalize to flat records
    records = extract_records(combined_data)
    df = pd.DataFrame(records)
    df["startdate"]  = pd.to_datetime(df["startdate"], dayfirst=True)
    df["finishdate"] = pd.to_datetime(df["finishdate"], dayfirst=True)

    # 2) Parse your filter dates (dd/mm/YYYY)
    start_date  = "20/04/2025"
    finish_date = "25/04/2025"

    start_dt  = pd.to_datetime(start_date,  format="%d/%m/%Y")
    finish_dt = pd.to_datetime(finish_date, format="%d/%m/%Y")

    # 3a) If you want **exact** equality on both fields:
    mask_exact = (df["startdate"]  == start_dt) & \
                (df["finishdate"] == finish_dt)
    filtered_exact = df.loc[mask_exact]

    # 3b) If you actually meant “between” (inclusive):
    mask_range = (df["startdate"]  >= start_dt) & \
                (df["finishdate"] <= finish_dt)
    filtered_range = df.loc[mask_range]

    # 4) save to CSV
    csv_path = os.path.join(json_folder, f"{form}_data.csv")
    filtered_range.to_csv(csv_path, index=False)
    print(f"Formatted CSV for form '{form}' saved to {csv_path}")

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

