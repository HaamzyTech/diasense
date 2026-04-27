"use client"

import * as React from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Moon02Icon, Sun03Icon } from "@hugeicons/core-free-icons"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  const { setTheme, resolvedTheme } = useTheme()
  const mounted = React.useSyncExternalStore(
    () => () => undefined,
    () => true,
    () => false
  )

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="text-on-surface-variant">
        <HugeiconsIcon icon={Sun03Icon} size={20} />
        <span className="sr-only">Toggle theme</span>
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className="text-on-surface-variant hover:text-primary"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      {resolvedTheme === "dark" ? (
        <HugeiconsIcon icon={Sun03Icon} size={20} />
      ) : (
        <HugeiconsIcon icon={Moon02Icon} size={20} />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
