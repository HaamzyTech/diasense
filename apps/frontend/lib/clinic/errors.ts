import { BackendApiError } from "@/lib/auth/server"

export function isMissingBackendFeature(error: unknown): boolean {
  return error instanceof BackendApiError && error.status === 404
}

export function getClinicFeatureErrorMessage(
  error: unknown,
  featureLabel: string
): string {
  if (error instanceof BackendApiError) {
    if (error.status === 404) {
      return `The backend route for ${featureLabel} is not available on the current API server. Restart or redeploy backend-api to enable this page.`
    }

    if (error.status === 403) {
      return `Your account does not have permission to access ${featureLabel}.`
    }

    if (error.status === 401) {
      return "Your session has expired. Please sign in again."
    }

    if (error.message) {
      return error.message
    }
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return `We couldn't load ${featureLabel} right now.`
}
