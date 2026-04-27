import Link from "next/link"

import { BackendFeatureNotice } from "@/components/clinic/backend-feature-notice"
import { CreatePatientSheet } from "@/components/clinic/create-patient-sheet"
import { DataTableCard } from "@/components/clinic/data-table-card"
import { DeletePatientForm } from "@/components/clinic/delete-patient-form"
import { RiskBadge } from "@/components/clinic/risk-badge"
import { Button } from "@/components/ui/button"
import { requireRoleSession } from "@/lib/auth/guards"
import { getClinicFeatureErrorMessage } from "@/lib/clinic/errors"
import {
  formatCalendarDate,
  formatCalendarDateTime,
  getAccountReference,
  getAccountSecondaryLabel,
} from "@/lib/clinic/presentation"
import { fetchPatients } from "@/lib/clinic/server"
import type { PatientSummary } from "@/lib/clinic/types"

function toPatientId(value: string): string {
  return `#PX-${value.replace(/-/g, "").slice(0, 4).toUpperCase()}`
}

function getRiskLabel(
  latestRiskBand: string | null,
  latestRiskProbability: number | null
) {
  if (!latestRiskBand || latestRiskProbability === null) {
    return "No result yet"
  }

  return `${latestRiskBand} (${Math.round(latestRiskProbability * 100)})`
}

export default async function PatientsPage() {
  await requireRoleSession(["clinician", "admin"])
  let patients: PatientSummary[] = []
  let loadMessage: string | null = null

  try {
    patients = await fetchPatients()
  } catch (error) {
    loadMessage = getClinicFeatureErrorMessage(error, "patient management")
  }

  const assessedPatients = patients.filter(
    (patient) => patient.assessment_count > 0
  ).length
  const highRiskPatients = patients.filter(
    (patient) => patient.latest_risk_band === "high"
  ).length

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Patients
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          Patient management
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          Review assessable accounts, identify high-risk cases quickly, and
          create dedicated patient logins when the clinic needs them.
        </p>
      </div>

      {loadMessage ? (
        <BackendFeatureNotice
          title="Patient management is temporarily unavailable"
          message={loadMessage}
          actionHref="/clinic/assessment"
          actionLabel="Open assessment instead"
        />
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            Assessable accounts
          </p>
          <p className="mt-4 font-headline text-5xl font-semibold text-on-surface">
            {patients.length}
          </p>
        </div>
        <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            With assessments
          </p>
          <p className="mt-4 font-headline text-5xl font-semibold text-on-surface">
            {assessedPatients}
          </p>
        </div>
        <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            High-risk roster
          </p>
          <p className="mt-4 font-headline text-5xl font-semibold text-on-surface">
            {highRiskPatients}
          </p>
        </div>
      </div>

      <DataTableCard
        title="Patient Roster"
        subtitle="Any registered account can be assessed as a patient. Dedicated patient logins remain labeled with the patient role."
        toolbar={
          <>
            <CreatePatientSheet />
            <Button asChild className="hero-gradient h-11 text-on-primary">
              <Link href="/clinic/assessment">New assessment</Link>
            </Button>
          </>
        }
        footer={
          loadMessage
            ? "Patient data could not be loaded from the backend right now."
            : `Showing ${patients.length} assessable account${patients.length === 1 ? "" : "s"}`
        }
      >
        {patients.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1220px]">
              <thead>
                <tr className="border-b border-outline-variant/10">
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Patient ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Account
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Registered
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Role
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Last assessment
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Assessments
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Risk score
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {patients.map((patient) => {
                  const patientReference = getAccountReference(patient)

                  return (
                    <tr
                      key={patient.id}
                      className="transition-colors hover:bg-surface-container-low/60"
                    >
                      <td className="px-6 py-5 text-lg text-on-surface-variant">
                        {toPatientId(patient.id)}
                      </td>
                      <td className="px-6 py-5">
                        <div className="space-y-1">
                          <p className="text-lg font-semibold text-on-surface">
                            {patientReference}
                          </p>
                          <p className="text-sm text-on-surface-variant">
                            {getAccountSecondaryLabel(patient)}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-5 text-sm text-on-surface-variant">
                        {formatCalendarDateTime(patient.created_at)}
                      </td>
                      <td className="px-6 py-5 text-base font-medium text-on-surface capitalize">
                        {patient.role}
                      </td>
                      <td className="px-6 py-5 text-base text-on-surface">
                        {patient.last_assessed_at
                          ? formatCalendarDate(patient.last_assessed_at)
                          : "Not yet assessed"}
                      </td>
                      <td className="px-6 py-5 text-base font-medium text-on-surface">
                        {patient.assessment_count}
                      </td>
                      <td className="px-6 py-5">
                        <RiskBadge
                          riskBand={patient.latest_risk_band}
                          label={getRiskLabel(
                            patient.latest_risk_band,
                            patient.latest_risk_probability
                          )}
                        />
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex flex-wrap items-start gap-3">
                          <Link
                            href={`/clinic/assessment?patient=${encodeURIComponent(patientReference)}`}
                            className="text-sm font-semibold text-primary transition-colors hover:text-primary/80"
                          >
                            Assess
                          </Link>
                          <Link
                            href={`/clinic/predictions?patient=${encodeURIComponent(patientReference)}`}
                            className="text-sm font-semibold text-primary transition-colors hover:text-primary/80"
                          >
                            View history
                          </Link>
                          {patient.role === "patient" ? (
                            <DeletePatientForm
                              patientId={patient.id}
                              patientLabel={patientReference}
                            />
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center text-sm text-on-surface-variant">
            {loadMessage
              ? "Patient data could not be loaded from the backend right now."
              : "No assessable accounts are available yet."}
          </div>
        )}
      </DataTableCard>
    </div>
  )
}
