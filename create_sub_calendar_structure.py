from dotenv import load_dotenv
import os
import requests
import csv
load_dotenv()
# ─── 1) Load your Teamup API token + calendar key from .env ──────────────────
# load_dotenv("c:/Users/Jack.Andrew/Downloads/teamup/.env", override=True)
API_TOKEN     = os.getenv("TEAMUP_TOKEN")         # ← your calendar-level key
CALENDAR_KEY  = os.getenv("TEAMUP_CALENDAR_KEY")  # ← e.g. "oahota"
TEAM_EMAIL = os.getenv("TEAMUP_EMAIL")  
TEAM_PASSWORD = os.getenv("TEAMUP_PASSWORD")

# ─── 2) Authenticate once to get your user token ─────────────────────────────
auth_resp = requests.post(
    "https://api.teamup.com/auth/tokens",
    headers={
        "Teamup-Token": API_TOKEN,
        "Content-Type":  "application/json",
        "Accept":        "application/json"
    },
    json={
        "app_name":  "My awesome app",
        "device_id": "Jack's Laptop",
        "email":     os.getenv("TEAMUP_EMAIL"),      # or hard-code
        "password":  os.getenv("TEAMUP_PASSWORD")    # or hard-code
    }
)
auth_resp.raise_for_status()
user_token = auth_resp.json()["auth_token"]
print("▶︎ Authenticated, user token:", user_token)

# # ─── 3) Read your CSV and create each sub-calendar ────────────────────────────
# CSV_PATH = "Venue and Group Calendar Structure.csv"

# with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         name     = row["Calendar Name"]
#         color    = int(row["Color Id"])
#         overlap  = bool(int(row["Allow Overlap"]))  # 1 → True, 0 → False

#         payload = {
#             "name":    name,
#             "active":  True,
#             "color":   color,
#             "overlap": overlap,
#             "type":    0
#         }

#         resp = requests.post(
#             f"https://api.teamup.com/{CALENDAR_KEY}/subcalendars",
#             headers={
#                 "Teamup-Token":  API_TOKEN,
#                 "Authorization": f"Bearer {user_token}",
#                 "Content-Type":  "application/json",
#                 "Accept":        "application/json"
#             },
#             json=payload
#         )

#         if resp.ok:
#             print(f"✓ Created “{name}” (color={color}, overlap={overlap})")
#         else:
#             print(f"✗ Failed “{name}”: {resp.status_code} {resp.text}")
