from dotenv import load_dotenv
import os
import requests

from utils.teamup_functions import delete_subcalendar, list_all_subcalendars

# Get Authorization token ──────────────────────────────────────────────────────────
load_dotenv(override=True)
API_TOKEN    = os.getenv("TEAMUP_TOKEN")         # ← calendar API key
CALENDAR_KEY = os.getenv("TEAMUP_CALENDAR_KEY")  # ← e.g. "oahota"
TEAM_EMAIL = os.getenv("TEAMUP_EMAIL")  
TEAM_PASSWORD = os.getenv("TEAMUP_PASSWORD")

# 2) log in to get your user token
auth_resp = requests.post(
    "https://api.teamup.com/auth/tokens",
    headers={
        "Teamup-Token": API_TOKEN,
        "Content-Type":  "application/json",
        "Accept":        "application/json"
    },
    json={
        "app_name":  "Aspire Sports Department Calendar",
        "device_id": "Jacks Laptop",
        "email":     TEAM_EMAIL,
        "password": TEAM_PASSWORD
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


if __name__ == "__main__":
    subcal_data = list_all_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS)
    sub_calendar_ids = [item["id"] for item in subcal_data]
    filtered_sub_calendar_ids = [id for id in sub_calendar_ids if id not in [14217582, 15155825,15166082]]

    # Exclude the last calendar from deletion
    ids_to_delete = filtered_sub_calendar_ids
    print("Will delete these IDs (keeping id: 15155825, 14217582):", ids_to_delete) #barney calendar is kept

    for sub_id in ids_to_delete:
        delete_subcalendar(BASE_URL, CALENDAR_KEY, HEADERS, sub_id)





