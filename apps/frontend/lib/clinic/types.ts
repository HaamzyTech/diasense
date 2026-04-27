export type PredictionSummary = {
  request_id: string
  submitted_by: string
  patient_email: string
  actor_role: string
  risk_probability: number
  risk_band: string
  predicted_label: boolean
  interpretation: string
  created_at: string
}

export type PredictionListResponse = {
  items: PredictionSummary[]
  count: number
}

export type PredictionRequestRecord = {
  id: string
  session_id: string
  submitted_by: string
  patient_email: string
  actor_role: string
  pregnancies: number
  glucose: number
  blood_pressure: number
  skin_thickness: number
  insulin: number
  bmi: number
  diabetes_pedigree_function: number
  age: number
  source: string
  created_at: string
}

export type PredictionResultRecord = {
  id: string | null
  model_version_id: string | null
  predicted_label: boolean | null
  risk_probability: number | null
  risk_band: string | null
  interpretation: string | null
  top_factors: Array<{
    feature: string
    importance: number
  }>
  latency_ms: number | null
  created_at: string | null
}

export type PredictionDetailResponse = {
  request: PredictionRequestRecord
  result: PredictionResultRecord | null
}

export type DeletePredictionResponse = {
  message: string
  request_id: string
  patient_email: string
  submitted_by: string
  actor_role: string
  deleted_at: string
}

export type AssessmentResult = {
  request_id: string
  model_version_id: string
  submitted_by: string
  patient_email: string
  predicted_label: boolean
  risk_probability: number
  risk_band: string
  interpretation: string
  top_factors: Array<{
    feature: string
    importance: number
  }>
  latency_ms: number
  created_at: string
}

export type ManagedUser = {
  id: string
  username: string
  email: string | null
  role: "patient" | "clinician" | "admin"
  created_at: string
}

export type ManagedUserListResponse = {
  items: ManagedUser[]
  count: number
}

export type DeleteUserResponse = {
  message: string
  user: ManagedUser
}

export type CreatePatientResponse = {
  message: string
  patient: ManagedUser
}

export type DeletePatientResponse = {
  message: string
  patient: ManagedUser
}

export type PatientSummary = {
  id: string
  username: string
  email: string | null
  role: "patient" | "clinician" | "admin"
  created_at: string
  assessment_count: number
  last_assessed_at: string | null
  latest_risk_band: string | null
  latest_risk_probability: number | null
}

export type PatientListResponse = {
  items: PatientSummary[]
  count: number
}

export type OpsSummary = {
  service: string
  version: string
  services: Record<string, string>
  active_model: {
    model_name: string
    model_version: string
    stage: string
  } | null
  latest_pipeline_status: string
  latest_drift_status: string
  timestamp: string
}

export type AssessmentFieldErrors = Partial<
  Record<
    | "patient_email"
    | "pregnancies"
    | "glucose"
    | "blood_pressure"
    | "skin_thickness"
    | "insulin"
    | "bmi"
    | "diabetes_pedigree_function"
    | "age",
    string
  >
>

export type AssessmentFormState = {
  message?: string
  fieldErrors?: AssessmentFieldErrors
  result?: AssessmentResult
}

export const initialAssessmentFormState: AssessmentFormState = {}

export type UserRoleFormState = {
  message?: string
  success?: boolean
}

export const initialUserRoleFormState: UserRoleFormState = {}

export type DeleteUserFormState = {
  message?: string
  success?: boolean
}

export const initialDeleteUserFormState: DeleteUserFormState = {}

export type CreatePatientFieldErrors = {
  username?: string
  email?: string
  password?: string
}

export type CreatePatientFormState = {
  message?: string
  success?: boolean
  fieldErrors?: CreatePatientFieldErrors
}

export const initialCreatePatientFormState: CreatePatientFormState = {}

export type DeletePatientFormState = {
  message?: string
  success?: boolean
}

export const initialDeletePatientFormState: DeletePatientFormState = {}

export type DeletePredictionFormState = {
  message?: string
  success?: boolean
}

export const initialDeletePredictionFormState: DeletePredictionFormState = {}

export type PasswordResetFieldErrors = {
  current_password?: string
  new_password?: string
  confirm_password?: string
}

export type PasswordResetFormState = {
  message?: string
  success?: boolean
  fieldErrors?: PasswordResetFieldErrors
}

export const initialPasswordResetFormState: PasswordResetFormState = {}
