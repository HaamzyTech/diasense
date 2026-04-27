export type UserRole = "patient" | "clinician" | "admin"

export type AuthUser = {
  username: string
  email?: string | null
  role: UserRole | string
  auth_source: string
}

export type AuthTokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export type AuthSessionResponse = {
  user: AuthUser
  session_expires_at: string
}

export type AuthFieldErrors = {
  username?: string
  email?: string
  password?: string
}

export type AuthFormState = {
  message?: string
  fieldErrors?: AuthFieldErrors
}

export const initialAuthFormState: AuthFormState = {}
