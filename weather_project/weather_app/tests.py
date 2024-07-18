from django.test import TestCase
from .utils import get_weather_icon, get_coordinates, fetch_weather_data

class UtilsTestCase(TestCase):

    def test_get_weather_icon(self):
        # Тестируем правильность отображения иконок
        self.assertEqual(get_weather_icon(0), 'sunny.png')
        self.assertEqual(get_weather_icon(45), 'fog.png')
        self.assertEqual(get_weather_icon(999), 'unknown.png')

    def test_get_coordinates(self):
        # Тестируем, что API возвращает координаты города
        result = get_coordinates("Tashkent")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result[0], (int, float))
        self.assertIsInstance(result[1], (int, float))

    def test_fetch_weather_data(self):
        # Тестируем получение данных погоды
        latitude, longitude = 41.2647, 69.2163
        hourly_df, daily_df, current_temp, current_icon = fetch_weather_data(latitude, longitude)

        self.assertIsNotNone(hourly_df)
        self.assertIsNotNone(daily_df)
        self.assertIsInstance(current_temp, (int, float))
        self.assertIsInstance(current_icon, str)

        # Проверяем наличие нужных колонок в DataFrame
        self.assertIn('time', hourly_df.columns)
        self.assertIn('temperature_2m', hourly_df.columns)
        self.assertIn('icon', hourly_df.columns)
        self.assertIn('formatted_time', hourly_df.columns)

