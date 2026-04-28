# Low-Level Design

## 1. Scope

This document captures the concrete runtime contracts for the DiaSense system:

- API endpoints
- request and response payloads
- database schema
- model-server invocation contract
- DVC and Airflow stage flow
- online and offline data movement
- error handling behavior

## 2. API Conventions

Base URL:

- `http://<backend-host>:8000/api/v1`

Authentication:

- protected endpoints expect `Authorization: Bearer <access_token>`
- `/logout` and `/me` can also accept `access_token` in the request body

Error envelope:

```json
{
  "detail": "Human-readable message",
  "error_code": "validation_error",
  "request_id": "uuid-or-null"
}
```

Validation errors use FastAPI/Pydantic detail arrays under `detail`.

## 3. Exact Endpoint Definitions

### 3.1 Auth Endpoints

#### `POST /signup`

- Auth: none
- Request:

```json
{
  "username": "string | null",
  "email": "string | null",
  "password": "string"
}
```

- Response `201`:

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 43200,
  "user": {
    "username": "string",
    "email": "string | null",
    "role": "patient | clinician | admin",
    "auth_source": "database | environment"
  }
}
```

#### `POST /login`

- Auth: none
- Request:

```json
{
  "username": "string",
  "password": "string"
}
```

- Response `200`: same shape as `/signup`

#### `POST /logout`

- Auth: bearer token or `access_token` in body
- Request:

```json
{
  "access_token": "string | null"
}
```

- Response `200`:

```json
{
  "message": "Logged out successfully"
}
```

#### `POST /me`

- Auth: bearer token or `access_token` in body
- Request:

```json
{
  "access_token": "string | null"
}
```

- Response `200`:

```json
{
  "user": {
    "username": "string",
    "email": "string | null",
    "role": "patient | clinician | admin",
    "auth_source": "database | environment"
  },
  "session_expires_at": "ISO-8601 string"
}
```

#### `POST /reset-password`

- Auth: optional bearer token or `access_token`
- Request:

```json
{
  "current_password": "string",
  "new_password": "string",
  "access_token": "string | null"
}
```

- Response `200`:

```json
{
  "message": "Password updated successfully"
}
```

### 3.2 Health And Ops Endpoints

#### `GET /health`

- Auth: none
- Response:

```json
{
  "status": "ok",
  "service": "backend-api",
  "version": "0.1.0",
  "timestamp": "ISO-8601 string"
}
```

#### `GET /ready`

- Auth: none
- Response `200` or `503`:

```json
{
  "status": "ready | not_ready",
  "service": "backend-api",
  "version": "0.1.0",
  "dependencies": {
    "postgres": "ok | error",
    "model_server": "ok | error",
    "mlflow_tracking": "ok | error"
  },
  "timestamp": "ISO-8601 string"
}
```

#### `GET /ops/summary`

- Auth: admin only
- Response:

```json
{
  "service": "backend-api",
  "version": "0.1.0",
  "services": {
    "postgres": "ok | error",
    "model_server": "ok | error",
    "mlflow_tracking": "ok | error"
  },
  "active_model": {
    "model_name": "string",
    "model_version": "string",
    "stage": "string"
  },
  "latest_pipeline_status": "queued | running | success | failed | unknown",
  "latest_drift_status": "stable | attention | unknown",
  "timestamp": "ISO-8601 string"
}
```

### 3.3 Model Metadata Endpoint

#### `GET /model/info`

- Auth: none
- Response:

```json
{
  "model_name": "string",
  "model_version": "string",
  "algorithm": "string",
  "stage": "string",
  "mlflow_run_id": "string",
  "mlflow_model_uri": "string",
  "metrics": {
    "key": "number | string | boolean"
  },
  "params": {
    "key": "number | string | boolean"
  },
  "created_at": "ISO-8601 string | null"
}
```

### 3.4 Prediction Endpoints

#### `POST /predict`

- Auth: required
- Request:

```json
{
  "patient_email": "string | null",
  "pregnancies": 0,
  "glucose": 138.0,
  "blood_pressure": 72.0,
  "skin_thickness": 35.0,
  "insulin": 0.0,
  "bmi": 33.6,
  "diabetes_pedigree_function": 0.627,
  "age": 50
}
```

- Field constraints:
  - `pregnancies`: `0..30`
  - `glucose`: `0..300`
  - `blood_pressure`: `0..200`
  - `skin_thickness`: `0..100`
  - `insulin`: `0..1000`
  - `bmi`: `0..100`
  - `diabetes_pedigree_function`: `0..10`
  - `age`: `1..120`
- Response:

```json
{
  "request_id": "uuid",
  "model_version_id": "uuid",
  "submitted_by": "string",
  "patient_email": "string",
  "predicted_label": true,
  "risk_probability": 0.8123,
  "risk_band": "low | moderate | high",
  "interpretation": "string",
  "top_factors": [
    {
      "feature": "string",
      "importance": 0.41
    }
  ],
  "latency_ms": 42,
  "created_at": "ISO-8601 string"
}
```

#### `POST /my-predictions`

- Auth: required
- Request:

```json
{
  "limit": 20
}
```

- Response:

```json
{
  "items": [
    {
      "request_id": "uuid",
      "submitted_by": "string",
      "patient_email": "string",
      "actor_role": "string",
      "risk_probability": 0.81,
      "risk_band": "high",
      "predicted_label": true,
      "interpretation": "string",
      "created_at": "ISO-8601 string | null"
    }
  ],
  "count": 1
}
```

#### `GET /predictions`

- Auth: required
- Query params:
  - `patient_email: string | null`
  - `limit: int` with `1..100`
- Response: same shape as `/my-predictions`

#### `GET /predictions/{request_id}`

- Auth: required
- Response:

```json
{
  "request": {
    "id": "uuid",
    "session_id": "uuid",
    "submitted_by": "string",
    "patient_email": "string",
    "actor_role": "string",
    "pregnancies": 2,
    "glucose": 138.0,
    "blood_pressure": 72.0,
    "skin_thickness": 35.0,
    "insulin": 0.0,
    "bmi": 33.6,
    "diabetes_pedigree_function": 0.627,
    "age": 50,
    "source": "web",
    "created_at": "ISO-8601 string"
  },
  "result": {
    "id": "uuid | null",
    "model_version_id": "uuid | null",
    "predicted_label": true,
    "risk_probability": 0.8123,
    "risk_band": "high",
    "interpretation": "string | null",
    "top_factors": [
      {
        "feature": "string",
        "importance": 0.41
      }
    ],
    "latency_ms": 42,
    "created_at": "ISO-8601 string | null"
  }
}
```

#### `DELETE /predictions/{request_id}`

- Auth: required
- Response:

```json
{
  "message": "Prediction result deleted successfully",
  "request_id": "uuid",
  "patient_email": "string",
  "submitted_by": "string",
  "actor_role": "string",
  "deleted_at": "ISO-8601 string"
}
```

### 3.5 User And Patient Endpoints

#### `GET /users`

- Auth: admin only
- Query params:
  - `limit: int` with `1..500`
- Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "username": "string",
      "email": "string | null",
      "role": "patient | clinician | admin",
      "created_at": "ISO-8601 string"
    }
  ],
  "count": 1
}
```

