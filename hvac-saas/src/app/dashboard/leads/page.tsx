import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import LeadsTable from '@/components/dashboard/LeadsTable'

export default async function LeadsPage() {
  const session = await auth()
  const userWithRole = session?.user as { companyId?: string }
  const companyId = userWithRole?.companyId

  const leads = await prisma.lead.findMany({
    where: companyId ? { companyId } : {},
    orderBy: { createdAt: 'desc' },
    take: 200,
    include: { company: { select: { name: true, slug: true } } },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        <p className="text-gray-500 text-sm mt-1">{leads.length} total leads</p>
      </div>
      <LeadsTable initialLeads={leads} />
    </div>
  )
}
