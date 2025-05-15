import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_fixed
from time import time

# Step 1: Define folder paths for JSON files
json_folder = "json_files"
os.makedirs(json_folder, exist_ok=True)

# Step 2: Get All SB User IDs
url_users = "https://aspire.smartabase.com/aspireacademy/api/v1/usersynchronise?informat=json&format=json"
payload_users = json.dumps({"lastSynchronisationTimeOnServer": 0, "userIds": []})

headers = {
    'X-APP-ID': 'internal.testing.postman',
    'Content-Type': 'text/plain',
    'Authorization': 'Basic c2Jfc2FwLmV0bDpBMXMycDMhcmU=',
    'Cookie': 'JSESSIONID=UnkQAYeXdo7QgqKNIoU7Xy0S'
}

response = requests.post(url_users, headers=headers, data=payload_users)
user_ids = [user['userId'] for user in response.json().get('users', [])]
print(f"User IDs fetched: {user_ids}")

# Step 3: Define API endpoint for form data
url_forms = "https://aspire.smartabase.com/aspireacademy/api/v1/filteredeventsearch?informat=json&format=json"

# Function to log failures
def log_failure(user_id, form, error_message):
    with open("fetch_failures.log", "a") as log_file:
        log_file.write(f"User: {user_id}, Form: {form}, Error: {error_message}\n")

# Step 4: Function to fetch data for a single user and form with retry logic
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))  # Retry up to 3 times, waiting 2 seconds between retries
def fetch_data(user_id, form):
    payload = json.dumps({
        "filter": [{"formName": form}],
        "userIds": [user_id]
    })
    try:
        response = requests.post(url_forms, headers=headers, data=payload, timeout=(5, 10))
        if response.status_code == 200:
            json_data = response.json()
            return json_data.get("events", [])
        else:
            error_message = f"Failed for user {user_id}, form {form}. Status code: {response.status_code}"
            log_failure(user_id, form, error_message)
            print(error_message)
            return []
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        log_failure(user_id, form, error_message)
        print(f"Error fetching data for user {user_id}, form {form}: {error_message}")
        raise

# Step 5: Worker function to process a single form
def process_form(form):
    combined_data = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust `max_workers` based on your system
        futures = [executor.submit(fetch_data, user_id, form) for user_id in user_ids]
        for future in futures:
            try:
                combined_data.extend(future.result())
            except Exception as e:
                print(f"Skipping user due to repeated failures: {e}")
    
    # Save combined data for the form
    
    json_file_path = os.path.join(json_folder, f"{form}_data.json")
    with open(json_file_path, "w") as json_file:
        json.dump({"form": form, "events": combined_data}, json_file, indent=4)
    print(f"Raw JSON data for form '{form}' saved to {json_file_path}")

# Step 6: Execute the workflow
def main():
    start_time = time()  # Start timer
    #form_list = ["Student Athlete Profile", "Anthro_Height_Weight", "Attendance and Training Plan"]
    form_list = ["Laveg","CMJ Test"]
    # Replace with your actual form list
    for form in form_list:
        print(f"Processing form: {form}")
        process_form(form)
    end_time = time()  # End timer
    elapsed_time = end_time - start_time
    print(f"Total time taken: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
