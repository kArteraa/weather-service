import os

from dotenv import load_dotenv

load_dotenv()

OWM_API_KEY: str = os.getenv("OWM_API_KEY", "7c293e1f109af8afb6b48cf47e339922")

OWM_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"

UNITS: str = "metric"
LANG: str = "ru"

CACHE_TTL: int = 600
MAX_CONCURRENCY: int = 20
