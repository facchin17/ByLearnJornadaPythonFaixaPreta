'use client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Phone, Calendar, Target, Users } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

type Props = {
  companyName: string
  leadsCount: number
  missedCallsCount: number
  appointmentsCount: number
  jobsWon: number
  estimatedRevenue: number
  monthlyFee: number
  roi: number
  avgTicket: number
}

export default function RoiDashboard(props: Props) {
  const { companyName, leadsCount, missedCallsCount, appointmentsCount, jobsWon, estimatedRevenue, monthlyFee, roi, avgTicket } = props
  const roiMultiple = roi.toFixed(1)
  const isPositive = roi >= 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ROI Report</h1>
        <p className="text-gray-500 text-sm mt-1">{companyName} &middot; {new Date().toLocaleString('en-US', { month: 'long', year: 'numeric' })}</p>
      </div>

      {/* ROI Hero */}
      <div className={`rounded-2xl p-8 text-white ${isPositive ? 'bg-gradient-to-br from-green-600 to-green-700' : 'bg-gradient-to-br from-gray-600 to-gray-700'}`}>
        <div className="grid md:grid-cols-2 gap-6 items-center">
          <div>
            <p className="text-green-100 font-medium mb-2">This Month&apos;s ROI</p>
            <div className="text-7xl font-black mb-2">{roiMultiple}x</div>
            <p className="text-green-100">For every $1 spent on HVAC Pro, you&apos;re getting {roiMultiple} dollars back.</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/10 rounded-xl p-4">
              <p className="text-green-100 text-sm">Estimated Revenue</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(estimatedRevenue)}</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4">
              <p className="text-green-100 text-sm">Monthly Investment</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(monthlyFee)}</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4">
              <p className="text-green-100 text-sm">Jobs Won</p>
              <p className="text-2xl font-bold mt-1">{jobsWon}</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4">
              <p className="text-green-100 text-sm">Avg Ticket</p>
              <p className="text-2xl font-bold mt-1">{formatCurrency(avgTicket)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Leads Captured', value: leadsCount, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50', desc: 'New leads this month' },
          { label: 'Missed Calls Recovered', value: missedCallsCount, icon: Phone, color: 'text-orange-600', bg: 'bg-orange-50', desc: 'Would have been lost' },
          { label: 'Appointments Booked', value: appointmentsCount, icon: Calendar, color: 'text-purple-600', bg: 'bg-purple-50', desc: 'Services scheduled' },
          { label: 'Jobs Won', value: jobsWon, icon: Target, color: 'text-green-600', bg: 'bg-green-50', desc: 'Completed & paid' },
        ].map(({ label, value, icon: Icon, color, bg, desc }) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">{label}</p>
                  <p className="text-4xl font-bold text-gray-900 mt-1">{value}</p>
                  <p className="text-xs text-gray-400 mt-1">{desc}</p>
                </div>
                <div className={`w-11 h-11 ${bg} rounded-xl flex items-center justify-center`}>
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Formula explanation */}
      <Card>
        <CardHeader><CardTitle className="text-base">How We Calculate ROI</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="font-medium text-gray-700 mb-1">Estimated Revenue</p>
              <p className="text-gray-500">{jobsWon} jobs won &times; {formatCurrency(avgTicket)} avg ticket = <span className="font-semibold text-gray-900">{formatCurrency(estimatedRevenue)}</span></p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="font-medium text-gray-700 mb-1">Monthly Investment</p>
              <p className="text-gray-500">HVAC Pro subscription = <span className="font-semibold text-gray-900">{formatCurrency(monthlyFee)}/mo</span></p>
            </div>
            <div className={`rounded-lg p-4 ${isPositive ? 'bg-green-50' : 'bg-gray-50'}`}>
              <p className="font-medium text-gray-700 mb-1">ROI Multiple</p>
              <p className="text-gray-500">{formatCurrency(estimatedRevenue)} &divide; {formatCurrency(monthlyFee)} = <span className={`font-bold text-lg ${isPositive ? 'text-green-700' : 'text-gray-700'}`}>{roiMultiple}x</span></p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
