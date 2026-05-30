'use client'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CheckCircle, Loader2 } from 'lucide-react'

type Props = {
  companyId: string
  companySlug: string
  services: string[]
}

export default function LeadForm({ companyId, companySlug, services }: Props) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [form, setForm] = useState({
    name: '', phone: '', email: '', service: '', urgency: 'NORMAL', city: '', notes: '',
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')
    try {
      const res = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, companyId, source: 'WEBSITE' }),
      })
      if (!res.ok) throw new Error()
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'success') {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-green-800 mb-2">Request Received!</h3>
        <p className="text-green-600">We&apos;ll contact you within 15 minutes. Check your phone!</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor="name">Full Name *</Label>
          <Input id="name" required placeholder="John Smith" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="phone">Phone Number *</Label>
          <Input id="phone" required type="tel" placeholder="(555) 000-0000" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} />
        </div>
      </div>
      <div className="space-y-1">
        <Label htmlFor="email">Email Address</Label>
        <Input id="email" type="email" placeholder="john@example.com" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} />
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label>Service Needed *</Label>
          <Select required value={form.service} onValueChange={v => setForm(p => ({ ...p, service: v }))}>
            <SelectTrigger><SelectValue placeholder="Select service" /></SelectTrigger>
            <SelectContent>
              {services.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label>Urgency</Label>
          <Select value={form.urgency} onValueChange={v => setForm(p => ({ ...p, urgency: v }))}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="EMERGENCY">Emergency - ASAP</SelectItem>
              <SelectItem value="HIGH">High - Today</SelectItem>
              <SelectItem value="NORMAL">Normal - This week</SelectItem>
              <SelectItem value="LOW">Low - Flexible</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="space-y-1">
        <Label htmlFor="city">City / Neighborhood *</Label>
        <Input id="city" required placeholder="Austin, TX" value={form.city} onChange={e => setForm(p => ({ ...p, city: e.target.value }))} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="notes">Tell us about the problem</Label>
        <Textarea id="notes" placeholder="My AC stopped working, it's making a strange noise..." value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
      </div>
      {status === 'error' && (
        <p className="text-red-600 text-sm">Something went wrong. Please try again or call us directly.</p>
      )}
      <Button type="submit" size="lg" className="w-full" disabled={status === 'loading'}>
        {status === 'loading' ? <><Loader2 className="h-4 w-4 animate-spin" /> Sending...</> : 'Request Service Now'}
      </Button>
    </form>
  )
}
