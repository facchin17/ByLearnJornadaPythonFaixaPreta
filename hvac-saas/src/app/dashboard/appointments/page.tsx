import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Calendar, Clock, MapPin, Phone, User } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

export default async function AppointmentsPage() {
  const session = await auth()
  const userWithRole = session?.user as { companyId?: string }
  const companyId = userWithRole?.companyId

  const appointments = await prisma.appointment.findMany({
    where: companyId ? { companyId } : {},
    orderBy: { scheduledAt: 'asc' },
    include: { company: { select: { name: true } } },
  })

  const upcoming = appointments.filter(a => new Date(a.scheduledAt) >= new Date() && a.status !== 'CANCELLED')
  const past = appointments.filter(a => new Date(a.scheduledAt) < new Date() || a.status === 'CANCELLED')

  // Suppress unused variable warning
  void past

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
        <p className="text-gray-500 text-sm mt-1">{upcoming.length} upcoming</p>
      </div>

      <div className="space-y-4">
        {upcoming.length === 0 && (
          <Card><CardContent className="py-12 text-center text-gray-400">No upcoming appointments</CardContent></Card>
        )}
        {upcoming.map(apt => (
          <Card key={apt.id} className="overflow-hidden">
            <div className="flex">
              <div className="w-2 bg-blue-600" />
              <CardContent className="flex-1 pt-4 pb-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{apt.service}</h3>
                      <Badge variant={apt.status === 'CONFIRMED' ? 'success' : 'default'}>
                        {apt.status}
                      </Badge>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-2 text-sm text-gray-600 mt-2">
                      <div className="flex items-center gap-2"><User className="h-4 w-4 text-gray-400" />{apt.customerName}</div>
                      <div className="flex items-center gap-2"><Phone className="h-4 w-4 text-gray-400" />{apt.customerPhone}</div>
                      {apt.address && <div className="flex items-center gap-2"><MapPin className="h-4 w-4 text-gray-400" />{apt.address}</div>}
                      <div className="flex items-center gap-2"><Calendar className="h-4 w-4 text-gray-400" />{formatDateTime(apt.scheduledAt)}</div>
                      <div className="flex items-center gap-2"><Clock className="h-4 w-4 text-gray-400" />{apt.duration} min</div>
                    </div>
                    {apt.notes && <p className="text-sm text-gray-500 mt-2 italic">&ldquo;{apt.notes}&rdquo;</p>}
                  </div>
                  <div className="text-right text-sm text-gray-400">
                    <p>{apt.company.name}</p>
                  </div>
                </div>
              </CardContent>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
