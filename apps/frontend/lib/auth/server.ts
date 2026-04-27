import "server-only"

import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import type { AuthSessionResponse, AuthTokenResponse } from "@/lib/auth/types"

const AUTH_COOKIE_NAME = "diasense_access_token"
const DEFAULT_BACKEND_ORIGINS = [
  "http://127.0.0.1:8000",
  "http://localhost:8000",
  "http://backend-api:8000",
]

type BackendErrorPayload = {
  detail?: unknown
}

export class BackendApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message)
    this.name = "BackendApiError"
  }
}

function normalizeOrigin(origin: string): string {
  return origin.replace(/\/+$/, "")
}

function getBackendOrigins(): string[] {
  const configuredOrigins = [
    process.env.BACKEND_API_URL,
    process.env.NEXT_PUBLIC_BACKEND_API_URL,
  ].filter((origin): origin is string => Boolean(origin))

  return Array.from(
    new Set(
      [...configuredOrigins, ...DEFAULT_BACKEND_ORIGINS].map((origin) =>
        normalizeOrigin(origin)
      )
    )
  )
}

async function parseJson<T>(response: Response): Promise<T | null> {
  const rawBody = await response.text()

  if (!rawBody) {
    return null
  }

  try {
    return JSON.parse(rawBody) as T
  } catch {
    return null
  }
}

function getErrorMessage(
  payload: BackendErrorPayload | null,
  fallbackMessage: string
): string {
  if (typeof payload?.detail === "string" && payload.detail) {
    return payload.detail
  }

  if (Array.isArray(payload?.detail)) {
    const [firstDetail] = payload.detail
    if (
      firstDetail &&
      typeof firstDetail === "object" &&
      "msg" in firstDetail &&
      typeof firstDetail.msg === "string"
    ) {
      return firstDetail.msg
    }
  }

  return fallbackMessage
}

function createBackendConnectionError(error: unknown): BackendApiError {
  const normalizedMessage =
    error instanceof Error
      ? `${error.name} ${error.message}`.toLowerCase()
      : ""

  if (
    normalizedMessage.includes("timeout") ||
    normalizedMessage.includes("timed out") ||
    normalizedMessage.includes("aborted")
  ) {
    return new BackendApiError(
      "The DiaSense backend API took too long to respond. Make sure the backend service is running and try again.",
      504
    )
  }

  return new BackendApiError(
    "We couldn't reach the DiaSense backend API. Make sure the backend service is running on port 8000 and try again.",
    503
  )
}

async function requestBackend(
  path: string,
  init: RequestInit
): Promise<Response> {
  let lastError: unknown = null

  for (const origin of getBackendOrigins()) {
    const headers = new Headers(init.headers)
    headers.set("accept", "application/json")

    try {
      return await fetch(`${origin}/api/v1${path}`, {
        ...init,
        headers,
        cache: "no-store",
        signal: init.signal ?? AbortSignal.timeout(5000),
      })
    } catch (error) {
      lastError = error
    }
  }

  throw createBackendConnectionError(lastError)
}

async function expectBackendJson<T>(
  response: Response,
  fallbackMessage: string
): Promise<T> {
  const payload = await parseJson<T | BackendErrorPayload>(response)

  if (!response.ok) {
    throw new BackendApiError(
      getErrorMessage(payload as BackendErrorPayload | null, fallbackMessage),
      response.status
    )
  }

  if (payload === null) {
    throw new BackendApiError(fallbackMessage, response.status)
  }

  return payload as T
}

export async function requestBackendJson<T>(
  path: string,
  init: RequestInit,
  fallbackMessage: string
): Promise<T> {
  const response = await requestBackend(path, init)
  return expectBackendJson<T>(response, fallbackMessage)
}

export async function requestBackendJsonWithAuth<T>(
  path: string,
  init: RequestInit,
  fallbackMessage: string
): Promise<T> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    throw new BackendApiError(
      "Your session has expired. Please sign in again.",
      401
    )
  }

  const headers = new Headers(init.headers)
  headers.set("authorization", `Bearer ${accessToken}`)

  return requestBackendJson<T>(
    path,
    {
      ...init,
      headers,
    },
    fallbackMessage
  )
}

export async function loginWithBackend(
  username: string,
  password: string
): Promise<AuthTokenResponse> {
  return requestBackendJson<AuthTokenResponse>(
    "/login",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        username,
        password,
      }),
    },
    "We couldn't sign you in. Please try again."
  )
}

export async function signupWithBackend(
  username: string | undefined,
  email: string | undefined,
  password: string
): Promise<AuthTokenResponse> {
  return requestBackendJson<AuthTokenResponse>(
    "/signup",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        username,
        email,
        password,
      }),
    },
    "We couldn't create your account. Please try again."
  )
}

export async function fetchCurrentSession(
  accessToken: string
): Promise<AuthSessionResponse> {
  return requestBackendJson<AuthSessionResponse>(
    "/me",
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${accessToken}`,
      },
    },
    "Your session is no longer valid."
  )
}

export async function logoutFromBackend(accessToken: string): Promise<void> {
  const response = await requestBackend("/logout", {
    method: "POST",
    headers: {
      authorization: `Bearer ${accessToken}`,
    },
  })

  if (response.ok || response.status === 401) {
    return
  }

  const payload = await parseJson<BackendErrorPayload>(response)

  throw new BackendApiError(
    getErrorMessage(payload, "We couldn't sign you out cleanly."),
    response.status
  )
}

export async function persistSession(
  session: AuthTokenResponse
): Promise<void> {
  const cookieStore = await cookies()

  cookieStore.set(AUTH_COOKIE_NAME, session.access_token, {
    httpOnly: true,
    path: "/",
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: session.expires_in,
  })
}

export async function clearSession(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(AUTH_COOKIE_NAME)
}

export async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies()
  return cookieStore.get(AUTH_COOKIE_NAME)?.value ?? null
}

export async function getSession(): Promise<AuthSessionResponse | null> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return null
  }

  try {
    return await fetchCurrentSession(accessToken)
  } catch {
    return null
  }
}

export async function requireAuthenticatedSession(): Promise<AuthSessionResponse> {
  const session = await getSession()

  if (!session) {
    redirect("/login")
  }

  return session
}

export async function redirectIfAuthenticated(): Promise<void> {
  const session = await getSession()

  if (session) {
    redirect("/clinic")
  }
}
