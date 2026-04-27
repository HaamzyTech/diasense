"use client"

import { useActionState, useState } from "react"
import { Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { deleteUserAction, updateUserRoleAction } from "@/lib/clinic/actions"
import {
  initialDeleteUserFormState,
  initialUserRoleFormState,
  type DeleteUserFormState,
  type ManagedUser,
} from "@/lib/clinic/types"

type UserRoleFormProps = {
  userId: string
  initialRole: ManagedUser["role"]
  userLabel: string
}

export function UserRoleForm({
  userId,
  initialRole,
  userLabel,
}: UserRoleFormProps) {
  const [role, setRole] = useState<ManagedUser["role"]>(initialRole)
  const [state, formAction, isPending] = useActionState(
    updateUserRoleAction,
    initialUserRoleFormState
  )
  const [deleteState, deleteAction, isDeleting] = useActionState(
    deleteUserAction,
    initialDeleteUserFormState
  )
  const feedbackState: DeleteUserFormState | typeof state = deleteState.message
    ? deleteState
    : state

  return (
    <div className="space-y-2">
      <div className="flex flex-col gap-2 xl:flex-row">
        <form
          action={formAction}
          className="flex flex-1 flex-col gap-2 sm:flex-row"
        >
          <input type="hidden" name="user_id" value={userId} />
          <input type="hidden" name="role" value={role} />

          <Select
            value={role}
            onValueChange={(value) => setRole(value as ManagedUser["role"])}
          >
            <SelectTrigger className="h-11 w-full border-outline-variant/20 bg-surface-container-low sm:w-44">
              <SelectValue placeholder="Choose role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="patient">Patient</SelectItem>
              <SelectItem value="clinician">Clinician</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>

          <Button
            type="submit"
            disabled={isPending}
            className="hero-gradient h-11 min-w-28 text-on-primary"
          >
            {isPending ? "Saving..." : "Save role"}
          </Button>
        </form>

        <form
          action={deleteAction}
          onSubmit={(event) => {
            if (
              !window.confirm(
                `Delete ${userLabel}? This action cannot be undone.`
              )
            ) {
              event.preventDefault()
            }
          }}
        >
          <input type="hidden" name="user_id" value={userId} />
          <Button
            type="submit"
            disabled={isDeleting}
            variant="destructive"
            className="h-11 min-w-28"
          >
            <Trash2 className="size-4" />
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </form>
      </div>

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
