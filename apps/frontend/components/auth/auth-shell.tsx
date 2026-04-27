import type { ReactNode } from "react"
import Link from "next/link"
import { Activity, LockKeyhole, ShieldCheck, UserCheck } from "lucide-react"

import { Separator } from "@/components/ui/separator"

type AuthShellProps = {
  eyebrow: string
  title: string
  description: string
  alternatePrompt: string
  alternateHref: string
  alternateLabel: string
  children: ReactNode
}

const authHighlights = [
  {
    icon: UserCheck,
    label: "Validated access",
    description:
      "Credentials are checked before protected clinic pages are rendered.",
  },
  {
    icon: ShieldCheck,
    label: "Protected workspace",
    description:
      "Authenticated sessions are routed into the secured clinic experience.",
  },
  {
    icon: LockKeyhole,
    label: "Secure sessions",
    description:
      "Session handling is enforced through the backend API and server-side guards.",
  },
]

export function AuthShell({
  eyebrow,
  title,
  description,
  alternatePrompt,
  alternateHref,
  alternateLabel,
  children,
}: AuthShellProps) {
  return (
    <div className="grid w-full max-w-6xl gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)] lg:items-center">
      <section className="order-2 rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_24px_60px_rgba(25,28,29,0.08)] sm:p-8 lg:order-1 lg:p-10 dark:shadow-none">
        {children}
      </section>

      <aside className="order-1 space-y-6 lg:order-2">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-outline-variant/20 bg-surface-container-low px-4 py-2 text-xs font-semibold tracking-[0.24em] text-primary uppercase">
            <Activity className="size-3.5" />
            {eyebrow}
          </div>
          <div className="space-y-3">
            <h1 className="font-headline text-4xl font-bold tracking-tight text-on-surface sm:text-5xl">
              {title}
            </h1>
            <p className="max-w-xl text-base leading-7 text-on-surface-variant sm:text-lg">
              {description}
            </p>
          </div>
        </div>

        <div className="glass-panel rounded-[28px] border border-outline-variant/10 p-6 sm:p-7">
          <div className="space-y-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                Secure access
              </p>
              <p className="mt-2 text-sm leading-6 text-on-surface-variant">
                Authentication is validated against the backend API and routed
                into the protected clinic workspace.
              </p>
            </div>

            <Separator className="bg-outline-variant/20" />

            <div className="space-y-3">
              {authHighlights.map((highlight) => (
                <div
                  key={highlight.label}
                  className="rounded-2xl border border-outline-variant/10 bg-surface-container-lowest/80 p-4"
                >
                  <div className="flex items-start gap-3">
                    <div className="hero-gradient flex size-10 shrink-0 items-center justify-center rounded-2xl text-on-primary">
                      <highlight.icon className="size-4.5" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-headline text-lg font-semibold text-on-surface">
                        {highlight.label}
                      </p>
                      <p className="text-sm leading-6 text-on-surface-variant">
                        {highlight.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <p className="text-sm text-on-surface-variant">
          {alternatePrompt}{" "}
          <Link
            href={alternateHref}
            className="font-semibold text-primary transition-colors hover:text-primary-container hover:underline"
          >
            {alternateLabel}
          </Link>
        </p>
      </aside>
    </div>
  )
}
