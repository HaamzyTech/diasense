import Link from "next/link"
import { ThemeToggle } from "@/components/theme-toggle"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "DiaSense-Auth",
  description:
    "Login or sign up to access DiaSense, an AI application that helps predict diabetes risk.",
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen flex-col bg-surface text-on-surface">
      {/* Header */}
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-8 py-8">
        <Link
          href="/"
          className="font-headline text-2xl font-bold tracking-tight text-primary"
        >
          DiaSense
        </Link>
        <ThemeToggle />
      </header>

      {/* Main Content */}
      <main className="flex flex-grow items-center justify-center px-6 py-12">
        {children}
      </main>

      {/* Footer */}
      <footer className="mt-auto w-full bg-surface-container-low dark:bg-surface-container-lowest">
        <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-8 px-8 py-12 md:grid-cols-2">
          <div className="flex flex-col gap-2">
            <span className="font-headline text-lg font-bold text-on-surface">
              DiaSense
            </span>
            <p className="text-xs tracking-wide text-on-surface-variant">
              © 2024 DiaSense. HIPAA Compliant.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 md:justify-end">
            <Link
              href="/privacy"
              className="text-xs tracking-wide text-on-surface-variant transition-all hover:text-on-surface hover:underline"
            >
              Privacy Policy
            </Link>
            <Link
              href="/terms"
              className="text-xs tracking-wide text-on-surface-variant transition-all hover:text-on-surface hover:underline"
            >
              Terms of Service
            </Link>
            <Link
              href="/support"
              className="text-xs tracking-wide text-on-surface-variant transition-all hover:text-on-surface hover:underline"
            >
              Security Architecture
            </Link>
            <Link
              href="/support"
              className="text-xs tracking-wide text-on-surface-variant transition-all hover:text-on-surface hover:underline"
            >
              Clinical Oversight
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
