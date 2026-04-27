"use client"

import Link from "next/link"
import { useActionState } from "react"
import { ArrowRight, AtSign, KeyRound, Mail } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { signupAction } from "@/lib/auth/actions"
import { initialAuthFormState } from "@/lib/auth/types"

export function SignupForm() {
  const [state, formAction, isPending] = useActionState(
    signupAction,
    initialAuthFormState
  )

  return (
    <form action={formAction} className="space-y-6">
      <div className="space-y-2">
        <label
          htmlFor="username"
          className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
        >
          Username
        </label>
        <div className="group relative">
          <Input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            placeholder="dr.richardson"
            aria-invalid={Boolean(state.fieldErrors?.username)}
            className="h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 pr-12 text-sm text-on-surface shadow-none placeholder:text-outline focus-visible:border-primary focus-visible:ring-0"
          />
          <AtSign className="pointer-events-none absolute top-1/2 right-4 size-4.5 -translate-y-1/2 text-on-surface-variant transition-colors group-focus-within:text-primary" />
        </div>
        {state.fieldErrors?.username ? (
          <p className="text-sm text-error">{state.fieldErrors.username}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <label
          htmlFor="email"
          className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
        >
          Email address
        </label>
        <div className="group relative">
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="name@example.com (optional)"
            aria-invalid={Boolean(state.fieldErrors?.email)}
            className="h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 pr-12 text-sm text-on-surface shadow-none placeholder:text-outline focus-visible:border-primary focus-visible:ring-0"
          />
          <Mail className="pointer-events-none absolute top-1/2 right-4 size-4.5 -translate-y-1/2 text-on-surface-variant transition-colors group-focus-within:text-primary" />
        </div>
        {state.fieldErrors?.email ? (
          <p className="text-sm text-error">{state.fieldErrors.email}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <label
          htmlFor="password"
          className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
        >
          Password
        </label>
        <div className="group relative">
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            placeholder="Use at least 8 characters"
            aria-invalid={Boolean(state.fieldErrors?.password)}
            className="h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 pr-12 text-sm text-on-surface shadow-none placeholder:text-outline focus-visible:border-primary focus-visible:ring-0"
          />
          <KeyRound className="pointer-events-none absolute top-1/2 right-4 size-4.5 -translate-y-1/2 text-on-surface-variant transition-colors group-focus-within:text-primary" />
        </div>
        {state.fieldErrors?.password ? (
          <p className="text-sm text-error">{state.fieldErrors.password}</p>
        ) : null}
      </div>

      {state.message ? (
        <div
          role="alert"
          className="rounded-2xl border border-error/20 bg-error-container/60 px-4 py-3 text-sm text-on-error-container"
        >
          {state.message}
        </div>
      ) : null}

      <Button
        type="submit"
        disabled={isPending}
        className="hero-gradient h-14 w-full rounded-xl text-base font-semibold text-on-primary shadow-lg shadow-primary/15 transition-transform hover:-translate-y-0.5 disabled:translate-y-0 disabled:opacity-70"
      >
        {isPending ? "Creating account..." : "Create Account"}
        <ArrowRight className="size-4.5" />
      </Button>

      <p className="text-center text-sm text-on-surface-variant">
        Already registered?{" "}
        <Link
          href="/login"
          className="font-semibold text-primary transition-colors hover:text-primary-container hover:underline"
        >
          Sign in here
        </Link>
      </p>
    </form>
  )
}
