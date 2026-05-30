import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { auth } from '@/lib/auth'

export async function GET() {
  const session = await auth()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const companies = await prisma.company.findMany({
    orderBy: { createdAt: 'desc' },
    select: { id: true, name: true, slug: true, phone: true, email: true, isActive: true, createdAt: true, averageTicket: true, monthlyFee: true },
  })
  return NextResponse.json(companies)
}

export async function POST(request: NextRequest) {
  const session = await auth()
  if (!session || (session.user as { role?: string }).role !== 'SUPER_ADMIN') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = await request.json()
    const company = await prisma.company.create({ data: body })
    return NextResponse.json(company, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Failed to create company' }, { status: 500 })
  }
}
