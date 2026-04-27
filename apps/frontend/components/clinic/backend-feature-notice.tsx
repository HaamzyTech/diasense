import Link from "next/link"
import { AlertTriangle, Info } from "lucide-react"

type BackendFeatureNoticeProps = {
  title: string
  message: string
  actionHref?: string
  actionLabel?: string
  tone?: "warning" | "info"
}

export function BackendFeatureNotice({
  title,
  message,
  actionHref,
  actionLabel,
  tone = "warning",
}: BackendFeatureNoticeProps) {
  const Icon = tone === "info" ? Info : AlertTriangle

  return (
    <div
      className={`rounded-[24px] border p-5 ${
        tone === "info"
          ? "border-primary/15 bg-primary/5"
          : "border-tertiary/20 bg-tertiary-container/30"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-2xl ${
            tone === "info"
              ? "hero-gradient text-on-primary"
              : "bg-tertiary text-on-tertiary"
          }`}
        >
          <Icon className="size-4.5" />
        </div>
        <div className="space-y-2">
          <h2 className="font-headline text-lg font-semibold text-on-surface">
            {title}
          </h2>
          <p className="text-sm leading-6 text-on-surface-variant">{message}</p>
          {actionHref && actionLabel ? (
            <Link
              href={actionHref}
              className="inline-flex text-sm font-semibold text-primary hover:underline"
            >
              {actionLabel}
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  )
}
