import type { AuthFieldErrors } from "@/lib/auth/types"

const EMAIL_PATTERN = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i
const USERNAME_PATTERN = /^[a-z0-9](?:[a-z0-9._-]{1,48}[a-z0-9])?$/i
const MIN_PASSWORD_LENGTH = 8

type LoginInput = {
  username: string
  password: string
}

type SignupInput = {
  username: string
  email: string
  password: string
}

export function validateLoginInput({
  username,
  password,
}: LoginInput): AuthFieldErrors {
  const fieldErrors: AuthFieldErrors = {}
  const normalizedUsername = username.trim()

  if (!normalizedUsername) {
    fieldErrors.username = "Enter your username or email."
  } else if (
    normalizedUsername.includes("@") &&
    EMAIL_PATTERN.test(normalizedUsername) === false
  ) {
    fieldErrors.username = "Enter a valid email address."
  }

  if (!password) {
    fieldErrors.password = "Enter your password."
  }

  return fieldErrors
}

export function validateSignupInput({
  username,
  email,
  password,
}: SignupInput): AuthFieldErrors {
  const fieldErrors: AuthFieldErrors = {}
  const normalizedUsername = username.trim()
  const normalizedEmail = email.trim().toLowerCase()

  if (!normalizedUsername && !normalizedEmail) {
    fieldErrors.username = "Enter a username or email."
    fieldErrors.email = "Enter an email or keep using username only."
  } else if (
    normalizedUsername &&
    USERNAME_PATTERN.test(normalizedUsername) === false
  ) {
    fieldErrors.username =
      "Use 3-50 letters, numbers, dots, hyphens, or underscores."
  }

  if (normalizedEmail && EMAIL_PATTERN.test(normalizedEmail) === false) {
    fieldErrors.email = "Enter a valid email address."
  }

  if (!password) {
    fieldErrors.password = "Create a password."
  } else if (password.length < MIN_PASSWORD_LENGTH) {
    fieldErrors.password = `Use at least ${MIN_PASSWORD_LENGTH} characters.`
  }

  return fieldErrors
}

export function hasFieldErrors(fieldErrors: AuthFieldErrors): boolean {
  return Object.values(fieldErrors).some(Boolean)
}
