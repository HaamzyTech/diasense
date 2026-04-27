import { HeroSection } from "@/components/marketing/hero-section"
import { NewsletterSection } from "@/components/marketing/newsletter-section"
import { SolutionsSection } from "@/components/marketing/solutions-section"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "DiaSense",
  description:
    "An AI application that uses metrics like age, blood pressure, BMI, and glucose levels to predict diabetes risk. Both patients and healthcare professionals will be able to access this application through an easy-to-use interface.",
}

export default function Page() {
  return (
    <div>
      <HeroSection />
      <SolutionsSection />
      <NewsletterSection />
    </div>
  )
}
