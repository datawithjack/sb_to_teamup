import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("TEAMUP_TOKEN")
CALENDAR_KEY = os.getenv("TEAMUP_CALENDAR_KEY")
BASE_URL = "https://api.teamup.com/"

# ─── Authenticate to get user token ───────────────────────────────────────────
auth_resp = requests.post(
    "https://api.teamup.com/auth/tokens",
    headers={
        "Teamup-Token": API_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    json={
        "app_name": "My awesome app",
        "device_id": "Jack's Laptop",
        "email": os.getenv("TEAMUP_EMAIL"),
        "password": os.getenv("TEAMUP_PASSWORD")
    }
)
auth_resp.raise_for_status()
user_token = auth_resp.json()["auth_token"]
print(f"✓ Authenticated, user token: {user_token[:20]}...")

# ─── Use BOTH tokens in headers ───────────────────────────────────────────────
HEADERS = {
    "Teamup-Token": API_TOKEN,              # ← Calendar API token
    "Authorization": f"Bearer {user_token}", # ← User session token
    "Accept": "application/json"
}


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

if __name__ == "__main__":
    subcalendars = list_all_subcalendars()
    
    for sc in subcalendars:
        print(sc)