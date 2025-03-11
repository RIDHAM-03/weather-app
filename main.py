import datetime
import requests
import string
from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv

load_dotenv()

# Correct way to retrieve API key from .env
api_key = os.getenv("API_KEY")  # Get API key from environment variables
if not api_key:
    raise ValueError("API_KEY is missing. Please set it in your .env file.")

OWM_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_API_ENDPOINT = "http://api.openweathermap.org/geo/1.0/direct"

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("search")
        return redirect(url_for("get_weather", city=city))
    return render_template("index.html")

@app.route("/<city>", methods=["GET", "POST"])
def get_weather(city):
    city_name = string.capwords(city)
    today = datetime.datetime.now()
    current_date = today.strftime("%A, %B %d")

    # Get latitude and longitude for city
    location_params = {
        "q": city_name,
        "appid": api_key,
        "limit": 1,
    }

    location_response = requests.get(GEOCODING_API_ENDPOINT, params=location_params)
    location_data = location_response.json()

    # Check if location data is empty
    if not location_data:
        return "Error: Location data not found", 400 

    lat = location_data[0].get("lat")
    lon = location_data[0].get("lon")

    if lat is None or lon is None:
        return "Error: Latitude or Longitude not found", 400

    # Get OpenWeather API data
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }

    weather_response = requests.get(OWM_ENDPOINT, params=weather_params)
    weather_data = weather_response.json()

    if "main" not in weather_data or "weather" not in weather_data:
        return "Error: Weather data not found", 400

    # Get current weather data
    current_temp = round(weather_data['main']['temp'])
    current_weather = weather_data['weather'][0]['main']
    min_temp = round(weather_data['main']['temp_min'])
    max_temp = round(weather_data['main']['temp_max'])
    wind_speed = weather_data['wind']['speed']

    # Get five-day weather forecast data
    forecast_response = requests.get(OWM_FORECAST_ENDPOINT, params=weather_params)
    forecast_data = forecast_response.json()

    if "list" not in forecast_data:
        return "Error: Forecast data not found", 400

    # Make lists of temperature and weather description data
    five_day_temp_list = [round(item['main']['temp']) for item in forecast_data['list'] if '12:00:00' in item['dt_txt']]
    five_day_weather_list = [item['weather'][0]['main'] for item in forecast_data['list'] if '12:00:00' in item['dt_txt']]

    # Get next four weekdays
    five_day_unformatted = [today + datetime.timedelta(days=i) for i in range(5)]
    five_day_dates_list = [date.strftime("%a") for date in five_day_unformatted]

    return render_template("city.html", city_name=city_name, current_date=current_date, current_temp=current_temp,
                           current_weather=current_weather, min_temp=min_temp, max_temp=max_temp, wind_speed=wind_speed,
                           five_day_temp_list=five_day_temp_list, five_day_weather_list=five_day_weather_list,
                           five_day_dates_list=five_day_dates_list)

@app.route("/error")
def error():
    return render_template("error.html")

if __name__ == "__main__":
    app.run(debug=True)
