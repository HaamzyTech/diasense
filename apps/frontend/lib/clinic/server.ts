import "server-only"

import { requestBackendJsonWithAuth } from "@/lib/auth/server"
import type {
  AssessmentResult,
  CreatePatientResponse,
  DeletePatientResponse,
  DeletePredictionResponse,
  DeleteUserResponse,
  ManagedUser,
  ManagedUserListResponse,
  OpsSummary,
  PatientListResponse,
  PatientSummary,
  PredictionDetailResponse,
  PredictionListResponse,
} from "@/lib/clinic/types"

type AssessmentPayload = {
  patient_email?: string
  pregnancies: number
  glucose: number
  blood_pressure: number
  skin_thickness: number
  insulin: number
  bmi: number
  diabetes_pedigree_function: number
  age: number
}

function buildQuery(
  params: Record<string, string | number | null | undefined>
) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      return
    }

    searchParams.set(key, String(value))
  })

  const query = searchParams.toString()
  return query ? `?${query}` : ""
}

export async function createAssessment(
  payload: AssessmentPayload
): Promise<AssessmentResult> {
  return requestBackendJsonWithAuth<AssessmentResult>(
    "/predict",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "We couldn't submit the assessment right now."
  )
}

export async function fetchPredictions(options?: {
  patientEmail?: string
  limit?: number
}): Promise<PredictionListResponse> {
  const query = buildQuery({
    patient_email: options?.patientEmail,
    limit: options?.limit ?? 50,
  })

  return requestBackendJsonWithAuth<PredictionListResponse>(
    `/predictions${query}`,
    {
      method: "GET",
    },
    "We couldn't load predictions right now."
  )
}

export async function fetchLegacyMyPredictions(
  limit = 50
): Promise<PredictionListResponse> {
  return requestBackendJsonWithAuth<PredictionListResponse>(
    "/my-predictions",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({ limit }),
    },
    "We couldn't load predictions right now."
  )
}

export async function fetchPredictionDetail(
  requestId: string
): Promise<PredictionDetailResponse> {
  return requestBackendJsonWithAuth<PredictionDetailResponse>(
    `/predictions/${requestId}`,
    {
      method: "GET",
    },
    "We couldn't load that prediction."
  )
}

export async function fetchPatients(limit = 200): Promise<PatientSummary[]> {
  const response = await requestBackendJsonWithAuth<PatientListResponse>(
    `/patients${buildQuery({ limit })}`,
    {
      method: "GET",
    },
    "We couldn't load patients right now."
  )

  return response.items
}

export async function createPatient(payload: {
  username?: string
  email?: string
  password: string
}): Promise<CreatePatientResponse> {
  return requestBackendJsonWithAuth<CreatePatientResponse>(
    "/patients",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "We couldn't create that patient account."
  )
}

export async function deletePatient(
  patientId: string
): Promise<DeletePatientResponse> {
  return requestBackendJsonWithAuth<DeletePatientResponse>(
    `/patients/${patientId}`,
    {
      method: "DELETE",
    },
    "We couldn't delete that patient account."
  )
}

export async function fetchUsers(limit = 200): Promise<ManagedUser[]> {
  const response = await requestBackendJsonWithAuth<ManagedUserListResponse>(
    `/users${buildQuery({ limit })}`,
    {
      method: "GET",
    },
    "We couldn't load registered users right now."
  )

  return response.items
}

export async function updateUserRole(
  userId: string,
  role: ManagedUser["role"]
): Promise<ManagedUser> {
  return requestBackendJsonWithAuth<ManagedUser>(
    `/users/${userId}/role`,
    {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({ role }),
    },
    "We couldn't update that user's role."
  )
}

export async function deleteUser(userId: string): Promise<DeleteUserResponse> {
  return requestBackendJsonWithAuth<DeleteUserResponse>(
    `/users/${userId}`,
    {
      method: "DELETE",
    },
    "We couldn't delete that user."
  )
}

export async function fetchOpsSummary(): Promise<OpsSummary> {
  return requestBackendJsonWithAuth<OpsSummary>(
    "/ops/summary",
    {
      method: "GET",
    },
    "We couldn't load monitoring details right now."
  )
}

export async function resetOwnPassword(
  currentPassword: string,
  newPassword: string
): Promise<{ message: string }> {
  return requestBackendJsonWithAuth<{ message: string }>(
    "/reset-password",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    },
    "We couldn't update your password right now."
  )
}

export async function deletePrediction(
  requestId: string
): Promise<DeletePredictionResponse> {
  return requestBackendJsonWithAuth<DeletePredictionResponse>(
    `/predictions/${requestId}`,
    {
      method: "DELETE",
    },
    "We couldn't delete that prediction result."
  )
}
