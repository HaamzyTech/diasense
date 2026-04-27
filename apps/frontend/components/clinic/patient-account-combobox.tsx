"use client"

import { useDeferredValue, useEffect, useId, useRef, useState } from "react"
import { Check, ChevronDown, Search } from "lucide-react"

import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

type PatientAccountOption = {
  value: string
  label: string
  description?: string
}

type PatientAccountComboboxProps = {
  id?: string
  name: string
  defaultValue?: string
  error?: string
  placeholder?: string
  options: PatientAccountOption[]
}

export function PatientAccountCombobox({
  id,
  name,
  defaultValue,
  error,
  placeholder = "Search by email or username",
  options,
}: PatientAccountComboboxProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const rootRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState(() => defaultValue ?? "")
  const deferredQuery = useDeferredValue(query)

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener("pointerdown", handlePointerDown)
    return () => document.removeEventListener("pointerdown", handlePointerDown)
  }, [])

  const normalizedQuery = deferredQuery.trim().toLowerCase()
  const filteredOptions = options
    .filter((option) => {
      if (!normalizedQuery) {
        return true
      }

      return [option.value, option.label, option.description ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery)
    })
    .slice(0, 8)

  return (
    <div ref={rootRef} className="relative">
      <Input
        id={inputId}
        type="text"
        value={query}
        autoComplete="off"
        aria-invalid={Boolean(error)}
        aria-expanded={open}
        aria-controls={`${inputId}-results`}
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value)
          setOpen(true)
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            setOpen(false)
          }
        }}
        className="h-14 rounded-none border-0 border-b-2 border-outline-variant bg-surface-container-highest/40 px-2 pr-12 text-sm text-on-surface shadow-none placeholder:text-outline focus-visible:border-primary focus-visible:ring-0"
      />
      <input type="hidden" name={name} value={query.trim()} />

      <div className="pointer-events-none absolute top-1/2 right-3 flex -translate-y-1/2 items-center gap-2 text-on-surface-variant">
        <Search className="size-4" />
        <ChevronDown className="size-4" />
      </div>

      {open ? (
        <div
          id={`${inputId}-results`}
          className="absolute z-30 mt-3 w-full overflow-hidden border border-outline-variant/15 bg-surface-container-lowest shadow-[0_18px_40px_rgba(25,28,29,0.08)]"
        >
          {filteredOptions.length > 0 ? (
            <div className="max-h-72 overflow-y-auto">
              {filteredOptions.map((option) => {
                const isSelected =
                  query.trim().toLowerCase() === option.value.toLowerCase()

                return (
                  <button
                    key={option.value}
                    type="button"
                    className="flex w-full items-start justify-between gap-4 border-b border-outline-variant/10 px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-surface-container-low"
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => {
                      setQuery(option.value)
                      setOpen(false)
                    }}
                  >
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-on-surface">
                        {option.label}
                      </p>
                      {option.description ? (
                        <p className="text-xs text-on-surface-variant">
                          {option.description}
                        </p>
                      ) : null}
                    </div>
                    <Check
                      className={cn(
                        "mt-0.5 size-4 shrink-0 text-primary transition-opacity",
                        isSelected ? "opacity-100" : "opacity-0"
                      )}
                    />
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="px-4 py-4 text-sm text-on-surface-variant">
              No accounts matched your search.
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
