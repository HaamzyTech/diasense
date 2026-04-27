import { BackendFeatureNotice } from "@/components/clinic/backend-feature-notice"
import { AssessmentForm } from "@/components/clinic/assessment-form"
import { requireAuthenticatedSession } from "@/lib/auth/server"
import { getClinicFeatureErrorMessage } from "@/lib/clinic/errors"
import { fetchPatients } from "@/lib/clinic/server"
import {
  getAccountReference,
  getAccountSecondaryLabel,
} from "@/lib/clinic/presentation"

type AssessmentPageProps = {
  searchParams?: Promise<{
    patient?: string
  }>
}

export default async function AssessmentPage({
  searchParams,
}: AssessmentPageProps) {
  const session = await requireAuthenticatedSession()
  const resolvedSearchParams = searchParams ? await searchParams : undefined
  const canAssessPatients =
    session.user.role === "clinician" || session.user.role === "admin"
  const defaultPatientEmail = canAssessPatients
    ? resolvedSearchParams?.patient
    : undefined
  let patientOptions: Array<{
    value: string
    label: string
    description: string
  }> = []
  let directoryMessage: string | null = null

  if (canAssessPatients) {
    try {
      const patients = await fetchPatients()
      patientOptions = patients.map((patient) => ({
        value: getAccountReference(patient),
        label: getAccountReference(patient),
        description: getAccountSecondaryLabel(patient),
      }))
    } catch (error) {
      directoryMessage = getClinicFeatureErrorMessage(error, "account search")
    }
  }

  return (
    <div className="space-y-8 py-4 lg:py-8">
      <div className="mx-auto w-full max-w-3xl space-y-2 text-center">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Assessment
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          Submit assessment metrics for prediction
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          Authenticated assessment requests are routed through the backend API,
          checked against your role permissions, and stored in protected
          prediction history.
        </p>
      </div>

      <div className="mx-auto w-full max-w-5xl rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest px-6 py-8 shadow-[0_20px_50px_rgba(25,28,29,0.05)] sm:px-8 lg:px-10 lg:py-10 dark:shadow-none">
        {directoryMessage ? (
          <div className="mb-6">
            <BackendFeatureNotice
              title="Account search is temporarily unavailable"
              message={`${directoryMessage} You can still enter a username or email manually.`}
              tone="info"
            />
          </div>
        ) : null}

        <AssessmentForm
          canAssessPatients={canAssessPatients}
          defaultPatientEmail={defaultPatientEmail}
          patientOptions={patientOptions}
        />
      </div>
    </div>
  )
}
