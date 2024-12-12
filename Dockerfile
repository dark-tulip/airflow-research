FROM apache/airflow:2.6.2-python3.9

USER root
RUN apt-get update && apt-get install -y python3-dev libpq-dev

USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["airflow"]
CMD ["webserver"]