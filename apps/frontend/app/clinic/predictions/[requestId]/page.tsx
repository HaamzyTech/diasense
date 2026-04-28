import Link from "next/link"
import { redirect } from "next/navigation"

import { DeletePredictionForm } from "@/components/clinic/delete-prediction-form"
import { BackendApiError } from "@/lib/auth/server"
import { requireAuthenticatedSession } from "@/lib/auth/server"
import { fetchPredictionDetail } from "@/lib/clinic/server"

type PredictionDetailPageProps = {
  params: Promise<{
    requestId: string
  }>
}

function DetailRow({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-outline-variant/10 py-3 text-sm last:border-b-0">
      <span className="text-on-surface-variant">{label}</span>
      <span className="font-medium text-on-surface">{value}</span>
    </div>
  )
}

export default async function PredictionDetailPage({
  params,
}: PredictionDetailPageProps) {
  await requireAuthenticatedSession()
  const { requestId } = await params
  let prediction

  try {
    prediction = await fetchPredictionDetail(requestId)
  } catch (error) {
    if (
      error instanceof BackendApiError &&
      (error.status === 403 || error.status === 404)
    ) {
      redirect("/clinic/predictions")
    }

    throw error
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Prediction detail
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          Assessment for {prediction.request.patient_email}
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          Review the submitted assessment metrics, ownership information, and
          generated prediction output for this single request.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.9fr)]">
        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <h2 className="font-headline text-xl font-semibold text-on-surface">
            Submitted data
          </h2>
          <div className="mt-4">
            <DetailRow
              label="Patient"
              value={prediction.request.patient_email}
            />
            <DetailRow
              label="Submitted by"
              value={prediction.request.submitted_by}
            />
            <DetailRow
              label="Actor role"
              value={prediction.request.actor_role}
            />
            <DetailRow
              label="Pregnancies"
              value={prediction.request.pregnancies}
            />
            <DetailRow label="Glucose" value={prediction.request.glucose} />
            <DetailRow
              label="Blood pressure"
              value={prediction.request.blood_pressure}
            />
            <DetailRow
              label="Skin thickness"
              value={prediction.request.skin_thickness}
            />
            <DetailRow label="Insulin" value={prediction.request.insulin} />
            <DetailRow label="BMI" value={prediction.request.bmi} />
            <DetailRow
              label="Diabetes pedigree function"
              value={prediction.request.diabetes_pedigree_function}
            />
            <DetailRow label="Age" value={prediction.request.age} />
            <DetailRow
              label="Created"
              value={new Date(prediction.request.created_at).toLocaleString()}
            />
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
            <h2 className="font-headline text-xl font-semibold text-on-surface">
              Prediction result
            </h2>

            {prediction.result ? (
              <div className="mt-4 space-y-4">
                <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4">
                  <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Risk band
                  </p>
                  <p className="mt-2 font-headline text-3xl font-bold text-on-surface">
                    {prediction.result.risk_band}
                  </p>
                  <p className="mt-2 text-sm text-on-surface-variant">
                    Probability{" "}
                    {prediction.result.risk_probability !== null
                      ? `${(prediction.result.risk_probability * 100).toFixed(1)}%`
                      : "N/A"}
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Interpretation
                  </p>
                  <p className="text-sm leading-6 text-on-surface-variant">
                    {prediction.result.interpretation}
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Top factors
                  </p>
                  <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4">
                    {prediction.result.top_factors.length > 0 ? (
                      <div className="space-y-3">
                        {prediction.result.top_factors.map((factor) => (
                          <div
                            key={factor.feature}
                            className="flex items-center justify-between text-sm"
                          >
                            <span className="text-on-surface">
                              {factor.feature}
                            </span>
                            <span className="font-semibold text-on-surface">
                              {factor.importance.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-on-surface-variant">
                        No factor explanations were returned for this
                        prediction.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-on-surface-variant">
                No prediction result has been generated for this request yet.
              </p>
            )}
          </div>

          <div className="flex gap-3">
            <Link
              href="/clinic/predictions"
              className="inline-flex rounded-xl border border-outline-variant/15 px-4 py-2 text-sm font-semibold text-on-surface hover:bg-surface-container-low"
            >
              Back to predictions
            </Link>
            <Link
              href={`/clinic/assessment?patient=${encodeURIComponent(
                prediction.request.patient_email
              )}`}
              className="hero-gradient inline-flex rounded-xl px-4 py-2 text-sm font-semibold text-on-primary"
            >
              Start related assessment
            </Link>
            <DeletePredictionForm
              requestId={prediction.request.id}
              label={`assessment ${prediction.request.id}`}
              redirectTo="/clinic/predictions"
            />
          </div>
        </section>
      </div>
    </div>
  )
}
