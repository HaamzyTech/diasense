"use client"

import { useActionState } from "react"
import { Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { deletePatientAction } from "@/lib/clinic/actions"
import {
  initialDeletePatientFormState,
  type DeletePatientFormState,
} from "@/lib/clinic/types"

type DeletePatientFormProps = {
  patientId: string
  patientLabel: string
}

export function DeletePatientForm({
  patientId,
  patientLabel,
}: DeletePatientFormProps) {
  const [state, formAction, isPending] = useActionState(
    deletePatientAction,
    initialDeletePatientFormState
  )
  const feedbackState: DeletePatientFormState = state

  return (
    <div className="space-y-2">
      <form
        action={formAction}
        onSubmit={(event) => {
          if (
            !window.confirm(
              `Delete ${patientLabel}? This patient account will lose access to the clinic workspace.`
            )
          ) {
            event.preventDefault()
          }
        }}
      >
        <input type="hidden" name="patient_id" value={patientId} />
        <Button
          type="submit"
          disabled={isPending}
          variant="destructive"
          size="sm"
          className="h-9 min-w-24"
        >
          <Trash2 className="size-4" />
          {isPending ? "Deleting..." : "Delete"}
        </Button>
      </form>

      {feedbackState.message ? (
        <p
          className={`text-sm ${
            feedbackState.success ? "text-primary" : "text-error"
          }`}
        >
          {feedbackState.message}
        </p>
      ) : null}
    </div>
  )
}
