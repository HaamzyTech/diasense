"use client"

import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { MenuIcon } from "@hugeicons/core-free-icons"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

const navLinks = [
  { href: "#solutions", label: "Solutions" },
  { href: "#providers", label: "Providers" },
  { href: "#patients", label: "Patients" },
  { href: "#research", label: "Research" },
]

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-outline-variant/10 bg-surface/80 backdrop-blur-md dark:border-white/5 dark:bg-background/80">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
        <Link
          href="/"
          className="text-2xl font-extrabold tracking-tight text-primary"
        >
          DiaSense
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-on-surface-variant transition-colors duration-200 hover:text-primary"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2 lg:gap-4">
          <ThemeToggle />
          <Button
            asChild
            variant="ghost"
            className="hidden text-sm font-semibold text-on-primary-fixed-variant hover:text-primary sm:inline-flex dark:text-on-surface"
          >
            <Link href="/login">Secure Login</Link>
          </Button>
          <Button className="hero-gradient rounded-xl px-4 py-2.5 text-sm font-semibold text-white lg:px-6">
            <Link href="/signup">Signup</Link>
          </Button>

          {/* Mobile Menu */}
          <Sheet>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon">
                <HugeiconsIcon icon={MenuIcon} size={20} />
                <span className="sr-only">Open menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="bg-surface dark:bg-surface-container"
            >
              <div className="mt-8 flex flex-col gap-6">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="text-lg font-medium text-on-surface transition-colors hover:text-primary"
                  >
                    {link.label}
                  </Link>
                ))}
                <Button
                  asChild
                  variant="ghost"
                  className="justify-start px-0 font-semibold text-on-surface-variant"
                >
                  <Link href="/login">Secure Login</Link>
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  )
}
