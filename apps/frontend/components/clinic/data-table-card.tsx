import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

type DataTableCardProps = {
  title: string
  subtitle?: string
  toolbar?: ReactNode
  footer?: ReactNode
  children: ReactNode
  className?: string
}

export function DataTableCard({
  title,
  subtitle,
  toolbar,
  footer,
  children,
  className,
}: DataTableCardProps) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none",
        className
      )}
    >
      <div className="flex flex-col gap-4 border-b border-outline-variant/10 px-6 py-5 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <h2 className="font-headline text-[1.9rem] font-semibold tracking-tight text-on-surface">
            {title}
          </h2>
          {subtitle ? (
            <p className="text-sm text-on-surface-variant">{subtitle}</p>
          ) : null}
        </div>
        {toolbar ? (
          <div className="flex flex-wrap items-center gap-3">{toolbar}</div>
        ) : null}
      </div>

      <div>{children}</div>

      {footer ? (
        <div className="border-t border-outline-variant/10 px-6 py-5 text-sm text-on-surface-variant">
          {footer}
        </div>
      ) : null}
    </section>
  )
}
