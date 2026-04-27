import { HugeiconsIcon } from "@hugeicons/react"
import {
  CheckmarkCircle01Icon,
  UserIcon,
  ActivityIcon,
  LockIcon,
  TestTubeIcon,
  ShieldKeyIcon,
  AiCloud01Icon,
} from "@hugeicons/core-free-icons"
import { Button } from "@/components/ui/button"

export function SolutionsSection() {
  return (
    <section
      id="solutions"
      className="bg-surface px-6 py-24 lg:px-8 lg:py-32 dark:bg-surface-container-lowest"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="mb-16 lg:mb-20">
          <h2 className="mb-4 text-3xl font-extrabold text-on-surface lg:mb-6 lg:text-4xl">
            Dual-Spectrum Intelligence
          </h2>
          <p className="max-w-2xl text-lg text-on-surface-variant">
            Designed for the entire care continuum. Empowering patients with
            clarity and providing practitioners with actionable depth.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-12 lg:gap-8">
          {/* Patient Section - Light gray in light mode */}
          <div
            id="patients"
            className="flex flex-col justify-between rounded-3xl border border-outline-variant/10 bg-surface-container-low p-8 md:col-span-5 lg:rounded-[2rem] lg:p-10 dark:border-white/5 dark:bg-surface-container"
          >
            <div>
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 lg:mb-8 dark:bg-primary/10">
                <HugeiconsIcon
                  icon={UserIcon}
                  size={28}
                  className="text-primary"
                />
              </div>
              <h3 className="mb-4 text-2xl font-bold text-on-surface">
                For Patients
              </h3>
              <p className="mb-8 leading-relaxed text-on-surface-variant">
                A simplified, intuitive assessment tool that translates complex
                biomarkers into a personal wellness roadmap.
              </p>
              <ul className="mb-10 space-y-4">
                {[
                  "60-Second Health Snapshot",
                  "Personalized Nutrition Insights",
                  "Direct Provider Connectivity",
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-3 text-sm font-medium text-on-surface"
                  >
                    <HugeiconsIcon
                      icon={CheckmarkCircle01Icon}
                      size={20}
                      className="flex-shrink-0 text-primary"
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <Button className="h-auto w-full rounded-xl bg-primary py-4 font-bold text-on-primary transition-all hover:bg-primary/90">
              Start My Assessment
            </Button>
          </div>

          {/* Provider Section - Dark navy in light mode, dark card in dark mode */}
          <div
            id="providers"
            className="flex flex-col gap-8 rounded-3xl border border-transparent bg-inverse-surface p-8 md:col-span-7 md:flex-row lg:gap-10 lg:rounded-[2rem] lg:p-10 dark:border-white/5 dark:bg-surface-container"
          >
            <div className="flex-1">
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/10 lg:mb-8 dark:border-primary/20 dark:bg-primary/10">
                <HugeiconsIcon
                  icon={ActivityIcon}
                  size={28}
                  className="text-primary-fixed dark:text-primary"
                />
              </div>
              <h3 className="mb-4 text-2xl font-bold text-inverse-on-surface dark:text-on-surface">
                For Providers
              </h3>
              <p className="mb-8 leading-relaxed text-inverse-on-surface/70 dark:text-on-surface-variant">
                High-fidelity longitudinal risk modeling and population health
                analytics for preventative clinical intervention.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-xl border border-white/10 bg-white/5 p-4 lg:rounded-2xl lg:p-5 dark:border-white/5 dark:bg-background/50">
                  <span className="mb-1 block text-xs font-bold tracking-wider text-primary-fixed uppercase lg:mb-2 lg:text-[10px] dark:text-primary">
                    EHR integration
                  </span>
                  <span className="text-sm font-semibold text-inverse-on-surface dark:text-on-surface">
                    FHIR &amp; HL7 Standards
                  </span>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-4 lg:rounded-2xl lg:p-5 dark:border-white/5 dark:bg-background/50">
                  <span className="mb-1 block text-xs font-bold tracking-wider text-primary-fixed uppercase lg:mb-2 lg:text-[10px] dark:text-primary">
                    Decision Support
                  </span>
                  <span className="text-sm font-semibold text-inverse-on-surface dark:text-on-surface">
                    Real-time Risk Alerts
                  </span>
                </div>
              </div>
              <Button className="mt-8 h-auto rounded-xl border-0 bg-white px-8 py-3 text-sm font-bold text-inverse-surface transition-all hover:bg-white/90 lg:mt-10 lg:py-4 dark:bg-white dark:text-background dark:hover:bg-white/90">
                Request Clinical Demo
              </Button>
            </div>
            <div className="hidden w-2/5 overflow-hidden rounded-2xl border border-white/10 bg-white/5 lg:block dark:border-white/5 dark:bg-background">
              <img
                className="h-full w-full object-cover transition-all duration-700 dark:opacity-80"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuB4wcdpWxA083rfpSMvMIrHiUbSx_hzeqtJI0s03rueFwfagF1BwFC1kgoo9Lmjqmt3EZXT19G3RJoUABQ1wQbrV43sUm0zNRO3lIrwnWmwOH_mkP9fppyz_N4US5LtzO6QeW-GQTDebWy7foy6W2defW-02tM_CNJeAJTvBV2rfagYg3-jT5bj0CsyhI68iNBJMqvhe0371NAS8ucElfz42NYfy9d-uTBxwM1JNfcjqAqfcbdpyCnv4SndUmt2G-APZhdjFdOdMfI"
                alt="Medical dashboard showing risk heatmaps and metabolic data trends"
              />
            </div>
          </div>

          {/* Trust Indicators - Light blue background in light mode */}
          <div className="grid grid-cols-2 gap-4 md:col-span-12 md:grid-cols-4 lg:gap-6">
            {[
              { icon: LockIcon, label: "HIPAA Secure" },
              { icon: TestTubeIcon, label: "Peer Reviewed" },
              { icon: ShieldKeyIcon, label: "FDA Registered" },
              { icon: AiCloud01Icon, label: "SOC 2 Type II" },
            ].map(({ icon, label }) => (
              <div
                key={label}
                className="group flex flex-col items-center rounded-2xl border border-outline-variant/10 bg-secondary-container/30 p-6 text-center transition-colors hover:bg-secondary-container/50 lg:rounded-3xl lg:p-8 dark:border-white/5 dark:bg-surface-container dark:hover:bg-surface-container-high"
              >
                <HugeiconsIcon
                  icon={icon}
                  size={24}
                  className="mb-2 text-primary transition-transform group-hover:scale-110 lg:mb-3"
                />
                <span className="text-[10px] font-bold tracking-widest text-on-surface uppercase">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
