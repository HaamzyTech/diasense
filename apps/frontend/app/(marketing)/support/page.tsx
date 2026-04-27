import Link from "next/link"
import { LifeBuoy } from "lucide-react"

export default function SupportPage() {
  return (
    <section className="bg-surface px-6 py-16 text-on-surface lg:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-outline-variant/20 bg-surface-container-low px-4 py-2 text-xs font-semibold tracking-[0.2em] text-primary uppercase">
            <LifeBuoy className="size-3.5" />
            Support
          </div>
          <h1 className="font-headline text-4xl font-bold tracking-tight">
            Support and guidance
          </h1>
          <p className="max-w-3xl text-sm leading-7 text-on-surface-variant">
            If you are unable to sign in, need help interpreting workflow
            access, or want to review legal and privacy guidance, the links
            below will take you to the right place.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Link
            href="/login"
            className="rounded-[24px] border border-outline-variant/10 bg-surface-container-lowest p-5 transition-transform hover:-translate-y-0.5"
          >
            <h2 className="font-headline text-xl font-semibold text-on-surface">
              Sign in
            </h2>
            <p className="mt-2 text-sm leading-6 text-on-surface-variant">
              Return to the secure login screen for protected workspace access.
            </p>
          </Link>
          <Link
            href="/privacy"
            className="rounded-[24px] border border-outline-variant/10 bg-surface-container-lowest p-5 transition-transform hover:-translate-y-0.5"
          >
            <h2 className="font-headline text-xl font-semibold text-on-surface">
              Privacy
            </h2>
            <p className="mt-2 text-sm leading-6 text-on-surface-variant">
              Review how sessions and protected health-related workflows are
              handled in the application.
            </p>
          </Link>
          <Link
            href="/terms"
            className="rounded-[24px] border border-outline-variant/10 bg-surface-container-lowest p-5 transition-transform hover:-translate-y-0.5"
          >
            <h2 className="font-headline text-xl font-semibold text-on-surface">
              Terms
            </h2>
            <p className="mt-2 text-sm leading-6 text-on-surface-variant">
              Review the intended-use guidance for DiaSense predictions and
              clinical review.
            </p>
          </Link>
        </div>
      </div>
    </section>
  )
}