#### `PATCH /users/{user_id}/role`

- Auth: admin only
- Request:

```json
{
  "role": "patient | clinician | admin"
}
```

- Response:

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string | null",
  "role": "patient | clinician | admin",
  "created_at": "ISO-8601 string"
}
```

#### `DELETE /users/{user_id}`

- Auth: admin only
- Response:

```json
{
  "message": "User deleted successfully",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string | null",
    "role": "patient | clinician | admin",
    "created_at": "ISO-8601 string"
  }
}
```

#### `POST /patients`

- Auth: clinician or admin
- Request:

```json
{
  "username": "string | null",
  "email": "string | null",
  "password": "string"
}
```

- Response:

```json
{
  "message": "Patient account created successfully",
  "patient": {
    "id": "uuid",
    "username": "string",
    "email": "string | null",
    "role": "patient | clinician | admin",
    "created_at": "ISO-8601 string"
  }
}
```

#### `GET /patients`

- Auth: clinician or admin
- Query params:
  - `limit: int` with `1..500`
- Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "username": "string",
      "email": "string | null",
      "role": "patient | clinician | admin",
      "created_at": "ISO-8601 string",
      "assessment_count": 0,
      "last_assessed_at": "ISO-8601 string | null",
      "latest_risk_band": "string | null",
      "latest_risk_probability": 0.7345
    }
  ],
  "count": 1
}
```

