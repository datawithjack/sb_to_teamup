from dotenv import load_dotenv
import os

load_dotenv()  # reads .env into os.environ
TOKEN = os.getenv("TEAMUP_TOKEN")
KEY   = os.getenv("TEAMUP_CALENDAR_KEY")