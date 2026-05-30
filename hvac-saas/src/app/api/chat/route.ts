import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { prisma } from '@/lib/prisma'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

export async function POST(request: NextRequest) {
  try {
    const { message, companyId, conversationId, history } = await request.json()

    const company = await prisma.company.findUnique({ where: { id: companyId } })
    if (!company) return NextResponse.json({ error: 'Company not found' }, { status: 404 })

    const systemPrompt = `You are a friendly and professional customer service assistant for ${company.name}, an HVAC company serving ${company.serviceArea.join(', ')}.

Your goal is to qualify leads by collecting:
1. Customer's name
2. Phone number
3. Email (optional)
4. Type of HVAC problem or service needed
5. Urgency level (emergency, today, this week, or flexible)
6. City/neighborhood

Services we offer: ${company.services.join(', ')}

RULES:
- Be warm, professional, and helpful
- Never quote specific prices - say "our technician will provide a free estimate"
- If emergency (no AC/heat, gas smell, fire), always recommend calling immediately: ${company.phone}
- After collecting info, tell them someone will call within 15 minutes during business hours
- Keep responses concise (2-3 sentences max)
- If customer wants to book, collect their availability (date/time preference)
- NEVER make up information about the company`

    const messages = [
      ...(history || []).map((m: { role: string; content: string }) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
      { role: 'user' as const, content: message },
    ]

    const response = await anthropic.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 400,
      system: systemPrompt,
      messages,
    })

    const reply = (response.content[0] as { type: string; text: string }).text

    // Upsert conversation
    let convId = conversationId
    if (!convId) {
      const conv = await prisma.conversation.create({
        data: { companyId, channel: 'CHAT' },
      })
      convId = conv.id
    }

    // Save messages
    await prisma.message.createMany({
      data: [
        { conversationId: convId, role: 'USER', content: message },
        { conversationId: convId, role: 'ASSISTANT', content: reply },
      ],
    })

    // Try to extract lead data from conversation
    await tryExtractLead(companyId, convId, [...(history || []), { role: 'user', content: message }, { role: 'assistant', content: reply }], company.averageTicket)

    return NextResponse.json({ reply, conversationId: convId })
  } catch (error) {
    console.error('Chat error:', error)
    return NextResponse.json({ reply: "I'm sorry, I'm having trouble right now. Please call us directly!" })
  }
}

async function tryExtractLead(companyId: string, conversationId: string, history: { role: string; content: string }[], avgTicket: number) {
  const fullText = history.map((m) => `${m.role}: ${m.content}`).join('\n')

  const phoneMatch = fullText.match(/(\+?1?\s?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})/)
  const nameMatch = fullText.match(/(?:i['']?m|my name is|name['']?s?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i)

  if (!phoneMatch) return

  const phone = phoneMatch[0].replace(/\D/g, '')
  const name = nameMatch ? nameMatch[1] : 'Chat Lead'

  const conv = await prisma.conversation.findUnique({ where: { id: conversationId } })
  if (conv?.leadId) return // already linked

  const existing = await prisma.lead.findFirst({ where: { companyId, phone } })
  if (existing) {
    await prisma.conversation.update({ where: { id: conversationId }, data: { leadId: existing.id } })
    return
  }

  const lead = await prisma.lead.create({
    data: {
      companyId,
      name,
      phone,
      source: 'CHATBOT',
      estimatedValue: avgTicket,
    },
  })
  await prisma.conversation.update({ where: { id: conversationId }, data: { leadId: lead.id } })
}