#### `DELETE /patients/{patient_id}`

- Auth: clinician or admin
- Response:

```json
{
  "message": "Patient account deleted successfully",
  "patient": {
    "id": "uuid",
    "username": "string",
    "email": "string | null",
    "role": "patient | clinician | admin",
    "created_at": "ISO-8601 string"
  }
}
```

### 3.6 Pipeline, Drift, And Feedback Endpoints

#### `GET /pipeline/runs`

- Auth: none
- Query params:
  - `limit: int` with `1..100`
- Response:

```json
{
  "items": [
    {
      "id": "uuid | null",
      "pipeline_name": "string",
      "airflow_dag_id": "string",
      "airflow_run_id": "string",
      "status": "queued | running | success | failed",
      "mlflow_run_id": "string | null",
      "started_at": "ISO-8601 string | null",
      "ended_at": "ISO-8601 string | null",
      "duration_seconds": 123
    }
  ],
  "count": 1
}
```

#### `GET /drift/latest`

- Auth: none
- Response:

```json
{
  "report_date": "YYYY-MM-DD",
  "overall_status": "stable | attention | unknown",
  "features": [
    {
      "feature_name": "string",
      "baseline_mean": 1.0,
      "current_mean": 1.1,
      "baseline_variance": 0.4,
      "current_variance": 0.5,
      "psi": 0.02,
      "ks_stat": 0.01,
      "status": "string"
    }
  ]
}
```

#### `POST /feedback`

- Auth: none in current implementation
- Request:

```json
{
  "request_id": "uuid",
  "ground_truth_label": true,
  "label_source": "manual",
  "notes": "string | null"
}
```

- Response:

```json
{
  "message": "Feedback recorded",
  "feedback_id": "uuid",
  "request_id": "uuid"
}
```

## 4. Model-Server Contract

Backend dependency:

- base URL: `MODEL_SERVER_URL`, default `http://model-server:5001`

Endpoints used by the backend:

### `GET /ping`

- Used by health checks
- Expected status: `<500`

### `POST /invocations`

- Request shape:

```json
{
  "dataframe_records": [
    {
      "pregnancies": 2,
      "glucose": 138.0,
      "blood_pressure": 72.0,
      "skin_thickness": 35.0,
      "insulin": 0.0,
      "bmi": 33.6,
      "bmi_group": "obese",
      "diabetes_pedigree_function": 0.627,
      "age": 50,
      "age_band": "middle_age"
    }
  ]
}
```

- Accepted response forms by `ModelServerClient`:
  - list of dicts
  - list of scalar predictions
  - object with `predictions: [...]`
- Normalized output fields:
  - `predicted_label: bool`
  - or `risk_probability: float`
  - optional `top_factors: [{feature, importance}]`

## 5. Exact Database Schema

### 5.1 Enums

- `actor_role`: `patient`, `clinician`, `admin`
- `pipeline_status`: `queued`, `running`, `success`, `failed`
- `risk_band`: `low`, `moderate`, `high`

### 5.2 Tables

#### `auth_users`

- `id UUID PK default gen_random_uuid()`
- `username VARCHAR(50) NOT NULL UNIQUE`
- `email VARCHAR(255) NULL`
- `password_hash TEXT NOT NULL`
- `role VARCHAR(50) NOT NULL default 'patient'`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Indexes:

- `ix_auth_users_username` unique
- `ix_auth_users_email` unique

#### `model_versions`

- `id UUID PK default gen_random_uuid()`
- `model_name VARCHAR(100) NOT NULL default 'diasense-diabetes-risk'`
- `model_version VARCHAR(50) NOT NULL`
- `mlflow_run_id VARCHAR(64) NOT NULL`
- `mlflow_model_uri TEXT NOT NULL`
- `algorithm VARCHAR(100) NOT NULL`
- `metrics JSONB NOT NULL default '{}'`
- `params JSONB NOT NULL default '{}'`
- `stage VARCHAR(30) NOT NULL default 'staging'`
- `is_active BOOLEAN NOT NULL default false`
- `created_at TIMESTAMPTZ NOT NULL default now()`

