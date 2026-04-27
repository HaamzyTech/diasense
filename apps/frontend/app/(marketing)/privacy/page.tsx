import { ShieldCheck } from "lucide-react"

export default function PrivacyPage() {
  return (
    <section className="bg-surface px-6 py-16 text-on-surface lg:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-outline-variant/20 bg-surface-container-low px-4 py-2 text-xs font-semibold tracking-[0.2em] text-primary uppercase">
            <ShieldCheck className="size-3.5" />
            Privacy
          </div>
          <h1 className="font-headline text-4xl font-bold tracking-tight">
            Privacy policy
          </h1>
          <p className="max-w-3xl text-sm leading-7 text-on-surface-variant">
            DiaSense is designed to handle clinical access carefully. This page
            summarizes how account credentials, protected assessments, and
            related workspace activity are treated across the application.
          </p>
        </div>

        <div className="space-y-4">
          <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6">
            <h2 className="font-headline text-xl font-semibold">
              Data handling
            </h2>
            <p className="mt-3 text-sm leading-7 text-on-surface-variant">
              Authentication tokens are stored in secure HTTP-only cookies, and
              protected clinic pages validate authenticated access before
              rendering patient-related content.
            </p>
          </div>

          <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6">
            <h2 className="font-headline text-xl font-semibold">
              Access boundaries
            </h2>
            <p className="mt-3 text-sm leading-7 text-on-surface-variant">
              Patients can only see their own prediction history. Clinicians and
              admins receive broader access based on backend role enforcement.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
