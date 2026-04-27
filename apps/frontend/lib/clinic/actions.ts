"use server"

import { revalidatePath } from "next/cache"

import { getClinicFeatureErrorMessage } from "@/lib/clinic/errors"
import {
  createAssessment,
  createPatient,
  deletePatient,
  deletePrediction,
  deleteUser,
  resetOwnPassword,
  updateUserRole,
} from "@/lib/clinic/server"
import type {
  AssessmentFieldErrors,
  AssessmentFormState,
  CreatePatientFieldErrors,
  CreatePatientFormState,
  DeletePatientFormState,
  DeletePredictionFormState,
  DeleteUserFormState,
  PasswordResetFieldErrors,
  PasswordResetFormState,
  UserRoleFormState,
} from "@/lib/clinic/types"

function parseNumber(
  formData: FormData,
  key:
    | "pregnancies"
    | "glucose"
    | "blood_pressure"
    | "skin_thickness"
    | "insulin"
    | "bmi"
    | "diabetes_pedigree_function"
    | "age"
) {
  return Number(formData.get(key) ?? "")
}

function validateAssessment(formData: FormData): AssessmentFieldErrors {
  const fieldErrors: AssessmentFieldErrors = {}
  const patientReference = String(formData.get("patient_email") ?? "").trim()
  const numericRules = [
    ["pregnancies", parseNumber(formData, "pregnancies"), 0, 30],
    ["glucose", parseNumber(formData, "glucose"), 0, 300],
    ["blood_pressure", parseNumber(formData, "blood_pressure"), 0, 200],
    ["skin_thickness", parseNumber(formData, "skin_thickness"), 0, 100],
    ["insulin", parseNumber(formData, "insulin"), 0, 1000],
    ["bmi", parseNumber(formData, "bmi"), 0, 100],
    [
      "diabetes_pedigree_function",
      parseNumber(formData, "diabetes_pedigree_function"),
      0,
      10,
    ],
    ["age", parseNumber(formData, "age"), 1, 120],
  ] as const

  if (patientReference && patientReference.length < 3) {
    fieldErrors.patient_email = "Enter a valid patient username or email."
  }

  numericRules.forEach(([field, value, minimum, maximum]) => {
    if (Number.isFinite(value) === false) {
      fieldErrors[field] = "Enter a valid number."
      return
    }

    if (value < minimum || value > maximum) {
      fieldErrors[field] = `Use a value between ${minimum} and ${maximum}.`
    }
  })

  return fieldErrors
}

export async function assessmentAction(
  _previousState: AssessmentFormState,
  formData: FormData
): Promise<AssessmentFormState> {
  const fieldErrors = validateAssessment(formData)

  if (Object.keys(fieldErrors).length > 0) {
    return {
      message: "Please correct the highlighted assessment fields.",
      fieldErrors,
    }
  }

  try {
    const result = await createAssessment({
      patient_email:
        String(formData.get("patient_email") ?? "").trim() || undefined,
      pregnancies: parseNumber(formData, "pregnancies"),
      glucose: parseNumber(formData, "glucose"),
      blood_pressure: parseNumber(formData, "blood_pressure"),
      skin_thickness: parseNumber(formData, "skin_thickness"),
      insulin: parseNumber(formData, "insulin"),
      bmi: parseNumber(formData, "bmi"),
      diabetes_pedigree_function: parseNumber(
        formData,
        "diabetes_pedigree_function"
      ),
      age: parseNumber(formData, "age"),
    })

    revalidatePath("/clinic")
    revalidatePath("/clinic/predictions")
    revalidatePath("/clinic/patients")

    return {
      message: "Assessment submitted successfully.",
      result,
    }
  } catch (error) {
    return {
      message: getClinicFeatureErrorMessage(error, "assessment submission"),
    }
  }
}

export async function updateUserRoleAction(
  _previousState: UserRoleFormState,
  formData: FormData
): Promise<UserRoleFormState> {
  const userId = String(formData.get("user_id") ?? "")
  const role = String(formData.get("role") ?? "") as
    | "patient"
    | "clinician"
    | "admin"

  if (!userId || !role) {
    return {
      message: "Choose a role before saving.",
      success: false,
    }
  }

  try {
    await updateUserRole(userId, role)
    revalidatePath("/clinic/users")
    revalidatePath("/clinic/patients")
    return {
      message: "Role updated.",
      success: true,
    }
  } catch (error) {
    return {
      message: getClinicFeatureErrorMessage(error, "user management"),
      success: false,
    }
  }
}

export async function deleteUserAction(
  _previousState: DeleteUserFormState,
  formData: FormData
): Promise<DeleteUserFormState> {
  const userId = String(formData.get("user_id") ?? "")

  if (!userId) {
    return {
      message: "We couldn't identify which user to delete.",
      success: false,
    }
  }

  try {
    const result = await deleteUser(userId)
    revalidatePath("/clinic/users")
    revalidatePath("/clinic/patients")

    return {
      message: result.message,
      success: true,
    }
  } catch (error) {
    return {
      message: getClinicFeatureErrorMessage(error, "user deletion"),
      success: false,
    }
  }
}

