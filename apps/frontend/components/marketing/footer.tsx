import Link from "next/link"

const legalLinks = [
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/terms", label: "Terms of Service" },
]

const integrityLinks = [
  { href: "/support", label: "Security Architecture" },
  { href: "/support", label: "Clinical Oversight" },
]

export function Footer() {
  return (
    <footer className="border-t border-outline-variant/10 bg-surface-container-low dark:border-white/5 dark:bg-background">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-8 px-6 py-12 md:grid-cols-2 lg:gap-12 lg:px-8 lg:py-16">
        <div className="space-y-4 lg:space-y-6">
          <div className="text-lg font-extrabold text-primary lg:text-2xl">
            DiaSense
          </div>
          <p className="max-w-xs text-xs leading-relaxed font-medium text-on-surface-variant lg:text-sm">
            Leading the transition from reactive care to proactive metabolic
            management through clinical AI.
          </p>
          <div className="text-[10px] font-bold tracking-widest text-outline uppercase">
            &copy; 2024 DiaSense. HIPAA Compliant.
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:gap-8">
          <div className="flex flex-col space-y-3 lg:space-y-4">
            <h4 className="text-xs font-bold tracking-widest text-on-surface uppercase">
              Legal
            </h4>
            {legalLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="text-xs font-medium text-on-surface-variant transition-all hover:text-primary lg:text-sm"
              >
                {link.label}
              </Link>
            ))}
          </div>
          <div className="flex flex-col space-y-3 lg:space-y-4">
            <h4 className="text-xs font-bold tracking-widest text-on-surface uppercase">
              Integrity
            </h4>
            {integrityLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="text-xs font-medium text-on-surface-variant transition-all hover:text-primary lg:text-sm"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}
