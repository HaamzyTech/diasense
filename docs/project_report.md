# DiaSense Project Report

## 1. Executive Summary

DiaSense is a full-stack ML-enabled clinical risk assessment system that combines:

- a protected web application
- a backend inference and persistence API
- ML training and evaluation workflows
- model registry and model serving
- data drift monitoring
- operational observability

The project demonstrates an end-to-end MLOps workflow rather than only a standalone classifier.

## 2. Problem Statement

Healthcare-oriented prediction tools often fail when they are delivered only as notebooks or isolated scripts. The main project goal was to produce a working operational system where:

- model training is reproducible
- inference is exposed through a protected application surface
- prediction history is persisted
- the serving model is traceable through MLflow
- monitoring detects potential feature drift over time

## 3. Delivered Solution

The delivered solution includes:

- Next.js clinic frontend with login, signup, assessment, history, settings, patient management, user management, and admin monitoring
- FastAPI backend with signed-token auth, role checks, prediction orchestration, persistence, and metrics
- MLflow model registry and a dedicated model-server for Production inference
- DVC-driven data preparation
- Airflow DAGs for training and monitoring
- Prometheus, Grafana, and Alertmanager for observability

## 4. Architecture Summary

Core runtime components:

- `frontend-ui`
- `backend-api`
- `model-server`
- `postgres`
- `mlflow-tracking`
- `minio`
- `ml`
- `airflow`
- `prometheus`
- `grafana`
- `alertmanager`

Design intent:

- keep user experience and backend inference separate
- keep online inference and offline training separate
- keep relational state and experiment tracking separate
- make both pipeline orchestration and observability first-class project elements

## 5. Training And Evaluation Outcome

Current recorded artifacts in `ml/artifacts/reports` show:

- training parent run ID: `11264a7bddb848d59813160a5f7e10e6`
- evaluation parent run ID: `8fac391629c64ef0b5a48aa0a9c9a3ed`
- best training candidate: `logistic_regression`
- best source run ID: `375d7924a94f4fe39a4b26037d74bcd3`
- current serving registered model version from `evaluation_summary.json`: `6`

Current best recorded test metrics for the promoted candidate:

- Accuracy: `0.7922`
- Precision: `0.6774`
- Recall: `0.7778`
- F1: `0.7241`
- Balanced accuracy: `0.7889`
- ROC AUC: `0.8844`
- Average precision: `0.8201`
- Log loss: `0.4314`

These satisfy the configured evaluation thresholds:

- accuracy `>= 0.70`
- F1 `>= 0.60`
- ROC AUC `>= 0.75`
- log loss `<= 0.70`

## 6. Monitoring Outcome

The inspected current drift artifact reports:

- generated at: `2026-04-27T05:05:19.340658+00:00`
- drift detected: `false`

Operational interpretation:

- the current processed data appears close to the stored baseline for all configured numeric features
- the monitoring DAG emits Prometheus-compatible metrics and persists drift rows for later review

## 7. Reproducibility

Current inspected source revision:

- Git commit hash: `4aa9e112dde2849fc4e9edbeec7b1ba63025b1f0`

Current pipeline lineage behavior:

- `pipeline_runs.git_commit_hash` stores the Git commit hash
- `pipeline_runs.dvc_rev` stores the same Git revision by implementation
- MLflow artifacts store the run-level experiment lineage
- `train_summary.json` and `evaluation_summary.json` capture the selected model information

This gives reproducibility across:

- source code version
- DVC-processed data version
- model training run
- evaluation run
- promoted model registry version

## 8. Testing Status

Existing automated coverage includes:

- backend auth service behavior
- backend auth and predict endpoints
- backend health and metrics endpoints
- backend bootstrap revision inference
- prediction service probability and feature engineering behavior
- ML candidate selection and registration gating logic

This does not replace full end-to-end acceptance testing, but it establishes a working regression base for the core contracts.

## 9. Key Implementation Notes

Positive implementation choices:

- HTTP-only cookie storage in the frontend
- backend-enforced role checks
- explicit prediction ownership columns
- MLflow registry promotion only after threshold-passing evaluation
- Airflow orchestration over both training and monitoring

Current operational constraints:

- model-server must be restarted after a new Production model is registered
- MLflow tracking image is not version-pinned in compose
- drift row status naming and backend drift summary semantics are slightly misaligned

## 10. Risks And Future Work

Recommended next improvements:

- pin all `latest` container tags
- automate model-server refresh on MLflow Promotion events
- align monitoring row statuses with backend summary logic
- add authenticated protection to non-public operational endpoints where needed
- add API integration tests for users, patients, and ops flows
- add CI for the Airflow DAGs and DVC pipeline
- add production-grade secret management and TLS termination

## 11. Conclusion

DiaSense successfully demonstrates a complete MLOps delivery path:

- data preparation with DVC
- multi-model training and evaluation with MLflow
- model promotion and serving
- authenticated application consumption
- persistent prediction history
- drift monitoring and operator dashboards

The project is not just a trained model; it is a deployable, inspectable, and reproducible ML application stack.
