import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator


def download_weather_data():
    """
    Скачивать данные с сайта Open Meteo для Физтеха с небольшим периодом (порядка минут).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    response = requests.get(url, params={
        "latitude": "22.125",
        "longitude": "71",
        "current": "temperature_2m,precipitation,weather_code,pressure_msl",
        "timezone": "Asia/Almaty"
    }).json()

    flattened_data = pd.json_normalize(response, sep='_')  # убираем вложенный json
    csv_file_path = "/opt/airflow/data/weather.csv"
    flattened_data.to_csv(csv_file_path, index=False, mode='a', header=not os.path.exists(csv_file_path))


def analyze_weather_data():
    """
    Периодически делать описательный анализ собранных данных (период порядка часов).
    В описательный анализ включить среднее, дисперсию, медиану значений.
    """
    df = pd.read_csv('/opt/airflow/data/weather.csv')
    stats = df['current_temperature_2m'].describe()
    stats.to_csv(r'/opt/airflow/data/weather_temperature_stats.csv')


def plot_temperature():
    """
    Отрисовывать график температуры за день (ежедневная задача).
    """
    df = pd.read_csv('/opt/airflow/data/weather.csv')
    df['time'] = pd.to_datetime(df['current_time'])
    df['temperature'] = pd.to_numeric(df['current_temperature_2m'])

    plt.figure(figsize=(10, 6))
    plt.plot(df['time'], df['temperature'], marker='o', color='crimson', linestyle='-', linewidth=2)
    plt.title('График температуры за день', fontsize=16)
    plt.xlabel('Время', fontsize=14)
    plt.ylabel('Температура (°C)', fontsize=14)
    plt.grid(axis='both', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('/opt/airflow/data/images/weather_temperature_plot.png')


default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 12, 11),
}

with DAG('weather_pipeline', default_args=default_args, schedule_interval='@hourly') as dag:
    t1 = PythonOperator(task_id='download_weather_data', python_callable=download_weather_data)
    t2 = PythonOperator(task_id='analyze_weather_data', python_callable=analyze_weather_data)
    t3 = PythonOperator(task_id='plot_temperature', python_callable=plot_temperature)

    t1 >> t2 >> t3
