import logging
import datetime
import requests
from livekit.agents import function_tool

# -------------------------------------------------
# 🧩 LOGGING SETUP
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# -------------------------------------------------
# 🕒 FUNCTION 1: Get Current Date & Time
# -------------------------------------------------
@function_tool
async def get_current_datetime() -> str:
    """
    Returns the current system date and time as a string.
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[Datetime Tool] Current datetime fetched: {current_time}")
    return f"The current date and time is {current_time}"


# -------------------------------------------------
# 🌤️ FUNCTION 2: Get Real-Time Weather
# -------------------------------------------------
@function_tool
async def get_weather(city: str = None) -> str:
    """
    Returns real-time weather for the given city.
    If no city is provided, it automatically detects the user's city from IP.
    """
    try:
        # Step 1: Detect user's city automatically if not given
        if not city:
            logger.info("[Weather Tool] City not provided, attempting auto-detect...")
            location_response = requests.get("https://ipinfo.io/json", timeout=5)
            location_data = location_response.json()
            city = location_data.get("city")
            logger.info(f"[Weather Tool] Auto-detected city: {city}")

        if not city:
            logger.warning("[Weather Tool] Could not auto-detect city.")
            return "Sorry, I couldn't detect your city automatically."

        # Step 2: Fetch weather data from Open-Meteo API (no key required)
        weather_url = f"https://api.open-meteo.com/v1/forecast?current_weather=true&timezone=auto"
        geo_resp = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}", timeout=5)
        geo_data = geo_resp.json()

        if "results" not in geo_data or len(geo_data["results"]) == 0:
            logger.error(f"[Weather Tool] City not found: {city}")
            return f"Sorry, I couldn't find weather data for {city}."

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        logger.info(f"[Weather Tool] Coordinates for {city}: lat={lat}, lon={lon}")

        weather_resp = requests.get(f"{weather_url}&latitude={lat}&longitude={lon}", timeout=5)
        weather_data = weather_resp.json()

        current_weather = weather_data.get("current_weather", {})
        temp = current_weather.get("temperature")
        wind = current_weather.get("windspeed")
        weather_code = current_weather.get("weathercode")

        logger.info(f"[Weather Tool] Weather data for {city}: Temp={temp}°C, Wind={wind} km/h, Code={weather_code}")

        if temp is None:
            return f"Sorry, I couldn’t fetch the weather data for {city} right now."

        return (
            f"The current temperature in {city} is {temp}°C with a wind speed of {wind} km/h."
        )

    except Exception as e:
        logger.exception("[Weather Tool] Exception occurred while fetching weather.")
        return f"An error occurred while fetching weather data: {str(e)}"


# -------------------------------------------------
# 🧠 MAIN TEST (Run this to check manually)
# -------------------------------------------------
if __name__ == "__main__":
    import asyncio

    async def test_tools():
        print(await get_current_datetime())
        print(await get_weather())           # Auto city detection
        print(await get_weather("Delhi"))    # Manual city

    asyncio.run(test_tools())