function validatePatientAccount(formData: FormData): CreatePatientFieldErrors {
  const fieldErrors: CreatePatientFieldErrors = {}
  const username = String(formData.get("username") ?? "").trim()
  const email = String(formData.get("email") ?? "").trim()
  const password = String(formData.get("password") ?? "")

  if (!username && !email) {
    fieldErrors.email = "Enter a username or email."
  }

  if (username && username.length < 3) {
    fieldErrors.username = "Use at least 3 characters."
  }

  if (email && !email.includes("@")) {
    fieldErrors.email = "Enter a valid email address."
  }

  if (!password) {
    fieldErrors.password = "Set a temporary password."
  } else if (password.length < 8) {
    fieldErrors.password = "Use at least 8 characters."
  }

  return fieldErrors
}

export async function createPatientAction(
  _previousState: CreatePatientFormState,
  formData: FormData
): Promise<CreatePatientFormState> {
  const fieldErrors = validatePatientAccount(formData)

  if (Object.keys(fieldErrors).length > 0) {
    return {
      message: "Please correct the highlighted patient fields.",
      success: false,
      fieldErrors,
    }
  }

  try {
    const result = await createPatient({
      username: String(formData.get("username") ?? "").trim() || undefined,
      email: String(formData.get("email") ?? "").trim() || undefined,
      password: String(formData.get("password") ?? ""),
    })

    revalidatePath("/clinic/dashboard")
    revalidatePath("/clinic/patients")
    revalidatePath("/clinic/assessment")
    revalidatePath("/clinic/users")

    return {
      message: result.message,
      success: true,
    }
  } catch (error) {
    return {
      message: getClinicFeatureErrorMessage(error, "patient creation"),
      success: false,
    }
  }
}

export async function deletePatientAction(
  _previousState: DeletePatientFormState,
  formData: FormData
): Promise<DeletePatientFormState> {
  const patientId = String(formData.get("patient_id") ?? "")

  if (!patientId) {
    return {
      message: "We couldn't identify which patient to delete.",
      success: false,
    }
  }

  try {
    const result = await deletePatient(patientId)
    revalidatePath("/clinic/dashboard")
    revalidatePath("/clinic/patients")
    revalidatePath("/clinic/assessment")
    revalidatePath("/clinic/users")

    return {
      message: result.message,
      success: true,
    }
  } catch (error) {
    return {
      message: getClinicFeatureErrorMessage(error, "patient deletion"),
      success: false,
    }
  }
}

export async function deletePredictionAction(
  _previousState: DeletePredictionFormState,
  formData: FormData
): Promise<DeletePredictionFormState> {
  const requestId = String(formData.get("request_id") ?? "")

  if (!requestId) {
    return {
      message: "We couldn't identify which prediction to delete.",
      success: false,
    }
  }

  try {
    const result = await deletePrediction(requestId)
    revalidatePath("/clinic")
    revalidatePath("/clinic/dashboard")
    revalidatePath("/clinic/patients")
    revalidatePath("/clinic/predictions")
    revalidatePath(`/clinic/predictions/${requestId}`)

    return {
      message: result.message,
      success: true,
    }
  } catch (error) {
    return {
      message: getClinicFeatureErrorMessage(error, "prediction deletion"),
      success: false,
    }
  }
}

function validatePasswordReset(formData: FormData): PasswordResetFieldErrors {
  const fieldErrors: PasswordResetFieldErrors = {}
  const currentPassword = String(formData.get("current_password") ?? "")
  const newPassword = String(formData.get("new_password") ?? "")
  const confirmPassword = String(formData.get("confirm_password") ?? "")

  if (!currentPassword) {
    fieldErrors.current_password = "Enter your current password."
  }

  if (!newPassword) {
    fieldErrors.new_password = "Enter a new password."
  } else if (newPassword.length < 8) {
    fieldErrors.new_password = "Use at least 8 characters."
  }

  if (!confirmPassword) {
    fieldErrors.confirm_password = "Confirm your new password."
  } else if (confirmPassword !== newPassword) {
    fieldErrors.confirm_password = "Passwords do not match."
  }

  return fieldErrors
}

export async function resetPasswordAction(
  _previousState: PasswordResetFormState,
  formData: FormData
): Promise<PasswordResetFormState> {
  const fieldErrors = validatePasswordReset(formData)

  if (Object.keys(fieldErrors).length > 0) {
    return {
      message: "Please correct the highlighted password fields.",
      success: false,
      fieldErrors,
    }
  }

  try {
    const result = await resetOwnPassword(
      String(formData.get("current_password") ?? ""),
      String(formData.get("new_password") ?? "")
    )

    return {
      message: result.message,
      success: true,
    }
  } catch (error) {
    return {
      message:
        error instanceof Error
          ? error.message
          : "We couldn't update your password right now.",
      success: false,
    }
  }
}
