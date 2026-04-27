import { BackendFeatureNotice } from "@/components/clinic/backend-feature-notice"
import { DataTableCard } from "@/components/clinic/data-table-card"
import { UserRoleForm } from "@/components/clinic/user-role-form"
import { requireRoleSession } from "@/lib/auth/guards"
import { getClinicFeatureErrorMessage } from "@/lib/clinic/errors"
import {
  formatCalendarDateTime,
  getAccountReference,
  getAccountSecondaryLabel,
} from "@/lib/clinic/presentation"
import { fetchUsers } from "@/lib/clinic/server"
import type { ManagedUser } from "@/lib/clinic/types"

function toUserId(value: string): string {
  return `#US-${value.replace(/-/g, "").slice(0, 4).toUpperCase()}`
}

export default async function UsersPage() {
  await requireRoleSession(["admin"])
  let users: ManagedUser[] = []
  let loadMessage: string | null = null

  try {
    users = await fetchUsers()
  } catch (error) {
    loadMessage = getClinicFeatureErrorMessage(error, "user management")
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Users
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          User management
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          Review registered accounts, keep role assignments current, and remove
          stale users from the protected clinic workspace.
        </p>
      </div>

      {loadMessage ? (
        <BackendFeatureNotice
          title="User management is temporarily unavailable"
          message={loadMessage}
          actionHref="/clinic/dashboard"
          actionLabel="Back to dashboard"
        />
      ) : null}

      <DataTableCard
        title="Registered Users"
        subtitle={`${users.length} authenticated account${users.length === 1 ? "" : "s"} currently available.`}
        footer={
          loadMessage
            ? "Registered users could not be loaded from the backend right now."
            : `Showing ${users.length} registered user${users.length === 1 ? "" : "s"}`
        }
      >
        {users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1040px]">
              <thead>
                <tr className="border-b border-outline-variant/10">
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    User ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Account
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Role
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Created
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold tracking-[0.18em] text-on-surface-variant uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="align-top transition-colors hover:bg-surface-container-low/60"
                  >
                    <td className="px-6 py-5 text-lg text-on-surface-variant">
                      {toUserId(user.id)}
                    </td>
                    <td className="px-6 py-5">
                      <div className="space-y-1">
                        <p className="text-lg font-semibold text-on-surface">
                          {getAccountReference(user)}
                        </p>
                        <p className="text-sm text-on-surface-variant">
                          {getAccountSecondaryLabel(user)}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-5 text-base font-medium text-on-surface capitalize">
                      {user.role}
                    </td>
                    <td className="px-6 py-5 text-sm text-on-surface-variant">
                      {formatCalendarDateTime(user.created_at)}
                    </td>
                    <td className="px-6 py-5">
                      <UserRoleForm
                        userId={user.id}
                        initialRole={user.role}
                        userLabel={getAccountReference(user)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center text-sm text-on-surface-variant">
            {loadMessage
              ? "Registered users could not be loaded from the backend right now."
              : "No registered users are available yet."}
          </div>
        )}
      </DataTableCard>
    </div>
  )
}
