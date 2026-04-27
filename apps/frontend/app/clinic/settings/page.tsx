import { PasswordResetForm } from "@/components/clinic/password-reset-form"
import { requireAuthenticatedSession } from "@/lib/auth/server"

export default async function SettingsPage() {
  const session = await requireAuthenticatedSession()

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs font-semibold tracking-[0.2em] text-primary uppercase">
          Settings
        </p>
        <h1 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
          Account settings
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-on-surface-variant">
          Reset your password for the authenticated account currently signed in
          as {` ${session.user.username}`}.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-[0_20px_50px_rgba(25,28,29,0.05)] dark:shadow-none">
          <h2 className="font-headline text-xl font-semibold text-on-surface">
            Reset password
          </h2>
          <p className="mt-2 text-sm leading-6 text-on-surface-variant">
            Patients can manage their own credentials here, and the same secure
            password update flow is available to clinician and admin accounts.
          </p>
          <div className="mt-6">
            <PasswordResetForm />
          </div>
        </section>

        <section className="rounded-[28px] border border-outline-variant/10 bg-surface-container-low p-6">
          <h2 className="font-headline text-xl font-semibold text-on-surface">
            Session details
          </h2>
          <div className="mt-4 space-y-3 text-sm text-on-surface-variant">
            <p>Username: {session.user.username}</p>
            <p>Role: {session.user.role}</p>
            <p>Auth source: {session.user.auth_source}</p>
          </div>
        </section>
      </div>
    </div>
  )
}
