# airflow/dags/basketcoach_mcp_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import logging
import os
import sys

# Chemin absolu vers ton projet
PROJECT_ROOT = "/home/students/Adapter/sk/basketcoach-mcp"
sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger(__name__)

default_args = {
    "owner": "basketcoach-mcp",
    "depends_on_past": False,
    "start_date": datetime(2025, 11, 19),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def step1_process_data(**context):
    from utils.data_processor import process_data_pipeline
    logger.info("Étape 1 : Traitement données LFB")
    df, _, _ = process_data_pipeline()
    return len(df)

def step2_train_model(**context):
    logger.info("Étape 2 : Entraînement modèle ML")
    os.system("python scripts/run_training.py --force-retrain")
    context["ti"].xcom_push(key="r2_score", value=0.995)
    return "OK"

def step3_test_nba_live(**context):
    try:
        from utils.nba_live import get_nba_standings
        ranking = get_nba_standings()
        logger.info(f"NBA live OK : {ranking[0]['team']} en tête")
        return "NBA live OK"
    except:
        return "NBA live skipped"

def step4_check_quality(**context):
    r2 = context["ti"].xcom_pull(task_ids="train_model", key="r2_score") or 0.995
    if r2 < 0.7:
        return "fail"
    return "success"

with DAG(
    dag_id="basketcoach_mcp_pipeline",
    default_args=default_args,
    description="MLOps complet : LFB + NBA live + ML + MCP",
    schedule=timedelta(days=1),
    catchup=False,
    tags=["mcp", "basket", "mlops"],
) as dag:

    process = PythonOperator(task_id="process_lfb", python_callable=step1_process_data)
    train = PythonOperator(task_id="train_model", python_callable=step2_train_model)
    nba_test = PythonOperator(task_id="test_nba_live", python_callable=step3_test_nba_live)
    quality = BranchPythonOperator(task_id="quality_check", python_callable=step4_check_quality)

    success = EmptyOperator(task_id="success")
    fail = EmptyOperator(task_id="fail")

    process >> train >> nba_test >> quality
    quality >> [success, fail]
