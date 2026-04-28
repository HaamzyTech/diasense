# High-Level Design

## Problem Statement

DiaSense addresses a simple operational problem with several moving parts:

- clinicians and patients need a consistent way to submit diabetes-risk assessment inputs
- the product needs an authenticated history of predictions and patient-specific ownership
- ML training, evaluation, and promotion must be reproducible
- the deployed model must be observable and monitored for drift
- operations teams need dashboards and alerts instead of ad hoc notebook-driven checks

## Why This Architecture Was Chosen

The architecture intentionally separates online inference, offline ML work, orchestration, and observability.

Reasons for the chosen design:

- a dedicated frontend keeps user-facing flows independent from model and pipeline internals
- a dedicated backend API centralizes auth, authorization, validation, persistence, and inference orchestration
- a model-server process isolates model invocation from the main API process
- ML scripts remain runnable both directly and under Airflow, which lowers coupling
- DVC tracks the data preparation lineage independently from MLflow experiment tracking
- Prometheus and Grafana provide an operator-focused surface for readiness, drift, and pipeline health

## Component Separation

### Frontend

- Built with Next.js 16 and React 19
- Handles login, signup, assessment forms, prediction history, patient management, settings, and admin monitoring
- Stores the backend access token in an HTTP-only cookie named `diasense_access_token`
- Uses server actions and server components to call the backend API

### Backend API

- Built with FastAPI
- Owns:
  - auth
  - role checks
  - assessment validation
  - prediction persistence
  - model metadata
  - drift and pipeline summaries
  - Prometheus metrics exposure
- Talks to PostgreSQL and the model-server

### Model-Server

- Runs `mlflow models serve`
- Serves the active MLflow Production model
- Exposes `/ping` and `/invocations`
- Keeps raw model loading and inference runtime separate from the backend API

### Pipeline Layer

- DVC covers `ingest`, `validate`, and `preprocess`
- Airflow covers:
  - end-to-end training and registration
  - monitoring and drift computation
- ML scripts produce artifacts and MLflow runs

### Monitoring Layer

- Prometheus scrapes metrics from the backend API
- Grafana visualizes infrastructure, backend, and pipeline dashboards
- Alertmanager is configured for notification fan-out
- The monitoring DAG emits drift metrics to a Prometheus text file artifact and stores drift rows in PostgreSQL

## Operational Flow

### Online Prediction Flow

1. A user signs in from the frontend.
2. The frontend stores the signed backend token in an HTTP-only cookie.
3. The user submits assessment values.
4. The frontend server action sends the request to `POST /api/v1/predict`.
5. The backend authenticates the caller and resolves the patient identity.
6. The backend writes a `prediction_requests` row.
7. The backend calls the model-server `/invocations` endpoint.
8. The backend resolves probability, risk band, interpretation, and explanation fields.
9. The backend writes a `prediction_results` row.
10. The frontend renders the result and later surfaces it in prediction history.

### Training Flow

1. Airflow triggers `diasense_training_pipeline`.
2. DVC stages ingest raw data, validate schema/ranges, and preprocess splits/features.
3. `train.py` trains logistic regression, random forest, and XGBoost candidates.
4. MLflow records nested experiment runs and model artifacts.
5. `evaluate.py` evaluates all candidates on the test split.
6. The best threshold-passing candidate is promoted to MLflow Production.
7. Airflow updates the backend-facing `model_versions` table.

### Monitoring Flow

1. Airflow triggers `diasense_monitoring_pipeline`.
2. Recent processed data is summarized into current feature statistics.
3. Current data is compared with the baseline training data.
4. Drift rows are stored in PostgreSQL.
5. Prometheus alert metrics are emitted.
6. Drift events are recorded for operations follow-up.

## Deployment Model

The current deployment model is container-first and single-stack:

- `frontend-ui`
- `backend-api`
- `model-server`
- `postgres`
- `mlflow-tracking`
- `minio`
- `ml`
- `airflow`
- `prometheus`
- `alertmanager`
- `grafana`

This is appropriate for a course/project environment because:

- service boundaries are explicit
- environment bootstrapping is simple
- reproducibility is high
- the same compose stack can support demo, testing, and documentation

## Security Assumptions

The current system assumes:

- a trusted internal or demo deployment perimeter
- single-origin use through the frontend and backend pair
- HTTPS and reverse-proxy hardening are handled outside this repo if deployed publicly
- the environment admin account is managed via env vars, not stored as a normal DB user
- backend tokens are HMAC-signed and time-bounded
- passwords for DB users are PBKDF2-SHA256 hashes
- frontend role restrictions are advisory only; backend role checks are authoritative

Known security trade-offs:

- several infra services use default demo credentials from `.env.example`
- the token format is signed but intentionally lightweight, not a full OAuth/JWT platform
- some operational endpoints such as pipeline and drift summary are not gated as tightly as the prediction endpoints

## Success Metrics

### Product Success

- authenticated users can sign up, sign in, and submit assessments
- patients can view only their own protected history
- clinicians and admins can assess other accounts and manage patient workflows

### ML Success

The evaluation stage checks these current minimum/maximum thresholds from `ml/params.yaml`:

- accuracy `>= 0.70`
- F1 `>= 0.60`
- ROC AUC `>= 0.75`
- log loss `<= 0.70`

### Operational Success

- backend `/health` returns `ok`
- backend `/ready` reflects dependency state
- the active model is present in `model_versions`
- Airflow DAGs can be triggered successfully
- Prometheus and Grafana expose backend and pipeline metrics
- the monitoring pipeline emits drift metrics and persists drift rows
