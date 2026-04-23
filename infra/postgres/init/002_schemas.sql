DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'actor_role') THEN
        CREATE TYPE actor_role AS ENUM ('patient', 'clinician', 'admin');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pipeline_status') THEN
        CREATE TYPE pipeline_status AS ENUM ('queued', 'running', 'success', 'failed');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_band') THEN
        CREATE TYPE risk_band AS ENUM ('low', 'moderate', 'high');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL DEFAULT 'diasense-diabetes-risk',
    model_version VARCHAR(50) NOT NULL,
    mlflow_run_id VARCHAR(64) NOT NULL,
    mlflow_model_uri TEXT NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    stage VARCHAR(30) NOT NULL DEFAULT 'staging',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prediction_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    actor_role actor_role NOT NULL,
    pregnancies INTEGER NOT NULL CHECK (pregnancies >= 0 AND pregnancies <= 30),
    glucose NUMERIC(6,2) NOT NULL CHECK (glucose >= 0 AND glucose <= 300),
    blood_pressure NUMERIC(6,2) NOT NULL CHECK (blood_pressure >= 0 AND blood_pressure <= 200),
    skin_thickness NUMERIC(6,2) NOT NULL CHECK (skin_thickness >= 0 AND skin_thickness <= 100),
    insulin NUMERIC(8,2) NOT NULL CHECK (insulin >= 0 AND insulin <= 1000),
    bmi NUMERIC(6,2) NOT NULL CHECK (bmi >= 0 AND bmi <= 100),
    diabetes_pedigree_function NUMERIC(8,4) NOT NULL CHECK (diabetes_pedigree_function >= 0 AND diabetes_pedigree_function <= 10),
    age INTEGER NOT NULL CHECK (age >= 1 AND age <= 120),
    source VARCHAR(30) NOT NULL DEFAULT 'web',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prediction_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL UNIQUE REFERENCES prediction_requests(id) ON DELETE CASCADE,
    model_version_id UUID NOT NULL REFERENCES model_versions(id),
    predicted_label BOOLEAN NOT NULL,
    risk_probability NUMERIC(5,4) NOT NULL CHECK (risk_probability >= 0 AND risk_probability <= 1),
    risk_band risk_band NOT NULL,
    explanation JSONB NOT NULL DEFAULT '{}'::jsonb,
    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES prediction_requests(id) ON DELETE CASCADE,
    ground_truth_label BOOLEAN NOT NULL,
    label_source VARCHAR(50) NOT NULL DEFAULT 'manual',
    notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drift_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NULL,
    feature_name VARCHAR(100) NOT NULL,
    baseline_mean DOUBLE PRECISION NOT NULL,
    current_mean DOUBLE PRECISION NOT NULL,
    baseline_variance DOUBLE PRECISION NOT NULL,
    current_variance DOUBLE PRECISION NOT NULL,
    psi DOUBLE PRECISION NULL,
    ks_stat DOUBLE PRECISION NULL,
    status VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(100) NOT NULL,
    airflow_dag_id VARCHAR(100) NOT NULL,
    airflow_run_id VARCHAR(100) NOT NULL,
    git_commit_hash VARCHAR(64) NULL,
    dvc_rev VARCHAR(64) NULL,
    mlflow_run_id VARCHAR(64) NULL,
    status pipeline_status NOT NULL,
    started_at TIMESTAMPTZ NULL,
    ended_at TIMESTAMPTZ NULL,
    duration_seconds INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_prediction_requests_session_id ON prediction_requests(session_id);
CREATE INDEX IF NOT EXISTS ix_prediction_requests_created_at ON prediction_requests(created_at);
CREATE INDEX IF NOT EXISTS ix_prediction_results_model_version_id ON prediction_results(model_version_id);
CREATE INDEX IF NOT EXISTS ix_feedback_labels_request_id ON feedback_labels(request_id);
CREATE INDEX IF NOT EXISTS ix_drift_reports_report_date ON drift_reports(report_date);
CREATE INDEX IF NOT EXISTS ix_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS ix_pipeline_runs_created_at ON pipeline_runs(created_at);
CREATE INDEX IF NOT EXISTS ix_system_events_service_name_created_at ON system_events(service_name, created_at);
