# Test Plan

## Objective

Validate that DiaSense is functionally correct, operationally runnable, and reproducible across:

- frontend user journeys
- backend API contracts
- prediction orchestration
- training and monitoring pipelines
- observability surfaces

## Acceptance Criteria

The release is acceptable when all of the following are true:

- users can sign up and sign in
- the default environment admin can sign in with the configured credentials
- patients can submit assessments only for themselves
- clinicians and admins can submit assessments for patient accounts
- prediction results are persisted and visible in history/detail views
- patient management works for clinician/admin roles
- user management works for admin role
- the backend health and ready endpoints respond correctly
- the training DAG completes and registers a Production-serving model
- the monitoring DAG completes and emits drift metrics
- Prometheus and Grafana are reachable
- model evaluation thresholds continue to pass for the promoted model

## Automated Unit Tests

### Backend Unit/Service Tests

Current files:

- `apps/backend-api/tests/test_auth_service.py`
- `apps/backend-api/tests/test_prediction_service.py`
- `apps/backend-api/tests/test_db_bootstrap.py`

Coverage intent:

- auth login/logout/reset/signup flows
- derived BMI and age band logic
- risk band mapping
- fallback probability inference path
- bootstrap revision inference

### Backend Endpoint/API Tests

Current files:

- `apps/backend-api/tests/test_auth_endpoint.py`
- `apps/backend-api/tests/test_health_ready.py`
- `apps/backend-api/tests/test_metrics_endpoint.py`
- `apps/backend-api/tests/test_predict_endpoint.py`

Coverage intent:

- signup endpoint contract
- health/ready responses
- metrics endpoint exposure
- prediction endpoint success and validation rejection

### ML Unit Tests

Current files:

- `ml/tests/test_model_selection.py`
- `ml/tests/test_register.py`

Coverage intent:

- training-time optional registration behavior
- serving candidate selection only from threshold-passing models
- registry-stage MLflow promotion and summary shaping

## Integration Tests

Recommended integration checks:

1. Frontend to backend auth
2. Frontend assessment submission to backend prediction flow
3. Backend to model-server inference
4. Backend persistence into PostgreSQL
5. Training DAG to MLflow registry update
6. Monitoring DAG to drift row persistence and alert metrics output

## API Tests

Run the backend automated tests:

```bash
docker compose exec backend-api python -m pytest -q
```

Additional manual API checks:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
curl http://localhost:8000/docs
```

Protected endpoint checks should be run using a bearer token captured from `/api/v1/login`.

## Pipeline Tests

### DVC Pipeline

```bash
docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro"
```

Expected result:

- `ingest`, `validate`, `preprocess`, `train`, `evaluate`, and `register` complete successfully
- `train_summary.json`, `evaluation_summary.json`, and `registration_summary.json` are refreshed
- `model_versions.is_active = true` for the promoted version

### Training Pipeline

```bash
docker compose exec airflow airflow dags trigger diasense_training_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_training_pipeline
```

Expected result:

- DAG run reaches `success`
- MLflow records new runs
- `ml/artifacts/reports/train_summary.json`, `evaluation_summary.json`, and `registration_summary.json` are updated
- `model_versions.is_active = true` for the promoted version

### Monitoring Pipeline

```bash
docker compose exec airflow airflow dags trigger diasense_monitoring_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_monitoring_pipeline
```

Expected result:

- DAG run reaches `success`
- `ml/artifacts/reports/current_feature_stats.json` is updated
- `ml/artifacts/reports/drift_report.json` is updated
- `ml/artifacts/reports/drift_alert_metrics.prom` is updated
- `drift_reports` table receives new rows

## Expected Results

### Backend

- `/health` returns `200` and `status=ok`
- `/ready` returns `200` when dependencies are up and `503` otherwise
- `/predict` returns a valid `PredictResponse` on good input
- invalid input returns `422`
- missing active model returns `503`

### Frontend

- login and signup flows surface validation errors inline
- assessment submission shows risk band, probability, and interpretation
- prediction list and detail pages render persisted values
- monitor page renders a notice instead of crashing when backend ops data is unavailable

### ML

- at least one evaluated model passes thresholds
- a Production model version exists in MLflow after the register stage
- the best current recorded candidate remains `logistic_regression` unless retraining changes results

### Monitoring

- drift metrics file is valid text and non-empty
- no-step failure occurs in `emit_alert_metrics` for partial/malformed feature lists

## Manual Test Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] `docker compose up -d --build`
- [ ] Backend bootstrap runs successfully
- [ ] Frontend UI opens
- [ ] Sign up a patient account
- [ ] Sign in with the new patient account
- [ ] Submit a self-assessment
- [ ] Open prediction history
- [ ] Open prediction detail
- [ ] Sign in as `admin`
- [ ] Open users page
- [ ] Promote another account to `clinician`
- [ ] Create a patient from the patients page
- [ ] Run the DVC pipeline in the `ml` container
- [ ] Trigger the training DAG
- [ ] Restart the model-server
- [ ] Trigger the monitoring DAG
- [ ] Open MLflow
- [ ] Open Airflow
- [ ] Open Prometheus
- [ ] Open Grafana

## Recommended Execution Commands

```bash
docker compose exec backend-api python -m pytest -q
docker compose exec ml bash -lc "python -m pip install pytest && cd /workspace/ml && python -m pytest -q tests"
docker compose exec airflow python -m py_compile /workspace/airflow/dags/diasense_training_pipeline.py /workspace/airflow/dags/diasense_monitoring_pipeline.py /workspace/airflow/dags/_diasense_common.py
docker compose exec airflow airflow dags test diasense_training_pipeline 2026-04-28T08:50:00+00:00
```

## Exit Criteria

Testing is complete when:

- automated tests pass
- manual acceptance checks pass
- training and monitoring DAGs complete successfully
- no blocking defects remain in auth, prediction, registry, or monitoring flows
