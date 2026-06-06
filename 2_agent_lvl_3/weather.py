import requests

def get_weather(city: str) -> str:
    """Get current weather for a city using Open-Meteo (no API key needed)."""
    
    # Open-Meteo needs lat/lon, so first geocode the city name
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_response = requests.get(geo_url, params={"name": city, "count": 1}, timeout=10)
    geo_data = geo_response.json()
    
    if not geo_data.get("results"):
        return f"Could not find location: {city}"
    
    location = geo_data["results"][0]
    lat = location["latitude"]
    lon = location["longitude"]
    name = location["name"]
    country = location.get("country", "")
    
    # Now fetch the weather
    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh"
    }
    weather_response = requests.get(weather_url, params=params, timeout=10)
    data = weather_response.json()
    
    current = data["current"]
    return (
        f"Weather in {name}, {country}:\n"
        f"Temperature: {current['temperature_2m']}°C\n"
        f"Humidity: {current['relative_humidity_2m']}%\n"
        f"Wind speed: {current['wind_speed_10m']} km/h\n"
        f"Weather code: {current['weather_code']} (see WMO codes)"
    )