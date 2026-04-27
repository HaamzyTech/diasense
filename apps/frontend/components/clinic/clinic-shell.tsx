"use client"

import type { ReactNode } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import {
  Activity,
  Bell,
  FileText,
  HelpCircle,
  LayoutGrid,
  LogOut,
  Menu,
  Plus,
  Search,
  Settings,
  Users,
} from "lucide-react"

import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { logoutAction } from "@/lib/auth/actions"
import type { AuthUser } from "@/lib/auth/types"
import { getInitialsFromReference } from "@/lib/clinic/presentation"
import { cn } from "@/lib/utils"

type ClinicShellProps = {
  children: ReactNode
  user: AuthUser
}

function getRoleLabel(role: string): string {
  switch (role) {
    case "clinician":
      return "Clinician"
    case "admin":
      return "Admin"
    default:
      return "Patient"
  }
}

function getNavItems(role: string) {
  const items = [
    {
      icon: LayoutGrid,
      label: role === "patient" ? "Overview" : "Dashboard",
      href: role === "patient" ? "/clinic" : "/clinic/dashboard",
    },
    { icon: Plus, label: "Assessment", href: "/clinic/assessment" },
    { icon: FileText, label: "Predictions", href: "/clinic/predictions" },
  ]

  if (role === "clinician" || role === "admin") {
    items.splice(2, 0, {
      icon: Users,
      label: "Patients",
      href: "/clinic/patients",
    })
  }

  if (role === "admin") {
    items.push(
      {
        icon: Users,
        label: "Users",
        href: "/clinic/users",
      },
      {
        icon: Activity,
        label: "Monitor",
        href: "/clinic/monitor",
      }
    )
  }

  items.push({
    icon: Settings,
    label: "Settings",
    href: "/clinic/settings",
  })

  return items
}

function getTopNavItems(role: string) {
  const sidebarItems = getNavItems(role)
  return sidebarItems.slice(0, Math.min(sidebarItems.length, 5))
}

function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`)
}

function Sidebar({ className, user }: { className?: string; user: AuthUser }) {
  const pathname = usePathname()
  const initials = getInitialsFromReference(user.email ?? user.username)
  const roleLabel = getRoleLabel(user.role)
  const navItems = getNavItems(user.role)

  return (
    <aside
      className={cn(
        "flex h-full flex-col bg-surface-container-lowest dark:bg-surface-container-low",
        className
      )}
    >
      <div className="p-6">
        <Link
          href="/"
          className="font-headline text-[1.85rem] font-bold tracking-tight text-primary"
        >
          DiaSense Clinic
        </Link>
      </div>

      <div className="px-4 py-3">
        <div
          id="session-overview"
          className="rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4"
        >
          <div className="flex items-center gap-3">
            <div className="hero-gradient flex size-11 shrink-0 items-center justify-center rounded-2xl text-sm font-bold text-on-primary">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-on-surface">
                {user.username}
              </p>
              <p className="text-xs text-on-surface-variant">
                {roleLabel} access
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-xl bg-surface-container-high/50 px-3 py-2">
            <p className="text-[11px] font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
              Authorized via
            </p>
            <p className="mt-1 text-sm text-on-surface">
              {user.auth_source === "environment"
                ? "Environment credentials"
                : "Backend API account"}
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = isActivePath(pathname, item.href)

          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "-ml-0.5 border-l-[3px] bg-primary/10 pl-3.5 text-primary"
                  : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
              )}
            >
              <item.icon className="size-5" />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="space-y-3 p-4">
        <Button asChild className="hero-gradient w-full gap-2 text-on-primary">
          <Link href="/clinic/assessment">
            <Plus className="size-4" />
            New Assessment
          </Link>
        </Button>

        <div className="space-y-1 pt-1">
          <Link
            href="/support"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-on-surface-variant transition-colors hover:bg-surface-container-high"
          >
            <HelpCircle className="size-5" />
            Support
          </Link>

          <form action={logoutAction}>
            <Button
              type="submit"
              variant="ghost"
              className="w-full justify-start gap-3 px-3 text-sm text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
            >
              <LogOut className="size-5" />
              Sign Out
            </Button>
          </form>
        </div>
      </div>
    </aside>
  )
}

export function ClinicShell({ children, user }: ClinicShellProps) {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const topNavItems = getTopNavItems(user.role)
  const searchPlaceholder =
    user.role === "patient" ? "Search predictions..." : "Search patients..."

  return (
    <div className="flex min-h-screen bg-surface">
      <div className="hidden w-72 flex-shrink-0 border-r border-outline-variant/10 lg:block">
        <div className="sticky top-0 h-screen">
          <Sidebar user={user} />
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 border-b border-outline-variant/10 bg-surface-container-lowest/85 backdrop-blur-md dark:bg-surface/80">
          <div className="flex h-14 items-center justify-between px-4 lg:px-6">
            <div className="lg:hidden">
              <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Menu className="size-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-72 p-0">
                  <Sidebar user={user} />
                </SheetContent>
              </Sheet>
            </div>

            <nav className="hidden items-center gap-1 md:flex">
              {topNavItems.map((item) => {
                const isActive = isActivePath(pathname, item.href)

                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    className={cn(
                      "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                      isActive
                        ? "border-b-2 border-primary text-primary"
                        : "text-on-surface-variant hover:text-on-surface"
                    )}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>

            <div className="flex items-center gap-3">
              <div className="relative hidden sm:block">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-on-surface-variant" />
                <Input
                  type="search"
                  placeholder={searchPlaceholder}
                  className="h-11 w-56 border-outline-variant/15 bg-surface-container-high/60 pl-9 lg:w-80"
                />
              </div>

              <div className="hidden rounded-full border border-outline-variant/15 bg-surface-container-low px-3 py-1 text-xs font-semibold text-on-surface-variant sm:block">
                {getRoleLabel(user.role)}
              </div>

              <Button
                variant="ghost"
                size="icon"
                className="text-on-surface-variant"
              >
                <Bell className="size-5" />
              </Button>

              <ThemeToggle />

              <div className="hero-gradient flex size-9 items-center justify-center rounded-full text-xs font-bold text-on-primary">
                {getInitialsFromReference(user.email ?? user.username)}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6">{children}</main>

        <footer className="border-t border-outline-variant/10 bg-surface-container-low/50 px-4 py-8 lg:px-6 dark:bg-surface-container-lowest/50">
          <div className="space-y-4 text-center">
            <p className="font-headline font-semibold text-on-surface">
              DiaSense Clinic
            </p>
            <p className="mx-auto max-w-3xl text-xs leading-6 text-on-surface-variant">
              DiaSense provides diabetes risk assessments from protected
              clinical inputs and should complement, not replace, professional
              medical judgment.
            </p>
            <div className="flex items-center justify-center gap-4 text-xs">
              <Link href="/privacy" className="text-primary hover:underline">
                Privacy Policy
              </Link>
              <Link href="/terms" className="text-primary hover:underline">
                Terms of Service
              </Link>
              <Link href="/support" className="text-primary hover:underline">
                Support
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
