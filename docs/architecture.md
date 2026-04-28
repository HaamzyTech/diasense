# Architecture

## Purpose

This document is the runtime architecture companion to the higher-level [HLD](HLD.md) and the contract-focused [LLD](LLD.md). It summarizes what runs, where state lives, and how the online, training, and monitoring planes interact.

## Architecture Artifacts

- High-level diagram: [../diagrams/high_level_architecture.mmd](../diagrams/high_level_architecture.mmd)
- Low-level diagram: [../diagrams/low_level_architecture.mmd](../diagrams/low_level_architecture.mmd)

## Runtime Topology

| Service | Tech/Image | Primary Responsibility | State/Dependency | External Port |
| --- | --- | --- | --- | --- |
| `frontend-ui` | Next.js 16, React 19, `node:24-alpine` build and `node:22-alpine` runtime | Web UI, server actions, session cookie handling | Calls backend API | `3100` from `.env.example` |
| `backend-api` | FastAPI, SQLAlchemy, `python:3.12-alpine` | Auth, prediction orchestration, ops APIs, Prometheus metrics | PostgreSQL, model-server, MLflow tracking | `8000` |
| `model-server` | `mlflow models serve`, `mlflow==3.11.1` | Runtime inference for Production MLflow model | MLflow tracking and artifact store | `5001` |
| `postgres` | `postgres:17-alpine` | Application relational state | Local Docker volume | `5432` |
| `mlflow-tracking` | Upstream MLflow tracking image | Experiment tracking and model registry | SQLite file + MinIO artifacts | `5000` |
| `minio` | MinIO | Artifact store and DVC remote | Local Docker volume | `9000`, `9001` |
| `ml` | `python:3.12-slim` | DVC, ML scripts, manual experiment execution | MinIO, MLflow, mounted repo | none |
| `airflow` | `apache/airflow:3.2.0-python3.12` | Pipeline orchestration | PostgreSQL, MLflow, mounted repo | `8080` |
| `prometheus` | Prometheus | Metrics collection and alert rule evaluation | Scrapes backend metrics | `9090` |
| `alertmanager` | Alertmanager | Alert routing | SMTP configuration | `9093` |
| `grafana` | Grafana OSS | Dashboards | Prometheus datasource | `3001` |

## Data Plane

The system has three primary data stores:

- PostgreSQL for application and pipeline metadata
- MLflow tracking for experiments, model registry, and model lineage
- MinIO for artifacts and the DVC remote

### PostgreSQL-Owned State

- users
- prediction requests
- prediction results
- drift rows
- pipeline runs
- feedback labels
- system events

### MLflow-Owned State

- training/evaluation experiment runs
- logged metrics
- model registry versions
- model URIs like `models:/diasense-diabetes-risk/Production`

### MinIO-Owned State

- DVC remote objects at `s3://mlflow/dvc`
- MLflow model artifacts and logged artifacts

## Control Plane

### Online Control Plane

- Next.js server actions call the FastAPI API
- FastAPI validates, persists, and calls the model-server
- the backend exposes `/metrics` for Prometheus

### Training Control Plane

- Airflow triggers DVC stages and ML scripts
- ML scripts log to MLflow and write local report artifacts
- the `register` task updates the backend-facing `model_versions` table
- operators restart the model-server to pick up the new Production version

### Monitoring Control Plane

- Airflow computes drift from baseline versus recent processed data
- drift is stored in PostgreSQL
- drift metrics are emitted as a Prometheus text artifact
- Prometheus and Grafana expose the operational picture

## Runtime Sequences

### Sequence A: Interactive Assessment

1. User signs in via `/login` or `/signup`.
2. Frontend stores the backend bearer token in `diasense_access_token`.
3. User submits assessment values through the clinic UI.
4. Backend authenticates and resolves the target patient.
5. Backend inserts `prediction_requests`.
6. Backend calls the model-server.
7. Backend inserts `prediction_results`.
8. Frontend shows risk band, probability, latency, and top factors.

### Sequence B: Model Refresh

1. DVC reproduces `ingest`, `validate`, and `preprocess`.
2. Airflow training DAG runs `train.py`.
3. Candidate models are logged to MLflow.
4. `evaluate.py` applies threshold checks and promotes the best eligible candidate.
5. `register` writes or updates the active row in `model_versions`.
6. Model-server is restarted to resolve the latest Production model.

### Sequence C: Drift Monitoring

1. Monitoring DAG loads the training baseline and current processed data.
2. PSI, KS statistic, and mean-shift metrics are computed per feature.
3. Drift rows are persisted.
4. Prometheus text metrics are emitted.
5. Dashboards and alerts consume the operational output.

## Security And Trust Boundaries

Primary trust boundaries:

- browser to frontend
- frontend to backend
- backend to PostgreSQL
- backend to model-server
- Airflow/ML tooling to MLflow and MinIO

Implemented controls:

- backend-signed access tokens with expiry
- password hashing with PBKDF2-SHA256
- backend role checks for protected operations
- HTTP-only frontend session cookie storage

Assumed controls outside repo scope:

- TLS termination
- reverse proxy hardening
- secret rotation
- production-grade identity federation

## Deployment Notes

- the compose stack is the reference deployment shape for this repository
- backend migrations are handled through `app.db.bootstrap`
- MLflow tracking metadata currently uses SQLite, not PostgreSQL
- the environment admin login is configuration-backed rather than persisted as a normal DB row
- the training pipeline currently does not wire the commented final record task in `diasense_training_pipeline.py`

## Known Architectural Constraints

- model-server refresh is not automatic after MLflow stage promotion
- MLflow tracking image is not pinned in `docker-compose.yml`
- some operational endpoints are open by implementation choice and should be reviewed before public deployment
- the drift summary service currently expects `stable` row values while the monitoring DAG emits `ok`
