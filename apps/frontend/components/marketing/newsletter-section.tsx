"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function NewsletterSection() {
  const [email, setEmail] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle form submission
    console.log("Newsletter signup:", email)
    setEmail("")
  }

  return (
    <section className="relative overflow-hidden bg-secondary-container/30 px-6 py-24 lg:px-8 lg:py-32 dark:bg-surface-container-high">
      {/* Background Gradient Effect */}
      <div className="absolute top-0 left-1/2 h-full w-full -translate-x-1/2 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent"></div>

      <div className="relative z-10 mx-auto max-w-4xl space-y-8 text-center">
        <h2 className="text-3xl font-extrabold text-balance text-on-surface md:text-4xl lg:text-5xl">
          The Future of Metabolic Health is Clinical.
        </h2>
        <p className="text-lg text-on-surface-variant">
          Join 2,500+ clinicians receiving our bi-weekly whitepapers on
          predictive diabetes risk management.
        </p>
        <form
          onSubmit={handleSubmit}
          className="mx-auto flex max-w-xl flex-col gap-4 pt-4 md:flex-row"
        >
          <Input
            type="email"
            placeholder="professional@clinic.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="h-auto flex-1 rounded-full border border-outline-variant/30 bg-white px-6 py-4 text-on-surface placeholder:text-outline focus:border-transparent focus:ring-2 focus:ring-primary dark:border-white/10 dark:bg-background"
          />
          <Button
            type="submit"
            className="hero-gradient h-auto rounded-full px-8 py-4 font-bold text-white shadow-lg shadow-primary/20 transition-all hover:opacity-90"
          >
            Subscribe
          </Button>
        </form>
        <p className="text-[10px] font-bold tracking-[0.2em] text-outline uppercase">
          No Spam. HIPAA compliant data handling.
        </p>
      </div>
    </section>
  )
}
