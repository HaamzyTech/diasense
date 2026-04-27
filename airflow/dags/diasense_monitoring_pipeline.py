from datetime import datetime, timezone
from pathlib import Path
import sys

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule

CURRENT_DAGS_DIR = Path(__file__).resolve().parent
if str(CURRENT_DAGS_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DAGS_DIR))

from _diasense_common import (
    alert_metrics_path,
    build_drift_report,
    current_feature_stats_path,
    emit_system_events_for_drift,
    ensure_pipeline_run_record,
    finalize_pipeline_run,
    load_dataframe,
    load_json,
    load_params,
    numeric_feature_columns,
    persist_drift_rows,
    recent_data_path,
    save_json,
    save_text,
    compute_feature_stats,
    drift_report_path,
)


PIPELINE_NAME = "diasense_monitoring_pipeline"


def recompute_current_feature_stats_from_recent_data(**context) -> None:
    ensure_pipeline_run_record(context, PIPELINE_NAME)
    params = load_params()
    recent_df = load_dataframe(recent_data_path())
    stats_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(recent_data_path()),
        "feature_stats": compute_feature_stats(
            recent_df,
            numeric_feature_columns(params),
        ),
    }
    save_json(current_feature_stats_path(params), stats_payload)


def compare_against_baseline(**context) -> None:
    ensure_pipeline_run_record(context, PIPELINE_NAME)
    params = load_params()
    drift_report = build_drift_report(params)
    save_json(drift_report_path(params), drift_report)


def persist_drift_report(**context) -> None:
    params = load_params()
    report = load_json(drift_report_path(params))
    pipeline_run_id = ensure_pipeline_run_record(context, PIPELINE_NAME)
    persist_drift_rows(pipeline_run_id, report)


def emit_alert_metrics(**context) -> None:
    params = load_params()
    report_path = drift_report_path(params)
    report = load_json(report_path) if report_path.exists() else {"features": [], "drift_detected": False}
    try:
        raw_features = report.get("features", [])
        features = [feature for feature in raw_features if isinstance(feature, dict)]
        drifted_features = [
            feature for feature in features if feature.get("status") == "drift"
        ]
        lines = [
            "# HELP drift_detected_gauge Whether the monitoring pipeline detected feature drift.",
            "# TYPE drift_detected_gauge gauge",
            f"drift_detected_gauge {1 if report.get('drift_detected') else 0}",
            "# HELP drift_feature_count Number of features currently marked as drifted.",
            "# TYPE drift_feature_count gauge",
            f"drift_feature_count {len(drifted_features)}",
            "# HELP feature_drift_status Whether a specific feature is currently marked as drifted.",
            "# TYPE feature_drift_status gauge",
            "# HELP feature_drift_psi Population stability index for a specific feature.",
            "# TYPE feature_drift_psi gauge",
            "# HELP feature_drift_ks_stat Kolmogorov-Smirnov statistic for a specific feature.",
            "# TYPE feature_drift_ks_stat gauge",
        ]

        for feature in features:
            feature_name = str(feature.get("feature_name") or feature.get("feature") or "unknown")
            safe_feature = feature_name.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
            lines.append(
                f'feature_drift_status{{feature="{safe_feature}"}} {1 if feature.get("status") == "drift" else 0}'
            )
            psi = feature.get("psi")
            if isinstance(psi, (int, float)):
                lines.append(
                    f'feature_drift_psi{{feature="{safe_feature}"}} {float(psi)}'
                )
            ks_stat = feature.get("ks_stat")
            if isinstance(ks_stat, (int, float)):
                lines.append(
                    f'feature_drift_ks_stat{{feature="{safe_feature}"}} {float(ks_stat)}'
                )

        try:
            emit_system_events_for_drift({**report, "features": features})
        except Exception as exc:
            print(f"emit_alert_metrics: unable to persist drift system events: {exc}")

        try:
            pipeline_status = finalize_pipeline_run(
                context=context,
                pipeline_name=PIPELINE_NAME,
                final_task_id="emit_alert_metrics",
            )
        except Exception as exc:
            print(f"emit_alert_metrics: unable to finalize pipeline run: {exc}")
            pipeline_status = "failed"

        lines.extend(
            [
                "# HELP monitoring_pipeline_run_status Whether the latest monitoring pipeline run finished successfully.",
                "# TYPE monitoring_pipeline_run_status gauge",
                f"monitoring_pipeline_run_status {1 if pipeline_status == 'success' else 0}",
            ]
        )
        save_text(alert_metrics_path(params), "\n".join(lines) + "\n")
    except Exception:
        finalize_pipeline_run(
            context=context,
            pipeline_name=PIPELINE_NAME,
            final_task_id="emit_alert_metrics",
            status_override="failed",
        )
        raise


with DAG(
    dag_id=PIPELINE_NAME,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["diasense", "monitoring"],
) as dag:
    recompute_stats = PythonOperator(
        task_id="recompute_current_feature_stats_from_recent_data",
        python_callable=recompute_current_feature_stats_from_recent_data,
    )

    compare_baseline = PythonOperator(
        task_id="compare_against_baseline",
        python_callable=compare_against_baseline,
    )

    persist_report = PythonOperator(
        task_id="persist_drift_report",
        python_callable=persist_drift_report,
    )

    emit_metrics = PythonOperator(
        task_id="emit_alert_metrics",
        python_callable=emit_alert_metrics,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    recompute_stats >> compare_baseline >> persist_report >> emit_metrics
