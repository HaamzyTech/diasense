import { HugeiconsIcon } from "@hugeicons/react"
import { LockKeyIcon, ShieldKeyIcon } from "@hugeicons/core-free-icons"

import { LoginForm } from "@/components/auth/login-form"
import { redirectIfAuthenticated } from "@/lib/auth/server"

export default async function LoginPage() {
  await redirectIfAuthenticated()

  return (
    <div className="w-full max-w-[480px] space-y-8">
      <div className="space-y-2 text-center md:text-left">
        <h1 className="font-headline text-4xl leading-tight font-extrabold tracking-tight text-on-surface">
          Secure Access
        </h1>
        <p className="max-w-sm text-base font-medium text-on-surface-variant">
          Welcome back to DiaSense. Sign in to continue into the protected
          clinic workspace.
        </p>
      </div>

      <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8 shadow-[0_20px_40px_rgba(25,28,29,0.05)] md:p-10 dark:shadow-none">
        <div className="space-y-6">
          <div className="space-y-1">
            <h2 className="font-headline text-3xl font-bold tracking-tight text-on-surface">
              Sign in
            </h2>
            <p className="text-sm text-on-surface-variant">
              Use your username or email and password to continue.
            </p>
          </div>
          <LoginForm />
        </div>
      </div>

      <div className="flex items-center justify-center gap-6 text-on-surface-variant/40">
        <div className="flex items-center gap-1.5">
          <HugeiconsIcon icon={ShieldKeyIcon} size={18} />
          <span className="text-[10px] font-bold tracking-widest uppercase">
            HIPAA COMPLIANT
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <HugeiconsIcon icon={LockKeyIcon} size={18} />
          <span className="text-[10px] font-bold tracking-widest uppercase">
            AES-256 ENCRYPTION
          </span>
        </div>
      </div>
    </div>
  )
}
