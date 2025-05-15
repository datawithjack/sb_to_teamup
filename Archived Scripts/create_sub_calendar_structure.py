from dotenv import load_dotenv
import os
import requests

# 1) load your calendar-level key and calendar ID
load_dotenv("c:/Users/Jack.Andrew/Downloads/teamup/.env", override=True)
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

# 3) create the sub-calendar
payload = {
    "name":    "Sport > AA > Athletics > Development > Development 3",
    "active":  True,
    "color":   19,
    "overlap": True,
    "type":    0
}

create_resp = requests.post(
    f"https://api.teamup.com/{CALENDAR_KEY}/subcalendars",
    headers={
        "Teamup-Token":  API_TOKEN,
        "Authorization": f"Bearer {user_token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json"
    },
    json=payload
)

print("Status Code:", create_resp.status_code)
print("Response:",   create_resp.text)
