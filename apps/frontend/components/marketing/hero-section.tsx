import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon } from "@hugeicons/core-free-icons"
import { Button } from "@/components/ui/button"

export function HeroSection() {
  return (
    <section className="relative flex min-h-[800px] items-center overflow-hidden bg-surface-container-lowest px-6 py-16 lg:min-h-[870px] lg:px-8 lg:py-20 dark:bg-background">
      <div className="mx-auto grid w-full max-w-7xl grid-cols-1 items-center gap-12 lg:grid-cols-12 lg:gap-16">
        {/* Left Content */}
        <div className="space-y-8 lg:col-span-7">
          <div className="inline-flex items-center gap-2 rounded-full border border-transparent bg-secondary-container px-4 py-1.5 text-xs font-bold tracking-wider text-on-secondary-container uppercase dark:border-primary/20 dark:bg-primary/10 dark:text-primary">
            <HugeiconsIcon icon={CheckmarkCircle01Icon} size={14} />
            Clinically Validated Precision
          </div>

          <h1 className="text-4xl leading-[1.1] font-extrabold tracking-tight text-balance text-on-surface sm:text-5xl lg:text-7xl">
            AI-Powered Precision for{" "}
            <span className="text-primary">Diabetes Risk</span> Management.
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-on-surface-variant">
            DiaSense integrates deep longitudinal data with proprietary risk
            modeling to predict metabolic shifts before they become chronic
            conditions.
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <Button className="hero-gradient h-auto rounded-xl px-8 py-4 text-lg font-bold text-white shadow-lg transition-all hover:shadow-xl active:scale-95">
              Get Early Access
            </Button>
            <Button
              variant="secondary"
              className="h-auto rounded-xl border-0 bg-surface-container-highest px-8 py-4 text-lg font-bold text-on-surface transition-all hover:bg-surface-dim active:scale-95 dark:bg-surface-container-highest dark:hover:bg-surface-bright"
            >
              View Methodology
            </Button>
          </div>

          <div className="flex items-center gap-8 pt-6 lg:gap-12">
            <div className="flex flex-col">
              <span className="text-2xl font-extrabold text-primary lg:text-3xl">
                99.4%
              </span>
              <span className="mt-1 text-[10px] font-semibold tracking-widest text-on-surface-variant uppercase">
                Model Accuracy
              </span>
            </div>
            <div className="h-10 w-px bg-outline-variant/30 lg:h-12 dark:bg-outline/20"></div>
            <div className="flex flex-col">
              <span className="text-2xl font-extrabold text-on-surface lg:text-3xl">
                HIPAA
              </span>
              <span className="mt-1 text-[10px] font-semibold tracking-widest text-on-surface-variant uppercase">
                Security Compliant
              </span>
            </div>
          </div>
        </div>

        {/* Right Content - Hero Image */}
        <div className="relative lg:col-span-5">
          <div className="relative z-10 aspect-square overflow-hidden rounded-3xl border border-transparent shadow-2xl lg:rounded-[2rem] dark:border-white/10">
            <img
              className="h-full w-full object-cover dark:opacity-90 dark:contrast-125"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4M5Pmu5hXJkinSvxJM5WhfgBKEeGCqVfaWem3vYthqr1PcHHy22_P-R9zquw2jh-WK7Wm6Aeicf4exeV3cXUVCa8-lMH8iQgfDWnc9l7p1ndQFtem3fEjCyBtxPt_jTXKTbk9_P0_xixUmBNHoRFWALaCY2gYah55QIfI_8wlSQ76YkqJ3hL91IJxJn6eSwwLAEmODOO9-_jwilQugf8jxo6NFSkKiDAuoCUjWUF1ag2iE-HfGDX5lNLyPyFl40uzuLJV-h6jUjk"
              alt="High-tech digital medical interface showing glowing blue neural network data visualizations and patient health trends"
            />
          </div>

          {/* Floating Glass Panel */}
          <div className="glass-panel absolute -bottom-6 -left-6 z-20 max-w-[240px] rounded-2xl p-5 shadow-xl lg:-bottom-8 lg:-left-8 lg:max-w-[280px] lg:p-6">
            <div className="mb-2 flex items-center gap-3 lg:mb-3">
              <div className="h-2 w-2 animate-pulse rounded-full bg-tertiary lg:h-2.5 lg:w-2.5"></div>
              <span className="text-[10px] font-bold tracking-widest text-tertiary uppercase dark:text-tertiary">
                Live Risk Alert
              </span>
            </div>
            <p className="text-sm leading-tight font-semibold text-on-surface">
              Patient ID: VC-8829 showing early glycemic instability.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
