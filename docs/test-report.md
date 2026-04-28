# Test Report

## 1. Report Metadata

- Project: DiaSense
- Build/Commit: `a180acd501c95c9568fe2699dd8a8b1c756acbe6`
- DVC Revision: `a180acd501c95c9568fe2699dd8a8b1c756acbe6`
- MLflow Run ID(s): `f58209d613c544b38b8441a9411b404b`, `dc95dec72661419babfedb47d2f68d99`, `8389419c296e432ca448f176b6488fe4`
- Test Report Date: `2026-04-28`
- Tester: Haambayi M
- Environment: Local Docker Compose

## 2. Scope

- Features covered: backend tests, ML tests, DVC repro, Airflow DAG compile, Airflow training/monitoring execution, auth flow, prediction flow, admin/clinician flow, observability and route reachability
- Features excluded: browser-only visual validation and screenshots
- Test types executed:
  - Unit
  - API
  - Integration
  - Pipeline
  - Manual UX

## 3. Environment Details

- Host OS: `Ubuntu 24.04.4 LTS`
- Docker version: `Docker version 29.4.1`
- Docker Compose version: `Docker Compose version v5.1.3`
- Active `.env` source: `.env present`
- Frontend URL: `http://localhost:3100`
- Backend URL: `http://localhost:8000`
- MLflow URL: `http://localhost:5000`
- Airflow URL: `http://localhost:8080`
- Prometheus URL: `http://localhost:9090`
- Grafana URL: `http://localhost:3001`

## 4. Execution Summary

| Suite | Command | Status | Notes |
| --- | --- | --- | --- |
| Backend tests | `docker compose exec backend-api python -m pytest -q` | Pass | `23 passed` |
| ML tests | `docker compose exec ml bash -lc "python -m pip install pytest && cd /workspace/ml && python -m pytest -q tests"` | Pass | `10 passed` |
| Airflow DAG compile | `docker compose exec airflow python -m py_compile /workspace/airflow/dags/...` | Pass | No syntax errors |
| DVC repro | `docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro"` | Pass | Pipeline up to date; all stages skipped |
| Training DAG | `docker compose exec airflow airflow dags trigger diasense_training_pipeline` | Pass | Trigger run ended `success` |
| Monitoring DAG | `docker compose exec airflow airflow dags trigger diasense_monitoring_pipeline` | Fail | Trigger run `remained `running` during this test window |

## 5. Functional Results

### Authentication

- Signup: Pass
- Login: Pass
- Logout: Pass
- Reset password: Pass

### Prediction Flow

- Assessment submission: Pass
- Prediction list: Pass
- Prediction detail: Pass
- Delete prediction: Pass

### Admin/Clinician Flow

- User management: Pass
- Patient creation: Pass
- Patient deletion: Pass
- Monitor page: Pass by route reachability

### Observability

- `/health`: Pass (`200`)
- `/ready`: Pass (`200`)
- `/metrics`: Pass (`200`)
- MLflow: Pass (`200`)
- Airflow: Pass (`200`)
- Prometheus: Pass (`200`)
- Grafana: Pass (`200`)

## 6. Model And Pipeline Results

- Best model selected: `logistic_regression`
- Serving model version: artifact shows `8`; live backend/DB shows `1`
- Threshold checks passed: Yes
- Latest drift status: `drift_detected=false`
- Alert metrics file generated: Yes

## 7. Defects

| ID | Severity | Area | Description | Reproduction | Status |
| --- | --- | --- | --- | --- | --- |
| DEF-001 | High | Monitoring DAG trigger | Trigger run stayed in `running` state during the test window, while direct `airflow dags test diasense_monitoring_pipeline 2026-04-28T16:05:00+00:00` succeeded. | Trigger monitoring DAG, then list runs | Open |
| DEF-002 | High | Model registry / serving sync | `registration_summary.json` reports serving model version `8`, but live backend/DB reports active version `1`. | Compare `ml/artifacts/reports/registration_summary.json` with `/api/v1/model/info` or `model_versions` table | Open |

## 8. Risks / Follow-ups

- Frontend checks were reachability-based, not browser-interactive.
- Trigger-based monitoring execution did not complete during this run.

## 9. Evidence

- Screenshots: None
- Logs: Backend `23 passed`; ML `10 passed`; training `dags test` success; monitoring `dags test` success
- MLflow links: `http://localhost:5000`
- Airflow run IDs:`manual__2026-04-28`, `manual__2026-04-28`
  - `ml/artifacts/reports/train_summary.json`
  - `ml/artifacts/reports/evaluation_summary.json`
  - `ml/artifacts/reports/registration_summary.json`
  - `ml/artifacts/reports/drift_report.json`
  - `ml/artifacts/reports/drift_alert_metrics.prom`

## 10. Sign-off

- Tester: Haambayi M
- Reviewer: Pending
- Decision: Fail
- Comments: Most checks passed, but the trigger-based monitoring DAG did not complete in the test window and the serving-model version does not match the registration artifact.
