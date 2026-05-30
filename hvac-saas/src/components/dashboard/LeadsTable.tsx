'use client'
import { useState } from 'react'
import { formatDateTime, formatCurrency, getStatusColor } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Phone, MapPin, Search } from 'lucide-react'

type Lead = {
  id: string
  name: string
  phone: string
  email: string | null
  service: string | null
  urgency: string
  city: string | null
  status: string
  source: string
  estimatedValue: number | null
  createdAt: Date
  company: { name: string; slug: string }
}

const SOURCE_LABELS: Record<string, string> = {
  WEBSITE: 'Website',
  CHATBOT: 'Chatbot',
  MISSED_CALL: 'Missed Call',
  MANUAL: 'Manual',
}

export default function LeadsTable({ initialLeads }: { initialLeads: Lead[] }) {
  const [leads, setLeads] = useState(initialLeads)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('ALL')

  const filtered = leads.filter(l => {
    const matchSearch = !search || l.name.toLowerCase().includes(search.toLowerCase()) || l.phone.includes(search)
    const matchStatus = filterStatus === 'ALL' || l.status === filterStatus
    return matchSearch && matchStatus
  })

  async function updateStatus(id: string, status: string) {
    await fetch(`/api/leads/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
    setLeads(prev => prev.map(l => l.id === id ? { ...l, status } : l))
  }

  return (
    <Card>
      <div className="p-4 border-b border-gray-100 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input className="pl-9" placeholder="Search leads..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Status</SelectItem>
            <SelectItem value="NEW">New</SelectItem>
            <SelectItem value="CONTACTED">Contacted</SelectItem>
            <SelectItem value="BOOKED">Booked</SelectItem>
            <SelectItem value="WON">Won</SelectItem>
            <SelectItem value="LOST">Lost</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600">Customer</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Service</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Source</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Value</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(lead => (
              <tr key={lead.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-900">{lead.name}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{lead.phone}</span>
                    {lead.city && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{lead.city}</span>}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600">{lead.service || '—'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{SOURCE_LABELS[lead.source] || lead.source}</td>
                <td className="px-4 py-3">
                  <Select value={lead.status} onValueChange={v => updateStatus(lead.id, v)}>
                    <SelectTrigger className="h-7 w-32 text-xs border-0 bg-transparent p-0">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(lead.status)}`}>
                        {lead.status}
                      </span>
                    </SelectTrigger>
                    <SelectContent>
                      {['NEW','CONTACTED','BOOKED','WON','LOST'].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </td>
                <td className="px-4 py-3 font-medium text-gray-900">
                  {lead.estimatedValue ? formatCurrency(lead.estimatedValue) : '—'}
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{formatDateTime(lead.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-400">No leads found</div>
        )}
      </div>
    </Card>
  )
}
