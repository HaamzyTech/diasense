# Test Report Template

## 1. Report Metadata

- Project:
- Build/Commit:
- DVC Revision:
- MLflow Run ID(s):
- Test Report Date:
- Tester:
- Environment:

## 2. Scope

- Features covered:
- Features excluded:
- Test types executed:
  - Unit
  - API
  - Integration
  - Pipeline
  - Manual UX

## 3. Environment Details

- Host OS:
- Docker version:
- Docker Compose version:
- Active `.env` source:
- Frontend URL:
- Backend URL:
- MLflow URL:
- Airflow URL:
- Prometheus URL:
- Grafana URL:

## 4. Execution Summary

| Suite | Command | Status | Notes |
| --- | --- | --- | --- |
| Backend tests | `docker compose exec backend-api pytest -q` | Pass/Fail | |
| ML tests | `docker compose exec ml bash -lc "pip install pytest && cd /workspace/ml && pytest -q"` | Pass/Fail | |
| Airflow DAG compile | `docker compose exec airflow python -m py_compile /workspace/airflow/dags/...` | Pass/Fail | |
| DVC repro | `docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro"` | Pass/Fail | |
| Training DAG | `docker compose exec airflow airflow dags trigger diasense_training_pipeline` | Pass/Fail | |
| Monitoring DAG | `docker compose exec airflow airflow dags trigger diasense_monitoring_pipeline` | Pass/Fail | |

## 5. Functional Results

### Authentication

- Signup:
- Login:
- Logout:
- Reset password:

### Prediction Flow

- Assessment submission:
- Prediction list:
- Prediction detail:
- Delete prediction:

### Admin/Clinician Flow

- User management:
- Patient creation:
- Patient deletion:
- Monitor page:

### Observability

- `/health`:
- `/ready`:
- `/metrics`:
- MLflow:
- Airflow:
- Prometheus:
- Grafana:

## 6. Model And Pipeline Results

- Best model selected:
- Serving model version:
- Threshold checks passed:
- Latest drift status:
- Alert metrics file generated:

## 7. Defects

| ID | Severity | Area | Description | Reproduction | Status |
| --- | --- | --- | --- | --- | --- |
| DEF-001 | | | | | |

## 8. Risks / Follow-ups

- 

## 9. Evidence

- Screenshots:
- Logs:
- MLflow links:
- Airflow run IDs:
- Artifact paths:

## 10. Sign-off

- Tester:
- Reviewer:
- Decision: Pass / Conditional Pass / Fail
- Comments:
