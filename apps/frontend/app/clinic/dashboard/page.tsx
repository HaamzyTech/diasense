import Link from "next/link"
import {
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  TrendingUp,
  Users,
} from "lucide-react"

import { DataTableCard } from "@/components/clinic/data-table-card"
import { RiskBadge } from "@/components/clinic/risk-badge"
import { Button } from "@/components/ui/button"
import { requireRoleSession } from "@/lib/auth/guards"
import {
  formatCalendarDate,
  getAccountReference,
  getAccountSecondaryLabel,
  getInitialsFromReference,
} from "@/lib/clinic/presentation"
import {
  fetchOpsSummary,
  fetchPatients,
  fetchPredictionDetail,
  fetchPredictions,
  fetchUsers,
} from "@/lib/clinic/server"

function toPatientId(value: string): string {
  return `#PX-${value.replace(/-/g, "").slice(0, 4).toUpperCase()}`
}

function getRiskScoreLabel(riskBand: string, probability: number): string {
  const score = Math.round(probability * 100)

  switch (riskBand) {
    case "high":
      return `Critical (${score})`
    case "moderate":
      return `Elevated (${score})`
    default:
      return `Normal (${score})`
  }
}

export default async function RoleDashboardPage() {
  const session = await requireRoleSession(["clinician", "admin"])
  const isAdmin = session.user.role === "admin"

  const [predictionsResult, patientsResult, usersResult, opsResult] =
    await Promise.allSettled([
      fetchPredictions({ limit: 6 }),
      fetchPatients(250),
      isAdmin ? fetchUsers(250) : Promise.resolve([]),
      isAdmin ? fetchOpsSummary() : Promise.resolve(null),
    ])

  const predictions =
    predictionsResult.status === "fulfilled"
      ? predictionsResult.value
      : { items: [], count: 0 }
  const patients =
    patientsResult.status === "fulfilled" ? patientsResult.value : []
  const users = usersResult.status === "fulfilled" ? usersResult.value : []
  const opsSummary = opsResult.status === "fulfilled" ? opsResult.value : null

  const patientLookup = new Map(
    patients.map((patient) => [
      getAccountReference(patient).toLowerCase(),
      patient,
    ])
  )
  const detailResults =
    predictions.items.length > 0
      ? await Promise.allSettled(
          predictions.items.map((item) =>
            fetchPredictionDetail(item.request_id)
          )
        )
      : []

  const recentAssessments = predictions.items.map((item, index) => {
    const detailResult = detailResults[index]
    const detail =
      detailResult?.status === "fulfilled" ? detailResult.value : null
    const matchedPatient = patientLookup.get(item.patient_email.toLowerCase())
    const accountLabel = matchedPatient
      ? getAccountReference(matchedPatient)
      : item.patient_email
    const secondaryLabel = matchedPatient
      ? getAccountSecondaryLabel(matchedPatient)
      : `Submitted by ${item.submitted_by}`

    return {
      requestId: item.request_id,
      patientId: toPatientId(matchedPatient?.id ?? item.request_id),
      accountLabel,
      secondaryLabel,
      lastAssessment: formatCalendarDate(item.created_at),
      bmi: detail?.request.bmi ?? null,
      glucose: detail?.request.glucose ?? null,
      riskBand: item.risk_band,
      riskProbability: item.risk_probability,
    }
  })

  const assessedPatients = patients.filter(
    (patient) => patient.assessment_count > 0
  ).length
  const highRiskPatients = patients.filter(
    (patient) => patient.latest_risk_band === "high"
  )
  const coverage = patients.length
    ? Math.round((assessedPatients / patients.length) * 100)
    : 0
  const averageGlucose =
    recentAssessments.length > 0
      ? recentAssessments
          .filter((assessment) => assessment.glucose !== null)
          .reduce((total, assessment) => total + (assessment.glucose ?? 0), 0) /
        Math.max(
          recentAssessments.filter((assessment) => assessment.glucose !== null)
            .length,
          1
        )
      : null

  const todayLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })
  const operationsFootnote = isAdmin
    ? `${users.length} total users • ${opsSummary?.latest_pipeline_status ?? "Pipeline unavailable"}`
    : `${patients.length} patient accounts in roster`

  return (
    <div className="space-y-8 py-1">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 border border-outline-variant/15 bg-surface-container-low px-3 py-1 text-xs font-semibold tracking-[0.18em] text-primary uppercase">
          {isAdmin ? "Admin view" : "Clinician view"}
        </div>
        <h1 className="font-headline text-4xl font-semibold tracking-tight text-on-surface lg:text-5xl">
          Clinical Dashboard
        </h1>
        <p className="text-base text-on-surface-variant lg:text-lg">
          {isAdmin ? "Operational overview" : "Provider overview"} for{" "}
          {todayLabel}
        </p>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,0.9fr)]">
        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] lg:p-8 dark:shadow-none">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                Total patients assessed
              </p>
              <div className="flex items-end gap-3">
                <p className="font-headline text-5xl font-semibold text-on-surface">
                  {assessedPatients}
                </p>
                <p className="pb-1 text-lg text-on-surface-variant">
                  Active cases
                </p>
              </div>
            </div>
            <div className="border border-primary/10 bg-primary/5 px-3 py-1 text-sm font-semibold text-primary">
              {coverage}% coverage
            </div>
          </div>

          <div className="mt-8 border-t border-outline-variant/10 pt-6">
            <p className="text-base text-on-surface-variant">
              Last 30 days performance
            </p>
            <p className="mt-3 text-sm text-on-surface-variant">
              {operationsFootnote}
            </p>
          </div>
        </section>

        <section className="rounded-[28px] border border-error/10 bg-[rgba(255,248,246,0.95)] p-6 shadow-[0_20px_50px_rgba(25,28,29,0.04)] lg:p-8 dark:shadow-none">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold tracking-[0.18em] text-[rgb(191,42,35)] uppercase">
                High-risk alerts
              </p>
              <div className="flex items-end gap-3">
                <p className="font-headline text-5xl font-semibold text-[rgb(191,42,35)]">
                  {highRiskPatients.length}
                </p>
                <p className="pb-1 text-lg text-[rgb(164,47,33)]">
                  Critical intervention needed
                </p>
              </div>
            </div>
            <AlertTriangle className="mt-1 size-7 text-[rgb(191,42,35)]" />
          </div>

          <Link
            href={isAdmin ? "/clinic/monitor" : "/clinic/patients"}
            className="mt-16 inline-flex items-center gap-2 text-base font-semibold text-[rgb(191,42,35)] transition-colors hover:text-[rgb(143,32,27)]"
          >
            {isAdmin ? "Open monitor" : "View urgent cases"}
            <ArrowRight className="size-4" />
          </Link>
        </section>

        <section className="relative overflow-hidden rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] lg:p-8 dark:shadow-none">
          <div className="relative z-10 space-y-2">
            <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
              Recent trends
            </p>
            <h2 className="font-headline text-3xl font-semibold text-on-surface">
              Glycemic Stability
            </h2>
            <p className="text-base text-on-surface-variant">
              {averageGlucose !== null
                ? `${averageGlucose.toFixed(1)} mg/dL recent average`
                : "System-wide patient average pending"}
            </p>
          </div>

          <div className="absolute inset-x-0 bottom-0 h-32 overflow-hidden">
            <div className="absolute -bottom-12 left-0 h-32 w-44 rounded-full bg-primary/8 blur-sm" />
            <div className="absolute -bottom-14 left-28 h-28 w-44 rounded-full bg-secondary/12 blur-sm" />
            <div className="absolute -right-10 -bottom-10 h-40 w-48 rounded-full bg-primary/12 blur-sm" />
          </div>

          <div className="relative z-10 mt-16 inline-flex items-center gap-2 text-sm font-semibold text-primary">
            Trendline updated from protected assessments
            <TrendingUp className="size-4" />
          </div>
        </section>
      </div>

      <DataTableCard
        title="Recent Assessments"
        subtitle="Protected clinical submissions captured from the latest assessment activity."
        toolbar={
          <>
            <Button
              asChild
              variant="outline"
              className="h-11 border-outline-variant/20 bg-surface-container-lowest"
            >
              <Link href="/clinic/predictions">View all predictions</Link>
            </Button>
            <Button asChild className="hero-gradient h-11 text-on-primary">
              <Link href="/clinic/assessment">New assessment</Link>
            </Button>
          </>
        }
        footer={`Showing ${recentAssessments.length} of ${predictions.count} recent assessments`}
      >
        {recentAssessments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[960px]">
              <thead>
                <tr className="border-b border-outline-variant/10">
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Patient ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Name
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Last assessment
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    BMI
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Glucose
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
                {recentAssessments.map((assessment) => (
                  <tr
                    key={assessment.requestId}
                    className="transition-colors hover:bg-surface-container-low/60"
                  >
                    <td className="px-6 py-5 text-lg text-on-surface-variant">
                      {assessment.patientId}
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-4">
                        <div className="flex size-11 items-center justify-center rounded-full border border-outline-variant/15 bg-surface-container-low text-sm font-semibold text-primary">
                          {getInitialsFromReference(assessment.accountLabel)}
                        </div>
                        <div className="space-y-1">
                          <p className="text-xl font-semibold text-on-surface">
                            {assessment.accountLabel}
                          </p>
                          <p className="text-sm text-on-surface-variant">
                            {assessment.secondaryLabel}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-5 text-xl text-on-surface">
                      {assessment.lastAssessment}
                    </td>
                    <td className="px-6 py-5 text-lg text-on-surface">
                      {assessment.bmi !== null
                        ? assessment.bmi.toFixed(1)
                        : "Pending"}
                    </td>
                    <td className="px-6 py-5 text-lg text-on-surface">
                      {assessment.glucose !== null
                        ? `${assessment.glucose.toFixed(0)} mg/dL`
                        : "Pending"}
                    </td>
                    <td className="px-6 py-5">
                      <RiskBadge
                        riskBand={assessment.riskBand}
                        label={getRiskScoreLabel(
                          assessment.riskBand,
                          assessment.riskProbability
                        )}
                      />
                    </td>
                    <td className="px-6 py-5">
                      <Link
                        href={`/clinic/predictions/${assessment.requestId}`}
                        className="inline-flex items-center gap-1 text-sm font-semibold text-primary transition-colors hover:text-primary/80"
                      >
                        View
                        <ChevronRight className="size-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-14 text-center">
            <Users className="mx-auto size-10 text-on-surface-variant/60" />
            <p className="mt-4 text-base text-on-surface-variant">
              No recent assessments are available yet.
            </p>
            <Button asChild className="hero-gradient mt-5 text-on-primary">
              <Link href="/clinic/assessment">Create the first assessment</Link>
            </Button>
          </div>
        )}
      </DataTableCard>
    </div>
  )
}
