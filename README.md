# DiaSense

DiaSense is an end-to-end diabetes risk assessment platform with a Next.js clinic UI, a FastAPI backend API, an MLflow-backed model registry, an MLflow model-serving container, Airflow pipelines for training and monitoring, DVC for data preparation lineage, and Prometheus/Grafana for operational visibility.

## 1. Project Overview

The platform is built to:

- let patients, clinicians, and admins submit protected diabetes-risk assessments
- store prediction requests and results in PostgreSQL
- train, evaluate, and register candidate models through the ML workflow
- serve the active Production model through an MLflow model-server
- monitor feature drift on recent data and emit alert metrics for observability

## 2. Final Architecture Summary

The final runtime is split into these layers:

- `apps/frontend`: Next.js 16 clinic and marketing UI
- `apps/backend-api`: FastAPI 0.136.1 API, auth, prediction orchestration, ops endpoints, and metrics
- `model-server`: MLflow `models serve` process for `models:/diasense-diabetes-risk/Production`
- `ml`: DVC and ML scripts for ingest, validate, preprocess, train, and evaluate
- `airflow`: orchestration for `diasense_training_pipeline` and `diasense_monitoring_pipeline`
- observability: Prometheus, Alertmanager, and Grafana
- state and artifacts: PostgreSQL, MLflow tracking, and MinIO-backed artifact/DVC storage

See [docs/HLD.md](docs/HLD.md), [docs/LLD.md](docs/LLD.md), [docs/architecture.md](docs/architecture.md), [diagrams/high_level_architecture.mmd](diagrams/high_level_architecture.mmd), and [diagrams/low_level_architecture.mmd](diagrams/low_level_architecture.mmd).

## 3. Prerequisites

Recommended host prerequisites:

- Git
- Docker Engine
- Docker Compose v2

The repository is runnable without installing Python, Node, DVC, MLflow, or Airflow on the host because those are provided by the containers below.

## 4. Exact Packages/Tools To Install

Host tools:

- `git`
- `docker`
- `docker compose`

Repo-pinned runtime versions used by containers and lockfiles:

- Frontend build image: `node:24-alpine`
- Frontend runtime image: `node:22-alpine`
- Frontend framework: `next@16.1.7`
- Frontend React runtime: `react@19.2.5`, `react-dom@19.2.5`
- Frontend TypeScript: `typescript@5.9.3`
- Frontend package manager format: `pnpm-lock.yaml` lockfile version `9.0`
- Backend base image: `python:3.12-alpine`
- Backend API: `fastapi==0.136.1`
- Backend server: `uvicorn[standard]==0.46.0`
- Backend ORM: `sqlalchemy==2.0.49`
- Backend migrations: `alembic==1.18.4`
- Backend HTTP client: `httpx==0.28.1`
- Backend telemetry: `prometheus-client==0.25.0`
- Backend MLflow client: `mlflow==3.11.1`
- ML worker image: `python:3.12-slim`
- Airflow image: `apache/airflow:3.2.0-python3.12`
- PostgreSQL image: `postgres:17-alpine`
- Model-server image base: `python:3.12-alpine`
- Model-server package: `mlflow==3.11.1`

Version note:

- `docker-compose.yml` currently pins most images exactly, but the `mlflow-tracking`, `prometheus`, `alertmanager`, and `grafana` services still use `latest` tags. The ML code and model-server image are pinned to `mlflow==3.11.1`.

## 5. Clone And Configure

If you already have the repository locally, start at step 3.

```bash
export REPO_SOURCE="<path-or-url-to-the-diasense-repository>"
git clone "$REPO_SOURCE" diasense
cd diasense
cp .env.example .env
```

The provided `.env.example` sets these default externally reachable ports:

- Frontend: `3100`
- Backend API: `8000`
- Model-server: `5001`
- MLflow tracking: `5000`
- Airflow: `8080`
- Prometheus: `9090`
- Alertmanager: `9093`
- Grafana: `3001`
- MinIO API: `9000`
- MinIO Console: `9001`

## 6. Build, Migrate, Train, Serve, And Run

### 6.1 Build The Full Stack

```bash
docker compose build
```

### 6.2 Start The Full Stack

```bash
docker compose up -d
docker compose ps
```

### 6.3 Run Database Bootstrap And Migrations Explicitly

The backend container already runs bootstrap on startup, but this is the exact manual migration/bootstrap command:

```bash
docker compose exec backend-api python -c "import sys; sys.path.insert(0, '/app'); from app.db.bootstrap import main; main()"
```

### 6.4 Run The DVC Pipeline

Run DVC inside the `ml` container so the configured MinIO remote resolves correctly:

```bash
docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro"
```

That reproduces these DVC stages from `ml/dvc.yaml`:

- `ingest`
- `validate`
- `preprocess`

### 6.5 Trigger The Airflow Training DAG

```bash
docker compose exec airflow airflow dags trigger diasense_training_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_training_pipeline
```

The training DAG executes:

- `ingest`
- `validate`
- `preprocess`
- `train`
- `evaluate`
- `register`

### 6.6 Restart The Model-Server After Registration

The model-server serves `models:/diasense-diabetes-risk/Production` at process start. After a new Production version is registered, restart it so it resolves the latest promoted version:

```bash
docker compose restart model-server
docker compose logs --tail=100 model-server
```

### 6.7 Trigger The Monitoring DAG

```bash
docker compose exec airflow airflow dags trigger diasense_monitoring_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_monitoring_pipeline
```

The monitoring DAG executes:

- `recompute_current_feature_stats_from_recent_data`
- `compare_against_baseline`
- `persist_drift_report`
- `emit_alert_metrics`

## 7. Exact Commands To Launch Docker Compose

Minimal one-shot command:

```bash
docker compose up -d --build
```

