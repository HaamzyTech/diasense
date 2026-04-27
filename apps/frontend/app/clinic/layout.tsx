import { ClinicShell } from "@/components/clinic/clinic-shell"
import { requireAuthenticatedSession } from "@/lib/auth/server"

export default async function ClinicLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await requireAuthenticatedSession()

  return <ClinicShell user={session.user}>{children}</ClinicShell>
}
