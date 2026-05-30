import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const params = new URLSearchParams(body)
    const from = params.get('From') || ''
    const messageBody = params.get('Body') || ''
    const to = params.get('To') || ''

    if (messageBody.trim().toUpperCase() === 'STOP') {
      return twimlResponse('You have been unsubscribed. Reply START to resubscribe.')
    }

    const company = await prisma.company.findFirst({ where: { twilioPhone: to } })
    if (!company) return twimlResponse('')

    // Find or create conversation
    let conversation = await prisma.conversation.findFirst({
      where: { companyId: company.id, phone: from, channel: 'SMS' },
      include: { messages: { orderBy: { createdAt: 'asc' }, take: 20 } },
    })

    if (!conversation) {
      conversation = await prisma.conversation.create({
        data: { companyId: company.id, phone: from, channel: 'SMS' },
        include: { messages: { orderBy: { createdAt: 'asc' }, take: 20 } },
      })
    }

    const history = (conversation.messages || []).map(m => ({
      role: m.role.toLowerCase() as 'user' | 'assistant',
      content: m.content,
    }))

    const systemPrompt = `You are a text-message assistant for ${company.name}, an HVAC company. A customer just texted after a missed call.

Be friendly and brief (SMS format - short messages). Your goal:
1. Apologize for missing their call
2. Ask what HVAC service they need
3. Collect: name, service needed, urgency, best callback time
4. Let them know a technician will call back shortly

Services: ${company.services.join(', ')}
Phone for emergencies: ${company.phone}

Keep responses under 160 characters when possible. Never quote prices.`

    const response = await anthropic.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 200,
      system: systemPrompt,
      messages: [...history, { role: 'user', content: messageBody }],
    })

    const reply = (response.content[0] as { type: string; text: string }).text

    await prisma.message.createMany({
      data: [
        { conversationId: conversation.id, role: 'USER', content: messageBody },
        { conversationId: conversation.id, role: 'ASSISTANT', content: reply },
      ],
    })

    const phoneClean = from.replace(/\D/g, '')
    const existingLead = await prisma.lead.findFirst({ where: { companyId: company.id, phone: phoneClean } })
    if (!existingLead) {
      const lead = await prisma.lead.create({
        data: { companyId: company.id, name: 'SMS Lead', phone: phoneClean, source: 'MISSED_CALL', estimatedValue: company.averageTicket },
      })
      await prisma.conversation.update({ where: { id: conversation.id }, data: { leadId: lead.id } })
    }

    return twimlResponse(reply)
  } catch (error) {
    console.error('SMS webhook error:', error)
    return twimlResponse("We're having issues. Please call us directly!")
  }
}

function twimlResponse(message: string) {
  const xml = `<?xml version="1.0" encoding="UTF-8"?><Response><Message>${message}</Message></Response>`
  return new NextResponse(xml, { headers: { 'Content-Type': 'text/xml' } })
}
