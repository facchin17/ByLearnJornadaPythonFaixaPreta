import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'

const schema = z.object({
  companyId: z.string(),
  name: z.string().min(1),
  phone: z.string().min(7),
  email: z.string().email().optional().or(z.literal('')),
  service: z.string().optional(),
  urgency: z.enum(['EMERGENCY', 'HIGH', 'NORMAL', 'LOW']).default('NORMAL'),
  city: z.string().optional(),
  notes: z.string().optional(),
  source: z.enum(['WEBSITE', 'CHATBOT', 'MISSED_CALL', 'MANUAL']).default('WEBSITE'),
})

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const data = schema.parse(body)

    const company = await prisma.company.findUnique({ where: { id: data.companyId } })
    if (!company) return NextResponse.json({ error: 'Company not found' }, { status: 404 })

    const lead = await prisma.lead.create({
      data: {
        companyId: data.companyId,
        name: data.name,
        phone: data.phone,
        email: data.email || null,
        service: data.service || null,
        urgency: data.urgency,
        city: data.city || null,
        notes: data.notes || null,
        source: data.source,
        estimatedValue: company.averageTicket,
      },
    })

    return NextResponse.json({ success: true, leadId: lead.id }, { status: 201 })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.issues }, { status: 400 })
    }
    console.error('Lead creation error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get('companyId')
  if (!companyId) return NextResponse.json({ error: 'companyId required' }, { status: 400 })

  const leads = await prisma.lead.findMany({
    where: { companyId },
    orderBy: { createdAt: 'desc' },
    take: 100,
  })
  return NextResponse.json(leads)
}
