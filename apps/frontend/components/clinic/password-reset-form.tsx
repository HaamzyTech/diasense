"use client"

import { useActionState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { resetPasswordAction } from "@/lib/clinic/actions"
import { initialPasswordResetFormState } from "@/lib/clinic/types"

const passwordInputClassName =
  "h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 text-sm text-on-surface shadow-none focus-visible:border-primary focus-visible:ring-0"

function PasswordField({
  id,
  label,
  error,
}: {
  id: "current_password" | "new_password" | "confirm_password"
  label: string
  error?: string
}) {
  return (
    <div className="space-y-2">
      <label
        htmlFor={id}
        className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
      >
        {label}
      </label>
      <Input
        id={id}
        name={id}
        type="password"
        aria-invalid={Boolean(error)}
        className={passwordInputClassName}
      />
      {error ? <p className="text-sm text-error">{error}</p> : null}
    </div>
  )
}

export function PasswordResetForm() {
  const [state, formAction, isPending] = useActionState(
    resetPasswordAction,
    initialPasswordResetFormState
  )

  return (
    <form action={formAction} className="space-y-5">
      <PasswordField
        id="current_password"
        label="Current password"
        error={state.fieldErrors?.current_password}
      />
      <PasswordField
        id="new_password"
        label="New password"
        error={state.fieldErrors?.new_password}
      />
      <PasswordField
        id="confirm_password"
        label="Confirm new password"
        error={state.fieldErrors?.confirm_password}
      />

      {state.message ? (
        <div
          role="alert"
          className={`border px-4 py-3 text-sm ${
            state.success
              ? "border-primary/15 bg-primary/10 text-on-surface"
              : "border-error/20 bg-error-container/60 text-on-error-container"
          }`}
        >
          {state.message}
        </div>
      ) : null}

      <Button
        type="submit"
        disabled={isPending}
        className="hero-gradient h-12 rounded-xl text-on-primary"
      >
        {isPending ? "Updating password..." : "Update password"}
      </Button>
    </form>
  )
}
