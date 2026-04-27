"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { deletePredictionAction } from "@/lib/clinic/actions"
import {
  initialDeletePredictionFormState,
  type DeletePredictionFormState,
} from "@/lib/clinic/types"

type DeletePredictionFormProps = {
  requestId: string
  label: string
  redirectTo?: string
  compact?: boolean
}

export function DeletePredictionForm({
  requestId,
  label,
  redirectTo,
  compact = false,
}: DeletePredictionFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(
    deletePredictionAction,
    initialDeletePredictionFormState
  )
  const feedbackState: DeletePredictionFormState = state

  useEffect(() => {
    if (feedbackState.success && redirectTo) {
      router.push(redirectTo)
      router.refresh()
    }
  }, [feedbackState.success, redirectTo, router])

  return (
    <div className="space-y-2">
      <form
        action={formAction}
        onSubmit={(event) => {
          if (
            !window.confirm(
              `Delete ${label}? This assessment result and its request record will be removed.`
            )
          ) {
            event.preventDefault()
          }
        }}
      >
        <input type="hidden" name="request_id" value={requestId} />
        <Button
          type="submit"
          disabled={isPending}
          variant="destructive"
          size={compact ? "sm" : "default"}
          className={compact ? "h-9 min-w-24" : "h-11 min-w-32"}
        >
          <Trash2 className="size-4" />
          {isPending ? "Deleting..." : "Delete result"}
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
