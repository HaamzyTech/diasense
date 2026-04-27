type AccountRecord = {
  username: string
  email: string | null
}

export function getAccountReference(account: AccountRecord): string {
  return account.email ?? account.username
}

export function getAccountSecondaryLabel(account: AccountRecord): string {
  if (account.email) {
    return `@${account.username}`
  }

  return "Username-only account"
}

export function getInitialsFromReference(reference: string): string {
  const normalized = reference.trim()

  if (!normalized) {
    return "DS"
  }

  const [localPart] = normalized.split("@")
  const parts = localPart
    .split(/[._-\s]+/)
    .filter(Boolean)
    .slice(0, 2)

  if (parts.length === 0) {
    return normalized.slice(0, 2).toUpperCase()
  }

  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("")
}

export function formatCalendarDate(value: string | null): string {
  if (!value) {
    return "Not available"
  }

  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function formatCalendarDateTime(value: string | null): string {
  if (!value) {
    return "Not available"
  }

  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

export function formatRiskProbability(probability: number | null): string {
  if (probability === null) {
    return "No result yet"
  }

  return `${(probability * 100).toFixed(1)}%`
}

export function getRiskBadgeClassName(riskBand: string | null): string {
  switch (riskBand) {
    case "high":
      return "border-error/15 bg-error-container/65 text-on-error-container"
    case "moderate":
      return "border-[rgba(191,116,24,0.14)] bg-[rgba(255,181,103,0.28)] text-[rgb(112,67,0)]"
    case "low":
      return "border-[rgba(84,139,177,0.16)] bg-[rgba(186,228,255,0.75)] text-[rgb(62,95,117)]"
    default:
      return "border-outline-variant/15 bg-surface-container-low text-on-surface-variant"
  }
}
