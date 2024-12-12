import unittest

import pandas as pd
import requests


class TestApiCallers(unittest.TestCase):
    """
    просто тестовый класс для тестирования кода
    """
    def test_call_open_meteo(self):
        url = "https://api.open-meteo.com/v1/forecast"
        response = requests.get(url, params={
            "latitude": "51.125",
            "longitude": "71",
            "current": "temperature_2m,precipitation,weather_code,pressure_msl",
            "timezone": "Asia/Almaty"
        }).json()

        flattened_data = pd.json_normalize(response, sep='_')

        print(flattened_data)

        csv_file_path = "data/flattened_json.csv"
        flattened_data.to_csv(csv_file_path, index=False)

    def test_merged_api_data_read(self):
        data = pd.read_csv('./data/merged_api_data.csv')
        print(data['time'].hist())


if __name__ == "__main__":
    unittest.main()