#### `prediction_requests`

- `id UUID PK default gen_random_uuid()`
- `session_id UUID NOT NULL`
- `submitted_by VARCHAR(255) NOT NULL`
- `patient_email VARCHAR(255) NOT NULL`
- `actor_role actor_role NOT NULL`
- `pregnancies INTEGER NOT NULL check 0..30`
- `glucose NUMERIC(6,2) NOT NULL check 0..300`
- `blood_pressure NUMERIC(6,2) NOT NULL check 0..200`
- `skin_thickness NUMERIC(6,2) NOT NULL check 0..100`
- `insulin NUMERIC(8,2) NOT NULL check 0..1000`
- `bmi NUMERIC(6,2) NOT NULL check 0..100`
- `diabetes_pedigree_function NUMERIC(8,4) NOT NULL check 0..10`
- `age INTEGER NOT NULL check 1..120`
- `source VARCHAR(30) NOT NULL default 'web'`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Indexes:

- `ix_prediction_requests_session_id`
- `ix_prediction_requests_created_at`
- `ix_prediction_requests_patient_email_created_at`
- `ix_prediction_requests_submitted_by_created_at`

#### `prediction_results`

- `id UUID PK default gen_random_uuid()`
- `request_id UUID NOT NULL UNIQUE FK prediction_requests(id) on delete cascade`
- `model_version_id UUID NOT NULL FK model_versions(id)`
- `predicted_label BOOLEAN NOT NULL`
- `risk_probability NUMERIC(5,4) NOT NULL check 0..1`
- `risk_band risk_band NOT NULL`
- `explanation JSONB NOT NULL default '{}'`
- `latency_ms INTEGER NOT NULL check >= 0`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Index:

- `ix_prediction_results_model_version_id`

#### `feedback_labels`

- `id UUID PK default gen_random_uuid()`
- `request_id UUID NOT NULL FK prediction_requests(id) on delete cascade`
- `ground_truth_label BOOLEAN NOT NULL`
- `label_source VARCHAR(50) NOT NULL default 'manual'`
- `notes TEXT NULL`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Index:

- `ix_feedback_labels_request_id`

#### `drift_reports`

- `id UUID PK default gen_random_uuid()`
- `pipeline_run_id UUID NULL`
- `feature_name VARCHAR(100) NOT NULL`
- `baseline_mean DOUBLE PRECISION NOT NULL`
- `current_mean DOUBLE PRECISION NOT NULL`
- `baseline_variance DOUBLE PRECISION NOT NULL`
- `current_variance DOUBLE PRECISION NOT NULL`
- `psi DOUBLE PRECISION NULL`
- `ks_stat DOUBLE PRECISION NULL`
- `status VARCHAR(20) NOT NULL`
- `report_date DATE NOT NULL default CURRENT_DATE`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Index:

- `ix_drift_reports_report_date`

#### `pipeline_runs`

- `id UUID PK default gen_random_uuid()`
- `pipeline_name VARCHAR(100) NOT NULL`
- `airflow_dag_id VARCHAR(100) NOT NULL`
- `airflow_run_id VARCHAR(100) NOT NULL`
- `git_commit_hash VARCHAR(64) NULL`
- `dvc_rev VARCHAR(64) NULL`
- `mlflow_run_id VARCHAR(64) NULL`
- `status pipeline_status NOT NULL`
- `started_at TIMESTAMPTZ NULL`
- `ended_at TIMESTAMPTZ NULL`
- `duration_seconds INTEGER NULL`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Indexes:

- `ix_pipeline_runs_status`
- `ix_pipeline_runs_created_at`

#### `system_events`

- `id UUID PK default gen_random_uuid()`
- `service_name VARCHAR(100) NOT NULL`
- `severity VARCHAR(20) NOT NULL`
- `message TEXT NOT NULL`
- `metadata JSONB NOT NULL default '{}'`
- `created_at TIMESTAMPTZ NOT NULL default now()`

Index:

- `ix_system_events_service_name_created_at`

## 6. Data Flow: UI To Backend To Model-Server To Database

### Assessment Submission

