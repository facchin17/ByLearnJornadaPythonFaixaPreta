'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { signOut } from 'next-auth/react'
import { LayoutDashboard, Users, Calendar, BarChart3, LogOut, Thermometer, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type Props = { user: { name?: string | null; email?: string | null } }

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/leads', label: 'Leads', icon: Users },
  { href: '/dashboard/appointments', label: 'Appointments', icon: Calendar },
  { href: '/dashboard/roi', label: 'ROI Report', icon: BarChart3 },
  { href: '/dashboard/companies', label: 'Companies', icon: Building2 },
]

export default function DashboardNav({ user }: Props) {
  const pathname = usePathname()

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2 font-bold text-gray-900">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Thermometer className="h-4 w-4 text-white" />
            </div>
            HVAC Pro
          </Link>
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  pathname === href
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500 hidden sm:block">{user.email}</span>
          <Button variant="ghost" size="sm" onClick={() => signOut({ callbackUrl: '/login' })}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </nav>
  )
}
