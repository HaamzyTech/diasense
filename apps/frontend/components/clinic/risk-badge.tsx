import { getRiskBadgeClassName } from "@/lib/clinic/presentation"
import { cn } from "@/lib/utils"

type RiskBadgeProps = {
  riskBand: string | null
  label?: string
  className?: string
}

export function RiskBadge({ riskBand, label, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center border px-3 py-1 text-xs font-semibold uppercase",
        getRiskBadgeClassName(riskBand),
        className
      )}
    >
      {label ?? riskBand ?? "Unassigned"}
    </span>
  )
}
