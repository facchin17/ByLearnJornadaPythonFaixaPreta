import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, Calendar, TrendingUp, Phone, ArrowUpRight } from 'lucide-react'
import { formatCurrency, formatDateTime } from '@/lib/utils'
import Link from 'next/link'

export default async function DashboardPage() {
  const session = await auth()
  const userWithRole = session?.user as { companyId?: string }
  const companyId = userWithRole?.companyId

  const whereClause = companyId ? { companyId } : {}
  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)

  const [totalLeads, newLeadsThisMonth, appointments, wonLeads, missedCalls, recentLeads] = await Promise.all([
    prisma.lead.count({ where: whereClause }),
    prisma.lead.count({ where: { ...whereClause, createdAt: { gte: monthStart } } }),
    prisma.appointment.count({ where: { ...whereClause, status: { in: ['PENDING', 'CONFIRMED'] } } }),
    prisma.lead.count({ where: { ...whereClause, status: 'WON', updatedAt: { gte: monthStart } } }),
    prisma.lead.count({ where: { ...whereClause, source: 'MISSED_CALL', createdAt: { gte: monthStart } } }),
    prisma.lead.findMany({
      where: whereClause,
      orderBy: { createdAt: 'desc' },
      take: 5,
      include: { company: { select: { name: true } } },
    }),
  ])

  const stats = [
    { label: 'Total Leads', value: totalLeads, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'New This Month', value: newLeadsThisMonth, icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Upcoming Jobs', value: appointments, icon: Calendar, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Missed Calls Recovered', value: missedCalls, icon: Phone, color: 'text-orange-600', bg: 'bg-orange-50' },
  ]

  // Suppress unused variable warning
  void wonLeads

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Welcome back. Here&apos;s what&apos;s happening.</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color, bg }) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">{label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
                </div>
                <div className={`w-12 h-12 ${bg} rounded-xl flex items-center justify-center`}>
                  <Icon className={`h-6 w-6 ${color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Leads</CardTitle>
          <Link href="/dashboard/leads" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
            View all <ArrowUpRight className="h-3 w-3" />
          </Link>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentLeads.map(lead => (
              <div key={lead.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <p className="font-medium text-gray-900 text-sm">{lead.name}</p>
                  <p className="text-xs text-gray-500">{lead.phone} &middot; {lead.service || 'General inquiry'} &middot; {lead.city || 'N/A'}</p>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    lead.status === 'NEW' ? 'bg-blue-100 text-blue-700' :
                    lead.status === 'WON' ? 'bg-green-100 text-green-700' :
                    lead.status === 'LOST' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>{lead.status}</span>
                  <p className="text-xs text-gray-400 mt-1">{formatDateTime(lead.createdAt)}</p>
                </div>
              </div>
            ))}
            {recentLeads.length === 0 && (
              <p className="text-center text-gray-400 text-sm py-4">No leads yet. Share your landing page to get started!</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
