import Link from "next/link"
import { redirect } from "next/navigation"
import { Activity, FileText, Settings, ShieldCheck, Users } from "lucide-react"

import { requireAuthenticatedSession } from "@/lib/auth/server"

function getQuickLinks(role: string) {
  const links = [
    {
      title: "Run Assessment",
      description: "Submit a new set of patient metrics for prediction.",
      href: "/clinic/assessment",
      icon: Activity,
    },
    {
      title: role === "patient" ? "My Predictions" : "Prediction History",
      description: "Review recorded assessments and detailed results.",
      href: "/clinic/predictions",
      icon: FileText,
    },
    {
      title: "Settings",
      description: "Manage your own authenticated account settings.",
      href: "/clinic/settings",
      icon: Settings,
    },
  ]

  if (role === "clinician" || role === "admin") {
    links.splice(1, 0, {
      title: "Patient Management",
      description: "Open the patient roster and launch targeted assessments.",
      href: "/clinic/patients",
      icon: Users,
    })
  }

  if (role === "admin") {
    links.push(
      {
        title: "User Management",
        description: "Review registered users and reassign account roles.",
        href: "/clinic/users",
        icon: ShieldCheck,
      },
      {
        title: "Monitor",
        description: "Inspect operational health, model, and pipeline status.",
        href: "/clinic/monitor",
        icon: Activity,
      }
    )
  }

  return links
}

export default async function DashboardPage() {
  const session = await requireAuthenticatedSession()

  if (session.user.role === "clinician" || session.user.role === "admin") {
    redirect("/clinic/dashboard")
  }

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  })
  const quickLinks = getQuickLinks(session.user.role)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
            Authenticated workspace
          </p>
          <h1 className="font-headline text-2xl font-bold tracking-tight text-on-surface lg:text-3xl">
            Welcome back, {session.user.username}
          </h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            Role: {session.user.role} • {today}
          </p>
        </div>

        <div className="hidden items-center gap-2 rounded-full border border-outline-variant/20 bg-surface-container-high px-4 py-2 dark:flex">
          <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
          <span className="text-xs text-on-surface-variant">
            Active Trials Connectivity: 99.8%
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {quickLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="obsidian-card rounded-[24px] p-5 transition-transform hover:-translate-y-0.5"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-3">
                <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                  Quick access
                </p>
                <div>
                  <h2 className="font-headline text-xl font-semibold text-on-surface">
                    {link.title}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-on-surface-variant">
                    {link.description}
                  </p>
                </div>
              </div>
              <div className="hero-gradient flex size-11 shrink-0 items-center justify-center rounded-2xl text-on-primary">
                <link.icon className="size-5" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
        <h2 className="font-headline text-xl font-semibold text-on-surface">
          Role-aware access summary
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4">
            <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
              Current role
            </p>
            <p className="mt-2 font-headline text-2xl font-bold text-on-surface">
              {session.user.role}
            </p>
            <p className="mt-2 text-sm text-on-surface-variant">
              Access is enforced both in the clinic UI and by the backend API.
            </p>
          </div>

          <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4">
            <p className="text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
              Available now
            </p>
            <div className="mt-3 space-y-2 text-sm text-on-surface">
              {quickLinks.map((link) => (
                <p key={link.href}>{link.title}</p>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
