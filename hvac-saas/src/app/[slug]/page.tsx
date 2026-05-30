import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import LandingHero from '@/components/landing/LandingHero'
import LeadForm from '@/components/landing/LeadForm'
import ChatWidget from '@/components/chat/ChatWidget'
import LandingServices from '@/components/landing/LandingServices'
import LandingFooter from '@/components/landing/LandingFooter'

type Props = { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const company = await prisma.company.findUnique({ where: { slug } })
  if (!company) return { title: 'HVAC Service' }
  return {
    title: `${company.name} | Professional HVAC Services`,
    description: `Expert AC repair, furnace repair, and HVAC installation. Serving ${company.serviceArea.join(', ')}. Call ${company.phone} for emergency service.`,
    keywords: 'AC repair, furnace repair, HVAC installation, emergency HVAC, air conditioning, heating',
  }
}

export default async function CompanyLandingPage({ params }: Props) {
  const { slug } = await params
  const company = await prisma.company.findUnique({ where: { slug } })
  if (!company || !company.isActive) notFound()

  return (
    <main className="min-h-screen bg-white">
      <LandingHero company={company} />
      <LandingServices company={company} />
      <section id="contact" className="py-16 bg-gray-50">
        <div className="max-w-2xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            Request Service
          </h2>
          <p className="text-center text-gray-500 mb-8">
            Fill out the form and we&apos;ll get back to you within minutes.
          </p>
          <LeadForm companyId={company.id} companySlug={company.slug} services={company.services} />
        </div>
      </section>
      <LandingFooter company={company} />
      <ChatWidget companyId={company.id} companyName={company.name} />
    </main>
  )
}
