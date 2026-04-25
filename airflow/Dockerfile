FROM apache/airflow:3.2.0-python3.12

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libgomp1 \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY airflow/requirements.txt /tmp/airflow-requirements.txt
COPY ml/requirements.txt /tmp/ml-requirements.txt
RUN pip install --no-cache-dir -r /tmp/airflow-requirements.txt -r /tmp/ml-requirements.txt