Clean shutdown:

```bash
docker compose down
```

Shutdown and remove volumes:

```bash
docker compose down -v
```

## 8. Exact Commands To Run The DVC Pipeline

Recommended:

```bash
docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro"
```

If you want stage-by-stage execution:

```bash
docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro ingest"
docker compose exec ml bash -lc "cd /workspace/ml && dvc repro validate"
docker compose exec ml bash -lc "cd /workspace/ml && dvc repro preprocess"
```

## 9. Exact Commands To Trigger Airflow DAGs

Training:

```bash
docker compose exec airflow airflow dags trigger diasense_training_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_training_pipeline
```

Monitoring:

```bash
docker compose exec airflow airflow dags trigger diasense_monitoring_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_monitoring_pipeline
```

Optional task-level logs:

```bash
docker compose logs --tail=200 airflow
```

## 10. Access The Running Services

Assuming you copied `.env.example` to `.env` without changes:

- Frontend UI: `http://localhost:3100`
- Backend API root: `http://localhost:8000`
- Backend OpenAPI docs: `http://localhost:8000/docs`
- MLflow Tracking UI: `http://localhost:5000`
- Airflow UI: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

Helpful optional services:

- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Alertmanager: `http://localhost:9093`

Default credentials from `.env.example`:

- Frontend/backend environment admin login: `admin / admin`
- Airflow login: `admin / admin`
- Grafana login: `admin / admin`
- MinIO login: `minioadmin / minioadmin`

## 11. Reproduce A Training Run Using Git Commit Hash + MLflow Run ID + DVC Rev

Current repository example from the inspected workspace:

- Git commit hash: `4aa9e112dde2849fc4e9edbeec7b1ba63025b1f0`
- DVC revision recorded by the pipelines: `4aa9e112dde2849fc4e9edbeec7b1ba63025b1f0`
- Training parent MLflow run ID: `11264a7bddb848d59813160a5f7e10e6`
- Best model source run ID: `375d7924a94f4fe39a4b26037d74bcd3`
- Evaluation parent run ID: `8fac391629c64ef0b5a48aa0a9c9a3ed`
- Serving evaluation run ID for the selected model: `efc0267d98434f68a0e041edef7c48c5`
- Serving registered model version in `evaluation_summary.json`: `6`

Exact reproduction flow:

```bash
git checkout 4aa9e112dde2849fc4e9edbeec7b1ba63025b1f0
cp .env.example .env
docker compose up -d --build postgres minio minio-create-bucket mlflow-tracking ml airflow backend-api
docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc checkout && dvc repro"
docker compose exec airflow airflow dags trigger diasense_training_pipeline
docker compose exec airflow airflow dags list-runs -d diasense_training_pipeline
docker compose restart model-server
```

How the identifiers relate:

- `git_commit_hash` is stored in `pipeline_runs.git_commit_hash`
- `dvc_rev` is the same Git revision because `airflow/dags/_diasense_common.py` derives `dvc_revision()` from `git rev-parse HEAD`
- MLflow run IDs are written into `ml/artifacts/reports/train_summary.json` and `ml/artifacts/reports/evaluation_summary.json`

## 12. Troubleshooting

### Frontend loads, but assessment submit says the backend cannot be reached

Check the backend and frontend containers:

```bash
docker compose ps
docker compose logs --tail=200 backend-api
docker compose logs --tail=200 frontend-ui
```

### Monitor page shows no active model or predictions fail with no model being served

Run the training DAG, then restart the model-server:

```bash
docker compose exec airflow airflow dags trigger diasense_training_pipeline
docker compose restart model-server
docker compose logs --tail=200 model-server
```

### Backend returns `No active model available for inference`

The `model_versions` table does not yet have an active row. Trigger the training DAG so the `register` task updates the registry record.

### Airflow UI is up but the DAG is missing

Give the scheduler a moment to parse the mounted DAGs, then recheck:

```bash
docker compose logs --tail=200 airflow
```

### DVC fails on the host with MinIO errors

Run DVC inside the `ml` container:

```bash
docker compose exec ml bash -lc "cd /workspace/ml && dvc pull && dvc repro"
```

### MLflow opens but there are no experiments or models yet

That is expected before training. Trigger the training DAG, then refresh MLflow.

### Monitoring DAG fails in `emit_alert_metrics`

The task has been hardened to tolerate malformed feature entries and best-effort bookkeeping failures while still writing the Prometheus metrics file. If it still fails, inspect the DAG logs:

```bash
docker compose logs --tail=300 airflow
```

## 13. Alpine Exceptions Note

This repo uses Alpine where it is practical:

- backend-api: `python:3.12-alpine`
- model-server build: `python:3.12-alpine`
- frontend build/runtime: `node:24-alpine` and `node:22-alpine`
- postgres: `postgres:17-alpine`

Non-Alpine exceptions were kept where they were operationally safer:

- `apache/airflow:3.2.0-python3.12` is used because Airflow and its dependency graph are much easier to run reliably on the upstream Airflow base image.
- `python:3.12-slim` is used for the `ml` container because scientific Python packages and build tooling are more predictable there than on Alpine.
- `ghcr.io/mlflow/mlflow:latest` is used for the tracking server because the compose stack currently relies on the upstream tracking image directly.

## Documentation Index

- [docs/HLD.md](docs/HLD.md)
- [docs/LLD.md](docs/LLD.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/test-plan.md](docs/test-plan.md)
- [docs/test-report-template.md](docs/test-report-template.md)
- [docs/user-manual.md](docs/user-manual.md)
- [docs/project_report.md](docs/project_report.md)
- [diagrams/high_level_architecture.mmd](diagrams/high_level_architecture.mmd)
- [diagrams/low_level_architecture.mmd](diagrams/low_level_architecture.mmd)
