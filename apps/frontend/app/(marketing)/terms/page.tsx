import { FileCheck2 } from "lucide-react"

export default function TermsPage() {
  return (
    <section className="bg-surface px-6 py-16 text-on-surface lg:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-outline-variant/20 bg-surface-container-low px-4 py-2 text-xs font-semibold tracking-[0.2em] text-primary uppercase">
            <FileCheck2 className="size-3.5" />
            Terms
          </div>
          <h1 className="font-headline text-4xl font-bold tracking-tight">
            Terms of service
          </h1>
          <p className="max-w-3xl text-sm leading-7 text-on-surface-variant">
            DiaSense provides decision-support style outputs for diabetes risk
            review. Predictions and explanations are informational and do not
            replace medical diagnosis or clinical judgment.
          </p>
        </div>

        <div className="space-y-4">
          <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6">
            <h2 className="font-headline text-xl font-semibold">
              Intended use
            </h2>
            <p className="mt-3 text-sm leading-7 text-on-surface-variant">
              The application is intended for secure assessment workflows and
              review of prediction outputs within the DiaSense workspace.
            </p>
          </div>

          <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6">
            <h2 className="font-headline text-xl font-semibold">
              Clinical responsibility
            </h2>
            <p className="mt-3 text-sm leading-7 text-on-surface-variant">
              Care decisions remain the responsibility of the patient and their
              healthcare professionals. Administrative access does not change
              this obligation.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
