import os
from dotenv import load_dotenv
from datetime import date

to_day = date.today().isoformat()

load_dotenv()

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10
API_KEY = os.getenv("API_KEY")