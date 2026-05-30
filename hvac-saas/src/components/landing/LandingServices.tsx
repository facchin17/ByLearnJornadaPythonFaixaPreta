import { Thermometer, Wind, Wrench, Home, Zap, Droplets } from 'lucide-react'

const SERVICE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'AC Repair': Wind,
  'Furnace Repair': Thermometer,
  'HVAC Installation': Home,
  'Emergency Service': Zap,
  'Maintenance': Wrench,
  'Indoor Air Quality': Droplets,
}

export default function LandingServices({ company }: { company: { services: string[] } }) {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">Our Services</h2>
        <p className="text-center text-gray-500 mb-10">Expert solutions for all your HVAC needs</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {company.services.map((service) => {
            const Icon = SERVICE_ICONS[service] || Wrench
            return (
              <div key={service} className="group border border-gray-200 rounded-xl p-6 hover:border-blue-300 hover:shadow-md transition-all">
                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-100 transition-colors">
                  <Icon className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{service}</h3>
                <p className="text-sm text-gray-500">
                  Professional {service.toLowerCase()} service by certified technicians. Fast response, guaranteed work.
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
