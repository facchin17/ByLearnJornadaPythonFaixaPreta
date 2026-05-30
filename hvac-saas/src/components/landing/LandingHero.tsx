import { Phone, Clock, Shield, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Company = {
  name: string
  phone: string
  services: string[]
  serviceArea: string[]
}

export default function LandingHero({ company }: { company: Company }) {
  return (
    <section className="relative bg-gradient-to-br from-blue-900 via-blue-800 to-blue-700 text-white overflow-hidden">
      <div className="absolute inset-0 bg-black/20" />
      <div className="relative max-w-6xl mx-auto px-4 py-20 md:py-28">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Star className="h-5 w-5 text-yellow-400 fill-yellow-400" />
              <span className="text-yellow-400 font-medium">Trusted Local HVAC Experts</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-4">
              {company.name}
            </h1>
            <p className="text-xl text-blue-100 mb-6">
              Professional HVAC services in {company.serviceArea.slice(0, 3).join(', ')}.
              Fast, reliable, and affordable.
            </p>
            <div className="flex flex-wrap gap-3 mb-8">
              {company.services.slice(0, 4).map((service) => (
                <span key={service} className="bg-blue-600/50 border border-blue-400/30 rounded-full px-4 py-1.5 text-sm font-medium">
                  {service}
                </span>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <a href={`tel:${company.phone}`}>
                <Button size="xl" variant="orange" className="w-full sm:w-auto">
                  <Phone className="h-5 w-5" />
                  Call Now: {company.phone}
                </Button>
              </a>
              <a href="#contact">
                <Button size="xl" variant="outline" className="w-full sm:w-auto text-white border-white hover:bg-white hover:text-blue-900">
                  Book Service Online
                </Button>
              </a>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              { icon: Clock, title: '24/7 Emergency', desc: 'Available around the clock' },
              { icon: Shield, title: 'Licensed & Insured', desc: 'Certified technicians' },
              { icon: Star, title: '5-Star Rated', desc: 'Hundreds of happy customers' },
              { icon: Phone, title: 'Same-Day Service', desc: 'Fast response times' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-white/10 backdrop-blur rounded-xl p-5 border border-white/20">
                <Icon className="h-8 w-8 text-orange-400 mb-3" />
                <h3 className="font-semibold text-white">{title}</h3>
                <p className="text-sm text-blue-200 mt-1">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
