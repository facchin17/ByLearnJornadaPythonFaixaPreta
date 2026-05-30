import { auth } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Building2, ExternalLink, Phone, Mail } from 'lucide-react'
import Link from 'next/link'
import { formatCurrency } from '@/lib/utils'

export default async function CompaniesPage() {
  const session = await auth()
  const userWithRole = session?.user as { role?: string }
  if (userWithRole?.role !== 'SUPER_ADMIN') redirect('/dashboard')

  const companies = await prisma.company.findMany({
    orderBy: { createdAt: 'desc' },
    include: { _count: { select: { leads: true, appointments: true } } },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Companies</h1>
          <p className="text-gray-500 text-sm mt-1">{companies.length} active clients</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {companies.map(company => (
          <Card key={company.id} className="hover:shadow-md transition-shadow">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{company.name}</h3>
                    <Link href={`/${company.slug}`} className="text-xs text-blue-600 hover:underline flex items-center gap-1" target="_blank">
                      /{company.slug} <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
                <Badge variant={company.isActive ? 'success' : 'secondary'}>
                  {company.isActive ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div className="space-y-1 text-sm text-gray-600 mb-3">
                <div className="flex items-center gap-2"><Phone className="h-3 w-3 text-gray-400" />{company.phone}</div>
                <div className="flex items-center gap-2"><Mail className="h-3 w-3 text-gray-400" />{company.email}</div>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-3 border-t border-gray-100 text-center">
                <div>
                  <p className="text-lg font-bold text-gray-900">{company._count.leads}</p>
                  <p className="text-xs text-gray-400">Leads</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-gray-900">{company._count.appointments}</p>
                  <p className="text-xs text-gray-400">Apts</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-gray-900">{formatCurrency(company.monthlyFee)}</p>
                  <p className="text-xs text-gray-400">/mo</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
