import "server-only"

import { redirect } from "next/navigation"

import { requireAuthenticatedSession } from "@/lib/auth/server"
import type { AuthSessionResponse, AuthUser, UserRole } from "@/lib/auth/types"

export function hasRole(user: AuthUser, allowedRoles: UserRole[]): boolean {
  return allowedRoles.includes(user.role as UserRole)
}

export async function requireRoleSession(
  allowedRoles: UserRole[]
): Promise<AuthSessionResponse> {
  const session = await requireAuthenticatedSession()

  if (!hasRole(session.user, allowedRoles)) {
    redirect("/clinic")
  }

  return session
}
