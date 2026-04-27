from datetime import datetime
from pathlib import Path
import sys

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule

CURRENT_DAGS_DIR = Path(__file__).resolve().parent
if str(CURRENT_DAGS_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DAGS_DIR))

from _diasense_common import (
    ensure_pipeline_run_record,
    finalize_pipeline_run,
    load_params,
    resolve_training_mlflow_run_id,
    run_dvc_stage,
    run_ml_script,
    update_model_registry_record,
)


PIPELINE_NAME = "diasense_training_pipeline"


def run_dvc_pipeline_stage(stage_name: str, **context) -> None:
    ensure_pipeline_run_record(context, PIPELINE_NAME)
    run_dvc_stage(stage_name)


def run_script_stage(script_name: str, **context) -> None:
    ensure_pipeline_run_record(context, PIPELINE_NAME)
    run_ml_script(script_name)


def register_serving_model(**context) -> None:
    ensure_pipeline_run_record(context, PIPELINE_NAME)
    params = load_params()
    update_model_registry_record(params)


def record_pipeline_run_success_or_failure(**context) -> None:
    params = load_params()
    finalize_pipeline_run(
        context=context,
        pipeline_name=PIPELINE_NAME,
        final_task_id="record_pipeline_run_success_or_failure",
        mlflow_run_id=resolve_training_mlflow_run_id(params),
    )


with DAG(
    dag_id=PIPELINE_NAME,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["diasense", "training"],
) as dag:
    ingest = PythonOperator(
        task_id="ingest",
        python_callable=run_dvc_pipeline_stage,
        op_kwargs={"stage_name": "ingest"},
    )
    validate = PythonOperator(
        task_id="validate",
        python_callable=run_dvc_pipeline_stage,
        op_kwargs={"stage_name": "validate"},
    )
    preprocess = PythonOperator(
        task_id="preprocess",
        python_callable=run_dvc_pipeline_stage,
        op_kwargs={"stage_name": "preprocess"},
    )
    train = PythonOperator(
        task_id="train",
        python_callable=run_script_stage,
        op_kwargs={"script_name": "train.py"},
    )
    evaluate = PythonOperator(
        task_id="evaluate",
        python_callable=run_script_stage,
        op_kwargs={"script_name": "evaluate.py"},
    )
    register = PythonOperator(
        task_id="register",
        python_callable=register_serving_model,
    )

    # record_pipeline_run = PythonOperator(
    #     task_id="record_pipeline_run_success_or_failure",
    #     python_callable=record_pipeline_run_success_or_failure,
    #     trigger_rule=TriggerRule.ALL_DONE,
    # )

    ingest >> validate >> preprocess >> train >> evaluate >> register 
    # >> record_pipeline_run
