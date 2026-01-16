from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

AIRFLOW_API_BASE_URL = (os.getenv("AIRFLOW_API_BASE_URL") or "http://api:8000").strip().rstrip("/")
AIRFLOW_TRIGGER_TOKEN = os.getenv("AIRFLOW_TRIGGER_TOKEN") or ""
DRONE_SOP_JIRA_TRIGGER_URL = f"{AIRFLOW_API_BASE_URL}/api/v1/line-dashboard/sop/jira/trigger"
DRONE_SOP_JIRA_HTTP_TIMEOUT = int(os.getenv("DRONE_SOP_JIRA_HTTP_TIMEOUT") or "60")
DRONE_SOP_JIRA_SCHEDULE = os.getenv("DRONE_SOP_JIRA_SCHEDULE") or None


def _parse_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
        if parsed <= 0:
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def run_drone_sop_jira_create(**_context):
    if not AIRFLOW_API_BASE_URL:
        raise ValueError("AIRFLOW_API_BASE_URL is not set")

    headers = {"Accept": "application/json"}
    if AIRFLOW_TRIGGER_TOKEN:
        headers["Authorization"] = f"Bearer {AIRFLOW_TRIGGER_TOKEN}"

    payload = {}
    limit = _parse_optional_int(os.getenv("DRONE_SOP_JIRA_LIMIT"))
    if limit is not None:
        payload["limit"] = limit

    response = requests.post(
        DRONE_SOP_JIRA_TRIGGER_URL,
        headers=headers,
        json=payload or None,
        timeout=DRONE_SOP_JIRA_HTTP_TIMEOUT,
    )
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code}


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="drone_sop_jira_create",
    default_args=default_args,
    schedule=DRONE_SOP_JIRA_SCHEDULE,
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["drone", "sop", "jira"],
) as dag:
    create_jira = PythonOperator(
        task_id="create_jira_drone_sop",
        python_callable=run_drone_sop_jira_create,
    )
