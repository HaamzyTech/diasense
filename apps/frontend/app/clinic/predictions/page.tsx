import Link from "next/link"

import { BackendFeatureNotice } from "@/components/clinic/backend-feature-notice"
import { DataTableCard } from "@/components/clinic/data-table-card"
import { DeletePredictionForm } from "@/components/clinic/delete-prediction-form"
import { RiskBadge } from "@/components/clinic/risk-badge"
import { Button } from "@/components/ui/button"
import { requireAuthenticatedSession } from "@/lib/auth/server"
import {
  getClinicFeatureErrorMessage,
  isMissingBackendFeature,
} from "@/lib/clinic/errors"
import { formatCalendarDateTime } from "@/lib/clinic/presentation"
import { fetchLegacyMyPredictions, fetchPredictions } from "@/lib/clinic/server"
import type { PredictionListResponse } from "@/lib/clinic/types"

type PredictionsPageProps = {
  searchParams?: Promise<{
    patient?: string
  }>
}

function getRiskLabel(riskBand: string, probability: number) {
  return `${riskBand} (${Math.round(probability * 100)})`
}

export default async function PredictionsPage({
  searchParams,
}: PredictionsPageProps) {
  const session = await requireAuthenticatedSession()
  const resolvedSearchParams = searchParams ? await searchParams : undefined
  const canFilterPatients =
    session.user.role === "clinician" || session.user.role === "admin"
  const patientFilter = canFilterPatients
    ? resolvedSearchParams?.patient
    : undefined
  let predictions: PredictionListResponse = { items: [], count: 0 }
  let loadMessage: string | null = null

  try {
    predictions = await fetchPredictions({
      patientEmail: patientFilter,
      limit: 100,
    })
  } catch (error) {
    if (
      session.user.role === "patient" &&
      patientFilter === undefined &&
      isMissingBackendFeature(error)
    ) {
      try {
        predictions = await fetchLegacyMyPredictions(100)
        loadMessage =
          "Prediction history was loaded through the legacy patient endpoint while the backend routes catch up."
      } catch (legacyError) {
        loadMessage = getClinicFeatureErrorMessage(
          legacyError,
          "prediction history"
        )
      }
    } else {
      loadMessage = getClinicFeatureErrorMessage(error, "prediction history")
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Prediction history
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          {session.user.role === "patient"
            ? "Your past assessments"
            : "Assessment predictions"}
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          {patientFilter
            ? `Showing predictions linked to ${patientFilter}.`
            : session.user.role === "patient"
              ? "Review every prediction linked to your authenticated account."
              : "Browse protected prediction history across the clinic workspace."}
        </p>
      </div>

      {loadMessage ? (
        <BackendFeatureNotice
          title={
            loadMessage.includes("legacy patient endpoint")
              ? "Prediction history loaded in compatibility mode"
              : "Prediction history is temporarily unavailable"
          }
          message={loadMessage}
          actionHref="/clinic/assessment"
          actionLabel="Run a new assessment"
          tone={
            loadMessage.includes("legacy patient endpoint") ? "info" : "warning"
          }
        />
      ) : null}

      <DataTableCard
        title="Recorded Predictions"
        subtitle={`${predictions.count} protected result${predictions.count === 1 ? "" : "s"} currently visible in this view.`}
        toolbar={
          <>
            {patientFilter ? (
              <Button
                asChild
                variant="outline"
                className="h-11 border-outline-variant/20 bg-surface-container-lowest"
              >
                <Link href="/clinic/predictions">Clear patient filter</Link>
              </Button>
            ) : null}
            <Button asChild className="hero-gradient h-11 text-on-primary">
              <Link href="/clinic/assessment">New assessment</Link>
            </Button>
          </>
        }
        footer={
          loadMessage
            ? "Prediction data could not be loaded from the backend right now."
            : `Showing ${predictions.items.length} prediction record${predictions.items.length === 1 ? "" : "s"}`
        }
      >
        {predictions.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1040px]">
              <thead>
                <tr className="border-b border-outline-variant/10">
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Created
                  </th>
                  {session.user.role !== "patient" ? (
                    <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                      Patient
                    </th>
                  ) : null}
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Submitted by
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Risk score
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Probability
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Interpretation
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {predictions.items.map((item) => (
                  <tr
                    key={item.request_id}
                    className="transition-colors hover:bg-surface-container-low/60"
                  >
                    <td className="px-6 py-5 text-sm text-on-surface-variant">
                      {formatCalendarDateTime(item.created_at)}
                    </td>
                    {session.user.role !== "patient" ? (
                      <td className="px-6 py-5 text-base font-medium text-on-surface">
                        {item.patient_email}
                      </td>
                    ) : null}
                    <td className="px-6 py-5 text-base text-on-surface">
                      {item.submitted_by}
                    </td>
                    <td className="px-6 py-5">
                      <RiskBadge
                        riskBand={item.risk_band}
                        label={getRiskLabel(
                          item.risk_band,
                          item.risk_probability
                        )}
                      />
                    </td>
                    <td className="px-6 py-5 text-base font-medium text-on-surface">
                      {(item.risk_probability * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-5 text-sm text-on-surface-variant">
                      {item.interpretation}
                    </td>
                    <td className="px-6 py-5 text-sm">
                      <div className="flex flex-wrap items-start gap-3">
                        <Link
                          href={`/clinic/predictions/${item.request_id}`}
                          className="font-semibold text-primary transition-colors hover:text-primary/80"
                        >
                          View details
                        </Link>
                        <DeletePredictionForm
                          requestId={item.request_id}
                          label={`assessment ${item.request_id}`}
                          compact
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <p className="text-sm text-on-surface-variant">
              {loadMessage
                ? "Prediction data could not be loaded from the backend right now."
                : "No predictions have been recorded for this view yet."}
            </p>
            <Button asChild className="hero-gradient mt-4 text-on-primary">
              <Link href="/clinic/assessment">Run a new assessment</Link>
            </Button>
          </div>
        )}
      </DataTableCard>
    </div>
  )
}
