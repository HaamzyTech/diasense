import { BackendFeatureNotice } from "@/components/clinic/backend-feature-notice"
import { requireRoleSession } from "@/lib/auth/guards"
import { getClinicFeatureErrorMessage } from "@/lib/clinic/errors"
import { fetchOpsSummary } from "@/lib/clinic/server"
import type { OpsSummary } from "@/lib/clinic/types"

export default async function MonitorPage() {
  await requireRoleSession(["admin"])
  let summary: OpsSummary | null = null
  let loadMessage: string | null = null

  try {
    summary = await fetchOpsSummary()
  } catch (error) {
    loadMessage = getClinicFeatureErrorMessage(error, "monitoring details")
  }

  const dependencyEntries = Object.entries(summary?.services ?? {})

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Monitor
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          Operational summary
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          Admin-only monitoring surfaces the backend readiness snapshot,
          dependency states, active model metadata, and the latest pipeline and
          drift health indicators.
        </p>
      </div>

      {loadMessage ? (
        <BackendFeatureNotice
          title="Monitoring is temporarily unavailable"
          message={loadMessage}
          actionHref="/clinic/dashboard"
          actionLabel="Return to dashboard"
        />
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="obsidian-card rounded-[24px] p-5">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            Service
          </p>
          <p className="mt-3 font-headline text-2xl font-bold text-on-surface">
            {summary?.service ?? "Unavailable"}
          </p>
          <p className="mt-2 text-sm text-on-surface-variant">
            Version {summary?.version ?? "Unavailable"}
          </p>
        </div>
        <div className="obsidian-card rounded-[24px] p-5">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            Pipeline
          </p>
          <p className="mt-3 font-headline text-2xl font-bold text-on-surface">
            {summary?.latest_pipeline_status ?? "Unavailable"}
          </p>
        </div>
        <div className="obsidian-card rounded-[24px] p-5">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            Drift
          </p>
          <p className="mt-3 font-headline text-2xl font-bold text-on-surface">
            {summary?.latest_drift_status ?? "Unavailable"}
          </p>
        </div>
        <div className="obsidian-card rounded-[24px] p-5">
          <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
            Active model
          </p>
          <p className="mt-3 font-headline text-2xl font-bold text-on-surface">
            {summary?.active_model?.model_version ?? "Unavailable"}
          </p>
          <p className="mt-2 text-sm text-on-surface-variant">
            {summary?.active_model?.model_name ?? "No active model"}
          </p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <h2 className="font-headline text-lg font-semibold text-on-surface">
            Dependency status
          </h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {dependencyEntries.length > 0 ? (
              dependencyEntries.map(([service, status]) => (
                <div
                  key={service}
                  className="rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4"
                >
                  <p className="text-sm font-semibold text-on-surface">
                    {service}
                  </p>
                  <p className="mt-2 text-sm text-on-surface-variant">
                    {status}
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-outline-variant/20 bg-surface-container-low p-4 text-sm text-on-surface-variant md:col-span-2">
                Dependency health could not be loaded from the backend.
              </div>
            )}
          </div>
        </section>

        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <h2 className="font-headline text-lg font-semibold text-on-surface">
            Snapshot metadata
          </h2>
          <div className="mt-4 space-y-3 text-sm text-on-surface-variant">
            <p>
              Captured:{" "}
              {summary?.timestamp
                ? new Date(summary.timestamp).toLocaleString()
                : "Unavailable"}
            </p>
            <p>Model stage: {summary?.active_model?.stage ?? "Unavailable"}</p>
            <p>
              Model version:{" "}
              {summary?.active_model?.model_version ?? "Unavailable"}
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
