import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'

const schema = z.object({
  companyId: z.string(),
  leadId: z.string().optional(),
  customerName: z.string().min(1),
  customerPhone: z.string().min(7),
  customerEmail: z.string().email().optional().or(z.literal('')),
  service: z.string().min(1),
  address: z.string().optional(),
  scheduledAt: z.string(),
  notes: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const data = schema.parse(body)

    const appointment = await prisma.appointment.create({
      data: {
        companyId: data.companyId,
        leadId: data.leadId || null,
        customerName: data.customerName,
        customerPhone: data.customerPhone,
        customerEmail: data.customerEmail || null,
        service: data.service,
        address: data.address || null,
        scheduledAt: new Date(data.scheduledAt),
        notes: data.notes || null,
      },
    })

    if (data.leadId) {
      await prisma.lead.update({
        where: { id: data.leadId },
        data: { status: 'BOOKED' },
      })
    }

    return NextResponse.json({ success: true, appointmentId: appointment.id }, { status: 201 })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.issues }, { status: 400 })
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get('companyId')
  if (!companyId) return NextResponse.json({ error: 'companyId required' }, { status: 400 })

  const appointments = await prisma.appointment.findMany({
    where: { companyId },
    orderBy: { scheduledAt: 'asc' },
    include: { lead: { select: { name: true, phone: true } } },
  })
  return NextResponse.json(appointments)
}
