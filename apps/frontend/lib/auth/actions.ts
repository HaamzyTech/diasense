"use server"

import { redirect } from "next/navigation"

import {
  clearSession,
  getAccessToken,
  loginWithBackend,
  logoutFromBackend,
  persistSession,
  signupWithBackend,
} from "@/lib/auth/server"
import type { AuthFormState } from "@/lib/auth/types"
import {
  hasFieldErrors,
  validateLoginInput,
  validateSignupInput,
} from "@/lib/auth/validation"

function buildValidationState(
  fieldErrors: AuthFormState["fieldErrors"]
): AuthFormState {
  return {
    message: "Please correct the highlighted fields.",
    fieldErrors,
  }
}

function buildFailureState(message: string): AuthFormState {
  return {
    message,
  }
}

export async function loginAction(
  _previousState: AuthFormState,
  formData: FormData
): Promise<AuthFormState> {
  const username = String(formData.get("username") ?? "")
  const password = String(formData.get("password") ?? "")
  const fieldErrors = validateLoginInput({
    username,
    password,
  })

  if (hasFieldErrors(fieldErrors)) {
    return buildValidationState(fieldErrors)
  }

  try {
    const session = await loginWithBackend(username.trim(), password)
    await persistSession(session)
  } catch (error) {
    return buildFailureState(
      error instanceof Error
        ? error.message
        : "We couldn't sign you in. Please try again."
    )
  }

  redirect("/clinic")
}

export async function signupAction(
  _previousState: AuthFormState,
  formData: FormData
): Promise<AuthFormState> {
  const username = String(formData.get("username") ?? "")
  const email = String(formData.get("email") ?? "")
  const password = String(formData.get("password") ?? "")
  const fieldErrors = validateSignupInput({
    username,
    email,
    password,
  })

  if (hasFieldErrors(fieldErrors)) {
    return buildValidationState(fieldErrors)
  }

  try {
    const session = await signupWithBackend(
      username.trim() || undefined,
      email.trim() || undefined,
      password
    )
    await persistSession(session)
  } catch (error) {
    return buildFailureState(
      error instanceof Error
        ? error.message
        : "We couldn't create your account. Please try again."
    )
  }

  redirect("/clinic")
}

export async function logoutAction(): Promise<void> {
  const accessToken = await getAccessToken()

  try {
    if (accessToken) {
      await logoutFromBackend(accessToken)
    }
  } finally {
    await clearSession()
  }

  redirect("/login")
}
