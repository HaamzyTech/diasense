"use client"

import { useActionState } from "react"
import { Plus, UserPlus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { createPatientAction } from "@/lib/clinic/actions"
import {
  initialCreatePatientFormState,
  type CreatePatientFieldErrors,
} from "@/lib/clinic/types"

const inputClassName =
  "h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 text-sm text-on-surface shadow-none placeholder:text-outline focus-visible:border-primary focus-visible:ring-0"

function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null
  }

  return <p className="text-sm text-error">{message}</p>
}

export function CreatePatientSheet() {
  const [state, formAction, isPending] = useActionState(
    createPatientAction,
    initialCreatePatientFormState
  )
  const fieldErrors: CreatePatientFieldErrors = state.fieldErrors ?? {}

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button className="hero-gradient h-11 text-on-primary">
          <Plus className="size-4" />
          Add patient
        </Button>
      </SheetTrigger>

      <SheetContent
        side="right"
        className="w-full max-w-xl border-outline-variant/15 bg-surface-container-lowest p-0"
      >
        <SheetHeader className="border-b border-outline-variant/10 px-6 py-6">
          <SheetTitle className="font-headline text-2xl font-semibold text-on-surface">
            Create patient account
          </SheetTitle>
          <SheetDescription className="max-w-md text-sm leading-6 text-on-surface-variant">
            Add a new patient login for the clinic workspace. Patients can sign
            in with the username or email you provide here.
          </SheetDescription>
        </SheetHeader>

        <form action={formAction} className="space-y-6 px-6 py-6">
          <div className="space-y-2">
            <label
              htmlFor="patient-username"
              className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
            >
              Username
            </label>
            <Input
              id="patient-username"
              name="username"
              type="text"
              placeholder="patient.name"
              aria-invalid={Boolean(fieldErrors.username)}
              className={inputClassName}
            />
            <p className="text-sm text-on-surface-variant">
              Optional when email is provided.
            </p>
            <FieldError message={fieldErrors.username} />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="patient-email"
              className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
            >
              Email
            </label>
            <Input
              id="patient-email"
              name="email"
              type="email"
              placeholder="patient@example.com"
              aria-invalid={Boolean(fieldErrors.email)}
              className={inputClassName}
            />
            <p className="text-sm text-on-surface-variant">
              Optional when username is provided.
            </p>
            <FieldError message={fieldErrors.email} />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="patient-password"
              className="text-xs font-bold tracking-[0.2em] text-on-surface-variant uppercase"
            >
              Temporary password
            </label>
            <Input
              id="patient-password"
              name="password"
              type="password"
              placeholder="At least 8 characters"
              aria-invalid={Boolean(fieldErrors.password)}
              className={inputClassName}
            />
            <FieldError message={fieldErrors.password} />
          </div>

          {state.message ? (
            <div
              role="alert"
              className={`rounded-xl px-4 py-3 text-sm ${
                state.success
                  ? "border border-[rgba(52,168,83,0.18)] bg-[rgba(52,168,83,0.12)] text-[rgb(22,101,52)]"
                  : "border border-error/20 bg-error-container/60 text-on-error-container"
              }`}
            >
              {state.message}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button
              type="submit"
              disabled={isPending}
              className="hero-gradient h-12 min-w-36 text-on-primary"
            >
              <UserPlus className="size-4" />
              {isPending ? "Creating..." : "Create patient"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}
