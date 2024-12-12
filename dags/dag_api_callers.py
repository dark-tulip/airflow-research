import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

URL_COFFEE_API_CALLER = "https://coffee.alexflipnote.dev/random"
URL_OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast?latitude=51.125&longitude=71&current=temperature_2m%2Cprecipitation%2Cweather_code%2Cpressure_msl&timezone=Asia%2FAlmaty"
URL_ARTISTS_INFO = "https://rest.bandsintown.com/artists/Lady%20Gaga?app_id=123123"
URL_CHUCK_NORRIS_JOKES = "https://api.chucknorris.io/jokes/random"


def fetch_api_data(api_url, output_path, params):
    """
    Выбрать 3 любых API с текстовыми ответами,
    или взять любые другие на свой вкус.
    Сделать 3 параллельные задачи на получение результатов 100 запросов.
    Собрать данные о времени выполнения запроса.
    """
    responses = []
    for i in range(5):
        start = datetime.now()
        response = requests.get(api_url, params)
        end = datetime.now()
        responses.append({'response': response.json(), 'time': int((end - start).total_seconds() * 1000), 'attempt': i})
    pd.DataFrame(responses).to_csv(output_path, index=False)


def merge_results():
    """
    Когда все данные будут получены, собрать их в единый csv-файл.
    """
    files = [f for f in os.listdir('/opt/airflow/data/') if f.startswith('api')]
    all_data = pd.concat([pd.read_csv(f'/opt/airflow/data/{file}') for file in files])
    all_data.to_csv('/opt/airflow/data/merged_api_data.csv', index=False)


def fetch_images():
    """
    После этого, если сегодня четный день месяца,
    собрать данные с помощью 4-го API, выдающего картинки, и записать их в папку.
    Собрать данные о времени выполнения запроса.
    Если день нечетный - ничего делать не надо.
    """
    if datetime.now().day % 2 == 0:
        url = URL_COFFEE_API_CALLER
        response = requests.get(url)
        with open(f'/opt/airflow/data/images/image_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png', 'wb') as f:
            f.write(response.content)


def plot_histograms():
    """
    Построить гистограммы времени ответа для всех использованных API.
    """
    data = pd.read_csv('/opt/airflow/data/merged_api_data.csv')
    data['time'].hist()

    plt.figure(figsize=(10, 6))
    plt.hist(data['time'], bins=10, color='skyblue', edgecolor='black', alpha=0.7)
    plt.title('Гистограммы времени ответа для всех использованных API', fontsize=16)
    plt.xlabel('Response Time (ms)', fontsize=14)
    plt.ylabel('Частота', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('/opt/airflow/data/images/api_time_histogram.png')


default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 12, 11),
}

with DAG('api_analysis_pipeline', default_args=default_args, schedule_interval='@daily') as dag:
    t1 = PythonOperator(task_id='fetch_api1', python_callable=fetch_api_data,
                        op_kwargs={'api_url': URL_OPEN_METEO_API, 'output_path': '/opt/airflow/data/api1.csv'})

    t2 = PythonOperator(task_id='fetch_api2', python_callable=fetch_api_data,
                        op_kwargs={'api_url': URL_ARTISTS_INFO, 'output_path': '/opt/airflow/data/api2.csv'})

    t3 = PythonOperator(task_id='fetch_api3', python_callable=fetch_api_data,
                        op_kwargs={'api_url': URL_CHUCK_NORRIS_JOKES, 'output_path': '/opt/airflow/data/api3.csv'})

    t4 = PythonOperator(task_id='merge_results', python_callable=merge_results)
    t5 = PythonOperator(task_id='fetch_images', python_callable=fetch_images)
    t6 = PythonOperator(task_id='plot_histograms', python_callable=plot_histograms)

    [t1, t2, t3] >> t4 >> t5 >> t6
