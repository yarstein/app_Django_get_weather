import datetime
from django.shortcuts import render
import json

from .utils import fetch_weather_data, get_coordinates
from .forms import CityForm

# Значения по умолчанию
DEFAULT_COORDS = (41.2647, 69.2163)
DEFAULT_CITY = ("Ташкент", "Узбекистан")


def weather_view(request):
    if request.method == 'POST':
        form = CityForm(request.POST)

        if form.is_valid():
            city = form.cleaned_data['city']
            city_data = get_coordinates(city)

            if city_data is None:
                errors = form.add_error(None, "Город не найден. Пожалуйста, попробуйте другой.")
            
            else:
                latitude, longitude, city_name, country_name = city_data
                hourly_dataframe, daily_dataframe, current_temperature, current_icon = fetch_weather_data(latitude, longitude)

                 # Получаем текущие данные из куки
                cities_data = request.COOKIES.get('cities_data')
                if cities_data:
                    cities_data = json.loads(cities_data)
                else:
                    cities_data = {}

                # Обновляем данные города
                if city in cities_data:
                    cities_data[city]['count'] += 1
                else:
                    cities_data[city] = {'count': 1}

                response = render(request, 'weather_app/index.html', {
                    'hourly_data': hourly_dataframe.to_dict(orient='records'),
                    'daily_data': daily_dataframe.to_dict(orient='records'),
                    'current_temperature': round(current_temperature),
                    'current_icon': current_icon,
                    'form': form,
                    'city_name': city_name,
                    'country_name': country_name,
                    'current_date': datetime.datetime.now().strftime('%d.%m.%Y'),
                     'cities_data': cities_data,
                    })
                response.set_cookie("last_city_data", json.dumps(city_data))
                response.set_cookie('cities_data', json.dumps(cities_data))
                return response
                
    else:
        form = CityForm()
        city_in_cooki = request.COOKIES.get("last_city_data")
        if city_in_cooki:
            city_data = json.loads(city_in_cooki)
        else:
            city_data = None

    latitude, longitude, city_name, country_name = city_data or (*DEFAULT_COORDS, *DEFAULT_CITY)
    hourly_dataframe, daily_dataframe, current_temperature, current_icon = fetch_weather_data(latitude, longitude)

    context = {
        'hourly_data': hourly_dataframe.to_dict(orient='records'),
        'daily_data': daily_dataframe.to_dict(orient='records'),
        'current_temperature': round(current_temperature),
        'current_icon': current_icon,
        'form': form,
        'city_name': city_name,
        'country_name': country_name,
        'current_date': datetime.datetime.now().strftime('%d.%m.%Y'),
    }
    return render(request, 'weather_app/index.html', context)