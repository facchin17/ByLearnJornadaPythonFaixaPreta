import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import RoiDashboard from '@/components/dashboard/RoiDashboard'

export default async function RoiPage() {
  const session = await auth()
  const userWithRole = session?.user as { companyId?: string }
  const companyId = userWithRole?.companyId

  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)

  const whereClause = companyId ? { companyId } : {}

  const [company, leadsThisMonth, missedCalls, appointments, jobsWon] = await Promise.all([
    companyId ? prisma.company.findUnique({ where: { id: companyId }, select: { averageTicket: true, monthlyFee: true, name: true } }) : null,
    prisma.lead.count({ where: { ...whereClause, createdAt: { gte: monthStart } } }),
    prisma.lead.count({ where: { ...whereClause, source: 'MISSED_CALL', createdAt: { gte: monthStart } } }),
    prisma.appointment.count({ where: { ...whereClause, createdAt: { gte: monthStart } } }),
    prisma.lead.count({ where: { ...whereClause, status: 'WON', updatedAt: { gte: monthStart } } }),
  ])

  const avgTicket = company?.averageTicket || 750
  const monthlyFee = company?.monthlyFee || 1000
  const estimatedRevenue = jobsWon * avgTicket
  const roi = monthlyFee > 0 ? estimatedRevenue / monthlyFee : 0

  return (
    <RoiDashboard
      companyName={company?.name || 'All Companies'}
      leadsCount={leadsThisMonth}
      missedCallsCount={missedCalls}
      appointmentsCount={appointments}
      jobsWon={jobsWon}
      estimatedRevenue={estimatedRevenue}
      monthlyFee={monthlyFee}
      roi={roi}
      avgTicket={avgTicket}
    />
  )
}
