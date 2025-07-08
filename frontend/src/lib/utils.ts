import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date) {
  return format(new Date(date), 'MMM dd, yyyy HH:mm')
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value)
}

export function getPositionColor(positionType: string) {
  switch (positionType) {
    case 'STRONG_BUY':
      return 'text-green-700 bg-green-50 border-green-200'
    case 'BUY':
      return 'text-green-600 bg-green-50 border-green-200'
    case 'SHORT':
      return 'text-red-600 bg-red-50 border-red-200'
    case 'STRONG_SHORT':
      return 'text-red-700 bg-red-50 border-red-200'
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function getConfidenceColor(confidence: number) {
  if (confidence >= 0.8) return 'text-green-600'
  if (confidence >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

export function formatConfidence(confidence: number) {
  return `${Math.round(confidence * 100)}%`
}