####### CREATE SUB CALENDAR STRUCTURE ######
# setup
from dotenv import load_dotenv
import os
import requests

load_dotenv(dotenv_path="c:/Users/Jack.Andrew/Downloads/teamup/.env", override=True) # reads .env into os.environ

# ——— Configuration ———
API_TOKEN     = os.getenv("TEAMUP_TOKEN")

# ######################  GET AUTH TOKEN #####################################
url = "https://api.teamup.com/auth/tokens"
payload = {
    "app_name": "My awesome new app",
    "device_id": "Jacks Laptop",
    "email": "Alessandra.moretti@aspire.qa",
    "password": "Aspire2025"
}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Teamup-Token": API_TOKEN 
}
response = requests.post(url, json=payload, headers=headers)
print(response.json())
###############################################################################
## Add auth token into .env file
###############################


load_dotenv(dotenv_path="c:/Users/Jack.Andrew/Downloads/teamup/.env", override=True) # reads .env into os.environ


# ——— Configuration ———
API_TOKEN     = os.getenv("TEAMUP_TOKEN")
CALENDAR_KEY  = os.getenv("TEAMUP_CALENDAR_KEY")
AUTHORIZATION_KEY = os.getenv("AUTHORIZATION_KEY")

BASE_URL      = "https://api.teamup.com"

HEADERS       = {
    "Teamup-Token": API_TOKEN, 
    "Authorization": AUTHORIZATION_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json, text/html",
}

# common payload fields
# build the correct payload

payload = {
    "name":    "Sport > AA > Athletics > Development > Development 2",
    "active":  True,
    "color":   17,
    "overlap": True,
    "type":    0
}

resp = requests.post(

    f"{BASE_URL}/{CALENDAR_KEY}/subcalendars",
    headers=HEADERS,
    json=payload
    )


# safer JSON parsing
try:
    print("Status Code:", resp.status_code)
    resp.raise_for_status()  # will raise an error if status is 4xx/5xx
    print(resp.json())
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
    print("Response Text:", resp.text)
except ValueError as e:
    print("Invalid JSON returned:", resp.text)
