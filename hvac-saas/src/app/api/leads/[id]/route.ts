import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const body = await request.json()

  const lead = await prisma.lead.update({
    where: { id },
    data: body,
  })
  return NextResponse.json(lead)
}
