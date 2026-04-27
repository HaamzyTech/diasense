"use client"

import Link from "next/link"
import { useActionState } from "react"
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react"

import { PatientAccountCombobox } from "@/components/clinic/patient-account-combobox"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { assessmentAction } from "@/lib/clinic/actions"
import {
  initialAssessmentFormState,
  type AssessmentFieldErrors,
} from "@/lib/clinic/types"

type AssessmentFormProps = {
  canAssessPatients: boolean
  defaultPatientEmail?: string
  patientOptions?: Array<{
    value: string
    label: string
    description?: string
  }>
}

const numericFields = [
  {
    name: "pregnancies",
    label: "Pregnancies",
    step: "1",
    min: "0",
    max: "30",
    defaultValue: "0",
  },
  {
    name: "glucose",
    label: "Glucose",
    step: "0.1",
    min: "0",
    max: "300",
    defaultValue: "138",
  },
  {
    name: "blood_pressure",
    label: "Blood Pressure",
    step: "0.1",
    min: "0",
    max: "200",
    defaultValue: "72",
  },
  {
    name: "skin_thickness",
    label: "Skin Thickness",
    step: "0.1",
    min: "0",
    max: "100",
    defaultValue: "35",
  },
  {
    name: "insulin",
    label: "Insulin",
    step: "0.1",
    min: "0",
    max: "1000",
    defaultValue: "0",
  },
  {
    name: "bmi",
    label: "BMI",
    step: "0.1",
    min: "0",
    max: "100",
    defaultValue: "33.6",
  },
  {
    name: "diabetes_pedigree_function",
    label: "Diabetes Pedigree Function",
    step: "0.001",
    min: "0",
    max: "10",
    defaultValue: "0.627",
  },
  {
    name: "age",
    label: "Age",
    step: "1",
    min: "1",
    max: "120",
    defaultValue: "50",
  },
] as const

function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null
  }

  return <p className="text-sm text-error">{message}</p>
}

function getRiskTone(riskBand: string) {
  switch (riskBand) {
    case "high":
      return "border-error/20 bg-error-container/70 text-on-error-container"
    case "moderate":
      return "border-tertiary/20 bg-tertiary-container/35 text-on-surface"
    default:
      return "border-secondary/20 bg-secondary-container/35 text-on-surface"
  }
}

const inputClassName =
  "h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 text-sm text-on-surface shadow-none focus-visible:border-primary focus-visible:ring-0"

export function AssessmentForm({
  canAssessPatients,
  defaultPatientEmail,
  patientOptions = [],
}: AssessmentFormProps) {
  const [state, formAction, isPending] = useActionState(
    assessmentAction,
    initialAssessmentFormState
  )
  const fieldErrors: AssessmentFieldErrors = state.fieldErrors ?? {}

  return (
    <div className="space-y-6">
      <form action={formAction} className="space-y-8">
        {canAssessPatients ? (
          <div className="space-y-3">
            <label
              htmlFor="patient_email"
              className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
            >
              Account to assess
            </label>
            <PatientAccountCombobox
              id="patient_email"
              name="patient_email"
              defaultValue={defaultPatientEmail}
              error={fieldErrors.patient_email}
              placeholder="Search accounts by email or username"
              options={patientOptions}
            />
            <p className="text-sm text-on-surface-variant">
              Leave this blank to assess your own account.
            </p>
            <FieldError message={fieldErrors.patient_email} />
          </div>
        ) : null}

        <div className="grid gap-x-6 gap-y-5 md:grid-cols-2">
          {numericFields.map((field) => (
            <div key={field.name} className="space-y-2">
              <label
                htmlFor={field.name}
                className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
              >
                {field.label}
              </label>
              <Input
                id={field.name}
                name={field.name}
                type="number"
                step={field.step}
                min={field.min}
                max={field.max}
                defaultValue={field.defaultValue}
                aria-invalid={Boolean(fieldErrors[field.name])}
                className={inputClassName}
              />
              <FieldError message={fieldErrors[field.name]} />
            </div>
          ))}
        </div>

        {state.message ? (
          <div
            role="alert"
            className={`rounded-xl px-4 py-3 text-sm ${
              state.result
                ? "border border-[rgba(52,168,83,0.18)] bg-[rgba(52,168,83,0.12)] text-[rgb(22,101,52)]"
                : "border border-outline-variant/15 bg-surface-container-low text-on-surface-variant"
            }`}
          >
            {state.message}
          </div>
        ) : null}

        <Button
          type="submit"
          disabled={isPending}
          className="hero-gradient h-12 rounded-xl px-5 text-on-primary"
        >
          {isPending ? "Running assessment..." : "Submit Assessment"}
          <ArrowRight className="size-4.5" />
        </Button>
      </form>

      {state.result ? (
        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_18px_50px_rgba(25,28,29,0.06)] dark:shadow-none">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-outline-variant/15 bg-surface-container-low px-3 py-1 text-xs font-semibold tracking-[0.18em] text-primary uppercase">
                <Sparkles className="size-3.5" />
                Prediction ready
              </div>
              <h3 className="font-headline text-2xl font-bold text-on-surface">
                Risk band: {state.result.risk_band}
              </h3>
              <p className="max-w-2xl text-sm leading-6 text-on-surface-variant">
                {state.result.interpretation}
              </p>
            </div>

            <div
              className={`border px-4 py-3 text-sm ${getRiskTone(state.result.risk_band)}`}
            >
              <p className="font-semibold">
                Probability {(state.result.risk_probability * 100).toFixed(1)}%
              </p>
              <p className="mt-1">Patient: {state.result.patient_email}</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-outline-variant/10 bg-surface-container-low p-4">
              <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                Submission details
              </p>
              <div className="mt-3 space-y-2 text-sm text-on-surface">
                <p>Submitted by: {state.result.submitted_by}</p>
                <p>Latency: {state.result.latency_ms} ms</p>
                <p>
                  Created: {new Date(state.result.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-outline-variant/10 bg-surface-container-low p-4">
              <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                Top factors
              </p>
              <div className="mt-3 space-y-2">
                {state.result.top_factors.length > 0 ? (
                  state.result.top_factors.map((factor) => (
                    <div
                      key={factor.feature}
                      className="flex items-center justify-between text-sm text-on-surface"
                    >
                      <span>{factor.feature}</span>
                      <span className="font-semibold">
                        {factor.importance.toFixed(2)}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-on-surface-variant">
                    No feature importance details were returned for this result.
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              asChild
              className="hero-gradient rounded-xl text-on-primary"
            >
              <Link href={`/clinic/predictions/${state.result.request_id}`}>
                Open prediction details
              </Link>
            </Button>
            <Button asChild variant="outline" className="rounded-xl">
              <Link href="/clinic/predictions">View prediction history</Link>
            </Button>
          </div>
        </section>
      ) : null}

      <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-low p-5">
        <div className="flex items-start gap-3">
          <div className="hero-gradient flex size-10 shrink-0 items-center justify-center rounded-xl text-on-primary">
            <ShieldCheck className="size-4.5" />
          </div>
          <div className="space-y-2">
            <h3 className="font-headline text-lg font-semibold text-on-surface">
              Protected clinical workflow
            </h3>
            <p className="text-sm leading-6 text-on-surface-variant">
              Submitted assessments are tied to the authenticated account and
              governed by backend role checks before prediction history becomes
              visible in the clinic workspace.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
