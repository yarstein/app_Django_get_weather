import requests_cache
import pandas as pd
import requests
import re
from retry_requests import retry
from openmeteo_requests import Client

# Настройка клиента Open-Meteo API с кешированием и повторной попыткой при ошибке
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = Client(session=retry_session)


def get_weather_icon(weather_code):
    # Сопоставление кодов погоды с иконками
    weather_icons = {
        0: "sunny.png",  # Ясно
        1: "partly_cloudy.png",  # В основном ясно
        2: "cloudy.png",  # Переменная облачность
        3: "overcast.png",  # Пасмурно
        45: "fog.png",  # Туман
        48: "fog.png",  # Осаждающий туман с изморозью
        51: "drizzle.png",  # Легкая морось
        53: "drizzle.png",  # Умеренная морось
        55: "drizzle.png",  # Густая морось
        56: "freezing_drizzle.png",  # Легкая морось с заморозками
        57: "freezing_drizzle.png",  # Густая морось с заморозками
        61: "rain.png",  # Небольшой дождь
        63: "rain.png",  # Умеренный дождь
        65: "rain.png",  # Сильный дождь
        66: "freezing_rain.png",  # Легкий ледяной дождь
        67: "freezing_rain.png",  # Сильный ледяной дождь
        71: "snow.png",  # Небольшой снегопад
        73: "snow.png",  # Умеренный снегопад
        75: "snow.png",  # Сильный снегопад
        80: "rain.png",  # Легкий дождь с ливнями
        81: "rain.png",  # Умеренный дождь с ливнями
        82: "rain.png",  # Сильный дождь с ливнями
        95: "thunderstorm.png",  # Гроза
        99: "thunderstorm.png",  # Гроза с градом
    }
    return weather_icons.get(weather_code, "unknown.png")


def get_coordinates(city):
    # Проверка, написано ли название города на кириллице
    if re.search(r'[А-Яа-я]', city):
        language = 'ru'
    else:
        language = 'en'

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&language={language}"
    response = requests.get(url)
    data = response.json()

    if data and 'results' in data:
        results = data['results'][0]  # Берем первый результат
        return results['latitude'], results['longitude'], results['name'], results['country']
    else:
        return None


def fetch_weather_data(latitude, longitude):
    # Порядок переменных в hourly или daily важен для правильного назначения ниже
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "hourly": "temperature_2m,weathercode",
        "daily": "weather_code",
        "timezone": "Europe/Moscow",
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)

    # Обработка первого местоположения
    response = responses[0]

    # Получение текущих значений
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_weather_code = current.Variables(1).Value()
    current_icon = get_weather_icon(current_weather_code)

    # Обработка почасовых данных
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(1).ValuesAsNumpy()

    # Создаем временной ряд, начиная с 00:00
    start_time = pd.to_datetime(hourly.Time(), unit="s", utc=True).normalize()
    hourly_data = {
        "time": pd.date_range(start=start_time, periods=24, freq='h', tz='UTC')
    }
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["weather_code"] = hourly_weather_code

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    hourly_dataframe['temperature_2m'] = hourly_dataframe['temperature_2m'].round().astype(int)
    hourly_dataframe['icon'] = hourly_dataframe['weather_code'].apply(get_weather_icon)
    hourly_dataframe['formatted_time'] = hourly_dataframe['time'].dt.strftime('%H:%M')


    # Обработка ежедневных данных
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()

    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )
    }
    daily_data["weather_code"] = daily_weather_code

    daily_dataframe = pd.DataFrame(data=daily_data)

    return hourly_dataframe, daily_dataframe, current_temperature_2m, current_icon