1. `apps/frontend/components/clinic/assessment-form.tsx` submits the form to `assessmentAction`.
2. `apps/frontend/lib/clinic/actions.ts` validates numeric ranges client-side/server-action-side.
3. `apps/frontend/lib/clinic/server.ts` calls `POST /api/v1/predict`.
4. `apps/backend-api/app/api/v1/endpoints/predict.py` resolves the authenticated user.
5. `PredictionService.create_prediction()`:
   - resolves patient ownership
   - writes `prediction_requests`
   - calls model-server `/invocations`
   - derives probability and risk band
   - writes `prediction_results`
6. The frontend revalidates `/clinic`, `/clinic/predictions`, and `/clinic/patients`.

### Prediction History

1. Frontend calls `GET /predictions` or legacy `POST /my-predictions`.
2. Backend joins `prediction_requests` and `prediction_results`.
3. The UI lists summary cards and lets the user open `GET /predictions/{request_id}`.

## 7. Airflow DAG Flow

### `diasense_training_pipeline`

Order:

1. `ingest`
2. `validate`
3. `preprocess`
4. `train`
5. `evaluate`
6. `register`

Task behavior:

- the first three tasks call `run_dvc_stage()`
- `train` and `evaluate` call the ML Python scripts directly
- `register` updates the backend `model_versions` table from `evaluation_summary.json`

### `diasense_monitoring_pipeline`

Order:

1. `recompute_current_feature_stats_from_recent_data`
2. `compare_against_baseline`
3. `persist_drift_report`
4. `emit_alert_metrics`

Task behavior:

- current feature stats are built from `ml/data/processed/processed.csv`
- baseline comes from `ml/data/features/train.csv`
- drift rows are persisted into `drift_reports`
- Prometheus text metrics are written to `ml/artifacts/reports/drift_alert_metrics.prom`

## 8. DVC Stage Flow

### `ingest`

- downloads the raw Pima diabetes CSV from GitHub
- writes:
  - `data/raw/diabetes.csv`
  - `artifacts/reports/raw_metrics.json`
  - `artifacts/reports/raw_schema.json`

### `validate`

- enforces expected column order
- renames columns using `schema.rename_map`
- counts suspicious value ranges
- writes:
  - `data/validated/validated.csv`
  - `artifacts/reports/validation_report.json`

### `preprocess`

- replaces configured zeros with missing values
- imputes medians
- adds `bmi_group` and `age_band`
- stratifies into train/val/test
- computes and applies clipping bounds
- writes:
  - `data/processed/raw_snapshot.csv`
  - `data/processed/processed.csv`
  - `data/features/train.csv`
  - `data/features/val.csv`
  - `data/features/test.csv`
  - `artifacts/reports/preprocessing_artifact.json`

## 9. Error Handling Behavior

### Backend Error Types

- `AuthenticationError` -> `401`
- `AuthorizationError` -> `403`
- `NotFoundError` -> `404`
- `ConflictError` -> `409`
- `ValidationError` -> `422`
- `DependencyError` -> `503`
- unhandled `SQLAlchemyError` -> `500` with `Database error`
- unhandled generic exception -> `500` with `Internal server error`

### Prediction-Specific Failure Cases

- no active model in `model_versions` -> `503`
- model-server connection or invocation failure -> `503`
- missing or invalid patient target -> `422`
- patient trying to assess another user -> `403`
- missing prediction request on detail/delete -> `404`

### Frontend Behavior

- monitor, patients, users, and predictions pages catch backend failures and render inline notices
- assessment submit returns clear error text instead of raw network errors
- if the backend is unreachable, the frontend now surfaces a service-unavailable message

### Monitoring Pipeline Behavior

- `emit_alert_metrics` tolerates malformed feature items by filtering to dictionary entries
- system event persistence and pipeline finalization are best-effort inside that step
- if metric generation itself fails, the task still marks the pipeline run as failed and raises

## 10. Current Implementation Notes

- `drift_reports.status` rows are populated as `ok`, `drift`, or `insufficient_data`
- `DriftService.latest()` currently reports `stable` only when all rows equal `stable`, so `overall_status` may resolve to `attention` even when rows are `ok`
- the model-server must be restarted after a newly promoted MLflow Production model is registered, because the serve process resolves the Production URI at startup
