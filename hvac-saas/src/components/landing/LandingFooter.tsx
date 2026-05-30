import { Phone, Mail, MapPin } from 'lucide-react'

type Company = {
  name: string
  phone: string
  email: string
  serviceArea: string[]
  website?: string | null
}

export default function LandingFooter({ company }: { company: Company }) {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="max-w-6xl mx-auto px-4">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-lg mb-4">{company.name}</h3>
            <p className="text-gray-400 text-sm">Professional HVAC services you can trust. Licensed, insured, and dedicated to your comfort.</p>
          </div>
          <div>
            <h3 className="font-bold mb-4">Contact Us</h3>
            <div className="space-y-2 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-orange-400" />
                <a href={`tel:${company.phone}`} className="hover:text-white">{company.phone}</a>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-orange-400" />
                <a href={`mailto:${company.email}`} className="hover:text-white">{company.email}</a>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-orange-400" />
                <span>{company.serviceArea.slice(0, 3).join(', ')}</span>
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-bold mb-4">Service Areas</h3>
            <div className="flex flex-wrap gap-2">
              {company.serviceArea.map((area) => (
                <span key={area} className="text-xs bg-gray-800 rounded-full px-3 py-1 text-gray-300">
                  {area}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="border-t border-gray-800 pt-6 text-center text-sm text-gray-500">
          &copy; {new Date().getFullYear()} {company.name}. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
