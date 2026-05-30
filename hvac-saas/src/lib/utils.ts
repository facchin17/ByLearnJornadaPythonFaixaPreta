import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPhone(phone: string): string {
  const cleaned = phone.replace(/\D/g, '')
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`
  }
  return phone
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatDateTime(date: Date | string): string {
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function getUrgencyColor(urgency: string): string {
  const map: Record<string, string> = {
    EMERGENCY: 'text-red-600 bg-red-50',
    HIGH: 'text-orange-600 bg-orange-50',
    NORMAL: 'text-blue-600 bg-blue-50',
    LOW: 'text-gray-600 bg-gray-50',
  }
  return map[urgency] || 'text-gray-600 bg-gray-50'
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    NEW: 'text-blue-700 bg-blue-100',
    CONTACTED: 'text-yellow-700 bg-yellow-100',
    BOOKED: 'text-purple-700 bg-purple-100',
    WON: 'text-green-700 bg-green-100',
    LOST: 'text-red-700 bg-red-100',
  }
  return map[status] || 'text-gray-700 bg-gray-100'
}
